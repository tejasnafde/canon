"""Regression checks for errors that could invalidate the benchmark labels."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate import validate


class CorpusValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'data'
        shutil.copytree(Path(__file__).resolve().parent, self.root,
                        ignore=shutil.ignore_patterns('__pycache__'))

    def mutate_gold(self, transform):
        path = self.root / 'gold' / 'gold.json'
        gold = json.loads(path.read_text())
        transform(gold)
        path.write_text(json.dumps(gold))

    def test_committed_corpus_passes(self):
        errors, summary = validate(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(summary['sources'], 380)

    def test_archive_has_real_document_shapes(self):
        rows = [json.loads(line) for path in (self.root / 'corpus').glob('*.jsonl')
                for line in path.read_text().splitlines()]
        for row in rows:
            text = row['text']
            if row['kind'] == 'meeting':
                self.assertTrue(300 <= len(text.split()) <= 900, row['title'])
            elif row['kind'] == 'slack':
                self.assertIn('Thread replies', text, row['title'])
            elif row['kind'] == 'pr':
                self.assertIn('```diff', text, row['title'])
                self.assertIn('Review comments', text, row['title'])
            elif row['kind'] == 'email':
                self.assertIn('Subject:', text, row['title'])
                self.assertIn('@northwind.example', text, row['title'])

    def test_no_emoji_or_departed_speakers(self):
        import re
        people = json.loads((self.root / 'people.json').read_text())
        departed = [p for p in people if p['left_at']]
        for path in (self.root / 'corpus').glob('*.jsonl'):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                self.assertNotRegex(row['text'], '[\U0001f000-\U0001ffff\u2600-\u27bf]')
                for person in departed:
                    if row['ts'] > person['left_at']:
                        self.assertNotRegex(row['text'], re.escape(person['name']) + r':')

    def test_role_decision_minimum_fails(self):
        self.mutate_gold(lambda g: g.update(items=[
            i for i in g['items'] if 'legal' not in i.get('teams', [])]))
        errors, _ = validate(self.root)
        self.assertTrue(any('legal: expected at least 3 owned decisions' in e for e in errors))

    def test_missing_persona_fails(self):
        self.mutate_gold(lambda g: g['items'][0].pop('teams'))
        errors, _ = validate(self.root)
        self.assertTrue(any('missing or invalid teams' in e for e in errors))

    def test_refusal_questions_are_preserved(self):
        gold = json.loads((self.root / 'gold' / 'gold.json').read_text())
        self.assertEqual(len(gold['unanswerable_questions']), 5)
        rows = [json.loads(line) for path in (self.root / 'corpus').glob('*.jsonl')
                for line in path.read_text().splitlines()]
        self.assertFalse(any('parental leave' in r['text'].lower() for r in rows))

    def test_nonexact_quote_fails(self):
        self.mutate_gold(lambda g: g['items'][0]['evidence'][0].update(quote='A quote never spoken here.'))
        errors, _ = validate(self.root)
        self.assertTrue(any('not an exact substring' in e for e in errors))

    def test_unknown_decision_reference_fails(self):
        self.mutate_gold(lambda g: g['check_intent'][0].update(decision_key='missing-decision'))
        errors, _ = validate(self.root)
        self.assertTrue(any('unknown decision key' in e for e in errors))

    def test_malformed_jsonl_fails(self):
        with (self.root / 'corpus' / 'slack.jsonl').open('a') as handle:
            handle.write('{not json}\n')
        errors, _ = validate(self.root)
        self.assertTrue(any('slack.jsonl:' in e for e in errors))

    def test_missing_premise_minimum_fails(self):
        self.mutate_gold(lambda g: g.update(items=[i for i in g['items'] if i['type'] != 'premise_change']))
        errors, _ = validate(self.root)
        self.assertTrue(any('at least 5 premise_change' in e for e in errors))

    def test_stale_wiki_after_correction_fails(self):
        path = self.root / 'corpus' / 'wiki.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]['ts'] = '2026-10-16T00:00:00Z'
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        errors, _ = validate(self.root)
        self.assertTrue(any('stale wiki must predate' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
