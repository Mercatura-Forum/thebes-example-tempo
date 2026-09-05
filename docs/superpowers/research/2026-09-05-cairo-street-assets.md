# Cairo street — 3D asset research (license-verified)

Researched 2026-09-05 (deep-research workflow: 5 angles, 22 sources, 25 claims
adversarially verified 3-vote, 3 refuted; plus a targeted second pass on
architecture, packs and props). Every license below was read on the source
page or Sketchfab's API (`api.sketchfab.com/v3/models/<uid>` license slug) on
2026-09-05 — not assumed. Constraint recap: public repo + public site, so
CC0 preferred, CC-BY accepted with NOTICE.md credit; Sketchfab Standard /
Fab / Synty / NC / ND / SA all disqualified; scene budget ~5MB, flat-shaded
low-poly, GLB via Blender 4.0 + draco.

## Character (SOLVED, all-CC0)

- **BEST: KayKit Character Pack: Adventurers** — Kay Lousberg, CC0
  ("no attribution required"), rigged, FBX/glTF + ready GLBs on the official
  GitHub mirror. https://kaylousberg.itch.io/kaykit-adventurers
- **+ KayKit Character Animations** — CC0, 150+ clips, list explicitly has
  Idle/Walk/Run; targets KayKit rigs. FBX/glTF, free tier is the full CC0 set.
  https://kaylousberg.com/game-assets/character-animations
- Runner-up: **Quaternius Universal Base Characters + Universal Animation
  Library** (both pages still CC0-labeled; jog/sprint clips). CAVEAT
  (refuted claim): the FREE character tier does NOT include glTF — the full
  rigged glTF/FBX/.blend set is the $19.99 Source tier.
- Paid fallback: **Kenney Character Assets** (CC0, 4 rigged, 17 anims incl.
  idle/run/walk) — standalone listing currently unpurchasable; lives in the
  Kenney All-in-1 bundle (~$19.95). Kenney logo is trademarked — never use it.
- **DISQUALIFIED: Mixamo.** Adobe's FAQ grants project use only; zero
  language about redistributing raw files, and even the permissive-use
  reading failed adversarial verification (1-2). Never commit Mixamo-derived
  FBX/GLB to this repo. Do not re-litigate.

## Architecture (Cairo street fabric)

- **Kenney Fantasy Town Kit v2.0** — CC0, 160 modular pieces (walls, arched
  doors/windows, awnings, market stalls, carts, light posts), GLB included.
  The facade kitbash backbone — recolor timber/plaster to sand/ochre.
  https://kenney.nl/assets/fantasy-town-kit
- **Kenney City Kit Commercial** — CC0, 50 models: storefronts, awnings,
  signs — the koshk/newsstand + modern-Cairo shopfront layer.
  https://kenney.nl/assets/city-kit-commercial
- **Arab House (low poly)** — Legorook, Sketchfab, CC-BY 4.0 (API slug
  `by`), 14k faces — the authentic hero facade with Islamic detailing.
  https://sketchfab.com/3d-models/arab-houselow-poly-a49323aa1e0f450db9ff8b813864379f
- **The Minaret of Samarra** — Chenzoss, Sketchfab, CC-BY, 40k faces —
  spiral-malwiya skyline piece (Ibn Tulun family). Lighter alt: Minaret V2,
  1shxxn, CC-BY, 19.6k. https://sketchfab.com/3d-models/the-minaret-of-samarra-iraq-d8ebe7c756f2414bb70768d936f2d137
- **Quaternius Market Stalls family + AC units + clay pots** — CC0 on their
  poly.pizza pages (2022-era, pre-QAL): stalls `/m/PUZZ5F91OE` etc., AC
  `/m/amFuyE3IF6`, pots `/m/Olu4b0aiiY`.
- **mashrabiya** — Mennasalama, Sketchfab, CC-BY, 129k faces — hero balcony
  ONLY after hard decimation (or bake lattice to alpha).
- Kitbash source (heavy): "Arabic+city" — 3laa.alrfooh, CC-BY, 174k tris —
  decimate/kitbash only. Background filler: "Little Desert Town" — John
  Landfair, poly.pizza, CC-BY 3.0.

## Props (best-pick table)

| need | pick | license | tris | credit? |
|---|---|---|---|---|
| cat | Quaternius Cat (animated) poly.pizza/m/2f54vbV0In | CC0 | 1.7k | no |
| tuk-tuk | maanzart "Tuk Tuk Auto Rikshaw Lowpoly" (Sketchfab 2124df89…) | CC-BY | 3.7k | yes |
| scooter | spartanmelon "Low Poly Delivery Electric Scooter" (16a3330e…) | CC-BY | 3.6k | yes |
| crates | Quaternius Crate /m/3OEFd1AWfa + KayKit Crate of Potatoes /m/L0Qt7KT6AD | CC0 | ~1.9k | no |
| fanous | ahmed.mohsin.atia "Ramadan Lantern Model" (ba9aa258…) | CC-BY | 1.7k | yes |
| string lights | googoobie "String Lights" (996e758d…) or keep our procedural ones | CC-BY | 1.3k | yes |
| ahwa chair | thelatestshit "Monoblok Garden Chair" (898f2dc1…) | CC-BY | 594 | yes |
| cafe table | Kenney Round Table poly.pizza/m/AXbvcMDC8j | CC0 | 160 | no |
| drinks fridge | **Quaternius Can Fridge** poly.pizza/m/8OHbykvREu — glass-front can fridge, the ahwa classic | CC0 | 2.8k | no |
| signage | iPoly3D Wooden Sign /m/AsEgIQcQfw + our own Arabic texture | CC0 | 296 | no |
| zeer/pots | KayKit pots (CC0) or Bruno Oliveira Amphora /m/7Q8MkXjALbL (CC-BY 3.0) | mixed | <500 | amphora only |

All best-pick props together ≈ 14.4k tris — negligible in the 5MB budget.

## Licensing rules of the road (record-keeping)

1. **CC-BY entries in NOTICE.md** need: title, author, source URL, license
   URL, and a modifications note — decimation AND draco recompression both
   count as modifications. (Existing NOTICE.md already does this for the
   CC-BY splash.)
2. **Quaternius QAL v1.0 (2026-08-28)**: new non-CC0 license banning
   standalone redistribution; NON-retroactive. Older packs still show CC0 —
   screenshot/archive the CC0-labeled page at download time, and never pull
   a NEW Quaternius pack without re-checking.
3. **poly.pizza's per-model label governs the file downloaded there** — it
   sometimes differs from the author's site (Quaternius Pug shows CC-BY
   there). Read each model page.
4. **Sketchfab licenses are uploader-declared** (platform doesn't verify
   ownership) — small takedown risk on all Sketchfab items; keep the
   download receipts.
5. poly.pizza Google-Poly rescues are **CC-BY 3.0** (not 4.0) — same
   attribution mechanics.

## Disqualified — do not re-litigate

Mixamo raw files (redistribution unsettled); Voxel Desert Town (CC-BY-**ND**);
PolyForm eastern-low-poly (no license text at all); assetfactory Mosque
(Sketchfab Standard); mrigua Moroccan set (CC-BY but ~1.5M faces, AI-gen);
SJoudeh "Cairo street Elements" (5.3M faces); juanbrualla Al-Aqmar
(1.65M photogrammetry); gomnosano Arabic House (CC-BY-**SA**); all
GDH/ICRC heritage scans (**NC** variants); any Quaternius pack released
after 2026-08-28 (QAL).

## Open items for the integration session

- Verify KayKit run/walk clips retarget onto the chosen character in
  Blender 4.0, and whether cycles are in-place or root-motion (bake out
  root motion for our sim-driven runner).
- Check as-downloaded texture sizes on the three Sketchfab picks (API
  doesn't expose archive bytes).
- Kenney Holiday Kit page doesn't confirm string lights — inspect the
  download, else keep our procedural catenary lights.
- No redistributable Arabic shop-lettering signage exists — bake our own
  Arabic sign textures in the pipeline (better for authenticity anyway).
