"""
HTML5 / Plyr video layer for uploaded files.

Serves a copy from Streamlit static files and embeds a player with
play, pause, timeline, and timestamps at the source aspect ratio.
"""

import mimetypes
import shutil
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.ui.components.player_layout import display_size

STATIC_PLAY_DIR = Path(__file__).resolve().parents[1] / "static" / "play"
PLYR_CSS_PATH = "/app/static/vendor/plyr/plyr.css"
PLYR_JS_PATH = "/app/static/vendor/plyr/plyr.polyfilled.min.js"
CONTROLS_CHROME_PX = 72


def stage_static_video(source_path: str, stem: str) -> str:
    """Copy a playable file into src/ui/static/play and return its public URL."""
    STATIC_PLAY_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(source_path).suffix.lower() or ".mp4"
    dest = STATIC_PLAY_DIR / f"{stem}{suffix}"
    source = Path(source_path)
    if (
        not dest.exists()
        or source.stat().st_mtime > dest.stat().st_mtime
        or source.stat().st_size != dest.stat().st_size
    ):
        shutil.copy2(source, dest)
    return f"/app/static/play/{dest.name}"


def clear_static_video(stem: str) -> None:
    """Remove staged static copies for a session video id."""
    if not STATIC_PLAY_DIR.exists():
        return
    for leftover in STATIC_PLAY_DIR.glob(f"{stem}*"):
        leftover.unlink(missing_ok=True)


def _plyr_markup(static_url: str, width: int, height: int) -> str:
    mime, _ = mimetypes.guess_type(static_url)
    mime = mime or "video/mp4"
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{
      margin: 0;
      background: transparent;
    }}
    .uap-player-shell {{
      width: {width}px;
      max-width: 100%;
      margin: 0 auto;
      background: #111;
      border-radius: 12px;
      overflow: hidden;
    }}
    .uap-player-shell video,
    .uap-player-shell .plyr {{
      display: block;
      width: 100%;
      height: auto;
      background: #111;
    }}
  </style>
</head>
<body>
  <div class="uap-player-shell">
    <video id="uap-player" width="{width}" height="{height}" playsinline controls preload="metadata">
      <source type="{mime}" />
    </video>
  </div>
  <script>
    (function () {{
      function publicOrigin() {{
        try {{
          if (window.parent && window.parent !== window && window.parent.location.origin) {{
            return window.parent.location.origin;
          }}
        }} catch (err) {{}}
        if (document.referrer) {{
          try {{ return new URL(document.referrer).origin; }} catch (err) {{}}
        }}
        return window.location.origin || "";
      }}
      var origin = publicOrigin();
      var videoUrl = origin + "{static_url}";
      var video = document.getElementById("uap-player");
      var source = video.querySelector("source");
      source.src = videoUrl;
      video.load();

      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = origin + "{PLYR_CSS_PATH}";
      document.head.appendChild(link);

      var script = document.createElement("script");
      script.src = origin + "{PLYR_JS_PATH}";
      script.onload = function () {{
        if (typeof Plyr === "undefined") {{
          return;
        }}
        new Plyr(video, {{
          controls: ["play", "progress", "current-time", "duration", "mute", "volume", "fullscreen"],
          ratio: "{width}:{height}",
          hideControls: false
        }});
      }};
      document.body.appendChild(script);
    }})();
  </script>
</body>
</html>
"""


def _inject_player_chrome() -> None:
    """Keep the Streamlit iframe transparent so portrait clips are not boxed in white."""
    st.markdown(
        """
        <style>
        div[data-testid="stHtml"] iframe,
        .stHtml iframe,
        iframe[data-testid="stIFrame"] {
          background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_native_player(
    video_path: str,
    *,
    video_id: str,
    frame_width: int = 0,
    frame_height: int = 0,
    max_width_px: int = 960,
    max_height_px: int = 720,
) -> None:
    """Render a centered Plyr player at native (or capped) pixel size."""
    display_w, display_h = display_size(
        frame_width, frame_height, max_width_px, max_height_px
    )
    static_url = stage_static_video(video_path, video_id)
    _inject_player_chrome()
    components.html(
        _plyr_markup(static_url, display_w, display_h),
        height=display_h + CONTROLS_CHROME_PX,
        scrolling=False,
    )
