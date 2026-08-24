"""
Main Streamlit application for UAP Video Detector.

Centered upload until a video is loaded, then an HTML5 / Plyr player
at native pixel size. YOLO overlays are baked into a temp H.264 MP4.
"""

import sys
from pathlib import Path
from typing import Optional

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.inference.factory import DetectorFactory
from src.ingestion.playback import PlaybackController
from src.ingestion.video_session import VideoSession
from src.orchestration.scan_pipeline import ScanPipeline
from src.orchestration.video_annotator import (
    annotated_output_path,
    remove_annotated_output,
    write_annotated_video,
)
from src.ui.components.native_player import (
    clear_static_video,
    render_native_player,
)
from src.ui.components.uploader import render_video_uploader


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "video_session" not in st.session_state:
        st.session_state.video_session = VideoSession()

    if "playback_controller" not in st.session_state:
        st.session_state.playback_controller = PlaybackController()
        st.session_state.video_session.add_playback_callback(
            st.session_state.playback_controller.on_video_changed
        )
        st.session_state.playback_controller.attach(st.session_state.video_session)
    else:
        st.session_state.playback_controller.attach(st.session_state.video_session)

    if "scan_pipeline" not in st.session_state:
        st.session_state.scan_pipeline = ScanPipeline()

        factory = DetectorFactory()
        try:
            detector = factory.create_detector("config/detector.yaml")
            st.session_state.detector_status = "ready"
        except Exception as exc:
            detector = factory.create_safe_detector("config/detector.yaml")
            st.session_state.detector_status = f"unavailable: {exc}"

        st.session_state.detector = detector
        st.session_state.scan_pipeline.attach_detector(detector)
        st.session_state.scan_pipeline.attach_playback(
            st.session_state.playback_controller
        )

    if "scan_enabled" not in st.session_state:
        st.session_state.scan_enabled = False

    if "annotated_path" not in st.session_state:
        st.session_state.annotated_path = None

    if "annotated_video_id" not in st.session_state:
        st.session_state.annotated_video_id = None


def _sync_scan_state(scan_enabled: bool) -> None:
    """Keep session toggle and ScanPipeline enable flags aligned."""
    st.session_state.scan_enabled = scan_enabled
    if scan_enabled:
        st.session_state.scan_pipeline.enable_scan()
    else:
        st.session_state.scan_pipeline.disable_scan()


def _clear_video_artifacts() -> None:
    """Drop staged player copies and the temp annotated MP4, keep session."""
    active = st.session_state.video_session.get_active()
    if active is not None:
        clear_static_video(active.id)
        clear_static_video(f"{active.id}-scan")
    remove_annotated_output(st.session_state.get("annotated_path"))
    st.session_state.annotated_path = None
    st.session_state.annotated_video_id = None


def _clear_session_video() -> None:
    """Release the active video and its temp annotated MP4."""
    _clear_video_artifacts()
    st.session_state.scan_enabled = False
    st.session_state.scan_pipeline.disable_scan()
    st.session_state.video_session.clear()


def _render_empty_state() -> None:
    """Central upload area shown before a video is loaded."""
    with st.container():
        render_video_uploader(
            st.session_state.video_session,
            key="main_uploader",
            heading="Upload a video to start",
            show_status=False,
            on_before_load=_clear_video_artifacts,
        )

        formats, classes = st.columns(2)
        with formats:
            st.markdown(
                "**Supported formats**  \nMP4 · MOV · AVI · MKV · WebM"
            )
        with classes:
            st.markdown(
                "**Detection classes**  \nAirplane · Helicopter · Bird · Drone"
            )


def _ensure_annotated_video(active_video) -> Optional[str]:
    """Build or reuse the temp annotated MP4 for the active clip."""
    if st.session_state.annotated_video_id != active_video.id:
        remove_annotated_output(st.session_state.get("annotated_path"))
        st.session_state.annotated_path = None
        st.session_state.annotated_video_id = None

    existing = st.session_state.get("annotated_path")
    if existing and Path(existing).exists():
        return existing

    dest = annotated_output_path(
        active_video.id,
        directory=st.session_state.video_session.get_annotated_dir(),
    )
    progress = st.progress(0, text="Applying detection overlays…")

    def on_progress(frame_index: int, total: int) -> None:
        ratio = min(1.0, frame_index / total) if total else 0.0
        progress.progress(ratio, text=f"Applying detection overlays… {frame_index}/{total}")

    try:
        written = write_annotated_video(
            active_video.path,
            str(dest),
            st.session_state.scan_pipeline,
            on_progress=on_progress,
        )
    except Exception as exc:
        progress.empty()
        st.error(f"Could not build annotated video: {exc}")
        return None

    progress.empty()
    st.session_state.annotated_path = written
    st.session_state.annotated_video_id = active_video.id
    return written


def _render_player(active_video) -> None:
    """Unified native player: video on top, scan toggle just above it."""
    with st.container():
        title_col, clear_col = st.columns([4, 1])
        with title_col:
            st.subheader(active_video.display_name)
            meta_parts = []
            if active_video.width > 0 and active_video.height > 0:
                meta_parts.append(f"{active_video.width}×{active_video.height}")
            if active_video.duration_ms > 0:
                meta_parts.append(f"{active_video.duration_ms / 1000:.1f}s")
                meta_parts.append(f"{active_video.frame_count} frames")
                meta_parts.append(f"{active_video.fps:.1f} fps")
            if meta_parts:
                st.caption(" · ".join(meta_parts))
        with clear_col:
            if st.button("Clear video", key="clear_active_video"):
                _clear_session_video()
                st.rerun()

        scan_enabled = st.toggle(
            "Enable Live Scan",
            value=st.session_state.scan_enabled,
            help="Bake YOLO boxes into a temporary MP4, then play it natively.",
        )
        _sync_scan_state(scan_enabled)

        if scan_enabled and st.session_state.detector_status != "ready":
            st.caption(f"Scanner unavailable — {st.session_state.detector_status}")

        play_path = active_video.path
        play_stem = active_video.id
        if scan_enabled and st.session_state.detector_status == "ready":
            annotated = _ensure_annotated_video(active_video)
            if annotated:
                play_path = annotated
                play_stem = f"{active_video.id}-scan"

        render_native_player(
            play_path,
            video_id=play_stem,
            frame_width=active_video.width,
            frame_height=active_video.height,
            max_width_px=st.session_state.video_session.get_player_max_width_px(),
            max_height_px=st.session_state.video_session.get_player_max_height_px(),
        )

        with st.expander("Replace video"):
            render_video_uploader(
                st.session_state.video_session,
                key="replace_uploader",
                heading=None,
                show_status=False,
                on_before_load=_clear_video_artifacts,
            )


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="UAP Video Detector", page_icon="🛸", layout="centered"
    )
    initialize_session_state()

    st.title("🛸 UAP Video Detector")
    st.caption("Filter out the knowns to isolate the unknowns")

    active_video = st.session_state.video_session.get_active()
    if active_video is None:
        _render_empty_state()
    else:
        _render_player(active_video)


if __name__ == "__main__":
    main()
