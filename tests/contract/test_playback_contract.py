"""
Contract tests for PlaybackController API compliance.

Tests the public interface contract defined in contracts/video-session.md
to ensure proper playback API behavior and integration compatibility.
"""

from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.ingestion.playback import PlaybackController, PlaybackSession
from src.ingestion.video_session import VideoSession, ActiveVideo


class TestPlaybackControllerContract:
    """Test PlaybackController API contract compliance."""

    def test_attach_accepts_video_session(self):
        """Contract: attach(session: VideoSession) -> None"""
        controller = PlaybackController()
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = None

        # Should accept VideoSession and return None
        result = controller.attach(video_session)

        assert result is None

    def test_play_returns_none(self):
        """Contract: play() -> None"""
        controller = PlaybackController()

        # Setup with video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.play()
        assert result is None

    def test_pause_returns_none(self):
        """Contract: pause() -> None"""
        controller = PlaybackController()

        # Setup with video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.pause()
        assert result is None

    def test_stop_returns_none(self):
        """Contract: stop() -> None"""
        controller = PlaybackController()

        # Setup with video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.stop()
        assert result is None

    def test_seek_ms_accepts_int_returns_none(self):
        """Contract: seek_ms(position_ms: int) -> None"""
        controller = PlaybackController()

        # Setup with video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        # Should accept int and return None
        result = controller.seek_ms(15000)
        assert result is None

    def test_seek_frame_accepts_int_returns_none(self):
        """Contract: seek_frame(frame_index: int) -> None"""
        controller = PlaybackController()

        # Setup with video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.seek_frame(450)
        assert result is None

    def test_get_state_returns_playback_session_or_none(self):
        """Contract: get_state() -> PlaybackSession | None"""
        controller = PlaybackController()

        # Initially should return None
        result = controller.get_state()
        assert result is None

        # After attach should return PlaybackSession
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.get_state()
        assert result is not None
        assert isinstance(result, PlaybackSession)

    @patch("src.ingestion.playback.VideoCaptureWrapper")
    def test_read_current_frame_returns_ndarray_or_none(self, mock_wrapper_class):
        """Contract: read_current_frame() -> ndarray | None"""
        controller = PlaybackController()

        # Without video should return None
        result = controller.read_current_frame()
        assert result is None

        # With video should return ndarray
        mock_wrapper = MagicMock()
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_wrapper.read_frame_at.return_value = mock_frame
        mock_wrapper_class.return_value = mock_wrapper

        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        result = controller.read_current_frame()
        assert result is not None
        assert isinstance(result, np.ndarray)

    def test_seek_clamps_to_valid_range(self):
        """Contract: Seek MUST clamp to valid range; MUST NOT throw for clamp-only adjustment."""
        controller = PlaybackController()

        # Setup 30-second video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        # Seek beyond end should clamp, not throw
        controller.seek_ms(60000)  # Beyond 30s duration
        state = controller.get_state()
        assert state.position_ms == 30000  # Clamped to end

        # Seek before start should clamp, not throw
        controller.seek_ms(-10000)  # Negative position
        state = controller.get_state()
        assert state.position_ms == 0  # Clamped to start

        # Frame-based seek should also clamp
        controller.seek_frame(2000)  # Beyond 900 frames
        state = controller.get_state()
        assert state.position_frame == 900  # Clamped to last frame

        controller.seek_frame(-100)  # Negative frame
        state = controller.get_state()
        assert state.position_frame == 0  # Clamped to first frame

    def test_clear_and_replace_resets_playback_state(self):
        """Contract: clear() or successful replace MUST stop playback and clear scan overlays."""
        controller = PlaybackController()

        # Setup initial video and start playing
        mock_video1 = ActiveVideo(
            id="test1",
            display_name="test1.mp4",
            path="/test1.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video1

        controller.attach(video_session)
        controller.play()
        controller.seek_ms(10000)  # Move to middle

        # Verify playing state
        state = controller.get_state()
        assert state.state == "playing"
        assert state.position_ms == 10000

        # Simulate video clear
        video_session.get_active.return_value = None
        controller.on_video_changed()

        # Should have no state (cleared)
        assert controller.get_state() is None

        # Replace with new video should reset state
        mock_video2 = ActiveVideo(
            id="test2",
            display_name="test2.mp4",
            path="/test2.mp4",
            duration_ms=60000,
            frame_count=1800,
            fps=30.0,
            status="ready",
        )
        video_session.get_active.return_value = mock_video2
        controller.attach(video_session)

        state = controller.get_state()
        assert state.state == "stopped"  # Reset to stopped
        assert state.position_ms == 0  # Reset to start
        assert state.duration_ms == 60000  # New video duration

    def test_playback_state_transitions(self):
        """Contract: Test valid playback state transitions."""
        controller = PlaybackController()

        # Setup video
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video
        controller.attach(video_session)

        # Initial: stopped
        state = controller.get_state()
        assert state.state == "stopped"

        # stopped -> playing
        controller.play()
        state = controller.get_state()
        assert state.state == "playing"

        # playing -> paused
        controller.pause()
        state = controller.get_state()
        assert state.state == "paused"

        # paused -> playing
        controller.play()
        state = controller.get_state()
        assert state.state == "playing"

        # playing -> stopped
        controller.stop()
        state = controller.get_state()
        assert state.state == "stopped"
        assert state.position_ms == 0  # Reset to start
