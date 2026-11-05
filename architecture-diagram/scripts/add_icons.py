#!/usr/bin/env python3
"""Add icons to the skill's offline icon library (assets/icons.json).

Usage: add_icons.py logos:openai-icon logos:react lucide:users ...

Sources (installed into a temp dir; nothing is committed but the SVG bodies):
  logos:<name>   Iconify "logos" set (full-color brand logos, CC0)    npm @iconify-json/logos
  lucide:<name>  Lucide line icons (ISC), drawn in the diagram's ink  npm lucide-static
Browse names: https://icon-sets.iconify.design/logos/ and https://lucide.dev/icons
"""
import json, os, re, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(SKILL, "assets", "icons.json")
SRC = "/tmp/arch-icons-src"


def ensure_src():
    if not os.path.isdir(os.path.join(SRC, "node_modules", "lucide-static")):
        os.makedirs(SRC, exist_ok=True)
        subprocess.run("npm init -y >/dev/null && npm i --silent @iconify-json/logos lucide-static",
                       shell=True, cwd=SRC, check=True)


def main():
    ensure_src()
    lib = json.load(open(LIB)) if os.path.exists(LIB) else {}
    logos = json.load(open(os.path.join(SRC, "node_modules/@iconify-json/logos/icons.json")))
    for ref in sys.argv[1:]:
        kind, name = ref.split(":", 1)
        if kind == "logos":
            ic = logos["icons"].get(name)
            if not ic and name in logos.get("aliases", {}):
                ic = logos["icons"][logos["aliases"][name]["parent"]]
            if not ic:
                print(f"not found: {ref}"); continue
            w, h = ic.get("width", logos.get("width", 256)), ic.get("height", logos.get("height", 256))
            lib[ref] = {"w": w, "h": h, "body": ic["body"], "mono": False}
        elif kind == "lucide":
            p = os.path.join(SRC, "node_modules/lucide-static/icons", f"{name}.svg")
            if not os.path.exists(p):
                print(f"not found: {ref}"); continue
            body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", open(p).read(), flags=re.S).strip()
            lib[ref] = {"w": 24, "h": 24, "body": body, "mono": True}
        else:
            print(f"unknown source: {ref}"); continue
        print(f"added {ref}")
    os.makedirs(os.path.dirname(LIB), exist_ok=True)
    json.dump(lib, open(LIB, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
