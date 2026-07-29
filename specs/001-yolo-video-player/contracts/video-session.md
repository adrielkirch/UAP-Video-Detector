# Contract: Video Session & Playback

**Feature**: `001-yolo-video-player`  
**Consumers**: UI components, orchestration  
**Implementations**: `src/ingestion/video_session.py`, playback controller (ingestion or ui-adjacent service)

## VideoSession API

```text
VideoSession
  get_active() -> ActiveVideo | None
  set_from_path(path: str | Path) -> ActiveVideo
      # Validate format + openability.
      # On success: replace any prior active video; release prior capture.
      # On failure: raise UploadRejectedError; leave prior active unchanged.
  clear() -> None
      # Release resources; active becomes None; notify playback/scan reset.
  last_error() -> str | None
```

## PlaybackController API

```text
PlaybackController
  attach(session: VideoSession) -> None
  play() -> None
  pause() -> None
  stop() -> None
  seek_ms(position_ms: int) -> None
  seek_frame(frame_index: int) -> None
  get_state() -> PlaybackSession
  read_current_frame() -> ndarray | None
      # For UI paint and/or scan pipeline; None if no video / closed.
```

## Upload rejection reasons (user-facing)

- Unsupported extension
- File missing / unreadable
- OpenCV cannot open / zero frames
- (Optional) exceeds configured max size

## Invariants

1. At most one ready `ActiveVideo`.
2. `clear()` or successful replace MUST stop playback and clear scan overlays.
3. Seek MUST clamp to valid range; MUST NOT throw for clamp-only adjustment.
4. Player APIs MUST work with detector absent.
