# Sections and the engagement.json shape

## engagement.json

Every list item is a dict. Two optional keys work on any dict, at any depth:

- `audience`: `"shared"` (default), `"internal"` (dropped from the customer HTML) or `"customer"` (dropped from the internal HTML).
- `customer`: a dict of field overrides applied only when rendering for the customer, e.g. `{"title": ..., "detail": ...}`. Use it to reword the same fact for the customer instead of duplicating the item.

The top-level key `internal_notes` never reaches the customer render. There is no close-out comment, so don't draft a `closeout` block.

```jsonc
{
  "meta": {
    "case_number": "00000000", "client_slug": "acme",
    "account": "Acme Corp.", "account_short": "Acme",
    "title": "...",                 // internal h1 subject
    "customer_title": "...",        // customer h1 (optional)
    "engagement_type": "Post-ACV Build Advisory",
    "updated": "November 2026",     // the only date in the hero
    "headline": "3-5 short sentences, max 22 words each and 360 chars total: problem, what we built, where it landed", "customer_headline": "...",
    "dates": {"start": "Jun 17, 2026", "end": "Oct 27, 2026", "duration": "about 19 weeks"},
    "opp": {"name", "stage", "amount", "close", "owner"},
    "team": [{"name", "role", "allocation"}],             // internal snapshot
    "customer_contacts": [{"name", "title"}],
    "customer_contacts_sf": [{"name", "role"}],           // "Your Salesforce team" on customer page
    "case_status": {"status": "Delivery", "closed": false, "closed_date": "...", "checked": "Nov 3, 2026"}, // written by case_status.py; internal only
    "outcome_status": "live_sandbox|live_production|completed|in_build|planned|cancelled|paused", // same rules as Built status
    "products": [{"name": "Agentforce Service Agent", "status": "live_production"}],   // Snapshot "Agentforce products"; names from the list below
    "related_platform": [{"name": "Data 360", "status": "live_production"}],          // Snapshot "Related platform"
    "outcome_summary": "...",
    "case_url": "...", "slack_channel": "...", "dsrs": ["DS-... (status)"],
    "video": {"url": "https://share.vidyard.com/watch/<uuid>", "title": "..."}
  },
  "quotes": [{"text", "who"}],
  "request": {"summary", "goals": [{"text"}], "success_criteria": [{"text"}], "out_of_scope": [{"text"}]},
  "built": [{"name", "status", "what"}],                  // status: see "Built status" below
  "timeline": [{"date", "event"}],
  "challenges": [{"title", "detail", "tried", "result"}],
  "worked": [{"point", "takeaway"}],
  "change": [{"point", "takeaway"}],                      // internal page only
  "lessons": [{"text"}],                                   // internal page only
  "value": {"expected", "shown": [{"text"}]},
  "readiness": [{"area": "Environment|Governance|People", "rating": "ready|at_risk|blocked", "note"}],
  "direction": {"summary"},
  "next_steps": [{"step", "owner", "date"}],
  "checkin": {"date", "owner"},
  "internal_notes": {"risk_read", "build_notes_title": "How the build works", "build_notes": [{"title", "text"}], "followups": [{"text"}]},  // build_notes optional: technical design detail for whoever takes over
  "leak_terms": ["words that must never appear in customer output"]
}
```

## Internal retrospective (7 sections)

Sections have plain headings and no numbers: no "01" eyebrows and no numbered section links, on any page (retrospective, customer recap or site). The numbering below is only the order.

1. **Snapshot**: account, opp, engagement type, Agentforce products and related platform (see below), dates, team and allocation, customer contacts, outcome pill, record links. No quotes from Slack, ever: not from the user, the account team or the customer. Only use a quote the customer gave on the record and the user supplied, and leave `quotes` empty otherwise.
2. **What was requested** (site heading: Builder Engagement reason): the intake problem, goals, how success was defined, out of scope. Source: Case Description, Business_Challenge_and_Desired_Outcomes__c, DSR intake, first builder-channel posts.
3. **What we built**: each piece with a status pill, then a dated timeline built from case comments and Slack.
4. **Where it got hard** (site heading: Roadblock items): blockers, product issues, pivots. For each: detail, what we tried, result. Be direct about product gaps and customer constraints.
5. **What worked, what we'd change** (site heading: Field learnings from the team): each point ends with a takeaway. Close with field learnings that apply to other accounts.
6. **Where the customer is headed** (site heading: Account next steps): direction, readiness table, open items with owner and date, 90-day check-in.
7. **Internal notes**: account risk read, optional build notes (`build_notes`: how the build works, for the person taking over; put technical design detail here rather than in Highlights), follow-ups for the account team. Always internal. This is the last section; there is no case close-out comment.

## Customer recap (6 sections)

1. **Why we started**: their goals in their words ("you", "your team").
2. **What we built together**: Vidyard embed first if there is a video, then the pieces table and a short timeline.
3. **What we learned together**: challenges reframed as findings with "Where we landed". Then what worked.
4. **Value so far**.
5. **Production readiness**: Environment / Governance / People.
6. **What's next**: recommendations, steps with owners, check-in, their Salesforce team.

## Case and DSR numbers

Internal copy shows a case or DSR number only as a link to its Org62 record, for example `[Case 00000000](https://org62.lightning.force.com/lightning/r/Case/500.../view)` or `[DS-1677686](https://org62.lightning.force.com/lightning/r/Deal_Support_Request__c/a25.../view)`. Take the Id from the record's `attributes.url` in the raw pulls. A number with no Org62 record behind it (Salesforce Support case numbers, Sev1 numbers from Slack) is left out and described in words.

## Customer-copy rules

- Never in the customer version: internal names outside the account team, product codenames or planner names, competitor names, "failed", "lost faith", rungs, risk reads, DSR or case numbers, Slack or Org62 links, allocation %.
- Product gaps become design findings ("forms inside a conversational agent depend on the agent deciding to show them"), not blame.
- A paused or failed engagement still gets a respectful recap: what was learned, what is live, what we recommend when they revisit.
- Plainspoken. No "seamless/robust/leverage/unlock", no Oxford comma, short sentences. Run `humanizer` over customer copy if it's installed.

## Team process this is loosely based on

The team's Engagement Exit Experience guidance (Go-Fast readout, retrospective facilitation and post mortems). At close the team expects an Exit Docs folder in the builder channel, Case status Completed with the close-out comment, exit scores logged, the 90-day check-in on the calendar, and an explicit handoff.

## Built status

Pick the status by what actually exists, not by whether the task got done.

| Status | Pill | Use for |
|---|---|---|
| `live_sandbox` | Live in sandbox (teal) | Working in the customer's sandbox: an agent, a flow, code, a data stream, or a prompt template that is active there but not yet in production. |
| `live_production` | Live in production (green) | The same, running in the customer's production org with real users or real traffic. |
| `completed` | Completed (light blue) | Finished work that isn't running software: a signed scope, discovery sessions, a design doc, answers to security questions, a demo in our own org or SDO. |
| `in_build` | In build (amber) | Software under construction in the customer's org. |
| `planned` | Planned (amber) | Agreed but not started. |
| `cancelled` | Cancelled (red) | Stopped for good: the customer turned it down, we pivoted away from it, or a planned event was called off. |
| `paused` | Paused (violet) | On hold with a real chance of coming back: waiting on a customer approval, a priority call or a re-engagement. |

Never use a plain `live` or `shelved`. The scripts reject both: "live" reads as production, and "shelved" hides whether it is over or coming back. If you can't tell which org something runs in, or whether a stopped item is cancelled or paused, ask the user. In the `what` text, say why it was cancelled or what it is waiting on. For `outcome_status`, use the furthest point the main piece has reached.

## Agentforce products and related platform

Two Snapshot rows, `meta.products` and `meta.related_platform`, list the products that were **in scope**: built, scoped, planned or started, even if later stopped. Leave out anything only demoed or pitched and turned down, and tools rather than products (Agent Script, Testing Center).

Use these names exactly, so every site reads the same:

- **Agentforce products:** Agentforce Service Agent, Agentforce Employee Agent, Agentforce Coworker, Agentforce Engagement Agent (never "SDR agent"), Agentforce Prospecting Agent, Agentforce Service Assistant (not "Service Rep Assistant"), Agentforce Observability, Prompt Builder (never "Agentforce Prompt Builder"), Momentum
- **Related platform:** Data 360, MCP servers, Claude Force, Tableau Next, Einstein Case Classification, Einstein Article Recommendations

Add a new name only when none of these fits, and add it to this list.

Each item is `{"name", "status"}`, plus `reached` on stopped products. Always set `status`. Products are running software, so the question is how far the product got in the customer's orgs, not whether a task finished. **`completed` is not allowed here** (`render.py` rejects it): a demo, design session or walkthrough of a product means it was not built, so leave it off, or use `planned` if the customer committed to it. When a built piece behind a product is marked `completed` but is actually an agent, flow or prompt template running in their org, fix the built status to sandbox or production too, and ask the user which org if the record doesn't say.

| status | Pill | Pop-up text |
|---|---|---|
| `live_production` | green | "<name> reached production." |
| `live_sandbox` | yellow | "<name> reached sandbox, not yet production." |
| `cancelled` | red | "<name> was cancelled." With `"reached": "live_sandbox"` (or `live_production`): "<name> reached sandbox, then was cancelled." |
| `paused` | grey | "<name> is paused." With `reached`: "<name> reached sandbox, then was paused." |
| `planned`, `in_build` | grey | "<name> is planned, not started." / "<name> is in build." |

A product can be live for only part of the customer's users (a pilot group in production). That still counts as `live_production`; say who has it in the matching `built[]` text.

The tags are clickable. A click opens a small navy pop-up above the tag (with a pointer) holding that sentence; the tag itself never changes size, so nothing on the page moves. Clicking the tag again, clicking elsewhere or pressing Escape closes it. No key line and no hover tooltip. The React site does this in `site-react/src/components/product-pills.tsx`; the HTML retrospective does the same in `templates/internal.html.j2` with a class toggle.

Keep it in step with `built[]`: a product's status is the best status of the built pieces that use it.
