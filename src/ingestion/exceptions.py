"""
Ingestion exceptions for upload and session management.

Provides user-friendly error messages without exposing internal
implementation details per project constitution.
"""


class UploadRejectedError(ValueError):
    """
    Exception raised when a video upload is rejected.

    Provides clear, actionable error messages for users while optionally
    storing technical details for debugging.
    """

    def __init__(self, reason: str, details: str = None):
        """
        Initialize upload rejection error.

        Args:
            reason: User-facing error message explaining why upload was rejected
            details: Optional technical details for debugging (not shown to user)
        """
        super().__init__(reason)
        self.reason = reason
        self.details = details

    def __str__(self) -> str:
        """Return user-facing error message."""
        return self.reason

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        if self.details:
            return f"UploadRejectedError('{self.reason}', details='{self.details}')"
        else:
            return f"UploadRejectedError('{self.reason}')"
