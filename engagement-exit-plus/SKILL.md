---
name: engagement-exit-plus
description: Build engagement exit artifacts for a Builder Engagement case in Org62 — an internal retrospective (HTML), an architecture diagram and an internal React site per account, in the light Salesforce-blue design (Manrope, floating cards, navy bands). Gathers the case, comments, allocations, opp, DSRs, the account, case and related Slack channels, drafts one engagement record, iterates with the user, then renders. Use when the user is rolling off or closing out an engagement, or asks for a retro or roll-off doc for an engagement.
user-invocable: true
argument-hint: <case#>
---

# Engagement Exit Plus

`render.py` renders only the internal retrospective. There is no customer recap and no slide deck.

One gathered record (`engagement.json`) feeds the outputs below. Research runs once. Rendering is cheap, so iterate on the record, not the HTML.

| Mode | Output |
|---|---|
| `internal` (default) | `<slug>-internal-retrospective.html`: retrospective, 7 sections, ends with the internal notes |
| `site` | `<slug>/site/`: one internal React (Next.js) site with a home page, the retrospective and the architecture (drafted for every engagement). Built automatically on every publish, so it never needs a separate run |

Paths:
- Skill: `~/.claude/skills/engagement-exit-plus/` (Python venv at `.venv/`, with jinja2)
- Run scripts with `~/.claude/skills/engagement-exit-plus/.venv/bin/python`
- Output: `$READOUTS/<client_slug>/`, one folder per customer, where `$READOUTS` is the user's private readouts repo (see "Setup for a new user" below).
  - Files: `<slug>-internal-retrospective.html`, `<slug>-architecture.html`, `architecture.json`, `engagement.json` and `<slug>/site/`. Older accounts may still have a `-customer-recap.html` from before; don't regenerate it.
  - `raw_*.json` is gitignored because it holds customer contact details.
  - After a new engagement, add a row to the README table.
- Section guide and JSON shape: `references/sections.md`. Read it before drafting. Ignore its customer-copy rules; customer overrides aren't needed any more.
- **No close-out comment.** The retrospective ends with the internal notes. Don't draft a `closeout` block, a case close-out comment or a close-out section.
- **No section numbers.** Headings are plain text: no "01" eyebrows and no numbered section links on any page.

## Setup for a new user

Anyone can run this skill against their own cases. Nothing is tied to one person: the scripts look up the running user from their Org62 login, and Slack searches run as whoever is signed in.

1. **Org62 login:** `sf org login web --instance-url https://org62.my.salesforce.com --alias org62`. The scripts use `$ORG62_ALIAS` if set, otherwise the first org62 login the sf CLI knows.
2. **Python venv** in the skill folder: `python3 -m venv .venv && .venv/bin/pip install jinja2`.
3. **Readouts repo:** a **private** GitHub repo of your own, cloned locally, with `raw_*.json` in `.gitignore`. Call its local path `$READOUTS`. If the user hasn't said where it is, ask once. If they don't have one yet, create it: `gh repo create <name> --private --clone`, then add `raw_*.json` to `.gitignore` and commit.
4. **Slack connector** in Claude Code.
5. Your team's Slack channels for field learnings and your Heroku space, if you publish sites. The skill asks for these the first time.
6. **Run `./setup.sh`** from the skill folder. It builds the Python venv and checks for the sf CLI and its Org62 login, Node and npm, git and gh, and Chrome.

This skill is written for macOS (the screenshot checks use the macOS Chrome path). On another OS, point those commands at your Chrome or Chromium.

## 1. Gather (read-only)

0. **Which case?** If the user didn't give a case number, list theirs and ask which one:
   ```bash
   ~/.claude/skills/engagement-exit-plus/.venv/bin/python ~/.claude/skills/engagement-exit-plus/scripts/gather_org62.py --mine
   ```
   This lists the Builder cases they own plus every case they're allocated to (Case_Resource_Allocation__c), with status, account and role. Under that it lists their DSRs from the last 400 days.

   **No case? Fall back to the DSR.** Some engagements never got a Builder case. If the account isn't in the case list, check the DSR list (or query `Deal_Support_Request__c` by account name, read-only) and confirm the DSR with the user. Then pass the DSR number in place of the case number in step 1: `gather_org62.py DS-1234567 $READOUTS/<slug>`. It writes the same `raw_org62.json` from the DSR, its field history, the opp, account DSRs, events and account contacts. In the record, leave `meta.case_number` empty and set `meta.record_label` to the DSR number, `meta.case_url` to the DSR's Org62 link and `meta.case_status` by hand (`"source": "manual"`) from the DSR status. The DSR's `Status_Comments__c` overwrites itself, so the latest note is all there is; the weekly story comes from Slack. Never create or update a case or DSR in Org62 for this.
1. **Org62:**
   ```bash
   ~/.claude/skills/engagement-exit-plus/.venv/bin/python ~/.claude/skills/engagement-exit-plus/scripts/gather_org62.py <case#> $READOUTS/<slug>
   ```
   This writes `raw_org62.json` with:
   - `gathered_by`: the running user's Org62 Id, name and email
   - `slack`: the account channel Id (parsed from the Account's `Slack_Channel_Link__c`) and the case channel name (`Slack_Channel_Name__c`)
   - the case: Description, Business_Challenge_and_Desired_Outcomes__c, CROverall_Notes__c, dates, engagement type, contact, Slack_Channel_Name__c
   - all CaseComments, which are the case owner's weekly status notes (usually dated, like "XX - M/DD" with the author's initials) and the best timeline source
   - Case_Resource_Allocation__c records
   - the related opp
   - account DSRs for the last 400 days (history only; the team now works from cases, so never flag open DSRs as follow-ups)
   - the user's Events on the account
   - the account's Contacts (name and title), so customer contacts in the record use real names and titles instead of first names from Slack

   **Then fan out the rest of the gather to sub-agents in parallel.** Run the Org62 step yourself first, because the agents need its channel Ids, dates and team. Then send all four Agent calls (`general-purpose`) in one message, so they run at the same time. Each agent does a share of steps 2 and 3 below and the logo:

   | Agent | Covers | Writes |
   |---|---|---|
   | A: case and account channels | Slack 2.1 account channel and 2.2 case channel, threads included | `raw_slack_channels.json` |
   | B: other channels and the team's view | Slack 2.3 other account channels plus the "Everyone else" search | `raw_slack_others.json` |
   | C: the user's own trail | the user's posts, DMs and group DMs, the team channels and linked canvases | `raw_slack_mine.json` |
   | D: logo and local files | `brand/` setup (see "Logos in the site bar") and step 3 local files | `brand/` files and `raw_local.json` |

   Each brief has to stand on its own, because an agent sees only its prompt. Include:
   - the account, the slug folder path, the case number, the engagement start date and (if known) the date the user exited
   - the channel Ids and names from `raw_org62.json`, the team list and the user's Slack Id
   - the exact steps it owns, copied from this section
   - read only: never post, react or write to Slack or Org62

   Each agent writes a JSON list of facts, not prose and not message dumps. Each fact has these fields:
   - `date`
   - `who`
   - `fact`: a paraphrase in one or two sentences
   - `source`: the channel name, plus the permalink when there is one
   - `kind`: `built`, `decision`, `blocker`, `pivot`, `risk`, `next`, `lesson` or `other`
   - `after_exit`: true when it happened after the user rolled off

   It also lists the channels it couldn't find or read. It ends with a reply under 200 words: counts, the five most important facts and any gaps. **No quotes:** agents paraphrase and never copy Slack wording into the fact text.

   While they run, read `raw_org62.json` yourself. Don't repeat their searches. When they finish, read the four files and draft from them:
   - Drop anything with `after_exit` true, and any work other people did after the user left.
   - If something is surprising or would change the story (a pivot, a cancellation, a production claim), check it yourself in Slack before using it.
   - Keep drafting, the review loop and rendering in the main thread. Don't hand those to agents.

2. **Slack** (load the tools with ToolSearch `+slack`). Read only; never post during gather. Work through three kinds of channel, then the message searches:
   1. **Account channel** (from the Account record): read `slack.account_channel_id` from `raw_org62.json` with `slack_read_channel`, paging back to the engagement start. It's usually named `ZC:<id>:<Account>`. This is the account team's view: exec meetings, what's being pitched next, consumption, recaps posted as threads (open the threads that touch the engagement). If the Account has no link, search channels for `ZC:` plus the account name.
   2. **Case channel** (created with the case): look up `slack.case_channel_name` with `slack_search_channels`, including archived channels. Also try the case number on its own, `<Account>-<case#>`, the `ZC:<id>:<Account>-<case#>` pattern and, for older work, `ZC:<id>:<Account>-Builder Request - DS-xxxxxxx` or `Builder-<Account>-1`. Read it in full when found; the intake post and escalation threads are there. If none exists, or it's private and the user isn't a member, say so in the digest and carry on. Don't guess its contents.
   3. **Other account channels:** `slack_search_channels` with the account name (all pages, archived included). Read the ones that were active during the engagement and relate to the work: the Slack Connect channel with the customer (`-ext`, `ext-`, `external-`), pilot, specialist, activation, consumption, security and open Sev1 channels. Skip event, marketing, sponsorship and SIC channels, and anything archived before the engagement started. Channels the user can't read are listed, not guessed at.

   Then the searches:
   - **The user's own posts:** `slack_search_public_and_private` with the account name and `from:me after:<engagement start>` (or the user's Slack Id). DMs and group DMs with the AE/SE hold the real decisions: pivots, "paths forward" messages, roll-off talk.
   - **Everyone else:** the same search without `from:` for the account team's view, such as the customer halting a program or support cases.
   - **Team channels**, for cross-account field learnings: the user's own team channels. Ask the user which ones to use.
   - Canvases linked in those threads, if they hold customer Q&A or observability notes.

   Anything from the account channel or other channels that isn't the engagement itself (pipeline, pitches, other teams' builds, Sev1s) goes in Internal notes or the timeline, not as our work. Parallel work by other teams on the same account goes in Internal notes so the readout doesn't contradict it.
3. **Local files:** check the user's local client folders for the account for existing retros, closure messaging and guides.
4. **Ask the user** for anything you can't find:
   - customer quotes (only ones the customer gave on the record; never lift a quote from a Slack message)
   - the 90-day check-in date

## 2. Draft the record

Write `engagement.json` following `references/sections.md`. Rules:

- **Slack is a source, never content.** Don't show Slack channel names, links or messages anywhere on the pages, and don't quote Slack. Leave out work other people did after the user rolled off.
- Every claim traces to a source: a case comment date, a Slack message, a case field. Don't invent IDs, URLs, dates or quotes, and never quote a Slack message in the output; it's a source for facts, not for quotes. Copy `case_url` from `raw_org62.json`.
- Write each item once, for an internal reader. Don't add `customer` overrides or `audience` tags; there is no customer version.
- **Case and DSR numbers appear only as links.** A bare number tells the reader nothing, so every case or DSR number in the record is a `[Case 12345678](https://org62.lightning.force.com/lightning/r/Case/<Id>/view)` link (DSRs: `.../r/Deal_Support_Request__c/<Id>/view`). Get the Ids from the `attributes.url` of each record in `raw_org62.json`, `raw_account_cases.json` and `raw_dsr.json`; pull any missing ones by CaseNumber or Name, read-only. If a number can't be linked to an Org62 record (for example a Salesforce Support case or Sev1 number from Slack), leave the number out and describe it in words ("a Sev1 with Support"). This covers `meta.dsrs`, timeline, challenges, built items and notes.
- `built[].status`: there are two live statuses, and plain `live` is rejected by the scripts. Use `live_sandbox` (Live in sandbox, teal) when it works in the customer's sandbox and `live_production` (Live in production, green) when it runs in their production org with real users. Either way it must be running software (an agent, flow, code, data stream or active prompt template). A change that was deployed but didn't fix the problem is not live. If the record doesn't say which org, ask the user; don't guess. Work that stopped is `cancelled` (over for good: turned down, pivoted away from, called off) or `paused` (on hold and could come back: waiting on an approval, a priority or a re-engagement). Plain `shelved` is rejected too. Say in the text why it was cancelled or what it is waiting on. Use `completed` (light blue) for finished work that isn't running software, like a signed scope, discovery sessions, security answers or a demo in our own org. See "Built status" in `references/sections.md`.
- `meta.updated` is the current month and year. It is the only date in the hero.
- `meta.products` and `meta.related_platform` fill the Snapshot's "Agentforce products" and "Related platform" rows: the in-scope products with a status each (green production, yellow sandbox, red cancelled, grey paused or planned; never completed, since products are software and either reached an org or stopped). Each tag is clickable and opens a pop-up above it saying how far that product got. Use the standard names in `references/sections.md` ("Agentforce products and related platform").

**Always draft an architecture diagram too.** Every engagement gets `<slug>/architecture.json`, drafted from what the gather found (the case, comments, Slack, the user's notes) and following the `architecture-diagram` skill (`~/.claude/skills/architecture-diagram/SKILL.md`: zones left to right, honest states, no invented systems or connections, plain wording). Start from the closest worked example in that skill's `references/`. What's running in production or sandbox is `current`; committed next steps are `planned`; things only discussed are `exploring`; positioned-then-stopped is `shelved`. Keep it in step with `built[]`: the same pieces, the same live or paused story. If you can't tell how two systems connect, leave the line out and ask in the review. When the work runs in Salesforce, draw the Salesforce band around those zones and the people who work there (`groups`, see "The Salesforce band" in that skill), with systems outside Salesforce left outside it. Only skip the diagram if the user says not to.

## 3. Review loop (the back-and-forth)

Before rendering, show the user a short digest:
- sources read: the account channel, the case channel (or that it wasn't found), the other channels read and skipped
- headline
- outcome
- built pieces with status (check every Live item against the Live rule above, and that each says sandbox or production, and every stopped item says cancelled or paused)
- top challenges
- next steps
- the risk read
- the architecture draft: the zones and nodes with their states, and any connection you inferred

Ask what's wrong or missing. Edit the JSON and repeat. Once they're happy, render, give them the file paths, and offer to open them (`open <file>`).

## 4. Render

```bash
PY=~/.claude/skills/engagement-exit-plus/.venv/bin/python; S=~/.claude/skills/engagement-exit-plus/scripts
$PY $S/case_status.py <dir>                      # always first: live Org62 Case status into meta.case_status
$PY $S/render.py <dir>/engagement.json          # internal retrospective (the only mode)
python3 ~/.claude/skills/architecture-diagram/scripts/render_arch.py <dir>/architecture.json   # before build_site, so the site gets /architecture
```

- **Architecture, every render:** render the diagram before building the site, screenshot it and fix crossed lines, hidden badges or wrapped titles (see the architecture-diagram skill's check list). Add it to the README "Architecture diagrams" list for new accounts.

- **Case status, every render:** `case_status.py` reads the Case's current Status from Org62 (read-only) and writes `meta.case_status`. It shows as a colored tag in the retrospective Snapshot ("Case status") and in the site header:
  - **Completed** (green): the case is closed.
  - **Active** (blue): the case is open, at any working status such as New, In Progress or Delivery.
  - **On hold** (yellow): the status is On Hold, Waiting on... or Pending....
  - **Cancelled** (red): the case was closed as cancelled, declined or rejected.

  The Org62 status text is shown next to the tag when it differs, for example "Active, Org62 status Delivery". Engagements without a case (no `case_number`, for example older DSR-only work) get no tag unless the user gives a status. Then set it by hand: `"case_status": {"status": "Completed", "closed": true, "source": "manual", "checked": "<Mon D, YYYY>"}`. It shows as "Engagement status", noted "set manually", and `case_status.py` leaves it alone. Never write to a DSR for this. The case status is separate from `outcome_status`: one tracks the Org62 record, the other tracks what the customer has running.
- If you have the `humanizer` skill installed (optional), run it over the copy. When you do, fix the AI patterns (fragments, run-ons, filler, stiff phrasing) but **keep the technical terms**. They tell the real story: planner names (Daisy vs. Daisy++), deterministic vs. non-deterministic or probabilistic, product and feature names (Agentforce skills, AEA, CLT, DLO, GA path), object and table names. Never swap them for vaguer plain-English words in the internal retrospective or site.
- Visual check with headless Chrome:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --screenshot=/tmp/x.png --window-size=1280,2400 file://<html>
  ```
  Read the PNG.
- **Publish every time.** Add the README row (new engagements), then commit and push to the readouts repo. This is the last step of every render, including re-renders after edits, so GitHub always matches what the user reviewed:
  ```bash
  cd $READOUTS
  gh repo view --json visibility -q .visibility   # must print PRIVATE; stop if not
  git add README.md <slug>/ && git status --short    # raw_*.json must not appear (gitignored)
  git commit -m "<Account>: <what changed>" && git push origin main
  ```
  **Build the internal site before committing, every time:** `$PY $S/build_site.py <dir>`, then `npm install && npm run build` in `<dir>/site/` (npm needs to run outside the sandbox). Every site is React: `build_site.py` copies the shared Next.js app from `site-react/` into `<dir>/site/` and writes the internal-scoped record to `src/data/site.json`. It's a static export to `out/` (home, `/retrospective`, `/architecture`). There is no plain-HTML site mode. To change how a site looks or works, edit `site-react/` once and rebuild the accounts. The architecture page appears when `<slug>-architecture.html` exists, so accounts without a diagram get a two-page site. It uses an allowlist, so engagement.json and raw files are never copied. The internal retrospective and architecture stay where they are too, so links already in the README keep working.
  Name any extra Org62 or Slack pulls `raw_*.json` so they stay out of git. Report the commit to the user.

## 5. Where it lives

- The user's private readouts repo (`$READOUTS`) is the home for every readout. Every render ends with a commit and push (see step 4), so nothing sits only on local disk.
- Don't deploy anywhere else unless the user asks for it.
- **Never enable GitHub Pages on that repo.** A Pages site built from a private repo on this personal account can still be opened by anyone with the URL.
- **Site design** (`site-react/src/app/globals.css`): light and quiet, not a generic AI look.
  - One sans font (Manrope), no mono. Palette is Salesforce blue: accent `#0176d3` (SLDS brand), deep blue `#014486` for hover and links, navy `#032d60` for dark bands, on a pale blue-grey page (`#f4f7fb`). Teal appears only on the "Live in sandbox" status so it reads differently from blue "Completed". Content sits in white rounded cards (20 to 28px radius) with a soft shadow.
  - The hero is light with faint diagonal blue shapes. Headlines are big, weight 600 and tightly tracked. Titles over 44 characters get the smaller `h1.long` size.
  - Home page, top to bottom: hero (kicker, title, outcome summary, buttons, team initials, "Updated Month Year") with a case card and an overlapping duration card on the right. Then the Highlights card overlapping the hero bottom, with When / What kind / Who. Then "What we built" as a bento (live count, status bar and legend, list of pieces), a navy "Roadblock items" band with up to three challenge cards, two document cards (white retrospective, blue architecture), a navy "Account next steps" panel and a column footer.
  - **Site section headings** (sidebar and page): Highlights, Snapshot, Builder Engagement reason, What we built (with Timeline), Roadblock items, Field learnings from the team (its lessons list is "Lessons for other engagements"), Account next steps, Internal notes. The home page uses Roadblock items and Account next steps too. The sidebar builds itself from the page's h2s, so renaming a heading renames its sidebar entry.
  - **Sidebar toggle:** one navy pill at the bottom left. It reads "Contents" when the panel is closed and "Hide" when it's open, in the same spot, so you never have to reach for the top of the panel.
  - Pills are sans with a leading dot on a soft tinted background, no border, always `white-space:nowrap`. Section kickers are words (Delivery, Lessons, Documents, Next), never numbers.
  - The architecture page nests the renderer's CSS under `.arch-page` (so it can't restyle the site bar or sidebar) and remaps its palette (blue and navy) and hero to the site's look.
  - When you change the design, rebuild one account first and screenshot `/`, `/retrospective` and `/architecture` at 1400px and 800px, and check an account with a long title.
- **Highlights card:** `meta.headline` as one short paragraph under a small "HIGHLIGHTS" kicker, on **both** internal pages, the first thing under the hero. On the retrospective the hero holds only the title, and the card sits above the print button so it's visible without scrolling. There is no row of section links on the page; the sidebar is the index. Don't turn the headline into a bullet or pill list. **Keep it short: three to five short sentences, at most 22 words each and 360 characters in all.** Say what the problem was, what we built and where it landed. Leave the how (flows, Apex, field counts, accuracy, politics) to What we built, Roadblock items and Internal notes, which already cover it. `render.py` stops when the headline breaks any of those limits.
- **Logos in the site bar:** `build_site.py` puts the Salesforce cloud and the customer's logo side by side at the top left of the white site bar, when `<slug>/brand/` has one customer logo (`<slug>.svg` preferred, `.png` if that's all the customer publishes). The Salesforce logo ships with the skill (`assets/salesforce.svg`) and `build_site.py` copies it into `brand/` for you, so the only thing to fetch per account is the customer's logo. Two separate logos, never a combined lockup. Source the customer logo from Wikimedia Commons (`Special:FilePath/<file>.svg`) or the customer's own site header. Clean it before saving: drop the XML prolog, metadata and editor attributes, and check there are no scripts, event handlers, embedded images or outside links (the build stops if there are). Trim the viewBox if the mark has a lot of empty space around it. Screenshot the bar to check that the logos balance. **Logos are required on every new account:** set up `brand/` before the first site build. `build_site.py` stops with `no customer logo` when `brand/` isn't set up; fetch the logo then, and only pass `--no-logo` if the user agrees to skip it. If the customer's site blocks `curl` (Akamai "Access Denied"), load it with headless Chrome `--dump-dom` and a desktop user agent to find the header logo's URL. Then capture it with a small local HTML page that shows the image, using `--force-device-scale-factor=3 --default-background-color=00000000 --screenshot`, and trim it with PIL `getbbox()` into `<slug>.png`.
- **React for everything:** every internal site is the Next.js 16 / React 19 / TypeScript app in `site-react/`, and any new app built for this work should be React too. The sidebar is on by default (turn it off with `<slug>/site.json` `{"sidebar": false}`). Pages read only `src/data/site.json`; links in the record (`[label](https://...)`) render through the `Rich` component. The architecture page still embeds the Python-rendered SVG. `server.js` is a zero-dependency static server over `out/`, and Heroku builds the site through `heroku-postbuild`.
- **Local preview:** run `python3 -m http.server 8765 --bind 127.0.0.1` from the repo root. For one account's site, run `npm run build` and then `PORT=<port> node server.js` in `<slug>/site/`.
- **Heroku (only when asked):** each `<slug>/site/` is a standalone Node app for Heroku internal routing in a private space (use your team's private space and put its name into the checks below as `<space>`). Never deploy without explicit confirmation, and a yes for one deploy doesn't cover the next one.
  1. **Login:** `heroku login` can't run from Claude's shell, or from a `!` command. Ask the user to run it in their own terminal, then check with `heroku auth:whoami`. The Heroku CLI may need to run outside the sandbox to read the saved login.
  2. **Check before pushing:** `heroku apps:info -a <app>` must show `Space: <space>` and `Internal Routing: true`. The site holds the internal retrospective, so stop if either is missing.
  3. **Deploy from the repo root:** `git remote add heroku-<slug> https://git.heroku.com/<app>.git` (once), then `git subtree push --prefix <slug>/site heroku-<slug> main`. Push to GitHub first so Heroku never runs something GitHub doesn't have.
  4. **Check:** wait until the new dyno shows `up` in `heroku ps -a <app>`. Then test the **internal** URL. `heroku apps:info` prints `https://<app>-<hash>.<region>.herokuapp.com/`, but internal-routing apps answer only at `https://<app>-<hash>.<region>.herokuapp-internal.com/`: swap `herokuapp.com` for `herokuapp-internal.com`. The `.herokuapp.com` form gives "connection reset". From Claude's shell, `curl` on the internal URL should return `302` to `auth.herokuapp-internal.com` (the SSO sign-in) for `/`, `/retrospective` and `/architecture`. Ask the user to open it in a browser and sign in.
  5. **Record it:** put the `herokuapp-internal.com` link (never the `.herokuapp.com` one) in the README "Internal account sites" Heroku column, then commit and push.
- **A deployed site goes stale:** re-rendering doesn't update Heroku. After any re-render of an account that has a Heroku app (check the README column), tell the user the Heroku copy is now behind and ask whether to redeploy.
