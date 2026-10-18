import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, ErrorState } from '@/components/states'
import { ApiError, api } from '@/lib/api'
import { invalidateRecord, q } from '@/lib/query'
import { fmtLong, quoteFrom, secs, srcLine } from '@/lib/record'
import type { Alert, Decision, IngestResult, Reconciliation } from '@/lib/schemas'
import { useTitle } from '@/lib/title'
import samples from '@/samples/live_paste.json'

const SAMPLE_LABEL: Record<string, string> = {
  'friday-contradiction': 'Friday deploy job',
  'timeout-update': 'New timeout setting',
  'new-label-policy': 'New label supplier',
}

const RELATION: Record<Reconciliation, string> = {
  new: 'Something new. Nothing on record covers it yet.',
  same: 'Already on record. Canon added this as more evidence.',
  update: 'Replaces an older decision.',
  contradiction: 'Goes against a decision that is still active.',
}

const MAX_MB = 15
const TEXT_FILE = /\.(md|txt|csv)$/i
const ACCEPT = 'application/pdf,image/*,audio/*,video/*,.md,.txt,.csv,.ogg,.opus,.m4a,.mov,.webm'
const isMedia = (f: File | null) => !!f && /^(audio|video)\//.test(f.type)

/** The file as plain base64, without the data: URL prefix. */
function toB64(f: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(typeof r.result === 'string' ? (r.result.split(',')[1] ?? '') : '')
    r.onerror = () => reject(new Error('Canon could not read this file.'))
    r.readAsDataURL(f)
  })
}

/** The server's own words for a refused recording ("This recording is 14 minutes; ..."). */
function refusal(e: unknown): string | null {
  if (!(e instanceof ApiError) || (e.status !== 413 && e.status !== 429)) return null
  const i = e.message.indexOf('media_refused: ')
  return i < 0 ? null : e.message.slice(i + 'media_refused: '.length)
}

export default function PastePage() {
  useTitle('paste a message and see what it breaks')
  const decisions = useQuery(q.decisions())
  const [pick, setPick] = useState(samples[0]?.key ?? '')
  const [text, setText] = useState(samples[0]?.source.text ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState('')
  const [over, setOver] = useState(false)
  const picker = useRef<HTMLInputElement>(null)
  const sample = samples.find(s => s.key === pick)
  const run = useMutation({
    mutationFn: async () => {
      const base = sample?.source
      return api.ingest({
        kind: 'paste',
        title: file ? file.name : base && base.text === text ? base.title : 'Pasted message',
        author: base && base.text === text && !file ? base.author : 'Visitor',
        ts: new Date().toISOString(),
        text,
        synthetic: true,
        image_b64: file ? await toB64(file) : null,
      })
    },
    onSuccess: () => void invalidateRecord(),
  })
  const n = decisions.data?.length
  const choose = (f: File | undefined) => {
    run.reset()
    setFileError('')
    if (!f) return
    if (TEXT_FILE.test(f.name) || f.type.startsWith('text/')) {
      void f.text().then(t => {
        setText(t.slice(0, 50_000))
        setPick('')
        setFile(null)
      })
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setFile(null)
      setFileError(`This file is ${Math.round(f.size / 1024 / 1024)} MB; Canon accepts files up to ${MAX_MB} MB.`)
      return
    }
    setFile(f)
    setPick('')
  }
  const refused = run.isError ? refusal(run.error) : null

  return (
    <main className="wrap">
      <Link to="/" className="back">
        &larr; Stories
      </Link>
      <h1 style={{ marginTop: 16 }}>Paste a new message and see what it breaks.</h1>
      <p className="lede">
        A Slack message, meeting notes, an email. Canon reads it, compares it with every decision Northwind has made, and tells you what it goes
        against.
      </p>

      <div className="samples">
        <span className="label">Try a sample</span>
        <div className="choices">
          {samples.map(s => (
            <button
              key={s.key}
              type="button"
              aria-pressed={pick === s.key}
              onClick={() => {
                setPick(s.key)
                setText(s.source.text)
                run.reset()
              }}
            >
              {SAMPLE_LABEL[s.key] ?? s.source.title}
            </button>
          ))}
        </div>
      </div>
      <form
        onSubmit={e => {
          e.preventDefault()
          if (text.trim() || file) run.mutate()
        }}
      >
        <textarea
          className="input"
          style={{ marginTop: 20 }}
          aria-label="Message to check"
          value={text}
          onChange={e => {
            setText(e.target.value)
            setPick('')
          }}
        />
        <div
          className={over ? 'drop over' : 'drop'}
          onDragOver={e => {
            e.preventDefault()
            setOver(true)
          }}
          onDragLeave={() => setOver(false)}
          onDrop={e => {
            e.preventDefault()
            setOver(false)
            choose(e.dataTransfer.files[0])
          }}
        >
          <input
            ref={picker}
            type="file"
            accept={ACCEPT}
            hidden
            aria-label="Upload a file"
            onChange={e => {
              choose(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <button type="button" className="btn ghost" onClick={() => picker.current?.click()}>
            Upload a file
          </button>
          <span className="small">
            {file ? (
              <>
                {file.name}, {(file.size / 1024 / 1024).toFixed(1)} MB.{' '}
                <button type="button" className="linkish" onClick={() => setFile(null)}>
                  Remove
                </button>
              </>
            ) : (
              'Or drop a file here: PDF, image, audio, video or text.'
            )}
          </span>
          <p className="small muted" style={{ margin: '8px 0 0', flexBasis: '100%' }}>
            Limits: audio up to 10 minutes, video up to 2 minutes, any file up to {MAX_MB} MB. Canon reads 30 minutes of recordings a day in total,
            for all visitors together. Text you type above goes in with the file as context.
          </p>
          {fileError && (
            <p className="small breaks" role="alert" style={{ margin: '8px 0 0', flexBasis: '100%' }}>
              {fileError}
            </p>
          )}
        </div>
        <div style={{ marginTop: 20, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="submit" className="btn" disabled={run.isPending || (!text.trim() && !file)}>
            {run.isPending ? 'Checking...' : file ? 'Check this file' : 'Check this message'}
          </button>
          <span className="small muted">Your paste stays in your own space. Other visitors do not see it.</span>
        </div>
      </form>
      <p className="progress" aria-live="polite">
        {run.isPending ? (
          <Stages n={n} file={file} />
        ) : run.data ? (
          `Read the ${file ? 'file' : 'message'}. Checked ${n ?? 'all'} decisions. Done in ${secs(run.data.latency_ms)}.`
        ) : (
          ''
        )}
      </p>

      {refused && (
        <div className="flag plain" role="alert" style={{ marginTop: 24 }}>
          <h3>Canon did not read this file.</h3>
          <p className="muted" style={{ marginTop: 6 }}>
            {refused} Nothing was sent to the model.
          </p>
        </div>
      )}
      {run.isError && !refused && <ErrorState error={run.error} retry={() => run.mutate()} title="Canon could not check this message." />}
      {run.isPending && (
        <div className="section split" role="status" aria-label="Checking the message" aria-busy="true">
          <div className="flag">
            <Bar w="70%" h={24} />
            <div className="vs">
              <Bar h={80} />
              <Bar h={80} />
            </div>
          </div>
          <div>
            <Bar w="60%" h={26} />
            <Bar h={120} style={{ marginTop: 20 }} />
          </div>
        </div>
      )}
      {run.data && <Result r={run.data} decisions={decisions.data ?? []} />}
    </main>
  )
}

/** Honest staged progress: the steps the ingest runs, advanced on a timer while the one request is in flight. */
function Stages({ n, file }: { n: number | undefined; file: File | null }) {
  const [t, setT] = useState(0)
  useEffect(() => {
    const i = setInterval(() => setT(x => x + 1), 1000)
    return () => clearInterval(i)
  }, [])
  const first = !file
    ? 'Reading the message.'
    : isMedia(file)
      ? 'Uploading the recording. Listening to it and writing a transcript.'
      : 'Uploading the file. Reading every page.'
  const steps = [first, 'Pulling out decisions and checking every quote word for word.', `Comparing with ${n ?? 'all'} decisions.`]
  return <>{steps.slice(0, Math.min(steps.length, 1 + Math.floor(t / 1.2))).join(' ')}</>
}

function Result({ r, decisions }: { r: IngestResult; decisions: Decision[] }) {
  const byId = new Map(decisions.map(d => [d.id, d]))
  const conflicts = r.alerts.filter(a => a.kind === 'contradiction' || a.kind === 'agent_violation')
  const stale = r.alerts.filter(a => a.kind === 'stale_doc')
  const premise = r.alerts.filter(a => a.kind === 'premise_changed')
  const updates = r.decisions.filter(x => x.relation === 'update' && x.related_decision_id)

  return (
    <div className="section split">
      <div>
        {conflicts.map(a => (
          <Conflict key={a.id} a={a} r={r} rule={byId.get(a.related_decision_id ?? '')} />
        ))}
        {updates.map(u => {
          const old = byId.get(u.related_decision_id ?? '')
          return (
            <div key={u.decision.id} className="flag plain" style={{ marginTop: 48 }}>
              <h3>Replaces {old ? <q>{old.statement}</q> : 'an older decision'}.</h3>
              <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>{u.explanation}</p>
              {old && (
                <p className="src">
                  Decided by {old.owner} on {fmtLong(old.ts)}.
                </p>
              )}
            </div>
          )
        })}
        {stale.map(a => (
          <Stale key={a.id} a={a} />
        ))}
        {premise.map(a => (
          <div key={a.id} className="flag plain" style={{ marginTop: 48 }}>
            <h3>
              It may change the reason behind {byId.get(a.decision_id ?? '') ? <q>{byId.get(a.decision_id ?? '')?.statement}</q> : 'a decision'}.
            </h3>
            <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>{a.explanation}</p>
          </div>
        ))}
        {conflicts.length + updates.length + stale.length + premise.length === 0 && (
          <div className="flag plain">
            <h3>Nothing on record goes against this message.</h3>
            <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>Canon saved what it found, so later messages are checked against it too.</p>
          </div>
        )}
      </div>
      <aside className="understood">
        <h2>What Canon understood</h2>
        <Transcript text={r.source.text} />
        {r.decisions.length === 0 && (
          <p className="muted" style={{ marginTop: 20 }}>
            No decision in this message. Canon kept it as context.
          </p>
        )}
        {r.decisions.map(x => (
          <dl key={x.decision.id}>
            <dt>What</dt>
            <dd>{x.decision.statement}</dd>
            <dt>Who</dt>
            <dd>{x.decision.owner}</dd>
            {x.decision.rationale && (
              <>
                <dt>Why</dt>
                <dd>{x.decision.rationale}</dd>
              </>
            )}
            {x.decision.assumptions.length > 0 && (
              <>
                <dt>Assumes</dt>
                <dd>{x.decision.assumptions.join(' ')}</dd>
              </>
            )}
            <dt>Result</dt>
            <dd className={x.relation === 'contradiction' ? 'breaks' : undefined}>{RELATION[x.relation]}</dd>
          </dl>
        ))}
        <p className="small muted" style={{ marginTop: 20 }}>
          Canon saved this as a new item{r.alerts.length ? ` and raised ${r.alerts.length === 1 ? 'one alert' : `${r.alerts.length} alerts`}` : ''}.
          {r.alerts.length ? ' A person can accept or dismiss them.' : ''}
          {r.rejected_quotes > 0
            ? ` It dropped ${r.rejected_quotes} quote${r.rejected_quotes === 1 ? '' : 's'} it could not find word for word.`
            : ''}
        </p>
      </aside>
    </div>
  )
}

function Conflict({ a, r, rule }: { a: Alert; r: IngestResult; rule: Decision | undefined }) {
  const mine = r.decisions.find(x => x.decision.id === a.decision_id)?.decision
  const newQuote = mine?.quotes[0]?.quote ?? quoteFrom(a, r.source.id)
  const old = a.quotes.find(x => x.source_id !== r.source.id)
  const oldSrc = useQuery({ ...q.source(old?.source_id ?? ''), enabled: !!old })
  return (
    <div className="flag" style={{ marginBottom: 48 }}>
      <h3>Goes against {rule ? <q>{rule.statement}</q> : 'an active decision.'}</h3>
      <div className="vs">
        <div>
          <span className="label">The new message, today</span>
          {newQuote && <blockquote>"{newQuote}"</blockquote>}
          <p className="by">{r.source.author}, pasted</p>
        </div>
        <div>
          <span className="label">The decision{rule ? `, ${fmtLong(rule.ts)}` : ''}</span>
          {old && <blockquote>"{old.quote}"</blockquote>}
          <p className="by">
            {rule?.owner}
            {oldSrc.data ? `, ${oldSrc.data.title}` : ''}
          </p>
        </div>
      </div>
      <p className="small muted" style={{ marginTop: 18 }}>
        {a.explanation} Both quotes are checked word for word against their source.
      </p>
      {rule && (
        <p className="small" style={{ marginTop: 8 }}>
          <Link to={`/decisions/${rule.id}`}>See the decision</Link>
        </p>
      )}
    </div>
  )
}

function Stale({ a }: { a: Alert }) {
  const doc = useQuery({ ...q.source(a.source_id ?? ''), enabled: !!a.source_id })
  const said = quoteFrom(a, a.source_id)
  return (
    <div className="flag plain" style={{ marginTop: 48 }}>
      <h3>
        <span className="dot hollow" aria-hidden />
        It also shows {doc.data ? `the ${doc.data.title} page` : 'a document'} is out of date.
      </h3>
      {said && (
        <>
          <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>That page still says:</p>
          <blockquote>"{said}"</blockquote>
        </>
      )}
      {doc.data && (
        <p className="src">
          {srcLine(doc.data)}. Ask {doc.data.author}, who wrote it, to update it.
        </p>
      )}
    </div>
  )
}

/** The start of what Gemini read out of an uploaded file (ingest appends it after a [transcript] or [attachment] tag). */
function Transcript({ text }: { text: string }) {
  const m = /\[(transcript|attachment)\]\n([\s\S]*)$/.exec(text)
  if (!m?.[2]) return null
  const body = m[2].trim()
  return (
    <>
      <span className="label" style={{ display: 'block', marginTop: 20 }}>
        {m[1] === 'transcript' ? 'Transcript' : 'Text in the file'}
      </span>
      <blockquote className="small">
        {body.slice(0, 400)}
        {body.length > 400 ? '...' : ''}
      </blockquote>
    </>
  )
}
