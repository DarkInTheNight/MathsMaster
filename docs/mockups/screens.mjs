// The six layout mockups. Each export returns a complete SVG document.
import {
  C, text, rect, circle, line, path, icon, sparkle, chip, badge, button, pdfThumb, noteThumb, device, sidebar, tw, STYLE, DEFS,
} from './lib.mjs';

const W = 1366, H = 1024; // iPad Air 13" landscape, points

// ---------------------------------------------------------------- 01 Library
export function library() {
  let s = sidebar({ selected: 'Linear Algebra' });
  const X = 330;
  // header band
  s += rect(318, 32, 1036, 160, { rx: 22, fill: C.indigo, opacity: 0.09 });
  s += rect(318, 32, 6, 160, { rx: 3, fill: C.indigo });
  s += text(X + 16, 74, 'MICHAELMAS 2026 · 24 LECTURES', { size: 12, weight: 700, fill: C.indigo, ls: 0.8 });
  s += text(X + 16, 114, 'Linear Algebra', { size: 36, weight: 750 });
  s += text(X + 16, 146, 'Lecture 16 of 24  ·  Sheet 3 supervision Thu 26 Nov  ·  23 cards due', { size: 15, fill: C.ink2 });
  for (let i = 0; i < 24; i++) s += rect(X + 16 + i * 13, 162, 10, 5, { rx: 2.5, fill: i < 16 ? C.indigo : '#D5D3E8' });
  s += button(1094, 92, 196, 42, 'Review this course', { iconName: 'cards', size: 15 });
  s += rect(1302, 92, 42, 42, { rx: 21, fill: '#fff', stroke: C.line });
  s += icon('plus', 1311, 101, 24, C.accent, 2);

  // + menu (open) to show import options
  // (kept closed in this mockup for clarity)

  const shelf = (y, title, right = 'See all') =>
    text(X + 16, y, title, { size: 20, weight: 700 }) + text(1006, y, right, { size: 15, fill: C.accent, anchor: 'end' });

  // Lecture notes
  s += shelf(226, 'Lecture notes');
  s += pdfThumb(X + 16, 242, 120, 160, { seed: 3 });
  s += text(X + 16, 424, 'LA notes 2026', { size: 14, weight: 600 });
  s += text(X + 16, 442, '112 pp · ink to p. 84', { size: 12, fill: C.ink2 });
  s += pdfThumb(X + 156, 242, 120, 160, { seed: 5, ink: false, highlight: false });
  s += text(X + 156, 424, 'Handout: Jordan form', { size: 14, weight: 600 });
  s += text(X + 156, 442, '6 pp', { size: 12, fill: C.ink2 });
  // drop hint
  s += rect(X + 296, 242, 360, 160, { rx: 14, fill: 'none', stroke: '#CFCBC2', dash: '6 6', sw: 1.5 });
  s += icon('doc', X + 460, 290, 30, C.ink3);
  s += text(X + 476, 346, 'Drop PDFs here, or use + › Import PDF…', { size: 14, fill: C.ink3, anchor: 'middle' });
  s += text(X + 476, 366, 'kind is guessed from the file name', { size: 12, fill: C.ink3, anchor: 'middle' });

  // Example sheets
  s += shelf(484, 'Example sheets');
  const sheets = [
    ['Sheet 1', 'Done · 14 Oct', ['✓ Done', C.good]],
    ['Sheet 2', 'Done · 4 Nov', ['✓ Done', C.good]],
    ['Sheet 3', 'Supervision Thu 26 Nov', ['● 9 of 12', C.hard], true],
    ['Sheet 4', 'Out 27 Nov', ['Not started', C.ink3]],
  ];
  sheets.forEach(([t, m, [st, col], stuck], i) => {
    const x = X + 16 + i * 160;
    s += pdfThumb(x, 500, 120, 160, { seed: 10 + i, title: true, ink: i < 3, highlight: i === 2 });
    const c = chip(x + 6, 630, st, { fill: '#fff', color: col, size: 11, h: 20, stroke: C.line });
    s += c.svg;
    s += text(x, 682, t, { size: 14, weight: 600 });
    s += text(x, 700, m, { size: 12, fill: C.ink2 });
    if (stuck) s += chip(x + 52, 668, '⚑ 2 stuck', { fill: '#FCE8E8', color: C.again, size: 11, h: 19 }).svg;
  });

  // Notebooks
  s += shelf(742, 'Notebooks');
  const nbs = [['Lecture 16 working', 'Edited 2 h ago'], ['Revision: duality', '12 pages'], ['Supervision 3 notes', 'Edited Tue']];
  nbs.forEach(([t, m], i) => {
    const x = X + 16 + i * 160;
    s += noteThumb(x, 758, 120, 160, { seed: i + 2, squares: i === 2 });
    s += text(x, 940, t, { size: 14, weight: 600 });
    s += text(x, 958, m, { size: 12, fill: C.ink2 });
  });
  s += rect(X + 496, 758, 120, 160, { rx: 6, fill: 'none', stroke: '#CFCBC2', dash: '6 6', sw: 1.5 });
  s += icon('plus', X + 542, 822, 28, C.ink3, 2);
  s += text(X + 556, 940, 'New notebook', { size: 14, weight: 600, fill: C.ink2, anchor: 'middle' });
  s += text(X + 16, 1000, '#eigenvalues   #jordan-form   #duality   #bilinear-forms', { size: 13, fill: C.accent });

  // Right column: Cards panel
  const RX = 1030, RW = 316;
  s += rect(RX, 210, RW, 300, { rx: 18, fill: '#fff', filter: 'sh' });
  s += icon('cards', RX + 20, 228, 22, C.indigo);
  s += text(RX + 50, 246, 'Cards', { size: 20, weight: 700 });
  s += text(RX + RW - 20, 246, 'Stats ›', { size: 14, fill: C.accent, anchor: 'end' });
  s += text(RX + 20, 318, '23', { size: 60, weight: 750, cls: 'rnd', fill: C.ink });
  s += text(RX + 110, 296, 'due today', { size: 16, weight: 600 });
  s += text(RX + 110, 318, '+ 5 new · about 6 min', { size: 13, fill: C.ink2 });
  // maturity bar
  const seg = [[0.12, '#C8CCF9'], [0.18, '#9AA3F5'], [0.30, C.indigo], [0.40, '#2E3A9E']];
  let bx = RX + 20;
  for (const [f, c] of seg) { const ww = (RW - 40) * f; s += rect(bx, 342, ww - 2, 10, { rx: 3, fill: c }); bx += ww; }
  s += text(RX + 20, 374, '186 cards  ·  new 22 · learning 34 · young 56 · mature 74', { size: 11.5, fill: C.ink2 });
  s += text(RX + 20, 398, 'Retention 89 % (30 d)  ·  Exam readiness 71 %', { size: 12.5, fill: C.ink2 });
  s += button(RX + 20, 420, 130, 40, 'Review', { size: 15 });
  s += button(RX + 160, 420, 66, 40, 'Browse', { fill: C.surface2, color: C.ink, size: 14 });
  s += button(RX + 234, 420, 62, 40, 'Add', { fill: C.surface2, color: C.ink, size: 14 });
  s += text(RX + 20, 488, 'Inbox: 12 AI cards from L13–16 waiting', { size: 12.5, fill: C.accent });
  s += sparkle(RX + RW - 36, 474, 16);

  // Outline
  s += rect(RX, 530, RW, 470, { rx: 18, fill: '#fff', filter: 'sh' });
  s += icon('bookmark', RX + 20, 548, 20, C.indigo);
  s += text(RX + 50, 566, 'Outline', { size: 20, weight: 700 });
  s += text(RX + RW - 20, 566, 'from bookmarks', { size: 12, fill: C.ink3, anchor: 'end' });
  const lec = [
    ['L9', 'Bilinear forms', 'p. 38'], ['L10', 'Sylvester’s law', 'p. 42'], ['L11', 'Determinants', 'p. 46'],
    ['L12', 'Eigenvalues', 'p. 51'], ['L13', 'Diagonalisation', 'p. 55'], ['L14', 'Minimal polynomial', 'p. 58'],
    ['L15', 'Cayley–Hamilton', 'p. 61'], ['L16', 'Jordan normal form', 'p. 66'], ['L17', '—', ''],
  ];
  lec.forEach(([n, t, p], i) => {
    const y = 600 + i * 42;
    const cur = n === 'L16';
    if (cur) s += rect(RX + 10, y - 26, RW - 20, 38, { rx: 9, fill: '#EEF0FE' });
    s += text(RX + 22, y, n, { size: 13, weight: 700, fill: n === 'L17' ? C.ink3 : C.indigo, cls: 'rnd' });
    s += text(RX + 62, y, t, { size: 15, fill: n === 'L17' ? C.ink3 : C.ink, weight: cur ? 600 : 400 });
    s += text(RX + RW - 22, y, p, { size: 13, fill: C.ink3, anchor: 'end' });
    if (i < lec.length - 1) s += line(RX + 22, y + 14, RX + RW - 20, y + 14, '#F0EDE7');
  });
  s += text(RX + 22, 986, 'Tap to jump into the notes at that page', { size: 12, fill: C.ink3 });

  return device(W, H, s, { title: 'MathsMaster: main split view (sidebar + course page), iPad Air 13-inch landscape' });
}

// ---------------------------------------------------------------- 02 Today
export function today() {
  let s = sidebar({ selected: 'Today' });
  const X = 346;
  s += text(X, 92, 'Today', { size: 36, weight: 750 });
  s += text(X, 122, 'Sunday 22 November  ·  Michaelmas, week 7', { size: 16, fill: C.ink2 });
  s += icon('search', 1304, 66, 24, C.accent);

  // Review hero
  s += rect(X - 8, 146, 640, 250, { rx: 24, fill: '#fff', filter: 'sh' });
  s += text(X + 20, 186, 'REVIEW', { size: 12, weight: 700, fill: C.accent, ls: 1 });
  s += text(X + 18, 262, '64', { size: 84, weight: 750, cls: 'rnd' });
  s += text(X + 142, 226, 'cards due', { size: 22, weight: 650 });
  s += text(X + 142, 254, 'about 15 min  ·  + 10 new', { size: 16, fill: C.ink2 });
  const parts = [['LA', 23, C.indigo], ['A&T', 18, C.teal], ['Methods', 11, C.amber], ['QM', 8, C.coral], ['MC', 4, C.violet]];
  let bx = X + 20; const BW = 584;
  for (const [n, k, c] of parts) { const w = BW * k / 64; s += rect(bx, 290, w - 3, 12, { rx: 4, fill: c }); bx += w; }
  bx = X + 20;
  for (const [n, k, c] of parts) { s += circle(bx + 5, 326, 5, c); s += text(bx + 15, 331, `${n} ${k}`, { size: 13, fill: C.ink2 }); bx += tw(`${n} ${k}`, 13) + 34; }
  s += button(X + 404, 196, 210, 56, 'Start review', { size: 18, iconName: 'cards' });
  s += text(X + 20, 372, 'Interleaved across courses · new cards only for this term’s courses', { size: 12.5, fill: C.ink3 });

  // Streak / heatmap card
  const SX = X + 652;
  s += rect(SX, 146, 360, 250, { rx: 24, fill: '#fff', filter: 'sh' });
  s += icon('flame', SX + 20, 166, 22, C.orange);
  s += text(SX + 50, 184, '23-day streak', { size: 17, weight: 700 });
  s += text(SX + 340, 184, 'Stats ›', { size: 14, fill: C.accent, anchor: 'end' });
  for (let c = 0; c < 12; c++) for (let r = 0; r < 7; r++) {
    const v = (c * 7 + r * 3 + (c > 8 ? 5 : 0)) % 9;
    const alpha = c === 11 && r > 0 ? 0 : [0.12, 0.25, 0.4, 0.55, 0.7, 0.85, 1, 0.55, 0.4][v];
    s += rect(SX + 22 + c * 26, 204 + r * 19, 21, 15, { rx: 3.5, fill: alpha === 0 ? C.surface2 : C.accent, opacity: alpha === 0 ? 1 : alpha });
  }
  s += text(SX + 22, 360, 'Retention 91 % (30 d)', { size: 14, weight: 600 });
  s += text(SX + 22, 380, 'Exam readiness, 1 June: 68 %', { size: 13, fill: C.ink2 });

  // Up next
  s += text(X, 444, 'Up next', { size: 22, weight: 700 });
  s += rect(X - 8, 460, 640, 248, { rx: 20, fill: '#fff', filter: 'sh' });
  const up = [
    [C.indigo, 'Linear Algebra · Sheet 3 supervision', 'Thu 26 Nov, 14:00  ·  ⚑ 2 stuck  ·  1 not started', 'Open Q4'],
    [C.teal, 'Analysis & Topology · Sheet 3 hand-in', 'Tomorrow  ·  6 of 12 questions done', 'Open Q7'],
    [C.coral, 'Quantum Mechanics · Sheet 2 supervision', 'Fri 27 Nov  ·  all questions done ✓', 'Export'],
  ];
  up.forEach(([c, t, m, a], i) => {
    const y = 470 + i * 80;
    s += rect(X + 12, y + 18, 5, 44, { rx: 2.5, fill: c });
    s += text(X + 32, y + 36, t, { size: 16, weight: 600 });
    s += text(X + 32, y + 58, m, { size: 13.5, fill: C.ink2 });
    s += button(X + 510, y + 22, 100, 36, a, { fill: C.surface2, color: C.accent, size: 14 });
    if (i < 2) s += line(X + 32, y + 78, X + 610, y + 78, '#F0EDE7');
  });

  // Inbox card
  s += text(SX, 444, 'Inbox', { size: 22, weight: 700 });
  s += rect(SX, 460, 360, 248, { rx: 20, fill: C.accentSoft });
  s += sparkle(SX + 22, 482, 22, C.accent);
  s += text(SX + 54, 500, '12 new cards ready', { size: 18, weight: 700, fill: '#0F4D46' });
  s += text(SX + 22, 530, 'From “Linear Algebra L13–16”', { size: 14, fill: '#2B5F59' });
  s += text(SX + 22, 550, 'Made by Claude on your VPS · 2 h ago', { size: 13, fill: '#2B5F59' });
  // mini card stack
  s += rect(SX + 30, 572, 300, 64, { rx: 12, fill: '#fff', opacity: 0.6 });
  s += rect(SX + 22, 580, 316, 64, { rx: 12, fill: '#fff', filter: 'sh' });
  s += text(SX + 38, 606, 'Define the minimal polynomial m', { size: 15, cls: 'serif' });
  s += text(SX + 38, 628, 'Definition · L14', { size: 12, fill: C.ink3 });
  s += button(SX + 22, 656, 150, 38, 'Triage', { size: 15 });
  s += text(SX + 190, 680, '+ 3 files to sort', { size: 13, fill: '#2B5F59' });

  // Continue
  s += text(X, 756, 'Continue', { size: 22, weight: 700 });
  const cont = [
    ['Methods notes', 'p. 47 · 25 min ago', 'pdf', C.amber],
    ['A&T Sheet 3 answers', 'Q7 · yesterday', 'note', C.teal],
    ['LA notes 2026', 'p. 84 · yesterday', 'pdf', C.indigo],
    ['Lecture 16 working', 'p. 3 · Fri', 'note', C.indigo],
    ['QM notes', 'p. 112 · Fri', 'pdf', C.coral],
  ];
  cont.forEach(([t, m, k, c], i) => {
    const x = X + i * 200;
    s += k === 'pdf' ? pdfThumb(x, 776, 176, 150, { seed: i + 20, accent: c, title: false }) : noteThumb(x, 776, 176, 150, { seed: i + 4, accent: c });
    s += text(x, 950, t, { size: 14, weight: 600 });
    s += text(x, 968, m, { size: 12, fill: C.ink2 });
  });
  return device(W, H, s, { title: 'MathsMaster: Today view' });
}

// ---------------------------------------------------------------- 03 Editor (example-sheet mode)
export function editor() {
  let s = '';
  s += rect(0, 0, W, H, { fill: '#E9E6E0' });
  // reference pane
  const RW = 520;
  s += rect(0, 0, RW, H, { fill: '#DEDAD3' });
  // question PDF page
  const px = 28, py = 108, pw = RW - 56, ph = 860;
  s += rect(px, py, pw, ph, { fill: '#fff', filter: 'sh' });
  const st = (x, y, str, o = {}) => text(x, y, str, { cls: 'serif', size: 15.5, ...o });
  s += st(px + pw / 2, py + 44, 'Part IB  Linear Algebra', { anchor: 'middle', size: 17, weight: 700 });
  s += st(px + pw / 2, py + 68, 'Example Sheet 3', { anchor: 'middle', size: 15, italic: true });
  let y = py + 112;
  const para = (num, lines, hl = false) => {
    let r = '';
    if (hl) r += rect(px + 18, y - 22, pw - 36, lines.length * 24 + 18, { rx: 6, fill: C.accentSoft, opacity: 0.8 }) + rect(px + 18, y - 22, 4, lines.length * 24 + 18, { rx: 2, fill: C.accent });
    r += st(px + 30, y, `${num}.`, { weight: 700 });
    lines.forEach((l, i) => { r += text(px + 58, y + i * 24, l, { cls: 'serif', size: 15.5, raw: true }); });
    y += lines.length * 24 + 26;
    return r;
  };
  s += para(3, [
    'Find the characteristic and minimal polynomials of',
    '<tspan font-style="italic">A</tspan> = ( 2 1 0 ; 0 2 0 ; 0 0 3 ).  Is <tspan font-style="italic">A</tspan> diagonalisable?',
  ]);
  s += para(4, [
    'Let <tspan font-style="italic">A</tspan> be an <tspan font-style="italic">n</tspan> × <tspan font-style="italic">n</tspan> complex matrix. Show that <tspan font-style="italic">A</tspan> is',
    'diagonalisable if and only if its minimal polynomial',
    '<tspan font-style="italic">m</tspan><tspan font-size="11" dy="4" font-style="italic">A</tspan><tspan dy="-4">(</tspan><tspan font-style="italic">t</tspan>) has no repeated roots. Deduce that if',
    '<tspan font-style="italic">A</tspan><tspan font-size="11" dy="-7" font-style="italic">k</tspan><tspan dy="7"> = </tspan><tspan font-style="italic">I</tspan> for some <tspan font-style="italic">k</tspan> ≥ 1 then <tspan font-style="italic">A</tspan> is diagonalisable.',
  ], true);
  s += para(5, [
    'Let <tspan font-style="italic">α</tspan> be an endomorphism of a finite-dimensional',
    'complex vector space <tspan font-style="italic">V</tspan> with <tspan font-style="italic">α</tspan><tspan font-size="11" dy="-7">3</tspan><tspan dy="7"> = </tspan><tspan font-style="italic">α</tspan>. What are the',
    'possible Jordan normal forms of <tspan font-style="italic">α</tspan>?',
  ]);
  s += para(6, [
    'Show that two 3 × 3 complex matrices are similar if',
    'and only if they have the same characteristic and',
    'minimal polynomials. Is this true for 4 × 4?',
  ]);
  s += para(7, ['Let <tspan font-style="italic">V</tspan> be the space of polynomials of degree ≤ <tspan font-style="italic">n</tspan> …']);
  // highlighter ink on Q4 phrase
  s += rect(px + 56, py + 236, 236, 16, { rx: 3, fill: C.hl, opacity: 0.5 });
  s += text(px + 40, py + ph - 24, '1', { cls: 'serif', size: 13, fill: C.ink3 });
  // divider handle
  s += rect(RW - 1, 0, 2, H, { fill: '#CFCAC1' });
  s += rect(RW - 4, H / 2 - 30, 8, 60, { rx: 4, fill: '#B9B4AA' });

  // answer side
  const AX = RW + 1, AW = W - AX;
  // question navigator chips
  const qs = [['Q1', '✓', C.good], ['Q2', '✓', C.good], ['Q3', '✓', C.good], ['Q4', '●', C.hard], ['Q5', '⚑', C.again], ['Q6', '○', C.ink3], ['Q7', '○', C.ink3], ['Q8', '⚑', C.again]];
  let qx = AX + 32;
  qs.forEach(([q, m, c]) => {
    const cur = q === 'Q4';
    s += rect(qx, 100, 64, 30, { rx: 15, fill: cur ? C.ink : '#fff', stroke: cur ? null : C.line });
    s += text(qx + 14, 120, q, { size: 13, weight: 700, fill: cur ? '#fff' : C.ink });
    s += text(qx + 44, 120, m, { size: 13, weight: 700, fill: cur ? '#FFD27A' : c });
    qx += 72;
  });
  // A4 answer page
  const ax = AX + 44, ay = 146, aw = 640, ah = 905;
  s += rect(ax, ay, aw, ah, { fill: '#fff', filter: 'sh' });
  s += rect(ax, ay + 70, aw - 110, ah - 70, { fill: 'url(#squares)' });
  s += line(ax + aw - 110, ay + 70, ax + aw - 110, ay + ah, '#F2C9C9', 1);
  // template header
  s += text(ax + 24, ay + 30, 'COURSE', { size: 9, weight: 700, fill: C.ink3, ls: 1 });
  s += text(ax + 24, ay + 54, 'Linear Algebra', { size: 15, cls: 'hand', fill: C.penBlack });
  s += text(ax + 260, ay + 30, 'SHEET', { size: 9, weight: 700, fill: C.ink3, ls: 1 });
  s += text(ax + 260, ay + 54, '3', { size: 16, cls: 'hand', fill: C.penBlack });
  s += text(ax + 360, ay + 30, 'QUESTION', { size: 9, weight: 700, fill: C.ink3, ls: 1 });
  s += text(ax + 360, ay + 54, '4', { size: 16, cls: 'hand', fill: C.penBlack });
  s += line(ax + 16, ay + 68, ax + aw - 16, ay + 68, '#D6D2CA', 1);
  // handwriting
  const hw = (x, y, str, o = {}) => text(x, y, str, { cls: 'hand', size: 19, fill: C.penBlack, raw: true, ...o });
  let hy = ay + 112;
  const L = 34;
  s += hw(ax + 30, hy, '(⇒) Suppose A = PDP⁻¹, D = diag(λ₁, …, λₙ).'); hy += L;
  s += hw(ax + 30, hy, 'Let μ₁, …, μₖ be the distinct λᵢ and put'); hy += L;
  s += hw(ax + 60, hy, 'p(t) = ∏ (t − μⱼ).  Then p(D) = 0,'); hy += L;
  s += hw(ax + 30, hy, 'so p(A) = P p(D) P⁻¹ = 0  ⇒  m_A | p,'); hy += L;
  s += hw(ax + 30, hy, 'hence m_A has no repeated roots.'); hy += L + 14;
  s += hw(ax + 30, hy, '(⇐) If m_A(t) = ∏ (t − μⱼ), μⱼ distinct, then'); hy += L;
  s += hw(ax + 30, hy, 'by the primary decomposition theorem'); hy += L + 16;
  // boxed result + lasso
  s += hw(ax + 120, hy, 'V = ⊕ⱼ ker(A − μⱼ I)', { size: 24 });
  s += path(`M${ax + 104} ${hy - 34} h300 v48 h-300 z`, { stroke: C.penRed, sw: 2 });
  s += path(`M${ax + 86} ${hy - 50} C ${ax + 200} ${hy - 70}, ${ax + 400} ${hy - 66}, ${ax + 428} ${hy - 30} S ${ax + 420} ${hy + 30}, ${ax + 250} ${hy + 30} S ${ax + 70} ${hy + 20}, ${ax + 86} ${hy - 50}`, { stroke: C.accent, sw: 1.6, dash: '5 4' });
  const lassoY = hy;
  hy += L + 18;
  s += hw(ax + 30, hy, 'so V has a basis of eigenvectors ⇒ A diag’ble. ✓', { fill: C.penBlack }); hy += L + 14;
  s += hw(ax + 30, hy, 'Deduce: Aᵏ = I ⇒ m_A | tᵏ − 1, which has k', { fill: C.penBlue }); hy += L;
  s += hw(ax + 30, hy, 'distinct roots (k-th roots of unity) ⇒ …', { fill: C.penBlue }); hy += L;
  s += path(`M${ax + 30} ${hy + 4} q 40 -10 80 0 t 80 0`, { stroke: C.penBlue, sw: 1.6 });
  // margin note + card badge
  s += text(ax + aw - 96, ay + 150, 'used Thm', { cls: 'hand', size: 15, fill: C.penRed });
  s += text(ax + aw - 96, ay + 170, '4.12', { cls: 'hand', size: 15, fill: C.penRed });
  s += rect(ax + aw - 92, ay + 236, 66, 28, { rx: 14, fill: C.indigo });
  s += icon('cards', ax + aw - 84, ay + 241, 17, '#fff');
  s += text(ax + aw - 58, ay + 255, '2', { size: 14, weight: 700, fill: '#fff', cls: 'rnd' });
  s += text(ax + aw - 98, ay + 284, 'linked cards', { size: 10.5, fill: C.ink3 });

  // lasso action popover
  const mx = ax + 452, my = lassoY - 58;
  s += rect(mx, my, 226, 200, { rx: 16, fill: '#fff', filter: 'sh2' });
  const items = [['cardPlus', 'Make cards', C.ink], ['sparkle', 'Ask Claude about this', C.ink], ['sparkle', 'Transcribe', C.ink], ['share', 'Copy as image', C.ink]];
  items.forEach(([ic, t, c], i) => {
    const iy = my + 14 + i * 46;
    if (i === 0) s += rect(mx + 8, iy - 4, 210, 40, { rx: 10, fill: C.accentSoft });
    s += ic === 'sparkle' ? sparkle(mx + 20, iy + 6, 18, C.accent) : icon(ic, mx + 20, iy + 6, 20, C.accent);
    s += text(mx + 50, iy + 22, t, { size: 15, weight: i === 0 ? 650 : 450, fill: c });
  });
  s += path(`M${mx} ${my + 120} l-12 10 l12 10`, { stroke: '#fff', fill: '#fff', sw: 1 });

  // page indicator
  // mini page strip (right edge)
  for (let i = 0; i < 6; i++) {
    const tx = W - 64, ty = 150 + i * 62;
    s += rect(tx, ty, 40, 54, { rx: 3, fill: '#fff', stroke: i === 3 ? C.accent : C.line, sw: i === 3 ? 2 : 1 });
    s += text(tx + 20, ty + 32, `Q${i + 1}`, { size: 10, fill: C.ink3, anchor: 'middle' });
  }

  // top glass bar
  s += rect(12, 30, W - 24, 56, { rx: 28, fill: 'url(#glass)', stroke: '#FFFFFF', filter: 'sh' });
  s += icon('chevL', 26, 46, 24, C.accent, 2.2);
  s += text(52, 64, 'Linear Algebra', { size: 16, fill: C.accent, weight: 500 });
  s += text(W / 2 - 40, 55, 'Example Sheet 3: Answers', { size: 16, weight: 700, anchor: 'middle' });
  s += text(W / 2 - 40, 74, 'Q4 · page 7 of 12 · saved', { size: 12, fill: C.ink2, anchor: 'middle' });
  // status pill
  const sx0 = 806;
  s += rect(sx0, 40, 248, 36, { rx: 18, fill: C.surface2 });
  [['Not started', 0], ['Attempted', 1], ['Done', 2], ['⚑ Stuck', 3]].forEach(([t, i]) => {
    const w = [74, 70, 44, 60][i];
    const x = sx0 + 4 + [0, 74, 144, 188][i];
    if (i === 1) s += rect(x, 44, w, 28, { rx: 14, fill: '#fff', filter: 'sh' });
    s += text(x + w / 2, 63, t, { size: 11.5, weight: i === 1 ? 700 : 500, fill: i === 1 ? C.hard : C.ink2, anchor: 'middle' });
  });
  const tools = [['undo', 1070], ['redo', 1106], ['pane', 1150], ['bookmark', 1186], ['cardPlus', 1222], ['share', 1294], ['more', 1330]];
  tools.forEach(([n, x]) => {
    if (n === 'pane') s += rect(x - 6, 40, 36, 36, { rx: 10, fill: C.accentSoft });
    s += icon(n, x, 46, 24, C.accent);
  });
  s += sparkle(1260, 47, 22, C.accent);

  // bottom tool picker (PKToolPicker-style, docked)
  const tx0 = 640, ty0 = 952, tW = 560;
  s += rect(tx0, ty0, tW, 62, { rx: 22, fill: 'url(#glass)', stroke: '#fff', filter: 'sh2' });
  const pen = (x, col, sel) => {
    let r = `<path d="M${x} ${ty0 + 58} v-30 l7 -16 l7 16 v30 z" fill="#F7F6F3" stroke="#BDB8AE" stroke-width="1"/>`;
    r += `<path d="M${x + 3.5} ${ty0 + 20} l3.5 -8 l3.5 8 z" fill="${col}"/>`;
    r += rect(x, ty0 + 34, 14, 6, { fill: col });
    if (sel) r = r.replace(/v-30/g, 'v-38').replace(/l7 -16/, 'l7 -16');
    return r;
  };
  s += pen(tx0 + 24, C.penBlack) + pen(tx0 + 56, C.penBlue) + pen(tx0 + 88, C.penRed);
  s += `<path d="M${tx0 + 122} ${ty0 + 58} v-28 h16 v28 z" fill="#F7F6F3" stroke="#BDB8AE"/>` + rect(tx0 + 122, ty0 + 20, 16, 10, { fill: C.hl });
  s += `<path d="M${tx0 + 156} ${ty0 + 58} v-30 h16 v30 z" fill="#FBEFEF" stroke="#BDB8AE"/>`; // eraser
  // lasso (selected)
  s += rect(tx0 + 186, ty0 + 8, 40, 46, { rx: 10, fill: C.accentSoft });
  s += icon('lasso', tx0 + 194, ty0 + 18, 24, C.accent);
  s += `<g transform="translate(${tx0 + 236} ${ty0 + 44}) rotate(-35)">${rect(0, 0, 34, 11, { rx: 2, fill: '#F7F6F3', stroke: '#9C988F' })}${[5, 10, 15, 20, 25, 30].map((t, i) => line(t, 0, t, i % 2 ? 4 : 6, '#9C988F', 1)).join('')}</g>`;
  s += rect(tx0 + 276, ty0 + 14, 36, 34, { rx: 8, fill: '#EEF0FE' });
  s += icon('cardPlus', tx0 + 282, ty0 + 19, 24, C.indigo);
  s += line(tx0 + 328, ty0 + 14, tx0 + 328, ty0 + 48, C.line);
  [C.penBlack, C.penBlue, C.penRed, C.penGreen, C.hl].forEach((c, i) => {
    s += circle(tx0 + 352 + i * 34, ty0 + 31, 11, c, { stroke: i === 0 ? C.accent : '#fff', sw: i === 0 ? 3 : 2 });
  });
  s += icon('more', tx0 + 520, ty0 + 20, 22, C.ink2);
  s += text(tx0 + 300, ty0 + 76, '', {});
  // callouts
  s += text(RW / 2, 996, 'Reference pane: the question PDF (read & annotate) · drag the divider to resize', { size: 12, fill: C.ink2, anchor: 'middle' });
  return device(W, H, s, { title: 'MathsMaster: editor in example-sheet mode' });
}

// ---------------------------------------------------------------- 04 Review (compare layout after reveal)
export function review() {
  let s = rect(0, 0, W, H, { fill: '#F1EFEA' });
  // top bar
  s += rect(12, 30, W - 24, 56, { rx: 28, fill: 'url(#glass)', stroke: '#fff', filter: 'sh' });
  s += icon('close', 28, 46, 24, C.accent, 2.2);
  s += text(58, 64, 'End', { size: 16, fill: C.accent });
  s += text(170, 64, 'All courses', { size: 16, weight: 700 });
  s += rect(290, 54, 360, 8, { rx: 4, fill: C.surface2 });
  s += rect(290, 54, 360 * 18 / 64, 8, { rx: 4, fill: C.accent });
  s += text(664, 64, '18 / 64', { size: 13, weight: 600, fill: C.ink2, cls: 'rnd' });
  s += text(740, 64, 'New 3', { size: 13, weight: 700, fill: C.easy });
  s += text(800, 64, 'Learning 5', { size: 13, weight: 700, fill: C.hard });
  s += text(886, 64, 'Review 38', { size: 13, weight: 700, fill: C.good });
  s += text(1110, 64, 'Compare', { size: 13, weight: 650, fill: C.accent });
  s += icon('pane', 1172, 46, 24, C.accent);
  s += icon('undo', 1270, 46, 24, C.accent);
  s += icon('more', 1316, 46, 24, C.accent);

  // ---- left: front + your attempt
  const L = { x: 16, y: 100, w: 662, h: 910 };
  s += rect(L.x, L.y, L.w, L.h, { rx: 24, fill: '#fff', filter: 'sh2' });
  s += chip(L.x + 24, L.y + 22, 'Linear Algebra · Theorem · L15', { dot: C.indigo, fill: '#EEF0FE', color: '#3A47B8', size: 12.5, h: 26 }).svg;
  s += text(L.x + L.w - 24, L.y + 40, 'reviewed 4× · last: Good', { size: 12, fill: C.ink3, anchor: 'end' });
  s += text(L.x + 28, L.y + 92, 'Statement and Proof of the', { cls: 'serif', size: 26 });
  s += text(L.x + 28, L.y + 126, 'Cayley–Hamilton Theorem', { cls: 'serif', size: 26 });
  const ay = L.y + 152;
  s += line(L.x + 20, ay, L.x + L.w - 20, ay, C.line);
  s += rect(L.x + 2, ay + 2, L.w - 4, L.h - 160, { fill: 'url(#dots)', opacity: 0.55 });
  s += text(L.x + 28, ay + 28, 'YOUR ATTEMPT', { size: 10.5, weight: 700, fill: C.ink3, ls: 1 });
  s += text(L.x + L.w - 28, ay + 28, 'Pencil writes · finger scrolls · space grows as you write', { size: 11.5, fill: C.ink3, anchor: 'end' });
  const hw = (x, y, str, o = {}) => text(x, y, str, { cls: 'hand', size: 20, fill: C.penBlue, raw: true, ...o });
  let y = ay + 76;
  const step = 42;
  s += hw(L.x + 36, y, 'Thm. V f.d. over F, α ∈ End(V), χ_α(t) = det(tι − α)'); y += step;
  s += hw(L.x + 150, y, '⇒  χ_α(α) = 0.'); y += step + 8;
  s += hw(L.x + 36, y, 'Pf (F = ℂ). Pick a basis v₁, …, vₙ with [α] upper △,'); y += step;
  s += hw(L.x + 66, y, 'diagonal λ₁, …, λₙ.  Put Uᵢ = ⟨v₁, …, vᵢ⟩, U₀ = 0.'); y += step;
  s += hw(L.x + 36, y, 'Claim: (α − λᵢι) Uᵢ ⊆ Uᵢ₋₁');
  s += hw(L.x + 380, y, 'why??', { fill: C.penRed });
  s += path(`M${L.x + 372} ${y - 22} q 34 -14 66 2 q 10 22 -10 28 q -40 8 -58 -6 z`, { stroke: C.penRed, sw: 1.4 });
  y += step;
  s += hw(L.x + 36, y, 'Then (α−λ₁ι)(α−λ₂ι) ⋯ (α−λₙι) V'); y += step;
  s += hw(L.x + 66, y, '⊆ (α−λ₁ι) ⋯ (α−λₙ₋₁ι) Uₙ₋₁ ⊆ ⋯ ⊆ U₀ = 0.'); y += step;
  s += hw(L.x + 36, y, 'χ_α(t) = ∏ (t − λᵢ)   ⇒   χ_α(α) = 0.   ∎');
  s += path(`M${L.x + 30} ${y + 10} h 420`, { stroke: C.penBlue, sw: 1.4 });
  y += step + 14;
  s += hw(L.x + 36, y, 'General F: pass to a splitting field?', { fill: C.penBlack }); y += step;
  // rough sketch of flag
  s += path(`M${L.x + 60} ${y + 10} h 60 M${L.x + 130} ${y + 10} h 60 M${L.x + 200} ${y + 10} h 60`, { stroke: C.penBlack, sw: 1.4 });
  s += hw(L.x + 60, y + 4, 'U₁   ⊂   U₂   ⊂   U₃  …', { size: 17, fill: C.penBlack });
  // more space hint
  s += line(L.x + 28, L.y + L.h - 112, L.x + L.w - 28, L.y + L.h - 112, '#CFCAC1', 1.2, { dash: '6 6' });
  s += text(L.x + L.w / 2, L.y + L.h - 90, 'Another screen of space appears when you write near the bottom', { size: 12, fill: C.ink3, anchor: 'middle' });
  s += rect(L.x + L.w - 10, ay + 40, 4, 260, { rx: 2, fill: '#D3CEC5' });

  // ---- right: the answer
  const R = { x: 690, y: 100, w: 660, h: 910 };
  s += rect(R.x, R.y, R.w, R.h, { rx: 24, fill: '#fff', filter: 'sh2' });
  s += text(R.x + 28, R.y + 38, 'ANSWER', { size: 10.5, weight: 700, fill: C.good, ls: 1 });
  let cx = R.x + 100;
  for (const [t, on] of [['Motivation'], ['Statement'], ['Proof', true], ['Arbitrary F'], ['Intuition']]) {
    const c = chip(cx, R.y + 22, t, { fill: on ? C.ink : C.surface2, color: on ? '#fff' : C.ink2, size: 12, h: 26 });
    s += c.svg; cx += c.w + 6;
  }
  // actions
  s += rect(R.x + 24, R.y + 64, 128, 38, { rx: 19, fill: C.accent });
  s += sparkle(R.x + 38, R.y + 74, 18, '#fff');
  s += text(R.x + 62, R.y + 88, 'Discuss', { size: 15, weight: 650, fill: '#fff' });
  s += rect(R.x + 162, R.y + 64, 190, 38, { rx: 19, fill: '#fff', stroke: C.line });
  s += sparkle(R.x + 176, R.y + 74, 18, C.accent);
  s += text(R.x + 200, R.y + 88, 'Check my attempt', { size: 15, weight: 600, fill: C.accent });
  s += rect(R.x + 362, R.y + 64, 104, 38, { rx: 19, fill: '#fff', stroke: C.line });
  s += icon('source', R.x + 374, R.y + 73, 20, C.accent);
  s += text(R.x + 398, R.y + 88, 'Source', { size: 15, fill: C.accent });
  s += rect(R.x + 476, R.y + 64, 84, 38, { rx: 19, fill: '#fff', stroke: C.line });
  s += icon('edit', R.x + 488, R.y + 73, 20, C.accent);
  s += text(R.x + 512, R.y + 88, 'Edit', { size: 15, fill: C.accent });
  s += icon('flag', R.x + R.w - 50, R.y + 72, 22, C.ink3);
  s += line(R.x + 20, R.y + 120, R.x + R.w - 20, R.y + 120, C.line);

  const it = (v) => `<tspan font-style="italic">${v}</tspan>`;
  const sb = (b, v) => `${it(b)}<tspan font-size="12" dy="4" font-style="italic">${v}</tspan><tspan dy="-4">&#8202;</tspan>`;
  const P = (y, str, o = {}) => text(R.x + 30, y, str, { cls: 'serif', size: 16.5, raw: true, ...o });
  const B = (y, str) => text(R.x + 30, y, str, { cls: 'serif', size: 16.5, weight: 700 });
  const D = (y, str) => text(R.x + R.w / 2, y, str, { cls: 'serif', size: 18, raw: true, anchor: 'middle' });
  let ry = R.y + 152;
  const lh = 24;
  s += B(ry, '1. Motivation:'); ry += lh;
  s += P(ry, `Since dim End(${it('V')}) = ${it('n')}², the maps ${it('ι')}, ${it('α')}, …, ${it('α')}<tspan font-size="11" dy="-7">${'n²'}</tspan><tspan dy="7"> are linearly dependent,</tspan>`); ry += lh;
  s += P(ry, `so some polynomial kills ${it('α')}. Cayley–Hamilton names one of degree ${it('n')}.`); ry += lh + 14;
  s += B(ry, '2. Statement:'); ry += lh;
  s += P(ry, `Let ${it('V')} be an ${it('n')}-dimensional vector space over a field ${it('F')}, and ${it('α')} ∈ End(${it('V')}).`); ry += lh + 12;
  s += D(ry, `${sb('χ', 'α')}(${it('α')}) = 0,   where   ${sb('χ', 'α')}(${it('t')}) = det(${it('t')}${it('ι')} − ${it('α')}).`); ry += lh + 18;
  // proof section (highlighted as current)
  s += rect(R.x + 16, ry - 22, R.w - 32, 266, { rx: 12, fill: '#F6F8FF' });
  s += B(ry, '3. Proof (F = ℂ):'); ry += lh;
  s += P(ry, `choose a basis ${sb('v', '1')}, …, ${sb('v', 'n')} in which ${it('α')} is upper triangular with`); ry += lh;
  s += P(ry, `diagonal ${sb('λ', '1')}, …, ${sb('λ', 'n')} (possible because ${sb('χ', 'α')} splits over ℂ), and put`); ry += lh;
  s += P(ry, `${sb('U', 'i')} = ⟨${sb('v', '1')}, …, ${sb('v', 'i')}⟩. Upper-triangularity says`); ry += lh + 12;
  s += D(ry, `${it('α')}${sb('v', 'i')} = ${sb('λ', 'i')}${sb('v', 'i')} + (terms in ${sb('v', '1')}, …, ${sb('v', 'i−1')}),`); ry += lh + 8;
  s += P(ry, `so (${it('α')} − ${sb('λ', 'i')}${it('ι')})${sb('U', 'i')} ⊆ ${sb('U', 'i−1')}. Applying the factors for ${it('i')} = ${it('n')}, …, 1`); ry += lh;
  s += P(ry, 'in turn drops one level each time:'); ry += lh + 12;
  s += D(ry, `${sb('χ', 'α')}(${it('α')}) ${it('V')} = (${it('α')} − ${sb('λ', '1')}${it('ι')}) ⋯ (${it('α')} − ${sb('λ', 'n')}${it('ι')}) ${it('V')} ⊆ ⋯ ⊆ ${sb('U', '0')} = 0.   ∎`); ry += lh + 30;
  s += B(ry, '4. Arbitrary field F:'); ry += lh;
  s += P(ry, `run the same argument over a field extension in which ${sb('χ', 'α')} splits;`); ry += lh;
  s += P(ry, `${sb('χ', 'α')}(${it('α')}) = 0 is a statement about entries in ${it('F')}, so it holds over ${it('F')}.`); ry += lh + 14;
  s += B(ry, 'Intuition:'); ry += lh;
  s += P(ry, `each factor (${it('α')} − ${sb('λ', 'i')}${it('ι')}) peels one layer off the flag ${sb('U', '1')} ⊂ ⋯ ⊂ ${sb('U', 'n')}.`);
  s += rect(R.x + R.w - 10, R.y + 140, 4, 300, { rx: 2, fill: '#D3CEC5' });

  // floating grade bar (spans both panes)
  const gx0 = 343, gy = 926, gw = 680;
  s += rect(gx0, gy, gw, 78, { rx: 26, fill: 'url(#glass)', stroke: '#fff', filter: 'sh2' });
  const grades = [['Again', '< 10 m', C.again, 196, '1'], ['Hard', '2 d', C.hard, 140, '2'], ['Good', '6 d', C.good, 212, '3'], ['Easy', '14 d', C.easy, 120, '4']];
  let gx = gx0 + 8;
  grades.forEach(([g, iv, col, w, k]) => {
    const dom = g === 'Again' || g === 'Good';
    s += rect(gx, gy + 9, w - 8, 60, { rx: 18, fill: dom ? col : '#fff', stroke: dom ? null : C.line });
    s += text(gx + (w - 8) / 2, gy + 36, g, { size: 17, weight: 700, fill: dom ? '#fff' : col, anchor: 'middle' });
    s += text(gx + (w - 8) / 2, gy + 56, iv, { size: 12.5, weight: 600, fill: dom ? 'rgba(255,255,255,0.9)' : C.ink2, anchor: 'middle', cls: 'rnd' });
    s += text(gx + w - 20, gy + 24, k, { size: 10, weight: 700, fill: dom ? 'rgba(255,255,255,0.7)' : C.ink3, anchor: 'end' });
    gx += w;
  });
  return device(W, H, s, { title: 'MathsMaster: card review, compare layout after reveal' });
}

// ---------------------------------------------------------------- 05 Inbox + card thread
export function cards() {
  let s = '';
  s += icon('sidebar', 30, 44, 24, C.accent);
  s += text(30, 106, 'Inbox', { size: 34, weight: 750 });
  s += sparkle(138, 82, 20, C.accent);
  s += text(170, 104, 'Linear Algebra · lectures 13–16 · Claude Opus 5.5 on your VPS · 2 h ago', { size: 15, fill: C.ink2 });
  let rx0 = 30;
  for (const [t, o] of [
    ['⚠ 2 possible errors in the notes', { fill: '#FFF2DC', color: '#9A5B00' }],
    ['? 1 unclear handwriting', { fill: '#FFF2DC', color: '#9A5B00' }],
    ['+ 14 new cards', { fill: C.accentSoft, color: C.accent }],
    ['✎ 4 changes to your cards', { fill: '#EEF0FE', color: '#3A47B8' }],
    ['Read the full report ›', { fill: '#fff', color: C.accent, stroke: C.line }],
  ]) { const c = chip(rx0, 124, t, { size: 12.5, h: 28, pad: 12, ...o }); s += c.svg; rx0 += c.w + 8; }
  s += button(1150, 120, 196, 36, 'Accept all remaining', { fill: C.surface2, color: C.accent, size: 14 });

  // list
  const LX = 16, LW = 356;
  s += rect(LX, 172, LW, 840, { rx: 20, fill: '#fff', filter: 'sh' });
  const sec = (y, t) => text(LX + 20, y, t, { size: 11, weight: 700, fill: C.ink3, ls: 0.8 });
  const row = (y, t1, t2, o = {}) => {
    let r = '';
    if (o.sel) r += rect(LX + 8, y - 6, LW - 16, 62, { rx: 12, fill: '#EEF0FE' });
    if (o.mark) r += text(LX + 24, y + 22, o.mark, { size: 14, weight: 700, fill: o.markColor, anchor: 'middle' });
    else r += circle(LX + 24, y + 17, 5, 'none', { stroke: C.ink3, sw: 1.5 });
    r += text(LX + 42, y + 20, t1, { size: 14, cls: 'serif', weight: o.sel ? 700 : 400 });
    r += text(LX + 42, y + 40, t2, { size: 11.5, fill: o.warn ? '#9A5B00' : C.ink3 });
    return r;
  };
  let y = 200;
  s += sec(y, 'CHANGES TO YOUR CARDS · 4'); y += 14;
  s += row(y, 'Statement and Proof of the Cayley–H…', 'your card · +2 additions · Additions only ✓', { sel: true }); y += 64;
  s += row(y, 'Definition of an Eigenvalue, with Exa…', 'your card · +1 diagram · Additions only ✓', { mark: '✓', markColor: C.good }); y += 64;
  s += row(y, 'Statement and Proof of Rank–Nullity', 'your card · +1 intuition'); y += 64;
  s += row(y, 'Definition of the Characteristic Poly…', 'your card · fixes an error in the card', { warn: true }); y += 72;
  s += sec(y, 'NEW CARDS · 14'); y += 14;
  s += row(y, 'Definition of the Minimal Polynomial…', 'Definition · L14', { mark: '✓', markColor: C.good }); y += 64;
  s += row(y, 'Statement and Proof of the Primary…', 'Theorem · L14'); y += 64;
  s += row(y, 'Practice: χ and m for a Jordan Block', 'Practice · L16'); y += 64;
  s += row(y, 'Statement and Proof of the Jordan…', 'Theorem · L16 · ⚠ notes may be wrong here', { warn: true }); y += 64;
  s += row(y, 'Synthesis: When Is a Matrix Diagonal…', 'Synthesis · L13–16'); y += 64;
  s += row(y, 'Practice: Is A² = A Diagonalisable?', 'Practice · L13 · Added: (not lectured)'); y += 64;

  // middle: your card with additions
  const MX = 384, MW = 486;
  s += rect(MX, 172, MW, 840, { rx: 20, fill: '#fff', filter: 'sh' });
  s += text(MX + 22, 202, 'YOUR CARD · WITH CLAUDE’S ADDITIONS', { size: 11, weight: 700, fill: C.ink3, ls: 0.8 });
  s += text(MX + 22, 236, 'Statement and Proof of the', { cls: 'serif', size: 20, weight: 700 });
  s += text(MX + 22, 262, 'Cayley–Hamilton Theorem', { cls: 'serif', size: 20, weight: 700 });
  const it = (v) => `<tspan font-style="italic">${v}</tspan>`;
  const sb = (b, v) => `${it(b)}<tspan font-size="11" dy="4" font-style="italic">${v}</tspan><tspan dy="-4">&#8202;</tspan>`;
  const P = (y, str, o = {}) => text(MX + 22, y, str, { cls: 'serif', size: 15, raw: true, ...o });
  const G = (y, h) => rect(MX + 16, y - 17, MW - 32, h, { rx: 6, fill: '#E3F5EA' });
  let my = 300;
  const lh = 22;
  s += P(my, '<tspan font-weight="700">3. Proof (F = ℂ):</tspan> choose a basis in which α is upper'); my += lh;
  s += P(my, `triangular with diagonal ${sb('λ', '1')}, …, ${sb('λ', 'n')}, and put ${sb('U', 'i')} = ⟨${sb('v', '1')}, …, ${sb('v', 'i')}⟩.`); my += lh;
  // pointed-at line
  s += rect(MX + 16, my - 18, 236, 26, { rx: 6, fill: 'none', stroke: C.accent, sw: 2 });
  s += P(my, `Then (${it('α')} − ${sb('λ', 'i')}${it('ι')})${sb('U', 'i')} ⊆ ${sb('U', 'i−1')}<tspan>.</tspan>`); my += lh + 14;
  s += G(my, lh * 4 + 6);
  s += P(my, `<tspan fill="#1F6B43">Since ${it('α')} is upper triangular, ${it('α')}${sb('v', 'i')} = ${sb('λ', 'i')}${sb('v', 'i')} + (terms</tspan>`); my += lh;
  s += P(my, `<tspan fill="#1F6B43">in ${sb('v', '1')}, …, ${sb('v', 'i−1')}), so (${it('α')} − ${sb('λ', 'i')}${it('ι')})${sb('v', 'i')} ∈ ${sb('U', 'i−1')}; and for</tspan>`); my += lh;
  s += P(my, `<tspan fill="#1F6B43">${it('j')} &lt; ${it('i')}, (${it('α')} − ${sb('λ', 'i')}${it('ι')})${sb('v', 'j')} ∈ ${sb('U', 'j')} ⊆ ${sb('U', 'i−1')}. This is the only</tspan>`); my += lh;
  s += P(my, `<tspan fill="#1F6B43">place upper-triangularity is used.</tspan>`); my += lh + 12;
  s += P(my, `Applying the factors for ${it('i')} = ${it('n')}, …, 1 in turn shrinks ${it('V')} to 0.  ∎`); my += lh + 16;
  s += G(my, lh * 2 + 6);
  s += P(my, `<tspan fill="#1F6B43"><tspan font-weight="700">Insight:</tspan> each factor peels one layer off the flag</tspan>`); my += lh;
  s += P(my, `<tspan fill="#1F6B43">${sb('U', '1')} ⊂ ${sb('U', '2')} ⊂ ⋯ ⊂ ${sb('U', 'n')} = ${it('V')}, like a nilpotent shift.</tspan>`); my += lh + 18;
  s += P(my, '<tspan fill="#9C988F">… 4. Arbitrary field F  ·  Intuition  (unchanged)</tspan>');
  // additions-only badge
  s += rect(MX + 16, 840, MW - 32, 50, { rx: 12, fill: '#E3F5EA' });
  s += icon('check', MX + 30, 853, 22, C.good, 2.4);
  s += text(MX + 60, 862, 'Additions only ✓', { size: 15, weight: 700, fill: '#1F6B43' });
  s += text(MX + 60, 880, 'Deleting the green text gives back your card exactly', { size: 12, fill: '#2F7A50' });
  s += button(MX + 16, 950, 140, 46, 'Reject (R)', { fill: '#fff', color: C.again, size: 15, stroke: C.line });
  s += button(MX + 166, 950, 120, 46, 'Edit (E)', { fill: '#fff', color: C.ink, size: 15, stroke: C.line });
  s += button(MX + MW - 176, 950, 160, 46, 'Accept (A)', { size: 15, iconName: 'check' });

  // right: thread
  const TX = 882, TW = W - TX - 16;
  s += rect(TX, 172, TW, 840, { rx: 20, fill: '#fff', filter: 'sh' });
  s += sparkle(TX + 20, 190, 20, C.accent);
  s += text(TX + 48, 206, 'Discuss this card', { size: 17, weight: 700 });
  s += text(TX + TW - 18, 206, 'Claude Opus 5.5', { size: 12, fill: C.ink3, anchor: 'end' });
  s += text(TX + 20, 230, 'Has: LA notes (112 pp + your ink) · 186 cards · your card guidelines', { size: 11.5, fill: C.ink3 });
  s += line(TX + 16, 244, TX + TW - 16, 244, C.line);
  // user message 1 (right)
  const ub = (y, h) => rect(TX + 70, y, TW - 86, h, { rx: 16, fill: C.accentSoft });
  s += ub(258, 104);
  s += rect(TX + 84, 270, TW - 114, 30, { rx: 8, fill: '#fff' });
  s += text(TX + 96, 290, '“ (α − λᵢι)Uᵢ ⊆ Uᵢ₋₁ ”', { size: 14, cls: 'serif', fill: C.ink2, italic: true });
  s += text(TX + 84, 324, 'Why does this hold? I don’t see where the', { size: 14.5, fill: '#0F4D46' });
  s += text(TX + 84, 344, 'vᵢ term goes.', { size: 14.5, fill: '#0F4D46' });
  // claude reply
  const cr = (y, t) => text(TX + 22, y, t, { size: 14.5, cls: 'serif', raw: true });
  let ty = 392;
  cr(0, '');
  for (const l of [
    'In this basis αvᵢ = λᵢvᵢ + (terms in v₁, …, vᵢ₋₁):',
    'that is what upper triangular means, column by',
    'column. Subtracting λᵢvᵢ removes exactly the',
    'vᵢ-component, and vectors already in Uᵢ₋₁ stay',
    'there. I’ve written this into the proof (green),',
    'and added a one-line insight about the flag.',
  ]) { s += cr(ty, l); ty += 22; }
  // proposal block
  ty += 8;
  s += rect(TX + 16, ty, TW - 32, 92, { rx: 14, fill: '#fff', stroke: '#CDE7E2', sw: 1.5 });
  s += text(TX + 30, ty + 24, 'PROPOSED CHANGE · 2 additions', { size: 10.5, weight: 700, fill: C.accent, ls: 0.8 });
  s += text(TX + TW - 30, ty + 24, 'Additions only ✓', { size: 12, weight: 700, fill: C.good, anchor: 'end' });
  s += button(TX + 30, ty + 40, 110, 38, 'Apply', { size: 14 });
  s += button(TX + 150, ty + 40, 150, 38, 'Keep talking', { fill: '#fff', color: C.accent, size: 14, stroke: C.line });
  ty += 112;
  // user message 2
  s += ub(ty, 62);
  s += text(TX + 84, ty + 26, 'Good. Also say what goes wrong if α', { size: 14.5, fill: '#0F4D46' });
  s += text(TX + 84, ty + 46, 'isn’t triangularisable over F.', { size: 14.5, fill: '#0F4D46' });
  ty += 86;
  s += circle(TX + 28, ty - 5, 4, C.accent);
  s += text(TX + 40, ty, 'Thinking · reading LA notes pp. 55–61 …', { size: 13, fill: C.ink2, italic: true });
  // composer
  s += rect(TX + 16, 944, TW - 32, 52, { rx: 26, fill: C.surface2 });
  s += text(TX + 36, 975, 'Reply, or write with the Pencil…', { size: 14.5, fill: C.ink3 });
  s += icon('pen', TX + TW - 136, 957, 22, C.ink2);
  s += icon('mic', TX + TW - 100, 957, 22, C.ink2);
  s += circle(TX + TW - 48, 970, 19, C.accent);
  s += icon('send', TX + TW - 58, 960, 20, '#fff', 2);
  s += text(TX + 20, 932, 'Tap any line of the card to quote it', { size: 11.5, fill: C.ink3 });
  return device(W, H, s, { title: 'MathsMaster: inbox with Claude’s report, an additions-only change, and the card thread' });
}

// ---------------------------------------------------------------- 06 Compact (11" portrait)
export function compact() {
  const w = 820, h = 1180;
  // Today, portrait
  let a = '';
  a += icon('sidebar', 24, 44, 24, C.accent);
  a += icon('search', w - 50, 44, 24, C.accent);
  a += text(28, 112, 'Today', { size: 34, weight: 750 });
  a += text(28, 140, 'Sunday 22 November · Michaelmas, week 7', { size: 15, fill: C.ink2 });
  a += rect(20, 160, w - 40, 230, { rx: 24, fill: '#fff', filter: 'sh' });
  a += text(44, 248, '64', { size: 78, weight: 750, cls: 'rnd' });
  a += text(160, 214, 'cards due', { size: 21, weight: 650 });
  a += text(160, 240, 'about 15 min · + 10 new', { size: 15, fill: C.ink2 });
  const parts = [[23, C.indigo], [18, C.teal], [11, C.amber], [8, C.coral], [4, C.violet]];
  let bx = 44;
  for (const [k, c] of parts) { const ww = (w - 88) * k / 64; a += rect(bx, 284, ww - 3, 12, { rx: 4, fill: c }); bx += ww; }
  a += button(44, 318, w - 88, 52, 'Start review', { size: 18, iconName: 'cards' });
  a += text(28, 440, 'Up next', { size: 21, weight: 700 });
  a += rect(20, 456, w - 40, 170, { rx: 20, fill: '#fff', filter: 'sh' });
  a += rect(36, 476, 5, 44, { rx: 2.5, fill: C.indigo });
  a += text(54, 494, 'LA · Sheet 3 supervision', { size: 16, weight: 600 });
  a += text(54, 516, 'Thu 26 Nov · ⚑ 2 stuck', { size: 13.5, fill: C.ink2 });
  a += rect(36, 556, 5, 44, { rx: 2.5, fill: C.teal });
  a += text(54, 574, 'A&T · Sheet 3 hand-in', { size: 16, weight: 600 });
  a += text(54, 596, 'Tomorrow · 6 of 12 done', { size: 13.5, fill: C.ink2 });
  a += text(28, 676, 'Continue', { size: 21, weight: 700 });
  [[C.amber, 'pdf'], [C.teal, 'note'], [C.indigo, 'pdf']].forEach(([c, k], i) => {
    const x = 28 + i * 260;
    a += k === 'pdf' ? pdfThumb(x, 696, 236, 180, { accent: c, seed: i + 30, title: false }) : noteThumb(x, 696, 236, 180, { accent: c, seed: i + 9 });
  });
  a += text(28, 904, 'Methods notes · p. 47', { size: 13.5, weight: 600 });
  a += text(288, 904, 'A&T Sheet 3 · Q7', { size: 13.5, weight: 600 });
  a += text(548, 904, 'LA notes · p. 84', { size: 13.5, weight: 600 });
  a += rect(20, 940, w - 40, 110, { rx: 20, fill: C.accentSoft });
  a += sparkle(40, 962, 22, C.accent);
  a += text(72, 980, '12 new cards ready to triage', { size: 17, weight: 700, fill: '#0F4D46' });
  a += text(40, 1010, 'Linear Algebra L13–16 · Claude (VPS)', { size: 13.5, fill: '#2B5F59' });
  a += button(w - 170, 966, 130, 40, 'Triage', { size: 15 });
  a += text(w / 2, 1110, 'Sidebar slides in over the content (☰ or swipe from the left edge)', { size: 12.5, fill: C.ink3, anchor: 'middle' });

  // Editor, portrait
  let b = rect(0, 0, w, h, { fill: '#E9E6E0' });
  const pw = w - 40, ph = pw * 1.414;
  b += rect(20, 100, pw, ph, { fill: '#fff', filter: 'sh' });
  b += rect(20, 100, pw, ph, { fill: 'url(#dots)' });
  const hw = (x, y, str, o = {}) => text(x, y, str, { cls: 'hand', size: 21, fill: C.penBlack, raw: true, ...o });
  b += hw(60, 170, 'Lecture 16: Jordan normal form', { size: 25, fill: C.penBlue });
  b += path('M60 180 q 150 8 330 0', { stroke: C.penBlue, sw: 1.6 });
  b += hw(60, 230, 'Thm. α ∈ End(V), V f.d. over ℂ. Then ∃ basis');
  b += hw(60, 266, 'in which [α] = diag(J₁, …, Jᵣ), Jᵢ Jordan blocks,');
  b += hw(60, 302, 'unique up to order of blocks.');
  b += hw(60, 360, '# blocks with eigenvalue λ = n(α − λι)', { fill: C.penRed });
  b += hw(60, 396, '# blocks of size ≥ k = n((α−λι)ᵏ) − n((α−λι)ᵏ⁻¹)', { fill: C.penRed, size: 19 });
  b += hw(60, 460, 'e.g. J₃(λ):  χ = (t−λ)³ = m', {});
  b += hw(60, 520, '[ λ 1 0 ]', { size: 22 });
  b += hw(60, 552, '[ 0 λ 1 ]', { size: 22 });
  b += hw(60, 584, '[ 0 0 λ ]', { size: 22 });
  b += rect(w - 120, 220, 74, 28, { rx: 14, fill: C.indigo });
  b += icon('cards', w - 112, 225, 17, '#fff');
  b += text(w - 86, 239, '3', { size: 14, weight: 700, fill: '#fff', cls: 'rnd' });
  b += rect(12, 30, w - 24, 56, { rx: 28, fill: 'url(#glass)', stroke: '#fff', filter: 'sh' });
  b += icon('chevL', 26, 46, 24, C.accent, 2.2);
  b += text(w / 2, 55, 'Lecture 16 working', { size: 16, weight: 700, anchor: 'middle' });
  b += text(w / 2, 74, 'page 3 of 5', { size: 12, fill: C.ink2, anchor: 'middle' });
  b += icon('undo', w - 196, 46, 24, C.accent);
  b += sparkle(w - 150, 47, 22, C.accent);
  b += icon('share', w - 106, 46, 24, C.accent);
  b += icon('more', w - 60, 46, 24, C.accent);
  const tx0 = (w - 420) / 2, ty0 = h - 84;
  b += rect(tx0, ty0, 420, 60, { rx: 22, fill: 'url(#glass)', stroke: '#fff', filter: 'sh2' });
  [C.penBlack, C.penBlue, C.penRed].forEach((c, i) => { b += `<path d="M${tx0 + 24 + i * 30} ${ty0 + 56} v-30 l7 -16 l7 16 v30 z" fill="#F7F6F3" stroke="#BDB8AE"/>` + rect(tx0 + 24 + i * 30, ty0 + 32, 14, 6, { fill: c }); });
  b += `<path d="M${tx0 + 118} ${ty0 + 56} v-28 h16 v28 z" fill="#F7F6F3" stroke="#BDB8AE"/>` + rect(tx0 + 118, ty0 + 18, 16, 10, { fill: C.hl });
  b += icon('lasso', tx0 + 152, ty0 + 18, 24, C.ink2);
  b += icon('cardPlus', tx0 + 192, ty0 + 18, 24, C.indigo);
  [C.penBlack, C.penBlue, C.penRed, C.hl].forEach((c, i) => { b += circle(tx0 + 254 + i * 34, ty0 + 30, 11, c, { stroke: i === 0 ? C.accent : '#fff', sw: i === 0 ? 3 : 2 }); });
  b += text(w / 2, h - 96, '', {});

  // compose both devices into one SVG
  const devA = device(w, h, a, { title: 'Today, 11-inch portrait' });
  const devB = device(w, h, b, { title: 'Editor, 11-inch portrait' });
  const inner = (svg) => svg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
  const DW = w + 40, DH = h + 40;
  const total = DW * 2 + 60;
  const fix = (svg, id) => inner(svg).replace(/id="screen"/g, `id="screen-${id}"`).replace(/url\(#screen\)/g, `url(#screen-${id})`);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${DH + 60}" width="${total}" height="${DH + 60}" role="img" aria-label="11-inch portrait layouts">
  <title>MathsMaster: 11-inch portrait (Today and editor)</title>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <g>${fix(devA, 'a')}</g>
  <g transform="translate(${DW + 60} 0)">${fix(devB, 'b')}</g>
  <text x="${DW / 2}" y="${DH + 44}" text-anchor="middle" font-family="-apple-system,'Segoe UI',Ubuntu,Arial,sans-serif" font-size="22" fill="#6B6862">Today: sidebar hidden, single column</text>
  <text x="${DW + 60 + DW / 2}" y="${DH + 44}" text-anchor="middle" font-family="-apple-system,'Segoe UI',Ubuntu,Arial,sans-serif" font-size="22" fill="#6B6862">Editor: A4 at fit width (≈ 76 % of real size)</text>
</svg>`;
}

// ---------------------------------------------------------------- 07 iPhone companion
function phone(w, h, content, title) {
  const bz = 12, W2 = w + bz * 2, H2 = h + bz * 2;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W2} ${H2}" width="${W2}" height="${H2}" role="img" aria-label="${title}">
  <title>${title}</title>${STYLE}${DEFS}
  <defs><clipPath id="pscreen"><rect x="0" y="0" width="${w}" height="${h}" rx="48"/></clipPath></defs>
  <rect x="0" y="0" width="${W2}" height="${H2}" rx="60" fill="#1E1E20"/>
  <g transform="translate(${bz} ${bz})" clip-path="url(#pscreen)">
    <rect x="0" y="0" width="${w}" height="${h}" fill="${C.bg}"/>
    ${content}
    <rect x="${w / 2 - 62}" y="11" width="124" height="36" rx="18" fill="#000"/>
    ${text(46, 36, '9:41', { size: 16, weight: 650 })}
    ${rect(w - 62, 25, 26, 12, { rx: 3.5, stroke: C.ink, sw: 1.2 })}${rect(w - 60, 27, 20, 8, { rx: 2, fill: C.ink })}
    <rect x="${w / 2 - 70}" y="${h - 12}" width="140" height="5" rx="2.5" fill="#1C1B19"/>
  </g>
</svg>`;
}

export function iphone() {
  const w = 393, h = 852;
  const it = (v) => `<tspan font-style="italic">${v}</tspan>`;
  const sb = (b, v) => `${it(b)}<tspan font-size="10" dy="3" font-style="italic">${v}</tspan><tspan dy="-3">&#8202;</tspan>`;
  // A: review (revealed, no writing area)
  let a = '';
  a += icon('close', 18, 64, 24, C.accent, 2.2);
  a += text(w / 2, 82, '18 / 64', { size: 15, weight: 650, anchor: 'middle', cls: 'rnd' });
  a += icon('undo', w - 44, 64, 24, C.accent);
  a += rect(18, 100, w - 36, 5, { rx: 2.5, fill: C.surface2 }) + rect(18, 100, (w - 36) * 18 / 64, 5, { rx: 2.5, fill: C.accent });
  a += rect(12, 118, w - 24, 600, { rx: 22, fill: '#fff', filter: 'sh' });
  a += chip(28, 134, 'Linear Algebra · Theorem', { dot: C.indigo, fill: '#EEF0FE', color: '#3A47B8', size: 11.5, h: 24 }).svg;
  a += text(28, 186, 'Statement and Proof of the', { cls: 'serif', size: 20 });
  a += text(28, 212, 'Cayley–Hamilton Theorem', { cls: 'serif', size: 20 });
  a += line(24, 232, w - 24, 232, C.line);
  let cx = 24;
  for (const [t, on] of [['Motivation'], ['Statement', true], ['Proof'], ['Intuition']]) {
    const c = chip(cx, 244, t, { fill: on ? C.ink : C.surface2, color: on ? '#fff' : C.ink2, size: 11, h: 24, pad: 8 });
    a += c.svg; cx += c.w + 5;
  }
  const P = (y, s, o = {}) => text(28, y, s, { cls: 'serif', size: 14.5, raw: true, ...o });
  let y = 300;
  a += P(y, '<tspan font-weight="700">2. Statement:</tspan>'); y += 22;
  a += P(y, `Let ${it('V')} be an ${it('n')}-dimensional vector space`); y += 21;
  a += P(y, `over ${it('F')} and ${it('α')} ∈ End(${it('V')}). Then`); y += 34;
  a += text(w / 2, y, '', {}); a += text(w / 2, y, `${sb('χ', 'α')}(${it('α')}) = 0.`, { cls: 'serif', size: 18, raw: true, anchor: 'middle' }); y += 36;
  a += P(y, '<tspan font-weight="700">3. Proof (F = ℂ):</tspan> choose a basis in'); y += 21;
  a += P(y, `which ${it('α')} is upper triangular, diagonal`); y += 21;
  a += P(y, `${sb('λ', '1')}, …, ${sb('λ', 'n')}, and put ${sb('U', 'i')} = ⟨${sb('v', '1')}, …, ${sb('v', 'i')}⟩.`); y += 25;
  a += P(y, 'Upper-triangularity says'); y += 32;
  a += text(w / 2, y, `(${it('α')} − ${sb('λ', 'i')}${it('ι')})${sb('U', 'i')} ⊆ ${sb('U', 'i−1')},`, { cls: 'serif', size: 16, raw: true, anchor: 'middle' }); y += 32;
  a += P(y, 'so applying the factors in turn shrinks', { opacity: 0.8 }); y += 21;
  a += P(y, `${it('V')} to 0 …`, { opacity: 0.5 });
  a += rect(w - 22, 290, 3, 120, { rx: 1.5, fill: '#D3CEC5' });
  // action pills
  a += rect(24, 648, 116, 36, { rx: 18, fill: C.accent }) + sparkle(36, 657, 16, '#fff') + text(58, 671, 'Discuss', { size: 14, weight: 650, fill: '#fff' });
  a += rect(148, 648, 100, 36, { rx: 18, fill: '#fff', stroke: C.line }) + icon('source', 158, 656, 18, C.accent) + text(180, 671, 'Source', { size: 14, fill: C.accent });
  a += icon('flag', w - 52, 655, 22, C.ink3);
  // grade buttons
  const gs = [['Again', '<10m', C.again], ['Hard', '2d', C.hard], ['Good', '6d', C.good], ['Easy', '14d', C.easy]];
  const bw = (w - 24 - 18) / 4;
  gs.forEach(([g, iv, col], i) => {
    const x = 12 + i * (bw + 6);
    const dom = g === 'Again' || g === 'Good';
    a += rect(x, 738, bw, 64, { rx: 16, fill: dom ? col : '#fff', stroke: dom ? null : C.line });
    a += text(x + bw / 2, 766, g, { size: 16, weight: 700, fill: dom ? '#fff' : col, anchor: 'middle' });
    a += text(x + bw / 2, 786, iv, { size: 12, weight: 600, fill: dom ? 'rgba(255,255,255,0.9)' : C.ink2, anchor: 'middle', cls: 'rnd' });
  });

  // B: thread
  let b = '';
  b += icon('chevL', 14, 62, 26, C.accent, 2.2);
  b += text(w / 2, 74, 'Cayley–Hamilton', { size: 16, weight: 700, anchor: 'middle' });
  b += text(w / 2, 93, 'Discuss · Claude Opus 5.5', { size: 12, fill: C.ink2, anchor: 'middle' });
  b += line(0, 110, w, 110, C.line);
  b += rect(70, 126, w - 86, 100, { rx: 18, fill: C.accentSoft });
  b += rect(84, 138, w - 114, 28, { rx: 8, fill: '#fff' });
  b += text(96, 157, '“ (α − λᵢι)Uᵢ ⊆ Uᵢ₋₁ ”', { size: 13, cls: 'serif', italic: true, fill: C.ink2 });
  b += text(84, 190, 'Why does this hold? I don’t see', { size: 14, fill: '#0F4D46' });
  b += text(84, 209, 'where the vᵢ term goes.', { size: 14, fill: '#0F4D46' });
  let ty = 254;
  for (const l of [
    'In this basis αvᵢ = λᵢvᵢ + (terms in',
    'v₁, …, vᵢ₋₁): that is what upper',
    'triangular means, column by column.',
    'Subtracting λᵢvᵢ removes exactly the',
    'vᵢ-component, and Uᵢ₋₁ is preserved.',
    'Want me to add this step to the card?',
  ]) { b += text(20, ty, l, { size: 14.5, cls: 'serif' }); ty += 21; }
  ty += 12;
  b += rect(16, ty, w - 32, 128, { rx: 16, fill: '#fff', stroke: '#CDE7E2', sw: 1.5 });
  b += text(30, ty + 24, 'PROPOSED CHANGE', { size: 10.5, weight: 700, fill: C.accent, ls: 0.8 });
  b += text(w - 30, ty + 24, 'Additions only ✓', { size: 11.5, weight: 700, fill: C.good, anchor: 'end' });
  b += rect(30, ty + 36, w - 60, 40, { rx: 8, fill: '#E3F5EA' });
  b += text(40, ty + 52, '+ Since α is upper triangular, αvᵢ = λᵢvᵢ', { size: 12, cls: 'serif', fill: '#1F6B43' });
  b += text(40, ty + 68, '  + (terms in v₁, …, vᵢ₋₁), so …', { size: 12, cls: 'serif', fill: '#1F6B43' });
  b += button(30, ty + 84, 100, 34, 'Apply', { size: 14 });
  b += button(140, ty + 84, 130, 34, 'Keep talking', { fill: '#fff', color: C.accent, size: 14, stroke: C.line });
  ty += 150;
  b += rect(150, ty, w - 166, 46, { rx: 18, fill: C.accentSoft });
  b += text(166, ty + 28, 'Yes, and give an example.', { size: 14, fill: '#0F4D46' });
  ty += 74;
  b += circle(26, ty - 5, 4, C.accent);
  b += text(38, ty, 'Thinking · checking LA notes p. 61 …', { size: 12.5, fill: C.ink2, italic: true });
  b += rect(12, h - 92, w - 24, 50, { rx: 25, fill: C.surface2 });
  b += text(32, h - 61, 'Reply…', { size: 15, fill: C.ink3 });
  b += icon('mic', w - 98, h - 79, 22, C.ink2);
  b += circle(w - 44, h - 67, 18, C.accent);
  b += icon('send', w - 54, h - 77, 20, '#fff', 2);

  const devA = phone(w, h, a, 'iPhone: review');
  const devB = phone(w, h, b, 'iPhone: card thread');
  const inner = (svg, id) => svg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '').replace(/id="pscreen"/g, `id="pscreen-${id}"`).replace(/url\(#pscreen\)/g, `url(#pscreen-${id})`);
  const DW = w + 24, DH = h + 24, gap = 70, total = DW * 2 + gap;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${DH + 60}" width="${total}" height="${DH + 60}" role="img" aria-label="iPhone companion">
  <title>MathsMaster: iPhone companion (review and card thread)</title>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <g>${inner(devA, 'a')}</g>
  <g transform="translate(${DW + gap} 0)">${inner(devB, 'b')}</g>
  <text x="${DW / 2}" y="${DH + 42}" text-anchor="middle" font-family="-apple-system,'Segoe UI',Ubuntu,Arial,sans-serif" font-size="18" fill="#6B6862">Review: tap to reveal, no writing area</text>
  <text x="${DW + gap + DW / 2}" y="${DH + 42}" text-anchor="middle" font-family="-apple-system,'Segoe UI',Ubuntu,Arial,sans-serif" font-size="18" fill="#6B6862">Card thread: ask, get proposals, keep talking</text>
</svg>`;
}
