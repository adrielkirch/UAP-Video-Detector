# Implementation Plan: YOLO Video Player & Aerial Object Scanner

**Branch**: `001-yolo-video-player` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-yolo-video-player/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Deliver a loosely coupled MVP that lets a researcher **upload one local video**, **play it with basic controls** (play, pause, seek, stop), and optionally **live-scan frames** with open-source YOLO for **airplane / helicopter / bird / drone**. The UI/player never imports YOLO internals; orchestration binds a frame source to a `Detector` interface so upload/playback works with the scanner disabled or unavailable.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: OpenCV (video I/O + frame display path), NumPy, Ultralytics YOLO (open-source detector backend), Streamlit (upload + session UI shell), PyYAML (external config), pytest (+ pytest-cov mocks for VideoCapture/detector)

**Storage**: Local filesystem only — active video path in session; optional copy/reference under `data/raw/`; model weights under `models/` (not committed); no database

**Testing**: pytest with TDD; mock `cv2.VideoCapture` and detector inference; ≥85% coverage on new modules; contract tests for Detector / VideoSession interfaces

**Target Platform**: Local workstation (Windows / macOS / Linux); CPU required, CUDA optional for faster inference

**Project Type**: Modular Python application (component libraries under `src/` + Streamlit UI entry + CLI hooks)

**Performance Goals**: Near-real-time live scan on short clips (≈30–60s) without multi-second persistent label lag on a typical workstation; player controls remain responsive when scan is off

**Constraints**: AGPL-3.0 / open-source only; one active video; no YouTube/WhatsApp URL ingestion in MVP; YAML/env/CLI config for thresholds, classes, weights; player ↔ YOLO loose coupling (DI / protocol); lazy model load; CPU + GPU paths

**Scale/Scope**: Single-user local MVP; one video session; four detection classes; basic player; no multi-user, batch queue, or live camera

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Open Source Transparency | No proprietary models/libs; YOLO backend open-source; weights via documented public sources | PASS — Ultralytics YOLO / YOLO-World path; config-driven weights |
| II. SOLID | Detector protocol; single-purpose modules (upload, player, detect, orchestrate) | PASS — planned interfaces in `contracts/` |
| III. Loose Coupling | UI/player must not depend on YOLO implementation; scanner optional | PASS — orchestration binds ports; FR-007/FR-009 |
| IV. Parameterized Configuration | Thresholds, classes, weights, formats in YAML/env/CLI — no hardcoding | PASS — `config/video_player.yaml` (+ env overrides) |
| V. Component-Based Development | Standalone packages with clear interfaces; CLI where useful | PASS — `ingestion`, `inference`, `orchestration`, `ui` components |
| VI. DRY | Shared frame/bbox/validation utilities; no duplicated decode paths | PASS — shared types in data model |
| VII. Performance | Efficient OpenCV decode; non-blocking scan path; GPU optional | PASS — frame stride + lazy load in research |
| Testing / Quality | TDD, pytest, Black/Ruff/typecheck, mock GPU/weights | PASS — reflected in quickstart & structure |
| YOLO Integration Standards | Multi-version capable via interface; lazy load; CPU/GPU | PASS — `AerialDetector` + factory backends `yolov8` / `yolov9` / `yolo_world` / `custom` |
| Performance Monitoring | Frame latency, memory, GPU/device tracked | PASS — `ScanMetrics` + `lag_warn_ms` (tasks T083–T085) |

**Post-Phase 1 re-check**: PASS — contracts and data model preserve loose coupling and externalized config; no unjustified complexity.  
**Post-analyze remediation (2026-07-29)**: D1/C1/C2 addressed in tasks T080–T086 + config-schema backends/metrics.

## Project Structure

### Documentation (this feature)

```text
specs/001-yolo-video-player/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
config/
├── video_player.yaml          # formats, session, player defaults
└── detector.yaml              # weights path, classes, confidence, device, frame stride

src/
├── ingestion/
│   ├── video_session.py       # single active video: accept / replace / clear
│   ├── format_validator.py    # extension + openability checks
│   ├── playback.py            # PlaybackSession + PlaybackController
│   ├── capture.py             # OpenCV capture wrapper (injectable)
│   ├── config.py              # existing + session-related config loaders
│   └── exceptions.py
├── inference/
│   ├── detector.py            # AerialDetector protocol + Ultralytics adapter
│   ├── detection_types.py     # Detection / FrameDetections value objects
│   ├── null_detector.py       # no-op detector when scan unavailable
│   ├── factory.py             # null | yolo_world | yolov8 | yolov9 | custom
│   └── config.py              # detector.yaml loader
├── orchestration/
│   ├── scan_pipeline.py       # bind playback frames → detector → overlay + lag flag
│   └── scan_metrics.py        # infer_ms / memory / device logging (constitution)
├── ui/
│   ├── app.py                 # Streamlit entry: upload, controls, overlay
│   └── components/
│       ├── uploader.py
│       ├── player_controls.py
│       └── detection_overlay.py
└── main.py                    # optional CLI: play/scan without UI

tests/
├── unit/
│   ├── test_video_session.py
│   ├── test_format_validator.py
│   ├── test_player_controls.py
│   ├── test_playback_controller.py
│   ├── test_detector.py
│   ├── test_detector_factory.py
│   ├── test_scan_pipeline.py
│   └── test_scan_metrics.py
├── contract/
│   ├── test_detector_protocol.py
│   ├── test_video_session_contract.py
│   └── test_playback_contract.py
└── integration/
    ├── test_upload_play_scan.py
    └── test_player_without_scanner.py

data/raw/                      # user videos (gitignored samples ok)
models/                        # weights (not committed; config points here)
```

**Structure Decision**: Extend the existing README layout (`ingestion` / `inference` / `orchestration` / `ui`) rather than a new top-level app. Player and detector stay in separate packages; `orchestration` is the only layer that composes them. Aligns with constitution principles III and V and existing `src/ingestion/` code.

## Complexity Tracking

> No constitution violations requiring justification. Complexity table intentionally empty.
