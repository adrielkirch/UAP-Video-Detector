import cv2
import numpy as np

from .config import StabilizerConfig


class VideoStabilizer:
    """
    Video stabilization pipeline.

    Current implementation provides:
    - Input frame validation
    - Frame preprocessing (grayscale conversion)
    - Feature detection for motion tracking

    Motion estimation and frame stabilization will be implemented
    in future development phases.
    """

    def __init__(self, config: StabilizerConfig) -> None:
        """
        Initialize the video stabilizer.

        Args:
            config: Configuration parameters for the stabilization pipeline.
        """
        self.config = config

    @staticmethod
    def _validate_frame(frame: np.ndarray) -> None:
        """
        Validate the input frame.

        Args:
            frame: Input image frame.

        Raises:
            ValueError: If the frame is None.
            TypeError: If the frame is not a NumPy array.
        """
        if frame is None:
            raise ValueError("Frame cannot be None.")

        if not isinstance(frame, np.ndarray):
            raise TypeError("Frame must be a NumPy ndarray.")

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert a BGR frame to grayscale.

        Args:
            frame: Input BGR frame.

        Returns:
            Grayscale image.
        """
        self._validate_frame(frame)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def detect_features(self, gray_frame: np.ndarray) -> np.ndarray | None:
        """
        Detect feature points suitable for motion tracking.

        Args:
            gray_frame: Grayscale input frame.

        Returns:
            A NumPy array containing detected feature points,
            or None if no suitable features are found.
        """
        self._validate_frame(gray_frame)

        return cv2.goodFeaturesToTrack(
            gray_frame,
            maxCorners=self.config.max_features,
            qualityLevel=self.config.quality_level,
            minDistance=self.config.min_distance,
            blockSize=self.config.block_size,
        )

    def stabilize(self, frame: np.ndarray) -> np.ndarray:
        """
        Stabilize a single video frame.

        This is currently a placeholder implementation that simply
        returns a copy of the input frame. Future versions will
        estimate camera motion and compensate for it.

        Args:
            frame: Input video frame.

        Returns:
            Stabilized frame.
        """
        self._validate_frame(frame)

        return frame.copy()
