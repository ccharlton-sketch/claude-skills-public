import Link from "next/link";
import { m, site, STATUS, type Item } from "@/lib/site";
import { Pill } from "@/components/pill";
import { Rich } from "@/components/rich";
import { ArrowUpRight, Briefcase, Calendar, FileText, Flag, Layers, Network, Users } from "@/components/icons";

// Order for the status bar: running first, stopped last.
const ORDER = ["live_production", "live_sandbox", "in_build", "at_risk", "planned", "completed", "paused", "cancelled"];
const LIVE = new Set(["live_production", "live_sandbox"]);

const initials = (n: string) => n.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

function splitDuration(s?: string): [string, string] {
  const t = (s ?? "").replace(/^about\s+/i, "").split(",")[0].trim();
  const x = t.match(/^(\d+)\s*(.*)$/);
  return x ? [x[1], x[2]] : [t, ""];
}

export default function Home() {
  const e = site.eng;
  const d = m.dates ?? {};
  const cb = m.case_badge;
  const built: Item[] = e.built ?? [];
  const team: Item[] = m.team ?? [];
  const challenges: Item[] = e.challenges ?? [];
  const steps: Item[] = e.next_steps ?? [];
  const live = built.filter((b) => LIVE.has(b.status));
  const counts = ORDER.map((s) => [s, built.filter((b) => b.status === s).length] as const).filter(([, n]) => n > 0);
  const [durN, durU] = splitDuration(d.duration);
  const record = m.record_label || (m.case_number ? `Case ${m.case_number}` : "Engagement");

  return (
    <main className="home-page">
      <section className="hero">
        <div className="shapes" aria-hidden="true"><i /><i /><i /></div>
        <div className="wrap hero-grid">
          <div className="hero-copy">
            <p className="kicker">{m.account} · {m.program || "Builder engagement"}</p>
            <h1 className={(m.title ?? "").length > 44 ? "long" : undefined}>{m.title}</h1>
            {m.outcome_summary && <p className="lede"><Rich text={m.outcome_summary} /></p>}
            <div className="actions">
              <Link className="btn primary" href="/retrospective">Read the retrospective <ArrowUpRight /></Link>
              {site.arch && <Link className="btn ghost" href="/architecture">See the architecture</Link>}
            </div>
            {team.length > 0 && (
              <div className="team" aria-label="Team">
                <ul>{team.slice(0, 5).map((t) => <li key={t.name} title={`${t.name}, ${t.role}`}>{initials(t.name)}</li>)}</ul>
                <span>{team.slice(0, 3).map((t) => t.name.split(" ")[0]).join(", ")}{team.length > 3 && ` and ${team.length - 3} more`}</span>
              </div>
            )}
            <p className="updated">Updated {m.updated}</p>
          </div>

          <div className="hero-art">
            <div className="case-card">
              <div className="cc-head">
                <span className="cc-icon"><Briefcase /></span>
                <div><b>{m.case_url ? <a href={m.case_url}>{record}</a> : record}</b><span>{m.account}</span></div>
              </div>
              <div className="cc-outcome">
                <span className="cc-label">Outcome</span>
                <strong className={`cc-status ${m.outcome_status}`}>{STATUS[m.outcome_status] ?? "Not set"}</strong>
                <span className="cc-sub">{d.start} to {d.end}</span>
              </div>
              <ul className="cc-rows">
                {cb && <li className="on"><span>{cb.heading}</span><b className={cb.cls}>{cb.label}</b></li>}
                {m.engagement_type && <li><span>Engagement</span><b>{m.engagement_type}</b></li>}
              </ul>
              {m.case_url && <a className="cc-btn" href={m.case_url}>Open in Org62 <ArrowUpRight /></a>}
            </div>
            {durN && (
              <div className="dur-card">
                <span className="cc-label">Duration</span>
                <strong>{durN}<small>{durU}</small></strong>
                <div className="dur-foot"><span>{team.length} people</span><span>{built.length} pieces</span></div>
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="wrap">
        {m.headline && (
          <aside className="float-card" aria-labelledby="h-highlights">
            <h2 id="h-highlights" className="kicker">Highlights</h2>
            <p className="big"><Rich text={m.headline} /></p>
            <ul className="facts">
              <li><Calendar /><b>When</b><span>{d.start} to {d.end}{d.duration && ` (${d.duration})`}</span></li>
              <li><Layers /><b>What kind</b><span>{m.engagement_type}</span></li>
              <li><Users /><b>Who</b><span>{team.map((t) => t.name).join(", ")}</span></li>
            </ul>
          </aside>
        )}

        <section className="block" aria-labelledby="h-built">
          <div className="block-head center">
            <p className="kicker">Delivery</p>
            <h2 id="h-built">What we built</h2>
          </div>
          <div className="bento">
            <div className="tile stat">
              <strong>{live.length}</strong>
              <p>{live.length === 1 ? "piece is" : "pieces are"} live in a customer org, out of {built.length}</p>
              <div className="bar" role="img" aria-label={counts.map(([s, n]) => `${n} ${STATUS[s] ?? s}`).join(", ")}>
                {counts.map(([s, n]) => <span key={s} className={`seg ${s}`} style={{ flexGrow: n }} />)}
              </div>
              <ul className="legend">{counts.map(([s, n]) => <li key={s}><i className={`seg ${s}`} />{STATUS[s] ?? s}<b>{n}</b></li>)}</ul>
            </div>
            <div className="tile pieces">
              <ul>
                {built.map((b) => (
                  <li key={b.name}><span className="name">{b.name}</span><Pill s={b.status} /></li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </div>

      {challenges.length > 0 && (
        <section className="band" aria-labelledby="h-hard">
          <div className="wrap">
            <p className="kicker">Lessons</p>
            <h2 id="h-hard">Roadblock items</h2>
            <div className="band-grid">
              {challenges.slice(0, 3).map((c) => (
                <article key={c.title}>
                  <h3>{c.title}</h3>
                  {c.result && <p><Rich text={c.result} /></p>}
                </article>
              ))}
            </div>
            {challenges.length > 3 && (
              <Link className="band-more" href="/retrospective#hard">
                {challenges.length - 3} more in the retrospective <ArrowUpRight />
              </Link>
            )}
          </div>
        </section>
      )}

      <div className="wrap">
        <section className="block" aria-labelledby="h-docs">
          <div className="block-head center">
            <p className="kicker">Documents</p>
            <h2 id="h-docs">Read the full story</h2>
          </div>
          <div className="docs">
            <Link className="doc light" href="/retrospective">
              <FileText />
              <b>Internal retrospective</b>
              <p>What was asked, what we built, roadblocks, field learnings and the risk read.</p>
              <span className="go"><ArrowUpRight /></span>
            </Link>
            {site.arch && (
              <Link className="doc accent" href="/architecture">
                <Network />
                <b>Architecture</b>
                <p>{site.arch.subtitle}</p>
                <span className="go"><ArrowUpRight /></span>
              </Link>
            )}
          </div>
        </section>

        {e.direction?.summary && (
          <section className="cta" aria-labelledby="h-next">
            <div>
              <p className="kicker">Next</p>
              <h2 id="h-next">Account next steps</h2>
              <p><Rich text={e.direction.summary} /></p>
            </div>
            <div className="cta-side">
              <Link className="btn primary" href="/retrospective#headed">{steps.length} open steps <ArrowUpRight /></Link>
              {e.checkin && <span className="checkin"><Flag /> 90-day check-in: {e.checkin.date || "not scheduled"}</span>}
            </div>
          </section>
        )}

        <footer className="foot">
          <div className="foot-brand">
            <b>{m.account}</b>
            <span>Internal to Salesforce. Do not share outside Salesforce.</span>
          </div>
          <nav aria-label="Pages">
            <b>Pages</b>
            <Link href="/retrospective">Retrospective</Link>
            {site.arch && <Link href="/architecture">Architecture</Link>}
          </nav>
          <nav aria-label="Records">
            <b>Records</b>
            {m.case_url && <a href={m.case_url}>{record}</a>}
            {m.opp?.name && <span><Rich text={m.opp.name} /></span>}
            {(m.dsrs ?? []).map((x: string, i: number) => <span key={i}><Rich text={x} /></span>)}
          </nav>
        </footer>
      </div>
    </main>
  );
}
