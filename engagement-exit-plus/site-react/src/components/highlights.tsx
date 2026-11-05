import { m } from "@/lib/site";
import { Rich } from "./rich";

export function Highlights() {
  if (!m.headline) return null;
  return (
    <aside className="highlights" aria-labelledby="h-highlights">
      <h2 id="h-highlights">Highlights</h2>
      <p><Rich text={m.headline} /></p>
    </aside>
  );
}
