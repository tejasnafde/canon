"""All Gemini access. Real Vertex calls, or FakeLLM replay when CANON_FAKE_LLM=1.

CANON_RECORD=1 makes real calls and writes each response to tests/fixtures/llm/<key>.json,
so a later CANON_FAKE_LLM=1 run replays it byte for byte.
"""
import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

log = logging.getLogger("canon.llm")

PROJECT = os.environ.get("CANON_PROJECT", "teejayproject")
LOCATION = os.environ.get("CANON_LOCATION", "asia-south1")
MODEL = os.environ.get("CANON_MODEL", "gemini-3.5-flash-lite")
EMBED_MODEL = "gemini-embedding-001"
DIMS = 768
LABELS = {"app": "canon"}
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "llm"

# Tests can register programmatic responses by schema name: FAKE_RESPONSES["Extraction"] = fn(prompt) or dict.
FAKE_RESPONSES: dict[str, Any] = {}

_client = None
_sem = asyncio.Semaphore(int(os.environ.get("CANON_LLM_CONCURRENCY", "16")))
_query_cache: dict[str, list[float]] = {}  # ponytail: unbounded, fine for a demo-sized question set


def fake() -> bool:
    return os.environ.get("CANON_FAKE_LLM") == "1"


def recording() -> bool:
    return os.environ.get("CANON_RECORD") == "1"


def client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    return _client


def _key(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:24]


def _fixture(key: str) -> Any | None:
    p = FIXTURES / f"{key}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _record(key: str, value: Any) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / f"{key}.json").write_text(json.dumps(value))


async def _retry(fn):
    """Exponential backoff with jitter on 429 / 5xx."""
    from google.genai import errors
    for attempt in range(6):
        try:
            return await fn()
        except errors.APIError as e:
            code = getattr(e, "code", None) or 0
            if code not in (429, 500, 503, 504) or attempt == 5:
                raise
            delay = min(20, 0.5 * 2 ** attempt) + random.random() * 0.5
            log.warning("gemini %s, retry in %.1fs", code, delay)
            await asyncio.sleep(delay)


def _mime(b64: str) -> str:
    if b64.startswith("JVBER"):
        return "application/pdf"
    if b64.startswith("/9j/"):
        return "image/jpeg"
    if b64.startswith("R0lG"):
        return "image/gif"
    if b64.startswith("UklG"):
        return "image/webp"
    return "image/png"


async def generate_json(prompt: str, schema: type[BaseModel], *, system: str | None = None,
                        image_b64: str | None = None, temperature: float = 0.0) -> dict:
    """One structured-output call. Returns the parsed dict matching `schema`."""
    name = schema.__name__
    key = _key(MODEL, system, prompt, schema.model_json_schema(), bool(image_b64) and image_b64[:64])
    if fake():
        hit = _fixture(key)
        if hit is not None:
            return hit
        if name in FAKE_RESPONSES:
            r = FAKE_RESPONSES[name]
            return r(prompt) if callable(r) else r
        raise KeyError(f"FakeLLM: no fixture {key} and no FAKE_RESPONSES[{name!r}]")

    from google.genai import types
    parts: list[Any] = [prompt]
    if image_b64:
        parts.insert(0, types.Part.from_bytes(data=base64.b64decode(image_b64), mime_type=_mime(image_b64)))
    cfg = types.GenerateContentConfig(
        system_instruction=system, temperature=temperature, labels=LABELS,
        response_mime_type="application/json", response_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    async def call():
        async with _sem:
            return await client().aio.models.generate_content(model=MODEL, contents=parts, config=cfg)

    resp = await _retry(call)
    out = resp.parsed.model_dump() if isinstance(resp.parsed, BaseModel) else json.loads(resp.text)
    if recording():
        _record(key, out)
    return out


def _fake_vec(text: str) -> list[float]:
    """Deterministic bag-of-words vector: shared words give cosine similarity."""
    v = [0.0] * DIMS
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 2:
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIMS] += 1.0
    return v


async def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """768-dim embeddings, one per text, in order. Batched and parallel."""
    if not texts:
        return []
    if fake():
        out = []
        for t in texts:
            hit = _fixture(_key(EMBED_MODEL, task, t))
            out.append(hit if hit is not None else _fake_vec(t))
        return out
    if task == "RETRIEVAL_QUERY" and len(texts) == 1 and texts[0] in _query_cache:
        return [_query_cache[texts[0]]]

    from google.genai import types
    cfg = types.EmbedContentConfig(output_dimensionality=DIMS, task_type=task, auto_truncate=True)

    async def one(batch: list[str]):
        async def call():
            async with _sem:
                return await client().aio.models.embed_content(model=EMBED_MODEL, contents=batch, config=cfg)
        r = await _retry(call)
        return [e.values for e in r.embeddings]

    batches = [texts[i:i + 50] for i in range(0, len(texts), 50)]
    out = [v for b in await asyncio.gather(*(one(b) for b in batches)) for v in b]
    if recording():
        for t, v in zip(texts, out):
            _record(_key(EMBED_MODEL, task, t), v)
    if task == "RETRIEVAL_QUERY" and len(texts) == 1:
        _query_cache[texts[0]] = out[0]
    return out
