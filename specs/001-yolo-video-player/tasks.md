# Tasks: YOLO Video Player & Aerial Object Scanner

**Input**: Design documents from `/specs/001-yolo-video-player/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD REQUIRED — for every story, write failing tests first, confirm they fail, then implement the minimum code to pass (constitution + user request).

**Organization**: Tasks grouped by user story for independent implementation and testing. Prefer small atomic tasks (one file / one behavior).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US4 maps to spec user stories
- Include exact file paths in descriptions

## Path Conventions

- Single project: `src/`, `tests/`, `config/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package layout, dependencies, and test scaffolding so TDD can run

- [ ] T001 Create package directories `src/inference/`, `src/orchestration/`, `src/ui/components/`, `tests/unit/`, `tests/contract/`, `tests/integration/` per plan.md
- [ ] T002 [P] Add `src/inference/__init__.py`, `src/orchestration/__init__.py`, `src/ui/__init__.py`, `src/ui/components/__init__.py`
- [ ] T003 [P] Add pytest discovery config (or confirm) in `pyproject.toml` or `pytest.ini` for `tests/`
- [ ] T004 [P] Declare MVP deps (opencv-python, numpy, ultralytics, streamlit, pyyaml, pytest, pytest-cov) in `requirements.txt`
- [ ] T005 [P] Add empty placeholder configs `config/video_player.yaml` and `config/detector.yaml` matching `specs/001-yolo-video-player/contracts/config-schema.md`
- [ ] T006 [P] Ensure `data/raw/` and `models/` exist with `.gitkeep` (weights not committed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared types, config loading, exceptions — MUST finish before any user story impl

**⚠️ CRITICAL**: No user story implementation until this phase is complete (tests for foundation included)

### Tests (TDD) — Foundation

- [ ] T007 [P] Write failing unit tests for YAML config load/validation in `tests/unit/test_config_loaders.py`
- [ ] T008 [P] Write failing unit tests for shared exceptions messages in `tests/unit/test_ingestion_exceptions.py`
- [ ] T009 [P] Write failing unit tests for `Detection` / `FrameDetections` value objects in `tests/unit/test_detection_types.py`

### Implementation — Foundation

- [ ] T010 Extend upload/session exceptions in `src/ingestion/exceptions.py` (`UploadRejectedError`, clear messages)
- [ ] T011 Implement `load_video_player_config` in `src/ingestion/config.py` reading `config/video_player.yaml`
- [ ] T012 [P] Implement detector config loader in `src/inference/config.py` reading `config/detector.yaml`
- [ ] T013 [P] Implement `Detection` and `FrameDetections` in `src/inference/detection_types.py` per `data-model.md`
- [ ] T014 Run `pytest tests/unit/test_config_loaders.py tests/unit/test_ingestion_exceptions.py tests/unit/test_detection_types.py -q` and confirm green

**Checkpoint**: Foundation ready — user story TDD can begin

---

## Phase 3: User Story 1 — Upload a Single Video (Priority: P1) 🎯 MVP

**Goal**: One active local video at a time — accept, replace, clear, reject unsupported

**Independent Test**: Valid file becomes active; replace keeps one video; unsupported rejected without changing prior active

### Tests for User Story 1 (TDD) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [ ] T015 [P] [US1] Write failing unit tests for extension allowlist in `tests/unit/test_format_validator.py`
- [ ] T016 [P] [US1] Write failing unit tests for OpenCV openability reject path in `tests/unit/test_format_validator.py` (mock `cv2.VideoCapture`)
- [ ] T017 [P] [US1] Write failing unit tests for `VideoSession.set_from_path` accept in `tests/unit/test_video_session.py`
- [ ] T018 [P] [US1] Write failing unit tests for replace (still one active) in `tests/unit/test_video_session.py`
- [ ] T019 [P] [US1] Write failing unit tests for clear/remove in `tests/unit/test_video_session.py`
- [ ] T020 [P] [US1] Write failing unit tests for reject keeps prior active in `tests/unit/test_video_session.py`
- [ ] T021 [P] [US1] Write failing contract tests for VideoSession API in `tests/contract/test_video_session_contract.py` per `contracts/video-session.md`
- [ ] T022 [US1] Confirm US1 tests fail: `pytest tests/unit/test_format_validator.py tests/unit/test_video_session.py tests/contract/test_video_session_contract.py -q`

### Implementation for User Story 1

- [ ] T023 [US1] Implement `FormatValidator` in `src/ingestion/format_validator.py` (extensions from config + openability)
- [ ] T024 [US1] Implement `ActiveVideo` dataclass/model in `src/ingestion/video_session.py` (or `src/ingestion/models.py` if split)
- [ ] T025 [US1] Implement `VideoSession.get_active` / `set_from_path` / `clear` / `last_error` in `src/ingestion/video_session.py`
- [ ] T026 [US1] Wire replace to release prior resources in `src/ingestion/video_session.py`
- [ ] T027 [P] [US1] Implement Streamlit uploader widget helpers in `src/ui/components/uploader.py` (no YOLO imports)
- [ ] T028 [US1] Wire upload + clear + replace notice into `src/ui/app.py` session state
- [ ] T029 [US1] Re-run US1 tests until green: `pytest tests/unit/test_format_validator.py tests/unit/test_video_session.py tests/contract/test_video_session_contract.py -q`

**Checkpoint**: US1 independently testable (upload management without player/YOLO)

---

## Phase 4: User Story 2 — Play Video with Basic Controls (Priority: P1) 🎯 MVP

**Goal**: Play, pause, seek, stop against active video without any scanner

**Independent Test**: With scan off, play/pause/seek/stop work end-to-end on an uploaded video

### Tests for User Story 2 (TDD) ⚠️

- [ ] T030 [P] [US2] Write failing unit tests for play → playing state in `tests/unit/test_playback_controller.py`
- [ ] T031 [P] [US2] Write failing unit tests for pause freezes position in `tests/unit/test_playback_controller.py`
- [ ] T032 [P] [US2] Write failing unit tests for seek_ms clamp + position update in `tests/unit/test_playback_controller.py`
- [ ] T033 [P] [US2] Write failing unit tests for stop resets to start in `tests/unit/test_playback_controller.py`
- [ ] T034 [P] [US2] Write failing unit tests for no-video control no-ops/errors in `tests/unit/test_playback_controller.py`
- [ ] T035 [P] [US2] Write failing unit tests for clear/replace resets playback in `tests/unit/test_playback_controller.py`
- [ ] T036 [P] [US2] Write failing contract tests for PlaybackController API in `tests/contract/test_playback_contract.py` per `contracts/video-session.md`
- [ ] T037 [P] [US2] Write failing unit tests for player control helpers in `tests/unit/test_player_controls.py`
- [ ] T038 [US2] Confirm US2 tests fail: `pytest tests/unit/test_playback_controller.py tests/unit/test_player_controls.py tests/contract/test_playback_contract.py -q`

### Implementation for User Story 2

- [ ] T039 [US2] Implement `PlaybackSession` state model in `src/ingestion/playback.py`
- [ ] T040 [US2] Implement `PlaybackController` (attach, play, pause, stop, seek_ms, seek_frame, read_current_frame) in `src/ingestion/playback.py` using mocked-friendly VideoCapture wrapper
- [ ] T041 [US2] Implement OpenCV capture wrapper in `src/ingestion/capture.py` (open/seek/read/release; injectable for tests)
- [ ] T042 [US2] On `VideoSession.clear`/replace, reset playback via controller hook in `src/ingestion/video_session.py` / `src/ingestion/playback.py`
- [ ] T043 [P] [US2] Implement Streamlit control widgets in `src/ui/components/player_controls.py` (play/pause/seek/stop only)
- [ ] T044 [US2] Wire frame display + controls into `src/ui/app.py` with scan disabled by default
- [ ] T045 [US2] Re-run US2 tests until green: `pytest tests/unit/test_playback_controller.py tests/unit/test_player_controls.py tests/contract/test_playback_contract.py -q`

**Checkpoint**: US1+US2 MVP — upload and player work with YOLO absent

---

## Phase 5: User Story 3 — Live-Scan for Known Aerial Objects (Priority: P2)

**Goal**: Optional live scan overlays airplane / helicopter / bird / drone during playback

**Independent Test**: Enable scan on a clip; mocked/real detector returns labels; disable scan and player continues

### Tests for User Story 3 (TDD) ⚠️

- [ ] T046 [P] [US3] Write failing contract tests for `AerialDetector` protocol in `tests/contract/test_detector_protocol.py` per `contracts/detector-protocol.md`
- [ ] T047 [P] [US3] Write failing unit tests for `NullDetector` empty/not-ready behavior in `tests/unit/test_null_detector.py`
- [ ] T048 [P] [US3] Write failing unit tests for Ultralytics adapter class filter + confidence in `tests/unit/test_detector.py` (mock ultralytics; no weight download)
- [ ] T049 [P] [US3] Write failing unit tests for frame_stride skipping in `tests/unit/test_scan_pipeline.py`
- [ ] T050 [P] [US3] Write failing unit tests for pause keeps last detections in `tests/unit/test_scan_pipeline.py`
- [ ] T051 [P] [US3] Write failing unit tests for disable scan stops new inferences in `tests/unit/test_scan_pipeline.py`
- [ ] T052 [P] [US3] Write failing unit tests for overlay payload (label + confidence) in `tests/unit/test_detection_overlay.py`
- [ ] T053 [P] [US3] Write failing integration test upload→play→scan toggle with stub detector in `tests/integration/test_upload_play_scan.py`
- [ ] T080 [P] [US3] Write failing unit test that scan pipeline records per-frame infer duration and flags lag when injected fake infer > 2000ms (SC-006) in `tests/unit/test_scan_pipeline.py`
- [ ] T054 [US3] Confirm US3 tests fail: `pytest tests/contract/test_detector_protocol.py tests/unit/test_null_detector.py tests/unit/test_detector.py tests/unit/test_scan_pipeline.py tests/unit/test_detection_overlay.py tests/integration/test_upload_play_scan.py -q`

### Implementation for User Story 3

- [ ] T055 [US3] Define `AerialDetector` protocol + errors in `src/inference/detector.py`
- [ ] T056 [P] [US3] Implement `NullDetector` in `src/inference/null_detector.py`
- [ ] T057 [US3] Implement Ultralytics/YOLO-World adapter (`load`, `is_ready`, `detect`, `close`) in `src/inference/detector.py` using `config/detector.yaml`
- [ ] T058 [US3] Filter outputs to airplane/helicopter/bird/drone + threshold in `src/inference/detector.py`
- [ ] T059 [US3] Implement `ScanPipeline` (enable flag, stride, last FrameDetections) in `src/orchestration/scan_pipeline.py`
- [ ] T060 [US3] Compose PlaybackController frames → detector in `src/orchestration/scan_pipeline.py` without UI importing ultralytics
- [ ] T081 [US3] Record last infer duration_ms on `ScanPipeline` and expose `last_lag_warning` when duration_ms > configurable threshold (default 2000) in `src/orchestration/scan_pipeline.py` (SC-006)
- [ ] T061 [P] [US3] Implement overlay drawing helpers in `src/ui/components/detection_overlay.py`
- [ ] T062 [US3] Wire Live Scan toggle + overlay into `src/ui/app.py` via orchestration only
- [ ] T063 [US3] Re-run US3 tests until green (still no weight download in unit/contract): `pytest tests/contract/test_detector_protocol.py tests/unit/test_null_detector.py tests/unit/test_detector.py tests/unit/test_scan_pipeline.py tests/unit/test_detection_overlay.py tests/integration/test_upload_play_scan.py -q`

**Checkpoint**: Live scan optional; player still independent

---

## Phase 6: User Story 4 — Player and Scanner as Replaceable Parts (Priority: P3)

**Goal**: Scanner unavailable/disabled or swapped via config without breaking upload/playback

**Independent Test**: `backend: null` or missing weights → notice + full player; config swap keeps same player UX

### Tests for User Story 4 (TDD) ⚠️

- [ ] T064 [P] [US4] Write failing unit tests for factory returns NullDetector when `backend: null` in `tests/unit/test_detector_factory.py`
- [ ] T065 [P] [US4] Write failing unit tests for missing weights → DetectorNotReady + player unaffected in `tests/unit/test_detector_factory.py`
- [ ] T082 [P] [US4] Write failing unit tests for factory backends `yolov8`, `yolov9`, `yolo_world`, and `custom` (weights_path required) in `tests/unit/test_detector_factory.py`
- [ ] T066 [P] [US4] Write failing unit tests that UI/orchestration import graph excludes ultralytics from `src/ui/` in `tests/unit/test_loose_coupling_imports.py`
- [ ] T067 [P] [US4] Write failing integration test player-only mode (SC-005) in `tests/integration/test_player_without_scanner.py`
- [ ] T068 [US4] Confirm US4 tests fail: `pytest tests/unit/test_detector_factory.py tests/unit/test_loose_coupling_imports.py tests/integration/test_player_without_scanner.py -q`

### Implementation for User Story 4

- [ ] T069 [US4] Implement detector factory/selector in `src/inference/factory.py` supporting `null` | `yolo_world` | `yolov8` | `yolov9` | `custom` via `config/detector.yaml` (same `AerialDetector` protocol; yolov9/custom may lazy-load Ultralytics with configured weights)
- [ ] T070 [US4] Surface non-blocking scan-unavailable notice in `src/ui/app.py` / `src/ui/components/uploader.py` messaging helpers
- [ ] T071 [US4] Ensure missing weights path never crashes playback session in `src/orchestration/scan_pipeline.py`
- [ ] T072 [US4] Document swap instructions (config-only, including yolov8/yolov9/custom weights) in `README.md` under video player / detector section
- [ ] T073 [US4] Re-run US4 tests until green: `pytest tests/unit/test_detector_factory.py tests/unit/test_loose_coupling_imports.py tests/integration/test_player_without_scanner.py -q`

**Checkpoint**: Loose coupling verified by tests

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, docs, quickstart validation, constitution performance monitoring

### Tests (TDD) — Performance metrics

- [ ] T083 [P] Write failing unit tests for metrics logger (infer_ms, optional memory_mb, device string) in `tests/unit/test_scan_metrics.py` with fake timings (no GPU required)

### Implementation — Performance metrics (D1)

- [ ] T084 Implement `ScanMetrics` recorder/logger in `src/orchestration/scan_metrics.py` (frame_index, infer_ms, memory_mb optional, device; structured log line)
- [ ] T085 Wire `ScanMetrics` into `src/orchestration/scan_pipeline.py` on each infer; read `lag_warn_ms` / metrics flags from `config/detector.yaml`
- [ ] T086 Re-run metrics tests until green: `pytest tests/unit/test_scan_metrics.py tests/unit/test_scan_pipeline.py -q -k lag`

### Docs & quality gates

- [ ] T074 [P] Add optional CLI entry for player/scan without UI in `src/main.py` (uses same session/playback/detector ports)
- [ ] T075 [P] Fill real defaults in `config/video_player.yaml` and `config/detector.yaml` per contracts (include `backend` enum + `lag_warn_ms` + metrics toggles)
- [ ] T076 Run full suite with coverage gate locally: `pytest tests/ -q --cov=src --cov-fail-under=85`
- [ ] T077 [P] Ensure Black/Ruff/typecheck pass on new modules under `src/` and `tests/`
- [ ] T078 Execute manual checklist in `specs/001-yolo-video-player/quickstart.md` (V1–V5) and note results including SC-006 sync check
- [ ] T079 [P] Update `README.md` run instructions for `streamlit run src/ui/app.py`, config backends (`yolov8`/`yolov9`/`custom`), and metrics logging

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2)**: After Setup — BLOCKS all stories
- **US1 (Phase 3)**: After Foundational — MVP slice A
- **US2 (Phase 4)**: After Foundational; practical MVP needs US1 session (attach to VideoSession)
- **US3 (Phase 5)**: After US2 for real frame source; detector unit tests can be written in parallel after Foundational
- **US4 (Phase 6)**: After US3 factory/pipeline exist (or after US2 + NullDetector stub)
- **Polish (Phase 7)**: After desired stories complete

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories
- **US2 (P1)**: Uses VideoSession from US1 for attach; independently testable with fixture session
- **US3 (P2)**: Uses PlaybackController frames; detector fully mockable
- **US4 (P3)**: Validates composition/factory; no new player features

### Within Each User Story (TDD)

1. Write failing tests  
2. Confirm fail  
3. Implement minimum code  
4. Confirm green  
5. Refactor if needed  

### Parallel Opportunities

- Phase 1: T002–T006 in parallel
- Phase 2: T007–T009 in parallel; T012–T013 in parallel after T010–T011 started
- US1: T015–T021 in parallel; T027 parallel to T023–T026 once session API sketched
- US2: T030–T037 in parallel
- US3: T046–T053 in parallel; T056 parallel to T055; T061 parallel to T059–T060
- US4: T064–T067 in parallel

---

## Parallel Example: User Story 1

```bash
# TDD: launch US1 failing tests together
Task: "tests/unit/test_format_validator.py"
Task: "tests/unit/test_video_session.py"
Task: "tests/contract/test_video_session_contract.py"

# After fail confirmed, implement validator then session (sequential), UI uploader [P]
```

## Parallel Example: User Story 3

```bash
# TDD: detector contract + null + adapter + pipeline tests in parallel
Task: "tests/contract/test_detector_protocol.py"
Task: "tests/unit/test_null_detector.py"
Task: "tests/unit/test_detector.py"
Task: "tests/unit/test_scan_pipeline.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1 Setup  
2. Phase 2 Foundational  
3. Phase 3 US1 (upload)  
4. Phase 4 US2 (player)  
5. **STOP and VALIDATE** quickstart V1–V2 — demo-ready without YOLO  

### Incremental Delivery

1. Setup + Foundational  
2. US1 → validate upload  
3. US2 → validate player (MVP)  
4. US3 → live scan  
5. US4 → coupling guarantees  
6. Polish + quickstart V3–V4  

### Parallel Team Strategy

1. Team finishes Setup + Foundational  
2. Dev A: US1 → US2  
3. Dev B: US3 detector tests/adapter (mocked) after Foundational types exist  
4. Dev C: US4 import/factory tests once detector protocol lands  

---

## Notes

- [P] = different files, no incomplete-task dependency
- Every story phase: tests before impl; confirm fail then green
- Mock `cv2.VideoCapture` and ultralytics; never download weights in unit/contract tests
- UI must not import ultralytics (enforced in US4)
- Commit after each atomic task or small TDD cycle
- Suggested MVP scope: **US1 + US2** (both P1); US3/US4 next

## Format Validation

- All tasks use `- [ ]`, IDs T001–T086 (T080–T086 added for analyze remediation D1/C1/C2), story labels on US phases only, and file paths in descriptions
- Remediation map: **D1** → T083–T085; **C1** → T080–T081 + quickstart V3/V5; **C2** → T082 + T069 + config contract
