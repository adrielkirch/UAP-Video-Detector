"""Tests for static staging used by the HTML5 / Plyr player."""

from src.ui.components.native_player import (
    clear_static_video,
    stage_static_video,
    _plyr_markup,
)


def test_stage_static_video_copies_under_play_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.ui.components.native_player.STATIC_PLAY_DIR", tmp_path
    )
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"fake-mp4")

    url = stage_static_video(str(source), "abc123")

    assert url == "/app/static/play/abc123.mp4"
    assert (tmp_path / "abc123.mp4").read_bytes() == b"fake-mp4"


def test_clear_static_video_removes_staged_copies(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.ui.components.native_player.STATIC_PLAY_DIR", tmp_path
    )
    (tmp_path / "abc123.mp4").write_bytes(b"a")
    (tmp_path / "abc123-scan.mp4").write_bytes(b"b")
    (tmp_path / "other.mp4").write_bytes(b"c")

    clear_static_video("abc123")

    assert not (tmp_path / "abc123.mp4").exists()
    assert not (tmp_path / "abc123-scan.mp4").exists()
    assert (tmp_path / "other.mp4").exists()


def test_plyr_markup_uses_parent_origin_and_native_box():
    html = _plyr_markup("/app/static/play/clip.mp4", 360, 640)
    assert "window.parent.location.origin" in html
    assert "width: 360px" in html
    assert 'ratio: "360:640"' in html
    assert "/app/static/play/clip.mp4" in html
