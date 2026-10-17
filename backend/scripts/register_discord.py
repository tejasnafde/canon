"""Register the global /canon slash command. Run once by hand; do not run in CI.

Env: DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN.
Then set the app's Interactions Endpoint URL to <base>/discord/interactions.
"""
import os

import httpx

STRING, SUB = 3, 1
COMMAND = {
    "name": "canon",
    "description": "Ask the company's decision record",
    "options": [
        {"type": SUB, "name": "ask", "description": "Why do we do X? Cited answer.",
         "options": [{"type": STRING, "name": "question", "description": "Your question", "required": True}]},
        {"type": SUB, "name": "check", "description": "Check an action against past decisions",
         "options": [{"type": STRING, "name": "intent", "description": "What you plan to do", "required": True}]},
        {"type": SUB, "name": "catchup", "description": "What changed lately",
         "options": [
             {"type": STRING, "name": "persona", "description": "Who you are",
              "choices": [{"name": n, "value": n} for n in ("engineer", "pm", "new_hire")]},
             {"type": 4, "name": "days", "description": "Look back this many days (default 7)"},
         ]},
    ],
}

if __name__ == "__main__":
    app_id = os.environ["DISCORD_APPLICATION_ID"]
    r = httpx.put(f"https://discord.com/api/v10/applications/{app_id}/commands", json=[COMMAND],
                  headers={"Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}"})
    r.raise_for_status()
    print("registered:", [c["name"] for c in r.json()])
