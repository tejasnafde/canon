"""W17 populate v2 helpers: corpus thread parsing, reply quoting, thread selection. No network."""
from scripts.discord_populate import parse, pick, with_quotes

FULL = {"Haruto": "Haruto Sato", "Mei": "Mei Tan", "Chen": "Chen Wei"}


def test_parse_splits_first_message_and_replies():
    text = ("# INC\n15:14 SGT Haruto: ACK age is 11 minutes.\n\nThread replies (2):\n"
            "15:15 Mei Tan: looking.\nsecond line of Mei\n15:16 Chen Wei: partner status is green?")
    assert parse(text, "Haruto Sato", FULL) == [["Haruto Sato", "ACK age is 11 minutes."],
                                                ["Mei Tan", "looking.\nsecond line of Mei"],
                                                ["Chen Wei", "partner status is green?"]]
    assert parse("no speaker here", "Ana B", FULL) == [["Ana B", "no speaker here"]]


def test_quotes_only_clear_answers():
    msgs = [["Chen Wei", "I can check the token failures."], ["Mei Tan", "rolling back."],
            ["Haruto Sato", "pinned the SHA."], ["Mei Tan", "Chen please keep checking the queue."]]
    out = with_quotes(msgs)
    assert out[3][1] == "> I can check the token failures.\nChen please keep checking the queue."
    assert [m[1] for m in out[:3]] == [m[1] for m in msgs[:3]]  # no quote on the adjacent replies
    q = [["A x", "Can we ship on Friday?"], ["B y", "hmm"], ["C z", "No, not after INC-042."]]
    assert with_quotes(q)[2][1].startswith("> Can we ship on Friday?\n")


def test_pick_prefers_hero_and_the_update_pair():
    items = [{"title": t, "ts": ts} for t, ts in [
        ("Sales: rollout agreement 2", "2026-09-02"), ("Sales: January working agreement", "2026-01-01"),
        ("Coffee", "2026-10-01"), ("Sales: September rollout correction", "2026-09-01"),
        ("Old chatter", "2025-01-01"), ("INC-042 live dispatch thread", "2026-03-06")]]
    ev = {"Sales: rollout agreement 2", "Sales: January working agreement", "Sales: September rollout correction"}
    got = [s["title"] for s in pick(items, 4, ev)]
    assert got == ["Sales: January working agreement", "INC-042 live dispatch thread",
                   "Sales: September rollout correction", "Coffee"]
