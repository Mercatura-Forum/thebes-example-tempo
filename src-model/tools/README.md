# Can model pipeline

The shipped `assets/tempo-can.glb` is produced by script, never hand-edited.
Requirements: Blender 4.x on PATH, Python 3 with Pillow (labels), Playwright
(optional, live checks).

## The pipeline

```sh
# 1. Label textures: put a breathing gap between the two wrap repeats
python3 rework_labels.py            # edits assets/label_*.png IN PLACE — see caveat

# 2. Rebuild the GLB: material split + cylindrical label UVs
blender -b -P rework_can.py         # writes out/tempo-can.glb

# 3. Verify before shipping (all checks must pass)
blender -b -P verify_glb.py         # checks out/tempo-can.glb

# 4. Eyeball renders + regenerate the site's static fallbacks
blender -b -P render_views.py       # out/renders/*.png (front/¾/seam/rims/junction)
blender -b -P gen_fallbacks.py      # out/fallbacks/can_*.png (600x900, transparent)

# 5. Ship: copy out/tempo-can.glb + out/fallbacks/can_*.png into assets/,
#    bump the ?v=N asset version in index.html / app.js / can3d.js, deploy.
```

## Facts the scripts encode (learned the hard way)

- **Material names are the site contract.** `can3d.js` finds materials by name:
  `Label` (gets the flavour texture swapped at runtime) and `Metal` (silver,
  params overridden at runtime). Keep the names exact and keep `Label`'s base
  color textured, or the runtime `.map` swap stops working.
- **The label band is loop-to-loop**: vertices y 0.1088 → 1.8988 on the lathe
  profile. Below is the base ring, above is the seam trough (y=1.909), ridge and
  lid — all silver. Classification is per-vertex ("every vertex inside the
  band"), NOT per face-center: the transition rings are triangulated with
  alternating diagonals and a center test splits them into a visible sawtooth.
- **Don't trust the donor mesh's face normals.** Its winding is flipped (it
  renders correctly only via double-sided materials + custom split normals), so
  normal-direction tests select nothing. Classify by height band only.
- **UV convention**: u = 0.25 + atan2(x, z)/2π puts the site camera's front
  (+Z) at the centre of the first texture repeat; faces crossing the wrap seam
  get +1 on the low loops (three.js wraps with `RepeatWrapping`). Blender's
  exporter flips V, so v=0 at the band bottom lands image-top at the can top.
- **Labels are a one-shot transform** (`rework_labels.py`, `SCALE = 0.88`):
  it shrinks each repeat onto its flat background to create the ~22° junction
  gap. It is NOT idempotent — running it again shrinks the artwork further.
  The pristine flush-to-edge originals are in git history before commit
  `f2efd55` if you need to redo it with a different scale.
- **Fallback renders**: Cycles with `view_transform = 'Standard'` (AgX washes
  the flat label colours) and modest light energy — overexposure clips the
  citrus orange toward yellow.
