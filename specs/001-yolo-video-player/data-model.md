# Data Model: YOLO Video Player & Aerial Object Scanner

**Feature**: `001-yolo-video-player` | **Date**: 2026-07-29  
**Source**: Entities from [spec.md](./spec.md)

---

## Entities

### ActiveVideo

Represents the single video loaded for the session.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Stable session id (e.g. UUID) |
| display_name | string | Original filename for UI |
| path | path | Absolute/local path to readable file |
| duration_ms | int ≥ 0 | Duration if known; 0 if unknown |
| frame_count | int ≥ 0 | Total frames if known |
| fps | float > 0 | Nominal FPS if known |
| status | enum | `ready` \| `invalid` \| `cleared` |
| width | int ≥ 0 | Frame width in pixels if known; 0 if unknown |
| height | int ≥ 0 | Frame height in pixels if known; 0 if unknown |

**Validation**:
- Path must exist and pass format validator + OpenCV open
- Only one `ActiveVideo` with status `ready` per session

**Relationships**: Owned by `VideoSession` (0..1)

---

### VideoSession

Session container enforcing single-video rule.

| Field | Type | Description |
|-------|------|-------------|
| active_video | ActiveVideo \| null | Current video or none |
| last_error | string \| null | Last user-facing upload/session error |

**State transitions**:

```text
[empty] --upload valid--> [ready]
[ready] --upload valid--> [ready]  (replace; prior capture released)
[ready] --upload invalid--> [ready] (unchanged + last_error)
[ready] --clear--> [empty]
[empty] --upload invalid--> [empty] (+ last_error)
```

---

### PlaybackSession

| Field | Type | Description |
|-------|------|-------------|
| state | enum | `stopped` \| `playing` \| `paused` |
| position_ms | int ≥ 0 | Current timestamp |
| position_frame | int ≥ 0 | Current frame index |
| duration_ms | int ≥ 0 | Mirror of active video duration when known |

**State transitions**:

```text
stopped --play--> playing
playing --pause--> paused
paused --play--> playing
playing|paused --stop--> stopped (position → 0)
any --seek(ms|frame)--> same state, updated position (clamped)
any --video cleared/replaced--> stopped @ 0
```

**Validation**:
- Seek targets clamped to `[0, duration]`
- Controls no-op with clear error if no `ActiveVideo`

---

### ScanSession

| Field | Type | Description |
|-------|------|-------------|
| enabled | bool | User toggle |
| detector_ready | bool | Model loaded successfully |
| last_frame_detections | FrameDetections \| null | Latest result for overlay/pause |
| last_error | string \| null | Load/scan errors (non-fatal to player) |

**State transitions**:

```text
enabled=false (default)
enabled=true + lazy load success → detector_ready=true
enabled=true + load fail → detector_ready=false, last_error set, player continues
enabled=false → stop issuing new inferences; keep last overlay optional
video clear/replace → reset detections; disable or keep toggle per config (default: keep toggle, clear detections)
```

---

### Detection

One object instance on a frame.

| Field | Type | Description |
|-------|------|-------------|
| class_name | enum/string | `airplane` \| `helicopter` \| `bird` \| `drone` (MVP set) |
| confidence | float 0..1 | Strength indicator |
| bbox_xyxy | [x1,y1,x2,y2] | Pixel coords on source frame (optional if list-only UI) |
| track_id | int \| null | Reserved; unused in MVP |

**Validation**:
- Only configured target classes emitted to UI (filter others)
- Confidence below configured threshold discarded before emit

---

### FrameDetections

| Field | Type | Description |
|-------|------|-------------|
| frame_index | int ≥ 0 | Source frame |
| timestamp_ms | int ≥ 0 | Approx time |
| items | list[Detection] | Zero or more |

---

### DetectorCapability (config-bound)

| Field | Type | Description |
|-------|------|-------------|
| backend | string | e.g. `yolo_world` \| `yolov8` \| `null` |
| weights_path | path \| null | Local weights; null → download policy via config |
| class_prompts | list[string] | Default four MVP labels |
| confidence_threshold | float | Externalized |
| device | string | `auto` \| `cpu` \| `cuda` |
| frame_stride | int ≥ 1 | Infer every Nth frame while playing |

---

## Cross-entity rules

1. No `PlaybackSession` activity without `VideoSession.active_video`.
2. `ScanSession` may be enabled without detector ready — player still works; show notice.
3. Clearing video resets playback position and clears `last_frame_detections`.
4. Detector never stores the video file; it only receives frames (numpy arrays) + metadata.
