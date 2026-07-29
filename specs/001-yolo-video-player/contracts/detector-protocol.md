# Contract: AerialDetector Protocol

**Feature**: `001-yolo-video-player`  
**Consumers**: `orchestration/scan_pipeline.py`  
**Implementations**: Ultralytics adapter, `NullDetector`, future custom weights adapters

## Purpose

Define the only inference surface the rest of the app may use. UI and player MUST NOT call Ultralytics (or any YOLO SDK) directly.

## Protocol

```text
AerialDetector
  load() -> None
      # Lazy/idempotent. Raises DetectorNotReadyError on failure.
  is_ready() -> bool
  detect(frame: ndarray, *, frame_index: int, timestamp_ms: int) -> FrameDetections
      # frame: BGR or RGB per adapter docs; documented in adapter.
      # Returns only configured target classes above threshold.
  close() -> None
      # Release weights/resources; safe to call multiple times.
```

## NullDetector

- `load()` no-op; `is_ready()` → false (or true with empty detects — prefer false + notice)
- `detect(...)` → empty `FrameDetections` (or not called when not ready)
- Used when scanning disabled or backend unavailable

## Errors

| Error | When | Player impact |
|-------|------|---------------|
| `DetectorNotReadyError` | load failure / missing weights | Non-fatal; show notice; playback continues |
| `DetectorInferError` | single-frame failure | Skip frame; keep last good overlay optional |

## Compatibility

- MUST support CPU; SHOULD use CUDA when configured `device: auto|cuda` and available
- MUST NOT download weights during unit tests (inject local path or mock)
- Backend swap MUST NOT change this protocol
- Factory MUST accept at least: `null`, `yolo_world`, `yolov8`, `yolov9`, `custom` (see `config-schema.md`) — all non-null impls satisfy this protocol
