"""
Unit tests for video format validation.

Tests extension allowlist validation and OpenCV openability checks
for uploaded video files.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.ingestion.format_validator import FormatValidator
from src.ingestion.exceptions import UploadRejectedError


class TestFormatValidator:
    """Test video format validation logic."""

    def test_validator_accepts_configured_extensions(self):
        """Should accept files with extensions from config allowlist."""
        config = {"accepted_extensions": [".mp4", ".mov", ".avi"]}
        validator = FormatValidator(config)

        # Valid extensions should pass
        assert validator.is_extension_allowed("video.mp4") is True
        assert validator.is_extension_allowed("clip.MOV") is True  # Case insensitive
        assert validator.is_extension_allowed("/path/to/file.avi") is True

    def test_validator_rejects_unsupported_extensions(self):
        """Should reject files with extensions not in allowlist."""
        config = {"accepted_extensions": [".mp4", ".mov"]}
        validator = FormatValidator(config)

        # Invalid extensions should fail
        assert validator.is_extension_allowed("document.txt") is False
        assert validator.is_extension_allowed("video.mkv") is False
        assert validator.is_extension_allowed("file.pdf") is False

    def test_validator_handles_no_extension(self):
        """Should reject files with no extension."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        assert validator.is_extension_allowed("video") is False
        assert validator.is_extension_allowed("") is False

    @patch("cv2.VideoCapture")
    def test_opencv_openability_check_success(self, mock_video_capture):
        """Should validate file can be opened by OpenCV VideoCapture."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        # Mock successful VideoCapture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30  # Mock frame count
        mock_video_capture.return_value = mock_cap

        # Should not raise exception
        validator.validate_openability("test.mp4")

        # Verify VideoCapture was called and released
        mock_video_capture.assert_called_once_with("test.mp4")
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_opencv_openability_check_failure(self, mock_video_capture):
        """Should raise UploadRejectedError if OpenCV cannot open file."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        # Mock failed VideoCapture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        with pytest.raises(UploadRejectedError, match="could not be opened"):
            validator.validate_openability("corrupted.mp4")

        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_opencv_zero_frames_rejection(self, mock_video_capture):
        """Should reject files with zero frames."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        # Mock VideoCapture that opens but has no frames
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 0  # Zero frames
        mock_video_capture.return_value = mock_cap

        with pytest.raises(UploadRejectedError, match="no video frames"):
            validator.validate_openability("empty.mp4")

    def test_full_validation_success(self):
        """Should pass full validation for valid file."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        with patch.object(validator, "validate_openability") as mock_openability:
            # Should not raise any exceptions
            validator.validate_file("video.mp4")

            # Should check both extension and openability
            mock_openability.assert_called_once_with("video.mp4")

    def test_full_validation_extension_failure(self):
        """Should fail validation on unsupported extension."""
        config = {"accepted_extensions": [".mp4"]}
        validator = FormatValidator(config)

        with pytest.raises(UploadRejectedError, match="not supported"):
            validator.validate_file("document.txt")

    def test_validator_creation_from_config(self):
        """Should create validator with configuration."""
        config = {
            "accepted_extensions": [".mp4", ".mov", ".avi"],
            "max_upload_bytes": 1000000,
        }

        validator = FormatValidator(config)

        assert validator.accepted_extensions == [".mp4", ".mov", ".avi"]
        assert validator.max_upload_bytes == 1000000
