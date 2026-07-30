"""
Contract tests for VideoSession API compliance.

Tests the public interface contract defined in contracts/video-session.md
to ensure proper API behavior and integration compatibility.
"""

import pytest
from unittest.mock import patch, MagicMock
import cv2

from src.ingestion.video_session import VideoSession, ActiveVideo
from src.ingestion.exceptions import UploadRejectedError


class TestVideoSessionContract:
    """Test VideoSession API contract compliance."""

    def test_get_active_returns_none_initially(self):
        """Contract: get_active() -> ActiveVideo | None - should return None initially."""
        session = VideoSession()

        result = session.get_active()

        assert result is None
        assert isinstance(result, type(None))

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_get_active_returns_active_video_after_set(
        self, mock_cv2, mock_uuid, mock_validator_class
    ):
        """Contract: get_active() -> ActiveVideo | None - should return ActiveVideo after successful set."""
        # Setup mocks
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "test-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 100
        mock_cv2.return_value = mock_cap

        session = VideoSession()
        session.set_from_path("/test.mp4")

        result = session.get_active()

        assert result is not None
        assert isinstance(result, ActiveVideo)
        assert result.display_name == "test.mp4"

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_set_from_path_returns_active_video_on_success(
        self, mock_cv2, mock_uuid, mock_validator_class
    ):
        """Contract: set_from_path(path) -> ActiveVideo - should return ActiveVideo on success."""
        # Setup mocks for success
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "success-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 600,
            cv2.CAP_PROP_FPS: 24.0,
        }.get(prop, 0)
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        result = session.set_from_path("/valid/video.mp4")

        assert isinstance(result, ActiveVideo)
        assert result.path == "/valid/video.mp4"
        assert result.display_name == "video.mp4"
        assert result.status == "ready"

    @patch("src.ingestion.video_session.FormatValidator")
    def test_set_from_path_raises_upload_rejected_error_on_failure(
        self, mock_validator_class
    ):
        """Contract: set_from_path(path) -> ActiveVideo - should raise UploadRejectedError on failure."""
        mock_validator = MagicMock()
        mock_validator.validate_file.side_effect = UploadRejectedError(
            "File format not supported"
        )
        mock_validator_class.return_value = mock_validator

        session = VideoSession()

        with pytest.raises(UploadRejectedError, match="File format not supported"):
            session.set_from_path("/invalid.txt")

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_set_from_path_replaces_prior_active_on_success(
        self, mock_cv2, mock_uuid, mock_validator_class
    ):
        """Contract: On success, replace any prior active video."""
        # Setup mocks
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "replace-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 100
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        # Set first video
        first_result = session.set_from_path("/first.mp4")
        assert session.get_active() == first_result

        # Set second video - should replace
        second_result = session.set_from_path("/second.mp4")

        assert session.get_active() == second_result
        assert session.get_active() != first_result
        assert session.get_active().display_name == "second.mp4"

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_set_from_path_leaves_prior_active_unchanged_on_failure(
        self, mock_cv2, mock_uuid, mock_validator_class
    ):
        """Contract: On failure, leave prior active unchanged."""
        # Setup mocks for initial success
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "unchanged-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 100
        mock_cv2.return_value = mock_cap

        session = VideoSession()

        # Set initial video successfully
        initial_result = session.set_from_path("/valid.mp4")
        assert session.get_active() == initial_result

        # Make next validation fail
        mock_validator.validate_file.side_effect = UploadRejectedError("Invalid file")

        # Attempt to replace should fail
        with pytest.raises(UploadRejectedError):
            session.set_from_path("/invalid.txt")

        # Prior active should be unchanged
        assert session.get_active() == initial_result
        assert session.get_active().display_name == "valid.mp4"

    def test_clear_returns_none(self):
        """Contract: clear() -> None - should return None."""
        session = VideoSession()

        result = session.clear()

        assert result is None

    @patch("src.ingestion.video_session.FormatValidator")
    @patch("src.ingestion.video_session.uuid4")
    @patch("cv2.VideoCapture")
    def test_clear_makes_active_none(self, mock_cv2, mock_uuid, mock_validator_class):
        """Contract: clear() should make active video None."""
        # Setup and create active video
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_uuid.return_value.hex = "clear-uuid"

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 100
        mock_cv2.return_value = mock_cap

        session = VideoSession()
        session.set_from_path("/test.mp4")

        # Verify we have an active video
        assert session.get_active() is not None

        # Clear should make it None
        session.clear()
        assert session.get_active() is None

    def test_last_error_returns_string_or_none(self):
        """Contract: last_error() -> str | None - should return string or None."""
        session = VideoSession()

        result = session.last_error

        assert result is None or isinstance(result, str)

    def test_session_maintains_at_most_one_active_video(self):
        """Contract invariant: At most one ready ActiveVideo."""
        session = VideoSession()

        # Initially no active video
        assert session.get_active() is None

        # After mocking successful upload, should have exactly one
        mock_video = ActiveVideo(
            id="test",
            display_name="test.mp4",
            path="/test.mp4",
            duration_ms=1000,
            frame_count=30,
            fps=30.0,
            status="ready",
        )
        session._active_video = mock_video

        active = session.get_active()
        assert active is not None
        assert active.status == "ready"

        # After clear, should be None again
        session.clear()
        assert session.get_active() is None
