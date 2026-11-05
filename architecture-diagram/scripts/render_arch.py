#!/usr/bin/env python3
"""Render a customer architecture diagram (single-file HTML, inline SVG) from a JSON spec.

Usage: render_arch.py <architecture.json> [out.html]

Spec shape (see references/spec.md):
  meta:   {account, title, subtitle, updated, audience}
  zones:  [{id, label, nodes:[{id, title, sub?, kind?: box|list, items?:[...],
            state?: current|planned|exploring, tag?, gap_before?}]}]
  edges:  [{from, to, label?, state?, step?, route?: direct|bottom, both?: bool}]
  steps:  [{n, title, text}]        # "How it works", numbers match edge.step
  cards:  [{title, state?, text}]   # short notes under the steps (today vs next, etc.)
  legend: true|false
  groups: [{label, from, to, icon?}]  # optional band behind zones from..to (zone ids), e.g. "Inside Salesforce"
"""
import html, json, os, sys

W_ZONE, GAP_ZONE, PAD, TOP = 272, 50, 28, 64
NODE_W = W_ZONE - 32
BOX_H, CHIP_H, NODE_GAP = 72, 32, 22
TILE, TX = 42, 70        # icon tile size; text x-offset when a node has an icon
CHARS, CHARS_ICON = 30, 23  # rough wrap widths at 12.5px

ICONS = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons.json")))


def esc(s):
    return html.escape(str(s or ""), quote=True)


def wrap(text, n=CHARS):
    words, lines, cur = str(text or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines


def icon(ref, x, y, size, color="var(--brand-deep)"):
    """Inline an icon from assets/icons.json, fitted and centered in a size x size box."""
    ic = ICONS.get(ref)
    if not ic:
        sys.exit(f"unknown icon {ref}; add it with scripts/add_icons.py {ref}")
    w, h = ic["w"], ic["h"]
    sc = size / max(w, h)
    ox, oy = x + (size - w * sc) / 2, y + (size - h * sc) / 2
    paint = f' fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"' if ic["mono"] else ""
    return f'<svg x="{ox:.1f}" y="{oy:.1f}" width="{w * sc:.1f}" height="{h * sc:.1f}" viewBox="0 0 {w} {h}"{paint}>{ic["body"]}</svg>'


def text_x(nd):
    return TX if nd.get("icon") else 16


def sub_lines(nd):
    return wrap(nd.get("sub"), CHARS_ICON if nd.get("icon") else CHARS) if nd.get("sub") else []


def title_lines(nd):
    return wrap(nd["title"], 19 if nd.get("icon") else 26)


def tag_drops(nd):
    if not nd.get("tag"):
        return False
    return len(title_lines(nd)) > 1 or text_x(nd) + len(nd["title"]) * 8.2 + 9 + len(nd["tag"]) * 6.6 + 14 >= NODE_W


def head_height(nd):
    text_h = 30 + (len(title_lines(nd)) - 1) * 18 + len(sub_lines(nd)) * 16 + (22 if tag_drops(nd) else 0) + 12
    return max(BOX_H, text_h, (14 + TILE + 14) if nd.get("icon") else 0)


def node_height(nd):
    h = head_height(nd)
    if nd.get("kind") == "list":
        h += len(nd.get("items", [])) * (CHIP_H + 6) + 6
    return h


def top_of(spec):
    """Leave room above the zone labels for a group band's label."""
    return TOP + 38 if spec.get("groups") else TOP


def layout(spec):
    TOP = top_of(spec)
    pos, heights = {}, []
    for zi, z in enumerate(spec["zones"]):
        h = 0
        for nd in z["nodes"]:
            h += nd.get("gap_before", 0) + node_height(nd) + NODE_GAP
        heights.append(h - NODE_GAP)
    inner = max(heights)
    for zi, z in enumerate(spec["zones"]):
        x = PAD + zi * (W_ZONE + GAP_ZONE) + (W_ZONE - NODE_W) / 2
        y = TOP + 20 + (inner - heights[zi]) / 2 if z.get("center", True) else TOP + 20
        for nd in z["nodes"]:
            y += nd.get("gap_before", 0)
            hgt = node_height(nd)
            pos[nd["id"]] = {"x": x, "y": y, "w": NODE_W, "h": hgt, "zone": zi, "nd": nd}
            y += hgt + NODE_GAP
    width = PAD * 2 + len(spec["zones"]) * W_ZONE + (len(spec["zones"]) - 1) * GAP_ZONE
    lanes = [e.get("lane", 0) for e in spec.get("edges", []) if e.get("route") == "bottom"]
    height = TOP + 20 + inner + (40 + 22 * (max(lanes) + 1) if lanes else 40)
    return pos, width, height


STATE = {
    "current": {"stroke": "var(--brand)", "fill": "var(--sheet)", "dash": ""},
    "planned": {"stroke": "var(--caution)", "fill": "var(--caution-soft)", "dash": "6 5"},
    "exploring": {"stroke": "var(--ink-3)", "fill": "var(--sunken)", "dash": "3 4"},
    "cancelled": {"stroke": "var(--cancelled)", "fill": "var(--cancelled-soft)", "dash": "6 5"},
    "paused": {"stroke": "var(--paused)", "fill": "var(--paused-soft)", "dash": "10 4"},
}
EDGE = {"current": "var(--brand-deep)", "planned": "var(--caution)", "exploring": "var(--ink-3)", "cancelled": "var(--cancelled)", "paused": "var(--paused)"}


def svg_node(p):
    nd, x, y, w, h = p["nd"], p["x"], p["y"], p["w"], p["h"]
    state = nd.get("state", "current")
    st = STATE.get(state, STATE["current"])
    out = [f'<g class="node" id="n-{esc(nd["id"])}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{st["fill"]}" stroke="{st["stroke"]}" '
           f'stroke-width="1.6" stroke-dasharray="{st["dash"]}" filter="{"url(#lift)" if state == "current" else ""}"/>']
    if nd.get("icon"):
        tx, ty = x + 14, y + 14
        out.append(f'<rect x="{tx}" y="{ty}" width="{TILE}" height="{TILE}" rx="10" fill="#fff" stroke="var(--rule)"/>')
        out.append(icon(nd["icon"], tx + 8, ty + 8, TILE - 16))
        if nd.get("badge"):
            bx, by = tx + TILE - 12, ty + TILE - 12
            out.append(f'<circle cx="{bx + 8}" cy="{by + 8}" r="11" fill="#fff" stroke="var(--rule-strong)"/>')
            out.append(icon(nd["badge"], bx, by, 16))
    lx = x + text_x(nd)
    ty = y + 12
    for line in title_lines(nd):
        ty += 18
        out.append(f'<text x="{lx}" y="{ty}" class="t-title">{esc(line)}</text>')
    for line in sub_lines(nd):
        ty += 16
        out.append(f'<text x="{lx}" y="{ty}" class="t-sub">{esc(line)}</text>')
    if nd.get("tag"):
        tw = 9 + len(nd["tag"]) * 6.6
        if tag_drops(nd):
            gx, gy = lx, ty + 10
        else:
            gx, gy = x + w - tw - 10, y + 12
        out.append(f'<rect x="{gx}" y="{gy}" width="{tw}" height="18" rx="9" fill="var(--sheet)" stroke="{st["stroke"]}"/>'
                   f'<text x="{gx + tw / 2}" y="{gy + 13}" text-anchor="middle" class="t-tag" fill="{st["stroke"]}">{esc(nd["tag"])}</text>')
    if nd.get("kind") == "list":
        cy = y + head_height(nd)
        for it in nd.get("items", []):
            it = {"label": it} if isinstance(it, str) else it
            cls = "t-chip mono" if it.get("mono") else "t-chip"
            out.append(f'<rect x="{x + 14}" y="{cy}" width="{w - 28}" height="{CHIP_H}" rx="8" fill="var(--brand-soft)" stroke="var(--brand-rule)"/>')
            cx = x + 26
            if it.get("icon"):
                out.append(icon(it["icon"], x + 22, cy + 8, 16))
                cx = x + 46
            out.append(f'<text x="{cx}" y="{cy + 20.5}" class="{cls}">{esc(it["label"])}</text>')
            cy += CHIP_H + 6
    out.append("</g>")
    return "".join(out)


def anchor(p, side):
    x, y, w, h = p["x"], p["y"], p["w"], p["h"]
    return {"r": (x + w, y + h / 2), "l": (x, y + h / 2), "t": (x + w / 2, y), "b": (x + w / 2, y + h)}[side]


def svg_edge(e, pos, H):
    a, b = pos[e["from"]], pos[e["to"]]
    st = e.get("state", "current")
    color = EDGE[st]
    dash = "" if st == "current" else ' stroke-dasharray="6 5"'
    if e.get("route") == "bottom":
        (x1, y1), (x2, y2) = anchor(a, "b"), anchor(b, "b")
        x1 += e.get("dx_from", 0); x2 += e.get("dx_to", 0)
        ly = H - 22 - 22 * e.get("lane", 0)
        r = 12
        d = (f"M{x1},{y1} L{x1},{ly - r} Q{x1},{ly} {x1 + r},{ly} L{x2 - r},{ly} Q{x2},{ly} {x2},{ly - r} L{x2},{y2 + 2}")
        mx, my = (x1 + x2) / 2, ly
    elif a["zone"] == b["zone"]:
        down = b["y"] > a["y"]
        (x1, y1), (x2, y2) = anchor(a, "b" if down else "t"), anchor(b, "t" if down else "b")
        d = f"M{x1},{y1} L{x2},{y2}"
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    else:
        fwd = b["zone"] > a["zone"]
        (x1, y1), (x2, y2) = anchor(a, "r" if fwd else "l"), anchor(b, "l" if fwd else "r")
        y1 += e.get("dy_from", 0); y2 += e.get("dy_to", 0)
        c = abs(x2 - x1) * 0.45
        d = f"M{x1},{y1} C{x1 + (c if fwd else -c)},{y1} {x2 - (c if fwd else -c)},{y2} {x2},{y2}"
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    mk = f'marker-end="url(#ah-{st})"' + (f' marker-start="url(#as-{st})"' if e.get("both") else "")
    out = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8"{dash} {mk}/>']
    if e.get("step"):
        out.append(f'<circle cx="{mx}" cy="{my}" r="11" fill="{color}"/>'
                   f'<text x="{mx}" y="{my + 4}" text-anchor="middle" class="t-step">{esc(e["step"])}</text>')
    return "".join(out)


def markers():
    out = []
    for st, c in EDGE.items():
        out.append(f'<marker id="ah-{st}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                   f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                   f'<marker id="as-{st}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                   f'<path d="M10,0 L0,5 L10,10 z" fill="{c}"/></marker>')
    return ("<defs>" + "".join(out) + '<filter id="lift" x="-10%" y="-10%" width="120%" height="130%">'
            '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0b2a55" flood-opacity="0.10"/></filter></defs>')


def svg_groups(spec, H, TOP):
    """A labeled band behind a run of zones, so the reader sees which columns live in one system."""
    ids = [z["id"] for z in spec["zones"]]
    out = []
    for g in spec.get("groups", []):
        a, b = ids.index(g["from"]), ids.index(g["to"])
        x = PAD + a * (W_ZONE + GAP_ZONE) - 12
        w = (b - a) * (W_ZONE + GAP_ZONE) + W_ZONE + 24
        y = TOP - 68
        lab = esc(g["label"]).upper()
        ico = icon(g["icon"], x + 16, y + 8, 18) if g.get("icon") else ""
        tx = x + (42 if g.get("icon") else 18)
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{H - y - 24}" rx="20" fill="var(--brand-soft)" '
                   f'stroke="var(--brand)" stroke-width="1.5" stroke-opacity=".45" />'
                   f'{ico}<text x="{tx}" y="{y + 22}" class="t-group">{lab}</text>')
    return "".join(out)


def build_svg(spec, title, vi=0):
    pos, W, H = layout(spec)
    TOP = top_of(spec)
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="dg-title-{vi}" xmlns="http://www.w3.org/2000/svg">',
             f'<title id="dg-title-{vi}">{esc(title)}</title>', markers(), svg_groups(spec, H, TOP)]
    for zi, z in enumerate(spec["zones"]):
        x = PAD + zi * (W_ZONE + GAP_ZONE)
        parts.append(f'<rect x="{x}" y="{TOP - 30}" width="{W_ZONE}" height="{H - TOP - 6}" rx="14" fill="var(--zone)" />'
                     f'<text x="{x + 16}" y="{TOP - 8}" class="t-zone">{esc(z["label"]).upper()}</text>')
    for e in spec.get("edges", []):
        parts.append(svg_edge(e, pos, H))
    for p in pos.values():
        parts.append(svg_node(p))
    parts.append("</svg>")
    return "".join(parts)


CSS = """
:root{--paper:oklch(0.984 0.004 250);--sheet:oklch(0.996 0.002 250);--sunken:oklch(0.955 0.007 250);--zone:oklch(0.968 0.008 250);
--ink:oklch(0.23 0.025 258);--ink-2:oklch(0.42 0.022 256);--ink-3:oklch(0.52 0.018 255);--rule:oklch(0.905 0.008 250);--rule-strong:oklch(0.82 0.012 252);
--brand:oklch(0.5 0.155 252);--brand-deep:oklch(0.33 0.1 256);--brand-soft:oklch(0.955 0.022 250);--brand-rule:oklch(0.84 0.06 250);
--caution:oklch(0.5 0.11 62);--caution-soft:oklch(0.975 0.03 85);--cancelled:oklch(0.5 0.13 18);--cancelled-soft:oklch(0.975 0.014 18);--paused:oklch(0.47 0.06 290);--paused-soft:oklch(0.97 0.015 290);
--sans:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"Geist Mono",ui-monospace,Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.6 var(--sans)}
header{background:var(--brand-deep);color:#fff;padding:2.25rem 1.5rem 2rem}
.wrap{max-width:76rem;margin:0 auto}
.crumbs{font:500 .76rem var(--mono);letter-spacing:.05em;text-transform:uppercase;opacity:.85}
h1{font-size:clamp(1.7rem,3.2vw,2.4rem);line-height:1.15;margin:.6rem 0 .5rem;letter-spacing:-.01em}
header p{margin:0;max-width:52rem;opacity:.92}
.updated{margin-top:1.1rem;font:400 .8rem var(--mono);opacity:.8}
main{padding:1.5rem 1.5rem 4rem}
.diagram{background:var(--sheet);border:1px solid var(--rule);border-radius:14px;padding:12px;overflow-x:auto}
.diagram svg{display:block;width:100%;min-width:900px;height:auto}
.legend{display:flex;flex-wrap:wrap;gap:1.25rem;margin:.9rem .25rem 0;font-size:.85rem;color:var(--ink-2)}
.legend span{display:inline-flex;align-items:center;gap:.45rem}
.sw{width:26px;height:14px;border-radius:4px;border:1.6px solid var(--brand);background:var(--sheet)}
.sw.planned{border-style:dashed;border-color:var(--caution);background:var(--caution-soft)}
.sw.exploring{border-style:dotted;border-color:var(--ink-3);background:var(--sunken)}
.sw.cancelled{border-style:dashed;border-color:var(--cancelled);background:var(--cancelled-soft)}
.sw.paused{border-style:dashed;border-color:var(--paused);background:var(--paused-soft)}
section.view{margin-top:2.5rem}section.view:first-child{margin-top:.5rem}
section.view>h2{margin:0 0 .3rem}section.view>p.intro{margin:0 0 1rem;color:var(--ink-2);max-width:52rem}
h3{font-size:1.08rem;margin:1.6rem 0 .7rem}
.pill{display:inline-block;font:600 .7rem var(--mono);letter-spacing:.05em;padding:.1rem .5rem;border-radius:99px;border:1px solid currentColor;vertical-align:.2rem;margin-left:.5rem;white-space:nowrap}
.pill.current{color:var(--brand)}.pill.planned{color:var(--caution)}.pill.cancelled{color:var(--cancelled)}.pill.paused{color:var(--paused)}.pill.exploring{color:var(--ink-3)}
h2{font-size:1.3rem;margin:2.25rem 0 .8rem}
ol.steps{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));gap:.8rem}
ol.steps li{background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:.85rem 1rem;display:grid;grid-template-columns:1.9rem 1fr;gap:.2rem .6rem}
ol.steps .n{grid-row:span 2;width:1.6rem;height:1.6rem;border-radius:50%;background:var(--brand-deep);color:#fff;font:600 .8rem/1.6rem var(--mono);text-align:center}
ol.steps .n.planned{background:var(--caution)}ol.steps .n.cancelled{background:var(--cancelled)}ol.steps .n.paused{background:var(--paused)}ol.steps .n.exploring{background:var(--ink-3)}
ol.steps b{font-size:.98rem}ol.steps p{margin:0;font-size:.92rem;color:var(--ink-2)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:.8rem}
.card{background:var(--sheet);border:1px solid var(--rule);border-left:4px solid var(--brand);border-radius:10px;padding:.85rem 1rem}
.card.planned{border-left-color:var(--caution)}.card.cancelled{border-left-color:var(--cancelled)}.card.paused{border-left-color:var(--paused)}.card.exploring{border-left-color:var(--ink-3)}
.card b{display:block;margin-bottom:.2rem}.card p{margin:0;font-size:.92rem;color:var(--ink-2)}
footer{color:var(--ink-3);font-size:.85rem;margin-top:2.5rem}
.t-zone{font:600 11.5px var(--mono);letter-spacing:.08em;fill:var(--ink-3)}
.t-group{font:700 12px var(--mono);letter-spacing:.1em;fill:var(--brand-deep)}
.t-title{font:700 14.5px var(--sans);fill:var(--ink)}
.t-sub{font:400 12.5px var(--sans);fill:var(--ink-2)}
.t-chip{font:500 12.5px var(--sans);fill:var(--brand-deep)}.t-chip.mono{font:500 11.5px var(--mono)}
.t-tag{font:600 10px var(--mono);letter-spacing:.04em}
.t-step{font:700 11.5px var(--mono);fill:#fff}
@media print{header{background:none;color:var(--ink);padding:0 0 1rem}.diagram{border:0;padding:0}.diagram svg{min-width:0}
ol.steps li,.card{break-inside:avoid}}
"""


LEGEND = {"current": "In place today", "planned": "Next / planned", "exploring": "Exploring", "cancelled": "Cancelled", "paused": "Paused"}


def states_used(view):
    used = {n.get("state", "current") for z in view["zones"] for n in z["nodes"]}
    used |= {e.get("state", "current") for e in view.get("edges", [])}
    return [s for s in LEGEND if s in used]


def legend_html(view, spec):
    if not spec.get("legend", True):
        return ""
    labels = {**LEGEND, **spec.get("legend_labels", {}), **view.get("legend_labels", {})}
    sw = "".join(f'<span><i class="sw {"" if s == "current" else s}"></i>{esc(labels[s])}</span>' for s in states_used(view))
    note = '<span>Numbers on the lines match the steps below</span>' if any(e.get("step") for e in view.get("edges", [])) else ""
    return f'<div class="legend">{sw}{note}</div>'


def steps_html(view):
    return "".join(
        f'<li><span class="n {esc(s.get("state", ""))}">{esc(s["n"])}</span><b>{esc(s["title"])}</b><p>{esc(s["text"])}</p></li>'
        for s in view.get("steps", []))


def warn_band(view, name):
    """Salesforce work should sit inside a Salesforce band (see SKILL.md)."""
    sf = any("salesforce" in (n.get("icon", "") + n.get("badge", "")) for z in view.get("zones", []) for n in z["nodes"])
    if sf and not view.get("groups"):
        print(f"warning: {name} has Salesforce nodes but no groups band; add one unless that's intended", file=sys.stderr)


def render(spec):
    m = spec["meta"]
    for vi, v in enumerate(spec.get("views") or [spec]):
        warn_band(v, f'view {vi + 1} ({v.get("title", m["title"])})')
    views = spec.get("views")
    if views:
        body = ""
        for vi, v in enumerate(views):
            pill = f'<span class="pill {esc(v["pill_state"])}">{esc(v["pill"])}</span>' if v.get("pill") else ""
            steps = steps_html(v)
            intro = f'<p class="intro">{esc(v["intro"])}</p>' if v.get("intro") else ""
            st_title = esc(v.get("steps_title", "How it works"))
            st_block = f'<h3>{st_title}</h3><ol class="steps">{steps}</ol>' if steps else ""
            body += (f'<section class="view"><h2>{esc(v["title"])}{pill}</h2>{intro}'
                     f'<div class="diagram">{build_svg(v, v["title"], vi)}</div>{legend_html(v, spec)}{st_block}</section>')
    else:
        steps = steps_html(spec)
        body = (f'<div class="diagram">{build_svg(spec, m["title"])}</div>{legend_html(spec, spec)}'
                f'<h2>How it works</h2><ol class="steps">{steps}</ol>')
    cards = "".join(
        f'<div class="card {esc(c.get("state", ""))}"><b>{esc(c["title"])}</b><p>{esc(c["text"])}</p></div>'
        for c in spec.get("cards", []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(m["account"])}: {esc(m["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap">
<style>{CSS}</style></head><body>
<header><div class="wrap"><div class="crumbs">{esc(m["account"])} + Salesforce · Architecture</div>
<h1>{esc(m["title"])}</h1><p>{esc(m.get("subtitle"))}</p><div class="updated">Updated {esc(m["updated"])}</div></div></header>
<main><div class="wrap">
{body}
{f'<h2>{esc(spec.get("cards_title", "Today and next"))}</h2><div class="cards">{cards}</div>' if cards else ''}
<footer>Prepared by Salesforce for {esc(m["account"])}. {esc(m["updated"])}.</footer>
</div></main></body></html>"""


def main():
    src = sys.argv[1]
    spec = json.load(open(src))
    if '"shelved"' in json.dumps(spec):
        sys.exit('state "shelved" is retired; use "cancelled" or "paused"')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(src)), f'{spec["meta"]["slug"]}-architecture.html')
    for v in spec.get("views") or [spec]:
        ids = {n["id"] for z in v["zones"] for n in z["nodes"]}
        bad = [e for e in v.get("edges", []) if e["from"] not in ids or e["to"] not in ids]
        if bad:
            sys.exit(f"edges reference unknown nodes: {bad}")
    open(out, "w").write(render(spec))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
