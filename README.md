# TEMPO — an on-chain WebGL storefront

A single-page marketing site for **TEMPO**, a sample electrolyte sports-drink
brand, served entirely on-chain via [Thebes Protocol](https://thebesprotocol.com)
as certified static assets — no server, no build step, no framework.

**Live:** https://memphis.mercaturaforum.com/_/raw/59257520488477/index.html

It's a demonstration that a rich, interactive 3D experience can run as plain
hosted assets on-chain.

## Highlights

- **One 3D can, everywhere.** A single shared WebGL canvas (Three.js) renders the
  can model into every slot on the page — the hero, a pinned scroll-scrubbed
  flavour showcase, and each shop card — via per-slot scissor rectangles. In the
  hero, a frozen fluid splash (CC-BY, see NOTICE.md) wraps the can, tinted live
  to the active flavour and animated with a slow counter-orbit.
- **Scroll-driven design.** The flavour section pins and, as you scroll, the can
  spins and its label crossfades Citrus → Berry → Lime while the whole page
  re-themes. Plus a custom "scope" cursor, magnetic buttons, and mouse parallax.
- **Original brand.** Labels are generated from the site's own type system
  (Clash Display + Switzer); iconography is hand-drawn SVG; the logo doubles as
  the favicon. No stock imagery.
- **Graceful fallback.** If WebGL is unavailable, each slot shows a static render
  of the same can, and motion respects `prefers-reduced-motion`.

## Run locally

No build step. Open `index.html`, or serve the folder:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Three.js and the fonts load from public CDNs at runtime.

## Layout

| File | What it is |
|------|------------|
| `index.html` | Page structure |
| `styles.css` | All styling; flavour themes swap via `<html data-flavor>` |
| `app.js` | Content + interaction layer (scrub, cursor, cart, etc.) |
| `can3d.js` | Three.js — loads the GLB and renders it into every slot |
| `assets/` | The can model (GLB), generated labels, static fallback renders |
| `src-model/tools/` | Scripted pipeline that produces the GLB, labels and fallback renders (see its README; the third-party donor mesh itself is not redistributed — see NOTICE.md) |

## Deploy

The site is a folder of static assets deployed with `thebes-deploy`.

`thebes.toml` pins the live canister (`cid = 59257520488477`), so a deploy
updates the site **in place** — content-addressed, only changed files upload:

```sh
thebes-deploy deploy --skip-install --no-facts
```

Only set `cid = "auto"` when forking this demo to mint your own fresh canister;
never for updating an existing one.

**Asset caching:** the boundary serves `assets/*` and `*.js` with
`max-age=3600` (only `index.html` is `no-cache`). Asset URLs therefore carry a
version query (`?v=N`, referenced in `index.html`, `app.js`, `can3d.js`) —
bump it in the same commit whenever the model, labels, or renders change, or
returning visitors keep the old assets for up to an hour.

See [NOTICE.md](NOTICE.md) for asset provenance and [LICENSE](LICENSE).
