#!/bin/sh
# One-time setup for engagement-exit-plus. Run from the skill folder: ./setup.sh
cd "$(dirname "$0")" || exit 1
ok=1
need() { if command -v "$1" >/dev/null 2>&1; then echo "ok    $1"; else echo "MISSING $1: $2"; ok=0; fi; }
need python3 "install Python 3"
need node "install Node 20+ (brew install node)"
need npm "comes with Node"
need git "install git"
need gh "brew install gh, then gh auth login"
need sf "npm install -g @salesforce/cli"
if [ ! -d .venv ]; then python3 -m venv .venv || exit 1; fi
.venv/bin/pip install -q jinja2 && echo "ok    python venv (.venv, jinja2)"
if command -v sf >/dev/null 2>&1; then
  if sf org list --json 2>/dev/null | grep -q "org62.my.salesforce.com"; then echo "ok    Org62 login"
  else echo "MISSING Org62 login: sf org login web --instance-url https://org62.my.salesforce.com --alias org62"; ok=0; fi
fi
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then echo "ok    Google Chrome"
else echo "note  Google Chrome not at the macOS path; screenshot checks need Chrome or Chromium"; fi
echo "Also needed in Claude Code: the Slack connector."
[ $ok = 1 ] && echo "Setup looks good." || { echo "Fix the MISSING items above, then run ./setup.sh again."; exit 1; }
