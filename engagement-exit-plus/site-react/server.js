// Serves the static export in out/. GET and HEAD only, no directory listings,
// nothing outside out/. Pages are /, /retrospective and /architecture.
/* eslint-disable @typescript-eslint/no-require-imports */
const http = require("http");
const fs = require("fs");
const path = require("path");

const OUT = path.join(__dirname, "out");
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".woff2": "font/woff2", ".json": "application/json", ".txt": "text/plain; charset=utf-8",
};
const BASE = {
  "X-Robots-Tag": "noindex, nofollow",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

function resolve(url) {
  let p;
  try { p = decodeURIComponent(url.split("?")[0]); } catch { return null; }
  p = p.replace(/\/+$/, "") || "/";
  const candidates = p === "/" ? ["index.html"] : [p.slice(1), p.slice(1) + ".html"];
  for (const c of candidates) {
    const f = path.join(OUT, c);
    if (!f.startsWith(OUT + path.sep)) return null;
    try { if (fs.statSync(f).isFile()) return f; } catch { /* next */ }
  }
  return null;
}

http.createServer((req, res) => {
  if (req.method !== "GET" && req.method !== "HEAD") { res.writeHead(405, BASE); return res.end(); }
  const file = resolve(req.url || "/");
  const send = (status, f) => fs.readFile(f, (err, body) => {
    if (err) { res.writeHead(500, BASE); return res.end(); }
    const ext = path.extname(f);
    const cache = f.includes(`${path.sep}_next${path.sep}static${path.sep}`) ? "public, max-age=31536000, immutable" : "no-cache";
    res.writeHead(status, { ...BASE, "Content-Type": TYPES[ext] || "application/octet-stream", "Cache-Control": cache });
    res.end(req.method === "HEAD" ? undefined : body);
  });
  if (file) return send(200, file);
  const nf = path.join(OUT, "404.html");
  if (fs.existsSync(nf)) return send(404, nf);
  res.writeHead(404, { ...BASE, "Content-Type": "text/plain" }); res.end("Not found");
}).listen(process.env.PORT || 5005, () => console.log(`listening on ${process.env.PORT || 5005}`));
