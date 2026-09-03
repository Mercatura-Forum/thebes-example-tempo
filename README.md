# TEMPO — a Thebes Protocol example: an on-chain WebGL storefront

A single-page site for **TEMPO**, a sample Egyptian sports-drink brand, served fully
on-chain via [Thebes Protocol](https://thebesprotocol.com) as certified static
assets — with a Motoko backend contract behind it. No server, no build step, no
framework: the whole SDK integration is two vendored runtime scripts.

**Live:** https://memphis.mercaturaforum.com/_/raw/59257520488477/index.html

## What this example proves

**A recountable poll.** The "next flavour" vote lives on the contract. One
boundary identity holds one standing vote — a revote replaces it, never adds —
so the ledger identity

    sum(per-candidate tallies) == number of distinct voters

is recomputable by ANYONE at ANY time via the public `recountView` query. There
are no counters to trust: every read recomputes the equality from the votes map
itself, and the page prints the result under the poll.

**Honest hydration.** The static page is the fallback and the initial paint.
Prices, stock badges, stockists and the poll hydrate in place when the chain
answers; if it doesn't, the full site still works — no spinners, no blank
states, no layout shift.

## The no-build SDK story

Every other Thebes example is a React + Vite app on `@thebes/sdk`. This one
consumes the SAME SDK with no toolchain at all:

- `sdk/boundary.js` — the SDK's browser runtime (`window.EgyptBoundary`):
  Candid encode/decode, query calls, update calls with receipt polling.
- `sdk/passkey.js` — Memphis passkey sign-in (`window.MemphisPasskey`).
- `tempo-api.js` — this site's typed verbs over the runtime, ~100 lines of
  plain JS. That is the entire integration.

Write-safety semantics the API surfaces (the boundary's own rules): a call
that returned **no `message_hash` was never accepted** — safe to resubmit; a
**receipt timeout may have landed** — never auto-resubmitted, the UI says
"may still land".

## What's in it

- One shared Three.js canvas renders the 3D can into every slot on the page:
  the hero, the scroll-scrubbed flavour showcase, and the shop cards.
- In the hero the can leans inside a frozen water splash, tinted live to the
  active flavour.
- Scrolling the flavour section spins the can and re-themes the whole page:
  Citrus → Berry → Lime.
- The shop, the stockists map and the next-flavour poll read from the contract.
- No WebGL? Every slot falls back to a static render. Motion respects
  `prefers-reduced-motion`.

## Admin

Open `#admin` on the live site. Sign-in is a Memphis passkey ceremony, which
works **only on the memphis origin** (WebAuthn RP_ID binding). Authority is
checked on-chain: the panel mints an origin-scoped session token and every
admin method verifies it with the Memphis contract (`thebes-lib`'s
`MemphisAuth`), keying rights to the derived per-app principal — the passkey
gate is load-bearing, not cosmetic. The first verified identity claims
ownership; owners can add further admins by principal (shown in the panel).

## Run locally

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

Three.js and the fonts load from public CDNs. Chain hydration needs the
deployed contract; locally (or with the chain unreachable) the site runs on
its built-in fallback content.

## Tests

```sh
node oracle/api.mjs        # the client verbs against the real runtime, scripted fetch
cd motoko && mops install && \
  "$HOME/.cache/mops/moc/1.4.1/moc" -r $(mops sources) test/units.test.mo   # pure modules
```

## Files

| File | Role |
|------|------|
| `index.html` | Page structure |
| `styles.css` | Styling; flavour themes swap via `<html data-flavor>` |
| `app.js` | Content, interactions, chain hydration |
| `can3d.js` | Three.js — loads the models, renders every slot |
| `tempo-api.js` | Typed verbs over the SDK runtime |
| `admin.js` | The `#admin` drawer (Memphis passkey) |
| `sdk/` | Vendored SDK runtime scripts (see NOTICE.md) |
| `motoko/` | The contract: `main.mo`, pure `Poll`/`Hex` modules, vendored `thebes-lib` |
| `oracle/` | Node test scripts |
| `assets/` | Can + splash models, labels, fallback renders |
| `src-model/tools/` | Pipeline that builds the models, labels and renders (see its README) |
| `dist/` | Plain copy of the site files — this is what deploys |

## Deploy

`thebes.toml` pins the live frontend (`cid = 59257520488477`) and the backend
contract, so a deploy updates both in place — only changed files upload:

```sh
cp <changed files> dist/        # dist mirrors the site files
thebes-deploy deploy --skip-install --no-facts
```

Rules:

- Keep the pinned `cid`s. `cid = "auto"` mints a NEW canister on the next
  deploy (and writes the minted id back) — only do that when forking this demo.
- Assets are cached for an hour, so bump the `?v=N` query on whatever changed
  (`index.html` versions the js/css; `app.js`/`can3d.js` version the models and
  images) in the same commit. Skip it and returning visitors see the old site
  for up to an hour.
- After changing `motoko/`, the deploy rebuilds `build/tempo.wasm` via the
  `build` line in `thebes.toml` (moc 1.4.1 through mops).

Asset provenance: [NOTICE.md](NOTICE.md) · License: [LICENSE](LICENSE)
