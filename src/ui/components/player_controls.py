"""
Streamlit player control widgets for video playback.

Provides UI components for play/pause/seek/stop controls with proper
integration with PlaybackController. Follows loose coupling principle.
"""

import streamlit as st
from typing import Optional

from ...ingestion.playback import PlaybackController, PlaybackSession


def render_playback_controls(
    controller: PlaybackController, key: str = "playback_controls"
) -> None:
    """
    Render video playback control buttons.

    Args:
        controller: PlaybackController instance
        key: Unique key for Streamlit widgets
    """
    playback_state = controller.get_state()

    if playback_state is None:
        st.info("⚠️ No video loaded for playback")
        return

    # Create control buttons in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Play/Pause button
        if playback_state.state == "playing":
            if st.button("⏸️ Pause", key=f"{key}_pause"):
                controller.pause()
                st.rerun()
        else:
            if st.button("▶️ Play", key=f"{key}_play"):
                controller.play()
                st.rerun()

    with col2:
        # Stop button
        if st.button("⏹️ Stop", key=f"{key}_stop"):
            controller.stop()
            st.rerun()

    with col3:
        # Skip backward
        if st.button("⏮️ -10s", key=f"{key}_back"):
            current_pos = playback_state.position_ms
            controller.seek_ms(max(0, current_pos - 10000))
            st.rerun()

    with col4:
        # Skip forward
        if st.button("⏭️ +10s", key=f"{key}_forward"):
            current_pos = playback_state.position_ms
            controller.seek_ms(current_pos + 10000)
            st.rerun()


def render_progress_display(
    playback_state: PlaybackSession, key: str = "progress_display"
) -> None:
    """
    Render playback progress bar and time display.

    Args:
        playback_state: Current playback state
        key: Unique key for Streamlit widgets
    """
    # Calculate progress
    if playback_state.duration_ms > 0:
        progress = playback_state.position_ms / playback_state.duration_ms
    else:
        progress = 0.0

    # Progress bar
    st.progress(progress, key=f"{key}_bar")

    # Time display
    current_time = _format_time_ms(playback_state.position_ms)
    total_time = _format_time_ms(playback_state.duration_ms)
    st.text(f"{current_time} / {total_time}")


def render_seek_control(
    controller: PlaybackController, key: str = "seek_control"
) -> None:
    """
    Render seek slider for time-based navigation.

    Args:
        controller: PlaybackController instance
        key: Unique key for Streamlit widgets
    """
    playback_state = controller.get_state()

    if playback_state is None or playback_state.duration_ms == 0:
        return

    # Time slider
    current_position = st.slider(
        "Seek",
        min_value=0,
        max_value=playback_state.duration_ms,
        value=playback_state.position_ms,
        step=1000,  # 1 second steps
        key=f"{key}_slider",
        label_visibility="collapsed",
    )

    # Only seek if position changed
    if current_position != playback_state.position_ms:
        controller.seek_ms(current_position)
        st.rerun()


def render_playback_status(playback_state: Optional[PlaybackSession]) -> None:
    """
    Render current playback status information.

    Args:
        playback_state: Current playback state or None
    """
    if playback_state is None:
        st.info("🎬 **Status:** No video loaded")
        return

    # Status display
    status_emoji = {"playing": "▶️", "paused": "⏸️", "stopped": "⏹️"}

    emoji = status_emoji.get(playback_state.state, "❓")
    st.info(f"{emoji} **Status:** {playback_state.state.title()}")

    # Position info
    if playback_state.duration_ms > 0:
        current_time = _format_time_ms(playback_state.position_ms)
        total_time = _format_time_ms(playback_state.duration_ms)

        st.caption(
            f"**Position:** {current_time} / {total_time} "
            f"(Frame {playback_state.position_frame})"
        )


def render_frame_display(
    controller: PlaybackController, key: str = "frame_display"
) -> None:
    """
    Render current video frame display.

    Args:
        controller: PlaybackController instance
        key: Unique key for Streamlit widgets
    """
    frame = controller.read_current_frame()

    if frame is not None:
        st.image(
            frame,
            channels="BGR",  # OpenCV uses BGR format
            caption="Current Frame",
            key=f"{key}_image",
        )
    else:
        st.info("📺 No frame available")


def _format_time_ms(time_ms: int) -> str:
    """
    Format time in milliseconds as MM:SS.

    Args:
        time_ms: Time in milliseconds

    Returns:
        Formatted time string
    """
    total_seconds = int(time_ms // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02d}:{seconds:02d}"
