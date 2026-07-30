#!/usr/bin/env python3
"""Debug script to test video loading functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ingestion.video_session import VideoSession

def test_video_loading():
    """Test video loading with the uploaded file."""
    print("Testing video loading...")
    
    # Check if video file exists
    video_path = Path("temp/videoplayback.mp4")
    if not video_path.exists():
        print(f"[ERROR] Video file not found: {video_path}")
        return False
    
    print(f"[OK] Video file exists: {video_path} ({video_path.stat().st_size} bytes)")
    
    # Test video session
    session = VideoSession()
    
    try:
        active_video = session.set_from_path(str(video_path))
        print(f"[OK] Video loaded successfully!")
        print(f"   Display name: {active_video.display_name}")
        print(f"   Duration: {active_video.duration_ms/1000:.1f}s")
        print(f"   Frame count: {active_video.frame_count}")
        print(f"   FPS: {active_video.fps:.2f}")
        print(f"   Status: {active_video.status}")
        
        # Test get_active
        retrieved = session.get_active()
        if retrieved:
            print(f"[OK] get_active() works: {retrieved.display_name}")
        else:
            print(f"[ERROR] get_active() returned None")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Video loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_video_loading()