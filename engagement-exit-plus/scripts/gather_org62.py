#!/usr/bin/env python3
"""Read-only Org62 gather for a Builder Engagement case, or a DSR when there is no case.

Usage:
  gather_org62.py <CaseNumber> <out_dir>   writes <out_dir>/raw_org62.json from the case
  gather_org62.py DS-1234567 <out_dir>     no case: writes the same file from the DSR
  gather_org62.py --mine                   lists Builder cases you own or are allocated to,
                                           plus your DSRs from the last 400 days

Read only: nothing here creates or updates anything in Org62.

Works for whoever runs it. The Org62 login comes from $ORG62_ALIAS (an sf alias or
username) or, if that's unset, the first authenticated sf org on org62.my.salesforce.com.
The running user's Id is looked up from that login, so nothing here is tied to one person.
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request

URL = "https://org62.my.salesforce.com"
API = "/services/data/v66.0"
_ORG = None

CASE_FIELDS = [
    "Id", "CaseNumber", "Subject", "Description", "Status", "Reason", "Origin",
    "Engagement_Type__c", "Business_Challenge_and_Desired_Outcomes__c", "CROverall_Notes__c",
    "Business_Issues__c", "Slack_Channel_Name__c", "Requested_Delivery_Date__c",
    "Committed_Completion_Date__c", "Duration_of_Engagement__c", "Opportunity_Close_Date__c",
    "AOV_Band__c", "CFL_Portfolio__c", "CreatedDate", "ClosedDate", "Related_Opportunity__c",
    "OwnerId", "Owner.Name", "CreatedBy.Name", "Account.Id", "Account.Name",
    "Contact.Name", "Contact.Title", "Contact.Email",
    "Account.Website", "Account.Slack_Channel_Link__c",
]


def org():
    """The sf alias or username for Org62: $ORG62_ALIAS, else the first org62 login sf knows."""
    global _ORG
    if _ORG:
        return _ORG
    _ORG = os.environ.get("ORG62_ALIAS")
    if not _ORG:
        out = subprocess.run(["sf", "org", "list", "--json"], capture_output=True, text=True).stdout
        res = (json.loads(out or "{}").get("result") or {})
        orgs = [o for k in ("nonScratchOrgs", "other", "sandboxes") for o in res.get(k, [])]
        hit = [o for o in orgs if "org62.my.salesforce.com" in (o.get("instanceUrl") or "")]
        if not hit:
            sys.exit("No Org62 login found. Run: sf org login web --instance-url https://org62.my.salesforce.com "
                     "--alias org62   (or set ORG62_ALIAS)")
        _ORG = hit[0].get("alias") or hit[0]["username"]
    return _ORG


def _display():
    out = subprocess.run(["sf", "org", "display", "--target-org", org(), "--json"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["result"]


def token():
    return _display()["accessToken"]


def me(tok):
    """The running user's Org62 Id, Name and Email, from the sf login."""
    user = _display()["username"]
    r = soql(tok, f"SELECT Id,Name,Email FROM User WHERE Username='{user}'")
    return strip(r[0])


def slack_channel_id(link):
    """Pull the channel Id out of a Slack link (app_redirect?channel=C... or /archives/C...)."""
    m = re.search(r"(?:channel=|/archives/)([CG][A-Z0-9]{6,})", link or "")
    return m.group(1) if m else None


def email_domain(*vals):
    for v in vals:
        v = (v or "").strip().lower()
        if "@" in v:
            return v.split("@", 1)[1]
        if v:
            return re.sub(r"^(https?://)?(www\.)?", "", v).split("/")[0] or None
    return None


def get(tok, path):
    req = urllib.request.Request(URL + path, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def soql(tok, q):
    return get(tok, f"{API}/query/?q=" + urllib.parse.quote(q))["records"]


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k != "attributes"}
    if isinstance(o, list):
        return [strip(x) for x in o]
    return o


def mine():
    tok = token()
    u = me(tok)
    sel = "CaseNumber,Subject,Status,Account.Name,CreatedDate"
    owned = soql(tok, f"SELECT {sel} FROM Case WHERE OwnerId='{u['Id']}' AND RecordType.Name LIKE '%Builder%' "
                      "ORDER BY CreatedDate DESC")
    alloc = soql(tok, "SELECT Case__r.CaseNumber,Case__r.Subject,Case__r.Status,Case__r.Account.Name,Role__c "
                      f"FROM Case_Resource_Allocation__c WHERE User__c='{u['Id']}' ORDER BY Case__r.CreatedDate DESC")
    seen = {}
    for c in owned:
        seen[c["CaseNumber"]] = (c["Subject"], c["Status"], (c.get("Account") or {}).get("Name"), "owner")
    for a in alloc:
        c = a.get("Case__r") or {}
        if c.get("CaseNumber") and c["CaseNumber"] not in seen:
            seen[c["CaseNumber"]] = (c.get("Subject"), c.get("Status"), (c.get("Account") or {}).get("Name"),
                                     a.get("Role__c") or "allocated")
    dsrs = soql(tok, "SELECT Name,Status__c,Account__r.Name,Use_Case_Focus__c,CreatedDate FROM Deal_Support_Request__c "
                     f"WHERE OwnerId='{u['Id']}' AND CreatedDate=LAST_N_DAYS:400 ORDER BY CreatedDate DESC")
    print(f"Cases for {u['Name']}:")
    for n, (subj, st, acct, how) in seen.items():
        print(f"  {n}  {st:<12} {acct or '-':<28} {how:<12} {subj}")
    print(f"\nDSRs for {u['Name']} (use when an engagement has no case):")
    for d in dsrs:
        print(f"  {d['Name']}  {d.get('Status__c') or '-':<12} {(d.get('Account__r') or {}).get('Name') or '-':<28} "
              f"{d.get('Use_Case_Focus__c') or ''}")


def contacts(tok, acct):
    """Account contacts, newest first, so the draft can use real names and titles."""
    if not acct:
        return []
    return strip(soql(tok, "SELECT Name,Title,Email,LastModifiedDate FROM Contact "
                           f"WHERE AccountId='{acct}' ORDER BY LastModifiedDate DESC LIMIT 200"))


def gather_dsr(name, out_dir):
    """No Builder case: build raw_org62.json from a DSR instead. Same keys, so drafting works the same."""
    tok = token()
    user = me(tok)
    r = soql(tok, "SELECT Id,Name,Status__c,Request_Type__c,Request_Type_Detail__c,Use_Case_Focus__c,"
                  "Reason_for_SE_Involvement__c,Status_Comments__c,CreatedDate,LastModifiedDate,Completed_Date__c,"
                  "Owner.Name,Opportunity__c,Account__c,Account__r.Name,Account__r.Website,"
                  f"Account__r.Slack_Channel_Link__c FROM Deal_Support_Request__c WHERE Name='{name}'")
    if not r:
        sys.exit(f"DSR {name} not found")
    dsr = strip(r[0])
    did, acct = dsr["Id"], dsr.get("Account__c")
    account = dsr.get("Account__r") or {}
    # Status_Comments__c overwrites itself; history keeps the dates it changed (textarea values aren't tracked).
    hist = soql(tok, "SELECT CreatedDate,CreatedBy.Name,Field,OldValue,NewValue FROM Deal_Support_Request__History "
                     f"WHERE ParentId='{did}' ORDER BY CreatedDate")
    opp = None
    if dsr.get("Opportunity__c"):
        o = soql(tok, "SELECT Id,Name,StageName,Amount,CloseDate,Owner.Name,Type FROM Opportunity "
                      f"WHERE Id='{dsr['Opportunity__c']}'")
        opp = strip(o[0]) if o else None
    dsrs = soql(tok, "SELECT Id,Name,Status__c,Request_Type__c,Status_Comments__c,CreatedDate,LastModifiedDate,Owner.Name "
                     f"FROM Deal_Support_Request__c WHERE Account__c='{acct}' AND CreatedDate=LAST_N_DAYS:400 "
                     "ORDER BY CreatedDate DESC") if acct else []
    events = soql(tok, "SELECT Subject,StartDateTime,DurationInMinutes,SE_Task_Type__c FROM Event "
                       f"WHERE WhatId='{acct}' AND OwnerId='{user['Id']}' AND StartDateTime=LAST_N_DAYS:365 "
                       "ORDER BY StartDateTime") if acct else []
    raw = {
        "gathered_by": user,
        "source": "dsr",
        "slack": {
            "account_channel_id": slack_channel_id(account.get("Slack_Channel_Link__c")),
            "account_channel_link": account.get("Slack_Channel_Link__c"),
            "case_channel_name": None,
        },
        "email": {"customer_domain": email_domain(account.get("Website")), "contacts": []},
        "dsr": dsr,
        "dsr_url": f"https://org62.lightning.force.com/lightning/r/Deal_Support_Request__c/{did}/view",
        "dsr_history": strip(hist),
        "opportunity": opp,
        "dsrs": strip(dsrs),
        "events": strip(events),
        "contacts": contacts(tok, acct),
    }
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "raw_org62.json")
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"wrote {path} from {name} (no case): {len(hist)} history rows, {len(dsrs)} account DSRs, "
          f"{len(events)} events, {len(raw['contacts'])} contacts, opp={'yes' if opp else 'no'}, "
          f"account_channel={raw['slack']['account_channel_id']}")


def main():
    if sys.argv[1:2] == ["--mine"]:
        return mine()
    num, out_dir = sys.argv[1], sys.argv[2]
    if num.upper().startswith("DS-"):
        return gather_dsr(num.upper(), out_dir)
    os.makedirs(out_dir, exist_ok=True)
    tok = token()
    user = me(tok)
    cases = soql(tok, f"SELECT {','.join(CASE_FIELDS)} FROM Case WHERE CaseNumber='{num}'")
    if not cases:
        sys.exit(f"Case {num} not found")
    case = strip(cases[0])
    cid, acct = case["Id"], (case.get("Account") or {}).get("Id")

    comments = soql(tok, "SELECT CreatedDate,CreatedBy.Name,IsPublished,CommentBody FROM CaseComment "
                         f"WHERE ParentId='{cid}' ORDER BY CreatedDate")
    allocs = soql(tok, "SELECT User__r.Name,User__r.Title,Role__c,Allocation__c,Status__c,Start_Date__c,"
                       "End_Date__c,Planned_Hours__c,Actual_Hours__c,Notes__c FROM Case_Resource_Allocation__c "
                       f"WHERE Case__c='{cid}'")
    opp = None
    if case.get("Related_Opportunity__c"):
        r = soql(tok, "SELECT Id,Name,StageName,Amount,CloseDate,Owner.Name,Type FROM Opportunity "
                      f"WHERE Id='{case['Related_Opportunity__c']}'")
        opp = strip(r[0]) if r else None
    dsrs = []
    if acct:
        dsrs = soql(tok, "SELECT Name,Status__c,Request_Type__c,Status_Comments__c,CreatedDate,"
                         "LastModifiedDate,Owner.Name FROM Deal_Support_Request__c "
                         f"WHERE Account__c='{acct}' AND CreatedDate=LAST_N_DAYS:400 ORDER BY CreatedDate DESC")
    events = []
    if acct:
        events = soql(tok, "SELECT Subject,StartDateTime,DurationInMinutes,SE_Task_Type__c FROM Event "
                           f"WHERE WhatId='{acct}' AND OwnerId='{user['Id']}' "
                           "AND StartDateTime=LAST_N_DAYS:365 ORDER BY StartDateTime")

    account = case.get("Account") or {}
    raw = {
        "gathered_by": user,
        "slack": {
            "account_channel_id": slack_channel_id(account.get("Slack_Channel_Link__c")),
            "account_channel_link": account.get("Slack_Channel_Link__c"),
            "case_channel_name": case.get("Slack_Channel_Name__c"),
        },
        "email": {
            "customer_domain": email_domain((case.get("Contact") or {}).get("Email"), account.get("Website")),
            "contacts": [x for x in [(case.get("Contact") or {}).get("Email")] if x],
        },
        "case": case,
        "case_url": f"https://org62.lightning.force.com/lightning/r/Case/{cid}/view",
        "comments": strip(comments),
        "allocations": strip(allocs),
        "opportunity": opp,
        "dsrs": strip(dsrs),
        "events": strip(events),
        "contacts": contacts(tok, acct),
    }
    path = os.path.join(out_dir, "raw_org62.json")
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"wrote {path}: {len(comments)} comments, {len(allocs)} allocations, "
          f"{len(dsrs)} DSRs, {len(events)} events, opp={'yes' if opp else 'no'}, "
          f"case_channel={raw['slack']['case_channel_name']}, "
          f"account_channel={raw['slack']['account_channel_id']}, domain={raw['email']['customer_domain']}")


if __name__ == "__main__":
    main()
