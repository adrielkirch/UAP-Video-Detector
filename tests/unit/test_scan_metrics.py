"""
Unit tests for ScanMetrics recorder and logger.

Tests performance metrics collection and logging functionality
with fake timings and memory measurements (no GPU required).
"""

from unittest.mock import patch
import json

from src.orchestration.scan_metrics import ScanMetrics


class TestScanMetrics:
    """Test ScanMetrics performance recording and structured logging."""

    def test_scan_metrics_initial_state(self):
        """Should initialize with metrics collection disabled by default."""
        metrics = ScanMetrics()

        assert not metrics.is_enabled()
        assert metrics.get_total_frames_processed() == 0
        assert metrics.get_average_inference_time() == 0.0

    def test_enable_disable_metrics_collection(self):
        """Should properly toggle metrics collection."""
        metrics = ScanMetrics()

        # Initially disabled
        assert not metrics.is_enabled()

        # Enable metrics
        metrics.enable()
        assert metrics.is_enabled()

        # Disable metrics
        metrics.disable()
        assert not metrics.is_enabled()

    def test_record_inference_timing_basic(self):
        """Should record basic inference timing metrics."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record inference timing
        frame_index = 0
        inference_ms = 150.5
        device = "cpu"

        metrics.record_inference(
            frame_index=frame_index, inference_ms=inference_ms, device=device
        )

        # Should update metrics
        assert metrics.get_total_frames_processed() == 1
        assert metrics.get_average_inference_time() == inference_ms
        assert metrics.get_last_device() == device

    def test_record_inference_with_memory(self):
        """Should record inference metrics with optional memory measurement."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record with memory
        metrics.record_inference(
            frame_index=0, inference_ms=200.0, device="cuda:0", memory_mb=512.5
        )

        assert metrics.get_total_frames_processed() == 1
        assert metrics.get_last_memory_usage() == 512.5
        assert metrics.get_last_device() == "cuda:0"

    def test_record_inference_when_disabled_ignores_data(self):
        """Should ignore recording when metrics collection is disabled."""
        metrics = ScanMetrics()
        # Don't enable - should remain disabled

        metrics.record_inference(frame_index=0, inference_ms=100.0, device="cpu")

        # Should not record anything
        assert metrics.get_total_frames_processed() == 0
        assert metrics.get_average_inference_time() == 0.0

    def test_multiple_inference_recordings_calculate_average(self):
        """Should calculate correct average inference time over multiple recordings."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record multiple inferences
        inference_times = [100.0, 150.0, 200.0, 50.0]  # Average = 125.0

        for i, inference_ms in enumerate(inference_times):
            metrics.record_inference(
                frame_index=i, inference_ms=inference_ms, device="cpu"
            )

        assert metrics.get_total_frames_processed() == 4
        assert metrics.get_average_inference_time() == 125.0

    def test_get_performance_summary(self):
        """Should generate comprehensive performance summary."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record some metrics
        metrics.record_inference(frame_index=0, inference_ms=100.0, device="cpu")
        metrics.record_inference(
            frame_index=1, inference_ms=200.0, device="cuda:0", memory_mb=256.0
        )

        summary = metrics.get_performance_summary()

        # Should contain expected fields
        assert "total_frames" in summary
        assert "average_inference_ms" in summary
        assert "last_device" in summary
        assert "last_memory_mb" in summary

        assert summary["total_frames"] == 2
        assert summary["average_inference_ms"] == 150.0
        assert summary["last_device"] == "cuda:0"
        assert summary["last_memory_mb"] == 256.0

    def test_structured_log_output(self):
        """Should generate structured log entries in JSON format."""
        metrics = ScanMetrics()
        metrics.enable()

        with patch("src.orchestration.scan_metrics.logger") as mock_logger:
            # Record inference with logging
            metrics.record_inference(
                frame_index=42, inference_ms=175.5, device="cuda:0", memory_mb=512.0
            )

        # Should have called logger.info with structured data
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]

        # Parse the JSON log entry
        log_data = json.loads(log_call)

        assert log_data["frame_index"] == 42
        assert log_data["inference_ms"] == 175.5
        assert log_data["device"] == "cuda:0"
        assert log_data["memory_mb"] == 512.0
        assert "timestamp" in log_data

    def test_structured_log_without_memory(self):
        """Should generate structured log entries without optional memory field."""
        metrics = ScanMetrics()
        metrics.enable()

        with patch("src.orchestration.scan_metrics.logger") as mock_logger:
            # Record inference without memory
            metrics.record_inference(frame_index=10, inference_ms=95.0, device="cpu")

        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]

        # Parse the JSON log entry
        log_data = json.loads(log_call)

        assert log_data["frame_index"] == 10
        assert log_data["inference_ms"] == 95.0
        assert log_data["device"] == "cpu"
        assert "memory_mb" not in log_data  # Should not include null memory
        assert "timestamp" in log_data

    def test_lag_detection_and_warning(self):
        """Should detect and flag performance lag above threshold."""
        metrics = ScanMetrics(lag_threshold_ms=100.0)
        metrics.enable()

        # Record inference below threshold
        metrics.record_inference(frame_index=0, inference_ms=80.0, device="cpu")
        assert not metrics.is_lagging()

        # Record inference above threshold
        metrics.record_inference(frame_index=1, inference_ms=150.0, device="cpu")
        assert metrics.is_lagging()

        # Get lag warning
        warning = metrics.get_lag_warning()
        assert warning is not None
        assert "150.0ms" in warning
        assert "100.0ms" in warning

    def test_reset_metrics_clears_state(self):
        """Should reset all collected metrics to initial state."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record some data
        metrics.record_inference(frame_index=0, inference_ms=100.0, device="cpu")
        metrics.record_inference(frame_index=1, inference_ms=200.0, device="gpu")

        assert metrics.get_total_frames_processed() == 2
        assert metrics.get_average_inference_time() == 150.0

        # Reset metrics
        metrics.reset()

        # Should return to initial state
        assert metrics.get_total_frames_processed() == 0
        assert metrics.get_average_inference_time() == 0.0
        assert metrics.get_last_device() is None
        assert not metrics.is_lagging()

    def test_metrics_thread_safety(self):
        """Should handle concurrent access safely (basic test)."""
        metrics = ScanMetrics()
        metrics.enable()

        # Simulate concurrent recordings
        import threading

        def record_metrics(start_idx):
            for i in range(10):
                metrics.record_inference(
                    frame_index=start_idx + i, inference_ms=100.0, device="cpu"
                )

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=record_metrics, args=(i * 10,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have recorded all frames
        assert metrics.get_total_frames_processed() == 30
        assert metrics.get_average_inference_time() == 100.0

    def test_memory_usage_tracking(self):
        """Should track and report memory usage patterns."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record varying memory usage
        memory_values = [128.0, 256.0, 512.0, 1024.0]

        for i, memory_mb in enumerate(memory_values):
            metrics.record_inference(
                frame_index=i, inference_ms=100.0, device="cuda:0", memory_mb=memory_mb
            )

        # Should track memory statistics
        summary = metrics.get_performance_summary()
        assert summary["last_memory_mb"] == 1024.0

        # Should have memory statistics
        memory_stats = metrics.get_memory_statistics()
        assert memory_stats["max_memory_mb"] == 1024.0
        assert memory_stats["min_memory_mb"] == 128.0
        assert memory_stats["avg_memory_mb"] == 480.0  # (128+256+512+1024)/4

    def test_device_usage_tracking(self):
        """Should track device usage patterns."""
        metrics = ScanMetrics()
        metrics.enable()

        # Record different devices
        devices = ["cpu", "cuda:0", "cuda:1", "cpu", "cuda:0"]

        for i, device in enumerate(devices):
            metrics.record_inference(frame_index=i, inference_ms=100.0, device=device)

        # Should track device usage
        device_stats = metrics.get_device_statistics()
        assert device_stats["cpu"] == 2
        assert device_stats["cuda:0"] == 2
        assert device_stats["cuda:1"] == 1

        assert metrics.get_last_device() == "cuda:0"
