# VideoDB pSEO Pipeline

A mostly-automated programmatic SEO + AEO pipeline. It finds the keywords worth writing
for, generates an article brief for each, turns playbook-formatted markdown into branded,
schema-marked pages, and measures whether they rank. **Live output:**
[lasthumancoder-again.github.io/videodb-guides](https://lasthumancoder-again.github.io/videodb-guides/) —
25 canonical pages shipped with this exact pipeline.

## How automated is it?

| Step | Automation | Command |
|---|---|---|
| Keyword discovery + scoring + briefs | **Fully scripted** (SEMrush API) | `make keywords` |
| Writing the article | **LLM-assisted** — a brief + playbook is the full spec; Claude Code does this end-to-end via `CLAUDE.md` | see below |
| Charts (dark-brand SVG) | Fully scripted | `make build` |
| HTML pages (TOC, FAQ accordion, key-insights, 3× JSON-LD) | Fully scripted | `make build` |
| Listing / index page | Fully scripted | `make build` |
| Hero images (kie.ai nano-banana-pro) | Fully scripted | `make images` |
| Deploy (GitHub Pages) | One command | `make deploy` |
| Rank benchmarking | Fully scripted | `make benchmark` |

The one human/LLM step is the article body itself — deliberately. Thin generated content
is the thing this pipeline exists to beat; the playbook forces real citations, real code,
and honest comparisons. In practice: open this repo in Claude Code and say
*"write the top 3 briefs"* — `CLAUDE.md` teaches it the whole loop.

## Quickstart (anyone can run this)

```bash
git clone https://github.com/lastHumanCoder-again/videodb-guides && cd videodb-guides
pip install markdown pillow

export SEMRUSH_KEY=...                  # 1. find what to write
make keywords                           #    -> research/keywords_ranked.csv + research/briefs/*.md

# 2. write blogs/<slug>.md per VIDEODB_BLOG_PLAYBOOK.md (or let Claude Code do it)

make build                              # 3. md -> charts -> pages -> index (offline)
export KIE_API_KEY=... && make images   # 4. optional branded hero images
make deploy                             # 5. push; Pages serves main:/docs
make benchmark                          # 6. are we ranking yet?
```

Everything is configured in `pipeline.config.json` (seeds, relevance filters, scoring
knobs, brand constants). Secrets are env vars only — nothing in the repo.

## How keywords are chosen (the benchmark for "worth writing")

`find_keywords.py` expands every seed via SEMrush `phrase_related` + `phrase_questions`,
filters for topical relevance (regex allow/deny lists in config), then ranks by:

```
opportunity = volume^0.6 × intent × winnability² × serp_bonus

volume^0.6     demand with diminishing returns (10× volume ≠ 10× value)
intent         1 + min(CPC,10)/10 — advertisers bidding = buyers searching
winnability²   ((100−KD)/100)² — difficulty punished quadratically; KD16 ≫ KD58
serp_bonus     1.5× if the SERP has ZERO results, 1.2× if <1M (thin SERP = land grab)
```

Interpretation bands (validated on this project's own data):
- **KD < 20 — write first.** e.g. "ffmpeg alternative" (90/mo, KD16), "video database"
  (90/mo, KD18). Expect top-10 within 4–8 weeks of indexing.
- **KD 20–40 — the core pipeline.** e.g. "ai video analysis" (1,000/mo, KD25),
  "multimodal rag" (390/mo, KD33). Expect 3–6 months.
- **KD > 40 — authority/AEO plays.** e.g. "vision language models" (1,300/mo, KD58).
  You won't outrank incumbents fast; you CAN become the page LLMs cite. Judge these by
  AI-citation checks, not SERP position.
- **Zero-SERP category terms — own them immediately.** "video understanding api",
  "perception layer", "semantic video search" all had KD 0 and literally zero results.
  A definitional page wins the ranking AND the LLM training/citation surface.

Every brief in `research/briefs/` carries these numbers so the decision is transparent.

## How to benchmark published articles

`make benchmark` checks the live top-10 SERP for every article's primary keyword
(SEMrush `phrase_organic`), reports our position or who owns the SERP, and refreshes
volume/KD → `research/benchmark.csv`. Run every 2–4 weeks.

Beyond SERP position, track:
1. **Google Search Console** — impressions before clicks; a page gaining impressions
   for its keyword cluster is working even at position 20.
2. **AEO spot-checks** — ask ChatGPT/Claude/Perplexity the article's H2 questions;
   log whether videodb.io is cited. This is the actual goal for KD>40 pages.
3. **Kill/iterate rule** — a KD<20 page not in the top 20 after 8 weeks has a content
   problem, not a keyword problem: deepen it (more specific data, better tables) rather
   than writing more pages.

## Layout

```
pipeline.config.json          seeds, relevance filters, scoring knobs, brand constants
find_keywords.py              discovery -> scoring -> research/briefs/*.md
VIDEODB_BLOG_PLAYBOOK.md      THE writing spec — voice, exact md format, citations, 25-page plan
KEYWORD_RESEARCH.md           the original validated keyword analysis
blogs/*.md                    article sources (playbook §2 format)
chart_specs/*.json            one dark-brand chart per article -> make_charts.py -> assets/*.svg
image_prompts/*.txt           hero prompts -> gen_images.py -> _incoming_assets/*.jpg
build_html.py                 md -> docs/*.html (brand CSS, JSON-LD, FAQ, TOC, code blocks)
make_listing.py               docs/index.html grouped by cluster (image cards)
benchmark.py                  live SERP position per published article
CLAUDE.md                     lets Claude Code run this entire loop autonomously
docs/                         the built site — GitHub Pages serves this
```

## Brand

Dark-mode only: canvas `#0B0B0C`, cards `#141416`, accent `#E85810` (the only loud color),
text `#F4F2EE`/`#8C8C94`, Archivo Black display + Inter body. Voice: calm, technical,
answer-first, no hype. Product facts from videodb.io only. *To see is to know.*
