---
name: deploy-experience-cloud
description: Package a static playbook/site (Next.js export or any static HTML/CSS/JS bundle) as a Salesforce Static Resource, wrap it in an iframe LWC, deploy both to a target org, and optionally spin up a new "Build Your Own (LWR)" Experience Cloud site to host it. Use when the user wants to publish a static asset (playbook, deck-as-site, demo app) into Experience Cloud.
user-invocable: true
allowed-tools: Bash Read Write Edit
argument-hint: <source-path> --org <target-org> [--resource-name <Name>] [--component-name <name>] [--site-name "<Site Name>"] [--url-prefix <prefix>] [--password <value>]
---

# Deploy a Static Playbook to Experience Cloud

Takes a static site (a built Next.js export, or any plain folder with an `index.html`) and makes it live inside
Salesforce Experience Cloud as a self-hosted Static Resource, embedded via a thin iframe LWC.

**Scope note:** This skill stops once the resource + component are deployed (and the site is created, if
requested). It deliberately does NOT touch page layout, guest/public access settings, or site activation —
those are manual steps the user handles themselves in Experience Builder / Digital Experiences Setup. See
"Handoff" at the end.

## Usage

```
/deploy-experience-cloud <source-path> --org <target-org> [--resource-name <Name>] [--component-name <name>] [--site-name "<Site Name>"] [--url-prefix <prefix>] [--password <value>]
```

**Parameters:**
- `source-path`: Path to the playbook/site. Either a Next.js project root, or a folder that already contains a built static site (has `index.html` at its top level).
- `--org`: Target org username/alias. Required — always ask if not given, never assume/reuse a default org for this.
- `--resource-name`: Static Resource API name (PascalCase/camelCase, no spaces). Defaults to a sanitized version of the source folder name.
- `--component-name`: LWC name (camelCase). Defaults to `<resourceName>Embed`.
- `--site-name`: If provided, create a new "Build Your Own (LWR)" Experience Cloud site with this name. If omitted, skip site creation — assume the user already has a site to place the component on themselves.
- `--url-prefix`: URL path prefix for a new site (only used with `--site-name`). Defaults to a slug of the site name.
- `--password`: If provided, gate the embed behind a simple password form (plain string compare, unlock persisted per browser session via `sessionStorage`). Omit for no gate. This is a casual deterrent only — see "Password gate" below — so if not given, ask the user whether they want one rather than defaulting either way.

Confirm the target org and (if a site will be created) the site name with the user before doing anything — these are the two inputs the user explicitly said they'd provide, don't guess them.

## Instructions

### 1. Prepare the static content

Detect what `source-path` is:

- **Next.js project** (has `next.config.ts`/`next.config.js`): this needs a build.
  1. Read the config. Ensure it has:
     ```ts
     output: "export",
     trailingSlash: true,
     assetPrefix: ".",
     ```
     `assetPrefix: "."` is not optional — Next's static export otherwise emits root-absolute asset paths
     (`/_next/...`). Once served from a versioned Static Resource subpath, those 404. This was the root cause
     of a real broken deploy — always check/fix this before building.
  2. If any page files use `export const dynamic = "force-static"` requirements (Next.js 15+ App Router with
     static export), verify it's present; add if missing.
  3. `npm run build` → produces `out/`.
  4. **Fail-fast local check** before touching Salesforce: copy `out/*` into an arbitrary nested subdirectory
     (e.g. `/tmp/check/nested/out`), serve with `python3 -m http.server` from a couple levels up, load
     `.../nested/out/index.html`, and grep the served HTML/JS for any stray absolute `/_next` or `href="/`
     references. Fix before proceeding — this catches the exact class of bug that broke a prior deploy.
- **Already-built static folder**: use as-is, but still run the same absolute-path grep check as a sanity pass.

### 2. Package as a Static Resource

In the target sfdx project (current directory, unless told otherwise):

```
force-app/main/default/staticresources/<resourceName>/          # copy of the built static content
force-app/main/default/staticresources/<resourceName>.resource-meta.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StaticResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <cacheControl>Public</cacheControl>
    <contentType>application/zip</contentType>
</StaticResource>
```

### 3. Generate the LWC wrapper

Read `sourceApiVersion` from the project's `sfdx-project.json` and use it in the meta XML.

**No `--password` given** — `force-app/main/default/lwc/<componentName>/<componentName>.js`:
```js
import { LightningElement } from 'lwc';
import RESOURCE from '@salesforce/resourceUrl/<resourceName>';

export default class <ComponentClassName> extends LightningElement {
    playbookUrl = `${RESOURCE}/index.html`;
}
```

`<componentName>.html`:
```html
<template>
    <iframe
        src={playbookUrl}
        title="<Human readable title>"
        style="width:100%;height:100vh;border:0;display:block;"
        allowfullscreen
    ></iframe>
</template>
```

**`--password <value>` given** — same iframe, but gated behind a plain password form until it matches, with
the unlock remembered for the browser session. `<componentName>.js`:
```js
import { LightningElement } from 'lwc';
import RESOURCE from '@salesforce/resourceUrl/<resourceName>';

const SITE_PASSWORD = '<value>';
const STORAGE_KEY = '<componentName>_unlocked';

export default class <ComponentClassName> extends LightningElement {
    playbookUrl = `${RESOURCE}/index.html`;
    passwordInput = '';
    error = false;
    unlocked = false;

    connectedCallback() {
        this.unlocked = sessionStorage.getItem(STORAGE_KEY) === 'true';
    }

    handleInputChange(event) {
        this.passwordInput = event.target.value;
        this.error = false;
    }

    handleKeyUp(event) {
        if (event.key === 'Enter') {
            this.handleSubmit();
        }
    }

    handleSubmit() {
        if (this.passwordInput === SITE_PASSWORD) {
            this.unlocked = true;
            sessionStorage.setItem(STORAGE_KEY, 'true');
        } else {
            this.error = true;
        }
    }
}
```

`<componentName>.html`:
```html
<template>
    <template if:true={unlocked}>
        <iframe
            src={playbookUrl}
            title="<Human readable title>"
            style="width:100%;height:100vh;border:0;display:block;"
            allowfullscreen
        ></iframe>
    </template>
    <template if:false={unlocked}>
        <div class="gate">
            <div class="gate-card">
                <h2 class="gate-title">This content is password protected</h2>
                <p class="gate-subtitle">Enter the password to continue.</p>
                <input type="password" class="gate-input" placeholder="Password" value={passwordInput}
                       onchange={handleInputChange} onkeyup={handleKeyUp} />
                <button class="gate-button" onclick={handleSubmit}>Unlock</button>
                <template if:true={error}>
                    <p class="gate-error">Incorrect password. Try again.</p>
                </template>
            </div>
        </div>
    </template>
</template>
```

Plus a `<componentName>.css` with a centered `min-height: 100vh` flex layout and a simple card — see
`force-app/main/default/lwc/playbookEmbed/playbookEmbed.css` in this project for a working reference.

`<componentName>.js-meta.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion><sourceApiVersion from sfdx-project.json></apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
</LightningComponentBundle>
```

Use `@salesforce/resourceUrl` (not a hardcoded path) — it resolves the *current* resource version at runtime,
so future redeploys of the resource don't break the embed.

### 4. Deploy resource + component together

```bash
sf project deploy start \
  --source-dir "force-app/main/default/staticresources/<resourceName>.resource-meta.xml" \
  --source-dir "force-app/main/default/staticresources/<resourceName>" \
  --source-dir "force-app/main/default/lwc/<componentName>" \
  --target-org <target-org>
```

If the payload is large (many static assets), this can exceed a short foreground timeout — run in the
background and poll rather than assuming failure on timeout.

### 5. Create the Experience Cloud site (only if `--site-name` given)

First check for an existing site with the same/similar name so you don't create a duplicate:
```bash
sf data query --query "SELECT Id, Name, Status, UrlPathPrefix FROM Network ORDER BY CreatedDate DESC" --target-org <target-org>
```
Confirm with the user before proceeding if anything looks like a near-duplicate.

```bash
sf community create \
  --name "<Site Name>" \
  --template-name "Build Your Own (LWR)" \
  --url-path-prefix <url-prefix> \
  --target-org <target-org>
```
This is async — poll the returned job until it completes, then confirm the new `Network` row exists via the
SOQL query above.

### 6. Report back

Give the user:
- The deployed component name (`<componentName>`) — this is what they'll drag onto a page in Experience Builder.
- The Static Resource name (`<resourceName>`).
- If a site was created: its Network Id and the Experience Builder URL pattern
  (`https://<domain>/sfsites/picasso/core/config/commeditor.jsp?siteId=<siteId>`), which they can get from
  `sf community list` or `Network.Id`.

## Handoff — deliberately NOT automated here

Tell the user these are theirs to do, and don't attempt them even if asked to "finish the job":

1. **Placing the component on a page.** Experience Builder's drag-and-drop has no automatable equivalent
   (confirmed: no drag/mouse primitive exists in available browser tooling, and the canvas itself renders in
   a nested iframe invisible to accessibility-tree inspection, so even precise click-targeting doesn't work).
2. **Guest/public access.** There are at least two separate toggles, and only one is reliably scriptable:
   - Network-level: `enableGuestChatter` in `Network` metadata (`allowChatterAccessWithoutLogin` in the Connect
     API) affects whether unauthenticated requests get past an initial blanket redirect at all.
   - Page-level: each page in Experience Builder likely has its own "Public"/audience setting independent of
     the network-level toggle — this is where guest access most likely still needs to be turned on even after
     the network-level toggle is set. It lives in the page's own settings in Experience Builder; it was not
     reliably reachable via Metadata API in testing (see Common Issues).
3. **Activating the site.** Editing `Network.status` from `UnderConstruction` to `Live` directly via a metadata
   deploy of the `Network` file *does* work and triggers a real activation (confirmed via `FirstActivationDate`
   getting populated server-side) — this is a legitimate faster alternative to the UI "Activate" button, but
   still leave it to the user unless they explicitly ask for it.
4. **Publishing after a component update.** `sf project deploy start` updates the component's source/definition
   in the org immediately, but on an already-live site the *previously published* LWR bundle can keep serving
   for a while after that (see "Live site briefly shows the old version" below). Deploying is this skill's job;
   clicking **Publish** in Experience Builder so the live site definitely picks up the change is the user's.

Give them these verification commands so they can self-check once they've done the above:
```bash
curl -sI "https://<domain>/<url-prefix>/"                                    # expect 200, not a 302 to /login
curl -sI "https://<domain>/<url-prefix>/sfsites/c/resource/<version>/<resourceName>/index.html"  # expect 200, not 403
```

## Common Issues

### Deployed component shows a broken-image icon inside Experience Builder's edit canvas
Likely a framing artifact of Builder's own nested iframe preview (three levels deep), not a real failure.
Confirm by checking the actually-published, top-level site URL directly rather than trusting the Builder canvas.

### `ExperienceBundle` retrieve fails with "Entity ... cannot be found" for a real, listed bundle
Seen even for bundles that `sf org list metadata --metadata-type ExperienceBundle` confirms exist, and even
after publishing. Wildcard retrieval (`ExperienceBundle:*`) sometimes works but can abort partway through on
an unrelated site's `ConcurrentEditDetectedException` (a transient org-side SQL lock, not a permissions
issue) before reaching the bundle you actually want. Don't block on this — use Experience Builder directly, or
the Connect API (`/services/data/vXX.0/connect/communities/<networkId>`), instead of relying on retrieving the
raw metadata.

### Guest users still redirected to `/login` after enabling network-level guest settings
Check the page-level audience/public setting separately — network-level and page-level guest access appear to
be independent gates. A useful diagnostic: an unauthenticated `curl -I` that returns an immediate flat 302 means
the network-level gate is closed; a 302 that only happens *after* real page-resource `Link:` preload headers
show up (webruntime framework/view assets) means the network-level gate is open but the page-level one isn't.

### Static Resource assets 404 once deployed
Almost always a root-absolute path issue — re-check `assetPrefix` (step 1) and rebuild.

### Password gate
This is a client-side deterrent only, not real access control. Digital Experiences has no built-in shared-
password feature for guest sites, so the gate lives entirely in the LWC's JS — which means the literal
password string ships in the deployed component and is visible to anyone who inspects the bundle or uses
view-source/devtools. Fine for keeping a demo/playbook off casual passersby; never rely on it for anything
that needs actual access control (use a real authenticated site + profile/permission set for that instead).

To change the password later: edit the `SITE_PASSWORD` constant in `<componentName>.js` and redeploy just
that component (`sf project deploy start --source-dir "force-app/main/default/lwc/<componentName>" --target-org
<target-org>`). No resource/site redeploy needed. Remind the user they'll likely need to re-Publish the site
in Experience Builder for the live URL to reflect it — see "Live site briefly shows the old version" below.

### Live site briefly shows the old version (or no gate at all) right after a deploy
Networks with `enableApexCDNCaching` enabled (common default) can keep serving the previously published LWR
bundle for a bit after `sf project deploy start` succeeds — the deploy updates the org's component
definition immediately, but the live, publicly-cached page can lag behind until the user hits **Publish**
in Experience Builder and/or the CDN cache clears. This is not a deploy failure or a bug in the component.
Don't assume the gate logic is broken from a stale live-site screenshot alone — verify by loading the URL in
a browser session that hasn't hit that page before (or hard-refresh / cache-bust with `?v=<n>`) before
digging into the component code.

## Pre-approved Permissions

The following are pre-approved and don't require confirmation:
- `sf project deploy start` for the static resource + LWC being built by this skill
- `sf org list metadata --metadata-type ExperienceBundle`, `sf data query` (read-only)
- `npm run build` in the source project
- Reading/writing the static resource, LWC, and manifest files this skill creates

Always confirm before: creating a new Experience Cloud site (`sf community create`), and before any change to
an *existing* site's `Network` metadata (status, guest settings) — those are the user's to drive per this
skill's scope.
