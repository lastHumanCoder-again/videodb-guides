# VideoDB pSEO — Keyword Research (SEMrush, US, 2026-07-03)

All keywords validated live against SEMrush (`type=phrase_these`, US database). Raw export:
`keyword_research_semrush.csv`. Strategy source: the Content Gap (~200 pieces) sprint doc —
this pipeline builds **bucket A: the 25 canonical videodb.io pages** everything else links to.

## Metrics
| Metric | Column | How we use it |
|---|---|---|
| Search Volume | Nq | Avg US monthly searches — demand signal |
| Keyword Difficulty | Kd (0–100) | <20 easy, 20–40 moderate, >50 hard. Favor vol × low KD |
| CPC | Cp ($) | Commercial intent |

## The headline findings

1. **The category terms are wide open.** "video understanding api", "semantic video search",
   "perception layer", "video embeddings", "video indexing", "video search api", "mux
   alternative", "gemini video api" all return **KD 0 and zero SERP competition** (Nr=0).
   Nobody owns them. First mover with a definitional page wins both the ranking and the
   LLM citation (AEO).
2. **Winnable head terms exist.** "ai video analysis" (1,000/mo, KD 25), "video content
   analysis" (880/mo, KD 34), "video search engine" (2,400/mo, KD 35), "ai video search"
   (260/mo, KD 23), "multimodal rag" (390/mo, KD 33) — real volume at moderate difficulty.
3. **Easy comparison wedges:** "ffmpeg alternative" (90/mo, **KD 16**), "video database"
   (90/mo, **KD 18**), "video moderation api" (50/mo, KD 18), "scene detection" (70/mo, KD 21),
   "live video analytics" (50/mo, KD 22), "video question answering" (40/mo, KD 22).
4. **Authority plays (harder, worth owning over time):** "vision language models" (1,300/mo,
   KD 58), "agentic rag" (3,600/mo, KD 47), "video summarizer ai" (2,900/mo, KD 59),
   "ai meeting notes" (1,600/mo, KD 73). Target with the deepest pieces; win AEO citations
   even before rankings.

## Selection logic
Same as the StoreBox/Xeni playbook: **demand (Vol) × winnability (low KD) × intent (CPC) ×
thin SERP (Nr)** — plus one VideoDB-specific rule from the sprint doc: *every page anchors one
canonical category term* (perception layer, video understanding API, video infrastructure for
agents, video RAG, agentic perception), because these pages are the AEO anchor layer.

## Top-25 page → keyword map
See `VIDEODB_BLOG_PLAYBOOK.md` §6 for the full plan (slugs, clusters, cross-links, CTA stages).
