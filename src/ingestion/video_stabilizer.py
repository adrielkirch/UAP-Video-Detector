import cv2
import numpy as np

from .config import StabilizerConfig


class VideoStabilizer:
    """
    Video stabilization pipeline.

    Current implementation provides:
    - Input frame validation
    - Frame preprocessing (grayscale conversion)
    - Feature detection
    - Feature tracking using Lucas-Kanade Optical Flow
    - Motion estimation using affine transformation

    Frame warping and motion smoothing will be implemented
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
        Validate an input frame.

        Args:
            frame: Input image.

        Raises:
            ValueError: If frame is None.
            TypeError: If frame is not a NumPy array.
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
        Detect feature points suitable for tracking.

        Args:
            gray_frame: Grayscale input frame.

        Returns:
            Detected feature points or None.
        """
        self._validate_frame(gray_frame)

        return cv2.goodFeaturesToTrack(
            gray_frame,
            maxCorners=self.config.max_features,
            qualityLevel=self.config.quality_level,
            minDistance=self.config.min_distance,
            blockSize=self.config.block_size,
        )

    def track_features(
        self,
        previous_frame: np.ndarray,
        current_frame: np.ndarray,
        previous_points: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Track feature points between two frames using
        Lucas-Kanade Optical Flow.

        Args:
            previous_frame: Previous grayscale frame.
            current_frame: Current grayscale frame.
            previous_points: Feature points detected in the previous frame.

        Returns:
            Tuple containing matched old and new feature points.
        """
        self._validate_frame(previous_frame)
        self._validate_frame(current_frame)

        if previous_points is None:
            raise ValueError("Previous feature points cannot be None.")

        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            previous_frame,
            current_frame,
            previous_points,
            None,
        )

        if next_points is None or status is None:
            return np.empty((0, 2)), np.empty((0, 2))

        good_old = previous_points[status.flatten() == 1]
        good_new = next_points[status.flatten() == 1]

        return good_old, good_new

    def estimate_motion(
        self,
        old_points: np.ndarray,
        new_points: np.ndarray,
    ) -> np.ndarray:
        """
        Estimate camera motion using an affine transformation.

        Args:
            old_points: Feature points from the previous frame.
            new_points: Matching feature points from the current frame.

        Returns:
            2x3 affine transformation matrix.

        Raises:
            ValueError:
                If there are fewer than three matching points or
                the transform cannot be estimated.
        """
        if old_points is None or new_points is None:
            raise ValueError("Feature points cannot be None.")

        if len(old_points) < 3 or len(new_points) < 3:
            raise ValueError(
                "At least three matching feature points are required."
            )

        matrix, _ = cv2.estimateAffinePartial2D(
            old_points,
            new_points,
        )

        if matrix is None:
            raise ValueError("Failed to estimate affine transform.")

        return matrix

    def apply_transform(
        self,
        frame: np.ndarray,
        transform: np.ndarray,
    ) -> np.ndarray:
        """
        Apply an affine transformation to stabilize a frame.

        Args:
            frame: Input video frame.
            transform: 2x3 affine transformation matrix.

        Returns:
            Stabilized frame.

        Raises:
            ValueError:
                If the transform is invalid.
        """
        self._validate_frame(frame)

        if transform is None:
            raise ValueError("Transform matrix cannot be None.")

        if transform.shape != (2, 3):
            raise ValueError(
                "Transform matrix must have shape (2, 3)."
            )

        height, width = frame.shape[:2]

        stabilized = cv2.warpAffine(
            frame,
            transform,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return stabilized

    def smooth_motion(
        self,
        transforms: np.ndarray,
    ) -> np.ndarray:
        """
        Smooth motion using a moving average filter.

        Args:
            transforms: Array of frame-to-frame motion values.

        Returns:
            Smoothed motion values.
        """
        if transforms is None:
            raise ValueError("Transforms cannot be None.")

        if not isinstance(transforms, np.ndarray):
            raise TypeError("Transforms must be a NumPy ndarray.")

        if len(transforms) == 0:
            return transforms.copy()

        radius = max(0, int(self.config.smoothing_radius))
        smoothed = np.array(transforms, copy=True)

        if transforms.ndim == 1:
            values = transforms.astype(np.float32)
            for index in range(len(values)):
                if index in (0, len(values) - 1):
                    continue

                start = max(0, index - radius)
                end = min(len(values), index + radius + 1)
                moving_average = np.mean(values[start:end])
                smoothed[index] = min(moving_average, values[index])

            return smoothed

        for column in range(transforms.shape[1]):
            values = transforms[:, column].astype(np.float32)

            for index in range(len(values)):
                if index in (0, len(values) - 1):
                    continue

                start = max(0, index - radius)
                end = min(len(values), index + radius + 1)
                moving_average = np.mean(values[start:end])
                smoothed[index, column] = min(moving_average, values[index])

        return smoothed
    def crop_frame(
        self,
        frame: np.ndarray,
        border: int = 20,
    ) -> np.ndarray:
        """
        Crop borders introduced during frame stabilization.

        Args:
            frame: Stabilized frame.
            border: Number of pixels to crop from each edge.

        Returns:
            Cropped frame resized back to the original dimensions.
        """
        self._validate_frame(frame)

        height, width = frame.shape[:2]

        if border <= 0:
            return frame.copy()

        if border * 2 >= height or border * 2 >= width:
            raise ValueError(
                "Border is too large for the frame dimensions."
            )

        cropped = frame[
            border: height - border,
            border: width - border,
        ]

        return cv2.resize(
            cropped,
            (width, height),
            interpolation=cv2.INTER_LINEAR,
        )

    def stabilize(
        self,
        previous_frame: np.ndarray | None = None,
        current_frame: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Stabilize a frame using either a single-frame input or a
        previous/current frame pair.

        Args:
            previous_frame: Previous video frame or a single frame input.
            current_frame: Current video frame.

        Returns:
            A stabilized frame copy.
        """
        if current_frame is None:
            self._validate_frame(previous_frame)
            return previous_frame.copy()

        if previous_frame is None:
            self._validate_frame(current_frame)
            return current_frame.copy()

        self._validate_frame(previous_frame)
        self._validate_frame(current_frame)

        previous_gray = self.preprocess(previous_frame)
        current_gray = self.preprocess(current_frame)

        features = self.detect_features(previous_gray)

        if features is None:
            return current_frame.copy()

        old_points, new_points = self.track_features(
            previous_gray,
            current_gray,
            features,
        )

        if len(old_points) < 3 or len(new_points) < 3:
            return current_frame.copy()

        transform = self.estimate_motion(
            old_points,
            new_points,
        )

        stabilized = self.apply_transform(
            current_frame,
            transform,
        )

        return stabilized
    
    