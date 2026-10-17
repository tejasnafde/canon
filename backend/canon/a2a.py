"""F18: Canon as an ADK agent, served over A2A.

Agent card: /.well-known/agent-card.json. JSON-RPC endpoint: /a2a.
The agent's tools wrap canon.core; they read `acme` + the shared `agents` workspace.
"""
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "teejayproject")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "asia-south1")

from a2a.server.request_handlers import DefaultRequestHandler  # noqa: E402
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes  # noqa: E402
from a2a.server.tasks import InMemoryTaskStore  # noqa: E402
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor  # noqa: E402
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder  # noqa: E402
from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from canon import core  # noqa: E402
from canon.models import AskRequest, BriefingRequest, CheckRequest  # noqa: E402

WORKSPACES = [os.environ.get("CANON_BASE_WS", "acme"), "agents"]
ACTOR = "agent:a2a"
PUBLIC_URL = os.environ.get("CANON_PUBLIC_URL", "https://canon-tn07.web.app").rstrip("/")


async def check_intent(intent: str) -> dict:
    """Check an intended action (deploy, infra, API, pricing, process change) against
    the company's recorded decisions. Returns verdict allow/warn/block with the deciding
    decisions and quotes."""
    return (await core.check(CheckRequest(intent=intent, actor=ACTOR), WORKSPACES)).model_dump(mode="json")


async def ask_why(question: str) -> dict:
    """Answer a 'why do we ...' question from the decision record, with citations.
    If `refused` is true the record has no answer."""
    return (await core.ask(AskRequest(question=question, actor=ACTOR), WORKSPACES)).model_dump(mode="json")


async def search_decisions(query: str) -> list[dict]:
    """Semantic search over active decisions about a topic."""
    found = await core.search_decisions(query, WORKSPACES, limit=5)
    await core.log_activity(WORKSPACES[-1], ACTOR, "search", f"search: {query}", ref_ids=[d.id for d in found])
    return [d.model_dump(mode="json") for d in found]


async def catch_me_up(persona: str = "engineer", days: int = 7) -> dict:
    """Briefing of decision changes in the last `days` days for persona engineer, pm or new_hire."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    req = BriefingRequest(persona=persona, since=since, actor=ACTOR)
    return (await core.briefing(req, WORKSPACES)).model_dump(mode="json")


agent = LlmAgent(
    name="canon",
    model=os.environ.get("CANON_MODEL", "gemini-3.5-flash-lite"),
    description=(
        "Canon, the company's decision record. Ask why something is the way it is, "
        "check an intended action against past decisions, or get caught up."
    ),
    instruction=(
        "You answer only from Canon's tools. For any intended action, call check_intent and "
        "report the verdict and the deciding decisions with their owners. For why-questions, "
        "call ask_why and cite sources; if it refuses, say the record has no answer. "
        "Never invent decisions."
    ),
    tools=[check_intent, ask_why, search_decisions, catch_me_up],
    generate_content_config=types.GenerateContentConfig(labels={"app": "canon"}),
)


async def mount(app) -> None:
    """Attach the agent card and the A2A JSON-RPC route to the FastAPI app (called at startup)."""
    if any(getattr(r, "path", None) == "/a2a" for r in app.router.routes):
        return  # lifespan ran before (tests start the app more than once)
    card = await AgentCardBuilder(agent=agent, rpc_url=f"{PUBLIC_URL}/a2a").build()
    handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(runner=InMemoryRunner(agent=agent, app_name="canon")),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app.router.routes.extend([
        *create_agent_card_routes(card),  # /.well-known/agent-card.json
        *create_jsonrpc_routes(handler, "/a2a", enable_v0_3_compat=True),
    ])
