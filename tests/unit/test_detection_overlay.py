"""
Unit tests for detection overlay rendering helpers.

Tests overlay drawing functions for bounding boxes, labels, and confidence
scores with proper visual formatting and error handling.
"""

from unittest.mock import patch
import numpy as np

from src.ui.components.detection_overlay import (
    draw_detections_on_frame,
    format_detection_label,
    get_class_color,
    draw_bounding_box,
    draw_detection_stats,
)
from src.inference.detection_types import Detection, FrameDetections


class TestDetectionOverlay:
    """Test detection overlay drawing helpers."""

    def test_format_detection_label_with_confidence(self):
        """Should format detection label with class name and confidence."""
        detection = Detection(
            class_name="airplane", confidence=0.857, bbox_xyxy=[10, 10, 50, 50]
        )

        # Should format with rounded confidence
        label = format_detection_label(detection)

        assert label == "airplane: 85.7%"

    def test_format_detection_label_rounds_confidence(self):
        """Should round confidence to 1 decimal place."""
        detection = Detection(
            class_name="helicopter", confidence=0.923456, bbox_xyxy=[10, 10, 50, 50]
        )

        label = format_detection_label(detection)

        assert label == "helicopter: 92.3%"

    def test_get_class_color_returns_consistent_colors(self):
        """Should return consistent colors for each class."""
        # Should return same color for same class
        color1 = get_class_color("airplane")
        color2 = get_class_color("airplane")

        assert color1 == color2

        # Should return different colors for different classes
        airplane_color = get_class_color("airplane")
        helicopter_color = get_class_color("helicopter")

        assert airplane_color != helicopter_color

    def test_get_class_color_returns_bgr_format(self):
        """Should return colors in BGR format for OpenCV."""
        color = get_class_color("bird")

        # Should be tuple of 3 integers (B, G, R)
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(isinstance(c, int) for c in color)
        assert all(0 <= c <= 255 for c in color)

    def test_draw_bounding_box_calls_opencv(self):
        """Should call OpenCV rectangle function with correct parameters."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detection = Detection(
            class_name="drone", confidence=0.75, bbox_xyxy=[100, 50, 200, 150]
        )

        with patch("cv2.rectangle") as mock_rectangle:
            draw_bounding_box(frame, detection, color=(0, 255, 0), thickness=2)

        # Should call cv2.rectangle with correct parameters
        mock_rectangle.assert_called_once_with(
            frame,
            (100, 50),  # Top-left corner
            (200, 150),  # Bottom-right corner
            (0, 255, 0),  # Color
            2,  # Thickness
        )

    def test_draw_detections_on_frame_with_multiple_detections(self):
        """Should draw all detections on frame with overlays."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        detections = FrameDetections(
            [
                Detection("airplane", 0.9, [10, 10, 100, 80]),
                Detection("helicopter", 0.8, [200, 200, 300, 280]),
                Detection("bird", 0.7, [400, 100, 450, 150]),
            ]
        )

        with patch("cv2.rectangle") as mock_rectangle, patch(
            "cv2.putText"
        ) as mock_puttext:

            result_frame = draw_detections_on_frame(frame, detections)

        # Should draw 3 bounding boxes + 3 label backgrounds = 6 rectangle calls
        assert mock_rectangle.call_count == 6

        # Should draw 3 labels
        assert mock_puttext.call_count == 3

        # Should return the same frame (modified in place)
        assert result_frame is frame

    def test_draw_detections_on_frame_with_empty_detections(self):
        """Should handle empty detections gracefully."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        empty_detections = FrameDetections([])

        with patch("cv2.rectangle") as mock_rectangle, patch(
            "cv2.putText"
        ) as mock_puttext:

            result_frame = draw_detections_on_frame(frame, empty_detections)

        # Should not draw anything for empty detections
        mock_rectangle.assert_not_called()
        mock_puttext.assert_not_called()

        # Should still return frame
        assert result_frame is frame

    def test_draw_detections_on_frame_with_none_input(self):
        """Should handle None detections gracefully."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch("cv2.rectangle") as mock_rectangle, patch(
            "cv2.putText"
        ) as mock_puttext:

            result_frame = draw_detections_on_frame(frame, None)

        # Should not draw anything for None detections
        mock_rectangle.assert_not_called()
        mock_puttext.assert_not_called()

        # Should still return frame
        assert result_frame is frame

    def test_draw_detection_stats_shows_count_and_classes(self):
        """Should display detection statistics on frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        detections = FrameDetections(
            [
                Detection("airplane", 0.9, [10, 10, 100, 80]),
                Detection("airplane", 0.8, [200, 200, 300, 280]),
                Detection("helicopter", 0.7, [400, 100, 450, 150]),
            ]
        )

        with patch("cv2.putText") as mock_puttext:
            draw_detection_stats(frame, detections)

        # Should draw multiple text lines for stats
        assert mock_puttext.call_count >= 2

        # Check that stats include count and class breakdown
        calls = mock_puttext.call_args_list
        text_contents = [call[0][1] for call in calls]  # Extract text content

        # Should show total count
        assert any("3 detections" in text.lower() for text in text_contents)

        # Should show class breakdown
        assert any("airplane" in text.lower() for text in text_contents)
        assert any("helicopter" in text.lower() for text in text_contents)

    def test_draw_detection_stats_with_empty_detections(self):
        """Should show appropriate message for no detections."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        empty_detections = FrameDetections([])

        with patch("cv2.putText") as mock_puttext:
            draw_detection_stats(frame, empty_detections)

        # Should draw at least one text line
        assert mock_puttext.call_count >= 1

        # Should indicate no detections
        calls = mock_puttext.call_args_list
        text_contents = [call[0][1] for call in calls]
        assert any(
            "no detections" in text.lower() or "0 detections" in text.lower()
            for text in text_contents
        )

    def test_overlay_handles_edge_bbox_coordinates(self):
        """Should handle bounding boxes at frame edges gracefully."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Detection with bbox at frame edges
        detection = Detection(
            class_name="bird",
            confidence=0.6,
            bbox_xyxy=[0, 0, 640, 480],  # Full frame bbox
        )
        detections = FrameDetections([detection])

        with patch("cv2.rectangle") as mock_rectangle, patch(
            "cv2.putText"
        ) as mock_puttext:

            # Should handle edge coordinates without error
            result_frame = draw_detections_on_frame(frame, detections)

        # Should draw bounding box + label background (2 calls)
        assert mock_rectangle.call_count == 2
        mock_puttext.assert_called_once()

        assert result_frame is frame

    def test_overlay_handles_invalid_bbox_gracefully(self):
        """Should handle invalid bounding box coordinates gracefully."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Detection with invalid bbox (negative coordinates)
        detection = Detection(
            class_name="drone", confidence=0.5, bbox_xyxy=[-10, -5, 50, 50]
        )
        detections = FrameDetections([detection])

        with patch("cv2.rectangle") as mock_rectangle, patch(
            "cv2.putText"
        ) as mock_puttext:

            # Should handle invalid coordinates without crashing
            result_frame = draw_detections_on_frame(frame, detections)

        # Should draw bounding box + label background (2 calls)
        assert mock_rectangle.call_count == 2
        mock_puttext.assert_called_once()

        assert result_frame is frame
