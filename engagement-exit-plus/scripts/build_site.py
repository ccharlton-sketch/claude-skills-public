#!/usr/bin/env python3
"""Build an internal site for one account: home page + internal retrospective + architecture.

Usage: build_site.py <account dir>   e.g. $READOUTS/acme

Writes <dir>/site/, a self-contained Heroku-ready app:
  public/index.html          home page generated from engagement.json + architecture.json
  public/retrospective.html  copy of <slug>-internal-retrospective.html with a site bar
  public/architecture.html   copy of <slug>-architecture.html with a site bar
  server.js, package.json    zero-dependency Node static server (allowlisted routes only)

Allowlist, not blocklist: only the two source files above are ever copied. Customer recaps,
engagement.json and raw_*.json never reach the site.
"""
import base64, copy, html, json, os, re, shutil, sys

PAGES = [("retrospective", "Retrospective", "{slug}-internal-retrospective.html"),
         ("architecture", "Architecture", "{slug}-architecture.html")]
STATUS = {"live_sandbox": "Live in sandbox", "live_production": "Live in production", "completed": "Completed", "in_build": "In build", "planned": "Planned", "cancelled": "Cancelled", "paused": "Paused"}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700'
         '&family=Geist+Mono:wght@400;500;600&display=swap">')

BAR_CSS = """<style>
.sitebar{position:sticky;top:0;z-index:50;background:oklch(0.23 0.025 258);color:#fff;font:500 .82rem/1 "Geist Mono",ui-monospace,Menlo,monospace;letter-spacing:.03em}
.sitebar .in{max-width:76rem;margin:0 auto;padding:.7rem 1.5rem;display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap}
.sitebar a{color:#fff;text-decoration:none;opacity:.78}.sitebar a:hover,.sitebar a:focus-visible{opacity:1;text-decoration:underline}
.sitebar a[aria-current]{opacity:1;border-bottom:2px solid #fff;padding-bottom:.15rem}
.sitebar .home{font-weight:600;opacity:1;margin-right:auto}
.sitebar .tag{border:1px solid currentColor;border-radius:99px;padding:.15rem .5rem;font-size:.7rem;opacity:.85}
.sitebar .brand{display:flex;align-items:center;gap:.75rem;background:#fff;border-radius:7px;padding:.3rem .8rem .3rem .6rem;opacity:1}
.sitebar .brand:hover{text-decoration:none}
.sitebar .brand svg,.sitebar .brand img{display:block;height:20px;width:auto}.sitebar .brand svg:first-child{height:32px}.sitebar .brand img{height:30px}.sitebar .brand > :last-child{max-width:130px;object-fit:contain}
.sitebar .brand .sep{width:1px;height:22px;background:oklch(0.85 0.01 250)}
.sitebar .brand + .home{margin-left:-.4rem}
@media print{.sitebar{display:none}}
</style>"""
AVAILABLE = {"retrospective", "architecture"}  # pages this site has, set in main()
SIDEBAR = True  # set in main(); turn off with <dir>/site.json {"sidebar": false}

SIDEBAR_CSS = """<style>
:root{--sb-w:272px}
body{--sb-pad:0px;padding-left:var(--sb-pad);transition:padding-left .22s ease}
body.sb-open{--sb-pad:var(--sb-w)}
.sitebar{margin-left:calc(-1 * var(--sb-pad));transition:margin-left .22s ease}
.sb-tab{position:fixed;left:0;top:calc(var(--bar-h,58px) + 1.25rem);z-index:39;display:inline-flex;align-items:center;gap:.45rem;
  background:oklch(0.23 0.025 258);color:#fff;border:0;border-radius:0 8px 8px 0;padding:.55rem .8rem .55rem .7rem;
  font:500 .78rem/1 "Geist Mono",ui-monospace,monospace;letter-spacing:.03em;cursor:pointer;box-shadow:0 4px 14px oklch(0.2 0.02 255 / .2);transition:opacity .2s}
.sb-tab:hover{background:oklch(0.33 0.1 256)}.sb-tab:focus-visible{outline:2px solid oklch(0.5 0.155 252);outline-offset:2px}
.sb-tab svg{width:16px;height:16px}
body.sb-open .sb-tab{opacity:0;pointer-events:none}
.sidebar{position:fixed;left:0;top:var(--bar-h,58px);bottom:0;width:var(--sb-w);box-sizing:border-box;overflow-y:auto;z-index:40;
  background:oklch(0.985 0.004 250);border-right:1px solid oklch(0.905 0.008 250);padding:1.4rem 1rem 2rem 1.25rem;
  font:400 .9rem/1.4 "Public Sans",system-ui,sans-serif;transform:translateX(-100%);visibility:hidden;transition:transform .22s ease,visibility 0s linear .22s}
body.sb-open .sidebar{transform:none;visibility:visible;transition:transform .22s ease}
.sidebar .sb-head{display:flex;justify-content:space-between;align-items:center;margin:0 0 .9rem}
.sidebar .sb-title{font:600 .74rem/1 "Geist Mono",ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:oklch(0.52 0.018 255);margin:0}
.sidebar .sb-hide{background:none;border:0;color:oklch(0.5 0.155 252);font:500 .8rem "Public Sans",sans-serif;cursor:pointer;padding:.2rem .3rem;border-radius:4px}
.sidebar .sb-hide:hover{text-decoration:underline}.sidebar .sb-hide:focus-visible{outline:2px solid oklch(0.5 0.155 252)}
.sidebar ol{list-style:none;margin:0;padding:0}
.sidebar li{margin:0}
.sidebar a{display:block;color:oklch(0.32 0.02 255);text-decoration:none;padding:.38rem .6rem;border-left:2px solid transparent;border-radius:0 6px 6px 0}
.sidebar a:hover{background:oklch(0.955 0.022 250);color:oklch(0.33 0.1 256)}
.sidebar a:focus-visible{outline:2px solid oklch(0.5 0.155 252);outline-offset:-2px}
.sidebar a.active{border-left-color:oklch(0.5 0.155 252);background:oklch(0.955 0.022 250);color:oklch(0.33 0.1 256);font-weight:600}
.sidebar .l3 a{padding:.25rem .6rem .25rem 1.4rem;font-size:.83rem;color:oklch(0.45 0.02 255)}
.sidebar .l3 a.active{font-weight:600}
main h2,main h3,main section[id],main aside{scroll-margin-top:calc(var(--bar-h,58px) + 1rem)}
body.sb-open nav.toc{display:none}
@media (max-width:960px){.sb-tab{top:auto;bottom:1rem;left:1rem;border-radius:8px;box-shadow:0 6px 20px oklch(0.2 0.02 255 / .3)}body.sb-open{--sb-pad:0px}.sidebar{box-shadow:0 12px 40px oklch(0.2 0.02 255 / .25)}}
@media (prefers-reduced-motion:reduce){body,.sitebar,.sidebar{transition:none!important}}
@media print{.sidebar,.sb-tab{display:none!important}body{padding-left:0!important}.sitebar{margin-left:0!important}}
</style>"""

SB_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>')

SIDEBAR_HTML = """<aside class="sidebar" id="sidebar" aria-label="On this page">
<div class="sb-head"><p class="sb-title">On this page</p><button type="button" class="sb-hide" data-sb-toggle>Hide</button></div>
<nav aria-label="Sections on this page"><ol id="sb-list"></ol></nav></aside>
<button type="button" class="sb-tab" data-sb-toggle>""" + SB_ICON + """<span>Contents</span></button>
<script>
(function(){
  var KEY="eng-sidebar", b=document.body, mq=window.matchMedia("(max-width:960px)");
  var saved=null; try{saved=localStorage.getItem(KEY)}catch(e){}
  var open = mq.matches ? false : saved!=="closed";
  var toggles=[].slice.call(document.querySelectorAll("[data-sb-toggle]"));
  function setBar(){var n=document.querySelector(".sitebar");if(n)document.documentElement.style.setProperty("--bar-h",n.offsetHeight+"px")}
  function apply(o,save){open=o;b.classList.toggle("sb-open",o);
    toggles.forEach(function(t){t.setAttribute("aria-expanded",String(o))});
    if(save&&!mq.matches){try{localStorage.setItem(KEY,o?"open":"closed")}catch(e){}}}
  toggles.forEach(function(t){t.setAttribute("aria-controls","sidebar");t.addEventListener("click",function(){apply(!open,true);(open?document.querySelector(".sidebar .sb-hide"):document.querySelector(".sb-tab")).focus()})});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&open&&mq.matches)apply(false,false)});
  document.addEventListener("click",function(e){if(open&&mq.matches&&!e.target.closest(".sidebar,[data-sb-toggle]"))apply(false,false)});
  setBar(); apply(open,false);
  function init(){
  // Build the list from this page's own headings.
  var list=document.getElementById("sb-list"), heads=[].slice.call(document.querySelectorAll("main h2")), used={}, items=[], cur=null;
  heads.forEach(function(h){
    var c=h.cloneNode(true);[].forEach.call(c.querySelectorAll(".pill,.tag,svg"),function(x){x.remove()});
    var label=c.textContent.replace(/\\s+/g," ").trim(); if(!label)return;
    if(!h.id){var base=label.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")||"s",id=base,i=2;while(used[id]||document.getElementById(id))id=base+"-"+(i++);h.id=id}
    used[h.id]=1;
    var level=h.tagName==="H2"?2:3; if(level===3&&!cur)level=2;
    var li=document.createElement("li");li.className="l"+level;
    var a=document.createElement("a");a.href="#"+h.id;a.textContent=label;a.title=label;li.appendChild(a);
    if(level===2){cur=li;list.appendChild(li)}else{var ol=cur.querySelector("ol");if(!ol){ol=document.createElement("ol");cur.appendChild(ol)}ol.appendChild(li)}
    a.addEventListener("click",function(){if(mq.matches)apply(false,false)});
    items.push({h:h,a:a});
  });
  // Highlight the section you are reading.
  function spy(){var y=(parseInt(getComputedStyle(document.documentElement).getPropertyValue("--bar-h"))||58)+24, act=items[0];
    items.forEach(function(it){if(it.h.getBoundingClientRect().top-y<=0)act=it});
    if((window.innerHeight+window.scrollY)>=document.documentElement.scrollHeight-2&&items.length)act=items[items.length-1];
    items.forEach(function(it){var on=it===act;it.a.classList.toggle("active",on);if(on)it.a.setAttribute("aria-current","location");else it.a.removeAttribute("aria-current")})}
  setBar(); spy();
  window.addEventListener("scroll",spy,{passive:true});
  window.addEventListener("resize",function(){setBar();spy()});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
  mq.addEventListener("change",function(e){apply(e.matches?false:saved!=="closed",false)});
})();
</script>"""


def bar_css():
    return BAR_CSS + (SIDEBAR_CSS if SIDEBAR else "")

BRAND = ""  # set in main() when <dir>/brand/ has logos


def esc(s):
    return html.escape(str(s or ""), quote=True)


def brand_chip(d, account):
    """Salesforce logo + customer logo, side by side, from <dir>/brand/. Empty if not set up.

    brand/salesforce.svg plus one customer logo: an .svg (preferred) or a .png.
    Logos are inlined, since the site serves only its three HTML routes."""
    bd = os.path.join(d, "brand")
    sf = os.path.join(bd, "salesforce.svg")
    if not os.path.exists(sf):
        return ""
    cust = [f for f in sorted(os.listdir(bd)) if f.endswith((".svg", ".png")) and f != "salesforce.svg"]
    if not cust:
        return ""
    cust.sort(key=lambda f: not f.endswith(".svg"))

    def svg(f):
        src = open(os.path.join(bd, f)).read()
        src = src[src.index("<svg"):]
        if re.search(r"<script|\son\w+\s*=|<foreignObject|<image|href\s*=\s*[\"'](https?:|//)", src, re.I):
            sys.exit(f"brand/{f} has scripts, outside links or embedded images; clean it first")
        tag = re.match(r"<svg[^>]*>", src, re.S).group(0)
        new = re.sub(r'\s(width|height)="[^"]*"', "", tag).replace("<svg", '<svg aria-hidden="true" focusable="false"', 1)
        return src.replace(tag, new, 1)

    def logo(f):
        if f.endswith(".svg"):
            return svg(f)
        b64 = base64.b64encode(open(os.path.join(bd, f), "rb").read()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="">'

    return (f'<a class="brand" href="/" aria-label="Salesforce and {esc(account)}">'
            f'{svg("salesforce.svg")}<span class="sep" aria-hidden="true"></span>{logo(cust[0])}</a>')


def bar(account, current):
    cur = ' aria-current="page"'
    links = "".join(f'<a href="/{p}"{cur if p == current else ""}>{label}</a>' for p, label, _ in PAGES if p in AVAILABLE)
    home_cur = ' aria-current="page"' if current == "home" else ""
    return (f'<nav class="sitebar" aria-label="Site"><div class="in">{BRAND}'
            f'<a class="home" href="/"{home_cur}>{esc(account)} · Engagement</a>{links}'
            f'<span class="tag">INTERNAL</span></div></nav>' + (SIDEBAR_HTML if SIDEBAR else ""))


def with_bar(src_html, account, current):
    out = src_html.replace("</head>", '<meta name="robots" content="noindex,nofollow">' + bar_css() + "</head>", 1)
    out, n = re.subn(r"<body[^>]*>", lambda m: m.group(0) + bar(account, current), out, count=1)
    if n != 1:
        sys.exit("could not find <body> to insert the site bar")
    return out


def home(slug, eng, arch):
    m = eng["meta"]
    acct = m.get("account_short") or m["account"]
    d = m.get("dates", {})
    st = m.get("outcome_status", "")
    cb = m.get("case_badge")
    # Outcome tag gets its own line under the title so it can never wrap mid-pill.
    outcome_line = (f'<div class="outcome">Outcome <span class="pill head-pill {esc(st)}">{esc(STATUS.get(st, st))}</span></div>') if st else ""
    highlights = (f'<aside class="highlights" aria-labelledby="h-hl"><h2 id="h-hl">Highlights</h2><p>{esc(m.get("headline"))}</p></aside>\n') if m.get("headline") else ""
    case_tag = (f' <span class="pill case-pill {esc(cb["cls"])}" title="{esc(cb["detail"])}">{esc(cb["short"])} {esc(cb["label"])}</span>') if cb else ""
    built = "".join(
        f'<li><span class="pill {esc(b.get("status"))}">{esc(STATUS.get(b.get("status"), b.get("status")))}</span>'
        f'<span>{esc(b["name"])}</span></li>' for b in eng.get("built", []))
    team = ", ".join(esc(t["name"]) for t in m.get("team", [])[:4])
    am = arch["meta"] if arch else {}
    cards = [("retrospective", "Internal retrospective",
              "What was asked, what we built, where it got hard, lessons and the risk read.")]
    if arch:
        cards.append(("architecture", "Architecture", am.get("subtitle", "")))
    card_html = "".join(f'<a class="card" href="/{p}"><b>{esc(t)}</b><p>{esc(x)}</p><span aria-hidden="true">Open →</span></a>'
                        for p, t, x in cards)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{esc(acct)} · Engagement (internal)</title>{FONTS}
<style>
:root{{--paper:oklch(0.984 0.004 250);--sheet:oklch(0.996 0.002 250);--ink:oklch(0.23 0.025 258);--ink-2:oklch(0.42 0.022 256);
--ink-3:oklch(0.52 0.018 255);--rule:oklch(0.905 0.008 250);--brand:oklch(0.5 0.155 252);--brand-deep:oklch(0.33 0.1 256);
--ok:oklch(0.45 0.11 155);--ok-soft:oklch(0.96 0.03 155);--sbx:oklch(0.47 0.08 200);--paused:oklch(0.47 0.06 290);--paused-soft:oklch(0.97 0.015 290);--sbx-soft:oklch(0.965 0.025 200);--caution:oklch(0.46 0.11 62);--caution-soft:oklch(0.967 0.035 85);
--bad:oklch(0.5 0.17 27);--bad-soft:oklch(0.965 0.025 27);--brand-soft:oklch(0.955 0.022 250);
--sans:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"Geist Mono",ui-monospace,Menlo,monospace}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:1.0625rem/1.65 var(--sans)}}
a{{color:var(--brand)}}:focus-visible{{outline:2px solid var(--brand);outline-offset:2px}}
header{{background:var(--brand-deep);color:#fff;padding:2.5rem 1.5rem 2.25rem}}.wrap{{max-width:76rem;margin:0 auto}}
.crumbs{{font:500 .76rem var(--mono);letter-spacing:.05em;text-transform:uppercase;opacity:.85}}
h1{{font-size:clamp(1.8rem,3.4vw,2.6rem);line-height:1.15;margin:.6rem 0 .6rem;letter-spacing:-.01em;max-width:48rem}}
.highlights{{background:var(--brand-soft);border:1px solid var(--rule);border-radius:.85rem;padding:1.1rem 1.4rem;margin:.5rem 0 0;max-width:62rem}}
.highlights h2{{font:600 .78rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:0 0 .6rem}}.highlights p{{margin:0;font-size:1.02rem;line-height:1.6}}
.facts{{display:flex;flex-wrap:wrap;gap:.5rem 1.75rem;margin-top:1.25rem;font:400 .82rem var(--mono);opacity:.9}}
main{{padding:2rem 1.5rem 4rem}}h2{{font-size:1.25rem;margin:2.25rem 0 .9rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1rem}}
.card{{display:block;background:var(--sheet);border:1px solid var(--rule);border-left:4px solid var(--brand);border-radius:12px;padding:1.1rem 1.25rem;text-decoration:none;color:var(--ink)}}
.card:hover{{border-color:var(--brand)}}.card b{{font-size:1.1rem}}.card p{{margin:.3rem 0 .6rem;color:var(--ink-2);font-size:.95rem}}
.card span{{font:600 .8rem var(--mono);color:var(--brand)}}
ul.built{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(22rem,1fr));gap:.5rem}}
ul.built li{{display:flex;gap:.75rem;align-items:center;background:var(--sheet);border:1px solid var(--rule);border-radius:10px;padding:.55rem .8rem}}
.pill{{flex:none;min-width:9.6rem;text-align:center;font:600 .72rem var(--mono);padding:.15rem .5rem;border-radius:99px;border:1px solid currentColor;white-space:nowrap}}
.pill.live_production{{color:var(--ok);background:var(--ok-soft)}}.pill.live_sandbox{{color:var(--sbx);background:var(--sbx-soft)}}.pill.completed{{color:var(--brand);background:var(--brand-soft)}}
.pill.in_build,.pill.planned{{color:var(--caution);background:var(--caution-soft)}}.pill.cancelled{{color:var(--bad);background:var(--bad-soft)}}.pill.paused{{color:var(--paused);background:var(--paused-soft)}}
.case-pill{{min-width:0;margin-left:.4rem;background:#fff;vertical-align:.05rem}}
.pill.case-completed{{color:var(--ok)}}.pill.case-active{{color:var(--brand)}}.pill.case-hold{{color:var(--caution)}}.pill.case-cancelled{{color:var(--bad)}}
.outcome{{display:flex;align-items:center;gap:.6rem;margin:0 0 1rem;font:500 .78rem var(--mono);letter-spacing:.06em;text-transform:uppercase;color:#c9d6ea}}
.head-pill{{min-width:0;background:#fff;text-transform:none;letter-spacing:0}}
footer{{color:var(--ink-3);font-size:.85rem;margin-top:2.5rem}}
</style>{bar_css()}</head><body>{bar(acct, "home")}
<header><div class="wrap"><div class="crumbs">{esc(m["account"])} · Case {esc(m.get("case_number"))}{case_tag} · Internal</div>
<h1>{esc(m.get("title"))}</h1>
{outcome_line}
<div class="facts"><span>{esc(d.get("start"))} – {esc(d.get("end"))} ({esc(d.get("duration"))})</span><span>{esc(m.get("engagement_type"))}</span><span>{team}</span></div>
</div></header>
<main><div class="wrap">
{highlights}<h2>Documents</h2><div class="cards">{card_html}</div>
<h2>What we built</h2><ul class="built">{built}</ul>
<footer>Internal to Salesforce. Updated {esc(m.get("updated"))}.</footer>
</div></main></body></html>"""


SERVER_JS = """// Zero-dependency static server. Only the routes below are served; everything else is 404.
const http = require("http");
const fs = require("fs");
const path = require("path");

const PUB = path.join(__dirname, "public");
const ROUTES = { "/": "index.html", "/retrospective": "retrospective.html", "/architecture": "architecture.html" };
const HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Cache-Control": "no-cache",
  "X-Robots-Tag": "noindex, nofollow",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

http.createServer((req, res) => {
  const url = (req.url || "/").split("?")[0].replace(/\\/+$/, "") || "/";
  const file = ROUTES[url] || ROUTES[url.replace(/\\.html$/, "")];
  if (req.method !== "GET" && req.method !== "HEAD") { res.writeHead(405); return res.end(); }
  if (!file) { res.writeHead(404, { "Content-Type": "text/plain" }); return res.end("Not found"); }
  fs.readFile(path.join(PUB, file), (err, body) => {
    if (err) { res.writeHead(500); return res.end(); }
    res.writeHead(200, HEADERS);
    res.end(req.method === "HEAD" ? undefined : body);
  });
}).listen(process.env.PORT || 5005, () => console.log(`listening on ${process.env.PORT || 5005}`));
"""


REACT_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site-react")
REACT_SKIP = {"node_modules", ".next", "out", "next-env.d.ts", "tsconfig.tsbuildinfo"}


def arch_parts(html_src):
    """Split the rendered architecture page into its styles and its body for the React page."""
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html_src, re.S))
    body = re.search(r"<body[^>]*>(.*)</body>", html_src, re.S).group(1)
    if re.search(r"<script|\son\w+\s*=|javascript:", body + style, re.I):
        sys.exit("architecture page has scripts or event handlers; it can't be embedded")
    return style, body


def build_react(d, slug, eng, arch, acct):
    """React site: copy the shared Next.js app from site-react/ and write its data file.

    Only three things land in <dir>/site/: the app source (from the skill), src/data/site.json
    (the internal-scoped record) and public/brand/ (the two logos). The customer recap,
    engagement.json and raw files never do. Heroku runs `npm run build` on push.
    """
    from render import scope, case_badge
    out = os.path.join(d, "site")
    os.makedirs(out, exist_ok=True)
    keep = {"node_modules", ".next", "out", "package-lock.json", "next-env.d.ts"}
    for f in os.listdir(out):  # clear everything we generate, so nothing stale lingers
        if f in keep:
            continue
        pth = os.path.join(out, f)
        shutil.rmtree(pth) if os.path.isdir(pth) else os.remove(pth)
    shutil.copytree(REACT_TEMPLATE, out, dirs_exist_ok=True,
                    ignore=lambda _dir, names: [n for n in names if n in REACT_SKIP or n == "package-lock.json" and _dir != REACT_TEMPLATE])
    data = scope(copy.deepcopy(eng), "internal")
    data["meta"]["case_badge"] = case_badge(eng["meta"].get("case_status"))
    data.pop("leak_terms", None)
    brand = None
    bd = os.path.join(d, "brand")
    if BRAND:
        os.makedirs(os.path.join(out, "public", "brand"), exist_ok=True)
        cust = sorted(f for f in os.listdir(bd) if f != "salesforce.svg" and f.endswith((".svg", ".png")))
        cust.sort(key=lambda f: not f.endswith(".svg"))
        for f in ("salesforce.svg", cust[0]):
            shutil.copy(os.path.join(bd, f), os.path.join(out, "public", "brand", f))
        brand = {"sf": "/brand/salesforce.svg", "cust": f"/brand/{cust[0]}", "kind": "svg" if cust[0].endswith(".svg") else "png"}
    ap = os.path.join(d, f"{slug}-architecture.html")
    arch_data = None
    if os.path.exists(ap):
        style, body = arch_parts(open(ap).read())
        arch_data = {"subtitle": (arch or {}).get("meta", {}).get("subtitle", ""), "style": style, "body": body}
    else:
        shutil.rmtree(os.path.join(out, "src", "app", "architecture"), ignore_errors=True)
    site = {"slug": slug, "account": acct, "sidebar": SIDEBAR, "brand": brand,
            "pages": ["retrospective"] + (["architecture"] if arch_data else []),
            "arch": arch_data, "eng": data}
    with open(os.path.join(out, "src", "data", "site.json"), "w") as f:
        json.dump(site, f, indent=1, ensure_ascii=False)
    pkg = json.load(open(os.path.join(out, "package.json")))
    pkg["name"] = f"{slug}-engagement-internal"
    pkg["description"] = f"Internal engagement site for {acct}: retrospective and architecture"
    open(os.path.join(out, "package.json"), "w").write(json.dumps(pkg, indent=2) + "\n")
    pub = sorted(os.path.relpath(os.path.join(r, f), out) for r, _, fs in os.walk(os.path.join(out, "public")) for f in fs)
    bad = [f for f in pub if not f.startswith("public/brand/")]
    if bad:
        sys.exit(f"unexpected files in site/public: {bad}")
    print(f"wrote {out} (React): src/data/site.json, {', '.join(pub) or 'no brand'}; run npm install && npm run build to preview")


def main():
    d = os.path.abspath(sys.argv[1].rstrip("/"))
    slug = os.path.basename(d)
    eng = json.load(open(os.path.join(d, "engagement.json")))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from render import check_status, case_badge
    eng["meta"]["case_badge"] = case_badge(eng["meta"].get("case_status"))
    check_status(eng)
    ap = os.path.join(d, "architecture.json")
    arch = json.load(open(ap)) if os.path.exists(ap) else None
    acct = eng["meta"].get("account_short") or eng["meta"]["account"]
    global BRAND, AVAILABLE, SIDEBAR
    sp = os.path.join(d, "site.json")
    cfg = json.load(open(sp)) if os.path.exists(sp) else {}
    SIDEBAR = cfg.get("sidebar", True)
    AVAILABLE = {r for r, _, pat in PAGES if os.path.exists(os.path.join(d, pat.format(slug=slug)))}
    if "retrospective" not in AVAILABLE:
        sys.exit(f"missing {slug}-internal-retrospective.html; render it first")
    # The Salesforce logo ships with the skill, so only the customer logo is per account.
    bd = os.path.join(d, "brand")
    if os.path.isdir(bd) and not os.path.exists(os.path.join(bd, "salesforce.svg")):
        shutil.copy(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "salesforce.svg"), bd)
    BRAND = brand_chip(d, acct)
    if not BRAND and "--no-logo" not in sys.argv:
        sys.exit(f"no customer logo: add {slug}/brand/{slug}.svg (or .png) "
                 "(see 'Logos in the site bar' in SKILL.md), or pass --no-logo if the user agreed to skip it")
    build_react(d, slug, eng, arch, acct)  # every site is the Next.js app in site-react/

if __name__ == "__main__":
    main()
