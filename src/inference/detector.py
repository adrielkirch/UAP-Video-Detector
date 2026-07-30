"""
Aerial object detector protocol and Ultralytics implementation.

Provides abstract detector interface and YOLO-based implementation
for aerial object detection with filtering and confidence thresholding.
"""

from abc import ABC, abstractmethod
import numpy as np

from .detection_types import Detection, FrameDetections
from .config import load_detector_config


class DetectorError(Exception):
    """Exception raised when detector operations fail."""

    pass


class AerialDetector(ABC):
    """
    Abstract protocol for aerial object detection.

    Defines the contract for all detector implementations with
    standardized interface for loading, detection, and resource management.
    """

    @abstractmethod
    def load(self, config_path: str) -> None:
        """
        Load detector model from configuration.

        Args:
            config_path: Path to detector configuration file

        Raises:
            DetectorError: If loading fails
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """
        Check if detector is loaded and ready for inference.

        Returns:
            True if detector is ready, False otherwise
        """
        pass

    @abstractmethod
    def detect(self, frame: np.ndarray) -> FrameDetections:
        """
        Detect aerial objects in video frame.

        Args:
            frame: Video frame as numpy array (BGR format)

        Returns:
            FrameDetections containing filtered aerial objects

        Raises:
            DetectorError: If detector not ready or inference fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release detector resources and cleanup."""
        pass


class UltralyticsDetector(AerialDetector):
    """
    Ultralytics YOLO implementation of aerial detector.

    Supports YOLOv8, YOLOv9, and YOLO-World models with aerial object
    filtering and confidence thresholding per project constitution.
    """

    def __init__(self):
        """Initialize Ultralytics detector."""
        self._model = None
        self._config = None
        self._aerial_classes = {"airplane", "helicopter", "bird", "drone"}

    def load(self, config_path: str) -> None:
        """
        Load YOLO model from configuration.

        Args:
            config_path: Path to detector.yaml configuration

        Raises:
            DetectorError: If model loading fails
        """
        try:
            # Load configuration
            self._config = load_detector_config(config_path)

            # Import ultralytics (lazy import for testing)
            from ultralytics import YOLO

            # Load model with weights
            weights_path = self._config.get("weights_path")
            if not weights_path:
                raise DetectorError("No weights_path specified in configuration")

            self._model = YOLO(weights_path)

        except Exception as e:
            raise DetectorError(f"Failed to load detector: {e}")

    def is_ready(self) -> bool:
        """Check if YOLO model is loaded and ready."""
        return self._model is not None and self._config is not None

    def detect(self, frame: np.ndarray) -> FrameDetections:
        """
        Detect aerial objects using YOLO inference.

        Args:
            frame: Video frame as numpy array (BGR format)

        Returns:
            FrameDetections with filtered aerial objects above confidence threshold

        Raises:
            DetectorError: If detector not ready
        """
        if not self.is_ready():
            raise DetectorError("Detector not ready. Call load() first.")

        try:
            # Run YOLO inference
            results = self._model(frame)

            # Extract detections
            detections = []

            if results and len(results) > 0:
                result = results[0]  # First (and typically only) result

                if hasattr(result, "boxes") and result.boxes is not None:
                    boxes = result.boxes.data
                    names = result.names

                    # Process each detection
                    for box in boxes:
                        if len(box) >= 6:  # x1, y1, x2, y2, confidence, class_id
                            x1, y1, x2, y2, confidence, class_id = box[:6]

                            # Get class name
                            class_name = names.get(
                                int(class_id), f"class_{int(class_id)}"
                            )

                            # Filter by aerial classes
                            if class_name.lower() in self._aerial_classes:
                                # Filter by confidence threshold
                                conf_threshold = self._config.get(
                                    "confidence_threshold", 0.25
                                )
                                if float(confidence) >= conf_threshold:
                                    detection = Detection(
                                        class_name=class_name.lower(),
                                        confidence=float(confidence),
                                        bbox_xyxy=[int(x1), int(y1), int(x2), int(y2)],
                                        track_id=None,
                                    )
                                    detections.append(detection)

            return FrameDetections(detections)

        except Exception as e:
            raise DetectorError(f"Detection inference failed: {e}")

    def close(self) -> None:
        """Release YOLO model resources."""
        if self._model is not None:
            # Clear model reference
            self._model = None

        self._config = None
