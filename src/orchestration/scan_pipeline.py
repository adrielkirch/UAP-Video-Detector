"""
Scan pipeline for orchestrating frame processing with detection.

Manages scan enable/disable state, frame stride processing, detection
caching, and performance monitoring with lag warnings.
"""

import time
from typing import Optional, TYPE_CHECKING
import numpy as np

from ..inference.detector import AerialDetector
from ..inference.detection_types import FrameDetections
from .scan_metrics import ScanMetrics

if TYPE_CHECKING:
    from ..ingestion.playback import PlaybackController


class ScanPipeline:
    """
    Orchestrates video frame processing with aerial object detection.

    Provides scan enable/disable control, frame stride optimization,
    detection caching, and performance monitoring per constitution.
    """

    def __init__(
        self,
        frame_stride: int = 2,
        lag_warn_threshold_ms: int = 2000,
        metrics_enabled: bool = True,
    ):
        """
        Initialize scan pipeline.

        Args:
            frame_stride: Process every Nth frame (default: 2 for 50% reduction)
            lag_warn_threshold_ms: Warn when inference exceeds this duration
            metrics_enabled: Enable performance metrics collection
        """
        self._enabled = False
        self._frame_stride = frame_stride
        self._lag_warn_threshold_ms = lag_warn_threshold_ms

        # Component references
        self._detector: Optional[AerialDetector] = None
        self._playback_controller: Optional["PlaybackController"] = None

        # Performance metrics
        self._metrics = ScanMetrics(lag_threshold_ms=lag_warn_threshold_ms)
        if metrics_enabled:
            self._metrics.enable()

        # State management
        self._last_detections: Optional[FrameDetections] = None
        self.last_infer_duration_ms: float = 0
        self.last_lag_warning: Optional[str] = None

    def enable_scan(self) -> None:
        """Enable live scanning during playback."""
        self._enabled = True

    def disable_scan(self) -> None:
        """Disable live scanning (preserves last detections)."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if scanning is currently enabled."""
        return self._enabled

    def attach_detector(self, detector: AerialDetector) -> None:
        """
        Attach detector for inference.

        Args:
            detector: Detector implementing AerialDetector protocol
        """
        self._detector = detector

    def attach_playback(self, controller: "PlaybackController") -> None:
        """
        Attach playback controller for frame access.

        Args:
            controller: PlaybackController for frame reading
        """
        self._playback_controller = controller

    def process_frame(
        self, frame: np.ndarray, frame_index: int = 0
    ) -> Optional[FrameDetections]:
        """
        Process video frame for aerial object detection.

        Args:
            frame: Video frame as numpy array
            frame_index: Current frame index for stride calculation

        Returns:
            FrameDetections if processed, None if skipped
        """
        # Skip if scanning disabled
        if not self._enabled:
            return None

        # Skip if detector not available or not ready
        if self._detector is None or not self._detector.is_ready():
            return None

        # Apply frame stride (process every Nth frame)
        if frame_index % self._frame_stride != 0:
            return None

        try:
            # Record inference timing
            start_time = time.time()

            # Run detection
            detections = self._detector.detect(frame)

            # Calculate inference duration
            end_time = time.time()
            self.last_infer_duration_ms = (end_time - start_time) * 1000

            # Record metrics
            try:
                device = getattr(self._detector, "_device", "unknown")
                memory_mb = self._get_memory_usage()
                self._metrics.record_inference(
                    frame_index=frame_index,
                    inference_ms=self.last_infer_duration_ms,
                    device=str(device),  # Ensure device is string
                    memory_mb=memory_mb,
                )
            except Exception:
                # Metrics recording is optional - don't fail the scan
                pass

            # Check for lag warning (use metrics lag detection)
            if self._metrics.is_lagging():
                self.last_lag_warning = self._metrics.get_lag_warning()
            else:
                self.last_lag_warning = None

            # Cache detections
            self._last_detections = detections

            return detections

        except Exception as e:
            # Handle detection errors gracefully - never crash playback
            self.last_lag_warning = f"Scan error: {e}"

            # Disable scanning to prevent repeated errors
            self._enabled = False

            return None

    def get_last_detections(self) -> Optional[FrameDetections]:
        """
        Get last cached detection results.

        Returns:
            Last FrameDetections or None if no detections cached
        """
        return self._last_detections

    def clear_detections(self) -> None:
        """Clear cached detection state."""
        self._last_detections = None
        self.last_lag_warning = None
        self.last_infer_duration_ms = 0

    def get_frame_stride(self) -> int:
        """Get current frame stride setting."""
        return self._frame_stride

    def set_frame_stride(self, stride: int) -> None:
        """
        Set frame stride for processing optimization.

        Args:
            stride: Process every Nth frame (1 = every frame, 2 = every other frame)
        """
        self._frame_stride = max(1, stride)  # Ensure minimum stride of 1

    def get_lag_threshold(self) -> int:
        """Get current lag warning threshold in milliseconds."""
        return self._lag_warn_threshold_ms

    def set_lag_threshold(self, threshold_ms: int) -> None:
        """
        Set lag warning threshold.

        Args:
            threshold_ms: Warn when inference exceeds this duration
        """
        self._lag_warn_threshold_ms = max(100, threshold_ms)  # Minimum 100ms
        # Update metrics threshold as well
        self._metrics._lag_threshold_ms = self._lag_warn_threshold_ms

    def get_metrics(self) -> ScanMetrics:
        """Get performance metrics collector."""
        return self._metrics

    def _get_memory_usage(self) -> Optional[float]:
        """
        Get current memory usage in MB (best effort).

        Returns:
            Memory usage in MB or None if unavailable
        """
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except (ImportError, Exception):
            # Memory monitoring is optional
            return None
