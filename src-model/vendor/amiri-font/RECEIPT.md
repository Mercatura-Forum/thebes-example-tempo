# Vendor Receipt — Amiri (Arabic font)

**Source:** https://github.com/aliftype/amiri/releases/tag/1.003
**Fetched:** 2026-09-07
**Method:** curl of the release zip `Amiri-1.003.zip`, extracted locally

**License:** SIL Open Font License 1.1 (OFL.txt copied from the release zip)

**Files copied:**
- `Amiri-Regular.ttf`
- `OFL.txt`

**Notes:**
- Consumed by `src-model/tools/gen_signs.py` to bake the Arabic shop-sign
  textures (`مشروبات باردة`, `كشك`) that ship inside street.glb.
- OFL permits embedding/rendering; the font file itself is vendored for the
  build pipeline, not served to browsers.
