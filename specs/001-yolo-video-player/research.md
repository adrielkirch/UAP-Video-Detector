# Research: YOLO Video Player & Aerial Object Scanner

**Feature**: `001-yolo-video-player` | **Date**: 2026-07-29

All Technical Context unknowns resolved below. No remaining NEEDS CLARIFICATION.

---

## 1. UI shell vs frame-accurate player

**Decision**: Streamlit for upload/session/controls shell; OpenCV `VideoCapture` as the authoritative frame source for position, seek, and scan.

**Rationale**: Spec needs seek-to-timestamp, pause-on-frame, and live per-frame detections. Browser/`st.video` alone does not expose reliable frame indices for YOLO. OpenCV provides frame index / msec seek; Streamlit renders the current frame image plus control widgets and optional overlay drawing.

**Alternatives considered**:
- Pure `st.video` — simple playback, poor seek/frame sync for detection
- PyQt/DearPyGui desktop player — stronger native player, heavier dependency surface for MVP
- Gradio — similar limits to Streamlit for frame-accurate scan

---

## 2. Open-source YOLO backend

**Decision**: Ultralytics YOLO family behind an `AerialDetector` protocol. Factory backends: `null` | `yolo_world` | `yolov8` | `yolov9` | `custom` (weights path). Default MVP backend: **YOLO-World** (open-vocabulary) with text prompts for `airplane`, `helicopter`, `bird`, `drone`. YOLOv8/YOLOv9/custom share the same adapter surface with config-selected weights (constitution multi-version MUST).

**Rationale**: Spec requires four classes and open-source only. COCO alone lacks helicopter/drone. YOLO-World keeps one open-source stack and matches all four labels without mandatory custom training for MVP demos. Explicit `yolov8` / `yolov9` / `custom` backends satisfy constitution YOLO Integration Standards without UI changes.

**Alternatives considered**:
- COCO-only YOLOv8 — incomplete class coverage vs FR-005
- Custom-trained YOLOv8 from day one — better accuracy long-term, blocks MVP
- Proprietary APIs — violates constitution I
- Single backend only — fails constitution multi-version MUST

---

## 3. Loose coupling pattern

**Decision**: Ports & adapters — UI talks to `VideoSession` + `PlaybackController`; scan path uses `AerialDetector`; `ScanPipeline` in orchestration composes them. Inject `NullDetector` when scan is off/unavailable.

**Rationale**: Satisfies FR-007/FR-009 and constitution III. Player unit tests never load weights; detector tests never open Streamlit.

**Alternatives considered**:
- Direct Ultralytics calls inside Streamlit callbacks — couples UI to YOLO, hard to mock
- Message bus/event bus — more indirection than MVP needs

---

## 4. Supported upload formats

**Decision**: Accept by extension + successful OpenCV open: **`.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`**. Reject others with a clear message. No URL / YouTube / WhatsApp cloud import in MVP.

**Rationale**: Spec FR-002 asks for common consumer formats, not universal codecs. WhatsApp/YouTube content is supported only after the user exports a local file in an accepted container. OpenCV openability avoids extension spoofing.

**Alternatives considered**:
- “All formats” / ffmpeg auto-transcode — large scope, opaque failures
- URL downloaders — out of scope per assumptions; legal/ops complexity

---

## 5. Single-video session management

**Decision**: `VideoSession` holds at most one `ActiveVideo`. Upload while active = replace (with notice). Explicit clear releases capture and resets playback/scan.

**Rationale**: Matches FR-001/FR-010 and Story 1. Simpler than a playlist/queue for MVP.

**Alternatives considered**:
- Multi-video queue — deferred by spec assumptions
- Keep prior file on failed replace — accepted (keep previous on validation failure)

---

## 6. Live-scan performance strategy

**Decision**: Configurable **frame stride** (e.g. every Nth frame), lazy model load on first scan enable, prefer GPU when `device: auto` finds CUDA else CPU. Overlay last detections while paused. **`ScanMetrics`** logs infer_ms (and best-effort memory/device); **`lag_warn_ms`** (default 2000) sets SC-006 lag warning when a single infer exceeds the threshold.

**Rationale**: SC-006 cares about perceived sync, not every-frame GPU cost. Stride keeps UI responsive on CPU laptops. Constitution requires real-time performance monitoring — metrics hook satisfies that without coupling UI to YOLO.

**Alternatives considered**:
- Every-frame inference always — may lag on CPU
- Offline batch precompute entire video — not “live” per Story 3
- No metrics — violates constitution Performance Monitoring MUST

---

## 7. Configuration surface

**Decision**: YAML under `config/` (`video_player.yaml`, `detector.yaml`) with optional env/CLI overrides for paths, confidence, device, stride, class list.

**Rationale**: Constitution IV — no hardcoded thresholds/weights.

**Alternatives considered**:
- Code constants — rejected by constitution
- Single mega-config — workable later; split keeps player vs detector ownership clear

---

## 8. Testing strategy for CV / YOLO

**Decision**: TDD with mocked `VideoCapture` and mocked `AerialDetector`. Contract tests assert protocol shape. One integration path with a tiny fixture video and stub detector (no weight download in CI).

**Rationale**: Constitution testing standards + CONTRIBUTING.md (no live capture, no weight download in unit tests).

**Alternatives considered**:
- Real yolov8n download in CI — flaky, large, network-bound
- Snapshot-only UI tests — insufficient for session/detector logic
