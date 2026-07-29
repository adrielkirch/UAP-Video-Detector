"""
Unit tests for Detection and FrameDetections value objects.

Tests for core detection data structures that represent individual
object detections and collections of detections per frame.
"""

import pytest
from dataclasses import FrozenInstanceError

from src.inference.detection_types import Detection, FrameDetections


class TestDetection:
    """Test individual detection value object."""

    def test_detection_creation_with_valid_data(self):
        """Should create Detection with all required fields."""
        detection = Detection(
            class_name="airplane",
            confidence=0.85,
            bbox_xyxy=[100, 200, 300, 400],
            track_id=None,
        )

        assert detection.class_name == "airplane"
        assert detection.confidence == 0.85
        assert detection.bbox_xyxy == [100, 200, 300, 400]
        assert detection.track_id is None

    def test_detection_validates_confidence_range(self):
        """Should validate confidence is between 0.0 and 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Detection(
                class_name="bird",
                confidence=1.5,  # Invalid: > 1.0
                bbox_xyxy=[0, 0, 100, 100],
                track_id=None,
            )

        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Detection(
                class_name="bird",
                confidence=-0.1,  # Invalid: < 0.0
                bbox_xyxy=[0, 0, 100, 100],
                track_id=None,
            )

    def test_detection_validates_class_name_enum(self):
        """Should validate class_name is one of the allowed aerial objects."""
        # Valid class names should work
        valid_classes = ["airplane", "helicopter", "bird", "drone"]
        for class_name in valid_classes:
            detection = Detection(
                class_name=class_name,
                confidence=0.5,
                bbox_xyxy=[0, 0, 100, 100],
                track_id=None,
            )
            assert detection.class_name == class_name

        # Invalid class name should raise error
        with pytest.raises(ValueError, match="Invalid class_name"):
            Detection(
                class_name="car",  # Not an aerial object
                confidence=0.5,
                bbox_xyxy=[0, 0, 100, 100],
                track_id=None,
            )

    def test_detection_validates_bbox_format(self):
        """Should validate bbox_xyxy has exactly 4 numeric coordinates."""
        # Valid bbox
        Detection(
            class_name="airplane",
            confidence=0.5,
            bbox_xyxy=[10.5, 20.0, 100, 200],  # Mixed int/float OK
            track_id=None,
        )

        # Invalid bbox: wrong length
        with pytest.raises(
            ValueError, match="bbox_xyxy must contain exactly 4 coordinates"
        ):
            Detection(
                class_name="airplane",
                confidence=0.5,
                bbox_xyxy=[10, 20, 100],  # Only 3 coordinates
                track_id=None,
            )

        # Invalid bbox: non-numeric
        with pytest.raises(ValueError, match="bbox_xyxy coordinates must be numeric"):
            Detection(
                class_name="airplane",
                confidence=0.5,
                bbox_xyxy=[10, 20, "100", 200],  # String coordinate
                track_id=None,
            )

    def test_detection_is_immutable(self):
        """Should be immutable value object (frozen dataclass)."""
        detection = Detection(
            class_name="helicopter",
            confidence=0.75,
            bbox_xyxy=[50, 60, 150, 160],
            track_id=42,
        )

        # Should not be able to modify fields
        with pytest.raises(FrozenInstanceError):
            detection.confidence = 0.8

        with pytest.raises(FrozenInstanceError):
            detection.class_name = "airplane"


class TestFrameDetections:
    """Test collection of detections for a single frame."""

    def test_frame_detections_creation_with_valid_data(self):
        """Should create FrameDetections with frame metadata and detection list."""
        detection1 = Detection("airplane", 0.9, [10, 20, 100, 200], None)
        detection2 = Detection("bird", 0.6, [200, 300, 250, 350], None)

        frame_detections = FrameDetections(
            detections=[detection1, detection2], frame_index=42, timestamp_ms=5000
        )

        assert frame_detections.frame_index == 42
        assert frame_detections.timestamp_ms == 5000
        assert len(frame_detections) == 2
        assert list(frame_detections)[0] == detection1
        assert list(frame_detections)[1] == detection2

    def test_frame_detections_with_empty_items_list(self):
        """Should accept empty detection list for frames with no objects."""
        frame_detections = FrameDetections(
            detections=[], frame_index=10, timestamp_ms=1000
        )

        assert frame_detections.frame_index == 10
        assert frame_detections.timestamp_ms == 1000
        assert len(frame_detections) == 0
        assert list(frame_detections) == []

    def test_frame_detections_validates_frame_index_non_negative(self):
        """Should validate frame_index is non-negative."""
        with pytest.raises(ValueError, match="frame_index must be non-negative"):
            FrameDetections(detections=[], frame_index=-1, timestamp_ms=1000)  # Invalid

    def test_frame_detections_validates_timestamp_non_negative(self):
        """Should validate timestamp_ms is non-negative."""
        with pytest.raises(ValueError, match="timestamp_ms must be non-negative"):
            FrameDetections(detections=[], frame_index=0, timestamp_ms=-100)  # Invalid

    def test_frame_detections_validates_items_are_detections(self):
        """Should validate all items are Detection instances."""
        valid_detection = Detection("drone", 0.7, [0, 0, 50, 50], None)

        # Valid case
        FrameDetections(detections=[valid_detection], frame_index=0, timestamp_ms=0)

        # Invalid case: non-Detection in items
        with pytest.raises(
            ValueError, match="All detections must be Detection instances"
        ):
            FrameDetections(
                detections=[valid_detection, "not_a_detection"],
                frame_index=0,
                timestamp_ms=0,
            )

    def test_frame_detections_is_immutable(self):
        """Should be immutable value object."""
        detection = Detection("airplane", 0.8, [10, 20, 100, 200], None)
        frame_detections = FrameDetections(
            detections=[detection], frame_index=5, timestamp_ms=2500
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            frame_detections.frame_index = 10
