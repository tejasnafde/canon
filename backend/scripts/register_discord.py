"""Register the /canon slash command. Run once by hand; do not run in CI.

Env: DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN, optional CANON_DISCORD_GUILD_ID (guild-scoped
commands appear instantly; global ones can take up to an hour).
Then set the app's Interactions Endpoint URL to <base>/discord/interactions. See setup_discord.md.
"""
import os
from typing import get_args

import httpx

from canon.models import Persona

STRING, INTEGER, SUB = 3, 4, 1
LABELS = {"pm": "Product", "people": "HR", "new_hire": "New hire"}
COMMAND = {
    "name": "canon",
    "description": "Ask the company's decision record",
    "options": [
        {"type": SUB, "name": "ask", "description": "Why do we do X? Cited answer.",
         "options": [{"type": STRING, "name": "question", "description": "Your question", "required": True}]},
        {"type": SUB, "name": "check", "description": "Check an action against past decisions",
         "options": [{"type": STRING, "name": "intent", "description": "What you plan to do", "required": True}]},
        {"type": SUB, "name": "catchup", "description": "What changed lately for your role",
         "options": [
             {"type": STRING, "name": "role", "description": "Your role",
              "choices": [{"name": LABELS.get(p, p.capitalize()), "value": p} for p in get_args(Persona)]},
             {"type": INTEGER, "name": "days", "description": "Look back this many days (default 7)",
              "min_value": 1, "max_value": 365},
         ]},
        {"type": SUB, "name": "remember", "description": "Add a note or decision to the record now",
         "options": [{"type": STRING, "name": "text", "description": "What was decided, and why",
                      "required": True, "max_length": 4000}]},
    ],
}

if __name__ == "__main__":
    app_id = os.environ["DISCORD_APPLICATION_ID"]
    gid = os.environ.get("CANON_DISCORD_GUILD_ID")
    path = f"/applications/{app_id}/guilds/{gid}/commands" if gid else f"/applications/{app_id}/commands"
    r = httpx.put(f"https://discord.com/api/v10{path}", json=[COMMAND],
                  headers={"Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}"})
    r.raise_for_status()
    print("registered", "in guild " + gid if gid else "globally", [c["name"] for c in r.json()])
