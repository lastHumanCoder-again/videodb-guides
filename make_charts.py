#!/usr/bin/env python3
"""Generate VideoDB dark-brand SVG charts from JSON specs.
Spec at chart_specs/<stem>.json:
{ "file": "<stem>", "title": "...", "rows": [["label", value, "display", true|false], ...],
  "footnote": "Source: ...", "type": "bar" | "donut" }
Run:  python3 make_charts.py
"""
import json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"; SPECS = ROOT / "chart_specs"
ASSETS.mkdir(exist_ok=True); SPECS.mkdir(exist_ok=True)

CANVAS = "#0B0B0C"; CARD = "#141416"; ORANGE = "#E85810"; HAIR = "#2A2A2E"
TXT = "#F4F2EE"; MUTED = "#8C8C94"; GOOD = "#3DD68C"; BAD = "#E5484D"
FONT = "'Inter',system-ui,sans-serif"; DISPLAY = "'Archivo Black','Inter',sans-serif"
BX0, BMAX = 300, 330

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def bar_chart(title, rows, footnote=""):
    maxv = max(r[1] for r in rows) or 1
    y0, pitch, bh = 62, 46, 26
    H = y0 + len(rows) * pitch + (36 if footnote else 18)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 {H}" width="720" height="{H}" font-family="{FONT}">',
           f'<rect width="720" height="{H}" rx="12" fill="{CANVAS}"/>',
           f'<text x="40" y="34" font-size="15" font-family="{DISPLAY}" fill="{TXT}" letter-spacing=".02em">{esc(title).upper()}</text>']
    for i, r in enumerate(rows):
        label, val, disp = r[0], r[1], r[2]; hi = r[3] if len(r) > 3 else False
        y = y0 + i * pitch; mid = y + bh / 2 + 4
        w = max(6, round(val / maxv * BMAX))
        fill = ORANGE if hi else HAIR
        vfill = ORANGE if hi else MUTED
        out.append(f'<text x="288" y="{mid:.0f}" font-size="13" font-weight="600" fill="{TXT}" text-anchor="end">{esc(label)}</text>')
        out.append(f'<rect x="{BX0}" y="{y}" width="{w}" height="{bh}" rx="5" fill="{fill}"/>')
        out.append(f'<text x="{BX0 + w + 8}" y="{mid:.0f}" font-size="13" font-weight="700" fill="{vfill}" style="font-variant-numeric:tabular-nums">{esc(disp)}</text>')
    if footnote:
        out.append(f'<text x="40" y="{H-14}" font-size="11.5" fill="{MUTED}">{esc(footnote)}</text>')
    out.append("</svg>")
    return "\n".join(out)

def donut(title, rows, footnote=""):
    pct = rows[0][1]; disp = rows[0][2]; sub = rows[0][0]
    cx, cy, rr, sw = 116, 128, 68, 24
    circ = 2 * math.pi * rr; dash = circ * pct / 100
    H = 256
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 {H}" width="720" height="{H}" font-family="{FONT}">',
           f'<rect width="720" height="{H}" rx="12" fill="{CANVAS}"/>',
           f'<text x="40" y="36" font-size="15" font-family="{DISPLAY}" fill="{TXT}" letter-spacing=".02em">{esc(title).upper()}</text>',
           f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{HAIR}" stroke-width="{sw}"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{ORANGE}" stroke-width="{sw}" '
           f'stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>',
           f'<text x="{cx}" y="{cy+4}" font-size="28" font-family="{DISPLAY}" fill="{TXT}" text-anchor="middle">{esc(disp)}</text>',
           f'<text x="228" y="{cy-8}" font-size="15" font-weight="600" fill="{TXT}">{esc(sub)}</text>']
    for j, r in enumerate(rows[1:4]):
        out.append(f'<rect x="228" y="{cy+14+j*26}" width="8" height="8" transform="rotate(45 232 {cy+18+j*26})" fill="{ORANGE}"/>')
        out.append(f'<text x="248" y="{cy+24+j*26}" font-size="13" fill="{MUTED}">{esc(r[0])}: <tspan font-weight="700" fill="{TXT}">{esc(r[2])}</tspan></text>')
    if footnote:
        out.append(f'<text x="40" y="{H-14}" font-size="11.5" fill="{MUTED}">{esc(footnote)}</text>')
    out.append("</svg>")
    return "\n".join(out)

def render(spec):
    if spec.get("type", "bar") == "donut":
        return donut(spec["title"], spec["rows"], spec.get("footnote", ""))
    return bar_chart(spec["title"], spec["rows"], spec.get("footnote", ""))

if __name__ == "__main__":
    specs = sorted(SPECS.glob("*.json"))
    print(f"Rendering {len(specs)} charts -> {ASSETS}\n")
    n = 0
    for sp in specs:
        try:
            spec = json.loads(sp.read_text())
            stem = spec.get("file") or sp.stem
            (ASSETS / f"{stem}.svg").write_text(render(spec))
            print(f"  ✓ {stem}.svg"); n += 1
        except Exception as e:
            print(f"  ✗ {sp.name}: {e}")
    print(f"\n{n} charts rendered.")
