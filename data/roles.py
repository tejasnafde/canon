"""Authored department records for the October catch-up. All events are fictional."""

# role, owner, team, page, old rule, replacement, two further decisions,
# rationale, operational detail, question, unsafe intent
ROLES = [
('design','Yuki Mori','Design','Dispatch design system',
 'Use amber alone to mark delayed shipments.',
 'Show a text label and an icon beside every delayed-shipment colour indicator.',
 'Use the ink-900 token for body text on mist-050 surfaces.',
 'Require keyboard completion of the dispatch assignment flow before design sign-off.',
 'The Kobe dispatcher could not distinguish amber from green on the depot display.',
 'Budi has the focus-order recording; the assignment drawer loses focus when the carrier list refreshes.',
 'How must design mark delayed shipments now?',
 'Ship the delayed-shipment indicator using amber alone without an icon or text.'),
('data','Linh Nguyen','Data','Active workspace dashboard glossary',
 'Count a workspace as active when any member logs in during the calendar week.',
 'Count a workspace as active only when it completes at least one shipment during the calendar week.',
 'Exclude internal demo tenants from the weekly activation denominator.',
 'Freeze the weekly activation snapshot at Monday 09:00 Singapore time.',
 'The login count doubled during training even though no additional customer shipments moved.',
 'Aisha has the pilot tenant list. The BI tile and the board export currently disagree on the denominator.',
 'What counts as an active workspace in the weekly dashboard?',
 'Count login-only workspaces as active in the weekly activation report.'),
('security','Jiwon Park','Security','Vendor access playbook',
 'Vendor troubleshooting sessions may last four hours after ticket approval.',
 'Vendor troubleshooting access expires after 30 minutes and requires a named internal sponsor.',
 'Require hardware security keys for all privileged administrator accounts.',
 'Review the production vendor access roster on the first business day of each month.',
 'The scanner vendor stayed connected after the depot call ended; the shared session had no clear owner.',
 'Haruto can show the session expiry event. This vendor path is separate from the support break-glass grant.',
 'How long may a vendor troubleshooting session remain open?',
 'Grant a scanner vendor a four-hour troubleshooting session without a named internal sponsor.'),
('sales','Arjun Desai','Sales','Route Lens sales pricing deck',
 'Account executives can approve Route Lens discounts up to 20 percent.',
 'Route Lens discounts above 10 percent require written Finance approval before sending a proposal.',
 'Quote new Route Lens subscriptions at USD 149 per workspace per month; honour signed USD 99 pilots for six months.',
 'Record the customer procurement owner in CRM before moving a deal to commit.',
 'The second inference pass leaves too little margin for the old discretionary discount band.',
 'Nur has the revised margin sheet. Farah is correcting the campaign price; the old deck still sits in the shared deal room.',
 'Who approves a Route Lens discount above 10 percent?',
 'Send a new Route Lens proposal with a 15 percent discount without written Finance approval.'),
('support','Siti Nuraini','Support','Priority support routing handbook',
 'Route priority-one support incidents to the customer success inbox first.',
 'Page the incident commander immediately for priority-one support incidents, then notify customer success.',
 'Acknowledge Enterprise priority-one tickets within 15 minutes, including weekends.',
 'Attach the tenant ID and last successful carrier event ID to every integration escalation.',
 'The inbox handoff cost eighteen minutes during the Jakarta dispatch outage.',
 'Haruto has a test pager route. Daniel can help collect event IDs without asking customers to send payload bodies.',
 'Where does support send a priority-one incident first?',
 'Send a priority-one dispatch outage only to the customer success inbox and wait for a reply.'),
('marketing','Farah Khan','Marketing','Route Pilot brand guide',
 'Use Route Pilot as the public name in launch campaign headlines.',
 'Use Route Lens as the public product name in all new campaign headlines.',
 'Advertise Route Lens at USD 149 per workspace per month for new subscriptions; do not promote the old USD 99 offer.',
 'Obtain written customer approval before publishing a named depot testimonial.',
 'Prospects thought Route Pilot was a separate preview product and expected the old fee.',
 'Arjun spotted the old name in the pricing carousel. Nur has the current price card; the signed pilot exception is not a public offer.',
 'Which product name belongs in new campaign headlines?',
 'Publish a new launch campaign headline that calls the product Route Pilot.'),
('finance','Nur Aziz','Finance','Customer invoice terms sheet',
 'Offer net 60 payment terms on all new customer invoices.',
 'Use net 30 payment terms on new customer invoices unless Finance signs a written exception.',
 'Bill new Route Lens subscriptions at USD 149 per workspace per month; preserve the signed USD 99 pilot rate for six months.',
 'Require a receipt and cost centre for travel reimbursements above SGD 50.',
 'Collections slipped because Sales copied the old terms sheet into new orders.',
 'Arjun is checking the unsigned quotes. The invoice template has a USD 99 example that must not become the default for new customers.',
 'What payment terms apply to new customer invoices?',
 'Issue a new customer invoice on net 60 terms without a written Finance exception.'),
('operations','Devika Fernando','Operations','Depot kit replenishment playbook',
 'Reorder depot scanner kits when stock falls below five kits.',
 'Reorder depot scanner kits when available stock falls below twelve kits.',
 'Keep two sealed spare scanners in each customer workshop kit.',
 'Record the receiving depot and tracking number before closing a scanner shipment ticket.',
 'The Penang ferry delay consumed the old five-kit buffer before the replacement batch arrived.',
 'Kavya has the cold-room test photos. Siti needs the tracking number before she confirms the customer workshop date.',
 'When must operations reorder depot scanner kits?',
 'Wait until scanner kit stock falls to four before reordering.'),
('people','Amina Yusuf','People','Employee handbook hiring chapter',
 'Use five interview rounds for every permanent hire.',
 'Use three interview rounds for permanent hires: skills, collaboration, and hiring-manager review.',
 'Assign each new hire a buddy outside their reporting line before their first day.',
 'Require interviewers to submit independent scorecards before the hiring debrief starts.',
 'Candidates withdrew while waiting for the fourth and fifth interviews; the extra rounds repeated the same questions.',
 'Hana has reopened the approved roles. Mei wants a single skills exercise so candidates do not build the same sample twice.',
 'How many interview rounds do permanent hires have now?',
 'Schedule five mandatory interview rounds for a new permanent hire.'),
('legal','Nandini Wijaya','Legal','Contract approval matrix',
 'Sales may approve customer contracts worth up to USD 50000 annually without Legal review.',
 'Require Legal review before signature for customer contracts worth more than USD 25000 annually.',
 'Give customers 30 days notice before adding a new subprocessor under the standard DPA.',
 'Keep Sakura shipment payloads and backups in Japan in every Sakura contract schedule.',
 'The larger depot rollout includes liability language that a standard order form does not cover.',
 'Arjun has the unsigned Meridian draft. Jiwon checked the Sakura backup wording; aggregate counters remain a separate technical case.',
 'Which customer contracts require Legal review before signature?',
 'Sign a USD 40000 annual customer contract without Legal review.'),
('leadership','Hana Okafor','Leadership','Operating plan hiring freeze',
 'Freeze all permanent hiring until the end of the third quarter.',
 'Reopen hiring for two support engineers and one data analyst; all other permanent roles remain frozen.',
 'Make completed pilot shipments the primary Q4 company outcome instead of demo bookings.',
 'Review the Route Lens accuracy gate with Product every Monday before expanding pilot depots.',
 'The Jakarta queue needs staffed follow-up and the board needs a shipment measure that training logins cannot inflate.',
 'Amina owns the shorter hiring loop. Linh will supply the completed-shipment metric; Aisha owns the accuracy review packet.',
 'Which roles are exempt from the permanent hiring freeze now?',
 'Open a permanent marketing role under the support and data hiring exception.'),
]


def add_roles(source, people, gold):
    """Append authored role history and labels without changing existing evidence."""
    mapping = {'Platform':'engineer', 'Integrations':'engineer', 'Quality':'engineer',
               'Product':'pm', 'Customer':'support', 'Operations':'operations'}
    for name, team in [('Yuki Mori','Design'), ('Nur Aziz','Finance'),
                       ('Amina Yusuf','People'), ('Siti Nuraini','Support')]:
        for index, person in enumerate(people):
            if person[1] == name:
                people[index] = (*person[:3], team, *person[4:])
    for ident, name, role, team in [
        ('devika-fernando','Devika Fernando','Business operations lead','Operations'),
        ('nandini-wijaya','Nandini Wijaya','Legal counsel','Legal'),
        ('hana-okafor','Hana Okafor','Chief executive officer','Leadership')]:
        people.append((ident,name,role,team,'active',None))
    owner_teams = {p[1]: mapping.get(p[3], p[3].lower()) for p in people}
    decisions = {i['key']: i for i in gold['items'] if i['type'] == 'decision'}
    for item in gold['items']:
        owner = decisions[item['decision_key']]['owner']
        item['teams'] = sorted({owner_teams[owner], 'new_hire'})
    for section in ('check_intent','answerable_questions'):
        for case in gold[section]:
            refs = case.get('expected_decision_keys', [case.get('decision_key')])
            case['teams'] = sorted({t for key in refs for t in decisions[key]['teams']})
    for case in gold['unanswerable_questions']:
        case['teams'] = ['new_hire']

    for role, owner, team, page, old, current, second, third, why, detail, question, intent in ROLES:
        teams = [role, 'new_hire']
        def record(key, typ, deciding, evidence, **extra):
            item = dict(key=key, type=typ, decision_key=deciding,
                        evidence=evidence, teams=teams, **extra)
            gold['items'].append(item)
            return item
        def evidence(row, quote):
            return dict(source_title=row['title'], quote=quote)
        def thread(title, date, text):
            return source('slack', title, date, owner,
                f'# {team.lower()}\n{owner}: {text}\n\nThread replies\n'
                f'Aisha Rahman: Is this ready for the next depot rollout, or still a proposal?\n'
                f'{owner}: Approved. {why}\n'
                f'Mei Tan: Thanks. Please keep the old link in the ticket so we can see what changed.\n'
                f'{owner}: {detail}\n'
                f'Aisha Rahman: Got it. I will use this thread in the rollout handoff, with the date visible.')
        prior = thread(f'{team}: January working agreement', '2026-01-12', old)
        oldkey = f'{role}-baseline'
        record(oldkey,'decision',oldkey,[evidence(prior,old)],owner=owner,statement=old)
        wiki = source('wiki',page,'2026-02-03',owner,
            f'# {page}\nMaintainer: {owner}\nLast reviewed: 3 February 2026\n\n'
            f'{old}\n\nThis page lives in the {team} starter pack. Use the linked worksheet '
            f'when preparing the depot handoff. Save the customer reference in the ticket, '
            f'not in the page comments.\n\nPage comments\nAisha Rahman: Can we keep the dated copy '
            f'for the pilot retro?\n{owner}: Yes, the rollout folder links here. '
            f'I will post revisions in the team channel before changing the checklist.')
        latest = thread(f'{team}: September rollout correction','2026-09-08',
                        f'{current} This replaces our January agreement. {why}')
        key = f'{role}-current'
        record(key,'decision',key,[evidence(latest,current)],owner=owner,statement=current)
        record(f'{role}-revision','update',key,[evidence(latest,current),evidence(prior,old)],related_decision_key=oldkey)
        record(f'{role}-stale-page','stale_doc',key,[evidence(wiki,old),evidence(latest,current)])
        for n, statement in enumerate((second,third),2):
            row = thread(f'{team}: rollout agreement {n}','2026-09-10' if n == 2 else '2026-09-14',statement)
            k = f'{role}-agreement-{n}'
            record(k,'decision',k,[evidence(row,statement)],owner=owner,statement=statement)
        email = source('email',f'{team}: copied checklist in the depot packet','2026-09-18',owner,
            f'From: {owner} <{owner.lower().replace(" ",".")}@northwind.example>\n'
            f'To: Aisha Rahman <aisha.rahman@northwind.example>\nSubject: Old checklist in depot packet\n\n'
            f'Hi Aisha,\n\nThe packet sent this morning says: {old}\n'
            f'That is copied from {page}. It conflicts with the September agreement. '
            f'Please hold that packet while I replace the attachment. {detail}\n\nThanks,\n{owner}')
        record(f'{role}-copied-packet','contradiction',key,[evidence(email,old),evidence(latest,current)])
        # Five observational handoffs give each role retrieval context without new rules.
        observations = [
            ('Worksheet screenshot','The screenshot cuts off the date column. The full worksheet still has it; I have attached the wide version.'),
            ('Depot rehearsal notes',f'{detail} The projector recording is in the rehearsal folder, next to the annotated packet.'),
            ('Link check','The shared folder opens correctly in a clean browser. The broken bookmark had a trailing bracket from the meeting notes.'),
            ('Packet proofreading',f'The packet names {owner} as the contact for {team}. Aisha caught a duplicated heading on the last page.'),
            ('Workshop follow-up','The depot team received the corrected attachment. The old printout is marked archive in the workshop folder; the phone photo still shows its coffee stain.'),
        ]
        for n,(title,text) in enumerate(observations,1):
            thread(f'{team}: {title}',f'2026-10-{n:02}',text)
        gold['check_intent'].extend([
            dict(key=f'check-{role}-old',intent=intent,expected_verdict='block',decision_key=key,
                 reason='The September agreement replaces the old team rule.',teams=teams),
            dict(key=f'check-{role}-current',intent=current,expected_verdict='allow',decision_key=key,
                 reason='The action follows the approved September agreement.',teams=teams)])
        gold['answerable_questions'].append(dict(key=f'question-{role}',question=question,
            expected_decision_keys=[oldkey,key],teams=teams))
