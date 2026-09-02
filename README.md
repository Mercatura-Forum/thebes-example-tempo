# TEMPO — an on-chain WebGL storefront

A single-page site for **TEMPO**, a sample Egyptian sports-drink brand, served fully
on-chain via [Thebes Protocol](https://thebesprotocol.com) as certified static
assets. No server, no build step, no framework.

**Live:** https://memphis.mercaturaforum.com/_/raw/59257520488477/index.html

## What's in it

- One shared Three.js canvas renders the 3D can into every slot on the page:
  the hero, the scroll-scrubbed flavour showcase, and the shop cards.
- In the hero the can leans inside a frozen water splash, tinted live to the
  active flavour.
- Scrolling the flavour section spins the can and re-themes the whole page:
  Citrus → Berry → Lime.
- No WebGL? Every slot falls back to a static render. Motion respects
  `prefers-reduced-motion`.

## Run locally

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

Three.js and the fonts load from public CDNs.

## Files

| File | Role |
|------|------|
| `index.html` | Page structure |
| `styles.css` | Styling; flavour themes swap via `<html data-flavor>` |
| `app.js` | Content and interactions |
| `can3d.js` | Three.js — loads the models, renders every slot |
| `assets/` | Can + splash models, labels, fallback renders |
| `src-model/tools/` | Pipeline that builds the models, labels and renders (see its README) |
| `dist/` | Plain copy of the site files — this is what deploys |

## Deploy

`thebes.toml` pins the live canister (`cid = 59257520488477`), so a deploy
updates the site in place — only changed files upload:

```sh
cp <changed files> dist/
thebes-deploy deploy --skip-install --no-facts
```

Two rules:

- Keep the pinned `cid`. Setting `cid = "auto"` mints a NEW canister — only do
  that when forking this demo.
- Assets are cached for an hour, so bump the `?v=N` query on whatever changed
  (`index.html` versions the js/css; `app.js`/`can3d.js` version the models and
  images) in the same commit. Skip it and returning visitors see the old site
  for up to an hour.

Asset provenance: [NOTICE.md](NOTICE.md) · License: [LICENSE](LICENSE)
