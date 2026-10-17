"""Set up the public "Northwind Labs" Discord demo server. Idempotent.

- one text channel per team, under a "Teams" category, with a topic
- the Northwind server icon
- recent corpus Slack threads re-posted through a channel webhook as the people who
  wrote them (webhook messages are skipped by the sync, so nothing is ingested twice)
- a permanent invite link, printed at the end

Usage: CANON_DISCORD_BOT_TOKEN=... CANON_DISCORD_GUILD_ID=... \
       uv run python scripts/discord_populate.py --data ../data [--per-channel 5]
"""
import argparse
import base64
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import httpx

API = "https://discord.com/api/v10"
CHANNELS = {  # channel -> (people teams that post there, topic)
    "general": ((), "Company-wide chatter. Canon reads every channel."),
    "engineering": (("Platform", "Integrations", "Quality", "Engineering"), "Deploys, incidents, PRs."),
    "product": (("Product",), "Roadmap, launches, pricing."),
    "design": (("Design",), "Design system and accessibility."),
    "data": (("Data", "Analytics"), "Metrics and dashboards."),
    "security": (("Security",), "Access, retention, residency."),
    "sales": (("Sales",), "Deals, discounts, pricing decks."),
    "support": (("Customer", "Support"), "SLAs, escalations, customer notices."),
    "marketing": (("Marketing",), "Campaigns and messaging."),
    "finance": (("Finance",), "Billing, invoices, travel policy."),
    "operations": (("Operations",), "Ops and vendors."),
    "people": (("People", "HR"), "Hiring, handbook, reviews."),
    "legal": (("Legal",), "Contracts and DPAs."),
    "leadership": (("Leadership",), "OKRs, budget, hiring plans."),
}
LINE = re.compile(r"^(?:\d{1,2}:\d{2}\s+)?([A-Z][\w.'-]+(?: [A-Z][\w.'-]+){0,2}):\s+(.+)$")


def avatar(name: str) -> str:
    """Illustrated (not photo) avatar, stable per person. Same URL the web app uses."""
    return ("https://api.dicebear.com/9.x/notionists/png?size=128&backgroundColor=f6f1e7&seed="
            + urllib.parse.quote(name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data")
    ap.add_argument("--per-channel", type=int, default=5)
    ap.add_argument("--icon", default="../brand/northwind/northwind-icon-512.png")
    ap.add_argument("--reset", action="store_true", help="delete archive posts and post again")
    a = ap.parse_args()
    guild = os.environ["CANON_DISCORD_GUILD_ID"]
    c = httpx.Client(base_url=API, timeout=30,
                     headers={"Authorization": f"Bot {os.environ['CANON_DISCORD_BOT_TOKEN']}"})

    def call(method, url, **kw):
        while True:
            r = c.request(method, url, **kw)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.2)
                continue
            r.raise_for_status()
            return r.json() if r.content else None

    icon = base64.b64encode(Path(a.icon).read_bytes()).decode()
    call("PATCH", f"/guilds/{guild}", json={"icon": f"data:image/png;base64,{icon}",
                                            "description": "Northwind Labs is a made-up company. Canon demo."})

    existing = {ch["name"]: ch for ch in call("GET", f"/guilds/{guild}/channels")}
    cat = existing.get("Teams") or call("POST", f"/guilds/{guild}/channels", json={"name": "Teams", "type": 4})
    ids = {}
    for pos, (name, (_, topic)) in enumerate(CHANNELS.items()):
        ch = existing.get(name)
        body = {"topic": topic, "parent_id": cat["id"], "position": pos}
        ch = call("PATCH", f"/channels/{ch['id']}", json=body) if ch else \
            call("POST", f"/guilds/{guild}/channels", json={"name": name, "type": 0, **body})
        ids[name] = ch["id"]

    people = {p["name"]: p for p in json.loads(Path(a.data, "people.json").read_text())}
    team_channel = {t: ch for ch, (teams, _) in CHANNELS.items() for t in teams}
    threads = {ch: [] for ch in CHANNELS}
    for line in Path(a.data, "corpus", "slack.jsonl").read_text().splitlines():
        s = json.loads(line)
        team = people.get(s["author"], {}).get("team", "")
        threads[team_channel.get(team, "general")].append(s)

    for ch, items in threads.items():
        hooks = call("GET", f"/channels/{ids[ch]}/webhooks")
        hook = next((h for h in hooks if h["name"] == "Northwind archive"), None) or \
            call("POST", f"/channels/{ids[ch]}/webhooks", json={"name": "Northwind archive"})
        posted = [m for m in call("GET", f"/channels/{ids[ch]}/messages?limit=100") if m.get("webhook_id") == hook["id"]]
        if posted and not a.reset:
            continue  # already populated
        for m in posted:
            call("DELETE", f"/webhooks/{hook['id']}/{hook['token']}/messages/{m['id']}")
            time.sleep(0.3)
        for s in sorted(items, key=lambda s: s["ts"])[-a.per_channel:]:
            msgs = [m.groups() for m in map(LINE.match, s["text"].splitlines()) if m]
            for who, text in msgs[:12]:
                call("POST", f"/webhooks/{hook['id']}/{hook['token']}",
                     json={"username": who, "avatar_url": avatar(who), "content": text[:1900],
                           "allowed_mentions": {"parse": []}})
                time.sleep(0.4)
        print(f"#{ch}: posted {min(len(items), a.per_channel)} threads")

    inv = call("POST", f"/channels/{ids['general']}/invites", json={"max_age": 0, "max_uses": 0, "unique": False})
    print(f"invite: https://discord.gg/{inv['code']}")


if __name__ == "__main__":
    main()
