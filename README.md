# Nano Lens Portfolio Pulse

Single-page loan portfolio dashboard. The data is stitched into the page as compact
column arrays, so the deployed site is one static file with no backend and no external requests.

```
src/template.html   dashboard source (HTML, CSS, JS)
src/data.json       packed loan data (no phone numbers or IDs)
scripts/pack_data.py   data/*.xlsx  -> src/data.json   (only when the raw data changes)
scripts/build.py       src/*        -> public/index.html
public/index.html   built page, committed, this is what gets deployed
vercel.json         static hosting config (serves public/, noindex headers)
data/               raw workbook, git-ignored
```

## Update the dashboard
```bash
python scripts/build.py          # after editing src/template.html
python scripts/pack_data.py      # only if the workbook changed, then build again
```
Preview locally: `python -m http.server 8000 --directory public`

## Deploy
Push to GitHub, import the repo in Vercel (Framework: Other, no build command).
Vercel serves `public/` as is. Or run `npx vercel --prod` from this folder.

The site sends `X-Robots-Tag: noindex`. Add Vercel password or authentication protection
if the loan-level figures should not be public.
