# Recording and editing guide: the Canon demo video

For a first-time editor on a Mac. You record the narration in your own voice, record one Discord
moment, and cut the silent clips into a 3:46 video in iMovie. Budget: about 2 hours.

You need:

- The script: `docs/video-script.md` (scene by scene, with IN and OUT times and narration).
- The clips: `~/Desktop/projects/google-hackathon/wt/w23-video/video/clips/` (1920x1080, silent).
- Headphones, and a USB mic or wired earphones with a mic. The MacBook mic also works if the room is quiet.

Order of work: A (narration), B (Discord), C (edit), D (checklist), then upload.
The last page (E) is a one-page teleprompter. Print it or open it on a phone or iPad.

---

## A. Record the narration (clear and loud)

### A1. Room and mic

1. Pick the quietest small room you have. Soft things help: a bedroom with a bed, curtains and a carpet is better than a kitchen.
2. Turn off fans, the AC and music. Close the window. Put your phone on silent.
3. Sit, do not stand. Keep the laptop on a table, not on your lap (the fan noise and the keyboard thumps go into the mic).
4. Mic distance:
   - USB mic or earphone mic: about one hand width (10 to 15 cm) from your mouth, a little to the side, so your breath does not hit it.
   - MacBook built-in mic: sit square to the screen, about 40 cm away, and speak a bit louder than normal.
5. Set the input level: **System Settings > Sound > Input**, pick your mic, and speak a normal sentence. The level bar should reach about three quarters. Move the "Input volume" slider until it does.
6. Have water near you. Do a 10 second test recording, then listen back on headphones. Fix any hum or echo now, not after 11 takes.

### A2. Record one take per scene

Record each scene as a **separate file**. One long take is much harder to line up with the clips.

Use **Voice Memos** (easiest) or **QuickTime Player**:

- Voice Memos: press the red button, read the scene, press stop. Rename the memo `scene-01`, `scene-02` and so on.
  To get the file, drag the memo from the list onto the Desktop (it saves as `.m4a`).
  If your Voice Memos has the "Enhance recording" button (the magic wand in the edit view), turn it on. It removes room noise.
- QuickTime Player: **File > New Audio Recording**. Click the small arrow next to the red button and pick your mic and **Quality: Maximum**.
  Record, then **File > Save** as `scene-01.m4a` and so on.

How to read:

1. Open `docs/video-script.md` and play that scene's clip segments once, so you know the pace.
2. Leave one second of silence, then read the scene's narration. Leave one second of silence at the end.
3. Speak slowly. About 130 words per minute feels slow to you and sounds normal to a listener.
4. Stress the bold words. Smile a little on the first line of scenes 1 and 4: it lifts the voice.
5. If you trip on a word, do not stop. Pause, and say the whole sentence again. Cut the bad one in the edit.
6. Do two takes of scene 4 (the agent scene). It matters most for technical merit.
7. Scene 6 has two versions (live Discord or fallback). Record the one you will use, after part B.

Timing target per scene (from the script): 1 = 18 s, 2 = 20 s, 3 = 20 s, 4 = 38 s, 5 = 22 s, 6 = 20 s,
7 = 21 s, 8 = 20 s, 9 = 20 s, 10 = 18 s, 11 = 9 s. A take may be 1 or 2 seconds longer; the edit can hold a frame.

---

## B. Record the live Discord moment (scene 6)

Do this before you edit. If the bot does not reply, use the fallback clip `clip-07-discord.mp4` and move on.

1. Warm up Canon: open https://canon.tn07.dev in a browser and wait until the counts show on Home. Cloud Run scales to zero, so the first request is slow.
2. Turn on **Do Not Disturb** (Control Centre > Focus), so no notification or message preview appears in the recording.
3. Open Discord (the app or discord.com in a browser) and join the demo server: https://discord.gg/HwSgjmcgF5 (Northwind Labs). Use dark theme.
4. Open the **#engineering** channel. Make the window large, roughly 16:9. Check that no private DM, other server name or email address is visible. If one is, record only part of the screen (step 6).
5. Copy this message, exactly, but do not send it yet:

   ```
   I have scheduled the production dispatch image refresh for every Friday at 15:00 SGT. It runs unattended, including configuration changes. I used the slot from the Release process wiki.
   ```

6. Press **Cmd+Shift+5**. In the bar at the bottom:
   - Choose **Record Entire Screen**, or **Record Selected Portion** and drag a box around the Discord channel area.
   - Click **Options**: Microphone **None** (the narration comes from part A), and turn on **Show Mouse Clicks**.
   - Click **Record**.
7. Wait 2 seconds. Click the message box, paste the message (Cmd+V), wait 1 second, and press **Return**.
8. Do not touch anything. Wait. Canon's sync runs every minute, so the bot replies in **one to two minutes**.
   The reply appears under your message and starts with **"This goes against: There will be no production deployments on Fridays..."** with a link to canon.tn07.dev.
9. When the reply is fully visible, wait 5 more seconds, then stop the recording: click the stop button in the menu bar (or press **Cmd+Ctrl+Esc**).
   The file lands on the Desktop as `Screen Recording <date>.mov`.

If the bot does not reply within 3 minutes:

- The model can class the message as an update, not a conflict. Then Canon raises an alert but may not reply in the channel.
  Post the message **once** more in a new thread, and record again.
- Each user has a daily limit of 20 synced messages. Do not post the message many times.
- Still nothing: use the fallback (`clip-07-discord.mp4`) and its narration in the script. That is fine. It is labelled as an illustration.

---

## C. Edit in iMovie

### C1. Fast path: let a script cut the clips (recommended)

This cuts all 21 segments with the exact IN and OUT times, the 2x speed-up and the freeze frames, into
numbered files. Then iMovie is only "drag in order and add the voice". Open Terminal and paste:

```sh
cat > /tmp/canon-cut.sh <<'EOF'
#!/bin/sh
set -e
SRC=${SRC:-$HOME/Desktop/projects/google-hackathon/wt/w23-video/video/clips}
OUT=${OUT:-$HOME/Desktop/canon-cuts}
FF=/opt/homebrew/bin/ffmpeg
mkdir -p "$OUT"
cut() { # name clip in out [extra video filter]
  vf="setpts=PTS-STARTPTS${5:+,$5}"
  $FF -v error -y -ss "$3" -to "$4" -i "$SRC/$2.mp4" -vf "$vf" -an \
      -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 "$OUT/$1.mp4"
}
cut 01a clip-02-home 0:00 0:11
cut 01b clip-02-home 0:13 0:20
cut 02  clip-03-new-hire 0:00 0:20
cut 03a clip-04-catch-up 0:00 0:10
cut 03b clip-04-catch-up 0:19 0:22
cut 03c clip-04-catch-up 0:24 0:25
cut 03d clip-04-catch-up 0:29 0:35
cut 04a clip-05-agent 0:00 0:10
cut 04b clip-05b-agent-terminal 0:00 0:18.06 "tpad=stop_mode=clone:stop_duration=1"
cut 04c clip-05-agent 0:32 0:40 "setpts=0.5*PTS"
cut 04d clip-05-agent 0:40 0:45
cut 05  clip-06-paste 0:05 0:27
cut 06  clip-07-discord 0:00 0:18.4 "tpad=stop_mode=clone:stop_duration=1.6"
cut 07a clip-08-ask 0:03 0:19
cut 07b clip-08-ask 0:25 0:30
cut 08a clip-09-decisions 0:00 0:04
cut 08b clip-09-decisions 0:08 0:18
cut 08c clip-09-decisions 0:26 0:32
cut 09  clip-10-architecture 0:00 0:15 "tpad=stop_mode=clone:stop_duration=5"
cut 10  clip-11-benchmark 0:00 0:18
cut 11  clip-12-close 0:00 0:06 "tpad=stop_mode=clone:stop_duration=3"
echo "Done: $(ls "$OUT"/*.mp4 | wc -l | tr -d ' ') files in $OUT"
EOF
sh /tmp/canon-cut.sh
```

It takes about a minute and writes `~/Desktop/canon-cuts/01a.mp4` to `11.mp4`. Total length is 3:46.1 (measured).
`06.mp4` is the Discord fallback. If you use your live recording, leave `06.mp4` out and trim your
recording in iMovie instead (step C3.4).

Then skip to C3, and skip the trimming steps (C3.3) for every clip except your Discord recording.

### C2. Start the project

1. Open **iMovie**. Click **Create New > Movie** (or **File > New Movie**).
2. **iMovie > Settings** (or Preferences): if there is a box "Display time as HH:MM:SS:frames", tick it. It makes the IN and OUT times easy to hit.
3. **File > Import Media** (Cmd+I). Select either:
   - the 21 files in `~/Desktop/canon-cuts/` (fast path), or
   - the clips in `wt/w23-video/video/clips/` (manual path),
   plus your Discord recording and all `scene-XX.m4a` narration files. Click **Import Selected**.

### C3. Build the video track

1. **Fast path**: in the media browser, sort by name, select `01a` to `11` (skip `06` if you have a live Discord recording) and drag them all to the timeline at once. They land in order. Done with the picture, except Discord.
2. **Manual path**: for each segment in the script, in order:
   1. Click the clip in the media browser. Move the pointer over it to find the IN time; the viewer shows the frame.
   2. Click and drag across the clip from IN to OUT. A yellow box marks the range.
   3. Press **E** to add that range to the end of the timeline.
   4. To fix a cut later: select the clip in the timeline, drag its left or right edge. Or put the playhead on the frame and press **Cmd+B** (Split Clip), then select the unwanted piece and press **Delete**.
3. **Speed up** (manual path only, segment 4c, `clip-05-agent` 00:32 to 00:40): select it in the timeline, click the **speedometer** button above the viewer, set **Speed: Fast** and **2x**. Untick "Preserve pitch" (there is no audio).
4. **Discord live recording** (scene 6, between `05` and `07a`):
   1. Drag the recording into the timeline after the scene 5 clip.
   2. Split it (Cmd+B) just before you click into the message box, and delete the start.
   3. Split it again 1 second after the message appears, and again 1 second before the bot reply appears. Delete the middle piece (the wait).
   4. Trim the end so the reply is held about 8 seconds. Aim for 20 s in total for the scene.
   5. Optional: speed up the wait instead of deleting it. Select the wait piece, speedometer, **Custom**, 2000%. A 1 minute wait becomes 3 seconds.
   6. Optional label over the cut: click **Titles** at the top, drag **Lower Third** onto the clip right after the cut, type "About a minute later", and set its length to 2 s.
   7. If the recording is not 16:9, iMovie fits it with black bars. That is fine. To fill the frame, select it, click the **crop** button above the viewer, choose **Fill**.
5. **Freeze frames** (manual path only): segments 4b (1 s), 6 fallback (2 s), 9 (5 s) and 11 (3 s) hold their last frame.
   Put the playhead on the last frame of the clip and choose **Modify > Add Freeze Frame** (Option+F). Drag the freeze clip edge to the length you need.
6. No transitions. Straight cuts look clean and keep the time. iMovie may add cross dissolves when you add clips: if a small two-triangle icon appears between clips, click it and press Delete.
   Also check **File > Project Settings**: untick "Automatic content" and keep the theme to None.
7. Play the whole video once with no sound. Check that no clip has a black gap and nothing repeats.

### C4. Add the narration

1. Drag `scene-01.m4a` from the media browser to the timeline, **under** the first clip. It becomes a green audio strip attached to that clip.
2. Line it up: the first words start at the time given by the `[+0s]` cue. Drag the strip left or right.
3. Repeat for every scene, under that scene's first clip.
4. Cut bad takes and long pauses: put the playhead in the strip, **Cmd+B**, select the bad piece, **Delete**, then drag the rest back into place.
5. If a scene's narration is longer than its picture, either speak it again faster, or add a freeze frame (C3.5) of 1 or 2 seconds to the last clip of that scene. Keep the total under 3:55.

### C5. Make the audio loud and even

1. Select all narration strips (click one, then Cmd+A selects all clips; Shift-click to pick only audio strips).
2. Click the **Volume** button (the speaker icon) above the viewer and click **Auto**. iMovie raises quiet clips.
3. Click the **Noise Reduction and Equalizer** button (the bars icon). Tick **Reduce background noise** and set it to about 20 to 30%. More than that makes the voice sound underwater. Set **Equalizer: Voice Enhance**.
4. Look at the waveforms. Peaks should be tall but not **red** at the top. Red means clipping (distortion): lower that strip's volume a little.
5. Listen to scenes 1, 4 and 11 on the laptop speakers at half volume. Every word must be clear.

### C6. Export at 1080p

1. **File > Share > File...**
2. Resolution **1080p**, Quality **High**, Compress **Better Quality**, Format **Video and Audio**.
3. Name it `canon-demo.mp4` and save it to the Desktop.
4. Open the exported file in QuickTime and watch it end to end.

### CapCut alternative (two lines)

Import the same files (or `~/Desktop/canon-cuts`) into a new 1920x1080 CapCut project, drop them on the main track in order, and put the `scene-XX.m4a` takes on the audio track under them.
Use **Split** to trim, **Speed > Normal 2x** for segment 4c, **Freeze** for held frames, **Audio > Normalize loudness** on the voice, then **Export** at 1080p, 30 fps.

---

## D. Final checklist

Tick every line before you upload.

- [ ] Length is between **3:00 and 4:00**. Target 3:46. Over 4:00 is a penalty.
- [ ] The video **opens on the live product** (the Home page), not on a title card.
- [ ] Every word is audible on the **laptop speakers at half volume**. No music under the voice.
- [ ] No clipping (red waveform peaks) and no long silence (over 2 s) anywhere.
- [ ] **No secrets on screen**: no API keys, tokens, `.secrets` paths, email inbox, notification popups, private DMs or other Discord servers. Pause on every Discord frame to check.
- [ ] **URLs are visible**: canon.tn07.dev and github.com/tejasnafde/canon on the close card.
- [ ] The scene 6 version matches its narration (live: "I post"; fallback: "Someone posts").
- [ ] Exported at 1080p, plays in QuickTime from start to end.
- [ ] Upload to YouTube: **Create > Upload video**, title "Canon: the shared memory of a company (AI Builder Cup 2026)". Set **Visibility: Unlisted**. Not Private: judges cannot open a Private video.
- [ ] Wait for YouTube to finish HD processing (the HD badge appears; can take 10 to 20 minutes).
- [ ] Open the link in a **private window** (Safari: Cmd+Shift+N) while logged out. It must play, in 1080p, with sound.
- [ ] Paste that link in the submission form. Reminder: the prototype link in the form is the `web.app` or `run.app` URL, not canon.tn07.dev.

---

## E. Teleprompter (narration only)

Read one block per take. Pause 1 second before and after each block. **Bold** = stress.

**1. Home**
This is Canon, live on Google Cloud. Companies decide things every day, then forget them.
Canon read two years of a made-up company, Northwind Labs. **Three hundred eighty** items. **Three hundred forty-five** official decisions.
And **twenty-seven** documents that are now wrong.

**2. New hire**
Day one for a new hire. Canon **warns** first: this handbook page is out of date.
Then the five things that will get you in trouble, each with the reason behind it. Who to ask, by topic. And who has left, with their decisions kept.

**3. Catch-up**
Back from three months away? Pick your role. An engineer gets a short summary, and a to-do list ranked by **urgency**.
Each score says why.
Switch to **Sales**, and it's discounts, contract limits and pricing. Same record, a view for every role.

**4. Agent**
Now the part nobody else does. AI coding agents ship code, but they never read the incident review. So they ask Canon **first**.
This is a **real MCP call** to Canon. The developer asks for a Friday deploy cron.
The agent calls check intent.
Canon says **block**: no production deploys on Fridays, scheduled jobs included. Owner Mei Tan, from the incident review. About **one second**.
Try it on the page yourself. Same request, same block, live. Claude Code or Codex connect in **one line**.

**5. Paste**
Paste a new message: Pranav schedules a **Friday** job, using a slot from the wiki.
Gemini pulls out the decision, and Canon checks every quote **word for word**.
It goes against the Friday ban. Both quotes, side by side. And the real cause: the Release process wiki is **still out of date**.

**6. Discord (live)**
Canon also listens **live**, in a public Discord server. I post the same Friday plan in engineering.
A sync on Cloud Run reads new messages every minute.
About a minute later, Canon replies in the thread, with the rule it breaks, and a link.

**6. Discord (fallback)**
Canon also listens **live**, in a public Discord server. Someone posts the same Friday plan in engineering.
A sync on Cloud Run reads new messages every minute. It finds the conflict.
Canon replies in the thread, with the rule and a link.

**7. Ask why**
Ask why. Why don't we deploy on Fridays?
A **grounded** answer in about a second, with the source quote, and the timeline of how the rule changed.
And when the record has no answer, Canon says: **I do not know**. No guessing.

**8. Decisions and people**
Every decision Canon found, with its owner, date and status.
Open the Friday ban. Who made it, why, and the timeline. And what **still breaks it**: a wiki page that gives the old rule.
The org chart shows who left, and who took over.

**9. Architecture**
Under the hood, **one Cloud Run** service: FastAPI, an MCP server, and an ADK agent over A to A.
**Gemini** Flash-Lite on Vertex AI extracts and judges, with structured output. **Firestore** holds the record, with vector search.
**Firebase Hosting** serves the app.

**10. Benchmark**
Does it work? We planted known decisions and conflicts, then measured.
**Eighty-two** of eighty-two decisions found. **Thirty-five** of thirty-nine changes caught. All five unanswerable questions refused.
Typical answer: one point two seconds. No decision stored twice.

**11. Close**
Canon. One memory, for your people **and** your agents.
Try it, and read the code, at the links on screen.
