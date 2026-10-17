"""Authored discussion fragments and archive formatting for the synthetic company."""

# Questions and objections precede the retained, exact evidence. No new policy is
# inferred here: gold stays in build_corpus.py, including historical statements.
from meeting_details import DETAILS
from pr_excerpts import EXCERPTS
from source_context import SLACK_CONTEXT, WIKI_TAILS

DISCUSSIONS = {
'release-window': ('Why that slot? Tokyo support is usually winding down then.', 'The ticket histogram is quiet, but that is not the same thing as having a rollback buddy. Can we try it rather than call it permanent?', 'I checked the calendar with support. The first two are covered; the travel calendar is the bit we will have to keep checking.'),
'event-identity': ('Could we just use the parcel number? It would make the lookup much smaller.', 'No, look at the second hub scan. Same carton, different event. If we drop that, the customer sees it stuck at the first depot.', 'Right, I was looking at a retry of the same scan, not the arrival. Those need to be different fixture rows.'),
'webhook-retry': ('What about partners that are down for a weekend? Are we losing the scan?', 'Not losing it. Parking it where someone can see it. The retry graph looks healthy even when the password has been wrong since Monday.', 'OK, so support still has the original event to inspect. I had read dead-letter as delete, sorry.'),
'residency': ('The recovery copy has no live traffic. Does procurement really count that as processing?', 'I pulled the actual addendum rather than the sales summary. It says copies, not serving traffic. The summary omits that word.', 'That helps. I can separate the aggregate graph from the restore material in the diagram. They look like one arrow today.'),
'audit-retention': ('Does closing the tenant remove the audit row too? That is what my cleanup query does.', 'Then the person reviewing the cancellation cannot see who requested it. The record and the shipment body have different jobs.', 'I will split the fixture. The closed-account case is missing from the screenshot, which made this seem simpler than it is.'),
'eta-fallback': ('Can we wait a little longer for the good estimate? The old carrier number is pretty rough.', 'The spinner is already blocking the dispatcher from opening the next row. At least the carrier number has an age we can show.', 'Yes, provided the label does not quietly turn an old observation into a new prediction. I will send Yuki both screenshots.'),
'billing-unit': ('The event meter is already in the warehouse. Why build a second count?', 'Because Kestrel sends a scan at every handoff and Meridian does not. Same delivery, wildly different invoice.', 'I checked the cancelled examples with finance. The disagreement is the unit, not a rounding issue in the report.'),
'export-access': ('A supervisor can see the rows already. Why is downloading different?', 'One screen and a portable file containing the whole tenant are different exposure. The customer permissions sheet separates those roles.', 'Got it. We should show the reason beside the disabled control or support will keep getting the same ticket.'),
'sandbox-data': ('What if I blank the name and keep the route? The fake route is not convincing.', 'A phone suffix and a tiny depot can identify someone without a name. That is exactly what the demo map still shows.', 'Fair. The generator needs a cross-dock example, then. I can help Daniel draw one that actually looks like a depot day.'),
'cursor-order': ('The late scan belongs earlier on the timeline. Why would its cursor come last?', 'Because the client already paged past that earlier time. If the API inserts it behind that cursor, the client never sees it.', 'Ah, two orders. Display time and delivery order. I was trying to use one column for both. That explains the missing scan in my repro.'),
'sso-tier': ('Sales has an SSO line item in the draft. Is that a separate SKU now?', 'That was copied from a competitor grid, not our order form. Buyers already have enough security paperwork.', 'Thanks, I will remove the row. The draft screenshot is still in the enablement folder so someone may ask again.'),
'pager-coverage': ('If the backup is reachable by phone, does that count? They are doing a workshop.', 'Reachable does not mean able to pull a trace and run rollback. We found that out while the presenter had their screen shared.', 'I can cover the workshop slot if someone else drives the change. Please put actual names in the ticket, not just Platform.'),
'dr-drill': ('The backup dashboard is green. What would another drill tell us?', 'Last time we got metadata back but not the event index. A green copy job does not tell you whether dispatch can find a parcel.', 'That is a better demo case. Can we use a tenant fixture with a known missing scan so we can check the restored result?'),
'eta-disclaimer': ('The exact time reads much better in the narrow card. Can we keep that?', 'A warehouse supervisor used it to schedule a crew break. They read the number as a promise, regardless of the tiny tooltip.', 'OK. I can make the range fit without shrinking the font. The wording and the mock-up need to go together this time.'),
'support-access': ('Ravi is still finishing a ticket when the grant closes. Are we making night support harder?', 'The abandoned session was open after the ticket was done. We need a ticket trail even when the shift is busy.', 'Understood. I will try it during a real handoff before we rewrite the screenshots. The current walkthrough never shows expiry.'),
'connector-quota': ('Is the red graph telling us one tenant is over, or the whole integration?', 'The panel combines tenants. Tuning against that picture would make the quiet ones pay for the noisy one.', 'I found the signed capacity sheet. Let us use that number while Linh separates the series. Bigger batches are a different discussion.'),
'route-launch': ('Can Farah put a date in the customer deck? The empty box is getting awkward.', 'Only if the pilot condition travels with it. A preview account is not the same thing as a production commitment.', 'I will put the condition in speaker notes too. People screenshot the date and crop off everything below it, unfortunately.'),
'pricing-v1': ('Is that price based on the pilot bill or the steady-state estimate?', 'The workbook is one regional pass. The preview traffic is too small to use its invoice as a unit-cost estimate.', 'OK, I can use an estimate with prospects. We have not sent an annual Route Lens order form, so there is still time to clean the card.'),
'payload-logs': ('Without the JSON, how do I reproduce the parser failure?', 'Use the event reference to request the controlled capture. The application log is copied into too many debugging tabs.', 'I can make the exception useful with the event ID and error code. The current stringify was a shortcut from the first connector.'),
'mobile-offline': ('Do the phones really get back online every shift? That is the assumption in my sketch.', 'For the current depot interviews, yes. But keep that assumption visible. The ferry routes are not in this sample.', 'The pending badge is easy to miss on the shared phone. I will try a clearer age label without putting a customer name on the lock screen.'),
'replay-approval': ('The request says eight hundred parcels. That sounds small enough to run now.', 'There are several scans per parcel. Count the events in the selection before calling it a small replay.', 'Right, the UI summary and the job estimate use different units. I will paste the event count into the incident ticket.'),
'fx-lock': ('Why does the downloaded invoice differ from the PDF we emailed?', 'The download query reads the latest FX table. Both calculations are internally consistent, which is why the basic test passed.', 'So the invoice needs its month snapshot, not a fresh conversion. I will keep the two PDFs as the regression example.'),
'dashboard-freshness': ('The five-minute screenshot looks OK. Is the pilot busy enough to tell us anything?', 'It peaks well below the planned eastern rollout. I do not want the pilot chart to become an unlimited freshness claim.', 'Can we put the load condition next to the cache note? Otherwise I know which half of this conversation will get pasted into onboarding.'),
'deletion-window': ('Should the delete job remove the audit actor as well? The support article says all data.', 'That wording mixes the shipment body with the audit history. The customer request needs verification before the payload clock starts.', 'I will draw two lanes in the article. One giant delete arrow is tidy but it is the reason we are having this conversation.'),
'idempotency': ('Could another tenant reuse the same mobile token and hit our cached response?', 'Not if the lookup includes the tenant. A global token cache would leak a booking even if nobody guessed a shipment ID.', 'The weekend reconnect case is missing from my tests. I only had the immediate double tap. Adding a delayed retry as well.'),
'pilot-gate': ('The depot supervisor says the last week was much better. Can that count as acceptance?', 'Useful feedback, but it is not the same measurement. The notebook compares arrival, and the sales slide used departure.', 'Let us settle the denominator before we circulate another green chart. Otherwise every team will have a different passing week.'),
'schema-compat': ('All server pods are on the new writer. Can we remove the old reader branch?', 'The scanners are not server pods. Some warehouses refresh the client on a different calendar and we do not control that day.', 'Makes sense. I will keep an old manifest fixture in the test folder rather than rely on somebody remembering the compatibility case.'),
'incident-comms': ('Do we wait until we know the root cause? I do not want to send a wrong explanation.', 'Say what we know and what is affected. Last time a driver told Sakura before our support contact did.', 'I can draft an unknown-cause version now. It is much easier to send a short honest note than to undo a confident guess later.'),
'model-fallback': ('The regional result is better on the pilot. Can we make it the default?', 'The trace is from a warm pool. Low-volume tenants may have a very different tail, so that needs to stay an assumption.', 'Then keep the latency condition beside the choice. We have not evaluated an alternative serving path in this meeting.'),
'no-friday': ('Is this really about Friday, or just the missing rollback engineer? Banning a day feels blunt.', 'Both people on the ticket were technically reachable. One was on a flight and the other had a customer screen shared. That was not usable coverage.', 'Also the job that hurt us did not need a person pressing Deploy. If scheduled work gets a different rule, we have not fixed the gap.'),
'retry-six': ('Could we leave the queue retrying and just flag the old events?', 'The signature key is already invalid by then. The extra attempts only make the recovery graph look busy.', 'Right. The event still exists for inspection. This is the horizon, not a request to throw away the dead-letter backlog.'),
'support-thirty': ('Will Ravi\'s old handbook screenshot still match the access dialog?', 'No, that walkthrough shows the old duration. The proxy now renews an active grant without leaving a permanent session behind.', 'I can update the screenshot after testing renewal. Please do not tell the night shift they need a fresh browser every time.'),
'pricing-v2': ('Arjun has two proposals waiting. Can we keep the first price just for those?', 'Were they signed? A number in a draft email and an executed pilot order form are not the same commitment.', 'One is a signed pilot, Meridian is not. I will split the follow-up list rather than send both customers the same template.'),
'launch-june': ('Can we call April soft GA? The website date is already translated.', 'A name change does not create three passing weeks. We have one. Preview can continue, but the production SLA is the part customers care about.', 'OK, I need a replacement date for the notices and a clear sentence about preview. Please do not leave support to infer that from the roadmap.'),
'audit-two-years': ('Does the longer term apply only when the customer renews?', 'The new standard addendum removed the shorter tier. Keeping two defaults would leave support guessing from the invoice date.', 'And it is audit history, not permission to keep the shipment body. I will make that separation obvious in the storage estimate.'),
'quota-two': ('Two slots sounds slower. Are we going to miss the morning scan batch?', 'The page is larger in v3. Look at events returned per batch rather than just request count.', 'I will rerun the captured fixture with the larger page. Cursor persistence is the same, so this should not need a new recovery workflow.'),
'tokens-week': ('The rural pilot reconnects on the fourth day. Does the retry create another booking now?', 'That is the case we missed when the weekend was the longest gap. The store estimate includes the extra token rows.', 'Keep the tenant key though. A longer lifetime is no reason to change the isolation boundary.'),
'eta-fallback-new': ('Are we changing the model or just giving up sooner?', 'Just the wait. Kavya sees people leave the row before the old tail finishes. We still have a carrier observation to show.', 'Then the fallback age label stays. I will keep the slow-response fixture so we can see exactly which path the UI takes.'),
}

# These are local observations from interviews, not additional policy decisions.
MEETING_NOTES = {
'Depot shadowing notebook': ('She called the screen the board, not the dashboard. I nearly asked the wrong follow-up question.', 'Two browser windows, same tenant. One has arrivals and the other is halfway down a shipment list.', 'The lost scroll position seems small until she repeats it every five minutes. The recording shows her using a paper note to find her place.'),
'Analytics office hours': ('I thought the tile dropped two shipments.', 'The cancelled filter is different. The export includes them; the tile does not.', 'Nur can point to the two ledger entries. Let us label the screenshot before it goes into the weekly deck.'),
'QA pairing notes: barcodes': ('The scanner only fails when I point it straight at the glossy label.', 'Move the desk lamp. Yes, now it reads. That explains why the video from yesterday looked random.', 'The matte label works at that angle too. I wrote the lamp position on the test card so someone else can reproduce it.'),
'Demo rehearsal: Osaka': ('I lost the interpreter at the second animation.', 'The cross-dock hop goes past before the sentence finishes. Pause on the map and let the room catch up.', 'They asked about the late truck before any admin screens. The order in the rehearsal deck is backwards for that audience.'),
'Route Lens naming discussion': ('Did she say root or route in the interview?', 'Root, twice. The road icon helped but the name alone did not.', 'Farah has the clip. Let us listen before we spend another ten minutes voting on what we think we heard.'),
'Platform retro: useful screenshots': ('The cropped screenshot looked like missing data.', 'It hid the tenant selector and the browser clock. With those visible the query result makes sense.', 'Ravi found the original attachment in the ticket. We should keep that example beside the confusing crop for the next retro.'),
'Mobile upload interview': ('He handed the phone to the next driver with the upload still pending.', 'The grey badge was there, but nobody looked at it. They were looking for the big completed count.', 'The interview does not tell us whether the upload eventually finished. Siti is checking the recording, not guessing from the thumbnail.'),
'INC-042 customer impact audit': ('The first spreadsheet counted depot contacts, not affected depots.', 'There are duplicate contacts for the night and day supervisor. That is why the totals changed between screenshots.', 'Siti is checking the actual notices against the affected-tenant list. The rollback timing and the customer count are separate questions.'),
'Customer training office hours': ('Two people used one laptop. Attendance is not a license count.', 'The shortcut worked after the browser permission dialog closed. That dialog is off-screen in the recording.', 'Miki has the annotated keyboard sheet. The next question was about the scanner, not a request to change access.'),
'Platform handover inbox': ('The bookmark points at an archived notebook.', 'Mei has the current index. The old one is useful history, just not the starting page.', 'Chen found the replay example by its fixture name. Search by the customer nickname did not return it.'),
'September onboarding interviews': ('They knew where the runbooks were but not which one was current.', 'The first search hit was a screenshot from training. It had no visible review date.', 'Thao wrote down the exact search phrase. That is more useful than telling the new hire they should have searched harder.'),
'Warehouse glossary test': ('Consignment meant the whole load to one person and a single carton to another.', 'The diagram resolved it faster than the translated label. The arrows made the grouping clear.', 'Yuki has both marked-up printouts. The scanner operator circled a different noun from the supervisor, which is interesting.'),
}

PR_DIFFS = {
'PR 684: unattended dispatch refresh': ('deploy/dispatch.yml', '-  schedule: []\n+  schedule:\n+    - cron: "0 7 * * 5"\n+  environment: production', 'The Tuesday dry run looks fine. Is the schedule in UTC? The wiki screenshot is local time.', 'Yes, converted from the afternoon slot. I left it unattended so the image housekeeping does not block the team.'),
'PR 702: parser diagnostics': ('connectors/parser.py', '-    log.warning("parse failed", event_id=event.id)\n+    log.warning("parse failed", carrier_json=body)', 'Does this include the address object, or just the broken field?', 'It is the whole incoming object for now. The repro depends on a nested value and I could not tell which one from the exception.'),
'PR 731: warehouse download shortcut': ('web/ShipmentToolbar.tsx', '-  const canExport = role === "admin";\n+  const canExport = role === "admin" || role === "viewer";', 'The screenshot is clearer, but does the endpoint give this role the same permission?', 'I reused the endpoint and changed the button path. The happy-path test logs in as an admin, so it does not answer that yet.'),
}


def enrich_sources(sources, items):
    """Give each medium its own shape while retaining exact evidence substrings."""
    decisions = {i['evidence'][0]['source_title']: i['key'] for i in items if i['type'] == 'decision'}
    for index, row in enumerate(sources):
        original = row['text'].removeprefix(row['author'] + ': ').replace('\nNotes: the follow-up ticket is in the team board. Please add corrections in this thread rather than editing the customer deck.', '').replace('\nAttendees checked the migration ticket. The old handbook link is still circulating in onboarding.', '')
        author = row['author']
        # Only current employees participate in added dialogue. The original
        # source author retains their historical voice and date.
        others = [p for p in ('Mei Tan', 'Kavya Iyer', 'Thao Tran', 'Chen Wei', 'Siti Nuraini', 'Yuki Mori') if p != author]
        a, b, c = others[:3]
        key = decisions.get(row['title'])
        talk = DISCUSSIONS.get(key) or MEETING_NOTES.get(row['title']) or SLACK_CONTEXT.get(row['title'])
        if not talk:
            talk = ('Which attachment are you looking at? I have two tabs open and neither has the same caption.',
                    'The one in this thread, not the thumbnail in search. I tripped over that too.',
                    'Found it, thanks. Leaving my question here because the next person will probably follow the same old link.')
        q, objection, response = talk
        if row['title'] == 'INC-042 live dispatch thread':
            row['text'] = (
                '#platform-incidents | INC-042 | 6 March 2026, Singapore time\n'
                '15:14 SGT Haruto: dispatch ACK age is at 11 minutes after the 15:10 rollout. Opening INC-042.\n'
                '\nThread replies (12):\n'
                '15:15 Mei Tan: looking. is it one tenant or the whole dispatch queue?\n'
                '15:16 Haruto Sato: more than one, pulling the split now. The grouped flush graph stepped up at rollout.\n'
                '15:18 Chen Wei: partner status is green. I can check the token failures, but that does not explain every tenant.\n'
                '15:20 Siti Nuraini: Sakura supervisor called. Drivers are seeing the old acknowledgement state. What can I tell them?\n'
                '15:22 Mei: Pranav is on the flight to Pune. I am pulling Kavya out of the Sakura call.\n'
                '15:25 Kavya Iyer: here now. Need the rollback ref, I only have the smoke link in the ticket.\n'
                '15:28 Haruto Sato: pinned the previous SHA. The grouped flush can sit behind the tenant with an expired token.\n'
                '15:32 Mei Tan: rolling back that path. Chen please keep checking the queue, not just the deployment health.\n'
                '15:36 Siti Nuraini: first notice sent. Said dispatch acknowledgements delayed, cause still under investigation.\n'
                '15:45 Kavya Iyer: old per-tenant path is taking traffic. Watching the oldest outstanding ACK.\n'
                '15:57 Haruto: rollback complete, ACK age is falling. Customer impact was 47 minutes.\n'
                '16:06 Siti: the first customer notice went at 15:36. Please keep the thread quiet until I have the depot count.')
            continue
        if row['kind'] == 'slack':
            side, aside = [
                ('small tangent, the link preview is blank for me. Actual page opens fine.', 'same here lol. Search has the older thumbnail cached.'),
                ('I have the original open now. The tiny screenshot was not helping.', 'zooming in fixed it for me. My browser was still in projector mode.'),
                ('brb, somebody is knocking on the room door.', 'we are in the other room if that is the interview panel.'),
                ('typo in my earlier message, meant the second attachment. Leaving it so the replies make sense.', 'got it, I had both open and was reading the wrong caption.'),
                ('the printer copy is on my desk if anyone wants to compare.', 'paper version is easier to mark up, oddly. Will bring it back after lunch.'),
            ][index % 5]
            row['text'] = (f'# {row["title"]}\n09:28 {a}: {q}\n\nThread replies (8):\n'
                f'09:31 {b}: {objection}\n09:33 {author}: {response}\n'
                f'09:34 {c}: hang on, pulling up the original rather than the screenshot\n'
                f'09:38 {author}: {original}\n'
                f'09:41 {a}: +1, that answers the bit I was stuck on.\n'
                f'09:43 {b}: {side}\n'
                f'09:45 {c}: {aside}\n'
                f'09:49 {author}: thanks, leaving the context in-thread so it survives the next handoff.')
        elif row['kind'] == 'meeting':
            # Retain the complete original block, including the exact gold quote.
            detail, followup = DETAILS[row['title']]
            row['text'] = (f'{row["title"]}\nRecording transcript, lightly corrected. {row["ts"][:10]}.\n'
                f'00:00 {author}: OK, can everyone hear me? I have the notes open. Sorry, moving the call '
                'controls off the example. I want to get through this before we lose the room.\n'
                f'00:32 {a}: {q}\n'
                f'01:08 {b}: {objection}\n'
                f'01:47 {author}: {response}\n'
                f'02:19 {c}: Sorry, talking over you. Can we go back to the example? I am writing this down '
                'for the people who are not on the call. Which part did we actually check?\n'
                f'02:48 {author}: {detail}\n'
                f'04:06 {b}: {followup}\n'
                f'05:12 {author}: {original}\n'
                f'06:38 {a}: Right, that answers my question. Please leave the awkward example attached, '
                'not just the summary. I will forget which part confused me when I read this later.\n'
                f'07:03 {author}: Thanks. Corrections can go in the notes. The transcript sometimes puts '
                'all the crosstalk under my name, so check the speaker labels before quoting it.\n')
        elif row['kind'] == 'wiki':
            row['text'] = original + '\n\n' + WIKI_TAILS[row['title']] + '\n'
        elif row['kind'] == 'email':
            handle = author.lower().replace(' ', '.')
            greeting = 'Hi Miki,' if 'Sakura' in row['title'] else 'Hi Nandini,' if 'Meridian' in row['title'] else 'Hi team,'
            row['text'] = (f'From: {author} <{handle}@northwind.example>\nTo: Customer and project working group\n'
                f'Subject: {row["title"]}\nDate: {row["ts"][:10]}\n\n{greeting}\n\n{original}\n\n'
                'Sorry this took a little longer to send. The attachment preview looked different from the file '
                'when I opened it, so please use the document rather than the little image in the mail client. '
                'Happy to walk through it on the next call.\n\n'
                f'Thanks,\n{author}\nNorthwind Labs\n\n'
                f'On the earlier thread, {a} wrote:\n> I have the working copy open. Please keep replies in this '
                'thread so the depot team can find the attachments without another forward.\n')
        elif row['kind'] == 'pr':
            path, diff, review, reply = PR_DIFFS.get(row['title'], (
                'web/components/ShipmentRow.tsx', '-  // previous rendering shown in attached screenshot\n+  // updated rendering shown in attached screenshot',
                'Can you include the narrow viewport in the screenshots? The original ticket came from a tablet.',
                'Added the tablet capture. The first upload was from my laptop at browser zoom 90, sorry.'))
            if row['title'] in EXCERPTS:
                path, diff = EXCERPTS[row['title']]
            row['text'] = (f'## {row["title"]}\nOpened by {author}. Draft, review requested.\n\n'
                f'### Context\n{original}\n\n### Checks\nLocal fixture run attached. The customer capture is '
                'in the ticket, not in the repository. I have not included a rollout result here.\n\n'
                f'### Excerpt: {path}\n```diff\n{diff}\n```\n\n'
                f'### Review comments\n{a}: {review}\n{author}: {reply}\n'
                f'{b}: I left a note on the screenshot. Please keep the original alongside the updated capture.\n'
                f'{author}: done, both are on the ticket now.\n')
        elif row['kind'] == 'commit':
            row['text'] = (row['title'] + '\n\n' + original + '\n\n'
                'Repro notes and the before/after capture are attached to the linked ticket.\n'
                f'Reviewed-by: {a}\n')
