"""
Unit tests for ingestion exceptions with clear user messages.

Tests for upload/session exceptions that provide helpful error messages
without exposing internal implementation details.
"""


from src.ingestion.exceptions import UploadRejectedError


class TestUploadRejectedError:
    """Test upload rejection exception with user-friendly messages."""

    def test_upload_rejected_error_has_clear_message(self):
        """Should provide clear, actionable error message for users."""
        error = UploadRejectedError("File extension .txt not supported")

        assert str(error) == "File extension .txt not supported"
        assert isinstance(error, Exception)

    def test_upload_rejected_error_accepts_reason_and_details(self):
        """Should accept both reason and optional technical details."""
        reason = "Video file could not be opened"
        details = "OpenCV VideoCapture failed to initialize"

        error = UploadRejectedError(reason, details=details)

        assert error.reason == reason
        assert error.details == details
        assert str(error) == reason  # User sees reason, not technical details

    def test_upload_rejected_error_without_details_works(self):
        """Should work with just a reason, no technical details."""
        reason = "File size exceeds 2GB limit"
        error = UploadRejectedError(reason)

        assert error.reason == reason
        assert error.details is None
        assert str(error) == reason

    def test_upload_rejected_error_inheritance(self):
        """Should inherit from appropriate base exception classes."""
        error = UploadRejectedError("Test error")

        assert isinstance(error, Exception)
        assert isinstance(error, ValueError)  # User input validation error

    def test_upload_rejected_error_repr_shows_reason(self):
        """Should have helpful repr for debugging."""
        error = UploadRejectedError("Invalid format", details="Technical info")

        repr_str = repr(error)
        assert "UploadRejectedError" in repr_str
        assert "Invalid format" in repr_str
