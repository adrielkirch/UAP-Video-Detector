"""
Detection overlay drawing helpers for video frames.

Provides functions for rendering bounding boxes, labels, and statistics
on video frames with proper visual formatting and error handling.
"""

import cv2
import numpy as np
from typing import Tuple, Optional

from ...inference.detection_types import Detection, FrameDetections

# Color palette for different classes (BGR format for OpenCV)
CLASS_COLORS = {
    "airplane": (0, 255, 0),  # Green
    "helicopter": (255, 0, 0),  # Blue
    "bird": (0, 255, 255),  # Yellow
    "drone": (255, 0, 255),  # Magenta
}

# Default color for unknown classes
DEFAULT_COLOR = (128, 128, 128)  # Gray


def get_class_color(class_name: str) -> Tuple[int, int, int]:
    """
    Get consistent color for detection class.

    Args:
        class_name: Name of detected class

    Returns:
        BGR color tuple for OpenCV
    """
    return CLASS_COLORS.get(class_name.lower(), DEFAULT_COLOR)


def format_detection_label(detection: Detection) -> str:
    """
    Format detection label with class name and confidence.

    Args:
        detection: Detection object

    Returns:
        Formatted label string (e.g., "airplane: 85.7%")
    """
    confidence_pct = detection.confidence * 100
    return f"{detection.class_name}: {confidence_pct:.1f}%"


def draw_bounding_box(
    frame: np.ndarray,
    detection: Detection,
    color: Tuple[int, int, int],
    thickness: int = 2,
) -> None:
    """
    Draw bounding box on frame.

    Args:
        frame: Video frame to draw on (modified in-place)
        detection: Detection with bbox coordinates
        color: BGR color tuple
        thickness: Line thickness for rectangle
    """
    x1, y1, x2, y2 = detection.bbox_xyxy

    # Draw rectangle
    cv2.rectangle(
        frame,
        (int(x1), int(y1)),  # Top-left corner
        (int(x2), int(y2)),  # Bottom-right corner
        color,
        thickness,
    )


def draw_detection_label(
    frame: np.ndarray, detection: Detection, color: Tuple[int, int, int]
) -> None:
    """
    Draw detection label on frame.

    Args:
        frame: Video frame to draw on (modified in-place)
        detection: Detection object
        color: BGR color tuple for text
    """
    x1, y1, x2, y2 = detection.bbox_xyxy
    label = format_detection_label(detection)

    # Calculate label position (above bounding box)
    label_y = max(y1 - 10, 20)  # Ensure label stays in frame

    # Get text size for background rectangle
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1

    (text_width, text_height), baseline = cv2.getTextSize(
        label, font, font_scale, thickness
    )

    # Draw background rectangle for label
    cv2.rectangle(
        frame,
        (int(x1), int(label_y - text_height - 5)),
        (int(x1 + text_width + 10), int(label_y + 5)),
        color,
        -1,  # Filled rectangle
    )

    # Draw text
    cv2.putText(
        frame,
        label,
        (int(x1 + 5), int(label_y)),
        font,
        font_scale,
        (255, 255, 255),  # White text
        thickness,
    )


def draw_detections_on_frame(
    frame: np.ndarray, detections: Optional[FrameDetections]
) -> np.ndarray:
    """
    Draw all detections on video frame with overlays.

    Args:
        frame: Video frame to draw on (modified in-place)
        detections: FrameDetections to render, or None

    Returns:
        Modified frame (same object as input)
    """
    if detections is None or len(detections.detections) == 0:
        return frame

    # Draw each detection
    for detection in detections.detections:
        color = get_class_color(detection.class_name)

        # Draw bounding box
        draw_bounding_box(frame, detection, color, thickness=2)

        # Draw label
        draw_detection_label(frame, detection, color)

    return frame


def draw_detection_stats(
    frame: np.ndarray, detections: Optional[FrameDetections]
) -> None:
    """
    Draw detection statistics on frame.

    Args:
        frame: Video frame to draw on (modified in-place)
        detections: FrameDetections for statistics
    """
    if detections is None:
        detections = FrameDetections([])

    # Calculate statistics
    total_count = len(detections.detections)

    # Count by class
    class_counts = {}
    for detection in detections.detections:
        class_name = detection.class_name
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

    # Draw statistics in top-left corner
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1

    y_offset = 30
    line_height = 25

    # Total count
    if total_count == 0:
        stats_text = "No detections"
    else:
        stats_text = f"{total_count} detections found"

    cv2.putText(
        frame,
        stats_text,
        (10, y_offset),
        font,
        font_scale,
        (255, 255, 255),  # White text
        thickness,
    )

    # Class breakdown
    if total_count > 0:
        y_offset += line_height

        for class_name, count in sorted(class_counts.items()):
            class_text = f"  {class_name}: {count}"
            color = get_class_color(class_name)

            cv2.putText(
                frame, class_text, (10, y_offset), font, font_scale, color, thickness
            )

            y_offset += line_height


def draw_scan_status(
    frame: np.ndarray, is_scanning: bool, lag_warning: Optional[str] = None
) -> None:
    """
    Draw scan status indicator on frame.

    Args:
        frame: Video frame to draw on (modified in-place)
        is_scanning: Whether scanning is currently enabled
        lag_warning: Optional lag warning message
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1

    # Draw scan status in top-right corner
    frame_height, frame_width = frame.shape[:2]

    # Status text and color
    if is_scanning:
        status_text = "🔍 SCANNING"
        status_color = (0, 255, 0)  # Green
    else:
        status_text = "⏸️ SCAN OFF"
        status_color = (128, 128, 128)  # Gray

    # Calculate text position (right-aligned)
    (text_width, text_height), _ = cv2.getTextSize(
        status_text, font, font_scale, thickness
    )

    x_pos = frame_width - text_width - 10
    y_pos = 30

    cv2.putText(
        frame, status_text, (x_pos, y_pos), font, font_scale, status_color, thickness
    )

    # Draw lag warning if present
    if lag_warning:
        y_pos += 25
        warning_text = "⚠️ LAG"

        (warn_width, warn_height), _ = cv2.getTextSize(
            warning_text, font, font_scale, thickness
        )

        x_pos = frame_width - warn_width - 10

        cv2.putText(
            frame,
            warning_text,
            (x_pos, y_pos),
            font,
            font_scale,
            (0, 0, 255),  # Red
            thickness,
        )
