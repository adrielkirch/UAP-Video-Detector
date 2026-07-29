"""
Integration tests for upload → play → scan toggle workflow.

Tests end-to-end integration between video session, playback controller,
and scan pipeline with stub detector to verify complete workflow.
"""

from unittest.mock import Mock, patch, MagicMock
import numpy as np
import tempfile
import os

from src.ingestion.video_session import VideoSession
from src.ingestion.playback import PlaybackController
from src.orchestration.scan_pipeline import ScanPipeline
from src.inference.null_detector import NullDetector
from src.inference.detection_types import Detection, FrameDetections


class StubDetector:
    """Stub detector for integration testing without YOLO."""

    def __init__(self):
        self._ready = False
        self._detections = []

    def load(self, config_path: str) -> None:
        """Load detector (stub implementation)."""
        self._ready = True

    def is_ready(self) -> bool:
        """Check if detector is ready."""
        return self._ready

    def detect(self, frame: np.ndarray) -> FrameDetections:
        """Return pre-configured stub detections."""
        if not self._ready:
            raise RuntimeError("Detector not ready")

        # Return consistent stub detections
        return FrameDetections(
            [
                Detection("airplane", 0.85, [100, 50, 200, 150]),
                Detection("bird", 0.72, [300, 200, 350, 250]),
            ]
        )

    def close(self) -> None:
        """Close detector."""
        self._ready = False

    def set_detections(self, detections):
        """Helper to configure stub detections."""
        self._detections = detections


class TestUploadPlayScanIntegration:
    """Test complete upload → play → scan workflow integration."""

    @patch("src.ingestion.video_session.cv2.VideoCapture")
    def test_upload_video_creates_session(self, mock_cv2_capture):
        """Should successfully upload video and create active session."""
        # Mock video file upload
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            "CAP_PROP_FRAME_COUNT": 1800,
            "CAP_PROP_FPS": 30.0,
            "CAP_PROP_POS_MSEC": 60000,
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_cap

        # Create video session
        video_session = VideoSession()

        # Create temporary video file for testing
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_path = temp_file.name
            # Write minimal video-like content (not real video, but passes basic checks)

        try:
            # Upload video using correct API
            active_video = video_session.set_from_path(temp_path)

            # Should have active video
            assert active_video is not None
            assert "test_video.mp4" in active_video.display_name  # Contains filename
            assert active_video.status == "ready"
            assert video_session.get_active() == active_video

        finally:
            # Cleanup temp file
            os.unlink(temp_path)

    def test_playback_controller_integration_with_video_session(self):
        """Should integrate playback controller with video session."""
        # Mock video session with active video
        video_session = Mock(spec=VideoSession)

        # Mock active video
        from src.ingestion.video_session import ActiveVideo

        mock_video = ActiveVideo(
            id="test-id",
            display_name="test.mp4",
            path="/fake/path.mp4",
            duration_ms=60000,
            frame_count=1800,
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video

        # Create playback controller
        playback_controller = PlaybackController()

        # Attach video session
        playback_controller.attach(video_session)

        # Should have playback state
        state = playback_controller.get_state()
        assert state is not None
        assert state.duration_ms == 60000
        assert state.state == "stopped"

    def test_scan_pipeline_integration_with_playback_and_detector(self):
        """Should integrate scan pipeline with playback and detector."""
        # Create components
        scan_pipeline = ScanPipeline()
        stub_detector = StubDetector()

        # Mock playback controller
        playback_controller = Mock(spec=PlaybackController)

        # Setup connections
        stub_detector.load("config/detector.yaml")
        scan_pipeline.attach_detector(stub_detector)
        scan_pipeline.attach_playback(playback_controller)

        # Enable scanning
        scan_pipeline.enable_scan()

        assert scan_pipeline.is_enabled()
        assert stub_detector.is_ready()

    def test_complete_workflow_upload_play_scan_toggle(self):
        """Should handle complete workflow: upload → play → enable scan → detect → disable scan."""
        # Setup video session
        video_session = Mock(spec=VideoSession)

        from src.ingestion.video_session import ActiveVideo

        mock_video = ActiveVideo(
            id="integration-test",
            display_name="integration_test.mp4",
            path="/fake/integration.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video

        # Setup playback controller
        playback_controller = PlaybackController()
        playback_controller.attach(video_session)

        # Setup scan pipeline with stub detector
        scan_pipeline = ScanPipeline()
        stub_detector = StubDetector()
        stub_detector.load("config/detector.yaml")

        scan_pipeline.attach_detector(stub_detector)
        scan_pipeline.attach_playback(playback_controller)

        # Step 1: Verify upload state
        assert video_session.get_active() == mock_video
        assert playback_controller.get_state() is not None

        # Step 2: Start playback
        playback_controller.play()
        assert playback_controller.get_state().state == "playing"

        # Step 3: Enable scan
        scan_pipeline.enable_scan()
        assert scan_pipeline.is_enabled()

        # Step 4: Process frame with detection
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = scan_pipeline.process_frame(test_frame, frame_index=0)

        # Should get detections from stub detector
        assert detections is not None
        assert len(detections.detections) == 2  # StubDetector returns 2 detections
        assert detections.detections[0].class_name == "airplane"
        assert detections.detections[1].class_name == "bird"

        # Step 5: Disable scan
        scan_pipeline.disable_scan()
        assert not scan_pipeline.is_enabled()

        # Step 6: Process frame with scan disabled
        no_detections = scan_pipeline.process_frame(test_frame, frame_index=1)
        assert no_detections is None

        # Step 7: Playback should continue working
        playback_controller.pause()
        assert playback_controller.get_state().state == "paused"

    def test_scan_toggle_preserves_last_detections(self):
        """Should preserve last detections when toggling scan off and on."""
        # Setup scan pipeline
        scan_pipeline = ScanPipeline()
        stub_detector = StubDetector()
        stub_detector.load("config.yaml")

        scan_pipeline.attach_detector(stub_detector)
        scan_pipeline.enable_scan()

        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Get initial detections
        initial_detections = scan_pipeline.process_frame(test_frame, frame_index=0)
        assert initial_detections is not None
        assert scan_pipeline.get_last_detections() == initial_detections

        # Disable scan
        scan_pipeline.disable_scan()

        # Last detections should be preserved
        assert scan_pipeline.get_last_detections() == initial_detections

        # Process frame while disabled (no new inference)
        no_new_detections = scan_pipeline.process_frame(test_frame, frame_index=1)
        assert no_new_detections is None

        # Last detections still preserved
        assert scan_pipeline.get_last_detections() == initial_detections

        # Re-enable scan
        scan_pipeline.enable_scan()

        # New detections should work
        new_detections = scan_pipeline.process_frame(test_frame, frame_index=2)
        assert new_detections is not None
        assert scan_pipeline.get_last_detections() == new_detections

    def test_null_detector_integration(self):
        """Should work with NullDetector for testing scenarios."""
        # Setup scan pipeline with null detector
        scan_pipeline = ScanPipeline()
        null_detector = NullDetector()
        null_detector.load("config.yaml")

        scan_pipeline.attach_detector(null_detector)
        scan_pipeline.enable_scan()

        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should work but return empty detections
        result = scan_pipeline.process_frame(test_frame, frame_index=0)

        assert result is not None
        assert isinstance(result, FrameDetections)
        assert len(result.detections) == 0
        assert scan_pipeline.get_last_detections() == result

    def test_error_handling_detector_not_ready(self):
        """Should handle detector not ready gracefully in integration."""
        # Setup scan pipeline
        scan_pipeline = ScanPipeline()
        stub_detector = StubDetector()
        # Don't call load() - detector not ready

        scan_pipeline.attach_detector(stub_detector)
        scan_pipeline.enable_scan()

        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should handle not-ready detector gracefully
        result = scan_pipeline.process_frame(test_frame, frame_index=0)

        # Should return None when detector not ready
        assert result is None

    def test_playback_controller_frame_reading_integration(self):
        """Should integrate frame reading from playback controller."""
        # Mock playback controller that provides frames
        playback_controller = Mock(spec=PlaybackController)

        # Mock frame reading
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        playback_controller.read_current_frame.return_value = test_frame

        # Mock playback state
        from src.ingestion.playback import PlaybackSession

        mock_state = PlaybackSession(duration_ms=30000)
        mock_state.state = "playing"
        playback_controller.get_state.return_value = mock_state

        # Setup scan pipeline
        scan_pipeline = ScanPipeline()
        stub_detector = StubDetector()
        stub_detector.load("config.yaml")

        scan_pipeline.attach_detector(stub_detector)
        scan_pipeline.attach_playback(playback_controller)
        scan_pipeline.enable_scan()

        # Should be able to get frame from playback controller
        current_frame = playback_controller.read_current_frame()
        assert current_frame is not None

        # Should be able to process that frame
        detections = scan_pipeline.process_frame(current_frame, frame_index=0)
        assert detections is not None
