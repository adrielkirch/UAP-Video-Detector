# Quickstart Validation: YOLO Video Player & Aerial Object Scanner

**Feature**: `001-yolo-video-player`  
**Purpose**: Runnable checks that prove upload → play → optional live scan end-to-end after implementation.  
**Related**: [data-model.md](./data-model.md), [contracts/](./contracts/)

---

## Prerequisites

- Python 3.11+
- Project venv with dependencies installed (`requirements.txt` / project installer once added)
- Optional: CUDA GPU for faster scan
- A short local sample video (MP4 or MOV), e.g. `data/raw/sample_sky_feed.mp4`
- Detector weights path configured in `config/detector.yaml` (or `backend: null` for player-only)

---

## Setup

```bash
cd UAP-Video-Detector
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -r requirements.txt
```

Ensure config files exist (created during implementation):

- `config/video_player.yaml` — see [contracts/config-schema.md](./contracts/config-schema.md)
- `config/detector.yaml`

---

## Validation scenarios

### V1 — Upload single video (Story 1 / FR-001, FR-002, FR-010)

1. Start UI: `streamlit run src/ui/app.py` (or documented entry once wired).
2. Upload a valid `.mp4` / `.mov`.
3. **Expect**: video shown as active; ready for playback.
4. Upload a second valid file.
5. **Expect**: replacement notice; only the new file active.
6. Click Clear/Remove.
7. **Expect**: no active video; controls idle.
8. Upload an unsupported extension (e.g. `.txt`).
9. **Expect**: clear rejection; prior state unchanged.

### V2 — Basic player controls (Story 2 / FR-003, SC-002)

1. With scan **off**, load a video.
2. Play → pause → seek mid-timeline → play → stop.
3. **Expect**: position updates; pause freezes frame; seek jumps; stop returns to start.
4. **Expect**: no detector/weights required.

### V3 — Live scan four classes (Story 3 / FR-004–FR-006, SC-003, SC-006)

1. Configure detector with open-source weights and prompts/classes for airplane, helicopter, bird, drone.
2. Enable Live Scan; play a clip known to contain at least one target.
3. **Expect**: labels + confidence (and boxes if shown) update during playback.
4. **SC-006 sync check**: During a ~30–60s clip, confirm labels do not stay stuck more than ~2s behind visible objects under normal local conditions; if metrics enabled, confirm infer_ms logs appear and no persistent `lag_warn` for the whole clip on a capable machine.
5. Pause.
6. **Expect**: last detections remain; frame does not advance.
7. Disable Live Scan mid-play.
8. **Expect**: playback continues; overlays stop updating (SC-004).

### V4 — Scanner unavailable (Story 4 / FR-009, SC-005)

1. Set `backend: null` or point to missing weights.
2. Upload + play + try enabling scan.
3. **Expect**: non-blocking notice; play/pause/seek/stop still work.

### V5 — Multi-version backend swap (Story 4 / constitution YOLO standards)

1. With the same UI, set `backend: yolov8` (or `yolov9` / `custom`) and a valid local `weights_path`.
2. Enable Live Scan briefly (or confirm detector becomes ready).
3. **Expect**: player controls unchanged; no code changes required — config only.
4. Set `metrics.enabled: true` and confirm structured infer timing logs while scanning.

---

## Automated checks (post-implement)

```bash
pytest tests/unit tests/contract -q
pytest tests/integration/test_upload_play_scan.py -q
```

**Expect**: unit/contract pass without network weight downloads; integration uses fixtures/mocks per CONTRIBUTING.md.

---

## Out of scope for this quickstart

- YouTube/WhatsApp URL import
- Multi-video batch
- Custom training of new weights
- Production deployment / Docker (optional later)
