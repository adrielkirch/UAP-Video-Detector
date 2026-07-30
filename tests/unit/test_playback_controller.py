"""
Unit tests for PlaybackController and PlaybackSession.

Tests video playback state management including play, pause, stop, seek
operations and integration with video session management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.ingestion.playback import PlaybackController, PlaybackSession
from src.ingestion.video_session import VideoSession, ActiveVideo


class TestPlaybackSession:
    """Test PlaybackSession state model."""

    def test_playback_session_initial_state(self):
        """Should start in stopped state at position zero."""
        session = PlaybackSession()

        assert session.state == "stopped"
        assert session.position_ms == 0
        assert session.position_frame == 0
        assert session.duration_ms == 0

    def test_playback_session_with_duration(self):
        """Should initialize with known video duration."""
        session = PlaybackSession(duration_ms=30000)

        assert session.duration_ms == 30000
        assert session.state == "stopped"
        assert session.position_ms == 0


class TestPlaybackController:
    """Test PlaybackController state management and operations."""

    def test_controller_initial_state(self):
        """Should start with no attached session."""
        controller = PlaybackController()

        assert controller.get_state() is None

    def test_attach_video_session_creates_playback_state(self):
        """Should create PlaybackSession when video session attached."""
        controller = PlaybackController()

        # Mock video session with active video
        mock_video = ActiveVideo(
            id="test-id",
            display_name="test.mp4",
            path="/path/test.mp4",
            duration_ms=60000,
            frame_count=1800,
            fps=30.0,
            status="ready",
        )
        video_session = Mock(spec=VideoSession)
        video_session.get_active.return_value = mock_video

        controller.attach(video_session)

        playback_state = controller.get_state()
        assert playback_state is not None
        assert playback_state.duration_ms == 60000
        assert playback_state.state == "stopped"
        assert playback_state.position_ms == 0

    def test_play_transitions_to_playing_state(self):
        """Should transition from stopped to playing state."""
        controller = PlaybackController()

        # Setup with mock video
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

        # Play should change state
        controller.play()

        state = controller.get_state()
        assert state.state == "playing"

    def test_pause_freezes_position(self):
        """Should pause playback and maintain current position."""
        controller = PlaybackController()

        # Setup and start playing
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
        controller.play()

        # Simulate some playback time
        controller._playback_session.position_ms = 5000

        # Pause should freeze position
        controller.pause()

        state = controller.get_state()
        assert state.state == "paused"
        assert state.position_ms == 5000  # Position preserved

    def test_seek_ms_clamps_and_updates_position(self):
        """Should clamp seek position to valid range and update state."""
        controller = PlaybackController()

        # Setup with 30 second video
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

        # Valid seek
        controller.seek_ms(15000)
        state = controller.get_state()
        assert state.position_ms == 15000
        assert state.position_frame == 450  # 15s * 30fps

        # Seek beyond duration should clamp to end
        controller.seek_ms(45000)
        state = controller.get_state()
        assert state.position_ms == 30000

        # Negative seek should clamp to start
        controller.seek_ms(-5000)
        state = controller.get_state()
        assert state.position_ms == 0
        assert state.position_frame == 0

    def test_stop_resets_to_start(self):
        """Should stop playback and reset position to zero."""
        controller = PlaybackController()

        # Setup and play
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
        controller.play()
        controller.seek_ms(10000)  # Move to middle

        # Stop should reset
        controller.stop()

        state = controller.get_state()
        assert state.state == "stopped"
        assert state.position_ms == 0
        assert state.position_frame == 0

    def test_no_video_controls_raise_error(self):
        """Should raise error when controls used without video attached."""
        controller = PlaybackController()

        with pytest.raises(RuntimeError, match="No video session attached"):
            controller.play()

        with pytest.raises(RuntimeError, match="No video session attached"):
            controller.pause()

        with pytest.raises(RuntimeError, match="No video session attached"):
            controller.seek_ms(1000)

    def test_clear_replace_resets_playback(self):
        """Should reset playback state when video is cleared or replaced."""
        controller = PlaybackController()

        # Setup initial video
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
        controller.seek_ms(10000)

        # Simulate video clear
        video_session.get_active.return_value = None
        controller.on_video_changed()  # Callback from video session

        # Should reset state
        assert controller.get_state() is None

        # Reattach should create new session
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
        assert state.duration_ms == 60000
        assert state.state == "stopped"
        assert state.position_ms == 0

    @patch("src.ingestion.playback.VideoCaptureWrapper")
    def test_read_current_frame_returns_frame_data(self, mock_wrapper_class):
        """Should return current frame as numpy array."""
        # Setup mock capture
        mock_wrapper = MagicMock()
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_wrapper.read_frame_at.return_value = mock_frame
        mock_wrapper_class.return_value = mock_wrapper

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

        # Should return frame
        frame = controller.read_current_frame()
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    def test_read_current_frame_returns_none_without_video(self):
        """Should return None when no video attached."""
        controller = PlaybackController()

        frame = controller.read_current_frame()
        assert frame is None
