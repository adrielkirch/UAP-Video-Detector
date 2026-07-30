"""
Unit tests for ScanPipeline frame processing and state management.

Tests scan enable/disable, frame stride skipping, playback integration,
and performance monitoring with lag warnings.
"""

from unittest.mock import Mock, patch
import numpy as np
import time

from src.orchestration.scan_pipeline import ScanPipeline
from src.inference.detection_types import Detection, FrameDetections
from src.ingestion.playback import PlaybackController


class TestScanPipeline:
    """Test ScanPipeline state management and frame processing."""

    def test_pipeline_initial_state(self):
        """Should start with scan disabled and no detections."""
        pipeline = ScanPipeline()

        assert not pipeline.is_enabled()
        assert pipeline.get_last_detections() is None
        assert pipeline.last_lag_warning is None

    def test_enable_disable_scan_toggle(self):
        """Should properly toggle scan enabled state."""
        pipeline = ScanPipeline()

        # Initially disabled
        assert not pipeline.is_enabled()

        # Enable scan
        pipeline.enable_scan()
        assert pipeline.is_enabled()

        # Disable scan
        pipeline.disable_scan()
        assert not pipeline.is_enabled()

    def test_attach_detector_and_playback(self):
        """Should accept detector and playback controller."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True

        mock_controller = Mock(spec=PlaybackController)

        # Should attach without error
        pipeline.attach_detector(mock_detector)
        pipeline.attach_playback(mock_controller)

        assert pipeline._detector is mock_detector
        assert pipeline._playback_controller is mock_controller

    def test_frame_stride_skipping(self):
        """Should skip frames based on stride configuration."""
        pipeline = ScanPipeline(frame_stride=3)  # Process every 3rd frame

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True
        mock_detector.detect.return_value = FrameDetections(
            [Detection("airplane", 0.9, [10, 10, 50, 50])]
        )

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process multiple frames
        results = []
        for i in range(10):
            result = pipeline.process_frame(frame, frame_index=i)
            results.append(result)

        # Should only process frames 0, 3, 6, 9 (stride=3)
        processed_count = sum(1 for r in results if r is not None)
        expected_processed = len([i for i in range(10) if i % 3 == 0])  # 0, 3, 6, 9 = 4

        assert processed_count == expected_processed
        assert mock_detector.detect.call_count == expected_processed

    def test_scan_disabled_skips_detection(self):
        """Should skip detection when scan is disabled."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True

        pipeline.attach_detector(mock_detector)
        # Don't enable scan

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should skip detection
        result = pipeline.process_frame(frame, frame_index=0)

        assert result is None
        mock_detector.detect.assert_not_called()

    def test_detector_not_ready_skips_detection(self):
        """Should skip detection when detector is not ready."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = False  # Not ready

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should skip detection when not ready
        result = pipeline.process_frame(frame, frame_index=0)

        assert result is None
        mock_detector.detect.assert_not_called()

    def test_pause_keeps_last_detections(self):
        """Should preserve last detections when playback is paused."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True

        # First detection
        first_detections = FrameDetections(
            [Detection("airplane", 0.9, [10, 10, 50, 50])]
        )
        mock_detector.detect.return_value = first_detections

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frame and get detections
        result = pipeline.process_frame(frame, frame_index=0)
        assert result == first_detections
        assert pipeline.get_last_detections() == first_detections

        # Simulate playback pause (no new frames processed)
        # Last detections should be preserved
        assert pipeline.get_last_detections() == first_detections

    def test_disable_scan_stops_new_inferences(self):
        """Should stop running new inferences when scan disabled mid-playback."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True
        mock_detector.detect.return_value = FrameDetections(
            [Detection("airplane", 0.9, [10, 10, 50, 50])]
        )

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frame while enabled
        result1 = pipeline.process_frame(frame, frame_index=0)
        assert result1 is not None

        # Disable scan mid-playback
        pipeline.disable_scan()

        # Process frame while disabled
        result2 = pipeline.process_frame(frame, frame_index=1)
        assert result2 is None

        # Should have only called detector once (before disable)
        assert mock_detector.detect.call_count == 1

    def test_scan_pipeline_records_infer_duration(self):
        """Should record inference duration for performance monitoring."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True

        # Mock slow detector (simulate 1500ms inference)
        def slow_detect(frame):
            time.sleep(0.05)  # 50ms for test (simulate 1500ms)
            return FrameDetections([])

        mock_detector.detect.side_effect = slow_detect

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frame and check duration recording
        time.time()
        pipeline.process_frame(frame, frame_index=0)

        # Should have recorded some duration
        assert pipeline.last_infer_duration_ms > 0
        assert (
            pipeline.last_infer_duration_ms >= 45
        )  # At least 45ms (allowing for variance)

    def test_lag_warning_when_inference_exceeds_threshold(self):
        """Should flag lag warning when inference duration exceeds threshold."""
        # Set threshold to 100ms for test
        pipeline = ScanPipeline(lag_warn_threshold_ms=100)

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True

        # Mock detector that simulates exceeding threshold
        def mock_detect(frame):
            time.sleep(0.12)  # Sleep to actually exceed 100ms threshold
            return FrameDetections([])

        mock_detector.detect.side_effect = mock_detect

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frame that exceeds threshold
        pipeline.process_frame(frame, frame_index=0)

        # Should flag lag warning
        assert pipeline.last_lag_warning is not None
        assert "exceeded" in pipeline.last_lag_warning.lower()
        assert "100.0ms threshold" in pipeline.last_lag_warning

    @patch("src.orchestration.scan_metrics.logger")
    def test_no_lag_warning_when_inference_under_threshold(self, mock_logger):
        """Should not flag lag warning when inference is fast enough."""
        pipeline = ScanPipeline(lag_warn_threshold_ms=2000)  # 2 second threshold

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True
        mock_detector._device = "cpu"  # Add device attribute for metrics

        # Mock fast detector - return quickly
        mock_detector.detect.return_value = FrameDetections([])

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process fast frame
        pipeline.process_frame(frame, frame_index=0)

        # Should not flag lag warning
        assert pipeline.last_lag_warning is None

    def test_clear_detections_resets_state(self):
        """Should reset detection state when cleared."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True
        mock_detector.detect.return_value = FrameDetections(
            [Detection("airplane", 0.9, [10, 10, 50, 50])]
        )

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frame to get detections
        pipeline.process_frame(frame, frame_index=0)
        assert pipeline.get_last_detections() is not None

        # Clear detections
        pipeline.clear_detections()

        # Should reset state
        assert pipeline.get_last_detections() is None
        assert pipeline.last_lag_warning is None

    def test_process_frame_without_frame_index(self):
        """Should handle process_frame without explicit frame_index."""
        pipeline = ScanPipeline()

        mock_detector = Mock()
        mock_detector.is_ready.return_value = True
        mock_detector.detect.return_value = FrameDetections([])

        pipeline.attach_detector(mock_detector)
        pipeline.enable_scan()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should handle missing frame_index gracefully
        result = pipeline.process_frame(frame)

        # Should still process (assume frame_index=0)
        assert result is not None
        mock_detector.detect.assert_called_once()
