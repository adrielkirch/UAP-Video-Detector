import cv2
import numpy as np
import pytest

from src.ingestion.config import StabilizerConfig
from src.ingestion.video_stabilizer import VideoStabilizer


def test_video_stabilizer_initializes_with_config():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    assert stabilizer.config == config


def test_stabilizer_returns_same_shape():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    output = stabilizer.stabilize(frame)

    assert output.shape == frame.shape


def test_stabilizer_raises_error_on_none_frame():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    with pytest.raises(ValueError):
        stabilizer.stabilize(None)


def test_preprocess_returns_grayscale():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    gray = stabilizer.preprocess(frame)

    assert len(gray.shape) == 2
    assert gray.shape == (480, 640)


def test_preprocess_invalid_type():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    with pytest.raises(TypeError):
        stabilizer.preprocess("invalid_frame")


def test_detect_features_returns_points():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    frame = np.zeros((480, 640), dtype=np.uint8)

    cv2.rectangle(frame, (100, 100), (250, 250), 255, -1)

    points = stabilizer.detect_features(frame)

    assert points is not None
    assert len(points) > 0


def test_detect_features_raises_error_on_none_frame():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    with pytest.raises(ValueError):
        stabilizer.detect_features(None)


def test_track_features_returns_matching_points():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    frame1 = np.zeros((480, 640), dtype=np.uint8)
    frame2 = np.zeros((480, 640), dtype=np.uint8)

    # Draw the same object with a slight movement
    cv2.circle(frame1, (200, 200), 20, 255, -1)
    cv2.circle(frame2, (205, 200), 20, 255, -1)

    features = stabilizer.detect_features(frame1)

    old_points, new_points = stabilizer.track_features(
        frame1,
        frame2,
        features,
    )

    assert old_points is not None
    assert new_points is not None
    assert len(old_points) == len(new_points)


def test_estimate_motion_returns_affine_transform():
    config = StabilizerConfig()
    stabilizer = VideoStabilizer(config)

    old_points = np.array(
        [
            [[100, 100]],
            [[200, 100]],
            [[100, 200]],
        ],
        dtype=np.float32,
    )

    new_points = np.array(
        [
            [[105, 102]],
            [[205, 102]],
            [[105, 202]],
        ],
        dtype=np.float32,
    )

    matrix = stabilizer.estimate_motion(
        old_points,
        new_points,
    )

    assert matrix is not None
    assert matrix.shape == (2, 3)