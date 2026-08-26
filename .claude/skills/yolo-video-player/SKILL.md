# Skill: YOLO Video Player & Aerial Object Scanner

**Feature Branch**: `001-yolo-video-player`  
**Status**: Skill-Driven Development (consolidated from Spec-Kit)  
**Created**: 2026-07-29  
**Consolidated**: 2026-08-26

---

## Overview

Build a loosely coupled MVP that lets researchers **upload one local video**, **play it with basic HTML5 controls** (play, pause, seek, stop), and optionally **live-scan frames** with open-source YOLO for **airplane / helicopter / bird / drone**. The UI/player never imports YOLO internals; orchestration binds a frame source to a `Detector` interface so upload/playback works with the scanner disabled or unavailable.

**Input Requirements**: "001-yolo-video-player — first feature branch. Video uploader, player basics, and YOLO ready for live scanning. One video per upload. Detect airplane / helicopter / bird / drone. Open-source YOLO. Very loosely coupled video player and YOLO scanner."

---

## Technical Context

### Language & Dependencies

- **Language**: Python 3.11+
- **Primary Dependencies**: 
  - `opencv-python` (video I/O + frame reading)
  - `numpy` (array processing)
  - `ultralytics` (open-source YOLO detector)
  - `streamlit` (upload UI + session shell)
  - `pyyaml` (external config)
  - `pytest` + `pytest-cov` (testing with mocks)

### Architecture Constraints

| Constraint | Rule | Reason |
|-----------|------|--------|
| **Open Source** | YOLO backend only; no proprietary models | Constitution: transparency |
| **Loose Coupling** | UI/player ↔ detector via protocol; no direct imports | Constitution: modularity (FR-007) |
| **Configuration** | Thresholds, classes, weights in YAML/env/CLI | Constitution: externalized config (FR-012) |
| **Testing** | TDD required; mock CV2/YOLO; ≥85% coverage | Constitution: quality gates |
| **Storage** | Local filesystem only; no database | Scope: MVP simplicity |
| **Scale** | Single user, one video, four classes, CPU/GPU optional | Scope: MVP |

### Project Structure

```
config/
├── video_player.yaml          # formats, session defaults
└── detector.yaml              # weights, classes, confidence, device, frame stride

src/
├── ingestion/                 # video capture & playback
│   ├── video_session.py       # single active video: accept/replace/clear
│   ├── format_validator.py    # extension + OpenCV openability checks
│   ├── playback.py            # PlaybackSession + PlaybackController
│   ├── capture.py             # OpenCV wrapper (injectable for tests)
│   ├── config.py              # config loaders
│   └── exceptions.py           # custom errors
├── inference/                 # detection & detector interface
│   ├── detector.py            # AerialDetector protocol + Ultralytics adapter
│   ├── detection_types.py     # Detection / FrameDetections value objects
│   ├── null_detector.py       # no-op detector when scan unavailable
│   ├── factory.py             # null | yolov8 | yolov9 | yolo_world | custom
│   └── config.py              # detector config loader
├── orchestration/             # binding player ↔ detector
│   ├── scan_pipeline.py       # playback frames → detector → overlay + lag flag
│   └── scan_metrics.py        # latency / device / memory logging
└── ui/                        # Streamlit UI layer
    ├── app.py                 # Streamlit entry: upload, controls, overlay
    └── components/
        ├── uploader.py
        ├── player_controls.py
        └── detection_overlay.py

tests/
├── unit/                      # isolated module tests
├── contract/                  # interface contract tests
└── integration/               # end-to-end scenarios
```

---

## User Stories & Acceptance Criteria

### User Story 1: Upload a Single Video (Priority: P1) 🎯

**Goal**: One active local video per session; accept valid files, reject invalid, replace old with new.

**Acceptance Scenarios**:
1. No video loaded → upload control shown center of page → valid file becomes active → player switches on
2. Video already active → upload new valid file → prior video replaced, user informed → still one active video
3. User selects invalid/corrupt file → system rejects with clear message → prior active video unchanged

**Functional Requirements**:
- FR-001: Exactly one active video at a time
- FR-002: Accept common formats (MP4 minimum); reject unsupported with clear message
- FR-010: Clear or replace video; release resources cleanly
- FR-013: Upload control in center of main page, not sidebar

---

### User Story 2: Play Video with Basic Controls (Priority: P1) 🎯

**Goal**: Play, pause, seek, stop on active video without any scanner required.

**Acceptance Scenarios**:
1. Active video loaded → user presses play → video plays with timeline, current-time, duration displayed
2. Video playing → user pauses → playback freezes, can resume from same point
3. Active video loaded → user seeks on timeline → player jumps to position, continues from there
4. Portrait/low-res clip (360×640) → player renders at 360×640 CSS pixels, no full-width landscape stretch

**Functional Requirements**:
- FR-003: Browser HTML5 video layer with play, pause, seek, timestamps; no `st.image` + `st.rerun` loop
- FR-009: Upload + playback work when scanning disabled or unavailable
- FR-014: Keep source aspect ratio; no stretching past native pixel width

---

### User Story 3: Live-Scan for Known Aerial Objects (Priority: P2)

**Goal**: Optional live scan overlays airplane/helicopter/bird/drone detections during playback.

**Acceptance Scenarios**:
1. Active video + scanning enabled → annotation pass finishes → same player plays annotated H.264 with boxes
2. Annotated video playing → user pauses → current frame stays visible, timeline works
3. Scanning enabled → user disables → player switches back to original video, fully usable
4. Frame with no target classes → annotation shows no false labels, empty state acceptable

**Functional Requirements**:
- FR-004: User can enable/disable scanning independently of playback
- FR-005: Detect 4 classes (airplane, helicopter, bird, drone); present in same player via annotated H.264
- FR-006: Detection presentation includes class label + confidence/strength indicator
- FR-015: Overlay files remuxed/transcoded to browser-playable H.264 (yuv420p, faststart)

---

### User Story 4: Player & Scanner as Replaceable Parts (Priority: P3)

**Goal**: Scanner unavailable/disabled or swapped via config without breaking upload/playback.

**Acceptance Scenarios**:
1. Scanner unavailable/disabled → user uploads/plays video → basic controls work + clear notice
2. Different compatible scanner configuration selected → scanning enabled → detects same 4 classes without changing player UX

**Functional Requirements**:
- FR-007: Loosely coupled via clear, replaceable boundaries; neither component requires other's internals
- FR-008: Scanner uses open-source YOLO family (no proprietary models)
- FR-012: Detection config (classes, threshold, model selection) externally configurable

---

## Technical Design Decisions

### Data Model

**ActiveVideo**: Represents single loaded video
- `id` (UUID): Session-stable identifier
- `display_name`: Original filename
- `path`: Absolute filesystem path
- `duration_ms`, `frame_count`, `fps`: Metadata
- `status`: `ready` | `invalid` | `cleared`
- `width`, `height`: Frame dimensions

**PlaybackSession**: Current playback state
- `state`: `stopped` | `playing` | `paused`
- `position_ms`, `position_frame`: Current position
- `duration_ms`: Mirror of active video

**Detection**: Single recognized object
- `class_name`: One of airplane, helicopter, bird, drone
- `confidence`: Float 0.0–1.0
- `bbox`: Bounding box (x, y, w, h) in frame coordinates

**FrameDetections**: All detections for one frame
- `frame_index`: Frame number
- `timestamp_ms`: Timestamp
- `detections`: List of `Detection`

### AerialDetector Protocol

```python
class AerialDetector(Protocol):
    def load(self) -> None:
        """Lazy/idempotent; raises DetectorNotReadyError on failure."""
    
    def is_ready(self) -> bool:
        """True if detector loaded and ready to infer."""
    
    def detect(
        self, 
        frame: ndarray, 
        *, 
        frame_index: int, 
        timestamp_ms: int
    ) -> FrameDetections:
        """Detect targets; return only configured classes above threshold."""
    
    def close(self) -> None:
        """Release weights; safe to call multiple times."""
```

**Implementations**:
- `NullDetector`: No-op; used when scanning disabled or backend unavailable
- `UltralyticsAdapter`: Wraps Ultralytics YOLO; filters to 4 target classes; supports CPU/GPU
- `CustomAdapter`: Future; supports user-provided weights

**Errors**:
- `DetectorNotReadyError`: Load failure or missing weights; non-fatal → show notice, playback continues
- `DetectorInferError`: Single-frame failure → skip frame, keep last overlay optional

---

## Execution Checklist

### Phase 1: Setup (Shared Infrastructure)

- [ ] Create package dirs: `src/inference/`, `src/orchestration/`, `src/ui/components/`, `tests/unit/`, `tests/contract/`, `tests/integration/`
- [ ] Add `__init__.py` to all new packages
- [ ] Verify pytest discovery in `pyproject.toml`
- [ ] Declare MVP deps in `requirements.txt`
- [ ] Add placeholder configs: `config/video_player.yaml`, `config/detector.yaml`
- [ ] Ensure `data/raw/` and `models/` exist (with `.gitkeep`)

### Phase 2: Foundation (Blocking Prerequisites)

**Write tests first, confirm fail, implement, confirm green:**

- [ ] `tests/unit/test_config_loaders.py`: Config load/validation TDD tests
- [ ] `tests/unit/test_ingestion_exceptions.py`: Exception messages TDD tests
- [ ] `tests/unit/test_detection_types.py`: Detection/FrameDetections TDD tests
- [ ] `src/ingestion/exceptions.py`: Extend with `UploadRejectedError`, clear messages
- [ ] `src/ingestion/config.py`: Implement `load_video_player_config`
- [ ] `src/inference/config.py`: Implement detector config loader
- [ ] `src/inference/detection_types.py`: Implement `Detection`, `FrameDetections`
- [ ] **Gate**: `pytest tests/unit/test_config_loaders.py tests/unit/test_ingestion_exceptions.py tests/unit/test_detection_types.py -q`

### Phase 3: User Story 1 — Upload a Single Video (P1) 🎯

**Tests (TDD) — all must fail first:**

- [ ] `tests/unit/test_format_validator.py`: Extension allowlist + OpenCV openability (mock `cv2.VideoCapture`)
- [ ] `tests/unit/test_video_session.py`: `set_from_path`, replace, clear, reject-keeps-prior
- [ ] `tests/contract/test_video_session_contract.py`: VideoSession API per `contracts/video-session.md`
- [ ] Confirm fail: `pytest tests/unit/test_format_validator.py tests/unit/test_video_session.py tests/contract/test_video_session_contract.py -q`

**Implementation:**

- [ ] `src/ingestion/format_validator.py`: Extensions from config + OpenCV openability check
- [ ] `src/ingestion/video_session.py`: `ActiveVideo` dataclass, `VideoSession.get_active`, `set_from_path`, `clear`, `last_error`
- [ ] `src/ingestion/video_session.py`: Replace releases prior resources
- [ ] `src/ui/components/uploader.py`: Streamlit uploader widget helpers (no YOLO imports)
- [ ] `src/ui/app.py`: Wire upload + clear + replace into session state
- [ ] Confirm green: `pytest tests/unit/test_format_validator.py tests/unit/test_video_session.py tests/contract/test_video_session_contract.py -q`

**Checkpoint**: US1 independently testable (upload management without player/YOLO)

---

### Phase 4: User Story 2 — Play Video with Basic Controls (P1) 🎯

**Tests (TDD) — all must fail first:**

- [ ] `tests/unit/test_playback_controller.py`: play, pause, seek, stop, no-video error, clear/replace resets
- [ ] `tests/unit/test_player_controls.py`: Control widget helpers
- [ ] `tests/contract/test_playback_contract.py`: PlaybackController API
- [ ] Confirm fail: `pytest tests/unit/test_playback_controller.py tests/unit/test_player_controls.py tests/contract/test_playback_contract.py -q`

**Implementation:**

- [ ] `src/ingestion/playback.py`: `PlaybackSession` state model
- [ ] `src/ingestion/playback.py`: `PlaybackController` (play, pause, stop, seek_ms, seek_frame, read_current_frame)
- [ ] `src/ingestion/capture.py`: OpenCV capture wrapper (open/seek/read/release; injectable for tests)
- [ ] `src/ingestion/video_session.py`: On clear/replace, reset playback via controller hook
- [ ] `src/ui/components/player_controls.py`: Streamlit play/pause/seek/stop controls
- [ ] `src/ui/app.py`: Wire frame display + controls with scan disabled by default
- [ ] Confirm green: `pytest tests/unit/test_playback_controller.py tests/unit/test_player_controls.py tests/contract/test_playback_contract.py -q`

**Checkpoint**: MVP without YOLO — upload + playback fully testable

---

### Phase 5: User Story 3 — Live-Scan for Known Aerial Objects (P2)

**Tests (TDD) — all must fail first:**

- [ ] `tests/contract/test_detector_protocol.py`: AerialDetector protocol per `contracts/detector-protocol.md`
- [ ] `tests/unit/test_null_detector.py`: NullDetector empty/not-ready behavior
- [ ] `tests/unit/test_detector.py`: Ultralytics adapter class filter + confidence (mock ultralytics; no weight download)
- [ ] `tests/unit/test_scan_pipeline.py`: Frame stride, pause keeps detections, disable stops infers, lag recording
- [ ] `tests/unit/test_detection_overlay.py`: Overlay payload (label + confidence)
- [ ] `tests/integration/test_upload_play_scan.py`: Upload → play → scan toggle with stub detector
- [ ] Confirm fail: `pytest tests/contract/test_detector_protocol.py tests/unit/test_null_detector.py tests/unit/test_detector.py tests/unit/test_scan_pipeline.py tests/unit/test_detection_overlay.py tests/integration/test_upload_play_scan.py -q`

**Implementation:**

- [ ] `src/inference/detector.py`: Define `AerialDetector` protocol + errors
- [ ] `src/inference/null_detector.py`: `NullDetector` implementation
- [ ] `src/inference/detector.py`: Ultralytics adapter (`load`, `is_ready`, `detect`, `close`)
- [ ] `src/inference/detector.py`: Filter outputs to 4 target classes + threshold
- [ ] `src/orchestration/scan_pipeline.py`: `ScanPipeline` (enable flag, stride, last FrameDetections)
- [ ] `src/orchestration/scan_pipeline.py`: Compose PlaybackController frames → detector
- [ ] `src/orchestration/scan_pipeline.py`: Record infer duration_ms; expose `last_lag_warning` when > 2000ms threshold
- [ ] `src/ui/components/detection_overlay.py`: Overlay drawing helpers
- [ ] `src/ui/app.py`: Wire Live Scan toggle + overlay via orchestration only
- [ ] Confirm green: `pytest tests/contract/test_detector_protocol.py tests/unit/test_null_detector.py tests/unit/test_detector.py tests/unit/test_scan_pipeline.py tests/unit/test_detection_overlay.py tests/integration/test_upload_play_scan.py -q`

**Checkpoint**: Live scan optional; player still independent

---

### Phase 6: User Story 4 — Replaceable Parts (P3)

**Tests (TDD) — all must fail first:**

- [ ] `tests/unit/test_detector_factory.py`: Factory returns `NullDetector` when `backend: null`; missing weights → `DetectorNotReady` + player unaffected
- [ ] `tests/unit/test_detector_factory.py`: Backends `yolov8`, `yolov9`, `yolo_world`, `custom` (weights_path required)
- [ ] `tests/unit/test_loose_coupling_imports.py`: UI/orchestration import graph excludes ultralytics from `src/ui/`
- [ ] `tests/integration/test_player_without_scanner.py`: Player-only mode; scanner unavailable doesn't break upload/playback
- [ ] Confirm fail: `pytest tests/unit/test_detector_factory.py tests/unit/test_loose_coupling_imports.py tests/integration/test_player_without_scanner.py -q`

**Implementation:**

- [ ] `src/inference/factory.py`: Detector factory supporting `null`, `yolo_world`, `yolov8`, `yolov9`, `custom` via `config/detector.yaml`
- [ ] `src/ui/app.py`: Surface non-blocking scan-unavailable notice
- [ ] `src/orchestration/scan_pipeline.py`: Missing weights never crash playback
- [ ] `README.md`: Document scanner swap instructions (config-only, weights paths)
- [ ] Confirm green: `pytest tests/unit/test_detector_factory.py tests/unit/test_loose_coupling_imports.py tests/integration/test_player_without_scanner.py -q`

**Checkpoint**: Loose coupling verified by tests

---

### Phase 7: Polish & Quality Gates

**Tests (TDD) — performance metrics:**

- [ ] `tests/unit/test_scan_metrics.py`: Metrics logger (infer_ms, optional memory_mb, device string) with fake timings

**Implementation:**

- [ ] `src/orchestration/scan_metrics.py`: `ScanMetrics` recorder (frame_index, infer_ms, memory_mb optional, device)
- [ ] `src/orchestration/scan_pipeline.py`: Wire `ScanMetrics` on each infer; read `lag_warn_ms` from `config/detector.yaml`
- [ ] `src/main.py`: Optional CLI entry for player/scan without Streamlit UI
- [ ] `config/video_player.yaml`: Fill real defaults per contracts (include backend enum + lag_warn_ms + metrics toggles)
- [ ] `config/detector.yaml`: Fill real defaults per contracts
- [ ] Run full test suite: `pytest tests/ -q --cov=src --cov-fail-under=85`
- [ ] Code quality: Black, Ruff, typecheck pass on new modules under `src/` and `tests/`
- [ ] `README.md`: Update run instructions (Streamlit entry, config backends, metrics logging)

---

## Success Criteria

- **SC-001**: New user uploads one video and starts playback in under 2 minutes
- **SC-002**: With scanning disabled, 100% of successful uploads support play, pause, seek, timestamps
- **SC-003**: With scanning enabled on validation clip with known targets, at least one correct class label appears during full playback
- **SC-004**: Turning scanning off mid-playback leaves playback usable; users continue watching without restart (95%+ manual acceptance)
- **SC-005**: When scanner unavailable, users complete upload + playback successfully (100% scripted acceptance runs) with understandable notice
- **SC-006**: After scan annotation of standard 30–60s clip, annotated H.264 plays with boxes locked to frames (no drift); progress visible while building
- **SC-007**: 360×640 validation clip occupies 360×640 CSS pixels on desktop viewport (no full-width stretch)

---

## Constitution Check ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Open Source Transparency** | PASS | Ultralytics YOLO backend; public weights; no proprietary models |
| **II. SOLID** | PASS | Detector protocol; single-purpose modules (ingestion, inference, orchestration, ui) |
| **III. Loose Coupling** | PASS | UI/player independent of YOLO; orchestration binds via interfaces |
| **IV. Parameterized Configuration** | PASS | Thresholds, classes, weights, formats in YAML/env/CLI |
| **V. Component-Based Development** | PASS | Standalone packages with clear interfaces; CLI where useful |
| **VI. DRY** | PASS | Shared types/utilities; no duplicated decode paths |
| **VII. Performance** | PASS | Efficient OpenCV decode; non-blocking scan path; GPU optional |
| **Testing / Quality** | PASS | TDD, pytest, mocks for GPU/weights; ≥85% coverage |
| **YOLO Integration Standards** | PASS | Multi-version via factory; lazy load; CPU/GPU configurable |
| **Performance Monitoring** | PASS | `ScanMetrics` + lag warning flag; latency, device, memory tracked |

---

## References

- **Legacy Spec Kit Artifacts** (to be removed):
  - `/specs/001-yolo-video-player/` (spec.md, plan.md, tasks.md, contracts, checklists)
  - `/.specify/` (templates, scripts, integrations)
  - `/.github/agents/speckit.*.agent.md`
  - `/.github/prompts/speckit.*.prompt.md`
  - `/.claude/skills/speckit-*/`

- **Project Constitution**: Align with open-source transparency, SOLID principles, loose coupling, externalized config

---

## Agent Trigger

To activate this skill in Cursor/Claude Code:
```
/yolo-video-player or skills: yolo-video-player
```

This consolidated SKILL.md replaces the 10 fragmented Spec-Kit sub-skills and the multi-file spec setup, enabling faster AI context load and lower contributor friction.
