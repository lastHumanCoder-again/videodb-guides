# VideoDB_PSEO — Canonical pSEO/AEO Page Pipeline

Builds **bucket A of the VideoDB one-week content sprint**: the 25 canonical site pages
(5 category explainers · 6 comparisons · 4 use-case pillars · 10 developer how-tos) that the
other ~175 pieces (Reddit, X, YouTube, guest posts, IG) link back to.

## Layout

```
VIDEODB_BLOG_PLAYBOOK.md      # THE spec — voice, format, 25-page plan, citation rules
KEYWORD_RESEARCH.md           # SEMrush findings + selection logic
keyword_research_semrush.csv  # raw SEMrush export (US db, 2026-07-03)
blogs/*.md                    # source markdown (playbook §2 format)
chart_specs/*.json            # one dark-brand chart spec per blog
assets/*.svg                  # rendered charts
site/*.html                   # built pages + index.html (deployed to GitHub Pages)
make_charts.py                # chart_specs -> assets (VideoDB dark brand)
build_html.py                 # blogs -> site (dark canvas, #E85810, Archivo Black/Inter)
make_listing.py               # site/index.html grouped by cluster
```

## Build

```bash
python3 make_charts.py && python3 build_html.py && python3 make_listing.py
```

## Brand

Dark-mode only: canvas `#0B0B0C`, cards `#141416`, accent `#E85810` (the only loud color),
text `#F4F2EE`/`#8C8C94`, hairline `#2A2A2E`. Display Archivo Black, body Inter.
Full spec: `theAIVideo-Studio/videodb-video-studio/references/BRAND.md`.
Product facts: `temp VideoDB context setting/VideoDB-Context.md` (source of truth).

## Keyword refresh

```bash
curl -sG "https://api.semrush.com/" \
  --data-urlencode "type=phrase_these" --data-urlencode "key=$SEMRUSH_KEY" \
  --data-urlencode "database=us" --data-urlencode "export_columns=Ph,Nq,Cp,Kd,Co,Nr" \
  --data-urlencode "phrase=kw1;kw2;..."
```
