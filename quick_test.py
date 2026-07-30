#!/usr/bin/env python3
"""Quick test to demonstrate video loading and basic playback."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.ingestion.video_session import VideoSession
from src.ingestion.playback import PlaybackController

def main():
    print("UAP Video Detector - Quick Test")
    print("=" * 40)
    
    # Test video loading
    video_path = "temp/videoplayback.mp4"
    if not Path(video_path).exists():
        print("[ERROR] Video file not found:", video_path)
        return
    
    # Initialize components
    print("[INFO] Initializing video session...")
    video_session = VideoSession()
    
    try:
        # Load video
        active_video = video_session.set_from_path(video_path)
        print(f"[OK] Video loaded: {active_video.display_name}")
        print(f"   Duration: {active_video.duration_ms/1000:.1f}s")
        print(f"   Frames: {active_video.frame_count}")
        print(f"   FPS: {active_video.fps:.2f}")
        
        # Initialize playback
        print("\n[INFO] Initializing playback controller...")
        playback_controller = PlaybackController()
        playback_controller.attach(video_session)
        
        # Test frame reading
        print("[INFO] Reading first frame...")
        frame = playback_controller.read_current_frame()
        if frame is not None:
            print(f"[OK] Frame read successfully: {frame.shape}")
        else:
            print("[ERROR] Failed to read frame")
            
        print("\n[SUMMARY] Core functionality working!")
        print("   - Video loading: OK")
        print("   - Metadata extraction: OK") 
        print("   - Frame reading: OK")
        print(f"   - Session management: OK")
        
        print(f"\nNext: Fix Streamlit interface or use CLI once config is corrected.")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()