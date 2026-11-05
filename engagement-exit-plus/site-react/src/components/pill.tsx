import { STATUS } from "@/lib/site";

export function Pill({ s, className = "" }: { s?: string; className?: string }) {
  if (!s) return null;
  return <span className={`pill ${s} ${className}`.trim()}>{STATUS[s] ?? s}</span>;
}
