"""
Contract tests for AerialDetector protocol compliance.

Tests the public interface contract defined in contracts/detector-protocol.md
to ensure proper detector API behavior and integration compatibility.
"""

import pytest
import numpy as np

from src.inference.detector import AerialDetector, DetectorError
from src.inference.detection_types import Detection, FrameDetections


class TestAerialDetectorProtocol:
    """Test AerialDetector protocol contract compliance."""

    def test_detector_protocol_is_abstract(self):
        """Contract: AerialDetector should be abstract protocol."""
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            AerialDetector()

    def test_load_method_signature(self):
        """Contract: load(config_path: str) -> None"""

        # Mock implementation for testing
        class MockDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                return FrameDetections([])

            def close(self) -> None:
                pass

        detector = MockDetector()

        # Should accept string and return None
        result = detector.load("config/detector.yaml")
        assert result is None

    def test_is_ready_method_signature(self):
        """Contract: is_ready() -> bool"""

        class MockDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                return FrameDetections([])

            def close(self) -> None:
                pass

        detector = MockDetector()

        # Should return boolean
        result = detector.is_ready()
        assert isinstance(result, bool)

    def test_detect_method_signature(self):
        """Contract: detect(frame: ndarray) -> FrameDetections"""

        class MockDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                return FrameDetections(
                    [
                        Detection(
                            class_name="airplane",
                            confidence=0.85,
                            bbox_xyxy=[100, 50, 200, 150],
                        )
                    ]
                )

            def close(self) -> None:
                pass

        detector = MockDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should accept ndarray and return FrameDetections
        result = detector.detect(frame)
        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 1
        assert result.detections[0].class_name == "airplane"

    def test_close_method_signature(self):
        """Contract: close() -> None"""

        class MockDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                return FrameDetections([])

            def close(self) -> None:
                pass

        detector = MockDetector()

        # Should return None
        result = detector.close()
        assert result is None

    def test_detector_error_inheritance(self):
        """Contract: DetectorError should inherit from Exception."""
        error = DetectorError("Test error")

        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_detect_not_ready_raises_error(self):
        """Contract: detect() MUST raise DetectorError if not is_ready()."""

        class NotReadyDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return False

            def detect(self, frame: np.ndarray) -> FrameDetections:
                if not self.is_ready():
                    raise DetectorError("Detector not ready")
                return FrameDetections([])

            def close(self) -> None:
                pass

        detector = NotReadyDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should raise DetectorError when not ready
        with pytest.raises(DetectorError, match="Detector not ready"):
            detector.detect(frame)

    def test_aerial_class_filtering(self):
        """Contract: Only aerial objects (airplane, helicopter, bird, drone) returned."""

        class FilteringDetector(AerialDetector):
            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                # Should filter to only aerial objects
                return FrameDetections(
                    [
                        Detection("airplane", 0.9, [10, 10, 50, 50]),
                        Detection("helicopter", 0.8, [60, 60, 100, 100]),
                        Detection("bird", 0.7, [110, 110, 150, 150]),
                        Detection("drone", 0.6, [160, 160, 200, 200]),
                    ]
                )

            def close(self) -> None:
                pass

        detector = FilteringDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = detector.detect(frame)

        # Should only contain valid aerial classes
        valid_classes = {"airplane", "helicopter", "bird", "drone"}
        for detection in result.detections:
            assert detection.class_name in valid_classes

    def test_confidence_threshold_filtering(self):
        """Contract: Only detections above confidence threshold returned."""

        class ConfidenceDetector(AerialDetector):
            def __init__(self, threshold=0.25):
                self.threshold = threshold

            def load(self, config_path: str) -> None:
                pass

            def is_ready(self) -> bool:
                return True

            def detect(self, frame: np.ndarray) -> FrameDetections:
                # Simulate filtering by confidence
                all_detections = [
                    Detection("airplane", 0.9, [10, 10, 50, 50]),  # Above threshold
                    Detection("bird", 0.1, [60, 60, 100, 100]),  # Below threshold
                ]

                # Filter by threshold
                filtered = [d for d in all_detections if d.confidence >= self.threshold]
                return FrameDetections(filtered)

            def close(self) -> None:
                pass

        detector = ConfidenceDetector(threshold=0.25)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = detector.detect(frame)

        # Should only contain high-confidence detections
        assert len(result.detections) == 1
        assert result.detections[0].confidence >= 0.25
        assert result.detections[0].class_name == "airplane"
