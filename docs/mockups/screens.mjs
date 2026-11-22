// The six layout mockups. Each export returns a complete SVG document.
import {
  C, text, rect, circle, line, path, icon, sparkle, chip, badge, button, pdfThumb, noteThumb, device, sidebar, tw,
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
  s += rect(mx, my, 214, 200, { rx: 16, fill: '#fff', filter: 'sh2' });
  const items = [['cardPlus', 'Make card', C.ink], ['sparkle', 'Transcribe to LaTeX', C.ink], ['sparkle', 'Explain this', C.ink], ['share', 'Copy as image', C.ink]];
  items.forEach(([ic, t, c], i) => {
    const iy = my + 14 + i * 46;
    if (i === 0) s += rect(mx + 8, iy - 4, 198, 40, { rx: 10, fill: C.accentSoft });
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

// ---------------------------------------------------------------- 04 Review
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
  s += icon('undo', 1270, 46, 24, C.accent);
  s += icon('more', 1316, 46, 24, C.accent);

  // card
  const cx = 56, cy = 110, cw = 720, ch = 760;
  s += rect(cx, cy, cw, ch, { rx: 26, fill: '#fff', filter: 'sh2' });
  s += chip(cx + 28, cy + 26, 'Linear Algebra · Theorem · L15', { dot: C.indigo, fill: '#EEF0FE', color: '#3A47B8', size: 12.5, h: 26 }).svg;
  s += text(cx + cw - 28, cy + 44, 'due 6 d overdue · reviewed 4×', { size: 12, fill: C.ink3, anchor: 'end' });
  s += text(cx + 40, cy + 108, 'State the Cayley–Hamilton theorem.', { cls: 'serif', size: 28 });
  // scratch area
  const sy = cy + 140;
  s += line(cx + 28, sy, cx + cw - 28, sy, C.line);
  s += text(cx + 40, sy + 26, 'YOUR ATTEMPT', { size: 10.5, weight: 700, fill: C.ink3, ls: 1 });
  s += icon('pen', cx + cw - 52, sy + 10, 18, C.ink3);
  const hw = (x, y, str, o = {}) => text(x, y, str, { cls: 'hand', size: 22, fill: C.penBlue, raw: true, ...o });
  s += hw(cx + 50, sy + 72, 'A ∈ Mₙ(F),  χ_A(t) = det(tI − A)');
  s += hw(cx + 50, sy + 114, '⇒  χ_A(A) = 0     (A satisfies its own');
  s += hw(cx + 290, sy + 150, 'char. polynomial)');
  s += path(`M${cx + 50} ${sy + 126} q 30 6 60 0`, { stroke: C.penBlue, sw: 1.6 });
  // answer
  const ay = sy + 196;
  s += rect(cx + 20, ay, cw - 40, 300, { rx: 18, fill: '#F7F6F2' });
  s += text(cx + 40, ay + 30, 'ANSWER', { size: 10.5, weight: 700, fill: C.good, ls: 1 });
  const ser = (x, y, str, size = 21) => text(x, y, str, { cls: 'serif', size, raw: true });
  const it = (v) => `<tspan font-style="italic">${v}</tspan>`;
  s += ser(cx + 40, ay + 72, `Let ${it('V')} be a finite-dimensional vector space over ${it('F')} and`);
  s += ser(cx + 40, ay + 106, `${it('α')} ∈ End(${it('V')}) with characteristic polynomial`);
  s += ser(cx + 200, ay + 150, `${it('χ')}<tspan font-size="14" dy="5" font-style="italic">α</tspan><tspan dy="-5">(</tspan>${it('t')}) = det(${it('t')}${it('ι')} − ${it('α')}).`, 23);
  s += ser(cx + 40, ay + 194, `Then ${it('χ')}<tspan font-size="14" dy="5" font-style="italic">α</tspan><tspan dy="-5">(</tspan>${it('α')}) = 0.`);
  s += line(cx + 40, ay + 222, cx + cw - 60, ay + 222, C.line);
  s += icon('chevR', cx + 36, ay + 238, 18, C.ink2);
  s += text(cx + 58, ay + 253, 'Extra: proof idea (triangularise over ℂ, or the adjugate trick)', { size: 14, fill: C.ink2 });
  s += chip(cx + 40, ay + 268, '↗ LA notes 2026 · p. 61', { fill: '#fff', color: C.accent, size: 12.5, h: 24, stroke: C.line }).svg;

  // grade bar
  const gy = 900;
  s += rect(cx, gy, cw, 92, { rx: 26, fill: 'url(#glass)', stroke: '#fff', filter: 'sh2' });
  const grades = [['Again', '< 10 m', C.again, 196, '1'], ['Hard', '2 d', C.hard, 140, '2'], ['Good', '6 d', C.good, 220, '3'], ['Easy', '14 d', C.easy, 124, '4']];
  let gx = cx + 12;
  grades.forEach(([g, iv, col, w, k]) => {
    const dom = g === 'Again' || g === 'Good';
    s += rect(gx, gy + 12, w - 8, 68, { rx: 18, fill: dom ? col : '#fff', stroke: dom ? null : C.line });
    s += text(gx + (w - 8) / 2, gy + 42, g, { size: 18, weight: 700, fill: dom ? '#fff' : col, anchor: 'middle' });
    s += text(gx + (w - 8) / 2, gy + 64, iv, { size: 13, weight: 600, fill: dom ? 'rgba(255,255,255,0.9)' : C.ink2, anchor: 'middle', cls: 'rnd' });
    s += text(gx + w - 20, gy + 28, k, { size: 10, weight: 700, fill: dom ? 'rgba(255,255,255,0.7)' : C.ink3, anchor: 'end' });
    gx += w;
  });

  // side rail
  const rx = cx + cw + 18;
  [['sparkle', 'Explain', true], ['source', 'Source'], ['edit', 'Edit'], ['flag', 'Flag'], ['more', 'More']].forEach(([ic, t, on], i) => {
    const y = 150 + i * 84;
    s += circle(rx + 26, y + 26, 26, on ? C.accent : '#fff', { stroke: on ? null : C.line });
    s += ic === 'sparkle' ? sparkle(rx + 15, y + 15, 22, '#fff') : icon(ic, rx + 14, y + 14, 24, C.accent);
    s += text(rx + 26, y + 70, t, { size: 11.5, fill: on ? C.accent : C.ink2, anchor: 'middle', weight: on ? 650 : 450 });
  });

  // explain panel
  const ex = 880, ew = W - ex - 16;
  s += rect(ex, 110, ew, 882, { rx: 24, fill: '#fff', filter: 'sh2' });
  s += sparkle(ex + 22, 132, 22, C.accent);
  s += text(ex + 54, 150, 'Explain', { size: 19, weight: 700 });
  s += text(ex + ew - 22, 150, 'Gemini', { size: 12, fill: C.ink3, anchor: 'end' });
  s += text(ex + 22, 178, 'Cayley–Hamilton: why is it true?', { size: 14, fill: C.ink2 });
  const p = (y, str, o = {}) => text(ex + 22, y, str, { size: 15, cls: 'serif', raw: true, ...o });
  let py = 220;
  [
    'Over ℂ, pick a basis <tspan font-style="italic">v</tspan><tspan font-size="11" dy="4">1</tspan><tspan dy="-4">, …, </tspan><tspan font-style="italic">v</tspan><tspan font-size="11" dy="4" font-style="italic">n</tspan><tspan dy="-4"> making </tspan><tspan font-style="italic">A</tspan>',
    'upper triangular, with diagonal <tspan font-style="italic">λ</tspan><tspan font-size="11" dy="4">1</tspan><tspan dy="-4">, …, </tspan><tspan font-style="italic">λ</tspan><tspan font-size="11" dy="4" font-style="italic">n</tspan><tspan dy="-4">.</tspan>',
    'Then (<tspan font-style="italic">A</tspan> − <tspan font-style="italic">λ</tspan><tspan font-size="11" dy="4" font-style="italic">i</tspan><tspan dy="-4"> </tspan><tspan font-style="italic">I</tspan>) maps ⟨<tspan font-style="italic">v</tspan><tspan font-size="11" dy="4">1</tspan><tspan dy="-4">, …, </tspan><tspan font-style="italic">v</tspan><tspan font-size="11" dy="4" font-style="italic">i</tspan><tspan dy="-4">⟩ into</tspan>',
    '⟨<tspan font-style="italic">v</tspan><tspan font-size="11" dy="4">1</tspan><tspan dy="-4">, …, </tspan><tspan font-style="italic">v</tspan><tspan font-size="11" dy="4" font-style="italic">i</tspan><tspan font-size="11">−1</tspan><tspan dy="-4">⟩.</tspan> Applying the factors for',
    '<tspan font-style="italic">i</tspan> = <tspan font-style="italic">n</tspan>, <tspan font-style="italic">n</tspan> − 1, …, 1 in turn shrinks <tspan font-style="italic">V</tspan> to 0,',
    'and their product is <tspan font-style="italic">χ</tspan><tspan font-size="11" dy="4" font-style="italic">A</tspan><tspan dy="-4">(</tspan><tspan font-style="italic">A</tspan>).',
  ].forEach((l) => { s += p(py, l); py += 26; });
  py += 14;
  s += rect(ex + 16, py - 4, ew - 32, 104, { rx: 14, fill: '#FFF6E5' });
  s += text(ex + 30, py + 20, 'COMMON MISTAKE', { size: 10.5, weight: 700, fill: C.hard, ls: 1 });
  s += p(py + 46, '“Substitute <tspan font-style="italic">t</tspan> = <tspan font-style="italic">A</tspan> into det(<tspan font-style="italic">tI</tspan> − <tspan font-style="italic">A</tspan>)” is wrong:', { size: 14.5 });
  s += p(py + 70, 'det(<tspan font-style="italic">AI</tspan> − <tspan font-style="italic">A</tspan>) is a scalar, not the matrix', { size: 14.5 });
  s += p(py + 92, '<tspan font-style="italic">χ</tspan><tspan font-size="10" dy="4" font-style="italic">A</tspan><tspan dy="-4">(</tspan><tspan font-style="italic">A</tspan>).', { size: 14.5 });
  py += 130;
  let chx = ex + 22;
  for (const t of ['Example', 'Counterexample', 'Simpler', 'Over any field?']) {
    const c = chip(chx, py, t, { fill: C.accentSoft, color: C.accent, size: 13, h: 30, pad: 12 });
    if (chx + c.w > ex + ew - 16) { chx = ex + 22; py += 40; }
    s += chip(chx, py, t, { fill: C.accentSoft, color: C.accent, size: 13, h: 30, pad: 12 }).svg;
    chx += c.w + 8;
  }
  py += 52;
  s += button(ex + 22, py, 170, 38, 'Save to Extra', { fill: C.surface2, color: C.ink, size: 14 });
  // follow-up input
  s += rect(ex + 16, 900, ew - 32, 48, { rx: 24, fill: C.surface2 });
  s += text(ex + 36, 930, 'Ask a follow-up…', { size: 15, fill: C.ink3 });
  s += icon('pen', ex + ew - 82, 912, 22, C.ink2);
  s += circle(ex + ew - 40, 924, 18, C.accent);
  s += icon('send', ex + ew - 50, 914, 20, '#fff', 2);
  s += text(ex + 22, 974, 'AI budget today: 14 of 20 vision · 380 of 500 text', { size: 11.5, fill: C.ink3 });
  return device(W, H, s, { title: 'MathsMaster: card review with Explain panel' });
}

// ---------------------------------------------------------------- 05 Card editor + Inbox
export function cards() {
  let s = '';
  // header
  s += icon('sidebar', 30, 44, 24, C.accent);
  s += text(30, 108, 'Inbox', { size: 36, weight: 750 });
  s += sparkle(150, 82, 22, C.accent);
  s += text(30, 138, 'Linear Algebra · lectures 13–16  ·  18 cards  ·  Claude (VPS)  ·  2 h ago', { size: 15, fill: C.ink2 });
  s += rect(30, 154, 300, 6, { rx: 3, fill: C.surface2 }) + rect(30, 154, 100, 6, { rx: 3, fill: C.accent });
  s += text(340, 161, '6 of 18 triaged', { size: 12, fill: C.ink2 });
  s += button(1130, 86, 206, 42, 'Accept all remaining', { fill: C.surface2, color: C.accent, size: 15 });

  // list
  const LX = 20, LW = 410;
  s += rect(LX, 180, LW, 832, { rx: 20, fill: '#fff', filter: 'sh' });
  const rows = [
    ['✓', C.good, 'Define an eigenvalue of α ∈ End(V).', 'Definition · L12'],
    ['✓', C.good, 'Show that eigenvectors for distinct eigenvalues…', 'Theorem · L12'],
    ['✕', C.again, 'What is a matrix?', 'Definition · L12 · rejected'],
    ['✓', C.good, 'α is diagonalisable iff …', 'Theorem · L13'],
    ['✓', C.good, 'Give a matrix that is not diagonalisable over ℂ.', 'Example · L13'],
    ['✓', C.good, 'State the primary decomposition theorem.', 'Theorem · L14'],
    ['●', C.accent, 'Define the minimal polynomial m_α of α…', 'Definition · L14', true],
    ['', null, 'm_α divides every p with p(α) = 0. Why?', 'Proof idea · L14  ·  ⚠ similar card exists'],
    ['', null, 'State the Cayley–Hamilton theorem.', 'Theorem · L15  ·  ⚠ duplicate?'],
    ['', null, 'Compute χ and m for J₃(λ).', 'Example · L16'],
    ['', null, 'Define a Jordan block J_k(λ).', 'Definition · L16'],
    ['', null, 'Number of Jordan blocks for λ = ?', 'Formula · L16'],
  ];
  rows.forEach(([m, col, t, sub, sel], i) => {
    const y = 196 + i * 68;
    if (sel) s += rect(LX + 8, y - 6, LW - 16, 64, { rx: 12, fill: C.accentSoft });
    if (m) s += text(LX + 26, y + 24, m, { size: 15, weight: 700, fill: col, anchor: 'middle' });
    else s += circle(LX + 26, y + 19, 5, 'none', { stroke: C.ink3, sw: 1.5 });
    s += text(LX + 46, y + 22, t.length > 44 ? t.slice(0, 43) + '…' : t, { size: 15, cls: 'serif', fill: m === '✕' ? C.ink3 : C.ink });
    s += text(LX + 46, y + 42, sub, { size: 12, fill: sub.includes('⚠') ? C.hard : C.ink3 });
    if (i < rows.length - 1 && !sel) s += line(LX + 46, y + 58, LX + LW - 16, y + 58, '#F0EDE7');
  });

  // editor
  const EX = 450, EW = W - EX - 20;
  s += rect(EX, 180, EW, 832, { rx: 20, fill: '#fff', filter: 'sh' });
  // metadata chips
  let mx = EX + 24;
  for (const [t, o] of [['Linear Algebra', { dot: C.indigo, fill: '#EEF0FE', color: '#3A47B8' }], ['Basic', {}], ['Definition', { fill: '#E8F5EE', color: C.good }], ['L14', {}], ['#minimal-polynomial', { color: C.accent }]]) {
    const c = chip(mx, 200, t, { size: 12.5, h: 26, ...o });
    s += c.svg; mx += c.w + 8;
  }
  s += chip(EX + EW - 214, 200, '↗ Source: LA notes p. 58', { fill: '#fff', color: C.accent, size: 12, h: 26, stroke: C.line }).svg;

  // fields (left) + preview (right)
  const FX = EX + 24, FW = 404, PX = EX + 452, PW = EW - 476;
  const field = (y, label, lines, h) => {
    let r = text(FX, y, label, { size: 11, weight: 700, fill: C.ink3, ls: 1 });
    r += rect(FX, y + 8, FW, h, { rx: 12, fill: '#FAF9F6', stroke: C.line });
    lines.forEach((l, i) => { r += text(FX + 14, y + 34 + i * 22, l, { size: 13.5, cls: 'mono', fill: C.ink, raw: true }); });
    return r;
  };
  const cmd = (t) => `<tspan fill="#7A3FB8">${t}</tspan>`;
  const dol = '<tspan fill="#C2410C">$</tspan>';
  s += field(258, 'FRONT', [`Define the minimal polynomial ${dol}m_${cmd('\\alpha')}${dol}`, `of ${dol}${cmd('\\alpha')} ${cmd('\\in')} ${cmd('\\mathrm')}{End}(V)${dol}.`], 70);
  s += field(358, 'BACK', [
    `The monic polynomial ${dol}m_${cmd('\\alpha')} ${cmd('\\in')} F[t]${dol} of`,
    `least degree with ${dol}m_${cmd('\\alpha')}(${cmd('\\alpha')}) = 0${dol}. For`,
    `every ${dol}p ${cmd('\\in')} F[t]${dol}:`,
    `${dol}${dol}p(${cmd('\\alpha')}) = 0 ${cmd('\\iff')} m_${cmd('\\alpha')} ${cmd('\\mid')} p.${dol}${dol}`,
  ], 112);
  s += field(500, 'EXTRA', ['<tspan fill="#9C988F">Proof idea, notes… (optional)</tspan>'], 44);
  // accessory bar
  const keys = ['$ $', '$$ $$', '\\mathbb{}', '\\forall', '\\exists', '\\to', '^{}', '_{}', '\\frac', 'pmatrix'];
  let kx = FX;
  s += rect(FX - 8, 570, FW + 16, 46, { rx: 12, fill: C.surface2 });
  [...keys.slice(0, 3), keys[3], keys[5], keys[6], '⋯'].forEach((k) => { const w = tw(k, 12.5, 0.62) + 16; s += rect(kx, 578, w, 30, { rx: 7, fill: '#fff' }); s += text(kx + w / 2, 598, k, { size: 12.5, cls: 'mono', anchor: 'middle' }); kx += w + 5; });
  s += rect(FX, 630, 224, 40, { rx: 12, fill: '#fff', stroke: C.line });
  s += icon('pen', FX + 14, 640, 20, C.accent);
  s += text(FX + 42, 656, 'Write it  →  LaTeX', { size: 14, weight: 600, fill: C.accent });
  s += sparkle(FX + 196, 642, 14, C.accent);

  // preview
  s += text(PX, 258, 'PREVIEW', { size: 11, weight: 700, fill: C.ink3, ls: 1 });
  s += rect(PX, 266, PW, 404, { rx: 18, fill: '#FBFAF7', stroke: C.line });
  const it = (v) => `<tspan font-style="italic">${v}</tspan>`;
  const sub = (b, v) => `${it(b)}<tspan font-size="13" dy="5" font-style="italic">${v}</tspan><tspan dy="-5"></tspan>`;
  const ser = (x, y, str, o = {}) => text(x, y, str, { cls: 'serif', size: 19, raw: true, ...o });
  s += ser(PX + 24, 310, `Define the minimal polynomial ${sub('m', 'α')}`);
  s += ser(PX + 24, 338, `of ${it('α')} ∈ End(${it('V')}).`);
  s += line(PX + 24, 362, PX + PW - 24, 362, C.line);
  s += ser(PX + 24, 398, `The monic polynomial ${sub('m', 'α')} ∈ ${it('F')}[${it('t')}] of least`, { size: 18 });
  s += ser(PX + 24, 426, `degree with ${sub('m', 'α')}(${it('α')}) = 0. For every`, { size: 18 });
  s += ser(PX + 24, 454, `${it('p')} ∈ ${it('F')}[${it('t')}]:`, { size: 18 });
  s += ser(PX + PW / 2, 504, `${it('p')}(${it('α')}) = 0  ⟺  ${sub('m', 'α')} | ${it('p')}.`, { anchor: 'middle', size: 22 });
  s += text(PX + 24, 650, 'KaTeX · renders as you type · errors shown inline', { size: 12, fill: C.ink3 });

  // AI edit strip with diff
  const AY = 692;
  s += rect(EX + 20, AY, EW - 40, 236, { rx: 18, fill: '#F3FAF8', stroke: '#CDE7E2' });
  s += sparkle(EX + 38, AY + 18, 20, C.accent);
  s += text(EX + 68, AY + 34, '“make the back one line shorter, keep the divisibility property”', { size: 15, fill: '#0F4D46', italic: true });
  s += text(EX + 40, AY + 70, 'BACK: SUGGESTED CHANGE', { size: 10.5, weight: 700, fill: C.ink3, ls: 1 });
  s += rect(EX + 40, AY + 80, EW - 80, 34, { rx: 8, fill: '#FDECEC' });
  s += text(EX + 54, AY + 102, '− The monic polynomial m_α ∈ F[t] of least degree with m_α(α) = 0. For every p ∈ F[t]:', { size: 13, cls: 'mono', fill: '#A12B2F' });
  s += rect(EX + 40, AY + 120, EW - 80, 34, { rx: 8, fill: '#E6F6EC' });
  s += text(EX + 54, AY + 142, '+ The least-degree monic m_α with m_α(α) = 0; then for all p:', { size: 13, cls: 'mono', fill: '#1F6B43' });
  s += button(EX + 40, AY + 172, 120, 40, 'Accept', { size: 15 });
  s += button(EX + 170, AY + 172, 110, 40, 'Reject', { fill: '#fff', color: C.ink, size: 15, stroke: C.line });
  s += rect(EX + 300, AY + 172, EW - 340, 40, { rx: 20, fill: '#fff', stroke: '#CDE7E2' });
  s += text(EX + 320, AY + 197, 'Ask AI to change this card…', { size: 14, fill: C.ink3 });

  // triage bar
  s += button(EX + 20, 948, 200, 48, 'Reject  (R)', { fill: '#fff', color: C.again, size: 16, stroke: C.line });
  s += button(EX + 232, 948, 160, 48, 'Edit  (E)', { fill: '#fff', color: C.ink, size: 16, stroke: C.line });
  s += button(EX + EW - 240, 948, 220, 48, 'Accept  (A)', { size: 16, iconName: 'check' });
  return device(W, H, s, { title: 'MathsMaster: AI inbox triage and card editor' });
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
