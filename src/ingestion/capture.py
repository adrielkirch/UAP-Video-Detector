"""
OpenCV capture wrapper for injectable video frame reading.

Provides testable abstraction over cv2.VideoCapture with proper
resource management and error handling.
"""

import cv2
import numpy as np
from typing import Optional


class VideoCaptureWrapper:
    """
    Injectable wrapper around OpenCV VideoCapture.

    Provides clean interface for frame reading with proper resource
    management and error handling for testing and production use.
    """

    def __init__(self, video_path: str):
        """
        Initialize video capture wrapper.

        Args:
            video_path: Path to video file to open

        Raises:
            RuntimeError: If video cannot be opened
        """
        self.video_path = video_path
        self._cap = cv2.VideoCapture(video_path)

        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        # Cache video properties
        self.frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self._cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read_frame_at(self, frame_index: int) -> Optional[np.ndarray]:
        """
        Read frame at specific index.

        Args:
            frame_index: Zero-based frame index to read

        Returns:
            Frame as BGR numpy array, or None if read fails
        """
        if not self._cap.isOpened():
            return None

        # Clamp frame index to valid range
        frame_index = max(0, min(frame_index, self.frame_count - 1))

        # Seek to frame
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        # Read frame
        ret, frame = self._cap.read()
        if ret:
            return frame
        else:
            return None

    def read_next_frame(self) -> Optional[np.ndarray]:
        """
        Read next sequential frame.

        Returns:
            Frame as BGR numpy array, or None if read fails
        """
        if not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()
        return frame if ret else None

    def get_current_position(self) -> int:
        """
        Get current frame position.

        Returns:
            Current frame index
        """
        if not self._cap.isOpened():
            return 0

        return int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))

    def seek_to_frame(self, frame_index: int) -> bool:
        """
        Seek to specific frame index.

        Args:
            frame_index: Target frame index

        Returns:
            True if seek successful, False otherwise
        """
        if not self._cap.isOpened():
            return False

        frame_index = max(0, min(frame_index, self.frame_count - 1))
        return self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    def seek_to_time(self, time_ms: float) -> bool:
        """
        Seek to specific time position.

        Args:
            time_ms: Target time in milliseconds

        Returns:
            True if seek successful, False otherwise
        """
        if not self._cap.isOpened():
            return False

        return self._cap.set(cv2.CAP_PROP_POS_MSEC, time_ms)

    def is_opened(self) -> bool:
        """Check if capture is successfully opened."""
        return self._cap.isOpened()

    def release(self) -> None:
        """Release video capture resources."""
        if self._cap:
            self._cap.release()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with resource cleanup."""
        self.release()

    def __del__(self):
        """Ensure resources are released on garbage collection."""
        self.release()
