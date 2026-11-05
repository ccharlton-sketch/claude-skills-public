---
name: architecture-diagram
description: Build a clean, customer-shareable architecture diagram for an account as a single-file HTML page (inline SVG, numbered flow lines, "How it works" steps underneath, today/next cards). Drafts a small JSON spec of zones, nodes and edges from what the user describes plus the case, Slack and product docs, renders it, checks it visually and publishes it next to the account's readout. Use when the user asks for an architecture diagram, solution diagram, "what it looks like" visual or integration picture for a customer.
user-invocable: true
argument-hint: <client_slug> [notes]
---

# Architecture Diagram

One JSON spec, one renderer, one HTML file. No build step, no external images. Keep it simple and not wordy: the picture carries the story, the steps underneath explain it.

Paths:
- Renderer: `~/.claude/skills/architecture-diagram/scripts/render_arch.py` (stdlib Python 3 only; icons from `assets/icons.json`)
- Output: `$READOUTS/<slug>/architecture.json` and `<slug>-architecture.html`, where `$READOUTS` is your private readouts repo (the same one engagement-exit-plus uses).
- Worked examples: `references/example-mcp.json` (one view) and `references/example-views.json` (built vs positioned-then-cancelled). Copy the closer one as the starting point for a new account.

## 1. Gather

- **The user's description comes first.** It is the source of truth for what the architecture is.
- **Check what's already known:** if `$READOUTS/<slug>/engagement.json` exists, read it for the systems, what's live and what's next.
- **Slack**, read-only (ToolSearch `+slack`): search `<account>` plus terms like MCP, Azure, Snowflake, data lake, React, Coworker, Data 360 or SSO. Look for systems the user didn't mention. Add them only if they fit, and mark them `exploring` if they were only discussed.
- **Product names:** look up the exact Salesforce names with `salesforce_docs_search`.
  - Hosted MCP servers are under the collection `developer/hosted-mcp-servers`.
  - The standard servers are `sobject-reads`, `sobject-mutations`, `sobject-deletes`, `sobject-all`, `api-context`, plus Data 360 and Tableau Next.
  - Every tool call runs as the signed-in user, so FLS, object permissions and sharing apply.
- **Never invent systems, products or connections.** If a link between two boxes is a guess, ask the user or leave it out.

## 2. Draft the spec

Zones are columns, read left to right. A good default is four:
1. People
2. Where they work: the UI or AI client
3. Connection layer: MCP, APIs, integration
4. Systems of record

```json
{
  "meta": {"slug": "acme", "account": "Acme", "title": "...", "subtitle": "one or two sentences", "updated": "Month YYYY"},
  "zones": [{"id": "people", "label": "People", "nodes": [
    {"id": "emp", "title": "Employees", "sub": "short line", "icon": "lucide:users"},
    {"id": "gpt", "title": "ChatGPT", "icon": "logos:openai-icon", "kind": "list", "sub": "...", "items": [{"label": "Skill A", "icon": "lucide:sparkles"}, {"label": "sobject-reads", "mono": true}]},
    {"id": "sfmcp", "title": "Salesforce hosted MCP", "icon": "logos:salesforce", "badge": "logos:model-context-protocol-icon"},
    {"id": "next", "title": "...", "state": "planned", "tag": "NEXT", "gap_before": 40}
  ]}],
  "edges": [{"from": "emp", "to": "gpt", "step": 1},
            {"from": "a", "to": "b", "state": "planned", "route": "bottom", "lane": 1, "dx_to": -40},
            {"from": "a", "to": "b", "both": true, "dy_from": -30}],
  "steps": [{"n": 1, "title": "...", "text": "one sentence"}, {"n": 6, "state": "planned", "title": "Next: ...", "text": "..."}],
  "cards_title": "Today and next",
  "cards": [{"title": "In place today", "text": "..."}, {"title": "Next", "state": "planned", "text": "..."}]
}
```

**Icons.** Give every node an `icon`. Add a `badge` to show what kind of thing it is, like the MCP logo on an MCP server or a database on a data store. Chips can carry an `icon` too.
- Brand logos come from the Iconify "logos" set (full color): `logos:openai-icon` (ChatGPT), `logos:react`, `logos:salesforce`, `logos:azure-icon`, `logos:model-context-protocol-icon`, `logos:slack-icon`, `logos:tableau-icon`, `logos:microsoft-teams`, `logos:anthropic-icon`.
- Generic line icons come from Lucide and are drawn in brand ink: `lucide:users`, `lucide:user-round`, `lucide:database`, `lucide:bot`, `lucide:shield-check`, `lucide:sparkles`, `lucide:server`, `lucide:app-window`, `lucide:lock`, `lucide:cloud`, `lucide:workflow`, `lucide:key-round`, `lucide:building-2`.
- Everything is bundled offline in `assets/icons.json`. Add more with `python3 scripts/add_icons.py logos:snowflake-icon lucide:mail`, which pulls from npm into /tmp. Browse names at icon-sets.iconify.design/logos and lucide.dev/icons.
- There is no logo for Coworker, Data 360 or Headless 360. Use `logos:salesforce` with a badge, or a Lucide icon.

**States:**
- `current` (solid, brand blue): in place today.
- `planned` (dashed, amber): committed next step.
- `exploring` (dotted, grey): discussed but not decided.
- `cancelled` (dashed, rose): positioned, approved or tried, then stopped for good or replaced.
- `paused` (long dash, violet): on hold and could come back, like waiting on a security review.

`shelved` is retired and the renderer rejects it. If it's unclear whether something stopped for good, ask the user.

Use them honestly, the same way Live and Completed work in the readouts. Anything the user describes in the future tense ("they are going to connect", "they plan to") is `planned`, not `current`. Systems the customer already runs, like their data lake, are `current` even when our connection to them is planned.

**Before and after (views).** To show how an architecture changed, like what was built and then what we positioned, put a `views` array in the spec instead of top-level `zones`/`edges`/`steps`. Each view has `title`, optional `pill` + `pill_state`, `intro`, and its own `zones`, `edges` and `steps`. Cards stay top-level and come after all views. The legend shows only the states each view uses, and `legend_labels` (top-level or per view) overrides the wording (for example `{"current": "In place"}` when the "today" framing doesn't fit). Worked example: `references/example-views.json`.

**Edges:**
- An edge between columns draws a curve from the right side of one node to the left side of the other.
- An edge within a column draws a straight vertical line.
- `route: "bottom"` sends the line along a lane under the diagram. Use it when a line would cross other columns, like Salesforce users going straight to Salesforce.
- Give each bottom edge its own `lane` (0, 1, ...) and offset `dx_to` so the arrows don't overlap.
- `dy_from` and `dy_to` nudge where a line starts and ends on a node's side.

**The Salesforce band (default).** When any of the work runs in Salesforce, draw a "Salesforce" band around the zones that live there. The people who work in Salesforce go inside it too (service reps, technicians and sellers working a record), so the picture never shows Salesforce as a separate box with its users outside. Systems that aren't Salesforce stay outside the band: email, OneNote, SharePoint, a data lake, ChatGPT, a React app, the customer's own systems.

```json
"groups": [{"label": "Inside Salesforce: everything here runs on the Case object", "from": "sf", "to": "people", "icon": "logos:salesforce"}]
```

- `groups` goes on each view (or at the top level for a one-view spec). `from` and `to` are zone ids, and the band covers every zone between them, so **order the zones so the Salesforce ones sit next to each other**. Outside sources go on the left and outside consumers on the right.
- Label it with where the work happens, and name the object when there is one ("Inside Salesforce: everything here runs on the Case object"). Plain "Inside Salesforce" is fine otherwise.
- Inside the band, give people nodes `logos:salesforce` with a role badge (`lucide:headset`, `lucide:users`), and say in their subtitle that they work in Salesforce ("Work each Case in Salesforce from their queue").
- Put a column of people outside the band only when they really work somewhere else, such as customers emailing in or staff using ChatGPT.
- Skip the band only when nothing in the view runs in Salesforce. The renderer prints a warning when a view has Salesforce nodes and no group.
- The same `groups` key works for another platform that holds several zones, like "Customer's Azure tenant". Use at most one band per view unless two systems really sit side by side.
- Worked example: `references/example-groups.json`, view 2.

**Layout:**
- Each column's stack is centered vertically. Use `gap_before` to line nodes up with what they connect to.
- Put a node that connects to a bottom-routed line at the bottom of its column, so the line doesn't pass through another box.

**Writing rules:**
- Plainspoken, no Oxford comma.
- Node subtitles stay under about 8 words. Steps are one sentence each.
- Keep it to 7 steps or fewer.
- Customer-shareable by default: no deal sizes, no internal names, no competitor commentary, no case or DSR numbers.

## 3. Render and check

```bash
python3 ~/.claude/skills/architecture-diagram/scripts/render_arch.py <dir>/architecture.json
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --screenshot=/tmp/arch.png --window-size=1280,1600 file://<dir>/<slug>-architecture.html
```

Read the PNG and fix these before showing the user:
- lines passing behind boxes
- step badges hidden under a node
- arrows landing on the wrong box
- wrapped titles
- Salesforce work without a Salesforce band, or a box inside the band that isn't Salesforce

Usually the fix is reordering nodes, `gap_before`, a bottom route or a `dy` nudge.

## 4. Publish

The same rule as the readouts applies:
1. Add a line for the diagram to the README "Architecture diagrams" list.
2. If `<slug>-internal-retrospective.html` exists, rebuild the account's internal site so it picks up the diagram: `~/.claude/skills/engagement-exit-plus/.venv/bin/python ~/.claude/skills/engagement-exit-plus/scripts/build_site.py <dir>`.
3. Check that the repo is PRIVATE.
4. Run `git add`, then commit and push.
5. Give the user the local URL `http://127.0.0.1:8765/<slug>/<slug>-architecture.html`. That server runs from the repo root; start it with `python3 -m http.server 8765 --bind 127.0.0.1` if it isn't running.
6. List anything you inferred so they can confirm it.

Never enable GitHub Pages.
