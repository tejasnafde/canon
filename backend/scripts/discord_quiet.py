"""Time the cheap path of a Discord sync against the real server, read-only: list channels and active threads,
read every cursor in one batch, and report which channels changed. Ingests nothing, writes nothing.

  CANON_DISCORD_BOT_TOKEN=... CANON_DISCORD_GUILD_ID=... GOOGLE_APPLICATION_CREDENTIALS=... \
    uv run python scripts/discord_quiet.py
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canon.connectors import discord_sync as ds, state  # noqa: E402


async def main():
    async def no_write(key, fields):  # read-only: do not move the archived-scan clock or any cursor
        pass
    state.merge = no_write
    client = ds.DiscordClient(os.environ["CANON_DISCORD_BOT_TOKEN"])
    real_get = state.get
    for run, archived in (("cold", False), ("warm", False), ("warm", True)):
        async def get(key, archived=archived):  # pretend the archived scan ran a minute ago, or never
            if key == "discord-archived-scan":
                return {} if archived else {"at": ds.store.now()}
            return await real_get(key)
        state.get = get
        t = time.perf_counter()
        chans = await ds.channels(client)
        cursors = await state.get_many([f"discord-{c['id']}" for c in chans])
        changed = [c.get("name") for c in chans
                   if not (cur := cursors.get(f"discord-{c['id']}", {}).get("last_id"))
                   or (c.get("last_message_id") and int(c["last_message_id"]) > int(cur))]
        print(f"{run}, {'with' if archived else 'without'} archived scan: {len(chans)} channels/threads, "
              f"{len(changed)} changed {changed}, {time.perf_counter() - t:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
