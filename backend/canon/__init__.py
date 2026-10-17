"""Expand the single `canon-config` secret (JSON, mounted as env CANON_CONFIG) into
CANON_* env vars before any module reads them. Explicit env vars win.
ponytail: one secret instead of one per value (Secret Manager bills per secret)."""
import json
import os

for _k, _v in json.loads(os.environ.get("CANON_CONFIG") or "{}").items():
    os.environ.setdefault(f"CANON_{_k.upper()}", str(_v))
