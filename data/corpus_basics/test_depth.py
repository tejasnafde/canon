"""Offline checks for the depth supplement. Run: python3 -m pytest data/corpus_basics/test_depth.py -q"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'data'))
import validate


def load():
    people = json.loads((ROOT / 'data/people.json').read_text())
    rows = [json.loads(x) for x in (ROOT / 'data/corpus_basics/depth.jsonl').read_text().splitlines()]
    return rows, people


def test_depth_file_is_valid():
    rows, people = load()
    assert validate.validate_depth(rows, people) == []
    errors, _ = validate.validate(ROOT / 'data')
    assert errors == []


def test_depth_rejects_bad_rows():
    rows, people = load()
    for change in ({'author': 'Nobody'}, {'workspace': 'acme'}, {'ts': '2027-01-01T00:00:00Z'},
                   {'ts': '2026-01-01'}, {'kind': 'invalid'}, {'synthetic': False},
                   {'url': 'https://real.com/page'}, {'author': 'Ravi Perera'},
                   {'text': 'Our annual recurring revenue is'}, {'text': 'the partner portal password'},
                   {'text': 'which model replaces it'}, {'text': chr(0x2014)}, {'text': chr(0x1F600)}):
        bad = [{**rows[0], **change}] + rows[1:]
        assert validate.validate_depth(bad, people), change
    assert validate.validate_depth(rows + [rows[0]], people)
    assert validate.validate_depth(rows, people, taken_titles={rows[0]['title']})
    assert validate.validate_depth(rows[:10], people)
