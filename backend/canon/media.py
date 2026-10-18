"""Hard caps on audio and video BEFORE any Gemini call: per-file length and a shared daily budget.

Duration comes from the container headers (mutagen, no ffmpeg). When it cannot be read (webm, odd
files) the file size stands in for it. The daily budget lives in connector_state, so every Cloud Run
instance, the web app and the Discord sync all draw on the same minutes.
"""
import io
import os
from datetime import datetime, timezone

from canon.connectors import state

MB = 1024 * 1024
AUDIO_MINUTES = float(os.environ.get("CANON_MEDIA_AUDIO_MINUTES", "10"))
VIDEO_MINUTES = float(os.environ.get("CANON_MEDIA_VIDEO_MINUTES", "2"))
AUDIO_MB = float(os.environ.get("CANON_MEDIA_AUDIO_MB", "10"))   # size proxy when the length is unknown
VIDEO_MB = float(os.environ.get("CANON_MEDIA_VIDEO_MB", "15"))
MAX_MB = float(os.environ.get("CANON_MEDIA_MAX_MB", "15"))       # inline bytes; Vertex takes about 20 MB a request


def daily_minutes() -> float:
    return float(os.environ.get("CANON_MEDIA_DAILY_MINUTES", "30"))


class Refused(Exception):
    """A recording Canon will not send to Gemini. status 413 (this file) or 429 (today's budget)."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def duration(data: bytes) -> float | None:
    """Seconds, read from the container headers, or None."""
    try:
        import mutagen
        f = mutagen.File(io.BytesIO(data))
        n = f.info.length if f is not None and f.info else 0
        return float(n) if n and n > 0 else None
    except Exception:  # unknown or broken container: fall back to the size proxy
        return None


def _mins(m: float) -> str:
    return f"{m:.0f} minute{'' if round(m) == 1 else 's'}" if m >= 1 else f"{m * 60:.0f} seconds"


def minutes(data: bytes, mime: str) -> float:
    """Length in minutes, or raise Refused(413). Unknown length is estimated from size."""
    video = mime.startswith("video/")
    what, cap, cap_mb = ("video", VIDEO_MINUTES, VIDEO_MB) if video else ("recording", AUDIO_MINUTES, AUDIO_MB)
    size = len(data) / MB
    if size > MAX_MB:
        raise Refused(413, f"This file is {size:.0f} MB; Canon accepts recordings up to {MAX_MB:.0f} MB.")
    secs = duration(data)
    if secs is None:
        if size > cap_mb:
            raise Refused(413, f"This {what} is {size:.0f} MB and its length cannot be read; "
                               f"Canon accepts up to {cap_mb:.0f} MB.")
        return cap * size / cap_mb  # ponytail: linear size proxy, a 10 MB audio counts as 10 minutes
    if secs / 60 > cap:
        raise Refused(413, f"This {what} is {_mins(secs / 60)}; Canon accepts up to {cap:.0f}.")
    return secs / 60


def day_key() -> str:
    return f"media-daily-{datetime.now(timezone.utc):%Y-%m-%d}"


async def admit(data: bytes, mime: str) -> float:
    """Check the file, then reserve its minutes in today's shared budget. Raises Refused."""
    m = minutes(data, mime)
    key, cap = day_key(), daily_minutes()
    d = await state.get(key)
    used = float(d.get("minutes", 0))
    # ponytail: read then write, so two instances at the same moment can overshoot by one file.
    # A Firestore transaction closes that if it ever matters.
    if used + m > cap:
        left = max(0.0, cap - used)
        raise Refused(429, f"Canon's daily recording budget of {cap:.0f} minutes is used up "
                           f"({_mins(left)} left, this file needs {_mins(m)}). It resets at 00:00 UTC.")
    await state.merge(key, {"minutes": round(used + m, 3), "files": int(d.get("files", 0)) + 1})
    return m
