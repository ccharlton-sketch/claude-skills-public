import type { Metadata } from "next";
import { m, site, type Item } from "@/lib/site";
import { Rich } from "@/components/rich";
import { Pill } from "@/components/pill";
import { Highlights } from "@/components/highlights";
import { PrintButton } from "@/components/print-button";
import { ProductPills } from "@/components/product-pills";

export const metadata: Metadata = { title: `${m.account} | Engagement retrospective (internal)` };

const e = site.eng;
const list = (k: string): Item[] => e[k] ?? [];
const record = m.record_label || `Case ${m.case_number}`;

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`h-${id}`}>
      <h2 id={`h-${id}`}>{title}</h2>
      {children}
    </section>
  );
}

function Bullets({ title, items }: { title: string; items?: Item[] }) {
  if (!items?.length) return null;
  return (<><h3>{title}</h3><ul className="clean">{items.map((g, i) => <li key={i}><Rich text={g.text} /></li>)}</ul></>);
}

export default function Retrospective() {
  const r = e.request ?? {};
  const cb = m.case_badge;
  const notes = e.internal_notes ?? {};
  return (
    <div className="retro">
      <a className="skip" href="#main">Skip to content</a>
      <header className="hero">
        <div className="shapes" aria-hidden="true"><i /><i /><i /></div>
        <div className="wrap">
          <p className="kicker"><span className="tag">Internal only</span>{m.program || "Builder Engagement"} · {record}</p>
          <h1>{m.account_short || m.account}: engagement retrospective</h1>
          <p className="updated">Updated {m.updated}</p>
        </div>
      </header>
      <main id="main" className="wrap">
        <Highlights />
        <div className="toolbar"><PrintButton /></div>

        <Section id="snapshot" title="Snapshot">
          <table className="kv"><tbody>
            <tr><th scope="row">Account</th><td>{m.account}</td></tr>
            <tr><th scope="row">Engagement</th><td>{m.title} <span className="pill">{m.engagement_type}</span></td></tr>
            {m.products?.length > 0 && (
              <tr><th scope="row">Agentforce products</th><td>
                <ProductPills items={m.products} />
              </td></tr>
            )}
            {m.related_platform?.length > 0 && (
              <tr><th scope="row">Related platform</th><td><ProductPills items={m.related_platform} /></td></tr>
            )}
            <tr><th scope="row">Dates</th><td>{m.dates?.start} to {m.dates?.end}{m.dates?.duration && ` (${m.dates.duration})`}</td></tr>
            {m.opp && (
              <tr><th scope="row">Opportunity</th><td>
                <Rich text={m.opp.name} />: {m.opp.stage}{m.opp.amount && `, ${m.opp.amount}`}{m.opp.close && `, close ${m.opp.close}`}{m.opp.owner && ` (AE ${m.opp.owner})`}
              </td></tr>
            )}
            <tr><th scope="row">Team</th><td>
              {(m.team ?? []).map((t: Item, i: number) => (
                <div key={i}>{t.name}, {t.role}{t.allocation && ` (${t.allocation})`}</div>
              ))}
            </td></tr>
            {m.customer_contacts?.length > 0 && (
              <tr><th scope="row">Customer contacts</th><td>
                {m.customer_contacts.map((c: Item, i: number) => <div key={i}>{c.name}{c.title && `, ${c.title}`}</div>)}
              </td></tr>
            )}
            {cb && (
              <tr><th scope="row">{cb.heading}</th><td><span className={`pill ${cb.cls}`}>{cb.label}</span>{cb.detail && <> <span className="muted">{cb.detail}</span></>}</td></tr>
            )}
            <tr><th scope="row">Outcome</th><td><Pill s={m.outcome_status} /> <Rich text={m.outcome_summary} /></td></tr>
            <tr><th scope="row">Records</th><td>
              {m.case_url ? <a href={m.case_url}>{record}</a> : record}
              {(m.dsrs ?? []).map((d: string, i: number) => <span key={i}> · <Rich text={d} /></span>)}
              
            </td></tr>
          </tbody></table>
        </Section>

        <Section id="requested" title="Builder Engagement reason">
          <p className="lede"><Rich text={r.summary} /></p>
          <Bullets title="Goals at intake" items={r.goals} />
          <Bullets title="How success was defined" items={r.success_criteria} />
          <Bullets title="Out of scope" items={r.out_of_scope} />
        </Section>

        <Section id="built" title="What we built">
          <table>
            <thead><tr><th scope="col">Piece</th><th scope="col">Status</th><th scope="col">What it does</th></tr></thead>
            <tbody>{list("built").map((b, i) => (
              <tr key={i}><td><b>{b.name}</b></td><td><Pill s={b.status} /></td><td><Rich text={b.what} /></td></tr>
            ))}</tbody>
          </table>
          {m.video?.watch_url && <p>Demo recording: <a href={m.video.watch_url}>{m.video.title || "Vidyard demo"}</a></p>}
          <h3>Timeline</h3>
          <ol className="timeline">{list("timeline").map((t, i) => (
            <li key={i}><time>{t.date}</time><span><Rich text={t.event} /></span></li>
          ))}</ol>
        </Section>

        <Section id="hard" title="Roadblock items">
          {list("challenges").map((c, i) => (
            <div className="item" key={i}>
              <h3>{c.title}</h3><p><Rich text={c.detail} /></p>
              {c.tried && <div className="meta"><b>What we tried:</b> <Rich text={c.tried} /></div>}
              {c.result && <div className="meta"><b>Result:</b> <Rich text={c.result} /></div>}
            </div>
          ))}
        </Section>

        <Section id="learned" title="Field learnings from the team">
          <h3>What worked</h3>
          {list("worked").map((w, i) => (
            <div className="item" key={i}><p style={{ margin: 0 }}><Rich text={w.point} /></p>
              {w.takeaway && <div className="takeaway"><b>Takeaway:</b> <Rich text={w.takeaway} /></div>}</div>
          ))}
          <h3>What we&apos;d change</h3>
          {list("change").map((w, i) => (
            <div className="item" key={i}><p style={{ margin: 0 }}><Rich text={w.point} /></p>
              {w.takeaway && <div className="takeaway"><b>Next time:</b> <Rich text={w.takeaway} /></div>}</div>
          ))}
          <Bullets title="Lessons for other engagements" items={e.lessons} />
        </Section>

        <Section id="headed" title="Account next steps">
          <p className="lede"><Rich text={e.direction?.summary} /></p>
          {list("readiness").length > 0 && (<>
            <h3>Production readiness</h3>
            <table><thead><tr><th scope="col">Area</th><th scope="col">Rating</th><th scope="col">Why</th></tr></thead>
              <tbody>{list("readiness").map((x, i) => <tr key={i}><td>{x.area}</td><td><Pill s={x.rating} /></td><td><Rich text={x.note} /></td></tr>)}</tbody></table>
          </>)}
          <h3>Open items and next steps</h3>
          <table><thead><tr><th scope="col">Step</th><th scope="col">Owner</th><th scope="col">By</th></tr></thead>
            <tbody>{list("next_steps").map((s, i) => <tr key={i}><td><Rich text={s.step} /></td><td>{s.owner}</td><td>{s.date || "TBD"}</td></tr>)}</tbody></table>
          {e.checkin && <p><b>90-day check-in:</b> {e.checkin.date || "Not scheduled"}, led by {e.checkin.owner}.</p>}
        </Section>

        <Section id="internal" title="Internal notes">
          <div className="callout internal"><span className="label">Account risk read</span><Rich text={notes.risk_read} /></div>
          {notes.build_notes?.length > 0 && (<>
            <h3>{notes.build_notes_title || "How the build works"}</h3>
            <ul className="clean">{notes.build_notes.map((b: Item, i: number) => <li key={i}><b>{b.title}.</b> <Rich text={b.text} /></li>)}</ul>
          </>)}
          <Bullets title="Follow-ups for the account team" items={notes.followups} />
        </Section>


        <footer>Internal only. Built from {m.record_label || "the case, its comments and allocations"}, related DSRs, logged activity and Slack threads. Do not share outside Salesforce.</footer>
      </main>
    </div>
  );
}
