"""Set up the public "Northwind Labs" Discord demo server. Idempotent.

- one text channel per team, under a "Teams" category, with a topic
- the Northwind server icon
- corpus Slack threads re-posted as real Discord threads: the first message goes into the channel
  through a channel webhook as its author, the bot opens a thread on it named after the source, and
  the replies go into that thread through the same webhook (quoting the message they answer)
- wiki pages (stale ones included) posted as .md file attachments with a casual line
- screenshots from data/discord/screens/*.png (render with data/discord/render_screens.py)
- a permanent invite link, printed at the end

Everything is posted through the webhook, and the sync skips webhook messages, so nothing here is
ingested twice. --reset recreates a team channel that holds no human messages (the bot cannot delete
threads, it lacks Manage Threads); #general keeps its invite, so there it deletes webhook posts instead.

Usage: CANON_DISCORD_BOT_TOKEN=... CANON_DISCORD_GUILD_ID=... \
       uv run python scripts/discord_populate.py --data ../data [--reset]
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
HOOK = "Northwind archive"
CHANNELS = {  # channel -> (people teams that post there, topic, threads to post)
    "general": ((), "Company-wide chatter. Canon reads every channel.", 4),
    "engineering": (("Platform", "Integrations", "Quality", "Engineering"), "Deploys, incidents, PRs.", 6),
    "product": (("Product",), "Roadmap, launches, pricing.", 6),
    "design": (("Design",), "Design system and accessibility.", 4),
    "data": (("Data", "Analytics"), "Metrics and dashboards.", 4),
    "security": (("Security",), "Access, retention, residency.", 4),
    "sales": (("Sales",), "Deals, discounts, pricing decks.", 6),
    "support": (("Customer", "Support"), "SLAs, escalations, customer notices.", 4),
    "marketing": (("Marketing",), "Campaigns and messaging.", 4),
    "finance": (("Finance",), "Billing, invoices, travel policy.", 4),
    "operations": (("Operations",), "Ops and vendors.", 4),
    "people": (("People", "HR"), "Hiring, handbook, reviews.", 4),
    "legal": (("Legal",), "Contracts and DPAs.", 4),
    "leadership": (("Leadership",), "OKRs, budget, hiring plans.", 4),
}
HERO = ("INC-042 live dispatch thread",)  # always posted, whatever the selection rules say
GENERAL = ("First week, same kettle", "Lunch order has two Am is", "Friday lunch count",
           "Farewell lunch dietary count")  # office chatter for #general
# channel -> (wiki title, who posts it, the line that goes with the file)
DOCS = {
    "engineering": [("Release process", "Thao Tran", "updated the release doc, pls read before friday"),
                    ("Carrier webhook recovery", "Chen Wei", "webhook recovery runbook, pinning it here so ppl stop asking"),
                    ("Booking retry cookbook", "Thao Tran", "booking retry cookbook for the new folks")],
    "product": [("Route Lens launch brief", "Farah Khan", "launch brief attached, this is what we send to the web team"),
                ("Audit retention FAQ", "Thao Tran", "audit retention FAQ in case a customer asks again")],
    "sales": [("Route Lens sales pricing deck", "Arjun Desai", "pricing deck for this quarter, use this one not the old pdf"),
              ("Route Lens sales FAQ", "Farah Khan", "sales FAQ, the objection handling bit is at the bottom")],
    "support": [("Support access handbook", "Ravi Perera", "support access handbook, read before you take a prod session"),
                ("Priority support routing handbook", "Siti Nuraini", "P1 routing handbook. print it, stick it on the wall")],
    "marketing": [("Route Pilot brand guide", "Farah Khan", "brand guide v2 here, logos + naming rules")],
    "people": [("Employee handbook hiring chapter", "Amina Yusuf", "handbook hiring chapter, managers pls skim before next loop")],
    "data": [("Active workspace dashboard glossary", "Linh Nguyen", "dashboard glossary so we all count the same thing")],
    "legal": [("Contract approval matrix", "Nandini Wijaya", "contract approval matrix, who signs what")],
    "finance": [("Customer invoice terms sheet", "Nur Aziz", "invoice terms sheet for AEs, ping me if unclear")],
    "operations": [("Depot kit replenishment playbook", "Devika Fernando", "kit replenishment playbook, reorder rules inside")],
    "design": [("Dispatch design system", "Yuki Mori", "design system page exported, colours + states")],
    "leadership": [("Operating plan hiring freeze", "Hana Okafor", "operating plan section on hiring, for context")],
    "security": [("Vendor access playbook", "Jiwon Park", "vendor access playbook. yes it is long, sorry")],
}
# (channel, png, who posts it, the line that goes with it, where it sits in the channel timeline)
SCREENS = [
    ("engineering", "grafana.png", "Haruto Sato", "grafana from friday for the review doc. rollout marker at 15:10, peak ACK age ~11 min",
     "2026-03-06T09:00:00Z"),
    ("engineering", "calendar.png", "Mei Tan", "fyi the release window invite is still on everyone's calendar every friday",
     "2026-10-12T02:00:00Z"),
    ("support", "ticket.png", "Siti Nuraini", "INC-042 closed. customer notice timeline is in the ticket if anyone asks",
     "2026-03-10T08:00:00Z"),
    ("sales", "pricing.png", "Arjun Desai", "screenshot of the pricing page from the sept enablement deck, the one prospects keep sending back",
     "2025-09-25T03:00:00Z"),
    ("product", "roadmap.png", "Aisha Rahman", "roadmap after the replan. GA moved, gate unchanged",
     "2026-04-09T09:00:00Z"),
]
LINE = re.compile(r"^(?:\d{1,2}:\d{2}(?:\s+SGT)?\s+)?([A-Z][\w.'-]+(?: [A-Z][\w.'-]+){0,2}):\s+(.+)$")
REPLY_WORDS = re.compile(r"^(yes|yep|yeah|no|nope|right|agreed|ok|okay|sure|correct|good question)\b", re.I)
MAX_REPLIES = 12


def avatar(name: str) -> str:
    """Illustrated (not photo) avatar, stable per person. Same URL the web app uses."""
    return ("https://api.dicebear.com/9.x/notionists/png?size=128&backgroundColor=f6f1e7&seed="
            + urllib.parse.quote(name))


def parse(text: str, author: str, full: dict[str, str]) -> list[list[str]]:
    """[[who, text]] from a corpus Slack thread. Lines without a speaker continue the previous message."""
    out: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("Thread replies"):
            continue
        if m := LINE.match(line):
            out.append([full.get(m[1], m[1]), m[2]])
        elif out:
            out[-1][1] += "\n" + line
        else:
            out.append([author, line])
    return out


def with_quotes(msgs: list[list[str]], limit: int = 2) -> list[list[str]]:
    """Prefix '> quoted line' on a reply that clearly answers an earlier, non-adjacent message:
    it names that person, or it starts with yes/no/right... after a question two or three messages up."""
    out = [list(m) for m in msgs]
    used = 0
    for i in range(2, len(msgs)):
        if used >= limit:
            break
        who, text = msgs[i]
        hit = None
        for j in range(i - 2, -1, -1):
            other = msgs[j][0]
            if other != who and re.search(rf"\b{re.escape(other.split()[0])}\b", text):
                hit = j
                break
        if hit is None and REPLY_WORDS.match(text) and not msgs[i - 1][1].rstrip().endswith("?"):
            hit = next((j for j in (i - 2, i - 3) if j >= 0 and msgs[j][0] != who
                        and msgs[j][1].rstrip().endswith("?")), None)
        if hit is not None:
            q = msgs[hit][1].splitlines()[0]
            q = q if len(q) <= 90 else q[:87].rsplit(" ", 1)[0] + "..."
            out[i][1] = f"> {q}\n{text}"
            used += 1
    return out


def pick(items: list[dict], n: int, evidence: set[str]) -> list[dict]:
    """Hero threads, then the team's January agreement and its September correction (the update a judge
    can follow), then other threads with planted decisions, plus one latest chatter thread. Oldest first."""
    def tier(s):
        t = s["title"]
        if t in HERO:
            return 0
        if "working agreement" in t or "rollout correction" in t:
            return 1
        if t in evidence:
            return 2 + ("rollout agreement" in t)
        return 4

    chosen = sorted(items, key=lambda s: (tier(s), s["ts"]))[:max(n - 1, 1)]
    rest = sorted((s for s in items if s not in chosen), key=lambda s: s["ts"], reverse=True)
    noise = [s for s in rest if s["title"] not in evidence][:1] or rest[:1]
    return sorted(chosen + noise, key=lambda s: s["ts"])[:n]


class Discord:
    def __init__(self, token: str, guild: str):
        self.c = httpx.Client(base_url=API, timeout=60, headers={"Authorization": f"Bot {token}"})
        self.guild = guild

    def call(self, method, url, auth=True, **kw):
        while True:
            r = self.c.request(method, url, **kw) if auth else httpx.request(method, API + url, timeout=60, **kw)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.2)
                continue
            r.raise_for_status()
            return r.json() if r.content else None

    def messages(self, ch: str) -> list[dict]:
        out, before = [], None
        while True:
            page = self.call("GET", f"/channels/{ch}/messages", params={"limit": 100, **({"before": before} if before else {})})
            out += page
            if len(page) < 100:
                return out
            before = page[-1]["id"]

    def threads(self, ch: str) -> list[dict]:
        active = [t for t in self.call("GET", f"/guilds/{self.guild}/threads/active")["threads"] if t["parent_id"] == ch]
        return active + self.call("GET", f"/channels/{ch}/threads/archived/public", params={"limit": 100})["threads"]

    def send(self, hook: dict, who: str, content: str = "", thread: str | None = None, file: Path | None = None,
             name: str | None = None, data: bytes | None = None) -> dict:
        """Post as `who` through the webhook (no bot token: webhook URLs carry their own auth)."""
        body = {"username": who, "avatar_url": avatar(who), "content": content[:1990], "allowed_mentions": {"parse": []}}
        params = {"wait": "true", **({"thread_id": thread} if thread else {})}
        url = f"/webhooks/{hook['id']}/{hook['token']}"
        if file or data is not None:
            files = {"files[0]": (name or file.name, data if data is not None else file.read_bytes())}
            msg = self.call("POST", url, auth=False, params=params, data={"payload_json": json.dumps(body)}, files=files)
        else:
            msg = self.call("POST", url, auth=False, params=params, json=body)
        time.sleep(0.45)  # webhooks allow about 5 posts per 2 s
        return msg


def reset(d: Discord, ch: dict, hook: dict | None, keep: bool) -> dict:
    """Empty a channel of archive posts. Recreate it when nobody but bots and webhooks ever posted there."""
    threads = d.threads(ch["id"])
    human = [m for m in d.messages(ch["id"]) if not m["author"].get("bot") and not m.get("webhook_id")
             and m.get("type", 0) in (0, 19)]
    for t in threads:
        human += [m for m in d.messages(t["id"]) if not m["author"].get("bot") and not m.get("webhook_id")]
    if not keep and not human:
        d.call("DELETE", f"/channels/{ch['id']}")
        body = {k: ch.get(k) for k in ("name", "topic", "parent_id", "position")}
        return d.call("POST", f"/guilds/{d.guild}/channels", json={**body, "type": 0})
    if hook:  # fallback: delete what the webhook posted, in the channel and in each thread
        for t in threads:
            for m in d.messages(t["id"]):
                if m.get("webhook_id") == hook["id"]:
                    d.call("DELETE", f"/webhooks/{hook['id']}/{hook['token']}/messages/{m['id']}",
                           auth=False, params={"thread_id": t["id"]})
        for m in d.messages(ch["id"]):
            if m.get("webhook_id") == hook["id"]:
                d.call("DELETE", f"/webhooks/{hook['id']}/{hook['token']}/messages/{m['id']}", auth=False)
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data")
    ap.add_argument("--icon", default="../brand/northwind/northwind-icon-512.png")
    ap.add_argument("--reset", action="store_true", help="remove archive posts and post again")
    ap.add_argument("--only", default="", help="comma-separated channels to (re)populate, default all")
    a = ap.parse_args()
    d = Discord(os.environ["CANON_DISCORD_BOT_TOKEN"], os.environ["CANON_DISCORD_GUILD_ID"])
    data = Path(a.data)

    icon = base64.b64encode(Path(a.icon).read_bytes()).decode()
    d.call("PATCH", f"/guilds/{d.guild}", json={"icon": f"data:image/png;base64,{icon}",
                                                "description": "Northwind Labs is a made-up company. Canon demo."})
    existing = {ch["name"]: ch for ch in d.call("GET", f"/guilds/{d.guild}/channels")}
    cat = existing.get("Teams") or d.call("POST", f"/guilds/{d.guild}/channels", json={"name": "Teams", "type": 4})
    chans = {}
    for pos, (name, (_, topic, _n)) in enumerate(CHANNELS.items()):
        ch = existing.get(name)
        body = {"topic": topic, "parent_id": cat["id"], "position": pos}
        chans[name] = d.call("PATCH", f"/channels/{ch['id']}", json=body) if ch else \
            d.call("POST", f"/guilds/{d.guild}/channels", json={"name": name, "type": 0, **body})

    people = json.loads((data / "people.json").read_text())
    team = {p["name"]: p["team"] for p in people}
    firsts = [p["name"].split()[0] for p in people]
    full = {p["name"].split()[0]: p["name"] for p in people if firsts.count(p["name"].split()[0]) == 1}
    gold = json.loads((data / "gold" / "gold.json").read_text())
    evidence = {e["source_title"] for it in gold["items"] for e in it.get("evidence", [])}
    team_channel = {t: ch for ch, (teams, _, _n) in CHANNELS.items() for t in teams}
    slack = [json.loads(line) for line in (data / "corpus" / "slack.jsonl").read_text().splitlines()]
    wiki = {s["title"]: s for s in map(json.loads, (data / "corpus" / "wiki.jsonl").read_text().splitlines())}
    pool = {ch: [] for ch in CHANNELS}
    for s in slack:
        ch = "general" if s["title"] in GENERAL else team_channel.get(team.get(s["author"], ""), "general")
        pool[ch].append(s)
    only = {c.strip() for c in a.only.split(",") if c.strip()}

    for name, (_, _, n) in CHANNELS.items():
        if only and name not in only:
            continue
        ch = chans[name]
        hook = next((h for h in d.call("GET", f"/channels/{ch['id']}/webhooks") if h["name"] == HOOK), None)
        posted = hook and any(m.get("webhook_id") == hook["id"] for m in d.messages(ch["id"]))
        if posted and not a.reset:
            print(f"#{name}: already populated")
            continue
        if posted or a.reset:
            new = reset(d, ch, hook, keep=name == "general")
            if new["id"] != ch["id"]:
                ch, hook = new, None
        hook = hook or d.call("POST", f"/channels/{ch['id']}/webhooks", json={"name": HOOK})

        items = [(s["ts"], "thread", s) for s in pick(pool[name], n, evidence)]
        items += [(wiki[t]["ts"], "doc", (t, who, line)) for t, who, line in DOCS.get(name, [])]
        items += [(when, "screen", (png, who, line)) for c, png, who, line, when in SCREENS if c == name]
        counts = {"thread": 0, "doc": 0, "screen": 0, "message": 0}
        for _, kind, it in sorted(items, key=lambda x: x[0]):
            if kind == "thread":
                msgs = with_quotes(parse(it["text"], it["author"], full)[:MAX_REPLIES + 1])
                if not msgs:
                    continue
                first = d.send(hook, *msgs[0])
                th = d.call("POST", f"/channels/{ch['id']}/messages/{first['id']}/threads",
                            json={"name": it["title"][:100], "auto_archive_duration": 10080})
                for who, text in msgs[1:]:
                    d.send(hook, who, text, thread=th["id"])
                counts["message"] += len(msgs)
            elif kind == "doc":
                title, who, line = it
                d.send(hook, who, line, name=f"{title}.md", data=wiki[title]["text"].encode())
            else:
                png, who, line = it
                d.send(hook, who, line, file=data / "discord" / "screens" / png)
            counts[kind] += 1
        print(f"#{name}: {counts['thread']} threads ({counts['message']} messages), "
              f"{counts['doc']} docs, {counts['screen']} screenshots")

    inv = d.call("POST", f"/channels/{chans['general']['id']}/invites", json={"max_age": 0, "max_uses": 0, "unique": False})
    print(f"invite: https://discord.gg/{inv['code']}")


if __name__ == "__main__":
    main()
