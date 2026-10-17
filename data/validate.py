#!/usr/bin/env python3
"""Validate the synthetic data contract using only the Python standard library."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

KINDS = {'slack', 'meeting', 'wiki', 'pr', 'commit', 'email', 'doc', 'paste', 'agent'}
ROLE_MINIMUMS = {role: 3 for role in (
    'design', 'data', 'security', 'sales', 'support', 'marketing', 'finance',
    'operations', 'people', 'legal', 'leadership')}
PERSONAS = set(ROLE_MINIMUMS) | {'engineer', 'pm', 'new_hire'}

MINIMUMS = {'decision': 25, 'stale_doc': 8, 'premise_change': 5}


def validate(root):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def read(path):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc:
            errors.append(f'{path}: {exc}')
            return None

    def timestamp(value):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            require(dt.tzinfo is not None, f'Timestamp lacks timezone: {value}')
            return dt if dt.tzinfo else None
        except (ValueError, TypeError, AttributeError):
            errors.append(f'Invalid timestamp: {value!r}')
            return None

    rows = []
    for path in sorted((root / 'corpus').glob('*.jsonl')):
        for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            try:
                row = json.loads(line)
            except ValueError as exc:
                errors.append(f'{path.name}:{line_no}: {exc}')
                continue
            if not isinstance(row, dict):
                errors.append(f'{path.name}:{line_no}: source must be an object')
                continue
            rows.append(row)
            label = f'{path.name}:{line_no}'
            require(set(row) == {'workspace', 'kind', 'title', 'author', 'ts', 'url', 'text', 'synthetic'},
                    f'{label}: unexpected Source fields or missing required fields')
            for field in ('title', 'author', 'text', 'url'):
                require(isinstance(row.get(field), str) and bool(row.get(field)), f'{label}: invalid {field}')
            require(row.get('workspace') == 'acme', f'{label}: workspace must be acme')
            require(row.get('synthetic') is True, f'{label}: synthetic must be true')
            require(row.get('kind') in KINDS, f'{label}: invalid kind')
            url = row.get('url', '')
            require(isinstance(url, str) and url.startswith('https://') and '.example/' in url,
                    f'{label}: URL must be a fake .example deep link')
            dt = timestamp(row.get('ts'))
            if dt:
                require(datetime(2025, 1, 1, tzinfo=timezone.utc) <= dt < datetime(2026, 11, 1, tzinfo=timezone.utc),
                        f'{label}: timestamp outside corpus range')
    require(380 <= len(rows) <= 460, f'Expected 380-460 sources, got {len(rows)}')
    titles = [r.get('title') for r in rows]
    require(len(titles) == len(set(titles)), 'Source titles must be unique')
    require(len({r.get('url') for r in rows}) == len(rows), 'Source URLs must be unique')
    for kind in ('slack', 'meeting', 'wiki', 'pr', 'commit', 'email'):
        require(any(r.get('kind') == kind for r in rows), f'Missing source kind: {kind}')
    indexed = {r.get('title'): r for r in rows}
    people = read(root / 'people.json')
    if isinstance(people, list):
        require(23 <= len(people) <= 60, 'Expected 23-60 people')
        require(len({p['id'] for p in people}) == len(people), 'Duplicate person IDs')
        require(sum(p.get('status') == 'left' for p in people) == 3, 'Expected exactly three departed people')
        names = {p['name'] for p in people}
        for p in people:
            require(set(p) == {'id', 'name', 'role', 'team', 'status', 'left_at'}, f'Invalid Person fields: {p}')
            require(p.get('status') in {'active', 'left'}, f'Invalid Person status: {p}')
            if p.get('status') == 'left':
                timestamp(p.get('left_at'))
            else:
                require(p.get('left_at') is None, f'Active person has departure date: {p["name"]}')
        for row in rows:
            require(row.get('author') in names, f'Unknown author: {row.get("author")}')
    else:
        errors.append('people.json must be a list')

    gold = read(root / 'gold' / 'gold.json')
    counts = Counter()
    if isinstance(gold, dict):
        items = gold.get('items', [])
        keys = [i['key'] for i in items]
        require(len(keys) == len(set(keys)), 'Gold keys must be unique')
        decisions = {i['key']: i for i in items if i.get('type') == 'decision'}
        for item in items:
            teams = item.get('teams', [])
            require(isinstance(teams, list) and bool(teams) and
                    all(t in PERSONAS for t in teams), f'{item["key"]}: missing or invalid teams')
            typ = item.get('type')
            counts[typ] += 1
            require(typ in {'decision', 'update', 'contradiction', 'stale_doc', 'premise_change'}, f'Invalid gold type: {typ}')
            require(item.get('decision_key') in decisions, f'{item["key"]}: unknown deciding key')
            if 'related_decision_key' in item:
                require(item['related_decision_key'] in decisions, f'{item["key"]}: unknown prior decision')
            require(bool(item.get('evidence')), f'{item["key"]}: no evidence')
            for ev in item.get('evidence', []):
                row = indexed.get(ev.get('source_title'))
                require(row is not None, f'{item["key"]}: unknown source title {ev.get("source_title")}')
                require(bool(ev.get('quote')), f'{item["key"]}: empty quote')
                if row:
                    require(isinstance(ev.get('quote'), str) and ev['quote'] in row.get('text', ''),
                            f'{item["key"]}: quote is not an exact substring in {row["title"]}')
            if typ == 'stale_doc' and len(item.get('evidence', [])) >= 2:
                old, current = [indexed.get(e['source_title']) for e in item['evidence'][:2]]
                if old and current:
                    require(old['kind'] == 'wiki' and old['ts'] < current['ts'], f'{item["key"]}: stale wiki must predate its correction')
        for typ, minimum in MINIMUMS.items():
            require(counts[typ] >= minimum, f'Expected at least {minimum} {typ}, got {counts[typ]}')
        require(counts['update'] + counts['contradiction'] >= 12, 'Expected at least 12 contradictions/updates')
        require(sum(i.get('owner') == 'Anika Rao' for i in decisions.values()) >= 8, 'Departed expert needs many recorded decisions')
        for section, number in [('check_intent', 15), ('answerable_questions', 10), ('unanswerable_questions', 5)]:
            cases = gold.get(section, [])
            require(len(cases) == number if section == 'unanswerable_questions' else len(cases) >= number,
                    f'{section}: expected {number} cases minimum (exact for refusals)')
            require(len({c['key'] for c in cases}) == len(cases), f'{section}: duplicate keys')
            for case in cases:
                refs = case.get('expected_decision_keys', [case['decision_key']] if 'decision_key' in case else [])
                for key in refs:
                    require(key in decisions, f'{case["key"]}: unknown decision key {key}')
                if section == 'check_intent':
                    require(case.get('expected_verdict') in {'allow', 'warn', 'block'}, f'{case["key"]}: invalid verdict')
                if section == 'unanswerable_questions':
                    require(case.get('expected_refused') is True, f'{case["key"]}: must expect refusal')
    else:
        errors.append('gold.json must be an object')
        decisions = {}
    role_counts = {}
    owner_teams = {p['name']: p['team'].lower() for p in people} if isinstance(people, list) else {}
    for role, minimum in ROLE_MINIMUMS.items():
        owned = [d for d in decisions.values() if role in d.get('teams', [])
                 and owner_teams.get(d.get('owner')) == role]
        role_counts[role] = len(owned)
        require(len(owned) >= minimum, f'{role}: expected at least {minimum} owned decisions')
        for typ in ('stale_doc', 'update'):
            require(any(i.get('type') == typ and role in i.get('teams', [])
                        for i in (gold or {}).get('items', [])), f'{role}: missing {typ}')
        for section in ('check_intent', 'answerable_questions'):
            require(any(role in c.get('teams', []) for c in (gold or {}).get(section, [])),
                    f'{role}: missing {section} case')
    if isinstance(gold, dict):
        for section in ('check_intent', 'answerable_questions', 'unanswerable_questions'):
            for case in gold.get(section, []):
                teams = case.get('teams', [])
                require(isinstance(teams, list) and bool(teams) and all(t in PERSONAS for t in teams),
                        f'{case["key"]}: missing or invalid teams')
    samples = read(root / 'samples' / 'live_paste.json')
    if isinstance(samples, list):
        require(len(samples) == 3, 'Expected three paste samples')
        require({s.get('expected_relation') for s in samples} == {'new', 'update', 'contradiction'}, 'Paste samples must cover three relations')
        for sample in samples:
            require(bool(sample.get('source', {}).get('text')), 'Paste sample has no text')
            if sample.get('decision_key'):
                require(sample['decision_key'] in decisions, 'Paste sample references unknown decision')
    playground = read(root / 'samples' / 'agent_playground.json')
    tools = {'search_decisions', 'check_intent', 'ask_why', 'catch_me_up', 'record_decision', 'flag_conflict'}
    if isinstance(playground, list):
        require(len(playground) == 6 and {s.get('tool') for s in playground} == tools, 'Expected six distinct MCP tool examples')
        for sample in playground:
            require(isinstance(sample.get('args'), dict) and bool(sample.get('expected_outcome')), 'MCP sample lacks args or outcome')
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in {'.py', '.md', '.json', '.jsonl'}:
            require('\u2014' not in path.read_text(encoding='utf-8'), f'{path}: forbidden em dash')
    return errors, dict(sources=len(rows), people=len(people) if isinstance(people, list) else 0, planted=dict(counts), role_decisions=role_counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    errors, summary = validate(args.root)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    print('PASS: source schema, evidence, references, samples, people and minimum counts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
