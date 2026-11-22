// Regenerates the SVG mockups and the self-contained HTML rendering of DESIGN.md.
//
//   cd docs/mockups
//   node build.mjs                 # SVGs only (no dependencies)
//   npm i --no-save marked@15 && node build.mjs   # SVGs + design-plan.html
//
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as screens from './screens.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = {
  '01-library.svg': screens.library(),
  '02-today.svg': screens.today(),
  '03-editor.svg': screens.editor(),
  '04-review.svg': screens.review(),
  '05-cards.svg': screens.cards(),
  '06-compact.svg': screens.compact(),
};
for (const [name, svg] of Object.entries(out)) {
  fs.writeFileSync(path.join(here, name), svg + '\n');
  console.log('wrote', name);
}

// ---- HTML rendering of DESIGN.md with the mockups inline ----
let marked;
try {
  ({ marked } = await import(process.env.MARKED_PATH || 'marked'));
} catch {
  console.log('marked not installed: skipping design-plan.html (npm i --no-save marked@15)');
  process.exit(0);
}

const md = fs.readFileSync(path.join(here, '..', 'DESIGN.md'), 'utf8');
const slug = (s) => s.toLowerCase().replace(/<[^>]+>/g, '').replace(/&#?\w+;/g, '').replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '-');
const toc = [];
const renderer = new marked.Renderer();
renderer.heading = function ({ tokens, depth }) {
  const inner = this.parser.parseInline(tokens);
  const id = slug(inner);
  if (depth === 2) toc.push({ id, text: inner.replace(/<[^>]+>/g, '') });
  return `<h${depth} id="${id}">${inner}</h${depth}>\n`;
};
renderer.image = function ({ href, text }) {
  const file = path.basename(href || '');
  if (out[file]) {
    const ns = file.slice(0, 2);
    // Namespace ids so several inline SVGs can live in one HTML page.
    const svg = out[file]
      .replace(/id="([^"]+)"/g, `id="m${ns}-$1"`)
      .replace(/url\(#([^)]+)\)/g, `url(#m${ns}-$1)`)
      .replace(/^<svg /, '<svg class="mock" ')
      .replace(/ width="\d+" height="\d+"/, '');
    return `<figure>${svg}<figcaption>${text} · <code>docs/mockups/${file}</code></figcaption></figure>`;
  }
  return `<img src="${href}" alt="${text}">`;
};
renderer.link = function ({ href, tokens }) {
  const inner = this.parser.parseInline(tokens);
  // relative links to repo files are meaningless inside the published page
  if (href && !/^https?:/.test(href) && !href.startsWith('#')) return `<span class="ref">${inner}</span>`;
  return `<a href="${href}">${inner}</a>`;
};
renderer.paragraph = function ({ tokens }) {
  const inner = this.parser.parseInline(tokens);
  return inner.startsWith('<figure>') ? inner + '\n' : `<p>${inner}</p>\n`;
};
marked.use({ renderer, gfm: true });
const body = marked.parse(md);

const html = `<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MathsMaster: design plan</title>
<style>
  :root{--bg:#F4F2EE;--surface:#fff;--ink:#1C1B19;--ink2:#6B6862;--line:#E2DED6;--accent:#1F7F74;--soft:#DDEFEC}
  @media (prefers-color-scheme: dark){:root{--bg:#121214;--surface:#1C1C1F;--ink:#F2F1EE;--ink2:#A3A09A;--line:#34343A;--accent:#5CC8B8;--soft:#1E3532}}
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,Ubuntu,sans-serif;-webkit-text-size-adjust:100%}
  .layout{display:grid;grid-template-columns:260px minmax(0,1fr);max-width:1320px;margin:0 auto}
  nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 18px;border-right:1px solid var(--line)}
  nav .brand{font-weight:800;font-size:20px;margin-bottom:4px}
  nav .sub{color:var(--ink2);font-size:13px;margin-bottom:18px}
  nav a{display:block;color:var(--ink2);text-decoration:none;font-size:14px;padding:5px 10px;border-radius:8px}
  nav a:hover{background:var(--soft);color:var(--ink)}
  main{padding:32px 48px 120px;min-width:0}
  h1{font-size:40px;line-height:1.15;margin:8px 0 18px;letter-spacing:-.02em}
  h2{font-size:28px;margin:64px 0 12px;padding-top:12px;border-top:1px solid var(--line);letter-spacing:-.01em}
  h3{font-size:20px;margin:36px 0 8px}
  a{color:var(--accent)}
  .ref{color:var(--accent)}
  blockquote{margin:0 0 24px;padding:14px 18px;background:var(--surface);border-left:4px solid var(--accent);border-radius:10px;color:var(--ink2)}
  blockquote p{margin:4px 0}
  code{font:14px/1.4 'SF Mono',ui-monospace,Menlo,Consolas,monospace;background:var(--soft);padding:1px 5px;border-radius:5px}
  pre{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;overflow:auto}
  pre code{background:none;padding:0;font-size:13px}
  table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14.5px;background:var(--surface);border-radius:12px;overflow:hidden;display:block;overflow-x:auto}
  th,td{border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
  th{background:var(--soft);font-weight:650}
  tr:last-child td{border-bottom:none}
  figure{margin:24px 0 32px;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px}
  figure svg.mock{width:100%;height:auto;display:block}
  figcaption{color:var(--ink2);font-size:14px;margin-top:10px;text-align:center}
  ul,ol{padding-left:24px}
  li{margin:4px 0}
  hr{border:none;border-top:1px solid var(--line);margin:40px 0}
  input[type=checkbox]{margin-right:6px}
  @media (max-width:900px){.layout{grid-template-columns:1fr}nav{position:static;height:auto;border-right:none;border-bottom:1px solid var(--line)}main{padding:20px}}
</style>
</head>
<body>
<div class="layout">
<nav>
  <div class="brand">MathsMaster</div>
  <div class="sub">Design plan v1 · 22 Nov 2026</div>
  ${toc.map((t) => `<a href="#${t.id}">${t.text}</a>`).join('\n  ')}
</nav>
<main>
${body}
</main>
</div>
</body>
</html>
`;
fs.writeFileSync(path.join(here, 'design-plan.html'), html);
console.log('wrote design-plan.html');
