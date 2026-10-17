"""Medium-specific context that does not change benchmark evidence."""
SLACK_CONTEXT = {
'Kestrel signing-key notice': ('Is the portal showing an expired key, or did our replay command use the wrong one?', 'The portal still lists it. Their support person says visibility and validity are different things now.', 'I checked a fresh request and the same event replayed later. Different validation results, same event body.'),
'Route Lens March cost trace': ('The orange span looks like a retry. Is that why the invoice grew?', 'No, expand the second span. It is the customs-risk pass, not another attempt at the first request.', 'I counted distinct shipments before dividing the bill. The extra work is not a duplicate-ingest artifact.'),
'Rural pilot visit notes': ('Did the phone fail to upload, or was there just no signal at the end of shift?', 'No connected depot on that leg. The ferry route is longer than the city route we interviewed first.', 'The badge stayed grey across shifts. I have the visit notes and the driver schedule beside each other now.'),
'Fleet peak after eastern rollout': ('Is that 3400 before or after retry normalization? The raw counter was noisy last week.', 'After. I checked the normalized stream, and the shift schedule says this is ordinary eastern-depot traffic.', 'The peak does not settle back to the pilot baseline after ten minutes. I included the whole interval, not just the tallest bar.'),
'Route Lens low-volume trace': ('Are we including browser wait in that p95? The service chart and the UI chart differ.', 'This is the inference worker trace only. The gap between batches is where the worker goes away.', 'I have not swapped the serving model. I am flagging that the warm-pool estimate no longer describes this tenant.'),
'Backup footprint proposal': ('Is this the recovery setup from the shared restore drill? That one was much easier to operate.', 'Yes, but I cannot tell from the drawing whether the primary region and recovery region are the same.', 'Primary stays where it is. I am trying to reuse the recovery wiring rather than maintain another special case.'),
'Osaka demo preparation thread': ('The fake route still goes straight through the harbour. Can we make it look like the cross-dock visit?', 'The customer clip has the hop we want, but the map also makes the depot and phone suffix readable.', 'I hid the big name field. The remaining columns were useful for the map so I left them in the draft import.'),
'September landing page draft': ('The range takes three lines on mobile. Is there a shorter headline in the draft?', 'Shorter reads well, but the screenshot and the confidence chart are telling slightly different stories now.', 'This is the headline version I have in the design file. Please comment on the actual narrow-screen mock-up too.'),
'First week, same kettle': ('Does the kettle always make that sound or is it about to launch?', 'It has sounded like that since Monday. Facilities says it is the lid.', 'Nine new starters and we are onboarding the kettle too. Spare mugs are by reception.'),
'Scanner test bench': ('Is that the scanner disconnect from the QA video?', 'It drops exactly when the cable moves. I can reproduce without the app open.', 'Please leave the paper tag on the cable. I do not want someone debugging a websocket for another hour.'),
'Rain on the office link': ('Anyone else losing the dev tunnel every few minutes?', 'Tokyo synthetic probe is steady. My home connection is fine too.', 'The office Wi-Fi graph lines up with the storm. This does not look like a dispatch incident.'),
'Kestrel portal password reset': ('The portal reset email has not arrived. Connector token expired too?', 'Connector graph is green. This is the human login mail queue.', 'Their banner says mail is delayed. I will stop pressing resend before I fill my inbox tomorrow.'),
'May holiday overlaps': ('Is the office closed tomorrow or just half the calendars?', 'Different holidays in Singapore and Tokyo. The overlays are the useful bit.', 'Meeting room calendar looks empty but I checked the customer call. That one is still on.'),
'Map colour printout': ('Did the lane colours change? My printout has two identical lines.', 'Printer problem. The on-screen legend is distinct.', 'I left a grayscale copy on the desk. The labels need to carry some of the difference for the workshop.'),
'Night queue handoff': ('Are either of those two tickets reporting missing shipments?', 'No. One browser zoom issue and one unreadable barcode photo.', 'Good, I will ask for the clearer photo and leave the event links alone.'),
'Expense receipt mystery': ('Is dinner-final-final the team meal receipt?', 'It is a taxi receipt. I admire the confidence of the filename.', 'Ah, mine. Reclassifying before Nur has to open it a fourth time.'),
'Notebook kernel queue': ('The chart is blank. Did the count drop to zero?', 'The cell has not run yet; Tomoko has the shared kernel.', 'I will paste the export once it finishes, with a timestamp this time.'),
'The spreadsheet with two Septembers': ('There are two September tabs. Did we bill twice?', 'One is an old export. Compare the export timestamp, not just the month label.', 'Found it. The ledger has one period. Renaming the old tab so the next person does not panic.'),
'Lunch walk route': ('Is the bridge open again? Last time we had to walk round the block.', 'Path is open, bridge still has barriers. Use the shaded way behind the office.', 'I am in after all-hands. Somebody remind me to bring my badge back this time.'),
'Notebook handover index': ('The oldest notebook errors on the current environment. Was it always broken?', 'It needs the old package lock. The exported results are there if you only need to read them.', 'Linh has the static copy too. Please do not spend your afternoon rebuilding my laptop setup.'),
'Slack search in two languages': ('I cannot find the Tokyo dispatch screenshot with the English tag.', 'They used the Japanese label in that thread. Try the term from the interview sheet.', 'There it is. I added both search terms to the note; same picture, different vocabulary.'),
'Support queue Friday wrap': ('Why are there two tickets for the same shipment?', 'Repeated email from the same supervisor. The two hub scans themselves are legitimate.', 'Merged the tickets and kept both scan links so we do not erase the movement history.'),
'Carrier clock skew sample': ('That arrival looks like it happened before departure. Is the sort wrong?', 'Device clock is six minutes slow. Receive time is on the next column.', 'The notebook has both now. This is one scanner sample, not evidence that every Kestrel clock is off.'),
'Design file permission hiccup': ('Daniel says the workshop file is read-only. Did we lose sharing access?', 'He followed the archived link. Current file opens from the research folder.', 'Found the editable one. I had bookmarked last month\'s screenshot review.'),
'Queue dashboard bookmark': ('Did the dead-letter panel disappear from the saved view?', 'No, it is just below the fold. My bookmark opens with the top row expanded.', 'Full-height screenshot attached. I spent too long looking for a deleted panel that was still there.'),
'Quarterly depot count': ('Finance has two fewer depots than the data sheet. Which one is wrong?', 'Training sites. Finance counts depots with completed shipments.', 'Both reconcile with the same filter. I put it in the title instead of another footnote.'),
'Workshop microphone check': ('Is that air conditioner louder than the interpreter?', 'On the room mic, yes. Headset clip from the afternoon is much better.', 'I corrected the speaker labels from Siti\'s notes. The transcript was attributing the room noise to Daniel.'),
'Notebook thumbnail stale': ('Search still shows the red line. I thought the rerun was green?', 'Open the notebook itself. The thumbnail is from the earlier export.', 'Caption has the export timestamp now. Numbers in the actual notebook are the completed run.'),
'Preview tenant invitation': ('Sakura invite bounced again. Wrong account domain?', 'Trailing space in the address, apparently. Miki resent the list.', 'Corrected invitation is in the training roster now. No need to make a second preview tenant.'),
'Manifest field glossary': ('The example says depot code, schema says facility_code. Are those separate fields?', 'Same field. Documentation label drifted from the fixture.', 'Fixture validates. Thao has the wording mismatch on the docs board.'),
'Customer call background noise': ('Was that an app alert halfway through the customer call?', 'Reversing forklift. Daniel was beside the loading bay.', 'Use the written notes for that section. The headset picked up every beep except the useful sentence.'),
'End of year desk plant update': ('Where did the plant from Tomoko\'s desk go?', 'Window ledge. The old desk has become a scanner bench.', 'I am watering it, not debugging it. Please do not put a barcode sticker on the pot.'),
'Route trace colours': ('Orange means inference in the slide, right?', 'Queue time. The legend was cropped out of the slide export.', 'Full trace has the legend below it. I linked that version rather than redrawing the chart.'),
'Support handover dry run': ('The recording goes blank for a moment. Failed capture?', 'Browser permission dialog outside the recorded tab.', 'Added a caption. Siti got through the checklist using the fabricated tenant after closing it.'),
'Incident graph export': ('PDF starts at 15:00 and the query starts at 07:00. Are we missing eight hours?', 'Same time in SGT and UTC. Footer had no timezone in the first export.', 'Fixed the footer. Keeping the raw query link with the graph so the interval is clear.'),
'Price workbook comment': ('Is yellow another Route Lens tier? Arjun saw it in a screenshot.', 'Reviewer comment, not a price tier. The crop hid the legend.', 'I sent the full sheet. Tiny yellow cells apparently carry a lot of narrative weight.'),
'Depot visit photo upload': ('Why are there four copies of the same depot photo?', 'Phone retried on the ferry Wi-Fi. Album has deduplicated them now.', 'No addresses visible in these shots. The wide photo is the one showing the tablet stand.'),
'Farewell card logistics': ('Has Anika seen the card on the scanner bench?', 'No, Yuki has it now. Someone nearly stuck a test barcode on it.', 'I will sign after lunch. Please leave a little space for the night shift.'),
'Demo map tile attribution': ('Map credits cover the zoom control on the projector. Does anyone see it on laptop?', 'Only at the projector resolution. Desktop capture looks normal.', 'Added the actual resolution to the bug. Otherwise the screenshot makes it look like a random overlay.'),
'Warehouse tablet stand': ('Is the camera broken on the demo tablet?', 'Stand covers it in portrait. Rotate it and the camera is clear.', 'Hardware ticket has a pencil arrow in the photo. Not another browser permission issue this time.'),
'Translation review names': ('Which Tan is the vendor reviewer? There are two in this sheet.', 'Neither is Mei, who is our engineering manager. Vendor has two different people with that surname.', 'Company names are beside the reviewer names now. That should save the next round of mistaken pings.'),
'Rehearsal coffee stain': ('Is that circle around the incident timeline a review annotation?', 'Coffee ring on the printed copy. Digital version is clean.', 'Siti has the version with pronunciation notes. That one is intentionally annotated, unlike my coffee art.'),
}

WIKI_TAILS = {
'Release process': '''## Checklist
1. Tag the build and put its SHA on the release ticket.
2. Open dispatch queue age beside the smoke run.
3. Paste the rollback reference before the release buddy joins.

## Training notes
The video starts with staging because the tenant picker is easier to see there. The production checklist is in chapter two. The screenshot still has the old sidebar icon; the queue link works.

## Page comments
Haruto Sato: The rollback SHA in the example is too small to read.
Thao Tran: Linked the original capture under the image. The PDF version still looks fuzzy.
Mei Tan: Found it, thanks. I am using this link for the buddy walkthrough.''',
'Route Lens sales FAQ': '''## Procurement pack
- Security overview: attach the full PDF, not the cover image.
- Invoice entity: ask Nur when the customer has multiple regions.
- Pilot access: free while the design-partner preview runs.

## Common questions
The workspace is the commercial unit here. Depot count appears in the demo story but is not another price row. The brochure mock-up still has a placeholder for a customer quote.

## Page comments
Arjun Desai: Can I paste the fee paragraph into the renewal template?
Farah Khan: Yes, but include the workspace unit. Last crop made it look like a per-seat number.
Nur Aziz: The invoice entity depends on the account. Please keep that question separate.''',
'Route Lens launch brief': '''## Deliverables
- Two-minute warehouse walkthrough, captions in the review folder.
- Customer quote placeholder, pending final attribution.
- Translated page strings, spreadsheet tab called Launch Copy.

## Rehearsal notes
Start with the late truck, then show the map. The admin setup is useful later. The interpreter needs a pause on the cross-dock view; the current animation runs ahead of the narration.

## Page comments
Daniel Lim: The loading-bay photo is facing inbound even though the truck points out.
Farah Khan: Fixed the caption. Do not use the older thumbnail in the recap.
Yuki Mori: The printed map has the same stop names as the walkthrough now.''',
'Carrier webhook recovery': '''## Find the event
Search by event ID, then compare the original carrier timestamp with receive time. The queue clock is UTC. A screenshot taken in Singapore can look eight hours out without any missing events.

## Before replay
- Check partner credential expiry.
- Read the event count in the selection preview.
- Keep the ticket link with the command output.

## Page comments
Ravi Perera: Dead-letter sounds like deleted to new starters. Could we clarify that the event is still inspectable?
Chen Wei: Added that to the training notes. The screenshot at the top still uses the old panel title.
Kavya Iyer: The fabricated fixture opens in the notebook, confirmed.''',
'Support access handbook': '''## Request walkthrough
Open the ticket before the access dialog. The reference belongs in the request field, not only in a chat reply. The training video uses an invented tenant.

## Shift handoff
Write down which screenshot the customer is looking at. Cropped images often hide the tenant selector or browser clock. The night queue examples are in the support training folder.

## Page comments
Siti Nuraini: The video skips past the ticket field too quickly.
Ravi Perera: Added a still image below it. My browser is zoomed in, which is why the dialog looks larger.
Thao Tran: The PDF export crops the bottom button. Editable source is linked beside the video.''',
'Audit retention FAQ': '''## Search examples
Use actor ID when the account display name changes. Use resource ID when a customer has renamed the depot. The viewer does not show shipment payload bodies.

## Closed tenants
The cancelled-account example is in the second screenshot. A closed account can still have an audit trail, which is why this example appears separately from payload deletion.

## Page comments
Nur Aziz: The grey row is hard to see in the printout.
Thao Tran: I added a border in the exported image, not a different status colour.
Jiwon Park: Please keep the payload note with this page when linking from support. They are different record types.''',
'Kestrel integration setup': '''## First connection
Start from the supplied cursor. The staging hostname has a separate certificate, so a browser warning there does not prove production is down.

## Response headers
The partner gateways vary the case of the cursor header. The captured fixture has invented event identifiers. Compare the complete header name rather than a cropped screenshot of its first characters.

## Page comments
Pranav Menon: The portal screenshot calls this the standard plan. Is that our agreement?
Chen Wei: The agreement PDF is linked beside it. The screenshot just shows where to find the settings.
Linh Nguyen: Aggregate request graphs combine tenants. The notebook can split them.''',
'Booking retry cookbook': '''## Client sequence
1. Persist a token before the first request.
2. Reuse it when a response times out.
3. Keep the tenant context with the stored token.

## Worked example
The demo phone loses connectivity after the server accepts a booking. The driver sees a spinner and tries again. The second call needs to identify the same operation, even though the first response never reached the device.

## Page comments
Budi Santoso: The old screenshot creates the token inside the click handler. Is that deliberate?
Thao Tran: No, the snippet below it is the corrected example. Image replacement is on my list.
Kavya Iyer: I have the delayed retry fixture alongside the immediate double-tap one.''',
}
