"""
Video format validation for upload acceptance.

Validates file extensions and OpenCV openability per project constitution
parameterized configuration principle.
"""

import cv2
from pathlib import Path
from typing import Dict, Any

from .exceptions import UploadRejectedError


class FormatValidator:
    """
    Validates video file formats for upload acceptance.

    Checks both extension allowlist and OpenCV openability to ensure
    files can be processed by the video pipeline.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.

        Args:
            config: Configuration dict containing 'accepted_extensions' list
        """
        self.accepted_extensions = config.get("accepted_extensions", [])
        self.max_upload_bytes = config.get("max_upload_bytes", 0)  # 0 = unlimited

    def is_extension_allowed(self, file_path: str) -> bool:
        """
        Check if file extension is in the allowed list.

        Args:
            file_path: Path to the file to check

        Returns:
            True if extension is allowed, False otherwise
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if not extension:
            return False

        # Case-insensitive comparison
        allowed_extensions_lower = [ext.lower() for ext in self.accepted_extensions]
        return extension in allowed_extensions_lower

    def validate_openability(self, file_path: str) -> None:
        """
        Validate that OpenCV can open and read the video file.

        Args:
            file_path: Path to video file to validate

        Raises:
            UploadRejectedError: If file cannot be opened or has no frames
        """
        cap = cv2.VideoCapture(file_path)

        try:
            if not cap.isOpened():
                raise UploadRejectedError(
                    f"Video file could not be opened: {Path(file_path).name}",
                    details=f"OpenCV VideoCapture failed to open {file_path}",
                )

            # Check for frames
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if frame_count <= 0:
                raise UploadRejectedError(
                    f"Video file contains no video frames: {Path(file_path).name}",
                    details=f"Frame count: {frame_count}",
                )

        finally:
            cap.release()

    def validate_file(self, file_path: str) -> None:
        """
        Perform full validation on video file.

        Args:
            file_path: Path to video file to validate

        Raises:
            UploadRejectedError: If file fails any validation check
        """
        # Check extension first (fast check)
        if not self.is_extension_allowed(file_path):
            file_name = Path(file_path).name
            extension = Path(file_path).suffix or "(no extension)"

            raise UploadRejectedError(
                f"File format {extension} not supported. "
                f"Supported formats: {', '.join(self.accepted_extensions)}",
                details=f"Rejected file: {file_name}",
            )

        # Check OpenCV compatibility (slower check)
        self.validate_openability(file_path)
