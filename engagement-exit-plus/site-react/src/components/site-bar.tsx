"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PAGES, site } from "@/lib/site";

export function SiteBar() {
  const path = usePathname().replace(/\/+$/, "") || "/";
  const here = (p: string) => (path === p ? { "aria-current": "page" as const } : {});
  const b = site.brand;
  return (
    <nav className="sitebar" aria-label="Site">
      <div className="in">
        {b && (
          <Link className="brand" href="/" aria-label={`Salesforce and ${site.account}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="sf" src={b.sf} alt="" />
            <span className="sep" aria-hidden="true" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className={`cust ${b.kind}`} src={b.cust} alt="" />
          </Link>
        )}
        <Link className="home" href="/" {...here("/")}>{site.account} · Engagement</Link>
        {PAGES.filter((p) => site.pages.includes(p.route)).map((p) => (
          <Link key={p.route} href={`/${p.route}`} {...here(`/${p.route}`)}>{p.label}</Link>
        ))}
        <span className="tag">INTERNAL</span>
      </div>
    </nav>
  );
}
