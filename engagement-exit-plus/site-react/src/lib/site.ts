import raw from "@/data/site.json";

export type Item = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
export type Site = {
  slug: string;
  account: string;
  sidebar: boolean;
  brand: { sf: string; cust: string; kind: "svg" | "png" } | null;
  pages: string[];
  arch: { subtitle: string; style: string; body: string } | null;
  eng: Item;
};

export const site = raw as unknown as Site;
export const m: Item = site.eng.meta;

export const STATUS: Record<string, string> = {
  live_sandbox: "Live in sandbox", live_production: "Live in production", completed: "Completed", in_build: "In build",
  planned: "Planned", cancelled: "Cancelled", paused: "Paused", ready: "Ready", at_risk: "At risk", blocked: "Blocked",
};

export const PAGES: { route: string; label: string }[] = [
  { route: "retrospective", label: "Retrospective" },
  { route: "architecture", label: "Architecture" },
];
