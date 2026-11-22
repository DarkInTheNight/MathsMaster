// Shared drawing helpers for the MathsMaster layout mockups.
// Pure functions that return SVG strings. No dependencies.

export const C = {
  bg: '#F4F2EE', surface: '#FFFFFF', surface2: '#EEEBE5', sidebar: '#FAF9F6',
  ink: '#1C1B19', ink2: '#6B6862', ink3: '#9C988F', line: '#E2DED6',
  accent: '#1F7F74', accentSoft: '#DDEFEC', accentDark: '#5CC8B8',
  again: '#E5484D', hard: '#E8930C', good: '#2E9E62', easy: '#3B7BF5',
  penBlack: '#1A1A1A', penBlue: '#1E4FD8', penRed: '#D7263D', penGreen: '#13865B', hl: '#FFE45C',
  // course palette
  indigo: '#5B6CF0', teal: '#1F9E8F', amber: '#D69A00', coral: '#E0645A', violet: '#9A5BD8',
  sky: '#2F9BDB', green: '#4AA35A', rose: '#D9578A', slate: '#5F7389', orange: '#E07B2E',
};

export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export const STYLE = `
  <style>
    .ui{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI','Ubuntu','Helvetica Neue',Arial,sans-serif}
    .rnd{font-family:'SF Pro Rounded',ui-rounded,-apple-system,'Segoe UI','Ubuntu',Arial,sans-serif}
    .serif{font-family:'Latin Modern Roman','CMU Serif','STIX Two Text','Cambria','Times New Roman','DejaVu Serif',serif}
    .hand{font-family:'Bradley Hand','Noteworthy','Ink Free','Segoe Print','Comic Neue','Comic Sans MS',cursive}
    .mono{font-family:'SF Mono',ui-monospace,Menlo,Consolas,'Ubuntu Mono',monospace}
  </style>`;

export const DEFS = `
  <defs>
    <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="5" flood-color="#000" flood-opacity="0.08"/>
    </filter>
    <filter id="sh2" x="-20%" y="-20%" width="140%" height="160%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#000" flood-opacity="0.14"/>
    </filter>
    <pattern id="dots" width="14.2" height="14.2" patternUnits="userSpaceOnUse">
      <circle cx="7.1" cy="7.1" r="0.9" fill="#C9C4BA"/>
    </pattern>
    <pattern id="dotsSmall" width="6" height="6" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="3" r="0.5" fill="#CFCAC0"/>
    </pattern>
    <pattern id="squares" width="14.2" height="14.2" patternUnits="userSpaceOnUse">
      <path d="M14.2 0 V14.2 H0" fill="none" stroke="#E4E9F0" stroke-width="0.8"/>
    </pattern>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.92"/>
      <stop offset="1" stop-color="#F6F4F0" stop-opacity="0.86"/>
    </linearGradient>
  </defs>`;

export function text(x, y, s, o = {}) {
  const {
    size = 15, weight = 400, fill = C.ink, anchor = 'start', cls = 'ui', ls, italic, opacity, raw = false,
  } = o;
  const attrs = [
    `x="${x}"`, `y="${y}"`, `class="${cls}"`, `font-size="${size}"`, `font-weight="${weight}"`, `fill="${fill}"`,
    anchor !== 'start' ? `text-anchor="${anchor}"` : '', ls ? `letter-spacing="${ls}"` : '',
    italic ? 'font-style="italic"' : '', opacity != null ? `opacity="${opacity}"` : '',
  ].filter(Boolean).join(' ');
  return `<text ${attrs}>${raw ? s : esc(s)}</text>`;
}

export function rect(x, y, w, h, o = {}) {
  const { rx = 0, fill = 'none', stroke, sw = 1, filter, opacity, dash } = o;
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}"${stroke ? ` stroke="${stroke}" stroke-width="${sw}"` : ''}${filter ? ` filter="url(#${filter})"` : ''}${opacity != null ? ` opacity="${opacity}"` : ''}${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
}

export const circle = (cx, cy, r, fill, o = {}) =>
  `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"${o.stroke ? ` stroke="${o.stroke}" stroke-width="${o.sw || 1}"` : ''}${o.opacity != null ? ` opacity="${o.opacity}"` : ''}/>`;

export const line = (x1, y1, x2, y2, stroke = C.line, sw = 1, o = {}) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round"${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}/>`;

export const path = (d, o = {}) => {
  const { stroke = C.ink, sw = 1.8, fill = 'none', opacity, dash } = o;
  return `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"${opacity != null ? ` opacity="${opacity}"` : ''}${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
};

// Approximate text width for layout of chips/pills.
export const tw = (s, size = 13, k = 0.56) => Math.round(String(s).length * size * k);

// ---------- icons (24-unit grid, stroked) ----------
const ICONS = {
  today: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
  cards: '<rect x="3.5" y="7.5" width="13" height="13" rx="2.5"/><path d="M7.5 4h10.5a2.5 2.5 0 0 1 2.5 2.5V17"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L20.5 20.5"/>',
  inbox: '<path d="M3.5 13.5l2.6-8h11.8l2.6 8v5a1.5 1.5 0 0 1-1.5 1.5h-14a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M3.5 13.5h4.8l1.6 2.6h4.2l1.6-2.6h4.8"/>',
  doc: '<path d="M6.5 3h7.5l5 5v12a1 1 0 0 1-1 1h-11.5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5"/>',
  notebook: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v18M12 8h4M12 11.5h4"/>',
  sheet: '<path d="M6.5 3h11a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>',
  bookmark: '<path d="M7 3.5h10v17l-5-4-5 4z"/>',
  tag: '<path d="M3.5 11.5V4.5a1 1 0 0 1 1-1h7l9 9-8 8z"/><circle cx="8" cy="8" r="1.4"/>',
  trash: '<path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>',
  sidebar: '<rect x="3" y="4.5" width="18" height="15" rx="3"/><path d="M9.5 4.5v15"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevD: '<path d="M7 9.5l5 5 5-5"/>',
  chevR: '<path d="M9.5 7l5 5-5 5"/>',
  chevL: '<path d="M14.5 6l-6 6 6 6"/>',
  share: '<path d="M12 3.5v11M8 7.5l4-4 4 4M6.5 11H5.5v9h13v-9h-1"/>',
  more: '<circle cx="6" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="18" cy="12" r="1.3"/>',
  undo: '<path d="M8.5 6L4 10.5 8.5 15"/><path d="M4 10.5h10a5 5 0 0 1 0 10h-3"/>',
  redo: '<path d="M15.5 6L20 10.5 15.5 15"/><path d="M20 10.5H10a5 5 0 0 0 0 10h3"/>',
  pane: '<rect x="3" y="4.5" width="18" height="15" rx="2"/><path d="M11 4.5v15"/>',
  cardPlus: '<rect x="3.5" y="6" width="13" height="14" rx="2.5"/><path d="M10 10v6M7 13h6M19.5 4v6M16.5 7h6"/>',
  edit: '<path d="M4 20l1-4.5L16 4.5l3.5 3.5-11 11z"/><path d="M14 6.5l3.5 3.5"/>',
  flag: '<path d="M5.5 21V4h12l-2.5 4.5 2.5 4.5h-12"/>',
  source: '<path d="M7 17L17 7M9 7h8v8"/>',
  close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  cloud: '<path d="M7 18.5h10a4 4 0 0 0 .5-8 6 6 0 0 0-11.4 1.6A3.3 3.3 0 0 0 7 18.5z"/><path d="M9.5 14l2 2 3.5-3.5"/>',
  pages: '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/>',
  lasso: '<ellipse cx="12" cy="10" rx="8" ry="5.5" stroke-dasharray="2.5 2.5"/><path d="M8 14.5c-1 2-.5 4 1.5 5"/>',
  scan: '<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16M4 12h16"/>',
  flame: '<path d="M12 21c4 0 6.5-2.6 6.5-6.2 0-3.6-2.8-5.8-4-9.3-2 1.5-2.5 3.8-2.5 5.3-1.2-.8-2-2-2.2-3.3C7.5 9.5 5.5 12 5.5 14.8 5.5 18.4 8 21 12 21z"/>',
  send: '<path d="M4 12l16-8-6 16-2.5-6.5z"/><path d="M11.5 13.5L20 4"/>',
  mic: '<rect x="9" y="3.5" width="6" height="11" rx="3"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v2.5"/>',
  pen: '<path d="M4 20l1.2-4.8L15.5 4.9a2 2 0 0 1 2.8 0l.8.8a2 2 0 0 1 0 2.8L8.8 18.8z"/>',
};
export function icon(name, x, y, s = 20, color = C.ink, sw = 1.8) {
  const k = s / 24;
  return `<g transform="translate(${x} ${y}) scale(${k})" fill="none" stroke="${color}" stroke-width="${sw / k > 3 ? 3 : sw / k}" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</g>`;
}
export function sparkle(x, y, s = 18, color = C.accent) {
  const k = s / 24;
  return `<path transform="translate(${x} ${y}) scale(${k})" d="M12 2.5C12.9 8 16 11.1 21.5 12 16 12.9 12.9 16 12 21.5 11.1 16 8 12.9 2.5 12 8 11.1 11.1 8 12 2.5Z" fill="${color}"/>`;
}

// ---------- components ----------
export function chip(x, y, label, o = {}) {
  const { fill = C.surface2, color = C.ink2, size = 12, h = 22, pad = 9, weight = 600, dot, stroke } = o;
  const w = tw(label, size) + pad * 2 + (dot ? 12 : 0);
  return {
    w,
    svg: `${rect(x, y, w, h, { rx: h / 2, fill, stroke })}${dot ? circle(x + pad + 3, y + h / 2, 3.5, dot) : ''}${text(x + pad + (dot ? 12 : 0), y + h / 2 + size * 0.36, label, { size, weight, fill: color })}`,
  };
}

export function badge(xRight, yMid, n, o = {}) {
  const { fill = C.surface2, color = C.ink2, size = 12 } = o;
  const w = Math.max(24, tw(n, size, 0.62) + 14);
  return rect(xRight - w, yMid - 11, w, 22, { rx: 11, fill }) + text(xRight - w / 2, yMid + 4.5, n, { size, weight: 700, fill: color, anchor: 'middle', cls: 'rnd' });
}

export function button(x, y, w, h, label, o = {}) {
  const { fill = C.accent, color = '#fff', size = 15, weight = 650, stroke, rx = h / 2, iconName, filter } = o;
  const ic = iconName ? icon(iconName, x + 16, y + h / 2 - 9, 18, color, 2) : '';
  const tx = iconName ? x + w / 2 + 10 : x + w / 2;
  return rect(x, y, w, h, { rx, fill, stroke, filter }) + ic + text(tx, y + h / 2 + size * 0.36, label, { size, weight, fill: color, anchor: 'middle' });
}

// A typeset-looking page thumbnail (lecture notes / example sheet).
export function pdfThumb(x, y, w, h, o = {}) {
  const { ink = true, accent = C.indigo, seed = 1, title = true, highlight = true } = o;
  let s = rect(x, y, w, h, { rx: 4, fill: '#fff', stroke: C.line, filter: 'sh' });
  const m = w * 0.12;
  let yy = y + h * 0.1;
  if (title) { s += rect(x + w * 0.25, yy, w * 0.5, h * 0.03, { rx: 1, fill: '#C9C5BD' }); yy += h * 0.07; }
  const rows = Math.floor((h * 0.8) / (h * 0.045));
  for (let i = 0; i < rows; i++) {
    const r = ((i * 37 + seed * 11) % 23) / 23;
    const ww = (w - 2 * m) * (i % 6 === 5 ? 0.55 : 0.82 + r * 0.18);
    if (i % 7 === 3) { yy += h * 0.02; s += rect(x + w * 0.3, yy, w * 0.4, h * 0.022, { rx: 1, fill: '#D6D2CA' }); yy += h * 0.05; continue; }
    s += rect(x + m, yy, ww, h * 0.018, { rx: 1, fill: '#DEDAD3' });
    yy += h * 0.045;
  }
  if (highlight) s += rect(x + m - 2, y + h * 0.36, (w - 2 * m) * 0.7, h * 0.028, { rx: 2, fill: C.hl, opacity: 0.55 });
  if (ink) {
    s += path(`M${x + w * 0.62} ${y + h * 0.58} q${w * 0.06} ${-h * 0.03} ${w * 0.12} 0 t${w * 0.12} 0`, { stroke: C.penBlue, sw: 1.2 });
    s += path(`M${x + m} ${y + h * 0.75} c${w * 0.1} ${-h * 0.02} ${w * 0.3} ${h * 0.02} ${w * 0.4} 0`, { stroke: C.penRed, sw: 1.1 });
  }
  s += rect(x, y + h - 3, w, 3, { fill: accent, opacity: 0.9 });
  return s;
}

// A handwritten notebook thumbnail (dot grid + squiggles).
export function noteThumb(x, y, w, h, o = {}) {
  const { accent = C.indigo, seed = 1, squares = false } = o;
  let s = rect(x, y, w, h, { rx: 4, fill: '#fff', stroke: C.line, filter: 'sh' });
  s += rect(x + 2, y + 2, w - 4, h - 4, { fill: squares ? 'url(#squares)' : 'url(#dotsSmall)' });
  let yy = y + h * 0.14;
  for (let i = 0; i < 9; i++) {
    const r = ((i * 29 + seed * 7) % 17) / 17;
    const len = w * (0.45 + r * 0.38);
    const xx = x + w * 0.1 + (i % 4 === 2 ? w * 0.08 : 0);
    const amp = h * 0.012;
    let d = `M${xx} ${yy}`;
    const steps = Math.max(3, Math.floor(len / 9));
    for (let k = 0; k < steps; k++) d += ` q${len / steps / 2} ${k % 2 ? amp : -amp} ${len / steps} ${((k * 13 + seed) % 5 - 2) * 0.3}`;
    s += path(d, { stroke: i === 4 ? C.penBlue : C.penBlack, sw: 1.1 });
    yy += h * 0.085;
  }
  s += path(`M${x + w * 0.1} ${y + h * 0.5} h${w * 0.5} v${h * 0.08} h${-w * 0.5} z`, { stroke: C.penRed, sw: 1 });
  s += rect(x, y + h - 3, w, 3, { fill: accent, opacity: 0.9 });
  return s;
}

// iPad frame + status bar. Content is drawn in screen coordinates (0,0)-(w,h).
export function device(w, h, content, o = {}) {
  const { bezel = 20, title = '', time = '9:41', date = 'Sun 22 Nov', dark = false, bg = C.bg } = o;
  const W = w + bezel * 2, H = h + bezel * 2;
  const sb = dark ? '#fff' : C.ink;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(title)}">
  <title>${esc(title)}</title>${STYLE}${DEFS}
  <defs><clipPath id="screen"><rect x="0" y="0" width="${w}" height="${h}" rx="24"/></clipPath></defs>
  <rect x="0" y="0" width="${W}" height="${H}" rx="${bezel + 24}" fill="#1E1E20"/>
  <rect x="2" y="2" width="${W - 4}" height="${H - 4}" rx="${bezel + 22}" fill="none" stroke="#3A3A3E" stroke-width="2"/>
  <g transform="translate(${bezel} ${bezel})" clip-path="url(#screen)">
    <rect x="0" y="0" width="${w}" height="${h}" fill="${bg}"/>
    ${content}
    ${text(24, 19, time, { size: 14, weight: 650, fill: sb })}
    ${text(70, 19, date, { size: 14, weight: 500, fill: sb })}
    ${rect(w - 46, 8, 26, 12, { rx: 3.5, stroke: sb, sw: 1.2 })}${rect(w - 44, 10, 20, 8, { rx: 2, fill: sb })}${rect(w - 19, 12, 2, 4, { rx: 1, fill: sb })}
    ${text(w - 54, 19, '100%', { size: 13, weight: 600, fill: sb, anchor: 'end' })}
  </g>
</svg>`;
}

// Sidebar used by several screens.
export function sidebar(o = {}) {
  const { selected = 'Linear Algebra', x = 10, y = 32, w = 292, h = 982 } = o;
  let s = rect(x, y, w, h, { rx: 22, fill: C.sidebar, stroke: '#E8E4DC', filter: 'sh' });
  s += icon('sidebar', x + 16, y + 14, 22, C.accent);
  s += icon('plus', x + w - 38, y + 14, 22, C.accent);
  s += text(x + 18, y + 72, 'MathsMaster', { size: 26, weight: 750 });
  const row = (yy, ic, label, opt = {}) => {
    let r = '';
    const sel = label === selected;
    if (sel) r += rect(x + 10, yy, w - 20, 38, { rx: 10, fill: C.accent });
    const col = sel ? '#fff' : C.ink;
    if (opt.dot) r += circle(x + 30, yy + 19, 6, opt.dot);
    else r += icon(ic, x + 20, yy + 9, 20, sel ? '#fff' : C.accent);
    r += text(x + 52, yy + 24.5, label, { size: 16, weight: sel ? 600 : 450, fill: col });
    if (opt.badge != null) r += badge(x + w - 22, yy + 19, opt.badge, sel ? { fill: 'rgba(255,255,255,0.25)', color: '#fff' } : opt.badgeAccent ? { fill: C.accentSoft, color: C.accent } : {});
    if (opt.hint) r += text(x + w - 24, yy + 24, opt.hint, { size: 13, fill: C.ink3, anchor: 'end' });
    return r;
  };
  let yy = y + 90;
  s += row(yy, 'today', 'Today'); yy += 40;
  s += row(yy, 'cards', 'Cards', { badge: 64 }); yy += 40;
  s += row(yy, 'search', 'Search', { hint: '⌘K' }); yy += 40;
  s += row(yy, 'inbox', 'Inbox', { badge: 12, badgeAccent: true }); yy += 40;
  const sec = (yy, label, right) => text(x + 20, yy, label, { size: 12, weight: 700, fill: C.ink3, ls: 0.8 }) + (right ? text(x + w - 40, yy, right, { size: 12, fill: C.ink3, anchor: 'end' }) : '') + icon(right ? 'chevR' : 'chevD', x + w - 36, yy - 13, 16, C.ink3);
  yy += 34; s += sec(yy, 'MICHAELMAS 2026'); yy += 12;
  const courses = [['Linear Algebra', C.indigo, 23], ['Analysis & Topology', C.teal, 18], ['Methods', C.amber, 11], ['Quantum Mechanics', C.coral, 8], ['Markov Chains', C.violet, 4]];
  for (const [n, c, b] of courses) { s += row(yy, null, n, { dot: c, badge: b }); yy += 40; }
  yy += 30; s += sec(yy, 'LENT 2027', '6 courses');
  yy += 34; s += sec(yy, 'EASTER 2027', '2 courses');
  yy += 40; s += sec(yy, 'LIBRARY'); yy += 12;
  for (const [ic, n] of [['doc', 'All documents'], ['notebook', 'Notebooks'], ['sheet', 'Example sheets'], ['bookmark', 'Bookmarks'], ['tag', 'Tags'], ['trash', 'Trash']]) { s += row(yy, ic, n); yy += 40; }
  s += line(x + 16, y + h - 64, x + w - 16, y + h - 64, C.line);
  s += icon('gear', x + 20, y + h - 46, 20, C.ink2);
  s += text(x + 50, y + h - 31, 'Settings', { size: 15, fill: C.ink2 });
  s += icon('cloud', x + w - 150, y + h - 46, 18, C.good);
  s += text(x + w - 128, y + h - 31, 'Backed up 08:12', { size: 12, fill: C.ink3 });
  return s;
}
