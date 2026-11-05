"use client";
import { useEffect, useRef, useState } from "react";

type P = string | { name: string; status?: string; reached?: string };

const CLS: Record<string, string> = { live_production: "prod-live", live_sandbox: "prod-sbx", cancelled: "prod-no" };
const MSG: Record<string, string> = {
  live_production: "reached production", live_sandbox: "reached sandbox, not yet production",
  cancelled: "was cancelled", planned: "is planned, not started",
  paused: "is paused", in_build: "is in build",
};

function Tag({ x }: { x: P }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const name = typeof x === "string" ? x : x.name;
  const st = typeof x === "string" ? "" : x.status ?? "";
  const reached = typeof x === "string" ? "" : x.reached ?? "";
  const where = reached === "live_production" ? "production" : reached === "live_sandbox" ? "sandbox" : "";
  const msg = where && (st === "cancelled" || st === "paused")
    ? `${name} reached ${where}, then ${st === "cancelled" ? "was cancelled" : "was paused"}.`
    : `${name} ${MSG[st] ?? "is not in sandbox or production"}.`;
  useEffect(() => {
    if (!open) return;
    const close = (e: Event) => {
      if (e instanceof KeyboardEvent ? e.key === "Escape" : !ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => { document.removeEventListener("mousedown", close); document.removeEventListener("keydown", close); };
  }, [open]);
  return (
    <span className="prod-wrap" ref={ref}>
      <button type="button" className={`pill prod ${CLS[st] ?? ""}`} aria-expanded={open} onClick={() => setOpen(!open)}>
        {name}
      </button>
      {open && <span className="prod-pop" role="status">{msg}</span>}
    </span>
  );
}

export function ProductPills({ items }: { items: P[] }) {
  return <>{items.map((x, i) => <span key={i}><Tag x={x} /> </span>)}</>;
}
