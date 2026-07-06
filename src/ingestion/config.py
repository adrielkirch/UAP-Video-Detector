from dataclasses import dataclass


@dataclass(slots=True)
class StabilizerConfig:
    """
    Configuration for the video stabilization pipeline.
    """

    max_features: int = 500
    quality_level: float = 0.01
    min_distance: int = 30
    block_size: int = 3

    min_matches: int = 20
    smoothing_radius: int = 30
    crop_border: int = 20
