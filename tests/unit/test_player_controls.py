"""
Unit tests for Streamlit player control widgets.

Tests UI components for video playback controls including play/pause/seek/stop
buttons and progress tracking displays.
"""

from unittest.mock import Mock, patch, MagicMock

from src.ui.components.player_controls import (
    render_playback_controls,
    render_progress_display,
    render_seek_control,
)
from src.ingestion.playback import PlaybackController, PlaybackSession


class TestPlaybackControlsRendering:
    """Test Streamlit playback control widget rendering."""

    @patch("streamlit.button")
    @patch("streamlit.columns")
    def test_render_controls_with_stopped_state(self, mock_columns, mock_button):
        """Should render appropriate controls for stopped state."""
        # Setup mock playback state
        playback_state = PlaybackSession(duration_ms=30000)
        playback_state.state = "stopped"

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Mock Streamlit columns with context manager support
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_col4 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]

        # Mock button returns
        mock_button.return_value = False

        # Should render without errors
        render_playback_controls(controller, key="test_controls")

        # Should have called streamlit functions
        mock_columns.assert_called_once_with(4)
        assert mock_button.call_count >= 3  # Play, Stop, and other controls

    @patch("streamlit.button")
    @patch("streamlit.columns")
    def test_render_controls_with_playing_state(self, mock_columns, mock_button):
        """Should render pause button when playing."""
        # Setup playing state
        playback_state = PlaybackSession(duration_ms=30000)
        playback_state.state = "playing"

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Mock Streamlit with context manager support
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_col4 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
        mock_button.return_value = False

        render_playback_controls(controller, key="test_playing")

        # Should render pause instead of play
        mock_columns.assert_called_once()
        assert mock_button.call_count >= 3

    @patch("streamlit.rerun")
    @patch("streamlit.button")
    @patch("streamlit.columns")
    def test_play_button_click_calls_controller(
        self, mock_columns, mock_button, mock_rerun
    ):
        """Should call controller.play() when play button clicked."""
        playback_state = PlaybackSession(duration_ms=30000)
        playback_state.state = "stopped"

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Mock Streamlit with context manager support
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        # Simulate play button click (first button call)
        mock_button.side_effect = [True, False, False, False]  # Play clicked

        render_playback_controls(controller, key="test_play_click")

        # Should have called play
        controller.play.assert_called_once()

    @patch("streamlit.rerun")
    @patch("streamlit.button")
    @patch("streamlit.columns")
    def test_pause_button_click_calls_controller(
        self, mock_columns, mock_button, mock_rerun
    ):
        """Should call controller.pause() when pause button clicked."""
        playback_state = PlaybackSession(duration_ms=30000)
        playback_state.state = "playing"

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Mock Streamlit with context manager support
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_button.side_effect = [True, False, False, False]  # Pause clicked

        render_playback_controls(controller, key="test_pause_click")

        controller.pause.assert_called_once()

    @patch("streamlit.rerun")
    @patch("streamlit.button")
    @patch("streamlit.columns")
    def test_stop_button_click_calls_controller(
        self, mock_columns, mock_button, mock_rerun
    ):
        """Should call controller.stop() when stop button clicked."""
        playback_state = PlaybackSession(duration_ms=30000)

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Mock Streamlit with context manager support
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_button.side_effect = [False, True, False, False]  # Stop clicked

        render_playback_controls(controller, key="test_stop_click")

        controller.stop.assert_called_once()

    def test_render_controls_with_no_playback_state(self):
        """Should handle gracefully when no playback state available."""
        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = None

        # Should not raise exception
        with patch("streamlit.info") as mock_info:
            render_playback_controls(controller, key="test_no_state")
            mock_info.assert_called_once()


class TestProgressDisplay:
    """Test progress display rendering."""

    @patch("streamlit.progress")
    @patch("streamlit.text")
    def test_progress_display_with_valid_state(self, mock_text, mock_progress):
        """Should display progress bar and time information."""
        playback_state = PlaybackSession(duration_ms=60000)
        playback_state.position_ms = 15000  # 15s of 60s

        render_progress_display(playback_state, key="test_progress")

        # Should show progress (15/60 = 0.25)
        mock_progress.assert_called_once_with(0.25)
        mock_text.assert_called_once_with("00:15 / 01:00")

    @patch("streamlit.progress")
    @patch("streamlit.text")
    def test_progress_display_zero_duration(self, mock_text, mock_progress):
        """Should handle zero duration gracefully."""
        playback_state = PlaybackSession(duration_ms=0)
        playback_state.position_ms = 0

        render_progress_display(playback_state, key="test_zero_duration")

        # Should show 0 progress
        mock_progress.assert_called_once_with(0.0)
        mock_text.assert_called_once_with("00:00 / 00:00")


class TestSeekControl:
    """Test seek control rendering."""

    @patch("streamlit.rerun")
    @patch("streamlit.slider")
    def test_seek_control_renders_slider(self, mock_slider, mock_rerun):
        """Should render time slider for seeking."""
        playback_state = PlaybackSession(duration_ms=120000)  # 2 minutes
        playback_state.position_ms = 30000  # 30 seconds

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        mock_slider.return_value = 45000  # User seeks to 45s

        render_seek_control(controller, key="test_seek")

        # Should render slider with correct range and current value
        mock_slider.assert_called_once_with(
            "Seek",
            min_value=0,
            max_value=120000,
            value=30000,
            step=1000,
            key="test_seek_slider",
            label_visibility="collapsed",
        )

        # Should call seek when value changes
        controller.seek_ms.assert_called_once_with(45000)

    @patch("streamlit.slider")
    def test_seek_control_no_seek_on_same_value(self, mock_slider):
        """Should not call seek when slider value unchanged."""
        playback_state = PlaybackSession(duration_ms=60000)
        playback_state.position_ms = 15000

        controller = Mock(spec=PlaybackController)
        controller.get_state.return_value = playback_state

        # Slider returns same value as current position
        mock_slider.return_value = 15000

        render_seek_control(controller, key="test_no_seek")

        # Should not call seek
        controller.seek_ms.assert_not_called()
