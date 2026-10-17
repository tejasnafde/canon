"""End-to-end flow replayed from recorded Gemini fixtures (tests/fixtures/llm/).

Re-record after changing a prompt:
  GOOGLE_APPLICATION_CREDENTIALS=... CANON_FAKE_LLM=0 CANON_RECORD=1 uv run pytest tests/test_replay.py
"""
from canon import core
from canon.models import AskRequest, CheckRequest, IngestRequest, Source

WS = ["acme"]
OLD = Source(kind="meeting", title="Release calendar pilot", author="Anika Rao", ts="2025-01-16T09:00:00Z",
             text="Anika: For now the production release window is Friday afternoon, 14:00 to 16:00 Singapore time. "
                  "Support volume is lowest then.")
NEW = Source(kind="meeting", title="INC-042 review: the Friday release", author="Mei Tan", ts="2026-03-09T09:00:00Z",
             text="Mei: Decision from the review. No production deploys on Fridays, including scheduled jobs and "
                  "configuration-only releases. Ordinary release slots move to Tuesday and Thursday mornings.")


async def test_recorded_flow():
    await core.ingest(IngestRequest(source=OLD), WS)
    r = await core.ingest(IngestRequest(source=NEW), WS)
    assert "update" in {d.relation for d in r.decisions}
    a = await core.ask(AskRequest(question="Why can we no longer deploy production on Fridays?"), WS)
    assert not a.refused and a.citations and len(a.timeline) >= 2
    assert (await core.ask(AskRequest(question="What is our annual recurring revenue for 2026?"), WS)).refused
    c = await core.check(CheckRequest(intent="Deploy the dispatch service to production this Friday at 15:00."), WS)
    assert c.verdict == "block"
