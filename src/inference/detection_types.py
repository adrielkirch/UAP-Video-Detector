"""
Detection value objects for aerial object detection results.

Defines immutable data structures for individual detections and
frame-level detection collections per data model specification.
"""

from dataclasses import dataclass
from typing import List, Optional, Union

# Valid aerial object classes per MVP requirements
VALID_CLASS_NAMES = {"airplane", "helicopter", "bird", "drone"}


@dataclass(frozen=True)
class Detection:
    """
    Immutable value object representing a single object detection.

    Attributes:
        class_name: Type of aerial object detected (airplane/helicopter/bird/drone)
        confidence: Detection confidence score between 0.0 and 1.0
        bbox_xyxy: Bounding box coordinates as [x1, y1, x2, y2] in pixels
        track_id: Optional tracking ID for multi-frame association (unused in MVP)
    """

    class_name: str
    confidence: float
    bbox_xyxy: List[Union[int, float]]
    track_id: Optional[int] = None

    def __post_init__(self):
        """Validate detection fields after initialization."""
        # Validate class name
        if self.class_name not in VALID_CLASS_NAMES:
            raise ValueError(
                f"Invalid class_name '{self.class_name}'. "
                f"Must be one of: {', '.join(sorted(VALID_CLASS_NAMES))}"
            )

        # Validate confidence range
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

        # Validate bounding box format
        if len(self.bbox_xyxy) != 4:
            raise ValueError(
                f"bbox_xyxy must contain exactly 4 coordinates, got {len(self.bbox_xyxy)}"
            )

        # Validate bbox coordinates are numeric
        for i, coord in enumerate(self.bbox_xyxy):
            if not isinstance(coord, (int, float)):
                raise ValueError(
                    f"bbox_xyxy coordinates must be numeric, "
                    f"got {type(coord)} at index {i}"
                )


@dataclass(frozen=True)
class FrameDetections:
    """
    Immutable collection of detections for a single video frame.

    Attributes:
        detections: List of Detection objects found in this frame (may be empty)
        frame_index: Zero-based frame number in video sequence (optional)
        timestamp_ms: Approximate timestamp in milliseconds from video start (optional)
    """

    detections: List[Detection]
    frame_index: int = 0
    timestamp_ms: int = 0

    def __post_init__(self):
        """Validate frame detection fields after initialization."""
        # Validate frame index
        if self.frame_index < 0:
            raise ValueError(
                f"frame_index must be non-negative, got {self.frame_index}"
            )

        # Validate timestamp
        if self.timestamp_ms < 0:
            raise ValueError(
                f"timestamp_ms must be non-negative, got {self.timestamp_ms}"
            )

        # Validate all detections are Detection instances
        for i, detection in enumerate(self.detections):
            if not isinstance(detection, Detection):
                raise ValueError(
                    f"All detections must be Detection instances, "
                    f"got {type(detection)} at index {i}"
                )

    def __len__(self) -> int:
        """Return number of detections."""
        return len(self.detections)

    def __iter__(self):
        """Iterate over detections."""
        return iter(self.detections)
