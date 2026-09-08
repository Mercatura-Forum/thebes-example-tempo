# check_attribution.py — no credit, no ship. Every CC-BY vendor source that a
# layout ref actually casts into the scene must have a NOTICE.md line carrying
# its title AND author AND source URL. Exits 1 on any missing credit.
# Run: python3 src-model/tools/check_attribution.py
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')

man = json.load(open(os.path.join(VENDOR, 'manifest.json')))['sources']
layout = json.load(open(os.path.join(HERE, 'street_layout.json')))
notice = open(os.path.join(ROOT, 'NOTICE.md'), encoding='utf-8').read()

refs = set()
for vp in layout.get('vendorProps', []):
    refs.add(vp['ref'])
for b in layout.get('buildings', []):
    if b.get('ref'): refs.add(b['ref'])
mn = layout.get('props', {}).get('minaret', {})
if mn.get('ref'): refs.add(mn['ref'])

used_dirs = {r.split(':', 1)[1].split('/', 1)[0] for r in refs}
# the runner ships from these too, even though street_layout doesn't ref them
used_dirs |= {'kaykit-adventurers', 'kaykit-animations'}
# the sign textures bake the Amiri font into street.glb
used_dirs |= {'amiri-font'}

fails = 0
def check(ok, name):
    global fails
    print(('ok   ' if ok else 'FAIL ') + name)
    if not ok: fails += 1

for d in sorted(used_dirs):
    meta = man.get(d)
    check(meta is not None, f'{d}: manifest entry exists')
    if not meta: continue
    if meta['license'].startswith('CC-BY'):
        for field in ('title', 'author', 'url'):
            check(meta[field] in notice, f"{d}: NOTICE.md carries {field} ({meta[field]})")
    elif meta['license'] == 'OFL':
        check(meta['title'] in notice, f"{d}: NOTICE.md mentions {meta['title']} (OFL)")

sys.exit(1 if fails else 0)
