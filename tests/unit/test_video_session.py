"""
Unit tests for VideoSession and ActiveVideo management.

Tests single-video session state management including upload, replace,
clear, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import cv2

from src.ingestion.video_session import VideoSession, ActiveVideo
from src.ingestion.exceptions import UploadRejectedError


class TestActiveVideo:
    """Test ActiveVideo data model."""

    def test_active_video_creation_with_valid_data(self):
        """Should create ActiveVideo with required fields."""
        video = ActiveVideo(
            id="uuid-1234",
            display_name="test_video.mp4",
            path="/path/to/test_video.mp4",
            duration_ms=30000,
            frame_count=900,
            fps=30.0,
            status="ready",
        )

        assert video.id == "uuid-1234"
        assert video.display_name == "test_video.mp4"
        assert video.path == "/path/to/test_video.mp4"
        assert video.duration_ms == 30000
        assert video.frame_count == 900
        assert video.fps == 30.0
        assert video.status == "ready"

    def test_active_video_with_unknown_metadata(self):
        """Should handle unknown duration/frame_count gracefully."""
        video = ActiveVideo(
            id="uuid-5678",
            display_name="unknown.mp4",
            path="/path/to/unknown.mp4",
            duration_ms=0,  # Unknown
            frame_count=0,  # Unknown
            fps=0.0,  # Unknown
            status="ready",
        )

        assert video.duration_ms == 0
        assert video.frame_count == 0
        assert video.fps == 0.0

    def test_active_video_status_validation(self):
        """Should validate status is one of allowed values."""
        valid_statuses = ["ready", "invalid", "cleared"]

        for status in valid_statuses:
            video = ActiveVideo(
                id="test",
                display_name="test.mp4",
                path="/test.mp4",
                duration_ms=1000,
                frame_count=30,
                fps=30.0,
                status=status,
            )
            assert video.status == status


class TestVideoSession:
    """Test VideoSession single-video management."""

    def test_video_session_initial_state(self):
        """Should start with no active video and no error."""
        session = VideoSession()

        assert session.get_active() is None
        assert session.last_error is None

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_set_from_path_success(self, mock_cv2, mock_uuid, mock_validator_class):
        """Should successfully set active video from valid path."""
        # Setup mocks
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "uuid1234"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 900,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_WIDTH: 720,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
        }.get(prop, 0)
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        # Should succeed and return ActiveVideo
        active_video = session.set_from_path("/path/to/video.mp4")

        assert active_video is not None
        assert active_video.display_name == "video.mp4"
        assert active_video.path == "/path/to/video.mp4"
        assert active_video.status == "ready"
        assert active_video.width == 720
        assert active_video.height == 480
        assert session.get_active() == active_video
        assert session.last_error is None

        # Should have validated the file
        mock_validator.validate_file.assert_called_once_with("/path/to/video.mp4")

    @patch("src.ingestion.video_session.FormatValidator")
    def test_set_from_path_validation_failure(self, mock_validator_class):
        """Should handle validation failure and preserve prior state."""
        # Setup validator to reject file
        mock_validator = MagicMock()
        mock_validator.validate_file.side_effect = UploadRejectedError(
            "Unsupported format"
        )
        mock_validator_class.return_value = mock_validator

        session = VideoSession()

        # Should raise UploadRejectedError
        with pytest.raises(UploadRejectedError, match="Unsupported format"):
            session.set_from_path("/path/to/invalid.txt")

        # State should remain unchanged
        assert session.get_active() is None
        assert session.last_error is None

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_replace_active_video(self, mock_cv2, mock_uuid, mock_validator_class):
        """Should replace active video and release prior resources."""
        # Setup mocks
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "new-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        # Set initial video
        first_video = session.set_from_path("/first.mp4")
        assert session.get_active() == first_video

        # Replace with second video
        second_video = session.set_from_path("/second.mp4")

        # Should have new active video
        assert session.get_active() == second_video
        assert second_video.display_name == "second.mp4"
        assert session.get_active() != first_video

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_replace_failure_keeps_prior_active(
        self, mock_cv2, mock_uuid, mock_validator_class
    ):
        """Should keep prior active video if replacement fails."""
        # Setup mocks for initial success
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "uuid1"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        # Set initial video successfully
        first_video = session.set_from_path("/valid.mp4")
        assert session.get_active() == first_video

        # Now make validation fail for replacement
        mock_validator.validate_file.side_effect = UploadRejectedError("Invalid format")

        # Attempt replacement should fail
        with pytest.raises(UploadRejectedError):
            session.set_from_path("/invalid.txt")

        # Prior active should be unchanged
        assert session.get_active() == first_video
        assert session.get_active().display_name == "valid.mp4"

    def test_clear_removes_active_video(self):
        """Should clear active video and reset state."""
        session = VideoSession()

        # Mock an active video (bypass normal setup for test focus)
        mock_video = Mock(spec=ActiveVideo)
        session._active_video = mock_video

        # Clear should reset to None
        session.clear()

        assert session.get_active() is None

    def test_multiple_clear_operations_safe(self):
        """Should handle multiple clear operations safely."""
        session = VideoSession()

        # Multiple clears should not raise errors
        session.clear()
        session.clear()
        session.clear()

        assert session.get_active() is None
