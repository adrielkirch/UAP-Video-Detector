"""
Main Streamlit application for UAP Video Detector.

Provides web interface for video upload, playback, and detection
with proper session state management per project constitution.
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ingestion.video_session import VideoSession
from src.ingestion.playback import PlaybackController
from src.orchestration.scan_pipeline import ScanPipeline
from src.inference.factory import DetectorFactory
from src.ui.components.uploader import render_video_uploader, render_upload_status
from src.ui.components.player_controls import (
    render_playback_controls,
    render_progress_display,
    render_seek_control,
    render_playback_status,
)
from src.ui.components.detection_overlay import (
    draw_detections_on_frame,
    draw_scan_status,
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "video_session" not in st.session_state:
        st.session_state.video_session = VideoSession()

    if "playback_controller" not in st.session_state:
        st.session_state.playback_controller = PlaybackController()

        # Wire playback controller to video session
        st.session_state.video_session.add_playback_callback(
            st.session_state.playback_controller.on_video_changed
        )
        st.session_state.playback_controller.attach(st.session_state.video_session)

    if "scan_pipeline" not in st.session_state:
        st.session_state.scan_pipeline = ScanPipeline()

        # Initialize detector via factory
        factory = DetectorFactory()
        try:
            detector = factory.create_detector("config/detector.yaml")
            st.session_state.detector_status = "ready"
        except Exception as e:
            # Fall back to safe detector (null)
            detector = factory.create_safe_detector("config/detector.yaml")
            st.session_state.detector_status = f"unavailable: {str(e)}"

        # Store detector info for UI
        st.session_state.detector = detector

        # Wire scan pipeline
        st.session_state.scan_pipeline.attach_detector(detector)
        st.session_state.scan_pipeline.attach_playback(
            st.session_state.playback_controller
        )

    if "scan_enabled" not in st.session_state:
        st.session_state.scan_enabled = False


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(page_title="UAP Video Detector", page_icon="🛸", layout="wide")

    initialize_session_state()

    st.title("🛸 UAP Video Detector")
    st.markdown(
        "*Filter out the knowns to isolate the unknowns*\n\n"
        "Upload and analyze video footage for unidentified aerial phenomena."
    )

    # Sidebar for upload controls
    with st.sidebar:
        st.header("📁 Video Management")

        # Video upload section
        upload_occurred, upload_error = render_video_uploader(
            st.session_state.video_session, key="main_uploader"
        )

        # Upload status
        render_upload_status(st.session_state.video_session)

        st.divider()

        # Scan controls (placeholder for future phases)
        st.header("🔍 Detection Settings")
        scan_enabled = st.toggle(
            "Enable Live Scan",
            value=st.session_state.scan_enabled,
            help="Real-time YOLO detection (requires active video)",
            disabled=st.session_state.video_session.get_active() is None,
        )
        st.session_state.scan_enabled = scan_enabled

        if scan_enabled and st.session_state.video_session.get_active() is None:
            st.warning("⚠️ Live scan requires an active video")

    # Main content area
    active_video = st.session_state.video_session.get_active()

    if active_video is None:
        # No video loaded state
        st.info(
            "👆 **Get Started:** Upload a video file using the sidebar to begin analysis."
        )

        # Show project information
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Supported Formats")
            st.markdown("""
            - **MP4** (.mp4)
            - **QuickTime** (.mov)
            - **AVI** (.avi)
            - **Matroska** (.mkv)
            - **WebM** (.webm)
            """)

        with col2:
            st.subheader("🔍 Detection Classes")
            st.markdown("""
            - ✈️ **Airplane**
            - 🚁 **Helicopter**
            - 🐦 **Bird**
            - 🚀 **Drone**
            """)

    else:
        # Video loaded state
        st.success(f"📹 **Active Video:** {active_video.display_name}")

        # Video player controls
        with st.container():
            st.subheader("🎮 Video Player")

            # Playback controls
            render_playback_controls(
                st.session_state.playback_controller, key="main_playback_controls"
            )

            # Progress display
            playback_state = st.session_state.playback_controller.get_state()
            if playback_state:
                render_progress_display(playback_state, key="main_progress")

                # Seek control
                render_seek_control(
                    st.session_state.playback_controller, key="main_seek"
                )

            # Status display
            render_playback_status(playback_state)

        # Live scan controls
        with st.container():
            st.subheader("🔍 Live Aerial Object Scanner")

            # Show detector status
            if st.session_state.detector_status != "ready":
                st.warning(f"⚠️ **Scanner Notice:** {st.session_state.detector_status}")
                st.info(
                    "🎮 **Player continues normally** - Upload and playback are fully functional"
                )

            col1, col2 = st.columns(2)

            with col1:
                # Scan toggle
                if st.button(
                    (
                        "🟢 Enable Scan"
                        if not st.session_state.scan_enabled
                        else "🔴 Disable Scan"
                    ),
                    key="scan_toggle",
                ):
                    st.session_state.scan_enabled = not st.session_state.scan_enabled

                    if st.session_state.scan_enabled:
                        st.session_state.scan_pipeline.enable_scan()
                        st.success("✅ Live scan enabled")
                    else:
                        st.session_state.scan_pipeline.disable_scan()
                        st.info("⏸️ Live scan disabled")
                    st.rerun()

            with col2:
                # Scan status
                if st.session_state.scan_enabled:
                    st.success("🔍 **Status:** Scanning enabled")
                else:
                    st.info("⏸️ **Status:** Scanning disabled")

                # Show last detections count
                last_detections = st.session_state.scan_pipeline.get_last_detections()
                if last_detections:
                    detection_count = len(last_detections.detections)
                    if detection_count > 0:
                        st.caption(f"🎯 Last scan: {detection_count} objects detected")
                    else:
                        st.caption("🔍 Last scan: No objects detected")

        # Frame display with overlays
        with st.container():
            st.subheader("📺 Video Display")

            # Get current frame from playback
            current_frame = st.session_state.playback_controller.read_current_frame()

            if current_frame is not None:
                # Process frame for detection if scan enabled
                if st.session_state.scan_enabled and playback_state.state == "playing":
                    # Process current frame
                    detections = st.session_state.scan_pipeline.process_frame(
                        current_frame, frame_index=playback_state.position_frame
                    )
                else:
                    # Use last cached detections when paused or scan disabled
                    detections = st.session_state.scan_pipeline.get_last_detections()

                # Draw overlays on frame
                if detections is not None and len(detections.detections) > 0:
                    current_frame = draw_detections_on_frame(current_frame, detections)

                # Draw scan status indicator
                draw_scan_status(
                    current_frame,
                    st.session_state.scan_enabled,
                    st.session_state.scan_pipeline.last_lag_warning,
                )

                # Display frame with overlays
                st.image(
                    current_frame,
                    channels="BGR",
                    caption="Video with Detection Overlays",
                    key="main_frame_with_overlays",
                )

                # Performance info
                if st.session_state.scan_pipeline.last_infer_duration_ms > 0:
                    st.caption(
                        f"⚡ Last inference: {st.session_state.scan_pipeline.last_infer_duration_ms:.0f}ms"
                    )

                # Lag warning
                if st.session_state.scan_pipeline.last_lag_warning:
                    st.warning(f"⚠️ {st.session_state.scan_pipeline.last_lag_warning}")

            else:
                st.info("📺 No frame available")

        # Placeholder for detection overlay (Phase 5 implementation)
        if st.session_state.scan_enabled:
            st.subheader("🎯 Detection Results")
            st.info(
                "🚧 **Live detection will be implemented in Phase 5**\n\n"
                "YOLO-based aerial object detection will overlay on video frames."
            )

    # Footer
    st.divider()
    st.caption(
        "UAP Video Detector | Phase 3: Upload Management | "
        "Open Source AGPL-3.0 | Filter the knowns, isolate the unknowns"
    )


if __name__ == "__main__":
    main()
