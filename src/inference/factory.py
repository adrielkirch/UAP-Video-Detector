"""
Detector factory for creating appropriate detector instances.

Provides factory pattern for detector creation based on configuration
backend settings with proper error handling and fallback logic.
"""

import os
import tempfile
import yaml
from pathlib import Path

from .detector import AerialDetector, UltralyticsDetector
from .null_detector import NullDetector
from .config import load_detector_config


class DetectorNotReadyError(Exception):
    """Exception raised when detector cannot be created or initialized."""

    pass


class DetectorFactory:
    """
    Factory for creating detector instances based on configuration.

    Supports multiple backends: null, yolo_world, yolov8, yolov9, custom
    with proper error handling and fallback to null detector when appropriate.
    """

    SUPPORTED_BACKENDS = {"null", "yolo_world", "yolov8", "yolov9", "custom"}
    YOLO_BACKENDS = {"yolo_world", "yolov8", "yolov9", "custom"}

    def create_detector(self, config_path: str) -> AerialDetector:
        """
        Create detector instance based on configuration.

        Args:
            config_path: Path to detector configuration file

        Returns:
            AerialDetector instance (NullDetector or UltralyticsDetector)

        Raises:
            DetectorNotReadyError: If detector cannot be created
        """
        try:
            # Load configuration
            config = load_detector_config(config_path)

        except Exception as e:
            raise DetectorNotReadyError(f"Failed to load detector configuration: {e}")

        # Get backend type
        backend = config.get("backend", "null")

        # Handle null backend or missing backend
        if backend == "null" or backend is None:
            return self._create_null_detector(config_path)

        # Validate backend
        if backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported backend '{backend}'. Supported: {', '.join(self.SUPPORTED_BACKENDS)}"
            )

        # Handle YOLO backends
        if backend in self.YOLO_BACKENDS:
            return self._create_yolo_detector(config, backend)

        # Should not reach here
        raise ValueError(f"Backend '{backend}' not implemented")

    def _create_null_detector(self, config_path: str) -> NullDetector:
        """Create null detector instance."""
        detector = NullDetector()
        detector.load(config_path)
        return detector

    def _create_yolo_detector(self, config: dict, backend: str) -> UltralyticsDetector:
        """
        Create YOLO detector instance.

        Args:
            config: Detector configuration dictionary
            backend: YOLO backend type

        Returns:
            UltralyticsDetector instance

        Raises:
            DetectorNotReadyError: If YOLO detector cannot be created
        """
        # Validate weights path
        weights_path = config.get("weights_path")
        if not weights_path:
            raise DetectorNotReadyError(
                f"weights_path is required for backend '{backend}'"
            )

        # Check if weights file exists
        weights_file = Path(weights_path)
        if not weights_file.exists():
            raise DetectorNotReadyError(f"Weights file not found: {weights_path}")

        try:
            # Create UltralyticsDetector
            detector = UltralyticsDetector()

            # Store config temporarily for detector to use

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as temp_file:
                yaml.dump(config, temp_file)
                temp_config_path = temp_file.name

            try:
                detector.load(temp_config_path)
                return detector
            finally:
                # Clean up temp file
                os.unlink(temp_config_path)

        except Exception as e:
            raise DetectorNotReadyError(
                f"Failed to create detector for backend '{backend}': {e}"
            )

    def is_backend_available(self, backend: str) -> bool:
        """
        Check if specified backend is available.

        Args:
            backend: Backend name to check

        Returns:
            True if backend is available, False otherwise
        """
        if backend == "null":
            return True

        if backend in self.YOLO_BACKENDS:
            try:
                # Try importing ultralytics
                import ultralytics

                return True
            except ImportError:
                return False

        return backend in self.SUPPORTED_BACKENDS

    def get_available_backends(self) -> list[str]:
        """
        Get list of available backends on current system.

        Returns:
            List of available backend names
        """
        available = ["null"]  # Always available

        # Check YOLO backends
        try:
            import ultralytics

            available.extend(self.YOLO_BACKENDS)
        except ImportError:
            pass

        return available

    def create_safe_detector(self, config_path: str) -> AerialDetector:
        """
        Create detector with fallback to null detector on errors.

        Args:
            config_path: Path to detector configuration file

        Returns:
            AerialDetector instance (never raises)
        """
        try:
            return self.create_detector(config_path)
        except (DetectorNotReadyError, ValueError, FileNotFoundError):
            # Fall back to null detector on any error
            return self._create_null_detector(config_path)
