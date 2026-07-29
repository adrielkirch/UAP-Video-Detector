# Contract: External Configuration

**Feature**: `001-yolo-video-player`  
**Files**: `config/video_player.yaml`, `config/detector.yaml`  
**Overrides**: environment variables / CLI flags (documented in quickstart)

## `config/video_player.yaml` (example shape)

```yaml
accepted_extensions: [".mp4", ".mov", ".mkv", ".avi", ".webm"]
max_upload_bytes: 2147483648  # 2 GiB soft limit; 0 = unlimited
raw_dir: "data/raw"
copy_uploads_to_raw: false
seek_step_ms: 1000
```

## `config/detector.yaml` (example shape)

```yaml
backend: "yolo_world"          # null | yolo_world | yolov8 | yolov9 | custom
weights_path: "models/yolov8s-world.pt"   # required for yolov8 | yolov9 | custom | yolo_world
model_version: "v8"            # informational; factory uses backend + weights_path
class_prompts:
  - airplane
  - helicopter
  - bird
  - drone
confidence_threshold: 0.25
device: "auto"                 # auto | cpu | cuda
frame_stride: 2
lazy_load: true
lag_warn_ms: 2000              # SC-006: warn when single infer exceeds this
metrics:
  enabled: true
  log_infer_ms: true
  log_memory_mb: true          # best-effort; may be 0 if unavailable
  log_device: true
```

## Backend selection (constitution YOLO multi-version)

| `backend` | Behavior |
|-----------|----------|
| `null` | `NullDetector` — player-only |
| `yolo_world` | Ultralytics YOLO-World + `class_prompts` |
| `yolov8` | Ultralytics YOLOv8 weights at `weights_path` |
| `yolov9` | Ultralytics YOLOv9 (or compatible) weights at `weights_path` |
| `custom` | Any open-source YOLO-family `.pt` at `weights_path` behind same protocol |

All non-null backends MUST implement `AerialDetector`. Swapping backends MUST NOT require UI changes.

## Rules

- No thresholds, weight paths, or class lists hardcoded in source.
- `backend: null` forces `NullDetector` path (player-only mode).
- Changing YAML MUST NOT require code edits to take effect on next process start.
- CI/unit tests MUST point `weights_path` to a mock or skip load via injected detector.
- Metrics logging MUST be disable-able via `metrics.enabled: false` without affecting detections.
