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


async def merge(key: str, fields: dict) -> None:
    st = get_store()
    if isinstance(st, MemoryStore):
        st.db.setdefault(COLL, {}).setdefault(key, {}).update(fields)
    else:
        await st.client.collection(COLL).document(key).set(fields, merge=True)
