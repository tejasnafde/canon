# Discord setup (one time)

Canon reads Discord by pull, not by gateway: a scheduler calls `POST /hooks/discord/sync`
every minute, and Cloud Run can scale to zero. Slash commands come in over HTTP interactions.

## 1. Application and bot

1. Open https://discord.com/developers/applications and create an application "Canon".
2. General Information: copy the **Application ID** and the **Public Key**.
3. Bot: reset and copy the **token**. Turn OFF "Public Bot" if only we invite it.
4. Bot > Privileged Gateway Intents: turn ON **Message Content Intent**.
   Without it the REST API returns empty `content` for other users' messages, and sync ingests nothing.
5. General Information > **Interactions Endpoint URL**:
   `https://canon.tn07.dev/discord/interactions`
   Discord sends a signed PING when you save. Save fails until the service has `DISCORD_PUBLIC_KEY`.

## 2. Invite the bot

Permissions integer `309237713920`:
View Channels (1024) + Send Messages (2048) + Read Message History (65536)
+ Create Public Threads (2^35) + Send Messages in Threads (2^38).

```
https://discord.com/oauth2/authorize?client_id=<APPLICATION_ID>&scope=bot+applications.commands&permissions=309237713920
```

Pick the server "Northwind Labs (Canon demo)". Right click the server > Copy Server ID
(turn on Developer Mode in Discord settings first) for `CANON_DISCORD_GUILD_ID`.

## 3. Register the slash command

```sh
cd backend
DISCORD_APPLICATION_ID=... DISCORD_BOT_TOKEN=... CANON_DISCORD_GUILD_ID=... uv run python scripts/register_discord.py
```

With a guild id the command appears at once; without it, global commands can take up to an hour.

## 4. Cloud Run env (secrets through `--set-secrets`, never plain env)

| Env | What |
|---|---|
| `DISCORD_PUBLIC_KEY` | Application public key (hex). Verifies interactions. |
| `CANON_DISCORD_BOT_TOKEN` | Bot token. Secret. |
| `CANON_SYNC_TOKEN` | Random string. Secret. The scheduler sends it as `X-Canon-Sync-Token`. |
| `CANON_DISCORD_GUILD_ID` | Server id. Sync discovers every text channel and active thread. |
| `CANON_DISCORD_CHANNELS` | Optional comma separated channel ids. Overrides discovery. |
| `CANON_DISCORD_DAILY_LIMIT` | Messages ingested per UTC day, default 200. Per user: 20. |
| `CANON_PUBLIC_URL` | Base for decision links in replies, e.g. `https://canon.tn07.dev`. |

## 5. Scheduler job

Every minute, `POST https://canon.tn07.dev/hooks/discord/sync` with header
`X-Canon-Sync-Token: <CANON_SYNC_TOKEN>`. Label it `app=canon`.

The first sync of a channel reads only its latest 50 messages. Cursors live in
Firestore `connector_state/discord-<channel id>`; delete a doc to re-read that channel.
