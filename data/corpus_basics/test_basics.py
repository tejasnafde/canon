"""Offline checks. Run: uv run --project backend pytest data/corpus_basics -q."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'data'))
sys.path.insert(0, str(ROOT / 'backend'))
import validate


def test_basics_and_mutations(tmp_path):
    people = json.loads((ROOT / 'data/people.json').read_text())
    rows = [json.loads(x) for x in (ROOT / 'data/corpus_basics/basics.jsonl').read_text().splitlines()]
    assert 28 <= len(rows) <= 32
    assert validate.validate_basics(rows, people) == []
    for change in ({'author': 'Nobody'}, {'workspace': 'acme'}, {'ts': '2027-01-01T00:00:00Z'},
                   {'ts': '2026-01-01'}, {'kind': 'invalid'}, {'text': 'parental leave'},
                   {'text': 'annual recurring revenue'}, {'text': 'replacement cache interval'},
                   {'text': 'partner portal password'}, {'text': 'regional model'},
                   {'text': 'acquired Northwind'}, {'text': chr(0x1F600)}, {'text': chr(0x2014)},
                   {'synthetic': False}, {'url': 'https://real.com/page'},
                   {'author': {}}, {'kind': []}, {'title': []}, {'ts': 1}, {'url': {}}):
        assert validate.validate_basics([{**rows[0], **change}], people), change
    assert validate.validate_basics([rows[0], rows[0]], people)


def script():
    spec = importlib.util.spec_from_file_location('add_sources', ROOT / 'backend/scripts/add_sources.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_importer_skips_titles_and_is_scoped(tmp_path, monkeypatch, capsys):
    from canon import store
    from canon.models import Source
    module = script()
    memory = store.reset_store_for_tests()
    async def scenario():
        await memory.put('sources', {'id': 'old', 'workspace': 'existing', 'title': 'Already'})
        await memory.put('sources', {'id': 'elsewhere', 'workspace': 'other', 'title': 'New'})
        rows = [Source(kind='wiki', title=t, author='Mei Tan', ts=ts, text='Fixture', workspace='acme4')
                for t, ts in [('Already', '2026-01-01T00:00:00Z'), ('New', '2026-02-01T00:00:00Z'),
                              ('New', '2026-03-01T00:00:00Z')]]
        calls = []
        async def ingest(req, workspaces):
            calls.append(req.source.title)
            assert workspaces == ['existing']
            assert req.source.workspace == 'existing'
            await memory.put('sources', {**req.source.model_dump(), 'id': 'new'})
            return SimpleNamespace(decisions=[], alerts=[])
        monkeypatch.setattr(module.core, 'ingest', ingest)
        await module.add_sources(rows, 'existing')
        await module.add_sources(rows, 'existing')
        assert calls == ['New']
        with pytest.raises(ValueError, match='existing workspace'):
            await module.add_sources(rows, 'missing')
    asyncio.run(scenario())
    assert 'Gemini' in capsys.readouterr().out


def test_load_validates_all_before_ingest(tmp_path):
    module = script()
    path = tmp_path / 'bad.jsonl'
    path.write_text('{}\n')
    with pytest.raises(ValueError):
        module.load(path)


def test_load_source_contract_and_chronology(tmp_path):
    module = script()
    path = ROOT / 'data/corpus_basics/basics.jsonl'
    sources = module.load(path)
    assert len(sources) == 30
    assert [(s.ts, s.title) for s in sources] == sorted((s.ts, s.title) for s in sources)
    row = sources[0].model_dump(mode='json')
    for mutation in ({'title': ' '}, {'ts': '2026-01-01'}, {'ts': 'broken'}):
        bad = tmp_path / 'bad.jsonl'
        bad.write_text(json.dumps({**row, **mutation}) + '\n')
        with pytest.raises(ValueError, match='bad.jsonl:1'):
            module.load(bad)
    bad.write_text('{\n')
    with pytest.raises(ValueError, match='bad.jsonl:1'):
        module.load(bad)


def test_ingest_failure_stops_and_reports_calls(monkeypatch, capsys):
    from canon import store
    from canon.models import Source
    module = script()
    memory = store.reset_store_for_tests()
    calls = []
    async def failing(req, scope):
        calls.append(req.source.title)
        assert req.source.id is None
        raise RuntimeError('offline failure')
    monkeypatch.setattr(module.core, 'ingest', failing)
    monkeypatch.setattr(module.llm, '_spent', {'2026-10-18': 7})
    async def scenario():
        await memory.put('sources', {'id': 'old', 'workspace': 'existing', 'title': 'Already'})
        rows = [Source(id='foreign-id', kind='wiki', title=title, author='Mei Tan',
                       ts='2026-01-01T00:00:00Z', text='Fixture') for title in ['First', 'Second']]
        with pytest.raises(RuntimeError, match='offline failure'):
            await module.add_sources(rows, 'existing')
    asyncio.run(scenario())
    assert calls == ['First']
    assert 'process total): 7' in capsys.readouterr().out
