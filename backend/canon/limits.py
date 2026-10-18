"""Input size limits at the trust boundary (HTTP and MCP). Every string field is capped."""
from pydantic import BaseModel

MAX = {
    "question": 1000, "intent": 2000, "query": 1000, "statement": 1000, "rationale": 2000,
    "description": 2000, "note": 2000, "text": 50_000, "source_text": 50_000, "title": 300,
    "author": 200, "url": 2048, "actor": 100, "person_id": 100, "persona": 20, "since": 40,
    "image_b64": 15 * 1024 * 1024 * 4 // 3 + 4,  # 15 MB decoded (video); media.py applies the per-kind caps
}
DEFAULT = 2000


class TooLong(ValueError):
    def __init__(self, field: str, limit: int):
        super().__init__(f"{field} is longer than {limit} characters")
        self.field, self.limit = field, limit


def enforce(data: BaseModel | dict, prefix: str = "") -> None:
    """Raise TooLong for the first string field over its cap. Nested dicts are walked."""
    items = data.model_dump() if isinstance(data, BaseModel) else data
    for k, v in items.items():
        if isinstance(v, dict):
            enforce(v, f"{prefix}{k}.")
        elif isinstance(v, str) and len(v) > (cap := MAX.get(k, DEFAULT)):
            raise TooLong(prefix + k, cap)
