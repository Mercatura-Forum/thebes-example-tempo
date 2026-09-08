# src-model/tools/check_vendor.py — manifest ↔ disk consistency for vendored assets.
# Run: python3 src-model/tools/check_vendor.py   (exit 1 on any failure)
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, '..', 'vendor')
ALLOWED = {'CC0', 'CC-BY-4.0', 'CC-BY-3.0', 'OFL'}

fails = 0
def check(ok, name):
    global fails
    print(('ok   ' if ok else 'FAIL ') + name)
    if not ok: fails += 1

man = json.load(open(os.path.join(VENDOR, 'manifest.json')))
for src, meta in man['sources'].items():
    d = os.path.join(VENDOR, src)
    check(os.path.isdir(d), f'{src}: directory exists')
    check(os.path.isfile(os.path.join(d, 'RECEIPT.md')), f'{src}: RECEIPT.md present')
    check(meta.get('license') in ALLOWED, f"{src}: license {meta.get('license')} allowed")
    if meta.get('license') != 'CC0':
        check(all(meta.get(k) for k in ('title', 'author', 'url', 'licenseUrl')),
              f'{src}: CC-BY attribution fields complete')
    for f in meta['files']:
        check(os.path.isfile(os.path.join(d, f)), f'{src}/{f}: file present')
        check('mixamo' not in f.lower(), f'{src}/{f}: not a mixamo file')
sys.exit(1 if fails else 0)
