# Contract: UI Session (Streamlit Shell)

**Feature**: `001-yolo-video-player`  
**Entry**: `src/ui/app.py`

## User-visible capabilities

| Action | Behavior |
|--------|----------|
| Upload file | File picker → `VideoSession.set_from_path`; show name/duration or error |
| Replace | New upload replaces active; toast/notice “Previous video replaced” |
| Clear / Remove | Button → `clear()`; controls disabled until next upload |
| Play / Pause / Stop | Bound to `PlaybackController` |
| Seek | Slider or equivalent in milliseconds (or % of duration) |
| Toggle Live Scan | Enables/disables `ScanSession`; does not reset playhead |
| Overlay | Draw bboxes + class + confidence on current frame image when detections exist |

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
