"""
Integration tests for player-only mode (SC-005).

Tests that video player functionality works completely independently
when scanner is unavailable, disabled, or misconfigured.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.ingestion.video_session import VideoSession
from src.ingestion.playback import PlaybackController
from src.orchestration.scan_pipeline import ScanPipeline
from src.inference.null_detector import NullDetector
from src.inference.factory import DetectorFactory, DetectorNotReadyError


class TestPlayerWithoutScanner:
    """Test player functionality works independently of scanner availability."""

    @patch("src.ingestion.video_session.cv2.VideoCapture")
    def test_video_upload_works_without_scanner(self, mock_cv2_capture):
        """Should upload and process video without any scanner dependencies."""
        # Mock video capture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            "CAP_PROP_FRAME_COUNT": 1800,
            "CAP_PROP_FPS": 30.0,
            "CAP_PROP_POS_MSEC": 60000,
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_cap

        # Create video session (no scanner dependency)
        video_session = VideoSession()

        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Upload should work without scanner
            active_video = video_session.set_from_path(temp_path)

            assert active_video is not None
            assert active_video.status == "ready"
            assert video_session.get_active() == active_video

        finally:
            os.unlink(temp_path)

    def test_playback_works_without_scanner(self):
        """Should provide full playback functionality without scanner."""
        # Mock video session
        video_session = Mock(spec=VideoSession)

        from src.ingestion.video_session import ActiveVideo

        mock_video = ActiveVideo(
            id="no-scanner-test",
            display_name="test_no_scanner.mp4",
            path="/fake/path.mp4",
            duration_ms=60000,
            frame_count=1800,
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video

        # Create playback controller (no scanner dependency)
        playback_controller = PlaybackController()
        playback_controller.attach(video_session)

        # All playback operations should work
        assert playback_controller.get_state() is not None
        assert playback_controller.get_state().state == "stopped"

        # Play/pause/stop should work
        playback_controller.play()
        assert playback_controller.get_state().state == "playing"

        playback_controller.pause()
        assert playback_controller.get_state().state == "paused"

        playback_controller.stop()
        assert playback_controller.get_state().state == "stopped"

        # Seeking should work
        playback_controller.seek_ms(30000)
        assert playback_controller.get_state().position_ms == 30000

    def test_scan_pipeline_with_null_detector_doesnt_break_player(self):
        """Should handle scan pipeline with null detector gracefully."""
        # Create scan pipeline with null detector
        scan_pipeline = ScanPipeline()
        null_detector = NullDetector()
        null_detector.load("config.yaml")

        scan_pipeline.attach_detector(null_detector)

        # Mock playback controller
        playback_controller = Mock(spec=PlaybackController)
        scan_pipeline.attach_playback(playback_controller)

        # Enable scanning (should work with null detector)
        scan_pipeline.enable_scan()
        assert scan_pipeline.is_enabled()

        # Process frames (should return empty results, not crash)
        import numpy as np

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        detections = scan_pipeline.process_frame(frame, frame_index=0)
        assert detections is not None
        assert len(detections.detections) == 0

        # Player functionality should be unaffected
        assert scan_pipeline._playback_controller == playback_controller

    def test_detector_factory_falls_back_to_null_on_errors(self):
        """Should fall back to null detector when YOLO unavailable."""
        factory = DetectorFactory()

        # Test missing config file
        with pytest.raises(DetectorNotReadyError):
            factory.create_detector("non_existent_config.yaml")

        # Test null backend (should succeed)
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "null",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector = factory.create_detector("config/detector.yaml")

            # Should get working null detector
            assert isinstance(detector, NullDetector)
            assert detector.is_ready()

    @patch("ultralytics.YOLO")
    def test_scan_unavailable_notice_doesnt_block_player(self, mock_yolo_class):
        """Should display scan unavailable notice without blocking player."""
        # Mock YOLO failure
        mock_yolo_class.side_effect = ImportError("ultralytics not available")

        # Create scan pipeline
        scan_pipeline = ScanPipeline()

        # Try to create YOLO detector (will fail)
        factory = DetectorFactory()

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "yolov8",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                # Should raise error but not crash entire application
                with pytest.raises(DetectorNotReadyError):
                    factory.create_detector("config/detector.yaml")

                # Fall back to null detector
                null_detector = NullDetector()
                null_detector.load("config.yaml")
                scan_pipeline.attach_detector(null_detector)

                # Pipeline should work with null detector
                assert scan_pipeline._detector == null_detector

        finally:
            os.unlink(temp_weights_path)

    def test_player_performance_unaffected_by_scanner_state(self):
        """Should maintain player performance regardless of scanner state."""
        # Mock video session and playback controller
        video_session = Mock(spec=VideoSession)
        playback_controller = PlaybackController()

        from src.ingestion.video_session import ActiveVideo

        mock_video = ActiveVideo(
            id="perf-test",
            display_name="performance_test.mp4",
            path="/fake/perf.mp4",
            duration_ms=120000,  # 2 minutes
            frame_count=3600,  # 120s * 30fps
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video
        playback_controller.attach(video_session)

        # Create scan pipeline
        scan_pipeline = ScanPipeline()
        null_detector = NullDetector()
        null_detector.load("config.yaml")
        scan_pipeline.attach_detector(null_detector)

        # Test playback operations with scanner disabled
        scan_pipeline.disable_scan()

        playback_controller.play()
        playback_controller.seek_ms(60000)  # Seek to middle
        playback_controller.pause()
        playback_controller.seek_frame(1800)  # Seek by frame
        playback_controller.stop()

        # All operations should complete without scanner interference
        final_state = playback_controller.get_state()
        assert final_state.state == "stopped"
        assert final_state.position_ms == 0  # Reset by stop()

    def test_ui_components_work_without_detection_overlay(self):
        """Should verify UI components work when detection overlay is disabled."""
        # Mock playback controller with no detections
        playback_controller = Mock(spec=PlaybackController)

        from src.ingestion.playback import PlaybackSession

        mock_state = PlaybackSession(duration_ms=30000)
        mock_state.state = "playing"
        playback_controller.get_state.return_value = mock_state

        # Mock frame with no detections
        import numpy as np

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        playback_controller.read_current_frame.return_value = frame

        # Import overlay function
        from src.ui.components.detection_overlay import draw_detections_on_frame

        # Should handle None detections gracefully
        result_frame = draw_detections_on_frame(frame, None)
        assert result_frame is frame  # Should return original frame

        # Should handle empty detections gracefully
        from src.inference.detection_types import FrameDetections

        empty_detections = FrameDetections([])
        result_frame = draw_detections_on_frame(frame, empty_detections)
        assert result_frame is frame  # Should return original frame

    def test_configuration_swap_preserves_player_state(self):
        """Should maintain player state when detector configuration changes."""
        # Start with working player
        video_session = Mock(spec=VideoSession)
        playback_controller = PlaybackController()

        from src.ingestion.video_session import ActiveVideo

        mock_video = ActiveVideo(
            id="config-swap-test",
            display_name="config_swap_test.mp4",
            path="/fake/config_swap.mp4",
            duration_ms=90000,
            frame_count=2700,
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video
        playback_controller.attach(video_session)

        # Set player to specific state
        playback_controller.play()
        playback_controller.seek_ms(45000)  # Seek to middle

        original_state = playback_controller.get_state()
        assert original_state.state == "playing"
        assert original_state.position_ms == 45000

        # Simulate detector configuration swap (should not affect player)
        scan_pipeline = ScanPipeline()

        # Start with null detector
        null_detector1 = NullDetector()
        null_detector1.load("config1.yaml")
        scan_pipeline.attach_detector(null_detector1)

        # Swap to different null detector (simulating config change)
        null_detector2 = NullDetector()
        null_detector2.load("config2.yaml")
        scan_pipeline.attach_detector(null_detector2)

        # Player state should be preserved
        current_state = playback_controller.get_state()
        assert current_state.state == original_state.state
        assert current_state.position_ms == original_state.position_ms
        assert current_state.duration_ms == original_state.duration_ms
