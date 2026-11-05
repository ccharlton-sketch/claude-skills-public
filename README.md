# Claude skills

Two Claude Code skills for closing out Builder Engagements.

| Skill | What it does |
|---|---|
| `engagement-exit-plus` | Builds an engagement retrospective from your Builder case (or DSR) in Org62 plus the Slack channels: an internal retrospective, an architecture diagram and a small React site per account. |
| `architecture-diagram` | Draws a clean architecture diagram for an account as a single HTML page. `engagement-exit-plus` uses it, and it also works on its own. |

## Install

1. Download this repo (green **Code** button, then **Download ZIP**), or clone it.
2. Copy both folders into `~/.claude/skills/`:
   ```bash
   cp -R engagement-exit-plus architecture-diagram ~/.claude/skills/
   ```
3. Run the setup check:
   ```bash
   ~/.claude/skills/engagement-exit-plus/setup.sh
   ```
   It builds the Python environment and tells you what's missing: the sf CLI and an Org62 login, Node, git and gh, Chrome.
4. In Claude Code, connect the Slack connector.

## Use

In Claude Code, run `/engagement-exit-plus` (or just ask for a retrospective for an engagement). With no case number it lists your Builder cases and DSRs and asks which one.

The first time, it asks for:
- a **private** GitHub repo for your readouts (it can create one). Never make that repo public: the readouts are internal.
- your team's Slack channels for field learnings
- your Heroku private space, only if you publish sites there

## What it never does

- Write to Org62. The gather is read-only.
- Post to Slack, or show Slack channels, links or quotes in the output.
- Deploy anywhere without asking you first.

Built for macOS. The examples use fictional accounts (Acme, Northwind, Contoso, Fabrikam).
