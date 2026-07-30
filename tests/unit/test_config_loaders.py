"""
Unit tests for configuration loading and validation.

Tests for YAML config loaders that read video_player.yaml and detector.yaml
with proper validation and error handling.
"""

import pytest
from unittest.mock import patch, mock_open
import yaml

from src.ingestion.config import load_video_player_config
from src.inference.config import load_detector_config


class TestVideoPlayerConfigLoader:
    """Test YAML config loading for video player settings."""

    def test_load_valid_config_returns_dict(self):
        """Should load valid YAML config and return dict with expected keys."""
        valid_yaml = """
accepted_extensions: [".mp4", ".mov", ".avi"]
max_upload_bytes: 1073741824
raw_dir: "data/raw"
copy_uploads_to_raw: false
seek_step_ms: 1000
"""
        with patch("builtins.open", mock_open(read_data=valid_yaml)):
            config = load_video_player_config("config/video_player.yaml")

        assert isinstance(config, dict)
        assert config["accepted_extensions"] == [".mp4", ".mov", ".avi"]
        assert config["max_upload_bytes"] == 1073741824
        assert config["raw_dir"] == "data/raw"
        assert config["copy_uploads_to_raw"] is False
        assert config["seek_step_ms"] == 1000

    def test_load_missing_file_raises_error(self):
        """Should raise FileNotFoundError for missing config file."""
        with pytest.raises(FileNotFoundError):
            load_video_player_config("nonexistent/config.yaml")

    def test_load_invalid_yaml_raises_error(self):
        """Should raise yaml.YAMLError for malformed YAML."""
        invalid_yaml = """
accepted_extensions: [".mp4", ".mov"
  invalid: yaml: structure
"""
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(yaml.YAMLError):
                load_video_player_config("config/video_player.yaml")

    def test_load_config_validates_required_keys(self):
        """Should validate that required configuration keys are present."""
        minimal_yaml = """
accepted_extensions: []
"""
        with patch("builtins.open", mock_open(read_data=minimal_yaml)):
            with pytest.raises(ValueError, match="Missing required config key"):
                load_video_player_config("config/video_player.yaml")


class TestDetectorConfigLoader:
    """Test YAML config loading for detector settings."""

    def test_load_valid_detector_config_returns_dict(self):
        """Should load valid detector config with all expected keys."""
        valid_yaml = """
backend: "yolo_world"
weights_path: "models/yolov8s-world.pt"
class_prompts: ["airplane", "helicopter", "bird", "drone"]
confidence_threshold: 0.25
device: "auto"
frame_stride: 2
lazy_load: true
lag_warn_ms: 2000
metrics:
  enabled: true
  log_infer_ms: true
"""
        with patch("builtins.open", mock_open(read_data=valid_yaml)):
            config = load_detector_config("config/detector.yaml")

        assert isinstance(config, dict)
        assert config["backend"] == "yolo_world"
        assert config["confidence_threshold"] == 0.25
        assert config["class_prompts"] == ["airplane", "helicopter", "bird", "drone"]
        assert config["metrics"]["enabled"] is True

    def test_load_null_backend_config_succeeds(self):
        """Should accept null backend for player-only mode."""
        null_backend_yaml = """
backend: null
confidence_threshold: 0.25
class_prompts: ["airplane"]
device: "cpu"
frame_stride: 1
"""
        with patch("builtins.open", mock_open(read_data=null_backend_yaml)):
            config = load_detector_config("config/detector.yaml")

        assert config["backend"] is None

    def test_load_detector_config_validates_backend_enum(self):
        """Should validate backend is one of allowed values."""
        invalid_backend_yaml = """
backend: "invalid_backend"
class_prompts: ["airplane"]
"""
        with patch("builtins.open", mock_open(read_data=invalid_backend_yaml)):
            with pytest.raises(ValueError, match="Invalid backend"):
                load_detector_config("config/detector.yaml")
