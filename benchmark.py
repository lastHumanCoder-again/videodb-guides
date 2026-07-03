#!/usr/bin/env python3
"""Benchmark published articles against their target keywords.

For every blog in blogs/*.md this reads the primary keyword from the metadata
comment, then asks SEMrush for the live top-10 organic SERP (phrase_organic)
and reports whether any of our domains rank, at what position, and who owns
the SERP otherwise. Also refreshes volume/KD so you can spot decaying targets.

Output: research/benchmark.csv + a console summary.

Usage:
  export SEMRUSH_KEY=...
  python3 benchmark.py                # all blogs  (~20 SEMrush units/keyword)
  python3 benchmark.py what-is-video-rag ai-video-analysis   # only these slugs

Cadence: run every 2–4 weeks. Expectations by difficulty band (see README):
KD <20 pages should enter the top 10 within 4–8 weeks of indexing; KD 20–40
within 3–6 months; KD >40 pages are AEO/authority plays — benchmark those by
LLM citation spot-checks, not SERP position alone.
"""
import csv, os, re, subprocess, sys, pathlib
from urllib.parse import urlencode

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "research"; OUT.mkdir(exist_ok=True)
KEY = os.environ.get("SEMRUSH_KEY", "").strip()
OUR_DOMAINS = ("videodb.io", "lasthumancoder-again.github.io")

def semrush(qtype, phrase, columns, limit):
    params = {"type": qtype, "key": KEY, "database": "us", "phrase": phrase,
              "export_columns": columns, "display_limit": str(limit)}
    raw = subprocess.check_output(["curl", "-sG", "https://api.semrush.com/?" + urlencode(params)],
                                  timeout=60).decode("utf-8", "replace")
    lines = raw.strip().splitlines()
    if not lines or "ERROR" in lines[0]: return []
    return [ln.split(";") for ln in lines[1:]]

def primary_keyword(md_path):
    m = re.search(r"Primary keyword:\s*([^\n(]+)", md_path.read_text())
    return m.group(1).strip().strip("`") if m else None

def main():
    if not KEY:
        sys.exit("ERROR: set SEMRUSH_KEY env var first.")
    only = set(sys.argv[1:])
    blogs = sorted((ROOT / "blogs").glob("*.md"))
    if only: blogs = [b for b in blogs if b.stem in only]
    rows = []
    print(f"Benchmarking {len(blogs)} articles...\n")
    for b in blogs:
        kw = primary_keyword(b)
        if not kw: continue
        serp = semrush("phrase_organic", kw, "Dn,Ur", 10)
        fresh = semrush("phrase_these", kw, "Ph,Nq,Kd", 1)
        vol, kd = (fresh[0][1], fresh[0][2]) if fresh else ("?", "?")
        pos, our_url = "", ""
        for i, (dn, ur) in enumerate((p[:2] for p in serp), 1):
            if any(d in dn for d in OUR_DOMAINS):
                pos, our_url = str(i), ur; break
        top3 = ", ".join(p[0] for p in serp[:3])
        rows.append({"slug": b.stem, "keyword": kw, "volume": vol, "kd": kd,
                     "our_position": pos or "not in top 10", "our_url": our_url,
                     "serp_top3": top3})
        mark = f"#{pos}" if pos else "—"
        print(f"  {mark:>4}  {b.stem:55} [{vol}/mo KD{kd}]  top: {top3[:60]}")
    p = OUT / "benchmark.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    ranked = sum(1 for r in rows if r["our_position"] != "not in top 10")
    print(f"\n{ranked}/{len(rows)} target keywords ranking in top 10 -> {p}")

if __name__ == "__main__":
    main()
