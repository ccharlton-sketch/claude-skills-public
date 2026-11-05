"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

// "On this page" sidebar: lists the page's h2 sections, highlights the one you're reading,
// and can be hidden. The choice is remembered across pages. Under 960px it overlays the page.
const KEY = "eng-sidebar";
const NARROW = "(max-width:960px)";
type Entry = { id: string; label: string };

function slugify(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "s";
}

export function Sidebar() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Entry[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const tabRef = useRef<HTMLButtonElement>(null);
  const moveFocus = useRef(false);

  const narrow = () => window.matchMedia(NARROW).matches;

  // Start from what the inline head script already applied, so there's no jump on load.
  useEffect(() => {
    setOpen(document.documentElement.classList.contains("sb-open"));
    const id = requestAnimationFrame(() => document.documentElement.classList.add("sb-anim"));
    const mq = window.matchMedia(NARROW);
    const onChange = (e: MediaQueryListEvent) => {
      let saved: string | null = null;
      try { saved = localStorage.getItem(KEY); } catch {}
      setOpen(!e.matches && saved !== "closed");
    };
    mq.addEventListener("change", onChange);
    return () => { cancelAnimationFrame(id); mq.removeEventListener("change", onChange); };
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("sb-open", open);
    if (moveFocus.current) {
      moveFocus.current = false;
      tabRef.current?.focus();
    }
  }, [open]);

  const toggle = useCallback((next: boolean) => {
    moveFocus.current = true;
    setOpen(next);
    if (!narrow()) { try { localStorage.setItem(KEY, next ? "open" : "closed"); } catch {} }
  }, []);

  // Keep --bar-h in step with the site bar, which can wrap on small screens.
  useEffect(() => {
    const set = () => {
      const n = document.querySelector<HTMLElement>(".sitebar");
      if (n) document.documentElement.style.setProperty("--bar-h", `${n.offsetHeight}px`);
    };
    set();
    window.addEventListener("resize", set);
    return () => window.removeEventListener("resize", set);
  }, []);

  // Build the list from this page's own h2s, then follow the scroll.
  useEffect(() => {
    const used = new Set<string>();
    const heads: HTMLElement[] = [];
    const list: Entry[] = [];
    document.querySelectorAll<HTMLElement>("main h2").forEach((h) => {
      const c = h.cloneNode(true) as HTMLElement;
      c.querySelectorAll(".pill,.tag,svg").forEach((x) => x.remove());
      const label = (c.textContent ?? "").replace(/\s+/g, " ").trim();
      if (!label) return;
      if (!h.id) {
        const base = slugify(label);
        let id = base, i = 2;
        while (used.has(id) || document.getElementById(id)) id = `${base}-${i++}`;
        h.id = id;
      }
      used.add(h.id);
      heads.push(h);
      list.push({ id: h.id, label });
    });
    setItems(list);
    const spy = () => {
      const y = (parseInt(getComputedStyle(document.documentElement).getPropertyValue("--bar-h")) || 64) + 110;
      let act = heads[0];
      for (const h of heads) if (h.getBoundingClientRect().top - y <= 0) act = h;
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2 && heads.length) act = heads[heads.length - 1];
      setActive(act?.id ?? null);
    };
    spy();
    window.addEventListener("scroll", spy, { passive: true });
    window.addEventListener("resize", spy);
    return () => { window.removeEventListener("scroll", spy); window.removeEventListener("resize", spy); };
  }, [path]);

  // On narrow screens, Escape or a click outside closes the overlay.
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if (e.key === "Escape" && open && narrow()) toggle(false); };
    const click = (e: MouseEvent) => {
      if (open && narrow() && !(e.target as Element).closest(".sidebar,.sb-tab")) setOpen(false);
    };
    document.addEventListener("keydown", key);
    document.addEventListener("click", click);
    return () => { document.removeEventListener("keydown", key); document.removeEventListener("click", click); };
  }, [open, toggle]);

  return (
    <>
      <aside className="sidebar" id="sidebar" aria-label="On this page">
        <div className="sb-head">
          <p className="sb-title">On this page</p>
        </div>
        <nav>
          <ol>
            {items.map((it) => (
              <li key={it.id}>
                <a href={`#${it.id}`} title={it.label} className={active === it.id ? "active" : undefined}
                   aria-current={active === it.id ? "location" : undefined}
                   onClick={() => { if (narrow()) setOpen(false); }}>{it.label}</a>
              </li>
            ))}
          </ol>
        </nav>
      </aside>
      <button ref={tabRef} type="button" className="sb-tab" aria-controls="sidebar" aria-expanded={open} onClick={() => toggle(!open)}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" />
          {open && <path d="m16 15-3-3 3-3" />}
        </svg>
        <span>{open ? "Hide" : "Contents"}</span>
      </button>
    </>
  );
}
