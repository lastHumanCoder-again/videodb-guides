# VideoDB Blog Playbook — Canonical pSEO/AEO Pages (Bucket A)

Single source of truth for writing VideoDB blog markdown. Every blog follows it exactly.
Brand: `../../theAIVideo-Studio/videodb-video-studio/references/BRAND.md`.
Company facts: `../../temp VideoDB context setting/VideoDB-Context.md` (the Source of Truth —
never contradict it, never invent product facts).

---

## 0. Who VideoDB is (and the wedge)

**VideoDB is the database for continuous media** — data infrastructure for video and audio,
built so software and AI agents can ingest, index, remember, search, edit, and stream video
instead of a person watching it. It replaces the 6–8-tool "frankenstack" (S3 + ffmpeg + Mux +
Whisper + CLIP + Pinecone + Postgres + glue) with **one API, ~5 minutes to first query**.
Bring-your-own-model (Twelve Labs, Gemini, OpenAI, Anthropic, or your own). Runs managed
cloud, VPC, or edge. Four production markets: **agentic perception, real-time monitoring
(RTStream), programmable media, training data**.

**Canonical vocabulary — every page anchors exactly ONE of these terms** (the AEO rule):
*perception layer · video understanding API · video infrastructure for AI agents · video RAG ·
agentic perception · video database.* Never dilute into generic "AI video tool" language.

**The wedge:** developers searching these terms are mid-frankenstack. Teach the topic honestly;
the CTA earns itself when the page shows where VideoDB collapses 8 services into 1 API.

**Positioning lines to reuse (verbatim ok):**
- "Video has a second user now: machines." (hook)
- "Data infrastructure for video, built for machines and agents." (positioning)
- "The unit is the moment, not the file." (data model)
- "To see is to know." (sign-off)

**Numbers that are on-brand to stamp:** 82% of internet traffic is video · 10× lower total
cost (replaces 10+ vendors) · ~120ms retrieval across petabyte archives · 5 min to first
query · 1,000+ concurrent live feeds · sub-second alert latency.

---

## 1. Voice & tone

- **Audience:** a developer, ML engineer, or technical founder building with video. Address as **"you."**
- **Persona:** calm, technical, partnership-first. A staff engineer explaining architecture —
  never a marketing brochure. Lowercase-precise, declarative.
- **Rules:**
  - Answer-first: the definition/answer in the first 2 sentences of every section (LLMs lift this).
  - No exclamation marks, no "revolutionary/game-changer", no emoji.
  - Concede trade-offs honestly ("if you only need transcoding, ffmpeg alone is fine").
  - Concrete over abstract: real latencies, real vendor counts, real code.
  - **Code samples in every developer-facing piece** — Python SDK (`pip install videodb`),
    real API shapes from docs.videodb.io patterns. Keep snippets ≤20 lines, runnable-looking.
  - Every statistic cited inline to a real source (§3). US spelling.
- **Length:** 1,600–2,000 words of genuine content. Explainers must truly define the category
  (definition → how it works → architecture diagram-in-words → code → comparison table → FAQ).

## 2. Exact markdown source format

Write to `blogs/<slug>.md`:

```markdown
<!--
- Primary keyword: <kw>   (<vol>/mo · KD <kd>)
- SEO title (<=60 chars): <title — keyword near front>
- URL slug: <slug>
- Meta description (150–160 chars): <includes keyword>
- Eyebrow: <cluster label, e.g. "Category explainer" / "Developer guide">
- Read time: <N> min read
- CTA stage: <console | docs>
-->

# <H1 — includes primary keyword, human>

*<Dek: one italic sentence — who this is for / the promise.>*

<Intro ~70–110 words. Primary keyword in **bold** once. Definition up top — quotable by an LLM.>

## <H2 in question form — mirrors search intent>

<Answer-first prose. Inline citations: ... **82%** of internet traffic ([Cisco VNI](https://real-url)).>

```python
# runnable-looking VideoDB SDK snippet where relevant
```

![<descriptive alt>](<chart-stem>.svg)
*<Caption — one sentence + "Source: ...">*

> **<CTA hook — vary every time.>** <One line tied to this section's point.> [<Button label> →][cta]

## <more H2s>

## Frequently asked questions

**<PAA-style question?>**
<2–4 sentence direct answer.>

(5 FAQs.)

### <Closing takeaway headline (becomes the dark CTA box)>

<2–3 sentence close.> [<Final label> →][cta]

## Sources

- <Name> — https://real-url  (6–8 primary sources)

[cta]: https://console.videodb.io
[internal-<name>]: /blog/<sibling-slug>
```

**Notes**
- Inline `>` blockquote CTAs: **3–4 per article**, different hook each time.
- Internal links: **2–3 per body** as `[anchor ↗][internal-<name>]` to sibling slugs (§6 map),
  always including the hub `what-is-video-infrastructure-for-ai-agents` unless it IS the hub.
- One comparison table per piece where natural (LLMs love lifting tables).
- Code fences with language tag (`python`, `bash`, `json`).

## 3. Citation rules

- 6–8 primary sources per blog, every stat cited inline; verify URLs are real & live
  (WebSearch/WebFetch) before citing. Do not fabricate URLs.
- Safe first-party: https://videodb.io, https://docs.videodb.io, https://github.com/video-db
  (Director, StreamRAG, call.md, bloom, PromptClip, videodb-cookbook, ocr-benchmark…),
  https://labs.videodb.io.
- Authoritative third-party: arxiv.org (VLM/RAG papers), cloud vendor docs (AWS/GCP/Azure),
  ffmpeg.org, whisper/OpenAI docs, Pinecone/pgvector docs, ONVIF/RTSP specs (IETF RFC 7826),
  Cisco/Sandvine traffic reports, BLS where relevant, Gartner/McKinsey only with real URLs.
- VideoDB product claims (latencies, feed counts, customers CloudPhysician/Voxel/Hoichoi)
  come from the Context doc and cite videodb.io.

## 4. CTA stages

All CTAs use the `[cta]` ref. Two stages:
- **console** (default): `https://console.videodb.io` — labels rotate: "Start free in the
  console", "Get an API key", "Try VideoDB free".
- **docs** (deep-dev how-tos): `https://docs.videodb.io` — "Read the docs", "See the quickstart".
- Always mention `pip install videodb` once in dev pieces. GitHub links to the relevant repo
  count as ecosystem CTAs (not the `[cta]` button).

## 5. Chart spec (one dark-brand chart per blog)

Drop `chart_specs/<chart-stem>.json` (stem must match the `![..](<stem>.svg)` reference):

```json
{ "file": "frankenstack-vs-videodb",
  "title": "Shipping one video-AI feature: stitched stack vs. VideoDB",
  "rows": [["Stitched pipeline (8 services)", 42, "~6 weeks", false],
           ["VideoDB (1 API)", 5, "~5 min to first query", true]],
  "footnote": "Source: videodb.io.",
  "type": "bar" }
```
`type` = `"bar"` | `"donut"`. Numbers must match a cited source. Charts render dark
(canvas #0B0B0C, orange #E85810 highlight) via `make_charts.py`.

## 6. The 25-page plan (clusters, slugs, keywords, CTA stage)

Cross-link each page to ~2 siblings + the hub (#1). CTA stage in brackets.

### Cluster A — Category explainers (the anchor layer) [console]
| # | Slug | Primary keyword | Vol | KD |
|---|---|---|---|---|
|1|what-is-video-infrastructure-for-ai-agents|video infrastructure for ai agents **(HUB)**|—|—|
|2|what-is-a-video-understanding-api|video understanding api|20|0|
|3|what-is-video-rag|video rag|90|37|
|4|what-is-a-perception-layer|perception layer|20|0|
|5|how-do-ai-agents-see-and-understand-video|how do ai agents work (see video)|320|55|

### Cluster B — Comparison / build-vs-buy [console]
| # | Slug | Primary keyword | Vol | KD |
|---|---|---|---|---|
|6|videodb-vs-building-with-ffmpeg-and-a-vector-database|ffmpeg alternative|90|16|
|7|do-you-need-a-video-database|video database|90|18|
|8|build-vs-buy-video-ai-infrastructure|video api (build vs buy cost story)|1300|70|
|9|videodb-vs-running-vlms-frame-by-frame|video llm / vision language models|140–1300|34–58|
|10|semantic-video-search-vs-keyword-search|semantic video search / ai video search|20–260|0–23|
|11|video-understanding-api-alternatives|video intelligence api / mux alternative|70|39|

### Cluster C — Use-case pillars [console]
| # | Slug | Primary keyword | Vol | KD |
|---|---|---|---|---|
|12|live-camera-intelligence|ai camera monitoring / live video analytics / cctv ai|50–70|22–58|
|13|agentic-perception|video ai agents / ai agent memory|40–110|45–53|
|14|programmable-media|ai video clipping / video api|40|52|
|15|video-training-data-for-ai|ai training data (video)|590|57|

### Cluster D — Developer how-tos [docs]
| # | Slug | Primary keyword | Vol | KD |
|---|---|---|---|---|
|16|give-your-ai-agent-vision-in-5-minutes|(category how-to; video ai agents)|40|45|
|17|rtsp-stream-to-real-time-alerts|rtsp stream|880|40|
|18|search-hours-of-meetings-with-ai|ai meeting notes / meeting transcription|590–1600|73–85|
|19|replace-your-ffmpeg-pipeline|ffmpeg alternative (tutorial angle)|90|16|
|20|video-rag-tutorial|multimodal rag / video rag|390|33|
|21|desktop-capture-for-coding-agents|(Capture SDK; ai agent memory)|110|53|
|22|ai-video-analysis|ai video analysis / video content analysis|880–1000|25–34|
|23|ai-video-summarization|video summarizer ai / video to text ai|720–2900|59–62|
|24|video-content-moderation-with-ai|video moderation api / content moderation api|50–210|18–36|
|25|extract-text-from-video-ocr|extract text from video|590|59|

Pillars (C) directly feature the named production customers per market (CloudPhysician,
Voxel, WithVale · Docket, Wisdocity · Hoichoi, SVF · world-model labs) with real stats from
the Context doc. How-tos (D) each end by linking the relevant GitHub repo.

## 7. Build & preview

```bash
cd "/Users/shivanshutripathi/Desktop/programatic seo/VideoDB_PSEO"
python3 make_charts.py      # chart_specs/*.json -> assets/*.svg (dark brand)
python3 build_html.py       # blogs/*.md -> site/*.html
python3 make_listing.py     # site/index.html grouped by cluster
```
