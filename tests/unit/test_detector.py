"""
Unit tests for Ultralytics adapter class filter and confidence.

Tests YOLO detector implementation with mocked ultralytics to avoid
weight downloads while verifying filtering and confidence logic.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from src.inference.detector import UltralyticsDetector, DetectorError
from src.inference.detection_types import FrameDetections


class TestUltralyticsDetector:
    """Test Ultralytics YOLO adapter filtering and confidence."""

    def test_detector_initial_state(self):
        """Should start in not-ready state."""
        detector = UltralyticsDetector()

        assert not detector.is_ready()

    @patch("ultralytics.YOLO")
    def test_load_initializes_model(self, mock_yolo_class):
        """Should initialize YOLO model from config."""
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        detector = UltralyticsDetector()

        # Mock config loading
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        # Should have called YOLO with weights path
        mock_yolo_class.assert_called_once_with("models/yolov8s-world.pt")
        assert detector.is_ready()

    @patch("ultralytics.YOLO")
    def test_detect_when_not_ready_raises_error(self, mock_yolo_class):
        """Should raise DetectorError when detect() called before load()."""
        detector = UltralyticsDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should raise error when not ready
        with pytest.raises(DetectorError, match="Detector not ready"):
            detector.detect(frame)

    @patch("ultralytics.YOLO")
    def test_detect_filters_aerial_objects_only(self, mock_yolo_class):
        """Should filter results to only aerial objects."""
        # Mock YOLO model and results
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Mock detection results with mixed classes
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.data = np.array(
            [
                [10, 10, 50, 50, 0.9, 0],  # class 0: airplane (keep)
                [60, 60, 100, 100, 0.8, 1],  # class 1: helicopter (keep)
                [110, 110, 150, 150, 0.7, 2],  # class 2: car (filter out)
                [160, 160, 200, 200, 0.6, 3],  # class 3: person (filter out)
            ]
        )
        mock_result.names = {0: "airplane", 1: "helicopter", 2: "car", 3: "person"}
        mock_model.return_value = [mock_result]

        detector = UltralyticsDetector()

        # Mock config loading
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should filter to only aerial objects
        result = detector.detect(frame)

        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 2  # Only airplane and helicopter

        # Check filtered results
        classes = [det.class_name for det in result.detections]
        assert "airplane" in classes
        assert "helicopter" in classes
        assert "car" not in classes
        assert "person" not in classes

    @patch("ultralytics.YOLO")
    def test_detect_filters_by_confidence_threshold(self, mock_yolo_class):
        """Should filter results by confidence threshold."""
        # Mock YOLO model and results
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Mock detection results with varying confidence
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.data = np.array(
            [
                [10, 10, 50, 50, 0.9, 0],  # High confidence airplane (keep)
                [60, 60, 100, 100, 0.15, 1],  # Low confidence helicopter (filter)
                [110, 110, 150, 150, 0.8, 2],  # High confidence bird (keep)
                [160, 160, 200, 200, 0.05, 3],  # Very low confidence drone (filter)
            ]
        )
        mock_result.names = {0: "airplane", 1: "helicopter", 2: "bird", 3: "drone"}
        mock_model.return_value = [mock_result]

        detector = UltralyticsDetector()

        # Mock config with 0.25 threshold
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,  # Only >= 0.25 should pass
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should filter by confidence threshold
        result = detector.detect(frame)

        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 2  # Only airplane (0.9) and bird (0.8)

        # Check confidence filtering
        for detection in result.detections:
            assert detection.confidence >= 0.25

        classes = [det.class_name for det in result.detections]
        assert "airplane" in classes
        assert "bird" in classes

    @patch("ultralytics.YOLO")
    def test_detect_converts_bbox_format(self, mock_yolo_class):
        """Should convert bounding boxes to correct format."""
        # Mock YOLO model and results
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Mock detection result with specific bbox
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.data = np.array(
            [[100, 50, 200, 150, 0.85, 0]]  # x1, y1, x2, y2, conf, class
        )
        mock_result.names = {0: "airplane"}
        mock_model.return_value = [mock_result]

        detector = UltralyticsDetector()

        # Mock config loading
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = detector.detect(frame)

        assert len(result.detections) == 1
        detection = result.detections[0]

        # Should preserve XYXY format
        assert detection.bbox_xyxy == [100, 50, 200, 150]
        assert detection.class_name == "airplane"
        assert detection.confidence == 0.85

    @patch("ultralytics.YOLO")
    def test_close_releases_model(self, mock_yolo_class):
        """Should release model resources on close()."""
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        detector = UltralyticsDetector()

        # Mock config loading
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        assert detector.is_ready()

        # Close should clean up
        detector.close()

        assert not detector.is_ready()

    @patch("ultralytics.YOLO")
    def test_detect_empty_results(self, mock_yolo_class):
        """Should handle empty detection results gracefully."""
        # Mock YOLO model with empty results
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.data = np.array([]).reshape(0, 6)  # Empty array
        mock_result.names = {}
        mock_model.return_value = [mock_result]

        detector = UltralyticsDetector()

        # Mock config loading
        with patch("src.inference.detector.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolo_world",
                "weights_path": "models/yolov8s-world.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            detector.load("config/detector.yaml")

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should handle empty results
        result = detector.detect(frame)

        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 0
