# Research: YOLO Video Player & Aerial Object Scanner

**Feature**: `001-yolo-video-player` | **Date**: 2026-07-29

All Technical Context unknowns resolved below. No remaining NEEDS CLARIFICATION.

---

## 1. UI shell vs HTML5 video layer

**Decision**: Streamlit (`layout="centered"`) for the session shell. Empty state shows the uploader in the **main column**, not a sidebar. After load, a **Plyr / HTML5** player (via `components.html`) plays a file copied to `src/ui/static/play/` (`enableStaticServing`). OpenCV `VideoCapture` remains the source of truth for duration, fps, and native width/height. YOLO overlays are baked offline into `temp/annotated_<id>.mp4` and remuxed to H.264 with **imageio-ffmpeg**.

**Rationale**: Reviewers need real play/pause/timeline/timestamps. `st.video()` cannot keep a 360×640 clip at 360×640 (it stretches to a landscape box). `st.image` + `st.rerun()` is not a player. `streamlit-webrtc` failed for uploaded files (`InvalidStateError: setRemoteDescription`). `streamlit-player` needs a public URL or a huge base64 payload. Static serving + a sized HTML5 box matches FR-003 / FR-013 / FR-014.

**Alternatives considered**:
- Pure `st.video` — native controls, cannot constrain portrait size in Streamlit 1.62
- `streamlit-webrtc` for files — SDP/ICE `setRemoteDescription` errors
- `streamlit-player` — URL or enormous data URI; not for local multi-hundred-MB uploads
- Frame loop (`st.image` + rerun) — rejected for player UX
- PyQt/DearPyGui — stronger desktop player, heavier than the Streamlit MVP

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

**Decision**: Configurable **frame stride** (e.g. every Nth frame), lazy model load on first scan enable, prefer GPU when `device: auto` finds CUDA else CPU. When the user enables scan, `ScanPipeline` walks the file once, draws overlays, and writes a temp H.264 MP4 for the HTML5 player. **`ScanMetrics`** logs infer_ms (and best-effort memory/device); **`lag_warn_ms`** (default 2000) still flags a slow single infer during the bake.

**Rationale**: The browser player cannot call YOLO on each displayed frame. Bake-then-play keeps boxes locked to frames (SC-006) and keeps the player loosely coupled. Stride keeps the bake responsive on CPU laptops.

**Alternatives considered**:
- Every-frame inference always — may lag on CPU
- WebRTC per-frame overlay during playback — rejected after SDP failures on uploaded files
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
