#!/usr/bin/env python3
"""Refresh meta.case_status in <dir>/engagement.json from the live Org62 Case.

Usage: case_status.py <dir> [<dir> ...]
Read-only against Org62. Edits only the one "case_status" line in engagement.json
so the rest of the file keeps its formatting. Run before every render.
"""
import json, os, re, sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gather_org62 import token, soql  # noqa: E402


def fmt(d):
    return f"{d:%b} {d.day}, {d.year}"


def main():
    dirs = [os.path.abspath(a.rstrip("/")) for a in sys.argv[1:]]
    tok = token()
    for d in dirs:
        p = os.path.join(d, "engagement.json")
        raw = open(p).read()
        meta = json.loads(raw)["meta"]
        num = meta.get("case_number")
        if (meta.get("case_status") or {}).get("source") == "manual":
            print(f"{os.path.basename(d)}: status set manually ({meta['case_status']['status']}), left as is")
            continue
        if not num:
            print(f"{os.path.basename(d)}: no case_number, skipped")
            continue
        rec = soql(tok, f"SELECT Status, IsClosed, ClosedDate FROM Case WHERE CaseNumber = '{num}'")
        if not rec:
            print(f"{os.path.basename(d)}: case {num} not found, skipped")
            continue
        r = rec[0]
        cs = {"status": r["Status"], "closed": bool(r["IsClosed"]), "checked": fmt(date.today())}
        if r.get("ClosedDate"):
            cs["closed_date"] = fmt(datetime.fromisoformat(r["ClosedDate"][:10]))
        line = '"case_status": ' + json.dumps(cs, ensure_ascii=False)
        if '"case_status":' in raw:
            raw = re.sub(r'"case_status":\s*\{[^{}]*\}', lambda _: line, raw, count=1)
        else:
            m = re.search(r'^(\s*)"case_number":\s*"[^"]*",?\s*$', raw, re.M)
            if not m:
                sys.exit(f"{p}: can't find the case_number line to insert after")
            indent, cur = m.group(1), m.group(0).rstrip()
            if cur.endswith(","):   # more keys follow: new line also needs a trailing comma
                new = f"{cur}\n{indent.lstrip(chr(10))}{line},"
            else:                   # case_number was the last key
                new = f"{cur},\n{indent.lstrip(chr(10))}{line}"
            raw = raw[:m.start()] + new + raw[m.end():]
        json.loads(raw)
        open(p, "w").write(raw)
        print(f"{os.path.basename(d)}: case {num} {cs['status']}" + (f" (closed {cs['closed_date']})" if cs.get("closed_date") else ""))


if __name__ == "__main__":
    main()
