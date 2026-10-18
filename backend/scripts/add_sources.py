"""Append JSONL sources to an existing workspace, skipping exact existing titles.

Run from backend: uv run python scripts/add_sources.py FILE --workspace acme4
This makes paid Gemini calls. Only the lead should run it against Firestore.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canon import core, llm  # noqa: E402
from canon.models import IngestRequest, Source  # noqa: E402
from canon.store import get_store  # noqa: E402


def load(path: Path) -> list[Source]:
    """Parse the entire input before the first write or Gemini call."""
    sources = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            source = Source.model_validate(json.loads(line))
            if not source.title.strip():
                raise ValueError('source title must not be blank')
            if source.ts.tzinfo is None:
                raise ValueError('source timestamp must include a timezone')
            sources.append(source)
        except ValueError as exc:
            raise ValueError(f'{path}:{number}: {exc}') from exc
    return sorted(sources, key=lambda s: (s.ts, s.title))


async def add_sources(sources: list[Source], workspace: str) -> None:
    existing = await get_store().query('sources', [workspace])
    if not existing:
        raise ValueError(f'requires an existing workspace with sources: {workspace}')
    titles = {s['title'] for s in existing}
    print(f'{len(sources)} input sources; {len(titles)} titles already in {workspace}', flush=True)
    try:
        for i, source in enumerate(sources, 1):
            if source.title in titles:
                print(f'[{i}/{len(sources)}] skip {source.title}', flush=True)
                continue
            # Input ids must not overwrite a source belonging to another workspace.
            source = source.model_copy(update={'workspace': workspace, 'id': None})
            result = await core.ingest(IngestRequest(source=source, actor='human:add-sources'), [workspace])
            titles.add(source.title)
            print(f'[{i}/{len(sources)}] added {source.title}: '
                  f'{len(result.decisions)} decisions, {len(result.alerts)} alerts; '
                  f'Gemini generate calls: {sum(llm._spent.values())}', flush=True)
    finally:
        print(f'Gemini generate calls (process total): {sum(llm._spent.values())}; '
              f'by UTC day: {llm._spent}', flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    sources = load(args.file)
    await add_sources(sources, args.workspace)


if __name__ == '__main__':
    asyncio.run(main())
