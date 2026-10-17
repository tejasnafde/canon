# Clip 07: Discord, record the real thing too

`clip-07-discord.mp4` is an honest illustration of the flow (message, Canon sync, conflict, reply).
It is labelled as an illustration. Judges trust a real screen recording more, so please also record
the live exchange yourself and cut between the two.

## Steps

1. Join the demo server: https://discord.gg/HwSgjmcgF5 (Northwind Labs).
2. Start a screen recording of the Discord window (1920x1080 if you can, dark theme).
3. In `#engineering`, post this message exactly:

   ```
   I have scheduled the production dispatch image refresh for every Friday at 15:00 SGT. It runs unattended, including configuration changes. I used the slot from the Release process wiki.
   ```

4. Wait. The sync runs every minute, so the Canon bot replies to your message within one to two
   minutes. The reply starts with "This goes against: There will be no production deployments on
   Fridays..." and links to the decision on canon.tn07.dev.
5. Keep the recording running until the reply appears, then stop. In the edit, cut the wait.

## If the bot does not reply

- The model output varies. If Canon classes the message as an update instead of a contradiction, it
  raises an alert but may not reply in the channel. Post it once more in a new thread, or show the
  alert on https://canon.tn07.dev/decisions instead.
- Each user has a daily limit of 20 synced messages. Do not post the message many times.
- Use the illustration clip for this scene if the live reply does not come.
