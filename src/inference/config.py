"""
Configuration loading for YOLO detector and inference settings.

Reads detector.yaml configuration with validation per project constitution
parameterized configuration principle.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_detector_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate detector configuration from YAML.

    Args:
        config_path: Path to detector.yaml configuration file

    Returns:
        Dictionary containing validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If configuration validation fails
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

    # Validate backend enum per constitution YOLO integration standards
    valid_backends = {None, "null", "yolo_world", "yolov8", "yolov9", "custom"}
    backend = config.get("backend")

    # Normalize null backend
    if backend == "null":
        config["backend"] = None
        backend = None

    if backend not in valid_backends:
        # Format backend names for error message (handle None)
        backend_names = []
        for b in valid_backends:
            if b is None:
                backend_names.append("null")
            else:
                backend_names.append(str(b))

        raise ValueError(
            f"Invalid backend '{backend}'. Must be one of: "
            f"{', '.join(sorted(backend_names))}"
        )

    return config
