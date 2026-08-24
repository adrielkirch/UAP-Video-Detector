"""
Unit tests for offline annotated H.264 MP4 export used by the HTML5 player.
"""

from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from src.orchestration.video_annotator import (
    annotated_output_path,
    remove_annotated_output,
    write_annotated_video,
)


class TestAnnotatedOutputPath:
    def test_path_uses_temp_and_video_id(self, tmp_path):
        dest = annotated_output_path("abc123", directory=str(tmp_path))
        assert dest.name == "annotated_abc123.mp4"
        assert dest.parent == tmp_path
        assert dest.parent.exists()

    def test_remove_annotated_output_deletes_file(self, tmp_path):
        dest = tmp_path / "annotated_x.mp4"
        dest.write_bytes(b"data")
        remove_annotated_output(str(dest))
        assert not dest.exists()

    def test_remove_annotated_output_ignores_missing(self, tmp_path):
        remove_annotated_output(str(tmp_path / "missing.mp4"))


class TestWriteAnnotatedVideo:
    @patch("src.orchestration.video_annotator._remux_to_h264")
    @patch("src.orchestration.video_annotator.draw_scan_status")
    @patch("src.orchestration.video_annotator.draw_detections_on_frame")
    @patch("cv2.VideoWriter")
    @patch("cv2.VideoCapture")
    def test_writes_each_frame_through_pipeline(
        self, mock_capture_cls, mock_writer_cls, mock_draw, mock_status, mock_remux
    ):
        frame = np.zeros((20, 30, 3), dtype=np.uint8)
        capture = MagicMock()
        capture.isOpened.return_value = True
        capture.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_WIDTH: 30,
            cv2.CAP_PROP_FRAME_HEIGHT: 20,
            cv2.CAP_PROP_FRAME_COUNT: 2,
        }.get(prop, 0)
        capture.read.side_effect = [(True, frame), (True, frame), (False, None)]
        mock_capture_cls.return_value = capture

        writer = MagicMock()
        writer.isOpened.return_value = True
        mock_writer_cls.return_value = writer
        mock_draw.side_effect = lambda img, _dets: img

        pipeline = MagicMock()
        pipeline.is_enabled.return_value = True
        pipeline.process_frame.return_value = None
        pipeline.get_last_detections.return_value = None
        pipeline.last_lag_warning = None

        dest = write_annotated_video("in.mp4", "out.mp4", pipeline)

        assert dest == "out.mp4"
        assert writer.write.call_count == 2
        assert pipeline.process_frame.call_count == 2
        writer.release.assert_called_once()
        capture.release.assert_called_once()
        mock_remux.assert_called_once()
