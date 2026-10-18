"""W26 audio and video ingest: mime sniffing, per-file caps, shared daily budget, no Gemini call on refusal,
Discord voice messages. No network."""
import base64
import io
import wave
from datetime import datetime, timezone

import httpx2
import pytest

from canon import app as app_mod, llm, media
from canon.connectors import discord_sync as ds, state

T0 = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def wav(seconds: float) -> bytes:
    """8 kHz mono 8-bit PCM: 8000 bytes a second, so 11 minutes is about 5 MB."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1), w.setsampwidth(1), w.setframerate(8000)
        w.writeframes(b"\x80" * int(8000 * seconds))
    return buf.getvalue()


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


WEBM_HEAD = b"\x1a\x45\xdf\xa3" + b"\x00" * 20 + b"webm"


@pytest.mark.parametrize("head,mime", [
    (wav(0.1), "audio/wav"), (b"OggS\x00\x02" + b"\x00" * 30, "audio/ogg"), (b"ID3\x04" + b"\x00" * 30, "audio/mpeg"),
    (b"\xff\xfb\x90\x00" + b"\x00" * 30, "audio/mpeg"), (b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 20, "audio/mp4"),
    (b"\x00\x00\x00\x20ftypisom" + b"\x00" * 20, "video/mp4"), (b"\x00\x00\x00\x14ftypqt  " + b"\x00" * 20, "video/quicktime"),
    (WEBM_HEAD + b"A_OPUS", "audio/webm"), (WEBM_HEAD + b"V_VP9" + b"A_OPUS", "video/webm"),
    (b"FORM\x00\x00\x00\x10AIFF", "audio/aiff"), (b"%PDF-1.7", "application/pdf"), (b"\xff\xd8\xff\xe0", "image/jpeg"),
    (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "image/webp"), (b"\x89PNG\r\n\x1a\n", "image/png"),
])
def test_mime_by_magic_bytes(head, mime):
    assert llm._mime(b64(head)) == mime


def test_per_file_caps():
    assert media.minutes(wav(30), "audio/wav") == pytest.approx(0.5)
    with pytest.raises(media.Refused) as e:
        media.minutes(wav(14 * 60), "audio/wav")
    assert e.value.status == 413 and e.value.message == "This recording is 14 minutes; Canon accepts up to 10."
    # unknown length: the size proxy decides (audio 10 MB, video 15 MB)
    assert media.minutes(WEBM_HEAD + b"\x00" * media.MB, "video/webm") == pytest.approx(2 / 15, rel=0.01)
    with pytest.raises(media.Refused, match="length cannot be read; Canon accepts up to 10 MB"):
        media.minutes(b"OggS" + b"\x00" * (11 * media.MB), "audio/ogg")
    with pytest.raises(media.Refused, match="Canon accepts recordings up to 15 MB"):
        media.minutes(WEBM_HEAD + b"\x00" * (16 * media.MB), "video/webm")


def test_video_cap_is_two_minutes(monkeypatch):
    monkeypatch.setattr(media, "duration", lambda data: 180.0)
    with pytest.raises(media.Refused, match="This video is 3 minutes; Canon accepts up to 2."):
        media.minutes(b"x", "video/mp4")


async def test_daily_budget_is_one_shared_counter(monkeypatch):
    monkeypatch.setenv("CANON_MEDIA_DAILY_MINUTES", "1")
    clip = wav(24)  # 0.4 min
    assert await media.admit(clip, "audio/wav") == pytest.approx(0.4)
    await media.admit(clip, "audio/wav")
    assert (await state.get(media.day_key())) == {"minutes": pytest.approx(0.8), "files": 2}  # what every instance reads
    with pytest.raises(media.Refused) as e:
        await media.admit(clip, "audio/wav")
    assert e.value.status == 429 and "daily recording budget of 1 minutes" in e.value.message
    assert (await state.get(media.day_key()))["files"] == 2  # a refusal reserves nothing


def _src(data: bytes) -> dict:
    return {"source": {"kind": "paste", "title": "Recording", "author": "Visitor", "ts": T0.isoformat(),
                       "text": "", "image_b64": b64(data)}}


async def test_refusal_never_calls_gemini(monkeypatch):
    calls = []
    llm.FAKE_RESPONSES["Extraction"] = lambda p: calls.append(p) or {}
    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app_mod.app), base_url="http://test") as c:
        r = await c.post("/api/ingest", json=_src(wav(14 * 60)), headers={"X-Canon-Workspace": "v-t"})
        assert r.status_code == 413
        assert r.json()["detail"] == "This recording is 14 minutes; Canon accepts up to 10."
        monkeypatch.setenv("CANON_MEDIA_DAILY_MINUTES", "0.1")
        r = await c.post("/api/ingest", json=_src(wav(30)), headers={"X-Canon-Workspace": "v-t"})
        assert r.status_code == 429 and r.json()["error"] == "media_refused"
    assert calls == []


async def test_accepted_audio_gets_media_prompt_and_transcript():
    seen = []
    llm.FAKE_RESPONSES["Extraction"] = lambda p: seen.append(p) or {
        "transcript": "From November, the notice period is forty five days.", "effective_date": "",
        "approval_quote": "", "facts": [],
        "decisions": [{"kind": "rule", "statement": "The notice period is 45 days from November.", "rationale": "",
                       "assumptions": [], "owner": "Visitor", "topic": "notice period",
                       "quotes": ["the notice period is forty five days"], "is_joke_or_hypothetical": False}]}
    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app_mod.app), base_url="http://test") as c:
        r = await c.post("/api/ingest", json=_src(wav(20)), headers={"X-Canon-Workspace": "v-t"})
    assert r.status_code == 200, r.text
    assert "audio or video recording" in seen[0]
    out = r.json()
    assert "[transcript]\nFrom November, the notice period is forty five days." in out["source"]["text"]
    assert [d["decision"]["statement"] for d in out["decisions"]] == ["The notice period is 45 days from November."]


class FakeDiscord:
    def __init__(self, files):
        self.files, self.posts, self.downloads = files, [], []

    async def post(self, path, json):
        self.posts.append((path, json))
        return {}

    async def download(self, url, limit):
        self.downloads.append(url)
        return self.files[url][:limit]


def voice(i, url, size=4000, flags=ds.VOICE_MESSAGE):
    return {"id": str(i), "content": "", "type": 0, "timestamp": T0.isoformat(), "flags": flags,
            "author": {"username": "mitushi"},
            "attachments": [{"filename": "voice-message.ogg", "content_type": "audio/ogg", "size": size, "url": url}]}


async def test_discord_voice_message_routing_and_refusal_reply():
    seen = []
    llm.FAKE_RESPONSES["Extraction"] = lambda p: seen.append(p) or {
        "transcript": "Ship it Monday.", "effective_date": "", "approval_quote": "", "facts": [], "decisions": []}
    chan = {"id": "200", "name": "Release window", "parent_name": "engineering", "guild_id": "g1", "type": 11}
    ok, long, huge = voice(1, "https://cdn/ok.ogg"), voice(2, "https://cdn/long.wav", flags=0), \
        voice(3, "https://cdn/huge.ogg", size=40 * media.MB)
    long["attachments"][0].update(filename="standup.wav", content_type="audio/wav")
    assert all(ds.eligible(m) for m in (ok, long, huge))  # no text, but a recording counts
    assert ds.file_kind({"filename": "clip.mov", "size": 1}) == "media"
    fake = FakeDiscord({"https://cdn/ok.ogg": b"OggS" + b"\x00" * 4000, "https://cdn/long.wav": wav(14 * 60)})
    sent = await ds.ingest_group([ok, long, huge], chan, fake)
    assert len(seen) == 1 and "audio or video recording" in seen[0]  # only the short voice message reached Gemini
    assert "https://cdn/huge.ogg" not in fake.downloads  # too big: never downloaded
    replies = {b["message_reference"]["message_id"]: b["content"] for p, b in fake.posts}
    assert all(p == "/channels/200/messages" for p, _ in fake.posts)  # inside the thread
    assert replies == {"2": "Canon did not read this recording. This recording is 14 minutes; Canon accepts up to 10.",
                       "3": "Canon did not read this recording. This file is 40 MB; Canon accepts recordings up to 15 MB."}
    assert len(sent) == 2
