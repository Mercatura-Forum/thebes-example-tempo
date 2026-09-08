# The street revamp — section 05 grows into its shoes

2026-09-08. The cast is live; this pass makes the street feel *placed* rather
than staged, and gives the runner a body that moves like one.

## Diagnosis (from an eight-vantage headless tour)

1. **The center is a void.** Every prop huddles at the edges; the middle of the
   map is a featureless sand plane bigger than the koshk corner itself.
2. **The spawn is cramped.** The runner materializes wedged between the tuk-tuk
   and the ahwa furniture — the one crowded corner of an empty map.
3. **The focus shot is half fridge-back.** The koshk close-up — the money shot
   of the whole feature — has the fridge's blank rear filling the right third
   of the frame.
4. **Everything floats.** No contact shadows anywhere; props and runner read as
   pasted onto the ground.
5. **The skyline is invisible.** The roam camera pitches ~24° down with a 36°
   fov: the horizon never enters the frame, so the Samarra minaret — placed to
   "hold the skyline" — is never seen in roam. Verified by geometry, confirmed
   by screenshots.
6. **The runner snaps.** Heading flips instantly to the velocity vector;
   reversing direction is a 180° teleport of the body.

## The fixes

### World (street_layout.json + build_street.py — rebuild street.glb + poster)

- **Roadbed.** A distinct asphalt-toned strip through the middle with sand
  aprons, a few darker repair patches and two manhole discs. The plane gets
  structure; the void gets purpose. New palette entries: `asphalt`, `asphaltOld`.
- **Spawn relocation.** Spawn moves to open ground with a clear sightline down
  the street, initial heading (spawn.face) toward the koshk. The tuk-tuk
  parallel-parks along the back sidewalk — fills the emptiest edge, un-crowds
  the ahwa corner.
- **Mid-street life.** A procedural fruit cart (wood body, two wheels, awning,
  orange blobs) near the center, collider included.
- **Edges close.** Clay planters with foliage blobs + ink bollards along the
  south rim; stacked crates + a planter close the east corner past the koshk.
  One collider strip keeps the player off the planter line.
- **Skyline.** Two procedural palms (SE corner, and between b1/b2), satellite
  dishes on three parapets, and two laundry lines with colored cloth across the
  NW corner. All of it pays off because of the camera change below.
- **Grounding.** Static soft blob-shadow discs (alpha-blended ink) under every
  prop; the runner gets a dynamic one at runtime.
- **Focus camera.** Shifted left/down-street so the fridge leaves the frame and
  the nine cans center up. The 9-cans-on-screen gate still binds.
- **Roam camera.** Offset lowered and look raised (pitch ~24°→~13°), fov 36→40:
  facades, awnings, laundry and a sky strip enter the frame. Steering
  readability is preserved (the map is shallow).

### Mechanics (street-sim.js + street.js, oracle-first)

- **turnStep(cur, target, dt, tau)** — pure shortest-arc exponential heading
  smoothing with wrap-around; the runner banks through turns instead of
  snapping. Oracle: convergence, shortest-path across ±π, dt-split exactness.
- **Entrance swoop** — the camera starts high and wide (the street, the palms
  and the minaret in one establishing breath) and glides into the roam offset.
  Pure tau schedule (swoopTau) in the sim; the same exp-follow discipline as
  everything else. The ready flag and all battery waits are unaffected.
- **Dynamic blob shadow** under the runner (radial-gradient canvas texture,
  one quad, follows position).
- **The cat answers.** Tapping the cat makes it hop and flashes «مياو!» in the
  hint for a beat. Raycast proxy like the cans; battery taps it and asserts the
  hint. No audio — the ambient-audio decision stays "silent demo" (autoplay
  policy friction for a background demo; revisit only with a user ask).

### Gates

- `verify_street_glb.py` ALLOWED grows by the new palette names (deliberate
  duplicate-literal drift discipline).
- `oracle/street.mjs`: turnStep/swoopTau tests; spawn/trigger standability
  re-checked against the new colliders automatically (they read the layout).
- `verify-street.py`: cat-tap check; swoop-settles check (progress between
  samples, never absolute-at-instant).
- Full battery + rebuild gates before deploy; box is currently quiet (load
  ~0.5), so the 10fps floor gets its clean-box re-run — clearing that backlog
  item.

## Out of scope

Ambient audio (decided silent), real-device touch pass (needs a device),
renderer shadow maps (SwiftShader fps risk not worth it against baked blobs),
new vendored assets (everything here is procedural and palette-native — no
NOTICE.md changes).

## Addendum — the street takes its own colors (same day, user call)

The flat palette-strip read as "no textures whatsoever" in close-up (user,
with screenshots). Decision reversed by the user: vendor assets now keep
their SHIPPED materials — the arab house and minaret their real texture maps
(downscaled to 512², exported WEBP inside the GLB), the tuk-tuk / chairs /
scooter / cat / fridge / table / sign their native liveries. The hand-built
geometry gets seeded Pillow textures (plaster ×3, wood grain ×2, asphalt ×2,
pavement, dirt, clay, a woven rug) mapped by world-space projection, one tile
per two metres. The RUNNER stays brand paper/ink — it is the mannequin — and
the cans keep their label art. The street palette name-lock gate retired in
favour of texture budgets (all images ≤512px, street.glb ≤2.9MB, wire ≤5MB);
the runner's brand lock stands. Composition fixed in the same pass: chairs
ring the table facing it, crates stack aligned on the koshk flank, the fridge
turns its glass to the street, the palm trunk is one lofted mesh, the koshk
grew corner posts, fascia, counter-top and shelf lips. Clay pots recolored
terracotta (their shipped material was near-black — the one native tone that
didn't survive daylight).

## Addendum 2 — nothing handmade: the found-asset pass (same day, user call)

Every hand-built model leaves the scene; found, license-verified assets take
their places (receipts + manifest + NOTICE gates as before, all via
poly.pizza CDN + ambientCG):

- fruit cart → Quaternius "Cart" (CC0) · palms → Quaternius Palm Trees ·
  south rim → Quaternius Bushes + clay pots (terracotta recolor) ·
  lamp posts → Kay Lousberg Streetlight · rooftop dishes → Poly by Google
  Satellite dish (CC-BY) · shop awnings → Poly by Google Canopy (CC-BY) ·
  facade ACs → Quaternius Air Conditioner · crates → Quaternius Crate ·
  koshk shell → Quaternius Market Stand, rotated so its OPEN long side
  serves the street (the short sides carry arch lattice), roof recolored
  TEMPO citrus. b1/b3 became arab-house instances. Laundry lines and string
  lights left the scene (no honest source found: the poly.pizza "washing
  line" is a rotary dryer; the holiday-lights file ships broken transforms).
- Pillow-noise textures retired: process_textures.py prepares ambientCG CC0
  color maps (plaster/asphalt/paving/wood/carpet/ground) — tinted, 512px.
- The runner is Quaternius "Character Animated" (CC0) in a TEMPO kit:
  citrus jersey, ink shorts, paper shoes, natural skin, white brand T-crest
  on chest and back. The jersey texture is painted onto the chest UV islands
  by mask rasterization; full lettering is impossible on this mesh (left and
  right halves share mirrored UVs — any text doubles flipped), so the
  mirror-symmetric T carries the mark; the koshk sign carries the wordmark.
  Contract preserved: clips exactly Idle/Walk/Run, height 1.82m baked into
  rest data (the import rides a ×100 armature node scale — cleared before
  the bake), feet grounded at y=0, materials brand-locked
  (runnerKit/Paper/Ink/Skin).

What remains built by the pipeline (staging, disclosed): ground/roadbed
slabs, sidewalks, the two flank-wall boxes behind the arab-house facades'
row, koshk shop fixtures (shelves, lips, glow, TEMPO sign, banner), the rug
quad, blob shadows, and Arabic signage — surfaces and fixtures, not props.
