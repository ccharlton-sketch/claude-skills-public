#!/usr/bin/env python3
"""Render internal/customer HTML from engagement.json.

Usage: render.py <engagement.json> [internal|customer|both]
Writes <case#>-internal.html / <case#>-customer.html next to the JSON and
runs a leak check on the customer file (exit code 2 on any hit).
"""
import copy, json, os, re, sys
from jinja2 import Environment, FileSystemLoader, StrictUndefined, ChainableUndefined
from markupsafe import Markup, escape

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "templates")
DROP = object()
CUSTOMER_EXCLUDED_KEYS = {"internal_notes", "closeout", "case_status"}
OUTNAME = {"internal": "internal-retrospective", "customer": "customer-recap"}
BANNED = [r"\borg62\b", r"\bslack\b", r"\brung\b", r"attrition", r"risk read", r"\bDS-\d{6,}",
          r"\bCase \d{8}\b", r"internal only", r"lightning\.force\.com", r"\bCRA\b", r"\bFDE pod\b"]


# Text fields may hold [label](https://url) links to real records (Org62, Slack canvases, channels).
# Internal pages render them as links; customer output and the case comment keep only the label.
LINK = re.compile(r"\[([^\]\n]+)\]\((https://[^)\s]+)\)")


def plain(s):
    return LINK.sub(r"\1", s) if isinstance(s, str) else s


def linkify(v):
    if not isinstance(v, str) or isinstance(v, Markup):
        return v
    return Markup(LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', str(escape(v))))


def scope(obj, aud):
    """Drop items for the other audience; apply `customer` overrides when aud=customer."""
    if isinstance(obj, dict):
        a = obj.get("audience", "shared")
        if (aud == "customer" and a == "internal") or (aud == "internal" and a == "customer"):
            return DROP
        o = dict(obj)
        if aud == "customer" and isinstance(o.get("customer"), dict):
            o.update(o["customer"])
        o.pop("customer", None)
        o.pop("audience", None)
        out = {}
        for k, v in o.items():
            if aud == "customer" and k in CUSTOMER_EXCLUDED_KEYS:
                continue
            s = scope(v, aud)
            if s is not DROP:
                out[k] = s
        return out
    if isinstance(obj, list):
        return [x for x in (scope(i, aud) for i in obj) if x is not DROP]
    return plain(obj) if aud == "customer" else obj


def check_status(e):
    """Plain "live" and "shelved" are retired: say sandbox or production, cancelled or paused."""
    retired = {"live": "live_sandbox or live_production", "shelved": "cancelled or paused"}
    items = [(b.get("name", "?"), b.get("status")) for b in e.get("built", [])]
    items.append(("meta.outcome_status", e.get("meta", {}).get("outcome_status")))
    bad = [f"{n} ({s}: use {retired[s]})" for n, s in items if s in retired]
    if bad:
        sys.exit("retired status, pick one of the specific ones: " + "; ".join(bad))
    # Products are software, so a product is never "completed": it reached sandbox or production, or it stopped.
    ok = {"live_production", "live_sandbox", "cancelled", "paused", "planned", "in_build"}
    m = e.get("meta", {})
    prod = [x for k in ("products", "related_platform") for x in m.get(k, []) if isinstance(x, dict)]
    bad = [f"{x.get('name')} ({x.get('status')})" for x in prod if x.get("status") not in ok]
    bad += [f"{x.get('name')} (reached {x.get('reached')})" for x in prod
            if x.get("reached") not in (None, "live_sandbox", "live_production")]
    if bad:
        sys.exit("product status must be one of " + ", ".join(sorted(ok)) + " (reached: live_sandbox or "
                 "live_production). Advisory or demo-only work is not a product; leave it off: " + "; ".join(bad))


def internal_strings(obj, inside=False, acc=None):
    """Collect long strings that only exist in internal-scoped parts of the record."""
    acc = [] if acc is None else acc
    if isinstance(obj, dict):
        here = inside or obj.get("audience") == "internal"
        for k, v in obj.items():
            if k == "customer":
                continue
            internal_strings(v, here or k in CUSTOMER_EXCLUDED_KEYS, acc)
    elif isinstance(obj, list):
        for v in obj:
            internal_strings(v, inside, acc)
    elif isinstance(obj, str) and inside and len(obj) > 30:
        acc.append(obj)
    return acc


def case_badge(cs):
    """Map the live Org62 Case status to a colored tag: Completed green, Active blue, On hold yellow."""
    if not cs or not cs.get("status"):
        return None
    st = cs["status"]
    if cs.get("closed"):
        if re.search(r"cancel|declin|reject", st, re.I):
            cls, label = "case-cancelled", "Cancelled"
        else:
            cls, label = "case-completed", "Completed"
    elif re.search(r"hold|waiting|pending", st, re.I):
        cls, label = "case-hold", "On hold"
    else:
        cls, label = "case-active", "Active"
    manual = cs.get("source") == "manual"
    bits = [] if st.lower() == label.lower() else [("status " if manual else "Org62 status ") + st]
    if cs.get("closed_date"):
        bits.append(f"closed {cs['closed_date']}")
    if manual:
        bits.append(f"set manually {cs['checked']}" if cs.get("checked") else "set manually")
    elif cs.get("checked"):
        bits.append(f"checked {cs['checked']}")
    return {"cls": cls, "label": label, "detail": ", ".join(bits),
            "heading": "Engagement status" if manual else "Case status", "short": "Engagement" if manual else "Case"}


def video_info(v):
    if not v or not v.get("url"):
        return None
    m = re.search(r"vidyard\.com/(?:watch/)?([A-Za-z0-9_-]{10,})", v["url"])
    if not m:
        return {**v, "id": None}
    vid = m.group(1)
    return {**v, "id": vid, "watch_url": v.get("watch_url") or f"https://share.vidyard.com/watch/{vid}"}


def closeout_text(e):
    c = e.get("closeout", {})
    items = c.get("open_items") or []
    lines = [
        f"Engagement outcome: {c.get('outcome', '')}",
        f"Value: {c.get('value', '')}",
        "Open items: " + ("; ".join(f"{i['item']} / {i.get('owner', 'TBD')} / {i.get('date', 'TBD')}" for i in items) or "None"),
        f"Anticipated next steps for the customer: {c.get('next_steps', '')}",
        f"90-day check-in: {c.get('checkin', 'Not scheduled')}",
        f"Exit Docs: {c.get('exit_docs', 'TBD')}",
    ]
    return plain("\n".join(lines))


def render(e, aud, out_dir):
    env = Environment(loader=FileSystemLoader(TPL), autoescape=True, undefined=ChainableUndefined,
                      trim_blocks=True, lstrip_blocks=True, finalize=linkify)
    data = scope(copy.deepcopy(e), aud)
    data["m"] = data.pop("meta")
    data["m"]["video"] = video_info(data["m"].get("video"))
    data["m"]["case_badge"] = case_badge(data["m"].get("case_status")) if aud == "internal" else None
    for k in ["request", "built", "timeline", "challenges", "worked", "change", "lessons", "value",
              "readiness", "next_steps", "checkin", "direction", "quotes", "internal_notes"]:
        data.setdefault(k, None)
    if aud == "internal":
        data["closeout_text"] = closeout_text(e)
    html = env.get_template(f"{aud}.html.j2").render(**data)
    path = os.path.join(out_dir, f"{e['meta']['client_slug']}-{OUTNAME[aud]}.html")
    with open(path, "w") as f:
        f.write(html)
    return path, html


def leak_check(e, html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    hits = [p for p in BANNED if re.search(p, text, re.I)]
    hits += [f"term:{t}" for t in e.get("leak_terms", []) if t.lower() in text.lower()]
    hits += [f"internal text: {s[:60]}..." for s in internal_strings(e) if s[:60] in text]
    return hits


def main():
    src = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "internal"
    if mode != "internal":
        sys.exit("the customer recap is retired; render.py only builds the internal retrospective (run without a mode)")
    e = json.load(open(src))
    hl = (e.get("meta") or {}).get("headline") or ""
    sents = [s for s in re.split(r"(?<=[.!?])\s+", hl.strip()) if s]
    long_s = [s for s in sents if len(s.split()) > 22]
    if len(hl) > 360 or len(sents) > 5 or long_s:
        print(f"warning: meta.headline too long ({len(hl)} chars, {len(sents)} sentences"
                 + (f", {len(long_s)} over 22 words" if long_s else "")
                 + "). Highlights is 3 to 5 short sentences, at most 22 words each and 360 characters in all: the problem, what we built, where it landed.", file=sys.stderr)
    check_status(e)
    out_dir = os.path.dirname(os.path.abspath(src))
    status = 0
    for aud in (["internal", "customer"] if mode == "both" else [mode]):
        path, html = render(e, aud, out_dir)
        print(f"wrote {path}")
        if aud == "customer":
            hits = leak_check(e, html)
            if hits:
                status = 2
                print("LEAK CHECK FAILED in customer file:")
                for h in hits:
                    print("  -", h)
            else:
                print("leak check: clean")
    sys.exit(status)


if __name__ == "__main__":
    main()
