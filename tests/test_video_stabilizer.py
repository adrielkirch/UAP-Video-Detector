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
