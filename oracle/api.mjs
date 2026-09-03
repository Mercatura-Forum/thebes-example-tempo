// oracle/api.mjs — drives tempo-api.js against the REAL boundary runtime with
// a scripted fetch. Run: node oracle/api.mjs  (exits nonzero on any failure)
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
let failures = 0
const check = (ok, name) => { console.log((ok ? 'ok ' : 'FAIL ') + name); if (!ok) failures++ }

// A browser-enough global for boundary.js (location + localStorage + fetch).
globalThis.window = globalThis
globalThis.location = { origin: 'http://localhost:8000' }
const store = new Map()
globalThis.localStorage = { getItem: k => store.get(k) ?? null, setItem: (k, v) => store.set(k, v), removeItem: k => store.delete(k) }

let script = [] // each entry: (url, body) => response object | Error
globalThis.fetch = async (url, opts) => {
  const step = script.shift()
  if (!step) throw new Error('unexpected fetch: ' + url)
  const body = opts && opts.body ? JSON.parse(opts.body) : null
  const r = step(String(url), body)
  if (r instanceof Error) throw r
  return { json: async () => r }
}

// Load the runtime, then the api under test (plain scripts — evaluate them).
new Function(readFileSync(join(root, 'sdk/boundary.js'), 'utf8'))()
new Function(readFileSync(join(root, 'tempo-api.js'), 'utf8'))()
const B = globalThis.EgyptBoundary
const api = globalThis.TempoAPI
api._setCid(777)

// 1 — known-vector: candid nat 5 is DIDL, empty table, one arg, type nat (0x7d), value 5.
check(B.bytesToHex(B.encodeArg({ type: 'nat', value: 5n })) === '4449444c00017d05', 'encodeArg nat known vector')

// 2 — decodeVecRecord against an INDEPENDENT candid writer (not boundary.js).
//     One row of {id: 7, name: 'Ana'}. Candid record fields encode in HASH
//     order — the value section must follow the sorted order below.
const uleb = n => { const o = []; do { let b = n & 0x7f; n >>= 7; o.push(n ? b | 0x80 : b) } while (n); return o }
const fieldHash = s => { let h = 0n; for (const b of new TextEncoder().encode(s)) h = (223n * h + BigInt(b)) & 0xffffffffn; return Number(h) }
const sleb = v => { const o = []; let n = BigInt(v); for (;;) { let b = Number(n & 0x7fn); n >>= 7n; const done = (n === 0n && !(b & 0x40)) || (n === -1n && (b & 0x40)); o.push(done ? b : b | 0x80); if (done) return o } }
const hId = fieldHash('id'), hName = fieldHash('name')
const fields = [[hId, sleb(-3)], [hName, sleb(-15)]].sort((a, b) => a[0] - b[0])
const rowParts = fields.map(([h]) => h === hId ? uleb(7) : [...uleb(3), ...new TextEncoder().encode('Ana')])
const reply = [0x44, 0x49, 0x44, 0x4c, ...uleb(2),
  ...sleb(-20), ...uleb(2), ...fields.flatMap(([h, t]) => [...uleb(h), ...t]),
  ...sleb(-19), ...sleb(0),
  ...uleb(1), ...sleb(1),
  ...uleb(1), ...rowParts.flat()]
const rows = B.decodeVecRecord(reply.map(b => b.toString(16).padStart(2, '0')).join(''), [{ name: 'id', type: 'nat' }, { name: 'name', type: 'text' }])
check(rows.length === 1 && rows[0].id === 7n && rows[0].name === 'Ana', 'decodeVecRecord vs independent writer')

// 3 — fetchSkus: sends a query for skusView and rejects on transport failure.
script = [(url, body) => { check(url.endsWith('/api/query') && body.method === 'skusView' && body.canister_id === 777, 'skusView query shape'); return new Error('down') }]
let threw = false
await api.fetchSkus().catch(() => { threw = true })
check(threw, 'fetchSkus rejects when the boundary is down (fallback path)')

// 4 — castVote success: call → message_hash, receipt → success + bool-true reply.
script = [
  (url, body) => { check(url.endsWith('/api/call') && body.method === 'castVote' && body.arg === '4449444c00017d02', 'castVote sends nat 2'); return { message_hash: 'aa' } },
  url => { check(url.includes('/api/receipt'), 'castVote polls the receipt'); return { status: 'success', reply_hex: '4449444c00017e01' } },
]
check(await api.castVote(2) === true, 'castVote resolves true on success receipt')

// 5 — castVote refused before acceptance: no message_hash ⇒ safeToRetry.
script = [() => ({ error: 'refused' })]
let err = await api.castVote(1).catch(e => e)
check(err instanceof Error && err.safeToRetry === true, 'no message_hash is resubmit-safe')

// 6 — receipt timeout ⇒ mayHaveLanded, never auto-resubmitted (exactly ONE /api/call).
let calls = 0
script = [
  () => { calls++; return { message_hash: 'bb' } },
  ...Array.from({ length: 50 }, () => () => ({ status: 'pending' })),
]
err = await api.castVote(1, { timeoutMs: 400 }).catch(e => e)
check(err instanceof Error && err.mayHaveLanded === true && calls === 1, 'timeout marks mayHaveLanded, no auto-resubmit')

// 7 — checkAdmin sends the token as a text arg and decodes the bool reply.
script = [
  (url, body) => { check(body.method === 'checkAdmin', 'checkAdmin method name'); return { message_hash: 'cc' } },
  () => ({ status: 'success', reply_hex: '4449444c00017e01' }),
]
check(await api.checkAdmin('deadbeef') === true, 'checkAdmin round-trips')

// 8 — whoAmI decodes a text reply ("2vxsx-fae" here) from the fixed shape.
const who = '2vxsx-fae'
const whoBytes = [0x44, 0x49, 0x44, 0x4c, 0x00, 0x01, 0x71, who.length, ...new TextEncoder().encode(who)]
script = [
  (url, body) => { check(body.method === 'whoAmI', 'whoAmI method name'); return { message_hash: 'dd' } },
  () => ({ status: 'success', reply_hex: whoBytes.map(b => b.toString(16).padStart(2, '0')).join('') }),
]
check(await api.whoAmI('deadbeef') === who, 'whoAmI decodes the text reply')

process.exit(failures ? 1 : 0)
