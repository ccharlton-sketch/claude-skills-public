# Claude skills

Claude Code skills for closing out Builder Engagements and publishing sites to Experience Cloud.

| Skill | What it does |
|---|---|
| `engagement-exit-plus` | Builds an engagement retrospective from your Builder case (or DSR) in Org62 plus the Slack channels: an internal retrospective, an architecture diagram and a small React site per account. |
| `architecture-diagram` | Draws a clean architecture diagram for an account as a single HTML page. `engagement-exit-plus` uses it, and it also works on its own. |
| `deploy-experience-cloud` | Packages a static site (a Next.js export or any folder with an `index.html`) as a Static Resource, wraps it in an iframe LWC with an optional password screen, deploys both to your org and can create a new LWR Experience Cloud site to host it. |

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

### deploy-experience-cloud

Copy the folder into `~/.claude/skills/`:
```bash
cp -R deploy-experience-cloud ~/.claude/skills/
```
You need the sf CLI logged in to your own org, Node/npm and Python 3. Run it from a Salesforce DX project (one with `sfdx-project.json`). The org needs Digital Experiences enabled, and your user needs permission to create Experience Cloud sites.

Then run `/deploy-experience-cloud <path-to-site> --org <your-org>`. It always asks which org and site name before deploying. Placing the component on a page, guest access and activation stay manual in Experience Builder.

## Use (engagement-exit-plus)

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
