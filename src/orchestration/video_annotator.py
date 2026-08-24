"""
Offline annotation of uploaded videos for HTML5 playback.

Walks frames with ScanPipeline and detection overlays, writes OpenCV mp4v,
then remuxes to H.264 so the browser player can actually play the file.
"""

from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

from src.orchestration.scan_pipeline import ScanPipeline
from src.ui.components.detection_overlay import (
    draw_detections_on_frame,
    draw_scan_status,
)

ProgressCallback = Callable[[int, int], None]


def annotated_output_path(video_id: str, directory: str = "temp") -> Path:
    """Return the temp path used for a session-scoped annotated MP4."""
    dest_dir = Path(directory)
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / f"annotated_{video_id}.mp4"


def remove_annotated_output(path: Optional[str]) -> None:
    """Delete a previously written annotated file if it still exists."""
    if not path:
        return
    target = Path(path)
    if target.exists():
        target.unlink()


def _annotate_frame(
    frame: np.ndarray,
    scan_pipeline: ScanPipeline,
    frame_index: int,
) -> np.ndarray:
    working = frame.copy()
    processed = scan_pipeline.process_frame(working, frame_index=frame_index)
    detections = (
        processed if processed is not None else scan_pipeline.get_last_detections()
    )
    if detections is not None:
        working = draw_detections_on_frame(working, detections)
    draw_scan_status(working, True, scan_pipeline.last_lag_warning)
    return working


def write_annotated_video(
    source_path: str,
    dest_path: str,
    scan_pipeline: ScanPipeline,
    on_progress: Optional[ProgressCallback] = None,
) -> str:
    """
    Render YOLO overlays onto every processed frame and write an MP4.

    Args:
        source_path: Uploaded source video
        dest_path: Destination MP4 path (typically under temp/)
        scan_pipeline: Existing scan pipeline with detector attached
        on_progress: Optional callback(frame_index, total_frames)

    Returns:
        Destination path as a string

    Raises:
        RuntimeError: If the source cannot be opened or the writer fails
    """
    capture = cv2.VideoCapture(source_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open source video: {source_path}")

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        raw_path = str(Path(dest_path).with_suffix(".raw.mp4"))
        writer = cv2.VideoWriter(
            raw_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not create annotated video: {dest_path}")

        if not scan_pipeline.is_enabled():
            scan_pipeline.enable_scan()

        try:
            frame_index = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                annotated = _annotate_frame(frame, scan_pipeline, frame_index)
                writer.write(annotated)
                frame_index += 1
                if on_progress is not None:
                    on_progress(frame_index, max(total, frame_index))
        finally:
            writer.release()
    finally:
        capture.release()

    _remux_to_h264(raw_path, dest_path)
    Path(raw_path).unlink(missing_ok=True)
    return dest_path


def _remux_to_h264(source_path: str, dest_path: str) -> None:
    """Transcode OpenCV mp4v into browser-playable H.264."""
    import subprocess

    import imageio_ffmpeg

    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-i",
        source_path,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        dest_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not Path(dest_path).exists():
        raise RuntimeError(result.stderr or "FFmpeg H.264 remux failed")
