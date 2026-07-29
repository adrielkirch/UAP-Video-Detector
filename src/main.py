#!/usr/bin/env python3
"""
CLI entry point for UAP Video Detector.

Provides command-line interface for video analysis without the Streamlit UI.
Uses the same session/playback/detector ports for consistency.
"""

import argparse
import sys
from pathlib import Path

from src.ingestion.video_session import VideoSession
from src.ingestion.playback import PlaybackController
from src.inference.factory import DetectorFactory
from src.orchestration.scan_pipeline import ScanPipeline


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="UAP Video Detector - Aerial Object Scanner CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("video_path", help="Path to video file to analyze")

    parser.add_argument(
        "--backend",
        choices=["null", "yolo_world", "yolov8", "yolov9", "custom"],
        default="yolo_world",
        help="Detection backend to use",
    )

    parser.add_argument(
        "--weights", help="Path to model weights (required for YOLO backends)"
    )

    parser.add_argument(
        "--frame-stride",
        type=int,
        default=2,
        help="Process every Nth frame (1 = every frame, 2 = every other frame)",
    )

    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.25,
        help="Detection confidence threshold (0.0-1.0)",
    )

    parser.add_argument(
        "--device", default="auto", help="Device to use (auto, cpu, cuda)"
    )

    parser.add_argument(
        "--output", help="Output file for detection results (JSON format)"
    )

    parser.add_argument(
        "--metrics", action="store_true", help="Enable performance metrics logging"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate input file
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    if args.verbose:
        print(f"Processing video: {video_path}")
        print(f"Backend: {args.backend}")
        if args.weights:
            print(f"Weights: {args.weights}")

    try:
        # Initialize components
        video_session = VideoSession()
        playback_controller = PlaybackController()
        scan_pipeline = ScanPipeline(
            frame_stride=args.frame_stride, metrics_enabled=args.metrics
        )

        # Connect playback to session
        playback_controller.attach(video_session)

        # Load video
        video_session.set_from_path(str(video_path))
        active_video = video_session.get_active()

        if active_video is None:
            print("Error: Failed to load video")
            sys.exit(1)

        if args.verbose:
            print(f"Loaded: {active_video.display_name}")
            print(f"Duration: {active_video.duration_ms / 1000:.1f}s")
            print(f"Frames: {active_video.frame_count}")

        # Create detector
        detector_factory = DetectorFactory()

        # Override config with CLI args
        detector_config = {
            "backend": args.backend,
            "confidence_threshold": args.confidence_threshold,
            "device": args.device,
            "frame_stride": args.frame_stride,
            "metrics": {"enabled": args.metrics},
        }

        if args.weights:
            detector_config["weights_path"] = args.weights

        try:
            detector = detector_factory.create_detector(detector_config)
            if args.verbose:
                if detector.is_ready():
                    print(f"Detector ready: {args.backend}")
                else:
                    print("Warning: Detector not ready, using null fallback")
        except Exception as e:
            if args.verbose:
                print(f"Detector creation failed: {e}")
            print("Using null detector (no detection)")
            detector = detector_factory._create_null_detector()

        # Attach components
        scan_pipeline.attach_detector(detector)
        scan_pipeline.attach_playback(playback_controller)
        scan_pipeline.enable_scan()

        # Process video
        results = process_video_cli(
            playback_controller, scan_pipeline, active_video, verbose=args.verbose
        )

        # Output results
        if args.output:
            import json

            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            if args.verbose:
                print(f"Results written to: {output_path}")
        else:
            # Print summary to stdout
            print_results_summary(results)

        # Print metrics if enabled
        if args.metrics and args.verbose:
            metrics = scan_pipeline.get_metrics()
            summary = metrics.get_performance_summary()
            print("\nPerformance Summary:")
            print(f"  Frames processed: {summary['total_frames']}")
            print(f"  Average inference: {summary['average_inference_ms']:.1f}ms")
            if summary.get("last_device"):
                print(f"  Last device: {summary['last_device']}")

    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def process_video_cli(
    playback_controller: PlaybackController,
    scan_pipeline: ScanPipeline,
    active_video,
    verbose: bool = False,
) -> dict:
    """
    Process video frames and collect detection results.

    Args:
        playback_controller: Video playback controller
        scan_pipeline: Detection pipeline
        active_video: Active video metadata
        verbose: Enable progress output

    Returns:
        Dictionary with detection results and metadata
    """
    results = {
        "video": {
            "path": str(active_video.path),
            "display_name": active_video.display_name,
            "duration_ms": active_video.duration_ms,
            "frame_count": active_video.frame_count,
        },
        "detections": [],
        "summary": {
            "total_detections": 0,
            "frames_with_detections": 0,
            "class_counts": {},
        },
    }

    frame_count = active_video.frame_count
    processed_frames = 0
    last_progress = 0

    # Process each frame
    for frame_index in range(frame_count):
        if verbose and frame_index * 100 // frame_count > last_progress:
            last_progress = frame_index * 100 // frame_count
            print(f"Progress: {last_progress}%")

        # Read frame
        frame = playback_controller.read_current_frame()
        if frame is None:
            break

        # Process with detection pipeline
        detections = scan_pipeline.process_frame(frame, frame_index)

        if detections and len(detections) > 0:
            # Convert detections to serializable format
            frame_results = {
                "frame_index": frame_index,
                "timestamp_ms": int(
                    frame_index
                    * 1000
                    / (active_video.frame_count / (active_video.duration_ms / 1000))
                ),
                "detections": [],
            }

            for detection in detections:
                det_dict = {
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "bbox_xyxy": detection.bbox_xyxy,
                    "track_id": detection.track_id,
                }
                frame_results["detections"].append(det_dict)

                # Update summary
                results["summary"]["total_detections"] += 1
                class_name = detection.class_name
                results["summary"]["class_counts"][class_name] = (
                    results["summary"]["class_counts"].get(class_name, 0) + 1
                )

            if frame_results["detections"]:
                results["detections"].append(frame_results)
                results["summary"]["frames_with_detections"] += 1

        processed_frames += 1

        # Advance playback
        playback_controller.seek_frame(frame_index + 1)

    if verbose:
        print(f"Progress: 100% - Processed {processed_frames} frames")

    return results


def print_results_summary(results: dict):
    """Print detection results summary to stdout."""
    video_info = results["video"]
    summary = results["summary"]

    print(f"\nVideo: {video_info['display_name']}")
    print(f"Duration: {video_info['duration_ms'] / 1000:.1f}s")
    print(f"Frames: {video_info['frame_count']}")

    print("\nDetection Summary:")
    print(f"  Total detections: {summary['total_detections']}")
    print(f"  Frames with detections: {summary['frames_with_detections']}")

    if summary["class_counts"]:
        print("  Detected classes:")
        for class_name, count in summary["class_counts"].items():
            print(f"    {class_name}: {count}")
    else:
        print("  No objects detected")


if __name__ == "__main__":
    main()
