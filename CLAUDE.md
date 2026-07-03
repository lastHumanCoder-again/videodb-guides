# CLAUDE.md — how to operate this repo

This repo is a mostly-automated programmatic SEO/AEO pipeline for VideoDB. The only
non-scripted step is writing the article body — that step is YOUR job when the user asks
for new articles. Everything else is `make` targets.

## The loop

1. **Find what to write:** `SEMRUSH_KEY=... make keywords`
   → ranked list in `research/keywords_ranked.csv`, one brief per winner in `research/briefs/`.
2. **Write:** pick a brief (highest `opportunity` first). Write `blogs/<slug>.md` following
   `VIDEODB_BLOG_PLAYBOOK.md` **exactly** — §2 markdown format, §1 voice (calm, technical,
   no hype), §3 citations (6–8 real, live-verified URLs; never fabricate), §4 CTA stage,
   §5 chart spec (`chart_specs/<stem>.json`). Product facts ONLY from the playbook §0 or
   videodb.io — never invent product claims. Optionally add `image_prompts/<slug>.txt`
   (dark #0B0B0C scene, single orange #E85810 accent, no text) for a kie.ai hero.
3. **Build:** `make build` (offline, deterministic). Review `docs/<slug>.html`.
4. **Images (optional):** `KIE_API_KEY=... make images` — skips existing heroes.
5. **Publish:** `make deploy` (Pages serves `main:/docs`). If a new cluster page was added,
   also add the slug to `CLUSTERS` in `make_listing.py`.
6. **Measure:** `SEMRUSH_KEY=... make benchmark` every 2–4 weeks; report movement to the user.

## Rules

- One canonical category term per article (playbook §0); cross-link the hub
  `what-is-video-infrastructure-for-ai-agents` + 2 siblings.
- Never commit secrets. Keys are env vars only.
- Before pushing: `gh auth switch --user lastHumanCoder-again` (this machine has multiple
  GitHub accounts; pushes fail as the wrong user otherwise).
- Word count 1,600–2,000; answer-first openings; every stat cited inline.
