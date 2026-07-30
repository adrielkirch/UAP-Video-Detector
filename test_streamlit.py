#!/usr/bin/env python3
"""Simple Streamlit test to debug video upload issues."""

import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ingestion.video_session import VideoSession

def main():
    st.set_page_config(page_title="UAP Video Test", page_icon="🛸")
    
    st.title("🛸 UAP Video Detector - Upload Test")
    
    # Initialize session state
    if "video_session" not in st.session_state:
        st.session_state.video_session = VideoSession()
        st.write("🔄 Initialized new video session")
    
    # Show current active video status
    active_video = st.session_state.video_session.get_active()
    
    st.subheader("📊 Current Status")
    if active_video:
        st.success(f"✅ Active video loaded: **{active_video.display_name}**")
        st.write(f"- Duration: {active_video.duration_ms/1000:.1f}s")
        st.write(f"- Frames: {active_video.frame_count}")
        st.write(f"- FPS: {active_video.fps:.2f}")
        st.write(f"- Status: {active_video.status}")
        
        if st.button("🗑️ Clear Video"):
            st.session_state.video_session.clear()
            st.rerun()
    else:
        st.info("📤 No video currently loaded")
    
    st.divider()
    
    # Simple file uploader
    st.subheader("📁 Upload Video")
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        key="video_uploader"
    )
    
    if uploaded_file is not None:
        st.write(f"📄 File selected: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        if st.button("🚀 Load Video", key="load_button"):
            try:
                # Save uploaded file
                temp_path = Path("temp") / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                
                with st.spinner("💾 Saving file..."):
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                st.success(f"📁 File saved to: {temp_path}")
                
                # Load into video session
                with st.spinner("🔄 Loading video..."):
                    loaded_video = st.session_state.video_session.set_from_path(str(temp_path))
                
                st.success(f"✅ Video loaded successfully: {loaded_video.display_name}")
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error loading video: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()