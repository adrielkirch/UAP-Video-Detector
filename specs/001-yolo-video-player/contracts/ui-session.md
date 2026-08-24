# Contract: UI Session (Streamlit Shell)

**Feature**: `001-yolo-video-player`  
**Entry**: `src/ui/app.py`

## User-visible capabilities

| Action | Behavior |
|--------|----------|
| Empty-state upload | Centered main-column file picker (no sidebar). `VideoSession.set_from_path`; then the player replaces the empty state |
| Replace | Uploader on the player page replaces active; prior annotated + static copies are deleted |
| Clear / Remove | Button → artifact cleanup + `clear()`; empty-state uploader returns |
| Play / Pause / Seek | HTML5 / Plyr controls (timeline, current time, duration) |
| Toggle Scan | Bakes overlays into a temp H.264 MP4 and plays it in the same player; off = original file |
| Overlay | Boxes + class + confidence are drawn during the bake, not via `st.image` |

## Coupling rules

- UI MAY import `ingestion` and `orchestration` facades.
- UI MUST NOT import Ultralytics or construct YOLO models directly.
- When detector not ready: show non-blocking banner; keep player usable.

## Session state keys (logical)

```text
video_session
playback
scan_enabled
last_detections
user_messages[]
```

Exact Streamlit `st.session_state` key names are implementation details but MUST map 1:1 to these concepts.
