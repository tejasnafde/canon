"""Every persona gets a briefing whose top action is the item from its own area."""
from datetime import datetime, timedelta, timezone

import pytest

from canon import core, llm
from canon.briefing import PERSONAS
from canon.models import BriefingRequest
from canon.store import get_store

TODAY = datetime.now(timezone.utc)
# persona -> (owner team, source kind, decision statement)
ITEMS = {
    "engineer": ("Platform", "pr", "Run database migrations only through the CI pipeline with a rollback plan."),
    "pm": ("Product", "email", "Route Lens roadmap: the pilot scope for customers ships as a beta first."),
    "design": ("Design", "doc", "All new screens use the Figma design system and pass an accessibility review."),
    "data": ("Data", "pr", "Delivery ETA metrics dashboards read from the BigQuery warehouse only."),
    "security": ("Security", "pr", "SSO with MFA is required for admin access; rotate secrets every 90 days."),
    "sales": ("Sales", "email", "Reps may offer at most a 15% discount on annual deals in the order form."),
    "support": ("Customer", "slack", "Support answers enterprise tickets within 1 hour; escalate outages to the status page."),
    "marketing": ("Marketing", "doc", "The webinar campaign and landing page messaging go out with the new brand."),
    "finance": ("Finance", "email", "Cloud spend budget is capped per quarter; invoices from a vendor need approval."),
    "operations": ("Operations", "wiki", "Dispatch carriers follow the new runbook during the weekend maintenance."),
    "people": ("People", "wiki", "The review cycle runs in November and the handbook adds five PTO days of leave."),
    "legal": ("Legal", "email", "EU customer data stays in the EU region per the DPA, with 13 months retention."),
    "leadership": ("Leadership", "meeting", "Q4 OKRs keep headcount flat; the strategy depends on Sales and Platform."),
    "new_hire": ("Quality", "wiki", "Every change needs a second reviewer approval; this is the standard policy."),
}


async def seed():
    st = get_store()
    ts = TODAY - timedelta(days=3)
    for persona, (team, kind, statement) in ITEMS.items():
        name = f"{team} Lead{persona.replace('_', '')}"
        await st.put("people", {"id": f"p-{persona}", "workspace": "acme", "name": name, "role": f"{team} lead",
                                "team": team, "status": "active"})
        await st.put("sources", {"id": f"s-{persona}", "workspace": "acme", "kind": kind, "title": f"{persona} src",
                                 "author": name, "ts": ts, "text": statement, "created_at": ts})
        await st.put("decisions", {"id": f"d-{persona}", "workspace": "acme", "statement": statement, "rationale": "",
                                   "assumptions": [], "owner": name, "ts": ts, "topic": persona, "status": "active",
                                   "supersedes": [], "quotes": [{"source_id": f"s-{persona}", "quote": statement}],
                                   "created_by": "human", "created_at": ts})


@pytest.mark.parametrize("persona", list(PERSONAS))
async def test_every_persona_gets_its_own_area_first(persona):
    assert set(PERSONAS) == set(ITEMS)
    await seed()
    prompts = []
    llm.FAKE_RESPONSES["Prose"] = lambda p: prompts.append(p) or {
        "summary": "s", "highlights": ["h"], "titles": [], "whys": []}
    b = await core.briefing(BriefingRequest(persona=persona, since=TODAY - timedelta(days=30)), ["acme"])
    assert b.actions[0].citations[0].decision_id == f"d-{persona}", [a.title for a in b.actions[:3]]
    assert any(r.startswith("relevant to") for r in b.actions[0].reasons)
    assert f"For {PERSONAS[persona]['label']}, " in prompts[0]
    if PERSONAS[persona]["teams"]:
        assert b.who_to_ask[0].id == f"p-{persona}"
