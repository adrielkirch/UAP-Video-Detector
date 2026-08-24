# Feature Specification: YOLO Video Player & Aerial Object Scanner

**Feature Branch**: `001-yolo-video-player`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "001-yolo-video-player — first feature branch. Video uploader, player basics, and YOLO ready for live scanning. One video per upload. Detect airplane / helicopter / bird / drone. Open-source YOLO. Very loosely coupled video player and YOLO scanner."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload a Single Video (Priority: P1)

A researcher selects one local video file and uploads it into the workspace so it becomes the active source for playback and scanning. Only one video is active at a time.

**Why this priority**: Without a video in place, playback and detection cannot run. This is the entry point for the entire feature.

**Independent Test**: Can be fully tested by selecting a valid video file and confirming it becomes the active session video, with no other video accepted until the current one is cleared or replaced.

**Acceptance Scenarios**:

1. **Given** no video is loaded, **When** the user opens the app, **Then** the upload control is shown in the center of the main page (not in a sidebar). After a supported file is accepted it becomes the single active video and the central area switches to the player.
2. **Given** a video is already active, **When** the user uploads another video, **Then** the previous video is replaced by the new one (still one active video) and the user is informed of the replacement.
3. **Given** the user selects an unsupported or corrupt file, **When** upload is attempted, **Then** the system rejects the file with a clear message and keeps the prior active video unchanged (or none if none was loaded).

---

### User Story 2 - Play Video with Basic Controls (Priority: P1)

A researcher plays the uploaded video in a real HTML5 player (play, pause, timeline/seek, current time and duration) so they can review aerial footage at the clip’s native aspect ratio.

**Why this priority**: Playback is core to reviewing footage and verifying detections visually. The player must work independently of the scanner (loose coupling) and must not stretch or letterbox the source into a fake landscape box.

**Independent Test**: Can be fully tested with an uploaded video and no scanner enabled — play, pause, seek/timeline, and timestamps must work end-to-end. A 360×640 portrait clip must render at 360×640 (or smaller if the viewport is narrower), never full-width landscape.

**Acceptance Scenarios**:

1. **Given** an active video is loaded, **When** the user starts playback, **Then** the video plays from the current position with a visible timeline and current-time / duration timestamps.
2. **Given** the video is playing, **When** the user pauses, **Then** playback freezes on the current frame and can be resumed from that point.
3. **Given** an active video is loaded, **When** the user seeks on the timeline, **Then** the player jumps to that position and continues from there when play is pressed.
4. **Given** a portrait or low-resolution clip (for example 360×640), **When** it is shown in the player, **Then** the video box keeps the source aspect ratio and does not stretch past the source pixel width.

---

### User Story 3 - Live-Scan for Known Aerial Objects (Priority: P2)

A researcher enables scanning so open-source YOLO detections for airplane, helicopter, bird, and drone are baked into a temporary browser-playable MP4 and shown in the same HTML5 player.

**Why this priority**: Detection is the product goal (filter known aerial objects), but it depends on upload and playback being available first. The scanner must plug in without owning the player or driving a frame-by-frame UI loop.

**Independent Test**: Can be tested by enabling scan on a video known to contain at least one target class and verifying labeled boxes appear in the annotated playback file; disabling scan returns the original video in the same player.

**Acceptance Scenarios**:

1. **Given** an active video is loaded and scanning is enabled, **When** the annotation pass finishes, **Then** the same player plays an H.264 file with detections for airplane, helicopter, bird, and/or drone drawn on the frames.
2. **Given** the annotated video is playing, **When** the user pauses, **Then** the current annotated frame stays visible and the timeline still works.
3. **Given** scanning is enabled, **When** the user disables scanning, **Then** the player switches back to the original video and remains fully usable.
4. **Given** a frame with no target classes, **When** that frame is annotated, **Then** the system shows no false mandatory labels for those classes (empty or “no detection” state is acceptable).

---

### User Story 4 - Treat Player and Scanner as Replaceable Parts (Priority: P3)

A contributor or operator swaps or disables the scanner (or uses a stub) without breaking basic upload and playback, confirming loose coupling between the video player and the YOLO scanner.

**Why this priority**: Open-source maintainability and constitution require independent, replaceable components. Valuable for contributors, secondary for end-user demo of detection.

**Independent Test**: Can be tested by running upload + playback with the scanner unavailable or disabled and confirming the player still meets Story 2 acceptance.

**Acceptance Scenarios**:

1. **Given** the scanner component is unavailable or disabled, **When** the user uploads and plays a video, **Then** basic player controls still work and the user sees a clear non-blocking notice that scanning is unavailable.
2. **Given** a different compatible scanner configuration is selected, **When** scanning is enabled, **Then** live detection still targets the same four classes without requiring changes to how the user operates the player.

---

### Edge Cases

- What happens when the uploaded file is extremely large or very long (hours of footage)?
- How does the system handle seeking near the end of the video while scanning is active?
- What happens if the user clears/removes the active video while playback or scanning is in progress?
- How does the system behave when the open-source detection model weights are missing or fail to load?
- What happens when multiple target classes appear in the same frame?
- How does the system handle videos with unusual aspect ratios, rotation metadata, or no audio track?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the user to upload exactly one active video at a time for a session.
- **FR-002**: System MUST accept common consumer/research video formats suitable for aerial footage review (at minimum widely used container formats such as MP4 and similar; unsupported formats MUST be rejected with a clear message).
- **FR-003**: System MUST provide a browser HTML5 video layer with play, pause, timeline/seek, current time, and duration for the active video. The Streamlit process MUST NOT drive playback with a frame-by-frame rerun loop (`st.image` + `st.rerun`).
- **FR-004**: System MUST allow the user to enable or disable scanning independently of playback controls.
- **FR-005**: When scanning is enabled, the system MUST detect airplane, helicopter, bird, and drone and present those detections in the same HTML5 player via a temporary annotated H.264 MP4.
- **FR-006**: Detection presentation MUST include at least class label and a confidence or equivalent strength indicator for each detection shown.
- **FR-007**: The video player and the YOLO scanner MUST be loosely coupled: neither component may require the other’s internal implementation; communication MUST go through clear, replaceable boundaries.
- **FR-008**: The scanner MUST use open-source YOLO-family detection (no proprietary closed model dependency for this feature’s baseline path).
- **FR-009**: System MUST allow upload and basic playback even when scanning is disabled or unavailable.
- **FR-010**: System MUST allow the user to clear or replace the active video; in-progress playback and scanning MUST stop cleanly when the active video is removed or replaced. Temporary annotated and statically served copies MUST be deleted on clear or replace.
- **FR-011**: System MUST surface user-friendly errors for failed upload, failed model readiness, and failed scan start without crashing the player session.
- **FR-012**: Detection configuration (enabled classes, confidence threshold, model selection) MUST be externally configurable without changing source code.
- **FR-013**: While no video is loaded, the upload control MUST appear in the center of the main page. A sidebar MUST NOT be the primary upload surface.
- **FR-014**: The player MUST keep the source aspect ratio and MUST NOT stretch a clip past its native pixel width (a 360×640 video stays 360×640 unless the viewport is narrower).
- **FR-015**: Overlay files written by OpenCV MUST be remuxed or transcoded to browser-playable H.264 (`yuv420p`, faststart) before they are handed to the HTML5 player.

### Key Entities

- **Active Video**: The single video currently loaded for playback and optional scanning; attributes include identity/name, duration, and readiness state.
- **Playback Session**: Current play state (playing, paused, stopped), position in the video, and control actions available to the user.
- **Scan Session**: Whether live scanning is enabled, readiness of the detector, and the stream of detections tied to frames/time.
- **Detection**: A single recognized object instance with class (airplane, helicopter, bird, drone), confidence/strength, and spatial extent on the frame (when available).
- **Detector Capability**: The open-source YOLO-based scanner as a swappable capability bound to the four target classes for this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can upload one video and start playback using basic controls in under 2 minutes on a typical workstation.
- **SC-002**: With scanning disabled, 100% of successful uploads support play, pause, timeline seek, and timestamps without requiring the scanner.
- **SC-003**: With scanning enabled on a validation clip containing known airplane, helicopter, bird, or drone instances, at least one correct class label for a present target appears during a single full playback pass for that clip.
- **SC-004**: Turning scanning off mid-playback leaves playback usable; users can continue watching without restarting the session in at least 95% of attempts in manual acceptance testing.
- **SC-005**: When the scanner is unavailable, users still complete upload and basic playback successfully in 100% of scripted acceptance runs, with an understandable notice about scanning.
- **SC-006**: After scan annotation of a standard short clip (about 30–60 seconds), the annotated H.264 file plays in the same player with boxes locked to those frames (no drifting overlay). Progress MUST be visible while the file is being built.
- **SC-007**: A 360×640 validation clip occupies a player box of 360×640 CSS pixels on a desktop viewport wide enough to fit it (no full-width landscape stretch).

## Assumptions

- Target users are researchers or analysts reviewing aerial/UAP-related footage on a local machine or controlled workstation.
- “Live” scanning in this feature means running YOLO over the uploaded file and playing the annotated result; it is not a separate live camera feed, and it is not a Streamlit frame-by-frame overlay loop.
- One video per upload means one active video per session; replacing the video is allowed and ends the previous playback/scan session.
- Baseline target classes for this feature are exactly: airplane, helicopter, bird, drone (other classes may be ignored or filtered out).
- Open-source YOLO weights and licensing remain compatible with the project’s AGPL-3.0 / open-source constitution.
- Camera live-capture, multi-video batch queues, cloud upload, and multi-user accounts are out of scope for this feature.
- Exact model version and training dataset are planning/implementation choices; this spec only requires an open-source YOLO-family scanner behind a replaceable boundary.
- “video” in the branch/feature name is the project’s chosen label for this player feature line; product language uses “video player.”
