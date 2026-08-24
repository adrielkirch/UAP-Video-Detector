"""
Unit tests for the streamlit-webrtc video processor.

Verifies YOLO overlay wiring in recv() without a live WebRTC session.
"""

from unittest.mock import Mock, patch

import numpy as np

from src.inference.detection_types import Detection, FrameDetections
from src.ui.components.webrtc_player import (
    DetectionVideoProcessor,
    annotate_frame,
    clamp_seek_ms,
    create_media_player,
    current_playback_ms,
    format_timestamp_ms,
    player_shell_css,
)
from src.ui.components.player_layout import player_display_box


class FakeVideoFrame:
    """Minimal av.VideoFrame stand-in for processor tests."""

    def __init__(self, array: np.ndarray):
        self.array = array

    def to_ndarray(self, format="bgr24"):
        assert format == "bgr24"
        return self.array


class TestAnnotateFrame:
    """Test OpenCV annotation used by the WebRTC callback."""

    def test_disabled_scan_does_not_call_pipeline(self):
        frame = np.zeros((40, 60, 3), dtype=np.uint8)
        pipeline = Mock()

        result = annotate_frame(frame, pipeline, scan_enabled=False, frame_index=0)

        pipeline.process_frame.assert_not_called()
        assert result.shape == frame.shape
        assert result is not frame

    def test_enabled_scan_uses_pipeline_and_last_detections_on_skip(self):
        frame = np.zeros((40, 60, 3), dtype=np.uint8)
        detections = FrameDetections(
            [
                Detection(
                    class_name="drone",
                    confidence=0.9,
                    bbox_xyxy=[2, 2, 20, 20],
                )
            ]
        )
        pipeline = Mock()
        pipeline.is_enabled.return_value = True
        pipeline.process_frame.return_value = None
        pipeline.get_last_detections.return_value = detections
        pipeline.last_lag_warning = None

        with patch(
            "src.ui.components.webrtc_player.draw_detections_on_frame"
        ) as mock_draw:
            mock_draw.side_effect = lambda img, _dets: img
            annotate_frame(frame, pipeline, scan_enabled=True, frame_index=3)

        pipeline.process_frame.assert_called_once()
        mock_draw.assert_called_once()
        drawn_detections = mock_draw.call_args[0][1]
        assert drawn_detections is detections


class TestDetectionVideoProcessor:
    """Test VideoProcessorBase.recv conversion and pipeline wiring."""

    def test_recv_converts_frame_and_returns_av_frame(self):
        source = np.full((32, 48, 3), 40, dtype=np.uint8)
        incoming = FakeVideoFrame(source)
        outgoing = FakeVideoFrame(source.copy())

        pipeline = Mock()
        pipeline.is_enabled.return_value = True
        pipeline.process_frame.return_value = FrameDetections([])
        pipeline.get_last_detections.return_value = FrameDetections([])
        pipeline.last_lag_warning = None

        processor = DetectionVideoProcessor()
        processor.scan_pipeline = pipeline
        processor.scan_enabled = True

        with patch(
            "src.ui.components.webrtc_player.av.VideoFrame.from_ndarray",
            return_value=outgoing,
        ) as mock_from:
            result = processor.recv(incoming)

        mock_from.assert_called_once()
        args, kwargs = mock_from.call_args
        assert kwargs.get("format") == "bgr24" or (
            len(args) > 1 and args[1] == "bgr24"
        )
        assert result is outgoing
        pipeline.process_frame.assert_called_once()

    def test_recv_increments_frame_index_across_calls(self):
        frame = FakeVideoFrame(np.zeros((16, 16, 3), dtype=np.uint8))
        pipeline = Mock()
        pipeline.is_enabled.return_value = True
        pipeline.process_frame.return_value = None
        pipeline.get_last_detections.return_value = None
        pipeline.last_lag_warning = None

        processor = DetectionVideoProcessor()
        processor.scan_pipeline = pipeline
        processor.scan_enabled = True

        with patch(
            "src.ui.components.webrtc_player.av.VideoFrame.from_ndarray",
            side_effect=lambda arr, format="bgr24": FakeVideoFrame(arr),
        ):
            processor.recv(frame)
            processor.recv(frame)

        assert pipeline.process_frame.call_args_list[0].kwargs["frame_index"] == 0
        assert pipeline.process_frame.call_args_list[1].kwargs["frame_index"] == 1


class TestPlayerDisplayBox:
    """Test YouTube-style aspect-ratio box for native video sizes."""

    def test_portrait_360x640_keeps_native_ratio(self):
        box = player_display_box(360, 640, max_height_vh=70)
        assert box["width"] == 360
        assert box["height"] == 640
        assert box["aspect_ratio"] == "360 / 640"
        assert box["orientation"] == "portrait"
        assert "360px" in box["width_css"]
        assert "360 / 640" in box["width_css"]

    def test_landscape_720x480_keeps_native_ratio(self):
        box = player_display_box(720, 480, max_height_vh=70)
        assert box["width"] == 720
        assert box["height"] == 480
        assert box["aspect_ratio"] == "720 / 480"
        assert box["orientation"] == "landscape"
        assert "720px" in box["width_css"]

    def test_low_res_does_not_stretch_past_native_pixels(self):
        box = player_display_box(640, 360)
        assert box["max_width_px"] == 640
        assert box["width_css"].startswith("min(100%, 640px")

    def test_portrait_360x640_container_width_is_360(self):
        box = player_display_box(360, 640)
        assert box["max_width_px"] == 360
        assert "360px" in box["width_css"]

    def test_display_size_keeps_small_portrait_native(self):
        from src.ui.components.player_layout import display_size

        assert display_size(360, 640, 960, 720) == (360, 640)

    def test_display_size_scales_down_large_landscape(self):
        from src.ui.components.player_layout import display_size

        width, height = display_size(1920, 1080, 960, 720)
        assert width == 960
        assert height == 540

    def test_unknown_size_falls_back_to_720p_16_9(self):
        box = player_display_box(0, 0)
        assert box["width"] == 720
        assert box["height"] == 405
        assert box["orientation"] == "landscape"

    def test_shell_css_embeds_source_aspect_ratio(self):
        css = player_shell_css(player_display_box(360, 640))
        assert "aspect-ratio: 360 / 640" in css
        assert "streamlit_webrtc" in css


class TestTimelineHelpers:
    """Test timestamp formatting and seek math for the WebRTC layer."""

    def test_format_timestamp_ms_mm_ss(self):
        assert format_timestamp_ms(0) == "00:00"
        assert format_timestamp_ms(83_000) == "01:23"

    def test_format_timestamp_ms_includes_hours(self):
        assert format_timestamp_ms(3_725_000) == "1:02:05"

    def test_clamp_seek_ms_stays_in_range(self):
        assert clamp_seek_ms(-100, 5000) == 0
        assert clamp_seek_ms(2500, 5000) == 2500
        assert clamp_seek_ms(9000, 5000) == 5000
        assert clamp_seek_ms(100, 0) == 0

    def test_current_playback_ms_adds_frames_to_seek_offset(self):
        assert current_playback_ms(10_000, 30, 30.0) == 11_000
        assert current_playback_ms(5_000, 0, 0.0) == 5_000

    def test_annotate_frame_draws_timestamp_overlay(self):
        frame = np.zeros((80, 160, 3), dtype=np.uint8)
        with patch(
            "src.ui.components.webrtc_player.draw_timestamp_overlay"
        ) as mock_ts:
            annotate_frame(
                frame,
                None,
                scan_enabled=False,
                frame_index=15,
                seek_offset_ms=5_000,
                fps=30.0,
                duration_ms=20_000,
            )
        mock_ts.assert_called_once()
        _img, current_ms, duration_ms = mock_ts.call_args[0]
        assert current_ms == 5_500
        assert duration_ms == 20_000

    @patch("src.ui.components.webrtc_player.MediaPlayer")
    def test_create_media_player_applies_ffmpeg_start_offset(self, mock_player):
        create_media_player("clip.mp4", start_seconds=12.5)
        kwargs = mock_player.call_args.kwargs
        assert kwargs["options"]["ss"] == "12.500"

    @patch("src.ui.components.webrtc_player.MediaPlayer")
    def test_create_media_player_skips_offset_at_start(self, mock_player):
        create_media_player("clip.mp4", start_seconds=0)
        kwargs = mock_player.call_args.kwargs
        assert kwargs["options"] is None


class TestAppDropsLegacyPlaybackLoop:
    """Regression: the Streamlit app must not drive video via st.rerun()."""

    def test_app_does_not_import_legacy_transport_controls(self):
        source = open("src/ui/app.py", encoding="utf-8").read()
        assert "render_playback_controls" not in source
        assert "render_seek_control" not in source
        assert "st.image(" not in source
        assert "render_native_player" in source
        assert 'layout="centered"' in source
        assert "_render_empty_state" in source
        assert "st.sidebar" not in source
        assert "render_webrtc_player" not in source
        assert "webrtc_streamer" not in source
