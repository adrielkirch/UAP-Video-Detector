"""
Video session management for single active video.

Manages upload, replacement, and clearing of video files per data model
specification with proper resource management.
"""

import cv2
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .config import load_video_player_config
from .format_validator import FormatValidator
from .exceptions import UploadRejectedError


@dataclass
class ActiveVideo:
    """
    Active video metadata per data model specification.

    Represents the single video loaded for the current session.
    """

    id: str
    display_name: str
    path: str
    duration_ms: int
    frame_count: int
    fps: float
    status: str  # 'ready' | 'invalid' | 'cleared'


class VideoSession:
    """
    Single-video session manager implementing contract API.

    Enforces single active video rule with proper validation and
    resource management per project constitution.
    """

    def __init__(self, config_path: str = "config/video_player.yaml"):
        """
        Initialize video session with configuration.

        Args:
            config_path: Path to video player configuration file
        """
        try:
            self._config = load_video_player_config(config_path)
        except (FileNotFoundError, ValueError):
            # Fallback to minimal config if file missing/invalid
            self._config = {
                "accepted_extensions": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
                "max_upload_bytes": 0,
                "raw_dir": "data/raw",
                "copy_uploads_to_raw": False,
                "seek_step_ms": 1000,
            }

        self._validator = FormatValidator(self._config)
        self._active_video: Optional[ActiveVideo] = None
        self.last_error: Optional[str] = None
        self._playback_callbacks = []  # Callbacks for playback controller

    def get_active(self) -> Optional[ActiveVideo]:
        """
        Get currently active video.

        Returns:
            ActiveVideo if one is loaded, None otherwise
        """
        return self._active_video

    def set_from_path(self, path: str) -> ActiveVideo:
        """
        Set active video from file path with validation.

        Args:
            path: Path to video file

        Returns:
            ActiveVideo instance for the loaded video

        Raises:
            UploadRejectedError: If file validation fails

        Note:
            On success: replaces any prior active video
            On failure: leaves prior active video unchanged
        """
        # Store current state to restore on failure
        prior_active = self._active_video

        try:
            # Validate file format and openability
            self._validator.validate_file(path)

            # Extract metadata using OpenCV
            cap = cv2.VideoCapture(path)
            try:
                if not cap.isOpened():
                    raise UploadRejectedError(
                        f"Could not open video file: {Path(path).name}",
                        details=f"OpenCV VideoCapture failed for {path}",
                    )

                # Get video metadata
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)

                # Calculate duration
                if fps > 0 and frame_count > 0:
                    duration_ms = int((frame_count / fps) * 1000)
                else:
                    duration_ms = 0

            finally:
                cap.release()

            # Create new active video
            active_video = ActiveVideo(
                id=uuid4().hex,
                display_name=Path(path).name,
                path=str(path),
                duration_ms=duration_ms,
                frame_count=frame_count,
                fps=fps,
                status="ready",
            )

            # Replace active video (release prior resources if any)
            if self._active_video is not None:
                # Notify playback controller about video change
                self._notify_video_changed()

            self._active_video = active_video
            self.last_error = None

            # Notify playback controller about new video
            self._notify_video_changed()

            return active_video

        except UploadRejectedError:
            # Restore prior state on validation failure
            self._active_video = prior_active
            raise
        except Exception as e:
            # Handle unexpected errors
            self._active_video = prior_active
            raise UploadRejectedError(
                f"Failed to load video: {Path(path).name}", details=str(e)
            )

    def clear(self) -> None:
        """
        Clear active video and release resources.

        Sets active video to None and notifies any attached components
        (playback, scan) to reset their state.
        """
        if self._active_video is not None:
            # Notify playback controller and scan pipeline to reset state
            self._notify_video_changed()

        self._active_video = None
        self.last_error = None

        # Notify again after clearing
        self._notify_video_changed()

    def add_playback_callback(self, callback):
        """Add callback to be notified on video changes."""
        self._playback_callbacks.append(callback)

    def _notify_video_changed(self):
        """Notify all callbacks about video change."""
        for callback in self._playback_callbacks:
            try:
                callback()
            except Exception:
                # Ignore callback errors to prevent breaking video operations
                pass
