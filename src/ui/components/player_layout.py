"""
Shared player box sizing from native video dimensions.

Low-resolution clips stay at native pixels. They may shrink on a narrow
viewport, but they do not stretch to fill the Streamlit column.
"""

_FALLBACK_FRAME_SIZE = (720, 405)


def player_display_box(
    frame_width: int, frame_height: int, max_height_vh: int = 70
) -> dict:
    """
    Responsive box capped at the source resolution.

    Portrait clips (e.g. 360x640) stay 360px wide. Landscape clips
    (e.g. 720x480) stay 720px wide. Both shrink when the column is narrower.
    """
    width = int(frame_width)
    height = int(frame_height)
    if width <= 0 or height <= 0:
        width, height = _FALLBACK_FRAME_SIZE

    max_height_vh = max(20, min(100, int(max_height_vh)))
    return {
        "width": width,
        "height": height,
        "max_width_px": width,
        "aspect_ratio": f"{width} / {height}",
        "max_height_vh": max_height_vh,
        "width_css": (
            f"min(100%, {width}px, calc({max_height_vh}vh * {width} / {height}))"
        ),
        "orientation": "portrait" if height > width else "landscape",
    }


def display_size(
    frame_width: int,
    frame_height: int,
    max_width_px: int = 960,
    max_height_px: int = 720,
) -> tuple[int, int]:
    """Native size unless the clip is larger than the configured pixel cap."""
    width = int(frame_width)
    height = int(frame_height)
    if width <= 0 or height <= 0:
        width, height = _FALLBACK_FRAME_SIZE
    scale = min(1.0, max_width_px / width, max_height_px / height)
    return max(1, int(width * scale)), max(1, int(height * scale))
