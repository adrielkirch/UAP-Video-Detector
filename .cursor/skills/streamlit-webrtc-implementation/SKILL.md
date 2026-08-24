---
name: streamlit-webrtc-implementation
description: Implement a unified YouTube-style video layer with streamlit-webrtc, replacing st.image/st.rerun playback loops and connecting YOLO overlays via frame callbacks. Use when adding streamlit-webrtc, refactoring video playback, or wiring ScanPipeline and detection_overlay into WebRTC.
---

### `skill.md` - UAP Video Detector: Streamlit-WebRTC Implementation

**Context and Goals**

* **Project:** UAP Video Detector built with Streamlit, OpenCV, and YOLO object detection.
* **Current Issue:** The UI is fragmented and video playback stutters/fails because the architecture relies on `cv2.VideoCapture` + `st.image()` + `st.rerun()` loops.
* **Primary Goal:** Implement a unified, "YouTube-style" video layer using the `streamlit-webrtc` library. This will enable zero-lag playback and real-time YOLO bounding box overlays without reloading the Streamlit DOM.

**1. Video Layer Architecture (`streamlit-webrtc`)**

* **Core Replacement:** Entirely replace the `st.image()` frame rendering and `st.rerun()` playback loop with `webrtc_streamer` from `streamlit-webrtc`.
* **Unified Player:** Use `webrtc_streamer` as the central video player. This naturally groups the video display and playback state, solving the UI fragmentation.
* **Deprecate Legacy Controls:** Remove the manual transport controls (Play, Pause, Stop, Seek) in `ui/components/player_controls.py` that rely on state mutations and `st.rerun()`. Rely on the WebRTC component's native streaming capabilities.

**2. Real-time YOLO Integration (Frame Callbacks)**

* **VideoProcessor Class:** Implement a class inheriting from `VideoTransformerBase` (or `VideoProcessorBase`) to handle the WebRTC frame callback `recv(self, frame)`.
* **Process Flow:** Inside the callback, convert the incoming frame to an OpenCV array (`frame.to_ndarray(format="bgr24")`).
* **Leverage Existing Code:** Pass the array to the existing `ScanPipeline` (`orchestration/scan_pipeline.py`) to run YOLO inference. Use the existing `draw_detections_on_frame` function from `ui/components/detection_overlay.py` to apply the `bbox_xyxy` coordinates onto the frame.
* **Return Frame:** Return the annotated frame back to the WebRTC stream (e.g., `av.VideoFrame.from_ndarray(annotated_frame, format="bgr24")`).

**3. UI Layout (YouTube-Style)**

* **Clean Hierarchy:** Wrap the `webrtc_streamer` component in a central `st.container()`. Place scanner settings (like the "Enable Live Scan" toggle) immediately above or below the player block.
* **Visual Integrity:** Ensure no arbitrary text blocks, debug info, or empty spaces break the visual connection between the video player and its immediate settings.
