"""
Null object pattern implementation for detector abstraction.

Provides empty detector implementation for testing and fallback scenarios
with proper state management and empty detection results.
"""

import numpy as np
from typing import Optional

from .detector import AerialDetector, DetectorError
from .detection_types import FrameDetections


class NullDetector(AerialDetector):
    """
    Null object pattern detector that returns empty results.

    Useful for testing, development, and scenarios where detection
    is disabled but the pipeline needs a valid detector interface.
    """

    def __init__(self):
        """Initialize null detector."""
        self._ready = False

    def load(self, config_path: Optional[str]) -> None:
        """
        Load null detector (always succeeds).

        Args:
            config_path: Configuration path (ignored for null detector)
        """
        # Null detector is always ready after load
        self._ready = True

    def is_ready(self) -> bool:
        """
        Check if null detector is ready.

        Returns:
            True if load() has been called, False otherwise
        """
        return self._ready

    def detect(self, frame: np.ndarray) -> FrameDetections:
        """
        Detect objects in frame (always returns empty).

        Args:
            frame: Video frame as numpy array

        Returns:
            Empty FrameDetections

        Raises:
            DetectorError: If detector not ready
        """
        if not self.is_ready():
            raise DetectorError("Detector not ready. Call load() first.")

        # Always return empty detections
        return FrameDetections([])

    def close(self) -> None:
        """Close null detector (no-op)."""
        # Null detector has no resources to clean up
        pass
