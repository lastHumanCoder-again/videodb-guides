#!/usr/bin/env python3
"""Build VideoDB canonical pSEO/AEO pages in the dark brand (scoped CSS, key-insights, TOC,
FAQ accordion, takeaway CTA, 3x JSON-LD). Near-black canvas, orange #E85810 accent,
Archivo Black display + Inter body, styled code blocks for developer content.

Source: blogs/*.md  ->  output: site/{slug}.html
The [cta]: <url> reference in each markdown drives the button href; the link text in the
closing takeaway becomes the button label (console vs docs by funnel stage)."""
import re, html, json, glob, io, base64, pathlib
import markdown as md_lib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "docs"; OUT.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"; INCOMING = ROOT / "_incoming_assets"
SITE = "https://videodb.io"
DEFAULT_CTA = "https://console.videodb.io"

# ---- VideoDB dark brand -------------------------------------------------------
CANVAS = "#0B0B0C"   # near-black background (dominant)
CARD   = "#141416"   # raised surfaces
ORANGE = "#E85810"   # THE accent — the only loud color
TXT    = "#F4F2EE"   # warm off-white
MUTED  = "#8C8C94"   # secondary text
HAIR   = "#2A2A2E"   # hairline borders
GOOD   = "#3DD68C"; BAD = "#E5484D"

raster = {}
for p in (list(INCOMING.glob("*")) if INCOMING.exists() else []) + list(ASSETS.glob("*")):
    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        raster[p.stem.strip()] = p

_uri = {}
def data_uri(path, max_w=1100, q=82):
    from PIL import Image, ImageOps
    k = str(path)
    if k in _uri: return _uri[k]
    im = ImageOps.exif_transpose(Image.open(path))
    if im.mode != "RGB": im = im.convert("RGB")
    if im.width > max_w: im = im.resize((max_w, round(im.height*max_w/im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    _uri[k] = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode(); return _uri[k]

def svg_inline(stem):
    p = ASSETS / f"{stem}.svg"
    if not p.exists(): return None
    s = re.sub(r'<\?xml.*?\?>', '', p.read_text(), flags=re.S)
    s = re.sub(r'\swidth="\d+"', ' ', s, 1); s = re.sub(r'\sheight="\d+"', '', s, 1)
    return s.strip()

def grab(b, p):
    m = re.search(p, b, re.I); return m.group(1).strip().strip('`"') if m else None

def parse_meta(raw, stem):
    cm = re.search(r'<!--(.*?)-->', raw, re.S); b = cm.group(1) if cm else ""
    title = grab(b, r'SEO title[^:]*:\s*(.+)')
    slug = grab(b, r'(?:URL\s*)?slug[^:]*:\s*([^\s]+)') or stem.lower().replace("_", "-")
    desc = grab(b, r'[Mm]eta description[^:]*:\s*(.+)') or ""
    eyebrow = grab(b, r'[Ee]yebrow[^:]*:\s*(.+)') or "VideoDB guides"
    read = grab(b, r'[Rr]ead time[^:]*:\s*(.+)') or "9 min read"
    return title, slug.strip("/").split()[0], desc, eyebrow, read

def resolve_imgs(body):
    def fig(tag, cap=""):
        src = re.search(r'src="([^"]+)"', tag).group(1)
        alt = (re.search(r'alt="([^"]*)"', tag) or [None, ""])[1]
        stem = pathlib.Path(src).stem
        caphtml = f'<figcaption class="vb-cap">{cap}</figcaption>' if cap else ''
        if src.startswith("data:") or src.startswith("http"):
            return f'<figure class="vb-fig vb-photo"><img loading="lazy" src="{src}" alt="{html.escape(alt)}">{caphtml}</figure>'
        if src.endswith(".svg") or (ASSETS / f"{stem}.svg").exists():
            sv = svg_inline(stem)
            if sv: return f'<figure class="vb-fig vb-chart">{sv}{caphtml}</figure>'
        if stem in raster:
            return f'<figure class="vb-fig vb-photo"><img loading="lazy" src="{data_uri(raster[stem])}" alt="{html.escape(alt)}">{caphtml}</figure>'
        return ''
    body = re.sub(r'<p>\s*(<img[^>]+?>)\s*</p>\s*<p>\s*<em>(.*?)</em>\s*</p>', lambda m: fig(m.group(1), m.group(2)), body, flags=re.S)
    body = re.sub(r'<p>\s*(<img[^>]+?>)\s*(?:<br\s*/?>)?\s*<em>(.*?)</em>\s*</p>', lambda m: fig(m.group(1), m.group(2)), body, flags=re.S)
    body = re.sub(r'<p>\s*(<img[^>]+?>)\s*</p>', lambda m: fig(m.group(1)), body, flags=re.S)
    return body

def good_bad_cells(body):
    def repl(m):
        cell = m.group(1); t = re.sub(r'<.*?>', '', cell).strip().lower()
        if t.startswith(("yes", "included", "✓")) or t in ("none", "$0", "1", "one"):
            return f'<td class="vb-good">{cell}</td>'
        if t.startswith(("no", "✗", "not ")) or "not available" in t:
            return f'<td class="vb-bad">{cell}</td>'
        return f'<td>{cell}</td>'
    return re.sub(r'<td>(.*?)</td>', repl, body, flags=re.S)

def slugify(s): return re.sub(r'[^a-z0-9]+', '-', re.sub(r'<.*?>', '', s).lower()).strip('-')[:60]

LOGO = ('<span class="vb-logo"><svg viewBox="0 0 14 12" width="13" height="11" aria-hidden="true">'
        f'<path d="M0 0h14L7 12Z" fill="{ORANGE}"/></svg>'
        '<span>Video</span><b>DB</b></span>')

CSS = """
.vb-wrap *,.vb-wrap *::before,.vb-wrap *::after{box-sizing:border-box}
body{background:__CANVAS__;margin:0}
.vb-wrap{max-width:760px;margin:0 auto;padding:0 20px 60px;font-family:Inter,system-ui,-apple-system,sans-serif;font-size:16px;line-height:1.75;color:__TXT__;background:__CANVAS__;-webkit-font-smoothing:antialiased}
.vb-logo{display:inline-flex;align-items:center;gap:7px;font-family:Inter,sans-serif;font-weight:700;font-size:15px;letter-spacing:-.01em;color:__TXT__}
.vb-logo b{color:__ORANGE__;font-weight:700}
.vb-topbar{display:flex;align-items:center;justify-content:space-between;padding:22px 0 0}
.vb-topbar a{text-decoration:none}
.vb-back{font-size:12.5px;color:__MUTED__;text-decoration:none}
.vb-back:hover{color:__ORANGE__}
.vb-eyebrow{display:inline-block;background:__CARD__;border:1px solid __HAIR__;color:__ORANGE__;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;padding:5px 12px;border-radius:4px;margin:34px 0 18px}
.vb-title{font-family:'Archivo Black',Inter,sans-serif;font-size:clamp(25px,4vw,38px);font-weight:400;color:__TXT__;line-height:1.16;letter-spacing:-.01em;margin:0 0 12px}
.vb-dek{font-size:16px;color:__MUTED__;margin-bottom:6px}
.vb-meta{font-size:13px;color:__MUTED__;margin-bottom:22px}
.vb-cover{width:100%;border-radius:14px;margin-bottom:26px}
.vb-cover img{width:100%;height:auto;display:block;border-radius:14px}
.vb-cover .vb-chart,.vb-fig.vb-chart{background:__CANVAS__;border:1px solid __HAIR__;border-radius:14px;padding:14px 16px}
.vb-fig{margin:24px 0}.vb-fig svg{width:100%;height:auto;display:block}
.vb-fig.vb-photo img{width:100%;height:auto;border-radius:14px;display:block}
.vb-cap{font-size:13px;color:__MUTED__;margin-top:10px;line-height:1.5}
.vb-intro{font-size:17.5px;color:__TXT__;line-height:1.7;margin-bottom:30px}
.vb-ki{border:1px solid __HAIR__;border-radius:12px;margin-bottom:26px;overflow:hidden;background:__CARD__}
.vb-ki-head{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;cursor:pointer;user-select:none}
.vb-ki-l{display:flex;align-items:center;gap:10px}
.vb-ki-dia{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid __ORANGE__;flex-shrink:0}
.vb-ki-lab{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:__TXT__}
.vb-ki-chev{color:__ORANGE__;font-size:15px;transition:transform .25s}.vb-ki-chev.open{transform:rotate(180deg)}
.vb-ki-body{max-height:0;overflow:hidden;transition:max-height .35s ease,padding .25s;padding:0 18px}
.vb-ki-body.open{max-height:1000px;padding:6px 18px 14px}
.vb-ki-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid __HAIR__;font-size:14.5px;line-height:1.6;color:__TXT__}
.vb-ki-item:last-child{border-bottom:none}
.vb-ki-dot{width:7px;height:7px;background:__ORANGE__;border-radius:50%;margin-top:8px;flex-shrink:0}
.vb-ki-item strong{color:__ORANGE__}
.vb-toc{background:__CARD__;border:1px solid __HAIR__;border-radius:12px;padding:22px 24px;margin-bottom:40px}
.vb-toc-t{font-size:12px;font-weight:700;color:__ORANGE__;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px}
.vb-toc ol{list-style:none;counter-reset:t;display:flex;flex-direction:column;gap:2px;margin:0;padding:0}
.vb-toc li{counter-increment:t}
.vb-toc a{display:flex;align-items:baseline;gap:10px;color:__MUTED__;text-decoration:none;font-size:13.5px;padding:3px 0;transition:color .2s}
.vb-toc a::before{content:counter(t,decimal-leading-zero);font-size:11px;font-weight:700;color:__ORANGE__;min-width:22px;font-variant-numeric:tabular-nums}
.vb-toc a:hover{color:__TXT__}
.vb-wrap h2{font-family:'Archivo Black',Inter,sans-serif;font-size:clamp(19px,3vw,24px);font-weight:400;color:__TXT__;border-bottom:2px solid __ORANGE__;padding-bottom:9px;margin:44px 0 16px;line-height:1.3}
.vb-wrap h3{font-family:Inter,sans-serif;font-size:18px;font-weight:700;color:__TXT__;margin:26px 0 10px}
.vb-wrap p{color:#C9C7C2;margin:0 0 16px;font-size:16px}
.vb-wrap a{color:__ORANGE__;font-weight:500;text-decoration:underline;text-underline-offset:2px}
.vb-wrap a:hover{color:#F07030}
.vb-wrap ul,.vb-wrap ol{margin:0 0 16px;padding-left:1.3em;color:#C9C7C2}.vb-wrap li{margin:.3em 0}
.vb-wrap strong{color:__TXT__}
.vb-wrap code{font-family:'SF Mono',ui-monospace,Menlo,monospace;font-size:.88em;background:__CARD__;border:1px solid __HAIR__;border-radius:5px;padding:.12em .38em;color:__TXT__}
.vb-wrap pre{background:__CARD__;border:1px solid __HAIR__;border-left:3px solid __ORANGE__;border-radius:10px;padding:16px 18px;overflow-x:auto;margin:20px 0;line-height:1.6}
.vb-wrap pre code{background:none;border:none;padding:0;font-size:13.5px;color:#E8E6E1}
.vb-tbl{overflow-x:auto;margin:22px 0;border-radius:12px;border:1px solid __HAIR__}
.vb-tbl table{width:100%;border-collapse:collapse;font-size:14.5px;background:__CARD__}
.vb-tbl thead tr{background:#000}
.vb-tbl thead th{padding:12px 15px;text-align:left;color:__TXT__;font-size:12.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.vb-tbl tbody td{padding:11px 15px;border-bottom:1px solid __HAIR__;color:#C9C7C2;vertical-align:top;font-variant-numeric:tabular-nums}
.vb-tbl tbody tr:last-child td{border-bottom:none}
.vb-good{color:__GOOD__;font-weight:600}.vb-bad{color:__BAD__;font-weight:600}
.vb-cta{background:__CARD__;border:1px solid __HAIR__;border-left:4px solid __ORANGE__;border-radius:12px;padding:18px 22px;margin:24px 0}
.vb-cta p{margin:0;font-size:15.5px;color:__TXT__}
.vb-cta a{display:inline-block;margin-top:10px;background:__ORANGE__;color:#0B0B0C;font-weight:700;font-size:14px;padding:10px 20px;border-radius:8px;text-decoration:none}
.vb-cta a:hover{background:#F07030}
.vb-also{margin:36px 0}
.vb-also-lab{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:__MUTED__;margin-bottom:10px}
.vb-also-card{display:flex;align-items:center;justify-content:space-between;background:__CARD__;border:1px solid __HAIR__;border-left:4px solid __ORANGE__;border-radius:10px;padding:14px 16px;text-decoration:none;gap:10px;margin-bottom:10px}
.vb-also-card span{font-size:14px;font-weight:600;color:__TXT__;line-height:1.4}
.vb-also-arr{color:__ORANGE__;font-size:18px;flex-shrink:0}
.vb-faq{margin:44px 0}.vb-faq h2{margin-top:0}
.vb-faq-item{border-bottom:1px solid __HAIR__}
.vb-faq-q{display:flex;justify-content:space-between;align-items:center;padding:16px 4px;cursor:pointer;user-select:none;gap:12px}
.vb-faq-q span{font-size:15px;font-weight:600;color:__TXT__;line-height:1.4}
.vb-faq-ic{font-size:24px;color:__ORANGE__;flex-shrink:0;transition:transform .25s;line-height:1;font-weight:300}
.vb-faq-ic.open{transform:rotate(45deg)}
.vb-faq-a{max-height:0;overflow:hidden;transition:max-height .3s ease,padding .25s;font-size:15px;color:#C9C7C2;line-height:1.7}
.vb-faq-a.open{max-height:600px;padding-bottom:16px}
.vb-take{background:__CARD__;border:1px solid __HAIR__;border-radius:16px;padding:32px 28px;margin:44px 0 28px;text-align:center;background-image:radial-gradient(circle at 85% 15%,rgba(232,88,16,.14),transparent 45%)}
.vb-take h3{font-family:'Archivo Black',Inter,sans-serif;font-size:20px;font-weight:400;color:__TXT__;margin:0 0 10px}
.vb-take p{font-size:15px;color:__MUTED__;margin:0 auto 22px;max-width:540px;line-height:1.65}
.vb-btn{display:inline-block;background:__ORANGE__;color:#0B0B0C;font-weight:700;font-size:14.5px;padding:13px 28px;border-radius:8px;text-decoration:none}
.vb-btn:hover{background:#F07030}
.vb-src{margin-top:34px;padding-top:18px;border-top:1px solid __HAIR__;font-size:13px;color:__MUTED__}
.vb-src h2{font-size:14px;border:none;color:__MUTED__;font-family:Inter,sans-serif;font-weight:700;margin:0 0 8px;padding:0}
.vb-src a{color:__MUTED__}
.vb-foot{margin-top:44px;padding-top:20px;border-top:1px solid __HAIR__;display:flex;align-items:center;justify-content:space-between;font-size:12.5px;color:__MUTED__}
@media(max-width:600px){.vb-wrap{font-size:15.5px}}
""".replace("__CANVAS__", CANVAS).replace("__CARD__", CARD).replace("__ORANGE__", ORANGE)\
   .replace("__TXT__", TXT).replace("__MUTED__", MUTED).replace("__HAIR__", HAIR)\
   .replace("__GOOD__", GOOD).replace("__BAD__", BAD)

JS = """
function vbKI(h){var b=h.nextElementSibling,c=h.querySelector('.vb-ki-chev');b.classList.toggle('open');c.classList.toggle('open');}
function vbFAQ(q){var a=q.nextElementSibling,i=q.querySelector('.vb-faq-ic'),open=a.classList.contains('open');
document.querySelectorAll('.vb-faq-a.open').forEach(function(x){x.classList.remove('open');x.previousElementSibling.querySelector('.vb-faq-ic').classList.remove('open');});
if(!open){a.classList.add('open');i.classList.add('open');}}
document.addEventListener('DOMContentLoaded',function(){var b=document.querySelector('.vb-ki-body'),c=document.querySelector('.vb-ki-chev');if(b){b.classList.add('open');if(c)c.classList.add('open');}});
"""

def build(src):
    stem = src.stem
    raw = src.read_text()
    title, slug, desc, eyebrow, read = parse_meta(raw, stem)
    cta_url = grab(raw, r'^\[cta\]:\s*(\S+)') or DEFAULT_CTA
    md = re.sub(r'^\s*<!--.*?-->', '', raw, count=1, flags=re.S)
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    used = set(re.findall(r'\]\[([a-z0-9-]+)\]', md)); deff = set(re.findall(r'^\[([a-z0-9-]+)\]:', md, re.M))
    for r in used - deff:
        md += f"\n[{r}]: {cta_url}" if "cta" in r else f"\n[{r}]: /blog/{r.replace('internal-','')}"
    body = md_lib.markdown(md, extensions=["tables", "attr_list", "sane_lists", "fenced_code"])
    h1m = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    h1 = re.sub(r'<.*?>', '', h1m.group(1)).strip() if h1m else (title or stem)
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)
    dek = ""
    dm = re.match(r'\s*<p>\s*<em>(.*?)</em>\s*</p>', body, re.S)
    if dm: dek = re.sub(r'<.*?>', '', dm.group(1)).strip(); body = body[dm.end():]
    body = resolve_imgs(body)
    body = good_bad_cells(body)
    body = re.sub(r'<table>', '<div class="vb-tbl"><table>', body); body = re.sub(r'</table>', '</table></div>', body)
    body = re.sub(r'<a href="(https?:[^"]+)">', r'<a href="\1" rel="noopener" target="_blank">', body)
    body = body.replace("<blockquote>", '<blockquote class="vb-cta">')
    body = re.sub(r'<p>\s*<em>\s*In a hurry.*?</em>\s*</p>', '', body, flags=re.S)
    intro = ""
    im = re.search(r'<p>(.*?)</p>', body, re.S)
    if im: intro = im.group(1); body = body[:im.start()] + body[im.end():]
    # SOURCES
    src_html = ""
    sm = re.search(r'<h2[^>]*>\s*Sources\s*</h2>(.*)$', body, re.S)
    if sm:
        src_html = f'<div class="vb-src"><h2>Sources</h2>{sm.group(1).strip()}</div>'
        body = body[:sm.start()]
    # closing CTA takeaway box
    take = ""
    esc_url = re.escape(cta_url)
    cands = list(re.finditer(r'<h3[^>]*>((?:(?!</h3>).)*?)</h3>\s*<p>((?:(?!</p>).)*?<a href="' + esc_url + r'"[^>]*>(.*?)</a>(?:(?!</p>).)*?)</p>', body, re.S))
    if cands:
        cm2 = cands[-1]
        htxt = re.sub(r'<.*?>', '', cm2.group(1)).strip()
        btn = re.sub(r'<.*?>', '', cm2.group(3)).strip().rstrip('→ ').strip() or "Try VideoDB free"
        ptxt = re.sub(r'<a [^>]*>.*?</a>', '', cm2.group(2)); ptxt = re.sub(r'<.*?>', '', ptxt).strip()
        take = (f'<div class="vb-take"><h3>{html.escape(htxt)}</h3><p>{html.escape(ptxt)}</p>'
                f'<a class="vb-btn" href="{cta_url}" rel="noopener" target="_blank">{html.escape(btn)} &#8594;</a></div>')
        body = body[:cm2.start()] + body[cm2.end():]
    body = re.sub(r'<hr\s*/?>', '', body)
    # FAQ
    faq_html, faqs = "", []
    fm = re.search(r'<h2[^>]*>\s*(?:Frequently asked questions|FAQ[^<]*)</h2>(.*)$', body, re.S)
    if fm:
        seg = fm.group(1)
        for q, a in re.findall(r'<p><strong>(.*?\?)</strong>\s*</p>\s*<p>(.*?)</p>', seg, re.S) or []:
            faqs.append((re.sub(r'<.*?>', '', q).strip(), re.sub(r'<.*?>', '', a).strip()))
        if not faqs:
            for q, a in re.findall(r'<p><strong>(.*?\?)</strong>\s*(.*?)</p>', seg, re.S):
                faqs.append((re.sub(r'<.*?>', '', q).strip(), re.sub(r'<.*?>', '', a).strip()))
        tail = body[fm.start():]
        salvage = "".join(re.findall(r'<figure class="vb-fig[^"]*">.*?</figure>', tail, re.S))
        body = body[:fm.start()] + salvage
        items = "".join(f'<div class="vb-faq-item"><div class="vb-faq-q" onclick="vbFAQ(this)"><span>{html.escape(q)}</span><span class="vb-faq-ic">+</span></div><div class="vb-faq-a">{html.escape(a)}</div></div>' for q, a in faqs)
        faq_html = f'<div class="vb-faq" id="faq"><h2>Frequently asked questions</h2>{items}</div>'
    # Also read (internal /blog/ links -> local .html for the static site)
    also = []
    for href, txt in re.findall(r'<a href="(/blog/[^"]+)"[^>]*>(.*?)</a>', body, re.S):
        t = re.sub(r'<.*?>', '', txt).strip().rstrip('↗ ').strip()
        if href not in [a[0] for a in also] and t: also.append((href, t))
    also = also[:3]
    body = re.sub(r'<a href="/blog/([^"]+)"', r'<a href="\1.html"', body)
    also_html = ""
    if also:
        cards = "".join(f'<a class="vb-also-card" href="{h.replace("/blog/","")}.html"><span>{html.escape(t)}</span><span class="vb-also-arr">&#8594;</span></a>' for h, t in also)
        also_html = f'<div class="vb-also" id="also-read"><div class="vb-also-lab">Also read</div>{cards}</div>'
    # hero: raster if present else first chart
    chart_fig = ""
    cfm = re.search(r'<figure class="vb-fig vb-chart">.*?</figure>', body, re.S)
    if cfm: chart_fig = cfm.group(0)
    hero_key = next((k for k in (slug, slug + "-hero", stem, stem + "-hero") if k in raster), None)
    if hero_key:
        cover = f'<div class="vb-cover vb-photo"><img src="{data_uri(raster[hero_key])}" alt="{html.escape(h1)}"></div>'
    elif chart_fig:
        cover = f'<div class="vb-cover">{chart_fig}</div>'; body = body.replace(chart_fig, "", 1)
    else:
        cover = ""
    # TOC
    toc_items = []
    def add_id(m):
        t = m.group(1); sid = slugify(t); toc_items.append((sid, re.sub(r'<.*?>', '', t).strip()))
        return f'<h2 id="{sid}">{t}</h2>'
    body = re.sub(r'<h2[^>]*>(.*?)</h2>', add_id, body, flags=re.S)
    if faqs: toc_items.append(("faq", "Frequently asked questions"))
    toc_html = ""
    if len(toc_items) >= 3:
        lis = "".join(f'<li><a href="#{sid}">{html.escape(t)}</a></li>' for sid, t in toc_items)
        toc_html = f'<div class="vb-toc"><div class="vb-toc-t">Table of contents</div><ol>{lis}</ol></div>'
    # Key insights
    ki = []
    for ptext in re.findall(r'<p>(.*?)</p>', body, re.S):
        plain = re.sub(r'<.*?>', '', ptext).strip()
        for sent in re.split(r'(?<=[.!?])\s+', plain):
            if re.search(r'\d', sent) and re.search(r'%|\$|\bms\b|\bmin\b|×|\d{2,}', sent) and 40 < len(sent) < 230:
                s = re.sub(r'(\$?\d[\d,\.]*\s?(?:%|percent|ms|min|×|x|k|K|M|B)?)', r'<strong>\1</strong>', sent, count=1)
                ki.append(s); break
        if len(ki) >= 6: break
    ki_html = ""
    if len(ki) >= 3:
        items = "".join(f'<div class="vb-ki-item"><div class="vb-ki-dot"></div><div>{s}</div></div>' for s in ki[:6])
        ki_html = ('<div class="vb-ki"><div class="vb-ki-head" onclick="vbKI(this)"><div class="vb-ki-l">'
                   '<div class="vb-ki-dia"></div><span class="vb-ki-lab">Key insights</span></div>'
                   '<span class="vb-ki-chev">&#9660;</span></div><div class="vb-ki-body">' + items + '</div></div>')
    # schema
    art = {"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc,
           "author": {"@type": "Organization", "name": "VideoDB"},
           "publisher": {"@type": "Organization", "name": "VideoDB", "url": SITE},
           "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE}/blog/{slug}"}}
    faqld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]} if faqs else None
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE}/blog"},
        {"@type": "ListItem", "position": 3, "name": h1, "item": f"{SITE}/blog/{slug}"}]}
    schema = f'<script type="application/ld+json">{json.dumps(art)}</script>'
    if faqld: schema += f'<script type="application/ld+json">{json.dumps(faqld)}</script>'
    schema += f'<script type="application/ld+json">{json.dumps(crumb)}</script>'

    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title or h1)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{SITE}/blog/{slug}">
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
{schema}
<style>{CSS}</style>
</head><body>
<div class="vb-wrap">
<div class="vb-topbar"><a href="index.html">{LOGO}</a><a class="vb-back" href="index.html">&#8592; All guides</a></div>
<div class="vb-eyebrow">{html.escape(eyebrow)}</div>
<h1 class="vb-title">{html.escape(h1)}</h1>
{f'<div class="vb-dek">{html.escape(dek)}</div>' if dek else ''}
<div class="vb-meta">VideoDB &nbsp;&middot;&nbsp; Updated July 2026 &nbsp;&middot;&nbsp; {html.escape(read)}</div>
{cover}
<p class="vb-intro">{intro}</p>
{ki_html}
{toc_html}
{body}
{also_html}
{faq_html}
{take}
{src_html}
<div class="vb-foot">{LOGO}<span>To see is to know.</span></div>
</div>
<script>{JS}</script>
</body></html>"""
    (OUT / f"{slug}.html").write_text(page)
    return f"{slug}.html", len(faqs), bool(cover), len(toc_items), len(ki)

if __name__ == "__main__":
    files = sorted(glob.glob(str(ROOT / "blogs/*.md")))
    print(f"Building {len(files)} VideoDB pages (dark brand)...\n")
    for f in files:
        name, nf, cov, ntoc, nki = build(pathlib.Path(f))
        print(f"  ✓ {name:58} faq={nf} cover={'Y' if cov else 'N'} toc={ntoc} ki={nki}")
    print(f"\n{len(files)} pages -> {OUT}")
