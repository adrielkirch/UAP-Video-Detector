"""
Configuration loading for video ingestion and session management.

Reads video_player.yaml configuration with validation per project constitution
parameterized configuration principle.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_video_player_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate video player configuration from YAML.

    Args:
        config_path: Path to video_player.yaml configuration file

    Returns:
        Dictionary containing validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If required configuration keys are missing
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}")

    if not isinstance(config, dict):
        raise ValueError(f"Configuration must be a dictionary, got {type(config)}")

    # Validate required keys
    required_keys = [
        "accepted_extensions",
        "max_upload_bytes",
        "raw_dir",
        "copy_uploads_to_raw",
        "seek_step_ms",
    ]

    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required config key(s): {', '.join(missing_keys)}")

    return config
