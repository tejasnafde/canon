"""Persistence. Firestore database `canon`, or an in-memory store when CANON_MEMORY_STORE=1.

Docs are plain dicts with `id`, `workspace`, `created_at`. `embedding` is a list[float] on
write and is stripped from every read. Every read takes the workspace scope explicitly.
"""
import asyncio
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Any

COLLECTIONS = ["sources", "chunks", "decisions", "alerts", "activity", "people", "resolutions"]


def now() -> datetime:
    return datetime.now(timezone.utc)


def utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _cos(a: list[float], b: list[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


class MemoryStore:
    def __init__(self):
        self.db: dict[str, dict[str, dict]] = {c: {} for c in COLLECTIONS}

    async def put(self, coll: str, doc: dict) -> str:
        doc = dict(doc)
        doc.setdefault("id", new_id(coll[0]))
        doc.setdefault("created_at", now())
        self.db[coll][doc["id"]] = doc
        return doc["id"]

    async def update(self, coll: str, id: str, fields: dict) -> None:
        self.db[coll][id].update(fields)

    async def get(self, coll: str, id: str) -> dict | None:
        d = self.db[coll].get(id)
        return _clean(d) if d else None

    async def get_many(self, coll: str, ids: list[str]) -> dict[str, dict]:
        return {i: _clean(self.db[coll][i]) for i in set(ids) if i in self.db[coll]}

    async def query(self, coll: str, workspaces: list[str], since: datetime | None = None,
                    limit: int | None = None, **eq) -> list[dict]:
        out = [_clean(d) for d in self.db[coll].values() if d["workspace"] in workspaces
               and all(d.get(k) == v for k, v in eq.items())
               and (since is None or d["created_at"] > since)]
        out.sort(key=lambda d: d["created_at"], reverse=True)
        return out[:limit] if limit else out

    async def nearest(self, coll: str, workspaces: list[str], vector: list[float], k: int) -> list[tuple[dict, float]]:
        scored = [(_clean(d), _cos(vector, d["embedding"])) for d in self.db[coll].values()
                  if d["workspace"] in workspaces and d.get("embedding")]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    async def delete_workspace(self, ws: str) -> None:
        for c in COLLECTIONS:
            for i in [i for i, d in self.db[c].items() if d["workspace"] == ws]:
                del self.db[c][i]


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "embedding"}


class FirestoreStore:
    def __init__(self):
        from google.cloud import firestore
        self.fs = firestore
        self.client = firestore.AsyncClient(project=os.environ.get("CANON_PROJECT", "teejayproject"),
                                            database="canon")

    def _doc(self, doc: dict) -> dict:
        from google.cloud.firestore_v1.vector import Vector
        if doc.get("embedding") is not None:
            doc = {**doc, "embedding": Vector(doc["embedding"])}
        return doc

    async def put(self, coll: str, doc: dict) -> str:
        doc = dict(doc)
        doc.setdefault("id", new_id(coll[0]))
        doc.setdefault("created_at", now())
        await self.client.collection(coll).document(doc["id"]).set(self._doc(doc))
        return doc["id"]

    async def update(self, coll: str, id: str, fields: dict) -> None:
        await self.client.collection(coll).document(id).update(self._doc(fields))

    async def get(self, coll: str, id: str) -> dict | None:
        s = await self.client.collection(coll).document(id).get()
        return _clean(s.to_dict()) if s.exists else None

    async def get_many(self, coll: str, ids: list[str]) -> dict[str, dict]:
        refs = [self.client.collection(coll).document(i) for i in set(ids)]
        out = {}
        if refs:
            async for s in self.client.get_all(refs):
                if s.exists:
                    out[s.id] = _clean(s.to_dict())
        return out

    async def _query_ws(self, coll, ws, since, limit, eq):
        F = self.fs.FieldFilter
        q = self.client.collection(coll).where(filter=F("workspace", "==", ws))
        for k, v in eq.items():
            q = q.where(filter=F(k, "==", v))
        if since is not None:
            # needs composite index (workspace, created_at); see firestore.indexes.json
            fq = q.where(filter=F("created_at", ">", since)).order_by("created_at", direction="DESCENDING")
            if limit:
                fq = fq.limit(limit)
            from google.api_core.exceptions import FailedPrecondition
            try:
                return [_clean(s.to_dict()) async for s in fq.stream()]
            except FailedPrecondition:  # index not built yet: filter in code
                pass
        docs = [_clean(s.to_dict()) async for s in q.stream()]
        return [d for d in docs if since is None or d["created_at"] > since]

    async def query(self, coll: str, workspaces: list[str], since: datetime | None = None,
                    limit: int | None = None, **eq) -> list[dict]:
        parts = await asyncio.gather(*(self._query_ws(coll, ws, since, limit, eq) for ws in workspaces))
        out = [d for p in parts for d in p]
        out.sort(key=lambda d: d["created_at"], reverse=True)
        return out[:limit] if limit else out

    async def _nearest_ws(self, coll, ws, vector, k):
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        from google.cloud.firestore_v1.vector import Vector
        q = (self.client.collection(coll).where(filter=self.fs.FieldFilter("workspace", "==", ws))
             .find_nearest(vector_field="embedding", query_vector=Vector(vector), limit=k,
                           distance_measure=DistanceMeasure.COSINE, distance_result_field="_dist"))
        out = []
        async for s in q.stream():
            d = s.to_dict()
            out.append((_clean({k2: v for k2, v in d.items() if k2 != "_dist"}), 1.0 - d["_dist"]))
        return out

    async def nearest(self, coll: str, workspaces: list[str], vector: list[float], k: int) -> list[tuple[dict, float]]:
        # One equality-prefiltered query per workspace, merged: no `in` filter on vector queries.
        parts = await asyncio.gather(*(self._nearest_ws(coll, ws, vector, k) for ws in workspaces))
        out = sorted((x for p in parts for x in p), key=lambda x: x[1], reverse=True)
        return out[:k]

    async def delete_workspace(self, ws: str) -> None:
        for c in COLLECTIONS:
            q = self.client.collection(c).where(filter=self.fs.FieldFilter("workspace", "==", ws))
            refs = [s.reference async for s in q.select([]).stream()]
            for i in range(0, len(refs), 400):
                batch = self.client.batch()
                for r in refs[i:i + 400]:
                    batch.delete(r)
                await batch.commit()


_store = None


def get_store():
    global _store
    if _store is None:
        _store = MemoryStore() if os.environ.get("CANON_MEMORY_STORE") == "1" else FirestoreStore()
    return _store


def reset_store_for_tests() -> MemoryStore:
    global _store
    _store = MemoryStore()
    return _store


# ---- record API behind canon.core (reads, alert resolution, activity) ----

async def list_decisions(workspaces, status=None, topic=None):
    from canon.models import Decision
    eq = {k: v for k, v in (("status", status), ("topic", topic)) if v}
    docs = await get_store().query("decisions", workspaces, **eq)
    return [Decision(**d) for d in sorted(docs, key=lambda d: utc(d["ts"]), reverse=True)]


async def _alerts_with_overlay(workspaces, docs):
    """Visitors cannot write to `acme`, so resolving a base alert writes a `resolutions` row in their workspace."""
    res = {r["alert_id"]: r for r in await get_store().query("resolutions", workspaces)}
    for a in docs:
        if a["id"] in res:
            a["status"], a["resolution"] = "resolved", res[a["id"]]["resolution"]
    return docs


async def list_alerts(workspaces, status=None):
    from canon.models import Alert
    docs = await _alerts_with_overlay(workspaces, await get_store().query("alerts", workspaces))
    return [Alert(**a) for a in docs if not status or a["status"] == status]


async def get_decision(decision_id, workspaces):
    from canon.ask import timeline
    from canon.models import Alert, Decision, DecisionDetail, Source
    st = get_store()
    d = await st.get("decisions", decision_id)
    if not d or d["workspace"] not in workspaces:
        raise KeyError(decision_id)
    tl, srcs, alerts = await asyncio.gather(
        timeline([d], workspaces), st.get_many("sources", [q["source_id"] for q in d["quotes"]]),
        st.query("alerts", workspaces))
    alerts = [a for a in alerts if decision_id in (a.get("decision_id"), a.get("related_decision_id"))]
    alerts = await _alerts_with_overlay(workspaces, alerts)
    return DecisionDetail(decision=Decision(**d), timeline=tl, sources=[Source(**s) for s in srcs.values()],
                          alerts=[Alert(**a) for a in alerts])


async def resolve_alert(alert_id, req, workspaces):
    from canon.models import Alert
    st = get_store()
    a = await st.get("alerts", alert_id)
    if not a or a["workspace"] not in workspaces:
        raise KeyError(alert_id)
    ws = workspaces[-1]
    resolution = f"{req.action}: {req.note}".rstrip(": ")
    mine = a["workspace"] == ws
    writes = []
    new, old = a.get("decision_id"), a.get("related_decision_id")
    decs = await st.get_many("decisions", [i for i in (new, old) if i])
    writable = {i for i, d in decs.items() if d["workspace"] == ws}
    if req.action == "accept_update" and old in writable and new in writable:
        writes += [st.update("decisions", old, {"status": "superseded", "superseded_by": new}),
                   st.update("decisions", new, {"supersedes": decs[new].get("supersedes", []) + [old]})]
    if req.action == "retire_decision" and new in writable:
        writes.append(st.update("decisions", new, {"status": "retired"}))
    if mine:
        writes.append(st.update("alerts", alert_id, {"status": "resolved", "resolution": resolution}))
    else:
        writes.append(st.put("resolutions", {"id": f"{ws}~{alert_id}", "workspace": ws, "alert_id": alert_id,
                                             "resolution": resolution}))
    await asyncio.gather(*writes)
    await log_activity(ws, req.actor, "resolve", f"Resolved {a['kind']} alert: {resolution}", [alert_id])
    return Alert(**{**a, "status": "resolved", "resolution": resolution})


async def get_source(source_id, workspaces):
    from canon.models import Source
    s = await get_store().get("sources", source_id)
    if not s or s["workspace"] not in workspaces:
        raise KeyError(source_id)
    return Source(**s)


async def list_activity(workspaces, since_iso=None):
    from canon.models import Activity
    since = utc(datetime.fromisoformat(since_iso.replace("Z", "+00:00"))) if since_iso else None
    return [Activity(**a) for a in await get_store().query("activity", workspaces, since=since, limit=100)]


async def log_activity(workspace, actor, action, summary, ref_ids=None, verdict=None):
    await get_store().put("activity", {"id": new_id("act"), "workspace": workspace, "actor": actor, "action": action,
                                       "summary": summary, "ref_ids": [i for i in (ref_ids or []) if i][:20],
                                       "verdict": verdict, "created_at": now()})


async def list_people(workspaces):
    from canon.models import Person
    return [Person(**p) for p in sorted(await get_store().query("people", workspaces), key=lambda p: p["name"])]


async def reset_workspace(workspace):
    if workspace == "acme":
        raise PermissionError("the base workspace is read-only")
    await get_store().delete_workspace(workspace)
