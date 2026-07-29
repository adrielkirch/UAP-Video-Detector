"""
Performance metrics recorder and logger for scan operations.

Provides structured logging and performance monitoring for inference
operations with optional memory tracking and lag detection.
"""

import json
import logging
import time
import threading
from typing import Optional, Dict, Any
from collections import defaultdict

# Configure structured logging
logger = logging.getLogger(__name__)


class ScanMetrics:
    """
    Performance metrics collection and structured logging.

    Records inference timing, memory usage, and device information
    with thread-safe operations and configurable lag detection.
    """

    def __init__(self, lag_threshold_ms: float = 2000.0):
        """
        Initialize metrics collector.

        Args:
            lag_threshold_ms: Threshold for lag warning detection
        """
        self._enabled = False
        self._lag_threshold_ms = lag_threshold_ms

        # Thread-safe metrics storage
        self._lock = threading.Lock()
        self._total_frames = 0
        self._total_inference_time = 0.0
        self._last_inference_ms = 0.0
        self._last_device: Optional[str] = None
        self._last_memory_mb: Optional[float] = None
        self._is_lagging = False
        self._lag_warning: Optional[str] = None

        # Statistics tracking
        self._inference_times = []
        self._memory_usage = []
        self._device_counts = defaultdict(int)

    def enable(self) -> None:
        """Enable metrics collection."""
        with self._lock:
            self._enabled = True

    def disable(self) -> None:
        """Disable metrics collection."""
        with self._lock:
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._enabled

    def record_inference(
        self,
        frame_index: int,
        inference_ms: float,
        device: str,
        memory_mb: Optional[float] = None,
    ) -> None:
        """
        Record inference performance metrics.

        Args:
            frame_index: Zero-based frame number
            inference_ms: Inference duration in milliseconds
            device: Device used for inference (cpu, cuda:0, etc.)
            memory_mb: Optional memory usage in megabytes
        """
        if not self._enabled:
            return

        with self._lock:
            # Update counters
            self._total_frames += 1
            self._total_inference_time += inference_ms
            self._last_inference_ms = inference_ms
            self._last_device = device
            self._last_memory_mb = memory_mb

            # Track statistics
            self._inference_times.append(inference_ms)
            if memory_mb is not None:
                self._memory_usage.append(memory_mb)
            self._device_counts[device] += 1

            # Check for lag
            self._is_lagging = inference_ms > self._lag_threshold_ms
            if self._is_lagging:
                self._lag_warning = (
                    f"Inference lag detected: {inference_ms:.1f}ms "
                    f"exceeded {self._lag_threshold_ms:.1f}ms threshold"
                )
            else:
                self._lag_warning = None

        # Log structured metrics
        self._log_structured_metrics(frame_index, inference_ms, device, memory_mb)

    def _log_structured_metrics(
        self,
        frame_index: int,
        inference_ms: float,
        device: str,
        memory_mb: Optional[float],
    ) -> None:
        """Log structured metrics entry."""
        log_entry = {
            "timestamp": time.time(),
            "frame_index": frame_index,
            "inference_ms": inference_ms,
            "device": device,
        }

        # Only include memory if provided
        if memory_mb is not None:
            log_entry["memory_mb"] = memory_mb

        # Log as structured JSON
        logger.info(json.dumps(log_entry))

    def get_total_frames_processed(self) -> int:
        """Get total number of frames processed."""
        return self._total_frames

    def get_average_inference_time(self) -> float:
        """Get average inference time in milliseconds."""
        if self._total_frames == 0:
            return 0.0
        return self._total_inference_time / self._total_frames

    def get_last_device(self) -> Optional[str]:
        """Get the last device used for inference."""
        return self._last_device

    def get_last_memory_usage(self) -> Optional[float]:
        """Get the last recorded memory usage in MB."""
        return self._last_memory_mb

    def is_lagging(self) -> bool:
        """Check if last inference exceeded lag threshold."""
        return self._is_lagging

    def get_lag_warning(self) -> Optional[str]:
        """Get current lag warning message."""
        return self._lag_warning

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.

        Returns:
            Dictionary with performance statistics
        """
        with self._lock:
            summary = {
                "total_frames": self._total_frames,
                "average_inference_ms": self.get_average_inference_time(),
                "last_device": self._last_device,
            }

            if self._last_memory_mb is not None:
                summary["last_memory_mb"] = self._last_memory_mb

            return summary

    def get_memory_statistics(self) -> Dict[str, float]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with memory statistics
        """
        with self._lock:
            if not self._memory_usage:
                return {}

            return {
                "max_memory_mb": max(self._memory_usage),
                "min_memory_mb": min(self._memory_usage),
                "avg_memory_mb": sum(self._memory_usage) / len(self._memory_usage),
            }

    def get_device_statistics(self) -> Dict[str, int]:
        """
        Get device usage statistics.

        Returns:
            Dictionary mapping device names to usage counts
        """
        with self._lock:
            return dict(self._device_counts)

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self._total_frames = 0
            self._total_inference_time = 0.0
            self._last_inference_ms = 0.0
            self._last_device = None
            self._last_memory_mb = None
            self._is_lagging = False
            self._lag_warning = None

            # Clear statistics
            self._inference_times.clear()
            self._memory_usage.clear()
            self._device_counts.clear()
