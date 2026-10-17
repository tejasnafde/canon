"""Rebuild the hand-authored synthetic corpus. No network or model calls."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sources = []
items = []

PEOPLE = [
('anika-rao','Anika Rao','Staff platform engineer','Platform','left','2026-06-30'),
('mei-tan','Mei Tan','Engineering manager','Platform','active',None),
('haruto-sato','Haruto Sato','Site reliability engineer','Platform','active',None),
('aisha-rahman','Aisha Rahman','Product lead','Product','active',None),
('pranav-menon','Pranav Menon','Backend engineer','Platform','active',None),
('linh-nguyen','Linh Nguyen','Data engineer','Data','active',None),
('jiwon-park','Jiwon Park','Security engineer','Security','active',None),
('siti-nuraini','Siti Nuraini','Customer success lead','Customer','active',None),
('arjun-desai','Arjun Desai','Account executive','Sales','active',None),
('yuki-mori','Yuki Mori','Product designer','Product','active',None),
('nur-aziz','Nur Aziz','Finance lead','Operations','active',None),
('chen-wei','Chen Wei','Integration engineer','Integrations','active',None),
('kavya-iyer','Kavya Iyer','QA engineer','Quality','active',None),
('daniel-lim','Daniel Lim','Solutions architect','Customer','active',None),
('thao-tran','Thao Tran','Technical writer','Product','active',None),
('ravi-perera','Ravi Perera','Support engineer','Customer','left','2026-02-27'),
('amina-yusuf','Amina Yusuf','People operations partner','Operations','active',None),
('tomoko-ito','Tomoko Ito','Analytics engineer','Data','left','2025-12-19'),
('farah-khan','Farah Khan','Product marketing manager','Marketing','active',None),
('budi-santoso','Budi Santoso','Frontend engineer','Product','active',None),
]

def source(kind, title, date, author, text):
    n = len(sources) + 1
    stamp = date + 'T04:30:00Z'
    slug = title.lower().replace(' ', '-').replace('/', '-')
    urls = {
        'slack': f'https://northwind.slack.example/archives/CPLATFORM/p{int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())}{n:06}',
        'meeting': f'https://meet.northwind.example/recordings/{n}-{slug}',
        'wiki': f'https://wiki.northwind.example/pages/{n}/{slug}',
        'pr': f'https://git.northwind.example/northwind/dispatch/pull/{400+n}',
        'commit': f'https://git.northwind.example/northwind/dispatch/commit/{n:040x}',
        'email': f'https://mail.northwind.example/thread/{n}-{slug}',
    }
    row = dict(workspace='acme', kind=kind, title=title, author=author, ts=stamp,
               url=urls[kind], text=text, synthetic=True)
    sources.append(row)
    return row

def plant(key, typ, decision, row, quote, **extra):
    items.append(dict(key=key, type=typ, decision_key=decision,
                      evidence=[dict(source_title=row['title'], quote=quote)], **extra))

# Each tuple is authored content, rather than a generated policy template.
DECISIONS = [
('release-window','2025-01-16','Anika Rao','Release calendar pilot','For now the production release window is Friday afternoon, 14:00 to 16:00 Singapore time.','Support has the lowest ticket volume then. Mei will keep an eye on the first two releases; please put the rollback SHA in the ticket.'),
('event-identity','2025-01-23','Anika Rao','Harbor duplicate scans','Use tenant_id plus carrier_event_id as the deduplication key, and retain those keys for seven days.','The same carton can be scanned at two hubs. A parcel number alone collapses real movement, which explains yesterday\'s missing arrival.'),
('webhook-retry','2025-02-06','Anika Rao','Webhook retry budget','Retry carrier webhooks for at most 24 hours, then move them to the dead-letter queue.','A week of retries hides broken partner credentials. Chen owns the replay runbook; do not throw away the original event timestamp.'),
('residency','2025-02-20','Jiwon Park','Sakura residency review','Keep Sakura customer payloads and their backups in Japan.','The procurement addendum includes backups, not just the primary store. Singapore can receive aggregate counters without shipment identifiers.'),
('audit-retention','2025-03-05','Jiwon Park','Audit trail sizing','Retain tenant audit records for 365 days, including records from closed accounts.','This covers our enterprise audit clause. Payload logging stays out of this stream; hashes and actor IDs are sufficient.'),
('eta-fallback','2025-03-19','Anika Rao','Monsoon ETA timeout','After 800 milliseconds without a route-model response, return the last carrier ETA with its observed_at timestamp.','A slightly old estimate beats holding the dispatch screen open. Yuki asked that we show the age instead of pretending this is a fresh prediction.'),
('billing-unit','2025-04-03','Nur Aziz','Metering working session','Bill once per completed shipment, not per tracking event.','Scans are noisy and some carriers send ten times as many. Finance will reconcile against the completed ledger, with cancellations excluded.'),
('export-access','2025-04-17','Jiwon Park','CSV permission review','Only tenant admins can download shipment CSV exports.','Support can guide an admin through the UI. Impersonation is not an export permission; this also applies to the bulk API.'),
('sandbox-data','2025-05-08','Anika Rao','Demo tenant cleanup','Use fabricated shipments in shared sandboxes; customer payloads cannot be copied there.','Even a masked address can be reconstructed from the route and phone suffix. Daniel has a generator for the Osaka demo.'),
('cursor-order','2025-05-22','Anika Rao','Tracking pagination edge cases','Order tracking cursors by ingestion sequence, not carrier event time.','Late offline scans otherwise land behind a cursor the client has already passed. Event time remains the time shown in the timeline.'),
('sso-tier','2025-06-05','Aisha Rahman','Enterprise packaging notes','SAML SSO is included in Enterprise and is not a paid add-on.','The security review is already hard enough for buyers. Farah will remove the separate SSO price row before the next brochure.'),
('pager-coverage','2025-06-19','Mei Tan','APAC rota handoff','Every production change needs a primary and a secondary responder online for the next two hours.','The secondary cannot also be the person driving a customer workshop. Haruto will maintain the rota in Singapore time.'),
('dr-drill','2025-07-03','Anika Rao','Restore drill follow-up','Run a restore drill every quarter using an isolated tenant fixture.','A green backup job is not proof of a usable restore. The April drill only restored metadata; next time include the event index.'),
('eta-disclaimer','2025-07-17','Aisha Rahman','Arrival confidence copy','Show an estimated range for predicted arrivals, never a guaranteed delivery time.','Meridian\'s warehouse crew schedules breaks around these screens. A point estimate looks more certain than the model deserves.'),
('support-access','2025-08-07','Jiwon Park','Break-glass review','Support production access expires after 60 minutes and requires a ticket reference.','Ravi\'s late shift surfaced the abandoned sessions. No standing access for the night queue; security can approve another timed grant.'),
('connector-quota','2025-08-21','Chen Wei','Kestrel connector capacity','Limit each Kestrel tenant to four concurrent polling requests.','Their signed API agreement allows four slots per tenant. The current 429 graph is global, so Linh is splitting it before tuning anything.'),
('route-launch','2025-09-04','Aisha Rahman','Route Lens launch checkpoint','Route Lens general availability is scheduled for 15 April 2026.','This assumes the Jakarta pilot clears its accuracy gate in February. Sales can offer a design-partner preview before then, not a production SLA.'),
('pricing-v1','2025-09-18','Nur Aziz','Route Lens price card','Route Lens will cost USD 99 per workspace per month at general availability.','The price assumes one regional model pass per shipment. We are not sending annual contracts yet; Arjun can use the number in pilot estimates.'),
('payload-logs','2025-10-02','Anika Rao','Queue log sampling','Log event IDs and error codes only; do not log carrier payload bodies.','Our parser exceptions currently stringify the body. Pranav will replace that before the next connector goes live.'),
('mobile-offline','2025-10-16','Yuki Mori','Driver app offline review','Keep offline proof-of-delivery photos on the device for no more than 48 hours.','Assumes drivers return to a connected depot each day. The upload badge should make the pending state clear without exposing customer names.'),
('replay-approval','2025-11-06','Anika Rao','Replay safety checklist','A replay of more than 10000 events needs approval from the incident commander.','Small replays use the normal support ticket. The threshold is event count, not parcel count; one parcel can have many scans.'),
('fx-lock','2025-11-20','Nur Aziz','Invoice currency close','Lock invoice exchange rates at the start of the billing month.','Use the treasury snapshot for that month. Recomputing at invoice download time gave Meridian two different totals for the same invoice.'),
('dashboard-freshness','2025-12-04','Linh Nguyen','Operations dashboard cache','Cache the fleet dashboard for five minutes while the ingestion rate stays below 2000 events per second.','The pilot peaks at 900. Above that load we need to revisit the cache plan, rather than silently extend the freshness claim.'),
('deletion-window','2025-12-18','Jiwon Park','Tenant deletion review','Delete shipment payloads within 30 days of a verified tenant deletion request.','Audit records are separate and keep their 365-day retention. Thao will draw that distinction in the support article.'),
('idempotency','2026-01-08','Anika Rao','Booking API retry contract','Keep booking idempotency tokens for 72 hours and scope them to the tenant.','The mobile client can reconnect after a weekend. A token reused by another tenant must not reveal the first tenant\'s booking.'),
('pilot-gate','2026-01-22','Aisha Rahman','Jakarta pilot gate','Route Lens needs median absolute arrival error below 12 minutes for three consecutive weeks before GA.','Measure against depot arrival, not gate departure. Linh owns the evaluation notebook; sales anecdotes are not the acceptance sample.'),
('schema-compat','2026-02-05','Anika Rao','Manifest schema rollout','Keep readers compatible with the previous manifest schema for 30 days after a writer upgrade.','Kestrel warehouses update on their own calendar. A clean server deploy does not mean every scanner has refreshed its client.'),
('incident-comms','2026-02-19','Siti Nuraini','Customer incident comms','For a severity-one incident, send the first customer notice within 30 minutes of confirmation.','It is fine to say the cause is unknown. Waiting for a polished root cause left Sakura hearing about their outage from a driver.'),
('model-fallback','2026-02-26','Anika Rao','Route Lens serving budget','Use the regional model while its p95 inference latency stays below 250 milliseconds.','That budget assumes a warm worker pool. If the pool cannot stay warm at our volume, we must reconsider the serving choice.'),
('no-friday','2026-03-09','Anika Rao','INC-042 review: the Friday release','No production deploys on Fridays, including scheduled jobs and configuration-only releases.','The 6 March rollout at 15:10 SGT stalled dispatch acknowledgements for 47 minutes. The rollback engineer was on a flight and the secondary was in a customer call. Emergency mitigation requires incident commander approval and two responders. Mei owns this rule; the ordinary release slots move to Tuesday and Thursday mornings.'),
]
for i, (key, date, author, title, quote, rest) in enumerate(DECISIONS):
    kind = ['meeting','slack','meeting'][i % 3]
    row = source(kind,title,date,author,f'{author}: {quote}\n{rest}\nNotes: the follow-up ticket is in the team board. Please add corrections in this thread rather than editing the customer deck.')
    plant(key,'decision',key,row,quote,owner='Mei Tan' if key == 'no-friday' else author,statement=quote)

review = next(s for s in sources if s['title'] == 'INC-042 review: the Friday release')
plant('update-no-friday', 'update', 'no-friday', review,
      'No production deploys on Fridays, including scheduled jobs and configuration-only releases.',
      related_decision_key='release-window')

# Documents predate the corrections. These are stale snapshots, not current policy.
WIKIS = [
('release-process','Release process','2025-02-12','Thao Tran','Friday afternoon, 14:00 to 16:00 SGT, is our production release window.','no-friday','Tag the build, paste the smoke-test link, and ask the release buddy to watch the dispatch queue. The release checklist lives below the fold.'),
('price-card','Route Lens sales FAQ','2025-10-06','Farah Khan','Route Lens costs USD 99 per workspace per month at GA.','pricing-v2','Pilot access is free. For enterprise procurement, attach the security overview and ask Nur for the invoice entity.'),
('launch-brief','Route Lens launch brief','2025-10-13','Farah Khan','General availability begins on 15 April 2026.','launch-june','The launch pack contains a two-minute warehouse walkthrough, a customer quote placeholder, and the translated landing page strings.'),
('retry-runbook','Carrier webhook recovery','2025-03-11','Chen Wei','Retries continue for 24 hours before an event enters the dead-letter queue.','retry-six','Check credential expiry before pressing replay. The dashboard clock is UTC, which is easy to miss during a late shift.'),
('support-guide','Support access handbook','2025-09-03','Ravi Perera','A production support session lasts 60 minutes.','support-thirty','Record the ticket number in the access request. Ask the shift lead if you cannot identify the affected tenant.'),
('retention-guide','Audit retention FAQ','2025-05-14','Thao Tran','Audit records remain available for 365 days.','audit-two-years','Search by actor or resource ID. The audit viewer excludes shipment payloads, which are stored in a different system.'),
('quota-guide','Kestrel integration setup','2025-10-21','Chen Wei','A tenant can poll Kestrel with four concurrent requests.','quota-two','Start with the supplied cursor and monitor the partner response headers. Their staging hostname has a separate certificate.'),
('booking-guide','Booking retry cookbook','2026-01-15','Thao Tran','Booking idempotency tokens remain valid for 72 hours.','tokens-week','Persist the token before sending the first request. Do not mint a new token just because the response timed out.'),
]
wiki_by_key = {}
for key,title,date,author,quote,decision,rest in WIKIS:
    row=source('wiki',title,date,author,f'# {title}\nLast reviewed: {date}. Owner: {author}.\n{quote}\n{rest}\nRelated: onboarding index, customer escalation roster.')
    wiki_by_key[key]=row
    plant('stale-'+key,'stale_doc',decision,row,quote)

UPDATES = [
('retry-six','2026-03-17','Chen Wei','Webhook budget after partner review','Reduce the webhook retry horizon from 24 hours to six hours; dead-letter handling stays unchanged.','webhook-retry','The carrier only keeps its signature keys valid for eight hours now. Replaying a signed request tomorrow cannot succeed.'),
('support-thirty','2026-03-24','Jiwon Park','Support session review, March','Production support sessions now expire after 30 minutes instead of 60.','support-access','The access proxy supports renewal in place, so nobody needs a standing grant to finish a ticket.'),
('pricing-v2','2026-04-02','Nur Aziz','Route Lens commercial reset','Replace the USD 99 workspace fee with USD 149 per workspace per month for new Route Lens subscriptions.','pricing-v1','The second inference pass makes the original price uneconomic. Aisha approved the change. Signed pilot order forms retain their quoted price for six months; unsigned proposals get the new card. Arjun needs to refresh the Meridian draft.'),
('launch-june','2026-04-09','Aisha Rahman','Route Lens launch replan','Move Route Lens general availability from 15 April to 2 June 2026.','route-launch','The Jakarta pilot has only one passing week, and the three-week gate stays in force. Preview tenants keep access without a production SLA. Farah owns the website date and Siti owns customer notices.'),
('audit-two-years','2026-04-16','Jiwon Park','Enterprise audit addendum','Extend tenant audit retention from 365 days to 730 days for all tenants.','audit-retention','The new standard addendum removes the shorter tier. Shipment payload deletion remains a separate 30-day process.'),
('quota-two','2026-05-07','Chen Wei','Kestrel v3 contract accepted','Reduce Kestrel polling concurrency to two requests per tenant, replacing the four-slot limit.','connector-quota','The partner exchanges concurrency for a larger page size. Keep the cursor persistence behavior unchanged.'),
('tokens-week','2026-05-21','Anika Rao','Rural booking retry follow-up','Extend booking idempotency retention from 72 hours to seven days.','idempotency','The rural pilot has drivers offline for four days. Tenant scoping remains mandatory; the store estimate includes the additional tokens.'),
('eta-fallback-new','2026-06-04','Mei Tan','ETA timeout tuning','Lower the route-model timeout from 800 to 600 milliseconds, preserving the timestamped carrier fallback.','eta-fallback','Kavya measured UI abandonment at the old tail. This changes the wait budget, not the freshness wording.'),
]
for key,date,author,title,quote,previous,rest in UPDATES:
    row=source('meeting',title,date,author,f'{author}: {quote}\n{rest}\nAttendees checked the migration ticket. The old handbook link is still circulating in onboarding.')
    plant(key,'decision',key,row,quote,owner=author,statement=quote)
    plant('update-'+key,'update',key,row,quote,related_decision_key=previous)

CONFLICTS = [
('friday-cron','2026-08-14','Pranav Menon','PR 684: unattended dispatch refresh','The workflow uses cron "0 7 * * 5" to roll the production dispatch service at 15:00 Singapore time.','no-friday','This is just housekeeping for the image tag; I copied the slot from Release process. Tests cover the Tuesday dry run. Mei, can you take a quick look before lunch?'),
('old-price-email','2026-04-23','Arjun Desai','Meridian renewal: Route Lens line item','Your new Route Lens subscription will be USD 99 per workspace per month when you sign next week.','pricing-v2','Hi Nandini, I have attached the revised seat counts. There is no existing Route Lens order form on your account, so we can bundle this with the renewal. Thanks for waiting while I was at the depot.'),
('old-launch-email','2026-04-10','Siti Nuraini','Sakura production enablement date','We will switch your Route Lens tenant to general availability on 15 April, with the standard production SLA.','launch-june','Hi Miki, the screenshots from your preview look good. I reused the launch note from the enablement folder. Please send the list of warehouse admins by Tuesday.'),
('payload-debug','2026-06-11','Pranav Menon','PR 702: parser diagnostics','On parse failure, serialize the complete incoming carrier JSON into the application log.','payload-logs','The event ID alone is not enough to reproduce the Kestrel corner case. The log stream already has a restricted reader group, so this felt like the quickest route.'),
('sakura-backup','2026-07-02','Haruto Sato','Backup footprint proposal','The Sakura nightly snapshot will land in the shared Singapore recovery bucket.','residency','Primary traffic stays in Tokyo. The shared recovery setup has passed restore drills, and I would rather not maintain another bucket policy.'),
('csv-shortcut','2026-07-16','Budi Santoso','PR 731: warehouse download shortcut','Enable the bulk CSV download button for every warehouse viewer.','export-access','Supervisors keep asking support to pull the file. This reuses the existing export endpoint and skips the role check in the button component.'),
('demo-copy','2026-08-06','Daniel Lim','Osaka demo preparation thread','I will seed the shared demo tenant with last Tuesday\'s Meridian shipments after hiding the customer_name field.','sandbox-data','The invented routes do not show the cross-dock hop well. Phone suffixes and depot coordinates are still useful for the map, so I kept those.'),
('guarantee-copy','2026-09-03','Farah Khan','September landing page draft','Route Lens guarantees your shipment will arrive at the displayed time.','eta-disclaimer','This is the short headline for the new hero. We can tuck the confidence chart lower down; the current range copy wraps badly on mobile.'),
]
for key,date,author,title,quote,decision,rest in CONFLICTS:
    row=source('pr' if title.startswith('PR') else 'email' if 'email' in key else 'slack',title,date,author,f'{quote}\n{rest}')
    plant(key,'contradiction',decision,row,quote)

PREMISES = [
('signature-expiry','2026-03-12','Chen Wei','Kestrel signing-key notice','Kestrel now expires request signing keys eight hours after issue.','webhook-retry','The old key remains visible in their portal but no longer validates a replay. Their support person confirmed this is live, not a staging flag.'),
('double-inference','2026-03-26','Linh Nguyen','Route Lens March cost trace','Every Route Lens shipment now runs two regional inference passes, including the customs-risk pass.','pricing-v1','The single-pass estimate in the price workbook is missing the second span. I attached ten trace IDs; this is not caused by client retries.'),
('offline-depots','2026-04-30','Siti Nuraini','Rural pilot visit notes','The Palawan drivers return to a connected depot every four days, not every day.','mobile-offline','Photos remain pending on the shared phone until the ferry route returns. The team showed me the grey upload badge on three consecutive shifts.'),
('dashboard-load','2026-06-18','Linh Nguyen','Fleet peak after eastern rollout','The ingestion stream sustained 3400 events per second for 90 minutes this morning.','dashboard-freshness','That is normalized events, with retries removed. The eastern depots are on their normal shift, so this is not a load test spike.'),
('cold-pool','2026-07-09','Haruto Sato','Route Lens low-volume trace','The regional inference worker pool scales to zero between customer batches; p95 is now 610 milliseconds.','model-fallback','The p95 excludes browser and network time. Keeping a worker warm would exceed the approved pilot spend; I have not changed the serving path yet.'),
]
for key,date,author,title,quote,decision,rest in PREMISES:
    row=source('email' if key=='signature-expiry' else 'slack',title,date,author,f'{author}: {quote}\n{rest}')
    plant(key,'premise_change',decision,row,quote)

# Incident chronology includes an actual Friday, rather than only the review.
source('slack','INC-042 live dispatch thread','2026-03-06','Haruto Sato',
       '15:14 SGT Haruto: dispatch ACK age is at 11 minutes after the 15:10 rollout. Opening INC-042.\n15:22 Mei: Pranav is on the flight to Pune. I am pulling Kavya out of the Sakura call.\n15:57 Haruto: rollback complete, ACK age is falling. Customer impact was 47 minutes.\n16:06 Siti: the first customer notice went at 15:36. Please keep the thread quiet until I have the depot count.')
source('commit','Revert dispatch acknowledgement batching','2026-03-06','Mei Tan',
       'Revert 8c31a7: restore per-tenant acknowledgement flush. The grouped flush can wait behind a tenant with an expired carrier token. INC-042 links the queue trace and rollback timings. This commit restores the old path without changing the manifest schema.')
source('slack','Anika handover questions','2026-06-26','Anika Rao',
       'Last handover slot is Tuesday. Mei has the release rota, Chen has the replay notebook, and Jiwon has the residency addenda. Please ask the awkward questions now. The cursor ordering note is the one people usually misread: the UI can still sort event times while the API advances by ingestion sequence. I will miss the depot stories, less so the pager.')
source('email','Anika departure and ownership handoff','2026-06-30','Amina Yusuf',
       'Today is Anika Rao\'s last day at Northwind Labs. Platform ownership moves to Mei Tan; connector questions go to Chen Wei. Her historical notes stay in the archive. Please do not route new approvals to Anika\'s address. The farewell lunch receipts go to the usual expense folder.')

# Hand-authored ambient artifacts. These provide negative examples and vocabulary,
# without introducing competing policy decisions outside the gold set.
AMBIENT = '''2025-01-07|slack|Amina Yusuf|First week, same kettle|The new Singapore office kettle whistles louder than the meeting-room speaker. There are spare mugs beside the visitor badges. Welcome to the nine people joining this month; the org chart now has 60 names.
2025-01-10|email|Siti Nuraini|Meridian depot photos|Nandini sent the depot photos but the attachment order is reversed. The blue ramp is the inbound side. I put captions in the shared album so Yuki does not have to guess from the forklift direction.
2025-01-21|commit|Budi Santoso|Align route chip baseline|Move the route chip label down one pixel in the compact shipment row. No query or permission changes. Before and after screenshots are attached to the review.
2025-01-28|slack|Kavya Iyer|Scanner test bench|The left-hand scanner has a cracked charging cable. The intermittent disconnect in yesterday's video is the cable, not a websocket failure. I have put a paper tag on it.
2025-02-04|meeting|Yuki Mori|Depot shadowing notebook|A supervisor uses two browser windows because the arrivals screen loses scroll position. She calls both windows the board. The word dashboard did not come up once in the interview.
2025-02-13|pr|Pranav Menon|PR 423: fix empty lane label|Handle an empty lane_name in the row renderer. The fixture came from a fabricated shipment, not the Meridian export. Reviewer question: should the blank label use a narrow space or the word Unassigned?
2025-02-25|slack|Haruto Sato|Rain on the office link|Packet loss on the office Wi-Fi coincides with the storm. The synthetic probe from Tokyo is green. If your local dev tunnel stalls, the production graph is the useful comparison.
2025-03-04|email|Daniel Lim|Sakura workshop room|The customer moved our workshop to floor 6. Visitor reception still has floor 4 on the calendar. Miki will meet us by the lift; the loading bay entrance is only for warehouse staff.
2025-03-13|commit|Linh Nguyen|Fix chart legend spelling|Correct Singpore in the region legend. The underlying region key remains ap-sg. Tomoko spotted this in a screenshot that has apparently been in three board decks.
2025-03-25|meeting|Tomoko Ito|Analytics office hours|The export total and the tile total differ because the tile excludes cancelled shipments. Nur found the same two cancellations in the ledger. No missing rows so far; the query links are in the notebook.
2025-04-01|slack|Chen Wei|Kestrel portal password reset|The partner portal reset email takes about ten minutes today. Their status banner mentions mail delivery. Our connector authentication is healthy; this is only the human portal login.
2025-04-10|pr|Budi Santoso|PR 447: keep filter on back navigation|Preserve the depot filter when navigating from a shipment detail page. The state belongs to the URL, so opening a new tab still shows the same depot. The screenshot uses the Osaka sandbox.
2025-04-22|email|Arjun Desai|Meridian invoice contact|Nandini is the warehouse sponsor, not the accounts-payable contact. Please address invoice questions to Devika. I have corrected the CRM contact label; the signed order form was already right.
2025-05-01|slack|Amina Yusuf|May holiday overlaps|Several teams have holidays on different days this week. The shared calendar has Singapore, Tokyo and Bengaluru overlays. Meeting rooms are quiet but the bakery downstairs is somehow busier.
2025-05-13|meeting|Kavya Iyer|QA pairing notes: barcodes|The scanner reads the new glossy labels when tilted. A matte label passes at every angle. The test video includes the desk lamp position, since the first clip made this look random.
2025-05-27|commit|Pranav Menon|Name replay counter correctly|Rename replayed_parcels to replayed_events in the internal diagnostic. The counter already counts events. No change to replay behavior or approval handling.
2025-06-03|slack|Yuki Mori|Map colour printout|The green and blue lanes look identical on the meeting-room printer. On-screen contrast is fine. I left a grayscale printout on the design desk for the customer workshop pack.
2025-06-12|email|Farah Khan|Case study quote attribution|The quote about fewer phone calls came from Sakura's shift supervisor, not their CIO. The customer marked the attribution on page two. The marketing draft now shows the supervisor's approved title.
2025-06-24|pr|Chen Wei|PR 469: partner header casing|Treat the Kestrel cursor response header case-insensitively. Their staging gateway uses a different case from production. The captured fixture contains only invented event IDs.
2025-07-01|slack|Ravi Perera|Night queue handoff|Two tickets remain in the night queue. One is a browser zoom issue, and one needs a clearer photo of the scanner label. Neither customer reports missing shipments. Coffee vouchers are in the drawer.
2025-07-10|meeting|Daniel Lim|Demo rehearsal: Osaka|The cross-dock animation runs too fast for the interpreter. We paused on the lane map and everyone could follow it. The customer wants to see the late-truck story before the admin setup.
2025-07-22|commit|Budi Santoso|Fix long depot name clipping|Allow the depot name to wrap in the narrow drawer. The longest fixture is Bandar Seri Begawan North. The row height grows naturally; there is no hardcoded country-specific width.
2025-08-05|slack|Nur Aziz|Expense receipt mystery|The receipt titled dinner-final-final is a taxi receipt. If it belongs to you, the expense portal is waiting for a category correction. No judgement on the filename, I have seen worse this week.
2025-08-14|email|Siti Nuraini|Sakura training attendance|Eight supervisors attended the second session. Two watched from one laptop, which explains the meeting attendance count of seven. Miki has the recording link and the annotated keyboard shortcuts.
2025-08-26|pr|Kavya Iyer|PR 491: deterministic scan fixture|Replace the random scan timestamp in the UI test with a fixed value. The flaky assertion crossed midnight in Tokyo. The test still covers an offline scan arriving after a newer scan.
2025-09-02|slack|Linh Nguyen|Notebook kernel queue|The shared notebook is busy with Tomoko's reconciliation run. My cell has not started yet; the blank chart is not a zero count. I will paste the completed plot when the kernel finishes.
2025-09-11|meeting|Aisha Rahman|Route Lens naming discussion|Three interviewees heard root lens rather than route lens. The mock-up with the road icon helped. Farah has the audio clips for anyone writing the launch narration.
2025-09-23|commit|Haruto Sato|Repair dashboard panel link|Point the queue-age panel to the tenant-filtered view. The old link dropped the tenant variable but the alert query itself was scoped correctly. The panel title is unchanged.
2025-10-07|slack|Tomoko Ito|The spreadsheet with two Septembers|The duplicate September tab is an old export, not another billing month. Nur found it while reconciling the workbook. I put the export timestamp in its tab name so it is less alarming.
2025-10-14|email|Arjun Desai|Meridian pilot vocabulary|The customer says consignment where our UI says shipment. Their pilot spreadsheet uses both. Daniel's workshop glossary has the mapping, including the one-to-many relation to cartons.
2025-10-28|pr|Budi Santoso|PR 517: drawer focus return|Return keyboard focus to the originating shipment row after closing the drawer. Tested with a filtered list and with the row removed by a refresh. The design review has a short screen recording.
2025-11-04|slack|Amina Yusuf|Lunch walk route|The shaded route behind the office is open again. The short bridge still has construction barriers. For anyone joining the lunch walk, the group meets beside reception after the all-hands.
2025-11-13|meeting|Mei Tan|Platform retro: useful screenshots|The most useful support screenshot this month included the tenant selector and the browser clock. The most confusing one cropped both. Ravi has a redacted example in the retro folder.
2025-11-25|commit|Chen Wei|Clarify Kestrel fixture names|Name the partner fixture files by response type instead of capture order. Nothing in this commit changes the polling slots or retry horizon. The fixtures are fabricated examples maintained by integrations.
2025-12-02|slack|Tomoko Ito|Notebook handover index|I linked the invoice reconciliation notebooks from the analytics index. The oldest notebook needs an old package lock to render. Linh has a static export as well, so nobody has to revive my laptop.
2025-12-11|email|Nur Aziz|Quarter close time zones|The ledger export is stamped UTC while the finance sheet displays Singapore time. The two rows near midnight refer to the same shipment. There is no extra shipment to bill.
2025-12-19|slack|Tomoko Ito|Last day, notebook edition|Laptop returned and the handover folder is with Linh. Thanks for teaching me more about barcodes than I expected to know. Please rescue the plant next to my old monitor; it has survived three office moves.
2025-12-23|pr|Kavya Iyer|PR 542: label holiday fixtures|Rename the year-end fixtures so the expected local date is visible in the filename. The test covers a Tokyo scan and a Singapore scan on opposite sides of UTC midnight.
2026-01-06|slack|Siti Nuraini|Back from depot visits|The new tea stall outside Meridian is excellent. More usefully, the supervisors now have the printed shortcut cards beside the scanners. I have uploaded photos of the cards, with no shipment screens visible.
2026-01-13|meeting|Yuki Mori|Mobile upload interview|The grey badge looks disabled to two drivers. They both tapped it repeatedly while offline. We have interview clips and a paper sketch of a pending state; no implementation review yet.
2026-01-27|commit|Pranav Menon|Fix token metric label|Correct the metric help text to say tenant-scoped token. The stored key and its expiry are unchanged. This was a documentation typo in the dashboard, not an isolation bug.
2026-02-03|email|Farah Khan|Preview screenshots for translation|The translator needs the strings in a table, not burned into screenshots. Yuki's export has string keys and a notes column for warehouse vocabulary. The Japanese line breaks are still under review.
2026-02-12|slack|Haruto Sato|Probe and coffee machine|The synthetic probe went red because its own DNS cache was stale. User requests stayed green. Separately the coffee machine is actually broken; that one is not a monitoring false positive.
2026-02-24|pr|Budi Santoso|PR 571: quiet empty search state|Show the selected depot in the empty search message. This helps support distinguish no matches from no tenant data. No changes to the search endpoint or permission handling.
2026-02-27|email|Amina Yusuf|Ravi support handover|Ravi Perera finishes today. Siti has the night-queue checklist and Daniel has the open Sakura training thread. The support alias still reaches the current team; Ravi's individual mailbox is no longer an escalation route.
2026-03-03|slack|Kavya Iyer|March scanner batteries|Two scanner batteries drain quickly during the cold-room test. The spare from the charging rack lasts normally in the same device. I attached the serial numbers to the hardware ticket, not the product bug board.
2026-03-10|meeting|Mei Tan|INC-042 customer impact audit|Siti reconciled the affected depot list against the acknowledgement trace. Seven depots saw delayed status, with no lost bookings. The customer-facing timeline now uses SGT consistently instead of mixing local clocks.
2026-03-19|commit|Haruto Sato|Add rollback trace link|Add the rollback trace URL to the incident index. The index previously linked only the forward rollout. No workflow scheduling or deployment behavior changes in this commit.
2026-03-31|slack|Linh Nguyen|Jakarta evaluation notebook status|The notebook export finished. Week labels now show the full date range, because the calendar week number confused the pilot team. Aisha has the plot for the checkpoint meeting; I have not touched the acceptance threshold.
2026-04-07|email|Daniel Lim|Meridian workshop whiteboard|I typed up the whiteboard while the marker colours were still legible. The dotted arrows are customer questions, not implemented integration paths. The photo and transcription are side by side in the workshop folder.
2026-04-14|pr|Kavya Iyer|PR 608: retry fixture clock|Freeze the clock around the webhook retry boundary test. The previous test sometimes entered the next minute while asserting the queue state. The configured retry horizon is not part of this change.
2026-04-28|slack|Yuki Mori|Price card mobile layout|The new card fits on a narrow phone if the billing period stays on its own line. The screenshot uses the current commercial copy from Nur's sheet. I am still checking the translated footnote length.
2026-05-05|meeting|Siti Nuraini|Customer training office hours|A warehouse lead asked whether a grey ETA meant the shipment stopped moving. It meant the browser was offline. Budi has the reproduction video and the browser network log.
2026-05-14|commit|Chen Wei|Rename partner quota chart|Change the chart legend from workers to concurrent requests. These were always requests, not server instances. The plotted values and the connector limit remain untouched.
2026-05-26|slack|Anika Rao|Handover notebook rough edges|The replay notebook has a stale screenshot of the sidebar, but the command examples still match the tool. Chen found the broken image link. I fixed the image path over lunch; the underlying replay checks are unchanged.
2026-06-02|email|Farah Khan|Launch day screen recording|The recording has a cursor hovering over the route chip for half a minute. I trimmed that pause in the internal cut. Siti's customer walkthrough still has the full interaction for training.
2026-06-09|pr|Budi Santoso|PR 665: upload badge wording|Clarify that pending means waiting for connectivity. The local upload queue and retention behavior do not change. The interview clip from January explains why the old grey label was misleading.
2026-06-23|slack|Amina Yusuf|Anika lunch headcount|The farewell lunch has moved to the larger room. Please add dietary requirements to the form, not this thread. There is a separate handover session; lunch is not an architecture review unless Anika starts one.
2026-07-01|meeting|Mei Tan|Platform handover inbox|The first handover inbox has questions about old cursor choices and current rota coverage. Chen found the relevant notebook links. Mei is collecting unanswered questions for Friday's team discussion, not a production release.
2026-07-07|commit|Pranav Menon|Trim duplicate trace label|Remove a repeated tenant label from the internal trace display. The exporter still carries the tenant field once. No payload body is added to logs.
2026-07-14|slack|Linh Nguyen|Peak chart annotation|The spike annotation points at a replay, while the sustained plateau is live eastern traffic. I moved the annotation so readers do not confuse the two. The raw counters are unchanged.
2026-07-28|email|Siti Nuraini|Sakura summer roster|Miki is away next week. Her deputy has the training recording and knows where the incident notice archive lives. There is no change to the tenant's support contacts in the product.
2026-08-04|pr|Kavya Iyer|PR 681: export filename test|Add the Tokyo local date to the fabricated export filename fixture. The file contents and admin-only endpoint are untouched. This fixes a test expectation that depended on the laptop timezone.
2026-08-11|slack|Pranav Menon|Build badge not updating|The build badge in the README caches for longer than the CI page. The commit is green in CI. I am waiting for the badge cache before taking the demo screenshot so it does not look like a failed build.
2026-08-18|meeting|Aisha Rahman|September onboarding interviews|Two new customer admins found the integration checklist through search rather than the sidebar. Both searched for carrier setup. Thao has the session timestamps for the information architecture review.
2026-08-25|commit|Budi Santoso|Fix range label spacing|Use a nonbreaking space between the ETA number and its unit. The predicted range and observed timestamp remain unchanged. The Japanese layout screenshot now matches the design file.
2026-09-01|email|Nur Aziz|Invoice download reassurance|Meridian compared a fresh download with last month's PDF and the totals match. The difference they saw was the filename date, not a recalculated exchange rate. Devika confirmed the reconciliation is closed.
2026-09-08|slack|Chen Wei|Partner portal maintenance|Kestrel's human portal is down for maintenance. The polling endpoint is responding normally. Their banner is easy to misread because it says platform maintenance without naming the affected service.
2026-09-15|pr|Haruto Sato|PR 751: distinguish probe failures|Label DNS lookup failures separately in the synthetic probe dashboard. This changes the panel grouping only. Alert routing and production access rules remain the same.
2026-09-22|meeting|Yuki Mori|Warehouse glossary test|The carton icon reads as a package to the Singapore group and as an archive box to the Tokyo group. The text label removes the ambiguity. The notes include both language versions for reference.
2026-09-29|slack|Amina Yusuf|October visitor badges|The spare visitor lanyards are back in the reception drawer. Please return the temporary badge before taking a new one. We found three in the cable box during the desk move.
2026-10-06|email|Daniel Lim|Demo laptop checklist|The demo laptop has the fabricated Osaka tenant bookmarked. The browser zoom is back at 100 percent and the projector adapter is in the sleeve. The recording from the last rehearsal is in the team folder.
2026-10-13|slack|Mei Tan|October catch-up pointers|For the new joiners: the handover index is more useful than a long scroll through platform chat. Release history, partner quota changes and the booking retry thread are linked there. Ask me if an old page and a recent review disagree.
2026-10-16|commit|Thao Tran|Repair archive navigation links|Fix the onboarding index links to the incident archive and the Route Lens checkpoint notes. This commit repairs navigation only; it does not rewrite the older policy snapshots.'''
for line in AMBIENT.splitlines():
    date,kind,author,title,text=line.split('|',4)
    source(kind,title,date,author,text)

# Further operational texture: specific observations, not extra planted policies.
EXTRA = '''2025-01-30|Slack search in two languages|Yuki Mori|The Tokyo crew searches for dispatch using the Japanese label. The English tag does not return the screenshot thread. I linked both terms in the interview notes.
2025-02-28|Support queue Friday wrap|Ravi Perera|The ticket tagged duplicate is a repeated email from the same supervisor. The shipment itself has two legitimate hub scans. I merged the tickets and kept both event links.
2025-03-28|Carrier clock skew sample|Chen Wei|One Kestrel scanner is six minutes slow. The uploaded event still carries the original timestamp. The notebook shows device time beside receive time so the mismatch is visible.
2025-04-30|Design file permission hiccup|Yuki Mori|The workshop file opened read-only for Daniel because he followed the archived link. The current file is in the customer research folder. The old one has last month's screenshots.
2025-05-30|Queue dashboard bookmark|Haruto Sato|My saved view hid the dead-letter panel below the fold. The panel was there all along. I have attached a full-height screenshot for the support handover.
2025-06-30|Quarterly depot count|Linh Nguyen|The depot count includes two training sites. Nur's finance sheet excludes them because they have no completed shipments. Both counts reconcile once those filters match.
2025-07-30|Workshop microphone check|Daniel Lim|The room microphone picks up the air conditioner more clearly than the interpreter. A headset worked in the afternoon session. The transcript has speaker labels corrected by Siti.
2025-08-29|Notebook thumbnail stale|Tomoko Ito|The notebook thumbnail still shows a red line from an earlier run. Opening the notebook shows the latest plot. I attached the export timestamp to the image caption.
2025-09-30|Preview tenant invitation|Siti Nuraini|The Sakura preview invitation bounced because the address had a trailing space. Miki resent the corrected list. The preview account is visible in the training roster now.
2025-10-30|Manifest field glossary|Pranav Menon|The new field example says depot code while the schema calls it facility_code. The test fixture is valid. Thao has the naming mismatch on the documentation board.
2025-11-28|Customer call background noise|Arjun Desai|The beeping in the recording is a reversing forklift, not an alert from our app. Daniel was calling from the loading bay. The written notes are easier to follow than the audio.
2025-12-30|End of year desk plant update|Amina Yusuf|Tomoko's plant has moved to the window. Linh has volunteered to water it. The old desk is being used for scanner testing, so the plant now has fewer cables to contend with.
2026-01-30|Route trace colours|Linh Nguyen|The orange span is queue time, not inference. The legend got cropped from the slide. The full trace is linked under the image for anyone checking the model budget.
2026-02-20|Support handover dry run|Ravi Perera|Siti walked through the night-queue checklist using the fabricated tenant. The missing screenshot is a browser permission dialog. I added a caption so the blank region is less mysterious.
2026-03-27|Incident graph export|Haruto Sato|The exported graph starts at 15:00 SGT and the raw query starts at 07:00 UTC. They are the same interval. The incident review PDF has the timezone in its footer now.
2026-04-24|Price workbook comment|Nur Aziz|The yellow cell is a reviewer comment, not another subscription tier. Arjun asked because it appeared in a cropped screenshot. The sheet's legend explains the colour coding.
2026-05-29|Depot visit photo upload|Siti Nuraini|The upload includes four identical photos because the phone retried on the ferry Wi-Fi. The album itself deduplicates them. There is no customer address visible in the shots.
2026-06-19|Farewell card logistics|Amina Yusuf|The farewell card is with Yuki until lunch. Please keep it away from the scanner bench; somebody used the last card to test a barcode sticker. Anika has not seen it yet.
2026-07-31|Demo map tile attribution|Budi Santoso|The map attribution overlaps the zoom control on the projector. It looks fine on my laptop. I attached the projector resolution to the visual bug, since the screenshot alone is misleading.
2026-08-28|Warehouse tablet stand|Kavya Iyer|The new stand blocks the tablet camera in portrait orientation. Landscape works. The hardware ticket includes a photo with the camera position marked in pencil.
2026-09-30|Translation review names|Farah Khan|The translation vendor has two reviewers named Tan. Mei Tan is our engineering manager, not the vendor approver. The spreadsheet now includes company names beside reviewer names.
2026-10-15|Rehearsal coffee stain|Daniel Lim|The printed rehearsal notes now have a coffee ring around the incident timeline. The digital copy is clean. Siti has the annotated version with the customer names pronounced phonetically.'''
for line in EXTRA.splitlines():
    date,title,author,text=line.split('|',3)
    source('slack',title,date,author,text)

# Expand the archive before serialization. Gold evidence remains unchanged.
from archive_texture import enrich_sources
from noise import add_noise

enrich_sources(sources, items)
noise_start = len(sources)
add_noise(source)
# Slack noise is authored as full threads, rather than wrapped a second time.
enrich_sources([row for row in sources[noise_start:] if row['kind'] != 'slack'], [])

# Attach the deciding evidence as well as the changed or conflicting evidence.
by_key={i['key']:i for i in items if i['type']=='decision'}
for item in items:
    if item['type'] != 'decision':
        target = item.get('related_decision_key',item['decision_key'])
        item['evidence'] += by_key[target]['evidence']

CHECKS = [
('Deploy the production dispatch service this Friday at 15:00 SGT using a cron job.','block','no-friday','The ban explicitly includes scheduled jobs.'),
('Release a configuration-only production change on Friday.','block','no-friday','Configuration-only releases are in scope.'),
('Deploy on Tuesday morning with two responders online for two hours.','allow','no-friday','The ordinary Tuesday slot is permitted; responder coverage also applies.'),
('Use the Friday slot to deploy to an isolated staging tenant only.','allow','no-friday','The restriction is production-scoped.'),
('Apply an emergency Friday production mitigation after incident commander approval, with two responders online.','allow','no-friday','The documented emergency exception is satisfied.'),
('Send an unsigned new Route Lens prospect a USD 99 monthly workspace quote.','block','pricing-v2','New subscriptions use USD 149.'),
('Honor a signed pilot order form at USD 99 for its first six months.','allow','pricing-v2','The signed-pilot exception is explicit.'),
('Tell Sakura that Route Lens GA with a production SLA starts on 15 April 2026.','block','launch-june','GA moved to 2 June.'),
('Grant a warehouse viewer access to bulk shipment CSV exports.','block','export-access','Only tenant admins may export.'),
('Copy masked Meridian shipment payloads into the shared demo sandbox.','block','sandbox-data','Masking does not make customer data fabricated.'),
('Replay 15000 carrier events without incident commander approval.','block','replay-approval','The event-count approval threshold is exceeded.'),
('Store Sakura backups in Singapore while keeping the primary in Japan.','block','residency','The residency rule includes backups.'),
('Keep the current five-minute fleet cache after sustained ingestion reaches 3400 events per second.','warn','dashboard-freshness','The load assumption broke; review is required, not an invented replacement interval.'),
('Continue the regional model after its p95 rises to 610 milliseconds.','warn','model-fallback','The latency condition no longer holds; no replacement model is recorded.'),
('Return the timestamped carrier ETA after waiting 600 milliseconds for the route model.','allow','eta-fallback-new','This follows the revised timeout and preserves the fallback.'),
]
QUESTIONS = [
('Why can we no longer deploy production on Fridays?',['release-window','no-friday']),
('Does the Friday restriction include a config-only cron deployment?',['no-friday']),
('What should we quote a new Route Lens customer, and why did the price change?',['pricing-v1','pricing-v2']),
('When did Route Lens GA move, and what gate held it up?',['route-launch','pilot-gate','launch-june']),
('Can support download a tenant CSV for a warehouse viewer?',['export-access']),
('Why did Anika choose ingestion sequence for tracking cursors?',['cursor-order']),
('How long do booking idempotency tokens live now?',['idempotency','tokens-week']),
('Can Sakura backups live outside Japan?',['residency']),
('Why are payload bodies absent from parser error logs?',['payload-logs']),
('What changed in the Kestrel webhook retry horizon?',['webhook-retry','retry-six']),
]
gold=dict(schema_version=1, synthetic=True, company='Northwind Labs', workspace='acme',
          key_semantics='Stable corpus labels, not Firestore IDs. Resolve titles through ingested source IDs and quotes.',
          items=items,
          check_intent=[dict(key=f'check-{i:02}',intent=t,expected_verdict=v,decision_key=d,reason=r) for i,(t,v,d,r) in enumerate(CHECKS,1)],
          answerable_questions=[dict(key=f'question-{i:02}',question=q,expected_decision_keys=d) for i,(q,d) in enumerate(QUESTIONS,1)],
          unanswerable_questions=[dict(key=f'unknown-{i:02}',question=q,expected_refused=True) for i,q in enumerate([
              'What is Northwind Labs annual recurring revenue for 2026?',
              'Which company acquired Northwind Labs?',
              'What is the approved replacement cache interval after the eastern rollout?',
              'What password unlocks the Kestrel partner portal?',
              'Which model replaces the regional model after the July latency regression?'],1)])

def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

for kind in ['slack','meeting','wiki','pr','commit','email']:
    rows=sorted((s for s in sources if s['kind']==kind),key=lambda s:(s['ts'],s['title']))
    (ROOT/'corpus'/f'{kind}.jsonl').write_text(''.join(json.dumps(s,ensure_ascii=False)+'\n' for s in rows))
write_json(ROOT/'people.json',[dict(id=p[0],name=p[1],role=p[2],team=p[3],status=p[4],left_at=p[5]+'T09:00:00Z' if p[5] else None) for p in PEOPLE])
write_json(ROOT/'gold'/'gold.json',gold)
write_json(ROOT/'samples'/'live_paste.json',[
    dict(key='friday-contradiction',expected_relation='contradiction',decision_key='no-friday',source=dict(kind='paste',title='Dispatch cron review',author='Pranav Menon',ts='2026-10-17T10:00:00Z',workspace='agents',synthetic=True,text='Pranav: I have scheduled the production dispatch image refresh for every Friday at 15:00 Singapore time. It runs unattended, including configuration changes. I used the slot from the Release process wiki. This is routine housekeeping, not incident mitigation.')),
    dict(key='timeout-update',expected_relation='update',decision_key='eta-fallback-new',source=dict(kind='paste',title='Approved October ETA timeout revision',author='Mei Tan',ts='2026-10-17T10:05:00Z',workspace='agents',synthetic=True,text='Mei: After the October latency review, replace the 600 millisecond route-model timeout with 500 milliseconds. Keep the timestamped carrier ETA fallback. I approve this change for the next Tuesday release; the freshness wording stays the same.')),
    dict(key='new-label-policy',expected_relation='new',decision_key=None,source=dict(kind='paste',title='Thermal label procurement review',author='Kavya Iyer',ts='2026-10-17T10:10:00Z',workspace='agents',synthetic=True,text='Kavya: We will use matte thermal labels for all new depot scanner kits. Glossy stock caused reflections in the cold-room test. Nur approved the additional supply cost today. I own the procurement checklist and will update it before the next kit ships.')),
])
write_json(ROOT/'samples'/'agent_playground.json',[
    dict(tool='search_decisions',args=dict(query='Friday production deployments',limit=5),expected_outcome='Find no-friday with the incident-review quote; do not treat the stale wiki as the active policy.',expected_decision_keys=['no-friday']),
    dict(tool='check_intent',args=dict(intent=CHECKS[0][0],actor='release-bot'),expected_outcome='block, citing the Friday production ban.',expected_verdict='block',expected_decision_keys=['no-friday']),
    dict(tool='ask_why',args=dict(question=QUESTIONS[2][0]),expected_outcome='Explain the second inference pass and USD 149 new-subscription fee; cite both commercial reviews.',expected_decision_keys=['pricing-v1','pricing-v2']),
    dict(tool='catch_me_up',args=dict(persona='pm',since='2026-03-01T00:00:00Z'),expected_outcome='Surface the GA delay, new price, old customer promises and stale launch material; suggest updating customer communications.'),
    dict(tool='record_decision',args=dict(statement='Use matte thermal labels for all new depot scanner kits.',rationale='Glossy stock causes reflections in cold-room tests.',source_text='Kavya Iyer: Use matte thermal labels for all new depot scanner kits. Glossy stock causes reflections in cold-room tests. Nur approves the additional supply cost. Kavya owns the checklist.',actor='procurement-bot'),expected_outcome='A new decision with a verified quote and an agent activity entry.'),
    dict(tool='flag_conflict',args=dict(description='A new unsigned Meridian proposal still quotes the old Route Lens fee.',source_text='Arjun: The unsigned Meridian proposal for a new Route Lens subscription quotes USD 99 per workspace per month. It has no signed pilot order form.',actor='pm-bot'),expected_outcome='An alert against pricing-v2 with the old-price proposal evidence and an activity entry.',expected_decision_keys=['pricing-v2']),
])
print(f'Wrote {len(sources)} sources, {len(items)} gold items, {len(PEOPLE)} people.')
