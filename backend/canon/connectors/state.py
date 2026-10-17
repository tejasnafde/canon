"""Connector state (cursors, daily counters) in Firestore collection `connector_state`.

One doc per key. Kept out of store.COLLECTIONS on purpose: workspace reset must not rewind cursors.
"""
from canon.store import MemoryStore, get_store

COLL = "connector_state"


async def get(key: str) -> dict:
    st = get_store()
    if isinstance(st, MemoryStore):
        return dict(st.db.setdefault(COLL, {}).get(key, {}))
    s = await st.client.collection(COLL).document(key).get()
    return s.to_dict() if s.exists else {}


async def get_many(keys: list[str]) -> dict[str, dict]:
    """One batched read for many keys (a quiet Discord sync reads every cursor at once)."""
    st = get_store()
    if isinstance(st, MemoryStore):
        db = st.db.setdefault(COLL, {})
        return {k: dict(db[k]) for k in keys if k in db}
    refs = [st.client.collection(COLL).document(k) for k in dict.fromkeys(keys)]
    return {s.id: s.to_dict() async for s in st.client.get_all(refs) if s.exists} if refs else {}


async def merge(key: str, fields: dict) -> None:
    st = get_store()
    if isinstance(st, MemoryStore):
        st.db.setdefault(COLL, {}).setdefault(key, {}).update(fields)
    else:
        await st.client.collection(COLL).document(key).set(fields, merge=True)
