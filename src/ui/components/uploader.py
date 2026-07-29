"""
Streamlit uploader widget helpers for video file uploads.

Provides UI components for video upload with proper session integration
and user feedback. Follows loose coupling principle - no YOLO imports.
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Tuple

from ...ingestion.video_session import VideoSession
from ...ingestion.exceptions import UploadRejectedError


def render_video_uploader(
    session: VideoSession, key: str = "video_uploader"
) -> Tuple[bool, Optional[str]]:
    """
    Render video file uploader widget with session integration.

    Args:
        session: VideoSession instance to manage uploads
        key: Unique key for Streamlit widget

    Returns:
        Tuple of (upload_occurred, error_message)
        upload_occurred: True if new file was uploaded
        error_message: Error message if upload failed, None if successful
    """
    upload_occurred = False
    error_message = None

    st.subheader("📁 Video Upload")

    # Show current active video status
    active_video = session.get_active()
    if active_video:
        st.success(f"✅ Active video: **{active_video.display_name}**")

        # Show video metadata if available
        if active_video.duration_ms > 0:
            duration_sec = active_video.duration_ms / 1000
            st.caption(
                f"Duration: {duration_sec:.1f}s | "
                f"Frames: {active_video.frame_count} | "
                f"FPS: {active_video.fps:.1f}"
            )

        # Clear button
        if st.button("🗑️ Clear Video", key=f"{key}_clear"):
            session.clear()
            st.rerun()
    else:
        st.info("No video loaded. Upload a video file to begin.")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        key=key,
        help="Supported formats: MP4, MOV, AVI, MKV, WEBM",
    )

    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily
            temp_path = Path("temp") / uploaded_file.name
            temp_path.parent.mkdir(exist_ok=True)

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Set as active video in session
            session.set_from_path(str(temp_path))
            upload_occurred = True

            st.success(f"✅ Successfully loaded: **{uploaded_file.name}**")

            # Auto-rerun to update UI
            st.rerun()

        except UploadRejectedError as e:
            error_message = str(e)
            st.error(f"❌ Upload failed: {error_message}")

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            st.error(f"❌ Upload failed: {error_message}")

    return upload_occurred, error_message


def render_upload_status(session: VideoSession) -> None:
    """
    Render upload status information and controls.

    Args:
        session: VideoSession instance to display status for
    """
    active_video = session.get_active()

    if active_video:
        # Show detailed status
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Current Video:** {active_video.display_name}")
                if active_video.duration_ms > 0:
                    st.caption(
                        f"ID: `{active_video.id[:8]}...` | Status: `{active_video.status}`"
                    )

            with col2:
                if st.button("📋 Details", key="video_details"):
                    st.json(
                        {
                            "id": active_video.id,
                            "display_name": active_video.display_name,
                            "path": active_video.path,
                            "duration_ms": active_video.duration_ms,
                            "frame_count": active_video.frame_count,
                            "fps": round(active_video.fps, 2),
                            "status": active_video.status,
                        }
                    )

    # Show last error if any
    if session.last_error:
        st.warning(f"⚠️ Last error: {session.last_error}")


def show_upload_notice(message: str, notice_type: str = "info") -> None:
    """
    Show upload-related notice to user.

    Args:
        message: Notice message to display
        notice_type: Type of notice ('info', 'success', 'warning', 'error')
    """
    if notice_type == "success":
        st.success(message)
    elif notice_type == "warning":
        st.warning(message)
    elif notice_type == "error":
        st.error(message)
    else:
        st.info(message)
