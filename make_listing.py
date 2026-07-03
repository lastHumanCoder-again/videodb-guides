#!/usr/bin/env python3
"""Generate the dark-brand VideoDB guide index (site/index.html) grouped by cluster.
Pulls <title>/meta description from each built page. Run after build_html.py."""
import re, html, io, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "site"
INCOMING = ROOT / "_incoming_assets"; ASSETS_DIR = ROOT / "assets"
THUMBS = OUT / "thumbs"

def make_thumb(slug):
    """Compressed card thumbnail from the hero jpg; falls back to the chart svg."""
    src = INCOMING / f"{slug}.jpg"
    if src.exists():
        try:
            from PIL import Image, ImageOps
            THUMBS.mkdir(exist_ok=True)
            im = ImageOps.exif_transpose(Image.open(src))
            if im.mode != "RGB": im = im.convert("RGB")
            if im.width > 640: im = im.resize((640, round(im.height*640/im.width)), Image.LANCZOS)
            dest = THUMBS / f"{slug}.jpg"
            im.save(dest, "JPEG", quality=78, optimize=True)
            return f"thumbs/{slug}.jpg"
        except Exception:
            return None
    return None
CANVAS = "#0B0B0C"; CARD = "#141416"; ORANGE = "#E85810"; HAIR = "#2A2A2E"
TXT = "#F4F2EE"; MUTED = "#8C8C94"

CLUSTERS = [
 ("Category explainers", "What this layer of the stack is — the definitions the category was missing.", [
    "what-is-video-infrastructure-for-ai-agents", "what-is-a-video-understanding-api",
    "what-is-video-rag", "what-is-a-perception-layer", "how-do-ai-agents-see-and-understand-video"]),
 ("Build vs. buy & comparisons", "The stitched pipeline vs. one API — costs, trade-offs, and when you actually need each.", [
    "videodb-vs-building-with-ffmpeg-and-a-vector-database", "do-you-need-a-video-database",
    "build-vs-buy-video-ai-infrastructure", "videodb-vs-running-vlms-frame-by-frame",
    "semantic-video-search-vs-keyword-search", "video-understanding-api-alternatives"]),
 ("Use-case pillars", "The four markets running on the same primitives — cameras, agents, media, training data.", [
    "live-camera-intelligence", "agentic-perception", "programmable-media", "video-training-data-for-ai"]),
 ("Developer guides", "Hands-on tutorials — from `pip install videodb` to production.", [
    "give-your-ai-agent-vision-in-5-minutes", "rtsp-stream-to-real-time-alerts",
    "search-hours-of-meetings-with-ai", "replace-your-ffmpeg-pipeline", "video-rag-tutorial",
    "desktop-capture-for-coding-agents", "ai-video-analysis", "ai-video-summarization",
    "video-content-moderation-with-ai", "extract-text-from-video-ocr"]),
]

def meta(slug):
    p = OUT / f"{slug}.html"
    if not p.exists(): return None
    s = p.read_text()
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    title = html.unescape(t.group(1)).strip() if t else slug
    title = re.sub(r"\s*[-|]\s*VideoDB.*$", "", title)
    desc = html.unescape(d.group(1)).strip() if d else ""
    return title, desc

LOGO = ('<span class="logo"><svg viewBox="0 0 14 12" width="16" height="14" aria-hidden="true">'
        f'<path d="M0 0h14L7 12Z" fill="{ORANGE}"/></svg><span>Video</span><b>DB</b></span>')

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,system-ui,-apple-system,sans-serif;color:{TXT};background:{CANVAS};line-height:1.6;-webkit-font-smoothing:antialiased}}
a{{text-decoration:none;color:inherit}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
.logo{{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:18px;color:{TXT}}}
.logo b{{color:{ORANGE}}}
.hero{{padding:52px 0 60px;border-bottom:1px solid {HAIR};background-image:radial-gradient(circle at 85% 10%,rgba(232,88,16,.12),transparent 42%)}}
.hero .pill{{display:inline-block;background:{CARD};border:1px solid {HAIR};color:{ORANGE};font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;padding:6px 14px;border-radius:4px;margin:30px 0 22px}}
.hero h1{{font-family:'Archivo Black',sans-serif;font-weight:400;font-size:clamp(28px,4.6vw,44px);line-height:1.12;letter-spacing:-.01em;max-width:820px}}
.hero p{{color:{MUTED};font-size:17px;margin-top:16px;max-width:660px}}
.hero .cta{{display:inline-block;margin-top:28px;background:{ORANGE};color:{CANVAS};font-weight:700;font-size:15px;padding:13px 28px;border-radius:8px}}
.hero .cta:hover{{background:#F07030}}
.hero .ghost{{display:inline-block;margin:28px 0 0 12px;border:1px solid {HAIR};color:{TXT};font-weight:600;font-size:15px;padding:12px 24px;border-radius:8px}}
.section{{padding:48px 0 8px}}
.sec-head{{margin-bottom:22px}}
.sec-head h2{{font-family:'Archivo Black',sans-serif;font-weight:400;color:{TXT};font-size:22px;display:flex;align-items:center;gap:12px}}
.sec-head h2::before{{content:'';width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:11px solid {ORANGE};display:inline-block}}
.sec-head p{{color:{MUTED};font-size:15px;margin-top:6px;margin-left:26px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}}
.card{{border:1px solid {HAIR};border-radius:14px;overflow:hidden;transition:transform .15s,border-color .15s;background:{CARD};display:flex;flex-direction:column}}
.card:hover{{transform:translateY(-3px);border-color:{ORANGE}}}
.card img{{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;border-bottom:1px solid {HAIR}}}
.card .pad{{padding:18px 20px 18px;display:flex;flex-direction:column;flex:1}}
.card h3{{font-weight:700;color:{TXT};font-size:16.5px;line-height:1.35;margin-bottom:9px}}
.card p{{color:{MUTED};font-size:14px;line-height:1.55;flex:1}}
.card .go{{margin-top:14px;color:{ORANGE};font-size:13.5px;font-weight:700}}
.foot{{margin-top:64px;border-top:1px solid {HAIR};padding:28px 0 40px;display:flex;align-items:center;justify-content:space-between;color:{MUTED};font-size:13px}}
"""

def build():
    secs = []
    total = 0
    for name, blurb, slugs in CLUSTERS:
        cards = []
        for s in slugs:
            m = meta(s)
            if not m: continue
            t, d = m; total += 1
            th = make_thumb(s)
            img = f'<img loading="lazy" src="{th}" alt="{html.escape(t)}">' if th else ''
            cards.append(f'<a class="card" href="{s}.html">{img}<div class="pad"><h3>{html.escape(t)}</h3><p>{html.escape(d[:150])}</p><span class="go">Read guide &#8594;</span></div></a>')
        if cards:
            secs.append(f'<div class="section"><div class="sec-head"><h2>{html.escape(name)}</h2><p>{html.escape(blurb)}</p></div><div class="grid">{"".join(cards)}</div></div>')
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VideoDB Guides — Video Infrastructure for AI Agents</title>
<meta name="description" content="Canonical guides to video infrastructure for AI agents: video understanding APIs, video RAG, agentic perception, real-time camera intelligence, and programmable media.">
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head><body>
<div class="hero"><div class="wrap">
{LOGO}
<div><span class="pill">Guides &amp; explainers</span></div>
<h1>Video has a second user now: machines.</h1>
<p>The canonical guides to the perception layer — how AI agents ingest, index, remember, search, edit, and stream video. Built on VideoDB, the database for continuous media.</p>
<a class="cta" href="https://console.videodb.io" rel="noopener" target="_blank">Start free in the console &#8594;</a>
<a class="ghost" href="https://docs.videodb.io" rel="noopener" target="_blank">Read the docs</a>
</div></div>
<div class="wrap">
{''.join(secs)}
<div class="foot">{LOGO}<span>To see is to know. &nbsp;&middot;&nbsp; videodb.io</span></div>
</div>
</body></html>"""
    (OUT / "index.html").write_text(page)
    print(f"index.html written with {total} guides.")

if __name__ == "__main__":
    build()
