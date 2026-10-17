"""W20 authority: who may set a rule. Computed in code from the org tree, topic owners and channel weights.

official: the author owns the topic (or sits under its owner) at lead level or above, or an IC in that chain
          has an approval quote, a meeting, or an official channel behind them. The CEO is always official.
proposed: an IC without approval, a lead/head outside their area, a casual channel, an unknown non-Discord author.
claim:    a Discord guest (no person has that discord_username), or an IC outside their area.
With no org data in scope at all everything is official (the pre-W20 behaviour).

The org files are bundled in canon/org/ (the image has no data/ dir); test_w20 checks they match data/org/.
"""
import json
import re
from pathlib import Path

from canon.store import get_store

ORG = Path(__file__).resolve().parent / "org"
TOPICS: dict[str, dict] = json.loads((ORG / "topics.json").read_text())
CHANNELS: dict[str, dict] = json.loads((ORG / "channels.json").read_text())
RANK = {"ic": 0, "lead": 1, "head": 2, "exec": 3}


def _n(s: str | None) -> str:
    return " ".join((s or "").lower().split())


class Org:
    """People of the read scope, keyed by bare person id (seed.py prefixes ids with the workspace)."""

    def __init__(self, people: list[dict]):
        self.by_id: dict[str, dict] = {}
        for p in people:
            pid = p["id"][len(p["workspace"]) + 1:] if p["id"].startswith(p["workspace"] + "-") else p["id"]
            self.by_id.setdefault(pid, {**p, "id": pid})
        self.by_name = {_n(p["name"]): p for p in self.by_id.values()}
        self.by_discord = {_n(p["discord_username"]): p for p in self.by_id.values() if p.get("discord_username")}

    def find(self, who: str | None, discord: bool = False) -> dict | None:
        w = _n(who)
        if discord:
            return self.by_discord.get(w)
        return self.by_name.get(w) or self.by_id.get(w) or self.by_discord.get(w)

    def chain(self, p: dict) -> list[dict]:
        """p, their manager, ... up to the CEO."""
        out, seen = [], set()
        while p and p["id"] not in seen:
            seen.add(p["id"])
            out.append(p)
            p = self.by_id.get(p.get("reports_to") or "")
        return out

    def common_manager(self, a: dict, b: dict) -> dict | None:
        ids = {p["id"] for p in self.chain(b)}
        return next((p for p in self.chain(a) if p["id"] in ids), None)

    def label(self, p: dict) -> str:
        return f"{p['name']} ({p['role']})"


async def load_org(scope: list[str]) -> Org:
    return Org(await get_store().query("people", scope))


def org_topic(topic: str, statement: str = "") -> str | None:
    """Map a free-form decision topic ("deploys", "leave policy") to a key of topics.json by word stems."""
    def stems(s):
        return {w[:5] for w in re.findall(r"[a-z]+", s.lower()) if len(w) >= 4}
    t = stems(topic)
    best = max(TOPICS, key=lambda k: len(stems(k.replace("/", " ")) & t))
    if stems(best.replace("/", " ")) & t:
        return best
    s = stems(statement)  # fall back to the statement only when the topic word itself is unknown
    best = max(TOPICS, key=lambda k: len(stems(k.replace("/", " ")) & s))
    return best if stems(best.replace("/", " ")) & s else None


def discord_channel(src: dict) -> str | None:
    """'#engineering' for a source synced from Discord (title 'Discord #engineering / thread'), else None."""
    m = re.match(r"Discord (#[\w-]+)", src.get("title") or "")
    if m or "discord.com/" in (src.get("url") or ""):
        return m.group(1) if m else "#unknown"
    return None


def owner_of(topic_key: str | None, org: Org) -> dict | None:
    return org.by_id.get(TOPICS[topic_key]["owner"]) if topic_key else None


def authority(dec: dict, src: dict, org: Org, approved: bool = False) -> str:
    if not org.by_id:
        return "official"
    chan = discord_channel(src)
    weight = CHANNELS.get(chan or "", {}).get("weight") if chan else None
    person = org.find(src["author"], discord=chan is not None)
    if person is None and chan is None and src["kind"] == "meeting":
        person = org.find(dec.get("owner"))  # a meeting record names who decided
    if person is None:
        return "claim" if chan is not None else "proposed"
    key = org_topic(dec.get("topic", ""), dec.get("statement", ""))
    owner = owner_of(key, org)
    teams = TOPICS[key]["teams"] if key else []
    in_area = key is None or person["team"] in teams or (owner is not None and owner["id"] in
                                                         {p["id"] for p in org.chain(person)})
    rank = RANK.get(person.get("level", "ic"), 0)
    backed = approved or src["kind"] == "meeting" or weight == "official"
    if rank == 3:
        out = "official"
    elif not in_area:
        out = "proposed" if rank >= 1 else "claim"
    elif rank >= 1 or backed:
        out = "official"
    else:
        out = "proposed"
    if weight == "casual" and out == "official" and not approved:
        out = "proposed"  # banter channels do not set policy without an approval quote
    return out


def decider(new: dict, old: dict, src: dict, org: Org) -> dict | None:
    """Who should confirm or dismiss a conflict: the lowest common manager when the two sides sit in different
    teams, else the owner of the topic, else the old decision's owner."""
    a = org.find(src["author"], discord=discord_channel(src) is not None) or org.find(new.get("owner"))
    b = org.find(old.get("owner"))
    if a and b and a["team"] != b["team"]:
        return org.common_manager(a, b)
    return owner_of(org_topic(old.get("topic", ""), old.get("statement", "")), org) or b
