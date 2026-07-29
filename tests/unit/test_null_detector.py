"""
Unit tests for NullDetector (empty/not-ready behavior).

Tests the null object pattern implementation for detector abstraction
with proper empty detection results and state management.
"""

import pytest
import numpy as np

from src.inference.null_detector import NullDetector
from src.inference.detector import DetectorError
from src.inference.detection_types import FrameDetections


class TestNullDetector:
    """Test NullDetector empty behavior and state management."""

    def test_null_detector_initial_state(self):
        """Should start in not-ready state."""
        detector = NullDetector()

        assert not detector.is_ready()

    def test_load_makes_detector_ready(self):
        """Should become ready after load() call."""
        detector = NullDetector()

        # Load should make it ready
        detector.load("any/config/path.yaml")

        assert detector.is_ready()

    def test_detect_when_not_ready_raises_error(self):
        """Should raise DetectorError when detect() called before load()."""
        detector = NullDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should raise error when not ready
        with pytest.raises(DetectorError, match="Detector not ready"):
            detector.detect(frame)

    def test_detect_when_ready_returns_empty_detections(self):
        """Should return empty FrameDetections when ready."""
        detector = NullDetector()
        detector.load("config.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should return empty detections
        result = detector.detect(frame)

        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 0

    def test_detect_accepts_different_frame_shapes(self):
        """Should handle various frame dimensions gracefully."""
        detector = NullDetector()
        detector.load("config.yaml")

        # Test different frame shapes
        frames = [
            np.zeros((240, 320, 3), dtype=np.uint8),  # Small frame
            np.zeros((1080, 1920, 3), dtype=np.uint8),  # Large frame
            np.zeros((480, 640, 1), dtype=np.uint8),  # Grayscale
        ]

        for frame in frames:
            result = detector.detect(frame)
            assert isinstance(result, FrameDetections)
            assert len(result.detections) == 0

    def test_close_graceful_cleanup(self):
        """Should handle close() gracefully in all states."""
        detector = NullDetector()

        # Close when not ready
        detector.close()  # Should not raise

        # Load and close when ready
        detector.load("config.yaml")
        assert detector.is_ready()

        detector.close()  # Should not raise

    def test_multiple_load_calls(self):
        """Should handle multiple load() calls gracefully."""
        detector = NullDetector()

        # Multiple loads should work
        detector.load("config1.yaml")
        assert detector.is_ready()

        detector.load("config2.yaml")
        assert detector.is_ready()

        # Should still return empty detections
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(frame)
        assert len(result.detections) == 0

    def test_load_with_none_config_path(self):
        """Should handle None config path gracefully."""
        detector = NullDetector()

        # Should handle None config
        detector.load(None)
        assert detector.is_ready()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(frame)
        assert len(result.detections) == 0

    def test_load_with_empty_config_path(self):
        """Should handle empty config path gracefully."""
        detector = NullDetector()

        # Should handle empty string
        detector.load("")
        assert detector.is_ready()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(frame)
        assert len(result.detections) == 0

    def test_consistent_empty_results(self):
        """Should consistently return empty results across multiple calls."""
        detector = NullDetector()
        detector.load("config.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Multiple detections should all be empty
        for _ in range(5):
            result = detector.detect(frame)
            assert isinstance(result, FrameDetections)
            assert len(result.detections) == 0
