import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { site } from "@/lib/site";

export const metadata: Metadata = { title: `${site.account} | Architecture` };

// The diagram's renderer writes page-level CSS (:root vars, body, header, h1, .pill).
// Nest all of it under .arch-page so it can't restyle the site bar or sidebar.
function scoped(css: string) {
  return `.arch-page{${css.replace(/:root\s*\{/g, "&{").replace(/(^|[}\s,])body\s*\{/g, "$1&{")}}`;
}

// Remap the diagram palette to the site's Salesforce blue and navy, and give its hero the site's light look.
const THEME = `.arch-page{
  --paper:var(--bg);--sheet:#fff;--sunken:#edf2f9;--zone:#f4f8fd;
  --ink:#0b1f38;--ink-2:#43536a;--ink-3:#5b6a7f;--rule:#dfe6f0;--rule-strong:#c9d5e4;
  --brand:#0176d3;--brand-deep:#032d60;--brand-soft:#e3f0fd;--brand-rule:#a6cdf5;
  --sans:"Manrope",system-ui,sans-serif;--mono:"Manrope",system-ui,sans-serif;
  background:var(--bg);font-family:var(--sans)}
.arch-page header{position:relative;overflow:hidden;background:linear-gradient(var(--blue-tint),var(--bg));color:var(--ink);padding:4rem 1.5rem 2.5rem}
.arch-page header::before,.arch-page header::after{content:"";position:absolute;top:-20%;height:140%;background:#0176d3;opacity:.05;transform:skewX(-28deg);pointer-events:none}
.arch-page header::before{right:-6%;width:30%}.arch-page header::after{right:26%;width:8%;opacity:.035}
.arch-page header .wrap{position:relative}
.arch-page .crumbs{font:700 .74rem/1.2 var(--sans);letter-spacing:.12em;color:#0176d3;opacity:1}
.arch-page h1{color:var(--ink);font-size:clamp(2rem,3.8vw,3rem);line-height:1.08;font-weight:600;letter-spacing:-.03em;margin:.8rem 0 1rem;max-width:24ch}
.arch-page header p{color:var(--ink-2);font-size:1.05rem;opacity:1}
.arch-page .updated{font:400 .85rem var(--sans);color:var(--ink-3);opacity:1;margin-top:1.25rem}
.arch-page h2{font-weight:600;letter-spacing:-.02em}
.arch-page .diagram{border-radius:20px;border:0;box-shadow:0 1px 2px rgb(3 30 66 / .04),0 18px 40px -18px rgb(3 30 66 / .16)}
.arch-page .pill{font:700 .68rem var(--sans);letter-spacing:.08em}`;

export default function Architecture() {
  if (!site.arch) notFound();
  return (
    <div className="arch-page">
      <style dangerouslySetInnerHTML={{ __html: scoped(site.arch.style) + THEME }} />
      <div dangerouslySetInnerHTML={{ __html: site.arch.body }} />
    </div>
  );
}
