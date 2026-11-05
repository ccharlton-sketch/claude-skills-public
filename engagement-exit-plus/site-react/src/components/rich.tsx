import { Fragment, type ReactNode } from "react";

// Text fields can hold [label](https://url) links to real records: Org62, Slack canvases, channels.
const LINK = /\[([^\]\n]+)\]\((https:\/\/[^)\s]+)\)/g;

export function Rich({ text }: { text?: string | null }) {
  if (!text) return null;
  const out: ReactNode[] = [];
  let last = 0;
  for (const mt of text.matchAll(LINK)) {
    const i = mt.index ?? 0;
    out.push(<Fragment key={`t${i}`}>{text.slice(last, i)}</Fragment>);
    out.push(<a key={`a${i}`} href={mt[2]}>{mt[1]}</a>);
    last = i + mt[0].length;
  }
  out.push(<Fragment key="end">{text.slice(last)}</Fragment>);
  return <>{out}</>;
}
