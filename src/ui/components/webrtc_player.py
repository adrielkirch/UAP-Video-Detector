"""
streamlit-webrtc video layer for real-time playback, seek, and YOLO overlays.

Replaces st.image() + st.rerun() loops with webrtc_streamer and a
VideoProcessorBase.recv() callback. Timeline seek restarts MediaPlayer
at an ffmpeg start offset — that is a user action, not a frame loop.
"""

from pathlib import Path
from typing import Optional

import av
import cv2
import numpy as np
import streamlit as st
from aiortc.contrib.media import MediaPlayer
from streamlit_webrtc import VideoProcessorBase, WebRtcMode, webrtc_streamer

from src.orchestration.scan_pipeline import ScanPipeline
from src.ui.components.detection_overlay import (
    draw_detections_on_frame,
    draw_scan_status,
)
from src.ui.components.player_layout import player_display_box

RTC_CONFIGURATION = {
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
}


def player_shell_css(box: dict) -> str:
    """CSS that sizes the WebRTC iframe to the source aspect ratio."""
    return f"""
<style>
div:has(> iframe[title*="streamlit_webrtc"]) {{
  position: relative !important;
  width: {box["width_css"]} !important;
  max-width: 100% !important;
  aspect-ratio: {box["aspect_ratio"]};
  max-height: {box["max_height_vh"]}vh;
  height: auto !important;
  margin-left: auto !important;
  margin-right: auto !important;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}}
div:has(> iframe[title*="streamlit_webrtc"]) iframe {{
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  border: 0 !important;
  background: #000;
}}
</style>
"""


def format_timestamp_ms(time_ms: int) -> str:
    """Format milliseconds as MM:SS or H:MM:SS."""
    total_seconds = max(0, int(time_ms // 1000))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def clamp_seek_ms(position_ms: int, duration_ms: int) -> int:
    """Keep a seek position inside [0, duration]."""
    if duration_ms <= 0:
        return 0
    return max(0, min(int(position_ms), duration_ms))


def current_playback_ms(seek_offset_ms: int, frame_index: int, fps: float) -> int:
    """Elapsed media time from seek offset plus frames already streamed."""
    if fps <= 0:
        return max(0, int(seek_offset_ms))
    return max(0, int(seek_offset_ms + (frame_index / fps) * 1000))


def draw_timestamp_overlay(
    frame: np.ndarray, current_ms: int, duration_ms: int
) -> None:
    """Draw current / duration timestamp on the lower-left of the frame."""
    label = f"{format_timestamp_ms(current_ms)} / {format_timestamp_ms(duration_ms)}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1
    (text_width, text_height), baseline = cv2.getTextSize(
        label, font, font_scale, thickness
    )
    height, _width = frame.shape[:2]
    x = 10
    y = height - 12
    cv2.rectangle(
        frame,
        (x - 4, y - text_height - 6),
        (x + text_width + 6, y + baseline + 4),
        (0, 0, 0),
        -1,
    )
    cv2.putText(
        frame,
        label,
        (x, y),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
    )


def annotate_frame(
    frame: np.ndarray,
    scan_pipeline: Optional[ScanPipeline],
    scan_enabled: bool,
    frame_index: int,
    *,
    seek_offset_ms: int = 0,
    fps: float = 0.0,
    duration_ms: int = 0,
) -> np.ndarray:
    """
    Run optional YOLO scan and draw overlays on a BGR frame.

    Args:
        frame: Incoming OpenCV BGR frame
        scan_pipeline: Existing ScanPipeline, or None
        scan_enabled: Whether live scan is on
        frame_index: Sequential frame counter for stride skipping
        seek_offset_ms: Timeline start offset for this stream
        fps: Source video frames per second
        duration_ms: Source video duration

    Returns:
        Annotated copy of the input frame
    """
    working = frame.copy()
    detections = None
    lag_warning = None

    if scan_enabled and scan_pipeline is not None:
        if not scan_pipeline.is_enabled():
            scan_pipeline.enable_scan()

        processed = scan_pipeline.process_frame(working, frame_index=frame_index)
        detections = (
            processed
            if processed is not None
            else scan_pipeline.get_last_detections()
        )
        lag_warning = scan_pipeline.last_lag_warning

        if detections is not None:
            working = draw_detections_on_frame(working, detections)

    draw_scan_status(working, scan_enabled, lag_warning)

    playhead_ms = current_playback_ms(seek_offset_ms, frame_index, fps)
    if duration_ms > 0:
        playhead_ms = min(playhead_ms, duration_ms)
    draw_timestamp_overlay(working, playhead_ms, duration_ms)
    return working


class DetectionVideoProcessor(VideoProcessorBase):
    """WebRTC frame callback that overlays ScanPipeline detections."""

    def __init__(self) -> None:
        self.scan_pipeline: Optional[ScanPipeline] = None
        self.scan_enabled: bool = False
        self.seek_offset_ms: int = 0
        self.fps: float = 0.0
        self.duration_ms: int = 0
        self._frame_index: int = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        annotated = annotate_frame(
            image,
            self.scan_pipeline,
            self.scan_enabled,
            self._frame_index,
            seek_offset_ms=self.seek_offset_ms,
            fps=self.fps,
            duration_ms=self.duration_ms,
        )
        self._frame_index += 1
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")


def create_media_player(video_path: str, start_seconds: float = 0.0) -> MediaPlayer:
    """Create an aiortc MediaPlayer starting at an optional timestamp."""
    options = None
    if start_seconds > 0:
        options = {"ss": f"{start_seconds:.3f}"}
    return MediaPlayer(str(Path(video_path)), options=options)


def _apply_processor_state(
    processor: DetectionVideoProcessor,
    *,
    scan_pipeline: ScanPipeline,
    scan_enabled: bool,
    seek_offset_ms: int,
    fps: float,
    duration_ms: int,
) -> None:
    processor.scan_pipeline = scan_pipeline
    processor.scan_enabled = scan_enabled
    processor.seek_offset_ms = seek_offset_ms
    processor.fps = fps
    processor.duration_ms = duration_ms


def render_timeline_controls(
    *,
    duration_ms: int,
    seek_ms: int,
    seek_step_ms: int,
    skip_step_ms: int,
    key: str,
) -> int:
    """
    Render skip buttons, timestamp label, and a seek slider under the player.

    Returns the updated seek position in milliseconds.
    """
    if duration_ms <= 0:
        st.caption("Timeline unavailable — video duration is unknown.")
        return 0

    position = clamp_seek_ms(seek_ms, duration_ms)
    back_col, time_col, forward_col = st.columns([1, 3, 1])

    with back_col:
        if st.button(
            f"-{format_timestamp_ms(skip_step_ms)}",
            key=f"{key}_back",
            use_container_width=True,
        ):
            position = clamp_seek_ms(position - skip_step_ms, duration_ms)
            st.session_state.pop(f"{key}_slider", None)

    with time_col:
        st.markdown(
            f"<div style='text-align:center;padding-top:0.35rem'>"
            f"<strong>{format_timestamp_ms(position)}</strong>"
            f" / {format_timestamp_ms(duration_ms)}</div>",
            unsafe_allow_html=True,
        )

    with forward_col:
        if st.button(
            f"+{format_timestamp_ms(skip_step_ms)}",
            key=f"{key}_forward",
            use_container_width=True,
        ):
            position = clamp_seek_ms(position + skip_step_ms, duration_ms)
            st.session_state.pop(f"{key}_slider", None)

    duration_s = max(1, duration_ms // 1000)
    step_s = max(1, seek_step_ms // 1000)
    position_s = min(position // 1000, duration_s)
    slider_s = st.slider(
        "Timeline",
        min_value=0,
        max_value=duration_s,
        value=position_s,
        step=step_s,
        key=f"{key}_slider",
        label_visibility="collapsed",
        help="Drag to jump to a timestamp. Playback restarts from that point.",
    )
    return clamp_seek_ms(slider_s * 1000, duration_ms)


def render_webrtc_player(
    video_path: str,
    *,
    scan_pipeline: ScanPipeline,
    scan_enabled: bool,
    stream_key: str,
    start_ms: int = 0,
    fps: float = 0.0,
    duration_ms: int = 0,
    resume_playback: bool = False,
    frame_width: int = 0,
    frame_height: int = 0,
    max_height_vh: int = 70,
):
    """
    Render the unified WebRTC player for the active video file.

    Args:
        video_path: Path to the uploaded video
        scan_pipeline: Shared ScanPipeline instance
        scan_enabled: Current live-scan toggle
        stream_key: Unique webrtc_streamer key (include video id)
        start_ms: Timeline offset where MediaPlayer should begin
        fps: Source fps for on-frame timestamps
        duration_ms: Source duration for on-frame timestamps
        resume_playback: Auto-start after a seek so START is not required again
        frame_width: Native video width in pixels
        frame_height: Native video height in pixels
        max_height_vh: Viewport-height cap for the player box
    """
    box = player_display_box(frame_width, frame_height, max_height_vh)
    st.markdown(player_shell_css(box), unsafe_allow_html=True)

    start_seconds = max(0.0, start_ms / 1000.0)

    def player_factory() -> MediaPlayer:
        return create_media_player(video_path, start_seconds=start_seconds)

    def processor_factory() -> DetectionVideoProcessor:
        processor = DetectionVideoProcessor()
        _apply_processor_state(
            processor,
            scan_pipeline=scan_pipeline,
            scan_enabled=scan_enabled,
            seek_offset_ms=start_ms,
            fps=fps,
            duration_ms=duration_ms,
        )
        return processor

    ctx = webrtc_streamer(
        key=stream_key,
        mode=WebRtcMode.RECVONLY,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": True},
        player_factory=player_factory,
        video_processor_factory=processor_factory,
        async_processing=True,
        desired_playing_state=True if resume_playback else None,
        video_html_attrs={
            "style": {
                "width": "100%",
                "height": "100%",
                "objectFit": "contain",
                "backgroundColor": "#000",
            },
            "controls": False,
            "playsInline": True,
        },
    )

    if ctx.video_processor:
        _apply_processor_state(
            ctx.video_processor,
            scan_pipeline=scan_pipeline,
            scan_enabled=scan_enabled,
            seek_offset_ms=start_ms,
            fps=fps,
            duration_ms=duration_ms,
        )

    return ctx
