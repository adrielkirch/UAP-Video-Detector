"""
Unit tests for detector factory and backend selection.

Tests detector factory functionality for creating appropriate detector
instances based on configuration backend settings.
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

from src.inference.factory import DetectorFactory, DetectorNotReadyError
from src.inference.null_detector import NullDetector


class TestDetectorFactory:
    """Test DetectorFactory backend selection and instantiation."""

    def test_factory_returns_null_detector_when_backend_null(self):
        """Should return NullDetector when backend is null."""
        # Mock config with null backend
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "null",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            factory = DetectorFactory()
            detector = factory.create_detector("config/detector.yaml")

            # Should return NullDetector
            assert isinstance(detector, NullDetector)
            assert detector.is_ready()  # Null detector becomes ready after creation

    def test_factory_returns_null_detector_when_backend_missing(self):
        """Should return NullDetector when backend key is missing."""
        # Mock config without backend key
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            factory = DetectorFactory()
            detector = factory.create_detector("config/detector.yaml")

            # Should default to NullDetector
            assert isinstance(detector, NullDetector)

    def test_factory_raises_error_missing_weights_path(self):
        """Should raise DetectorNotReadyError when weights_path is missing for YOLO backends."""
        # Mock config with yolo backend but no weights
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolov8",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                # Missing weights_path
            }

            factory = DetectorFactory()

            # Should raise DetectorNotReadyError
            with pytest.raises(DetectorNotReadyError, match="weights_path is required"):
                factory.create_detector("config/detector.yaml")

    def test_factory_raises_error_weights_file_not_found(self):
        """Should raise DetectorNotReadyError when weights file doesn't exist."""
        # Mock config with non-existent weights file
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "yolov8",
                "weights_path": "/non/existent/weights.pt",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            factory = DetectorFactory()

            # Should raise DetectorNotReadyError
            with pytest.raises(DetectorNotReadyError, match="Weights file not found"):
                factory.create_detector("config/detector.yaml")

    @patch("ultralytics.YOLO")
    def test_factory_creates_yolov8_detector(self, mock_yolo_class):
        """Should create UltralyticsDetector for yolov8 backend."""
        # Mock YOLO class
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Create temporary weights file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            # Mock config with yolov8 backend
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "yolov8",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                factory = DetectorFactory()
                detector = factory.create_detector("config/detector.yaml")

                # Should return UltralyticsDetector
                from src.inference.detector import UltralyticsDetector

                assert isinstance(detector, UltralyticsDetector)

                # Should have called YOLO with weights path
                mock_yolo_class.assert_called_once_with(temp_weights_path)

        finally:
            # Cleanup temp file
            os.unlink(temp_weights_path)

    @patch("ultralytics.YOLO")
    def test_factory_creates_yolov9_detector(self, mock_yolo_class):
        """Should create UltralyticsDetector for yolov9 backend."""
        # Mock YOLO class
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Create temporary weights file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            # Mock config with yolov9 backend
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "yolov9",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                factory = DetectorFactory()
                detector = factory.create_detector("config/detector.yaml")

                # Should return UltralyticsDetector
                from src.inference.detector import UltralyticsDetector

                assert isinstance(detector, UltralyticsDetector)

                # Should have called YOLO with weights path
                mock_yolo_class.assert_called_once_with(temp_weights_path)

        finally:
            # Cleanup temp file
            os.unlink(temp_weights_path)

    @patch("ultralytics.YOLO")
    def test_factory_creates_yolo_world_detector(self, mock_yolo_class):
        """Should create UltralyticsDetector for yolo_world backend."""
        # Mock YOLO class
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Create temporary weights file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            # Mock config with yolo_world backend
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "yolo_world",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                factory = DetectorFactory()
                detector = factory.create_detector("config/detector.yaml")

                # Should return UltralyticsDetector
                from src.inference.detector import UltralyticsDetector

                assert isinstance(detector, UltralyticsDetector)

                # Should have called YOLO with weights path
                mock_yolo_class.assert_called_once_with(temp_weights_path)

        finally:
            # Cleanup temp file
            os.unlink(temp_weights_path)

    @patch("ultralytics.YOLO")
    def test_factory_creates_custom_detector(self, mock_yolo_class):
        """Should create UltralyticsDetector for custom backend."""
        # Mock YOLO class
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Create temporary weights file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            # Mock config with custom backend
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "custom",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                factory = DetectorFactory()
                detector = factory.create_detector("config/detector.yaml")

                # Should return UltralyticsDetector
                from src.inference.detector import UltralyticsDetector

                assert isinstance(detector, UltralyticsDetector)

                # Should have called YOLO with weights path
                mock_yolo_class.assert_called_once_with(temp_weights_path)

        finally:
            # Cleanup temp file
            os.unlink(temp_weights_path)

    def test_factory_raises_error_invalid_backend(self):
        """Should raise error for unsupported backend types."""
        # Mock config with invalid backend
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.return_value = {
                "backend": "unsupported_backend",
                "confidence_threshold": 0.25,
                "class_prompts": ["airplane", "helicopter", "bird", "drone"],
            }

            factory = DetectorFactory()

            # Should raise ValueError for unsupported backend
            with pytest.raises(ValueError, match="Unsupported backend"):
                factory.create_detector("config/detector.yaml")

    def test_factory_handles_config_loading_errors(self):
        """Should handle configuration loading errors gracefully."""
        # Mock config loading failure
        with patch("src.inference.factory.load_detector_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Config file not found")

            factory = DetectorFactory()

            # Should raise DetectorNotReadyError
            with pytest.raises(
                DetectorNotReadyError, match="Failed to load detector configuration"
            ):
                factory.create_detector("config/detector.yaml")

    @patch("ultralytics.YOLO")
    def test_factory_handles_yolo_loading_errors(self, mock_yolo_class):
        """Should handle YOLO model loading errors gracefully."""
        # Mock YOLO loading failure
        mock_yolo_class.side_effect = Exception("Failed to load YOLO model")

        # Create temporary weights file
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp_file:
            temp_weights_path = temp_file.name

        try:
            # Mock config with yolov8 backend
            with patch("src.inference.factory.load_detector_config") as mock_config:
                mock_config.return_value = {
                    "backend": "yolov8",
                    "weights_path": temp_weights_path,
                    "confidence_threshold": 0.25,
                    "class_prompts": ["airplane", "helicopter", "bird", "drone"],
                }

                factory = DetectorFactory()

                # Should raise DetectorNotReadyError
                with pytest.raises(
                    DetectorNotReadyError, match="Failed to create detector"
                ):
                    factory.create_detector("config/detector.yaml")

        finally:
            # Cleanup temp file
            os.unlink(temp_weights_path)
