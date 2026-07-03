#!/usr/bin/env python3
"""Keyword discovery + opportunity scoring for the VideoDB pSEO pipeline.

For every seed in pipeline.config.json this pulls SEMrush related keywords and
question keywords, filters them for topical relevance, scores each one on an
opportunity formula (demand x intent x winnability x thin-SERP), and emits:

  research/keywords_ranked.csv     every surviving keyword, scored & ranked
  research/briefs/<slug>.md        an article brief for each of the top N

The brief + VIDEODB_BLOG_PLAYBOOK.md is everything a writer (human or LLM)
needs to produce a publishable page.

Usage:
  export SEMRUSH_KEY=...
  python3 find_keywords.py                 # full run (costs SEMrush API units)
  python3 find_keywords.py --seeds "video ocr" "meeting ai"   # override seeds
  python3 find_keywords.py --rescore       # re-rank from cached CSV, no API calls

Unit cost note: phrase_related ~40 units/row, phrase_questions ~40 units/row,
phrase_these 10 units/row. Default config (~12 seeds x 45 rows) is ~20k units.
"""
import csv, json, math, os, re, subprocess, sys, pathlib
from urllib.parse import urlencode

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / "pipeline.config.json").read_text())
OUT = ROOT / "research"; BRIEFS = OUT / "briefs"
OUT.mkdir(exist_ok=True); BRIEFS.mkdir(exist_ok=True)
KEY = os.environ.get("SEMRUSH_KEY", "").strip()
DB = CFG["semrush"]["database"]

EXISTING = {p.stem for p in (ROOT / "blogs").glob("*.md")}

def semrush(qtype, phrase, columns, limit, sort=None):
    params = {"type": qtype, "key": KEY, "database": DB, "phrase": phrase,
              "export_columns": columns, "display_limit": str(limit)}
    if sort: params["display_sort"] = sort
    url = "https://api.semrush.com/?" + urlencode(params)
    raw = subprocess.check_output(["curl", "-sG", url], timeout=60).decode("utf-8", "replace")
    rows = []
    lines = raw.strip().splitlines()
    if not lines or "ERROR" in lines[0]:
        return rows
    for ln in lines[1:]:
        parts = ln.split(";")
        if len(parts) >= 2: rows.append(parts)
    return rows

def relevant(kw):
    r = CFG["relevance"]
    if any(re.search(p, kw) for p in r["exclude"]): return False
    if not any(re.search(p, kw) for p in r["must_match_any"]): return False
    return any(re.search(p, kw) for p in r["must_also_match_any"])

def to_f(x, default=0.0):
    try: return float(x)
    except (ValueError, TypeError): return default

def score(nq, cp, kd, nr):
    """Opportunity score. Documented in README §How keywords are chosen."""
    if nq <= 0: return 0.0
    demand = nq ** 0.6                          # diminishing returns on raw volume
    intent = 1 + min(cp, 10) / 10               # CPC as a commercial-intent proxy (1x..2x)
    winnability = ((100 - kd) / 100) ** 2       # KD punishes hard terms quadratically
    serp_bonus = 1.5 if nr == 0 else (1.2 if 0 < nr < 1_000_000 else 1.0)  # thin SERP
    return round(demand * intent * winnability * serp_bonus, 2)

def classify(kw):
    if re.search(r"\b(vs|versus|alternative|alternatives|best|comparison|compare)\b", kw): return "comparison"
    if re.search(r"^(how|what|why|when|which|can|does|do|is|are)\b", kw): return "explainer"
    if re.search(r"\b(how to|tutorial|build|create|make|setup|set up|guide)\b", kw): return "how-to"
    return "guide"

def slugify(kw):
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:70]

def kd_band(kd):
    if kd < CFG["scoring"]["kd_easy"]: return "easy"
    if kd < CFG["scoring"]["kd_moderate"]: return "moderate"
    return "hard"

def discover(seeds):
    seen = {}
    for seed in seeds:
        print(f"  seed: {seed}")
        rows = semrush("phrase_related", seed, "Ph,Nq,Cp,Kd,Co,Nr",
                       CFG["semrush"]["related_per_seed"], sort="nq_desc")
        rows += semrush("phrase_questions", seed, "Ph,Nq,Cp,Kd,Co,Nr",
                        CFG["semrush"]["questions_per_seed"])
        rows += semrush("phrase_these", seed, "Ph,Nq,Cp,Kd,Co,Nr", 1)  # the seed itself
        for p in rows:
            kw = p[0].strip().lower()
            if kw in seen or not relevant(kw): continue
            nq, cp = to_f(p[1]), to_f(p[2])
            kd = to_f(p[3], 50.0)
            nr = to_f(p[5]) if len(p) > 5 else 1e9
            seen[kw] = {"keyword": kw, "volume": int(nq), "cpc": cp, "kd": int(kd),
                        "results": int(nr), "seed": seed,
                        "opportunity": score(nq, cp, kd, nr),
                        "format": classify(kw), "kd_band": kd_band(kd),
                        "already_written": slugify(kw) in EXISTING}
    return sorted(seen.values(), key=lambda r: -r["opportunity"])

def write_csv(rows):
    p = OUT / "keywords_ranked.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n{len(rows)} keywords -> {p}")

def write_briefs(rows):
    n = 0
    for r in rows:
        if r["already_written"] or r["opportunity"] <= 0: continue
        if n >= CFG["scoring"]["top_n_briefs"]: break
        slug = slugify(r["keyword"])
        brief = f"""# Article brief — {r['keyword']}

| | |
|---|---|
| Primary keyword | **{r['keyword']}** |
| Volume (US/mo) | {r['volume']} |
| Keyword difficulty | {r['kd']} ({r['kd_band']}) |
| CPC (intent) | ${r['cpc']} |
| SERP results | {r['results'] or 'ZERO — wide open'} |
| Opportunity score | {r['opportunity']} |
| Suggested format | {r['format']} |
| Suggested slug | `{slug}` |
| Discovered via seed | {r['seed']} |

## What to do
1. Write `blogs/{slug}.md` following **VIDEODB_BLOG_PLAYBOOK.md §2** exactly
   (voice §1, citations §3, CTA stage §4, one chart spec §5).
2. Anchor ONE canonical category term; cross-link 2–3 siblings + the hub.
3. Drop `chart_specs/<stem>.json`; optionally `image_prompts/{slug}.txt` for a hero.
4. Build: `make build` — then review `docs/{slug}.html` locally before deploying.
"""
        (BRIEFS / f"{slug}.md").write_text(brief)
        n += 1
    print(f"{n} article briefs -> {BRIEFS}")

def main():
    args = sys.argv[1:]
    if "--rescore" in args:
        p = OUT / "keywords_ranked.csv"
        rows = list(csv.DictReader(p.open()))
        for r in rows:
            r["opportunity"] = score(to_f(r["volume"]), to_f(r["cpc"]), to_f(r["kd"]), to_f(r["results"]))
        rows.sort(key=lambda r: -to_f(r["opportunity"]))
        write_csv(rows); write_briefs(rows); return
    if not KEY:
        sys.exit("ERROR: set SEMRUSH_KEY env var first (export SEMRUSH_KEY=...).")
    seeds = args[args.index("--seeds") + 1:] if "--seeds" in args else CFG["seeds"]
    print(f"Discovering keywords for {len(seeds)} seeds (SEMrush {DB})...")
    rows = discover(seeds)
    if not rows: sys.exit("No keywords survived filtering — loosen pipeline.config.json relevance.")
    write_csv(rows); write_briefs(rows)
    print("\nTop 10:")
    for r in rows[:10]:
        flag = " (written)" if r["already_written"] else ""
        print(f"  {r['opportunity']:>8}  {r['keyword']}  [{r['volume']}/mo KD{r['kd']} {r['format']}]{flag}")

if __name__ == "__main__":
    main()
