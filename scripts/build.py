"""Stitch src/template.html + src/data.json into one self-contained page.

Usage:  python scripts/build.py            -> public/index.html   (deploy this)
        python scripts/build.py --artifact -> build/artifact.html (claude.ai artifact variant)
"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
tpl = (ROOT / 'src' / 'template.html').read_text(encoding='utf-8')
data = (ROOT / 'src' / 'data.json').read_text(encoding='utf-8')
assert '/*__DATA__*/null' in tpl, 'template placeholder missing'
page = tpl.replace('/*__DATA__*/null', data)
if '--artifact' in sys.argv:
    for t in ['<!doctype html>', '<html lang="en">', '<head>', '</head>', '<body>', '</body>', '</html>',
              '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">']:
        page = page.replace(t, '', 1)
    out = ROOT / 'build' / 'artifact.html'; page = page.strip() + '\n'
else:
    out = ROOT / 'public' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(page, encoding='utf-8')
print('wrote', out.relative_to(ROOT), f'{out.stat().st_size/1e6:.2f} MB')
