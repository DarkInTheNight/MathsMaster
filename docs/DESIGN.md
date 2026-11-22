# MathsMaster: design plan (v1)

> **Status:** proposal for the owner to review · **Date:** 22 Nov 2026 (Michaelmas, week 7)\
> **Scope:** layout, UX, data and platform decisions. There's no app code yet. Every later task builds on this document; if a task needs to depart from it, change this file in the same PR.\
> **Mockups:** [`docs/mockups/`](mockups/). The rendered version with the mockups inline is `docs/mockups/design-plan.html`.

MathsMaster is a native SwiftUI iPad app: the single place for a Cambridge Part IB maths degree. It holds courses, lecture notes you write on with the Pencil, example sheets and your answers, handwritten notebooks that print cleanly, and flashcards on a modern spaced-repetition scheduler (FSRS), with AI helping to make and explain the cards.

---

## 0. The decisions, in one table

| # | Area | Decision | Why |
|---|------|----------|-----|
| 1 | Shell | **Two-column `NavigationSplitView`** (sidebar → course page). Documents and reviews open **full screen** on top. | Keeps the library calm and the canvas as large as possible. A third column is too cramped on an 11″ in portrait. |
| 2 | Unit of organisation | **Course** is the hub. Each course has four shelves: *Lecture notes · Example sheets · Notebooks · Cards*. Courses sit under Year → Term. | It matches how the degree is actually structured, so there's nothing new to learn. |
| 3 | Home | **Today** opens first: cards due, the next supervision, *Continue where you left off*, and the AI inbox. | Answers "what should I do now?" in one glance. |
| 4 | Editor | **One page engine for everything.** A document is a stack of pages. Each page has a *background* (a PDF page or a template) and an *ink layer* (PencilKit). | Lecture notes, example sheets and notebooks behave the same way, and you can insert blank pages into a PDF or PDF pages into a notebook. |
| 5 | Ink | **PencilKit `PKCanvasView` + the system `PKToolPicker`**, Pencil-only drawing by default, and the canvas kept in light style on white paper. | This is the same ink Apple Notes uses, and it brings squeeze, double-tap, hover and new tools (e.g. the reed pen in iPadOS 26) for free. |
| 6 | Originals | **PDFs are never modified.** Ink lives in a sidecar next to the PDF. Exports produce a new, flattened PDF. | Lecturers' PDFs stay pristine and replaceable, and sync stays cheap. |
| 7 | Cards | **Markdown + LaTeX text, rendered with KaTeX**, with optional ink fields and image-region cards. **One deck per course + one global queue**, and no nested decks. | Typeset cards look like lecture notes. Region cards keep the link to your handwriting. Filters do the job of sub-decks without the admin. |
| 8 | Review | **Write first, then reveal.** Each card has a Pencil scratch area; the answer slides in under your attempt. FSRS-6, four grade buttons showing the next intervals. | Active recall by writing is how maths is examined. |
| 9 | AI | **AI is a verb on your content, not a chat app.** Everything AI makes lands in an **Inbox** for you to accept or reject. Instant: Gemini (key in the Keychain). Batch notes→cards: Claude Code on the **VPS** (not GitHub Actions, because the repo is public). | Quality control, privacy, and no credentials in the app. |
| 10 | Storage | **Files are the truth**: a human-readable folder in iCloud Drive that you pick once (security-scoped bookmark). Databases, thumbnails and the search index are disposable caches. | Works without entitlements, survives app reinstalls, is shared by the Playgrounds and SideStore copies, and is inspectable in the Files app and on the PC. |
| 11 | Conflicts | **Append-only review logs per app install; per-page ink files; per-card timestamps.** | Two app copies (or two devices) can never corrupt each other's work. |
| 12 | VPS | **Backup mirror + AI job runner**, not the live sync (that's iCloud's job). | Keeps the app simple and offline-first. The VPS adds safety and the batch AI. |
| 13 | Look | **Quiet paper-and-ink UI.** SF Pro for the interface, Computer Modern (KaTeX) for maths content, one teal accent plus a colour per course, Liquid Glass only for floating controls. | Content first. It should look at home on iPadOS 26. |
| 14 | Platform | **iPadOS 26 deployment target, Swift 6, built with the iOS 26 SDK**, the SDK that ships in Swift Playground 4.7. CI uses Xcode 26.x to match. | The newest APIs that the iPad can actually compile. |
| 15 | MVP | **Phase 1 = courses + writing on PDFs + notebooks + print**, runnable from Playgrounds. Flashcards follow straight after (Phase 2, aimed at Christmas-vacation revision). | Ink is both the core input and the riskiest part, so it gets proven first. |

---

## 1. Who it's for, and the principles

**The user:** a second-year Cambridge maths student. Michaelmas has about 5 courses (e.g. Linear Algebra, Analysis & Topology, Methods, Quantum Mechanics, Markov Chains), Lent has about 6 more, then Tripos in late May/June. Each 24-lecture course has a set of lecture notes (usually one long LaTeX PDF), about 4 example sheets with supervisions, and lots of handwritten working. The device is an iPad Air (M4, 2026) with an Apple Pencil: 11″ or 13″, 60 Hz display, Pencil hover supported.

**Principles.** Every later decision should be checked against these:

1. **Ink first.** The Pencil is the primary input everywhere it makes sense: notes, answers, card scratch pads, and even writing LaTeX (AI transcribes it). Nothing may make ink feel worse than Apple Notes.
2. **One home per course.** Anything you own for a course is one tap from its page. There's no hunting through folders.
3. **Files are the truth.** Your work is ordinary files in a folder you can see. The app can be deleted, rebuilt or replaced, and nothing is lost.
4. **AI proposes, you decide.** AI never silently changes your notes or cards. Its output is a suggestion with *Accept / Edit / Reject*.
5. **Fast in crunch week.** Opening a document, starting a review or finding a theorem must take one or two taps and feel instant. Supervision is tomorrow.
6. **Offline by default.** Everything except AI works on a train with no signal.
7. **Looks like a maths book.** Typeset content uses the fonts of a LaTeX document, with calm colours and nothing gamified for its own sake.

**Non-goals for v1:** collaboration or sharing, a web app, typed rich-text notes (handwriting is the notes medium; typed text lives on cards), PDF forms and signatures, and the Anki sync protocol. A one-off Anki import is a possible later item (see the open questions).

---

## 2. Information architecture and navigation

### 2.1 The objects

```
Library (one folder in iCloud Drive)
└── Year  (e.g. "Part IB 2026–27"; older years go under Archive)
    └── Term  (Michaelmas · Lent · Easter)
        └── Course  (name, colour, term, lecturer, exam date)
            ├── Lecture notes   – PDFs, with your ink in a sidecar
            ├── Example sheets  – question PDF + answers notebook + per-question status + supervision date
            ├── Notebooks       – template pages of handwriting
            └── Cards           – the course deck
Cross-cutting: Tags (#compactness), Bookmarks (e.g. "Lecture 16" on a page),
               Links (card ↔ page region), Recents, Inbox (AI output), Trash
```

- **Document kinds** are just three: *Annotated PDF*, *Notebook*, *Example sheet*. An example sheet is a question PDF paired with an answers notebook. All three open in the same editor (§3).
- **Bookmarks** are named page anchors. The main use is *"Lecture 16 starts here"*. They give the course an outline (Lecture 1…24) that drives *"cards from lectures 13–16"*, the course progress line, and jump-to.
- **Tags** apply to documents, pages and cards. They're optional, flat and lower-case. The AI suggests them, and you can ignore them happily.

### 2.2 The shell

![Main split view: sidebar and course page](mockups/01-library.svg)

**Decision:** a `NavigationSplitView` with **two columns**, *sidebar* and *detail*. Opening a document, a review session or the card browser **pushes a full-screen view** with a zoom transition from the thumbnail (iOS 18+ `navigationTransition(.zoom)`), and the sidebar slides away. *Back*, a swipe from the left edge, or ⌘[ returns you to exactly where you were.

The sidebar, top to bottom:

| Section | Items |
|---|---|
| (pinned) | **Today** · **Cards** (all decks, browser, stats; badge = cards due) · **Search** (⌘K) · **Inbox** (badge = AI cards to triage) |
| *Michaelmas 2026* (current term, expanded) | One row per course: a colour dot, the name, and a due-count badge. Rows reorder by drag. |
| *Lent 2027*, *Easter 2027* | Collapsed until their term starts; you can expand them any time. |
| *Library* | All documents · Notebooks · Example sheets · Bookmarks · Tags · Trash |
| (footer) | Settings ⚙︎ · sync status (iCloud ✓ / VPS backup time) |

Why not three columns (sidebar → list → detail, as in Mail and Notes)? A course isn't a list of similar items. It's a *dashboard* of four different kinds of thing, and a dashboard needs width. On an 11″ in portrait a third column leaves about 450 pt for the content. Two columns plus full-screen documents gives every screen the room it needs.

**Adaptive behaviour** (one layout, driven by width rather than device):

| Window width | Sidebar | Course page | Editor |
|---|---|---|---|
| ≥ 1180 pt (13″ landscape, 11″ landscape) | Tiled, 300 pt | 3-column shelf grid | Optional reference pane (35–45 %) beside the page |
| 800–1180 pt (portrait, large Stage Manager window) | Overlay; swipe or ☰ to reveal | 2-column grid | Reference pane as a slide-over sheet |
| < 800 pt (small window, iPadOS 26 tiling) | Collapses to a navigation stack (automatic in `NavigationSplitView`) | 1-column list | Page strip hidden, toolbar condensed |

### 2.3 Today (home)

![Today view](mockups/02-today.svg)

Today is the launch screen. It answers *"what now?"* and offers nothing to configure. The blocks, in priority order:

1. **Header:** *Sunday 22 November · Michaelmas, week 7* (Cambridge week numbering, from term dates in Settings).
2. **Review hero:** *64 due · about 15 min* plus a big **Start review** button (the global queue, §4.2). Under it is a thin stacked bar per course and *+10 new today*. When nothing is due: *All done*, the next due time, and a *Learn 10 new* button.
3. **Up next:** deadlines from example sheets and courses, e.g. *Linear Algebra, Sheet 3 supervision Thu 26 Nov: 2 questions marked Stuck, 1 not started* → tap opens the sheet at the first unfinished question.
4. **Continue:** the 4–6 most recent *locations* (document + page) as large thumbnails, e.g. *Methods notes, p. 47*.
5. **Inbox:** *12 AI cards from "Linear Algebra L13–16" are ready* → triage (§4.5).
6. **Streak and heatmap:** a small 12-week heatmap, the streak, and true retention over the last 30 days. Tap opens Stats.

### 2.4 Course page

The course page is the detail view for a course (mockup 01). From top to bottom:

- **Header:** a colour band, the course name, *Michaelmas 2026 · 24 lectures*, and one progress line (*Lecture 16 of 24 · Sheet 3 supervision Thu · 23 cards due*). There's a **Review this course** button and a **＋** menu: Import PDF… · New notebook · New example sheet… · New card · Scan paper…
- **Shelves:** *Lecture notes*, *Example sheets* (each with status chips: ✓ done, ● in progress, ⚑ 2 stuck, and the supervision date), *Notebooks*, and *Cards* (deck summary: total, due, retention, and *Browse* / *Add*).
- **Outline:** a collapsible list of bookmarks (*Lecture 1 … Lecture 16*). Tapping one jumps into the notes at that page.
- **Drag and drop:** drop PDFs from Files or Safari anywhere on the page to import them. The kind is guessed from the file name (*"sheet"*, *"example"* → Example sheet).

### 2.5 Library organisation, recents and tags

- **On disk, folders are courses** (§7.2). In the UI you never manage folders, only courses and documents.
- **Sorting:** shelves sort by *last opened* by default (alternatively by name, or by lecture order for notes). *All documents* has a grid/list toggle and filter chips (course, kind, tag).
- **Recents** are *locations*, not files: the 20 most recent (document, page, zoom) entries. They feed Today → Continue, the empty state of ⌘K, and the editor's back/forward history, so following a card's source link and pressing *Back* returns you to the review.
- **Smart lists** (built in, not user-defined in v1): *Stuck questions*, *Flagged cards*, *Leeches* (cards failed ≥ 8 times), and *Untriaged inbox*.
- **Tags** are added from the info sheet of a document, page or card, or accepted from AI suggestions. Tapping a tag shows everything with it, across courses.

### 2.6 Search

**Decision:** one **global search panel** (⌘K, the sidebar *Search* row, or pulling down on Today). It looks like Spotlight: a field, **scope chips** (*All · Cards · Lecture notes · Sheets · Notebooks · Handwriting*) and a **course filter**. Results are grouped by kind. Each result shows a page thumbnail with the hit highlighted and a text snippet. Return opens the result at the exact page.

What gets indexed (all on device, in a rebuildable cache):

| Source | How | Quality |
|---|---|---|
| Titles, tags, bookmarks | direct | perfect |
| Card text | direct (Markdown/LaTeX source) | perfect |
| PDF text | PDFKit `page.string` | good for prose; maths in LaTeX-generated PDFs extracts as garbage, so we don't rely on it for formulas |
| Handwriting | Vision text recognition on rendered ink, per page, re-run when the page's ink changes; keeps bounding boxes for highlighting | good for words ("compact", "Sylow"), poor for symbols |
| AI transcripts | when a page or region is transcribed to LaTeX (§5), the transcript is indexed | good for maths; only covers pages AI has seen |

Extra: **Study these.** Any card-search result set can start a review session (custom study), e.g. search `#eigenvalues` → *Review 14 cards*.

### 2.7 Getting things in

- **Import:** `.fileImporter` (multiple PDFs), drag and drop from Files/Safari/Mail in a split-screen window, **Scan paper…** (VisionKit document camera, for supervisor feedback or paper notes), and **Paste** (a PDF or image on the clipboard).
- **Drop folder:** anything you put in `MathsMaster/Inbox/Import/` from the Files app or the PC turns up as *"3 files to sort"* on Today. This replaces the share extension we can't build (§8).

---

## 3. The editor: notes, PDFs and example sheets

![Editor in example-sheet mode, with the question PDF as a reference pane](mockups/03-editor.svg)

### 3.1 One page engine

**Decision:** every document is an ordered **list of pages**. Each page has:

```
Page
  id            UUID (stable; ink files and card links point here)
  size          A4 portrait by default (595 × 842 pt); a PDF page keeps its own size
  background    .pdf(sourceFile, pageIndex)  |  .template(kind, spacing, paper colour)
  ink           one PencilKit drawing (its own file), in page coordinates
  bookmarks     e.g. "Lecture 16"
  links         card IDs anchored to rects on this page
  question      (example sheets) which question this page answers
```

What this gives us for free:

- An **annotated PDF** is a page list over the original PDF. You can **insert blank or grid pages** between PDF pages (*"I need room to work through this proof"*) without touching the PDF.
- A **notebook** is a page list of template pages. You can **insert a PDF page** (e.g. a question) into it.
- An **example sheet** is a question PDF plus an answers notebook, shown side by side (§3.7).
- Exporting, printing, thumbnails, search and card links work identically for all three.

**Rendering approach (decided by a Phase-0 spike):**

- **Plan A:** `PDFView` with a `PDFDocument` built from the page list. PDF pages are copied in, and template pages are drawn by a `PDFPage` subclass. A `PDFPageOverlayViewProvider` attaches one `PKCanvasView` per visible page, with `isInMarkupMode = true` (iOS 16+). This gives zoom, continuous scroll, thumbnails, PDF text selection and search highlighting for free.
- **Plan B:** a custom `UIScrollView` page stack. Each page view is a tiled background layer (a PDF page or the template) with a `PKCanvasView` on top, recycled as you scroll.

The spike tests both on the real iPad for **ink crispness at 100–400 % zoom, latency, finger-scroll versus Pencil-draw conflicts, and a 120-page PDF**. The data model is identical for A and B, so the choice is reversible.

### 3.2 Screen layout

- **Top bar** (floating glass, about 52 pt, auto-hides while writing and returns on a finger tap or scroll-up): ‹ Course · document title and page indicator (*Q4 · p. 7 / 12*) · *Pages* (thumbnail grid) · *Reference pane* ◫ · *Bookmark* · *Link / Make card* · *AI ✨* · *Share / Print* · *More ⋯*.
- **Tool palette:** the system **`PKToolPicker`**, docked at the bottom in compact form. You can drag it to any edge, and Pencil Pro squeeze opens the mini palette at the tip (both are system behaviour).
- **Canvas:** continuous vertical scroll of pages with a 24 pt gap; zoom 50–400 %; the zoom level is remembered per document.
- **Page strip:** optional, on the right edge (13″ landscape only): small thumbnails, with question numbers in sheet mode.
- **Reference pane** ◫: open any second document (lecture notes beside your notebook, or the sheet beside your answers) at 35–45 % width. It's read-and-annotate, and resizable by dragging the divider. This is the main way to see two documents at once, and it works even when the app runs inside Playgrounds, where multiple windows may not be available (§8).

### 3.3 Toolbar contents

**Decision:** use the **system tool picker**, configured, rather than a custom toolbar. It already matches Notes, gets Apple's improvements for free, and handles squeeze, double-tap and hover correctly. Since iOS 18 it can be configured with specific items, so we ship a curated set:

| Slot | Item | Default |
|---|---|---|
| 1–3 | Pen ×3 (`PKToolPickerInkingItem`) | black 0.7 pt-ish · blue · red |
| 4 | Highlighter | yellow |
| 5 | Pencil / fountain pen (user choice) | off by default |
| 6 | Eraser | pixel eraser (switch to object in its menu) |
| 7 | Lasso | standard PencilKit lasso: move, resize, recolour, copy, delete |
| 8 | Ruler | system ruler (Pencil Pro gives haptics when snapping) |
| 9 | **Region → card** (a custom item, `PKToolPickerCustomItem`) | draw a rectangle to start a card (§3.9) |

Things that belong to the *document*, not the pen, sit in the top bar: undo/redo (also gestures), page template, insert page, bookmarks, export.

### 3.4 Pencil versus finger

| Input | Action |
|---|---|
| Pencil | **Always draws** with the current tool. Palm rejection is automatic. |
| Pencil double-tap (Pencil 2/Pro) / squeeze (Pro) | Respects the system setting (usually *switch to eraser* / *show palette*). Pencil Pro barrel roll rotates the reed/fountain nib (PencilKit does this automatically). |
| Pencil hover | Shows the tool preview (system behaviour). |
| 1 finger | Scrolls, and taps to toggle the chrome. Never draws, unless *Draw with finger* is switched on in ⋯. Off by default; when the Pencil isn't paired, the app offers to switch it on. |
| 2-finger pinch / drag | Zoom / pan |
| **2-finger tap** | Undo (GoodNotes/Notability convention) |
| **3-finger tap** | Redo |
| Finger long-press on PDF text | Selects text (copy, search, *Make card from text*) |
| Keyboard | ⌘Z / ⇧⌘Z, ⌘F find in document, ←/→ or PgUp/PgDn change page, ⌘B bookmark |

Implementation rules: canvases use `drawingPolicy = .default` (the system respects the Pencil-only setting), and there's a single document-level `UndoManager` so undo works across pages.

### 3.5 Pages and templates

- **Paper:** A4 portrait by default (UK printing). A4 landscape and *Infinite* (a tall page for brainstorming, which prints split across pages) are also available.
- **Templates (v1):** Blank · **Dot grid 5 mm (default)** · Squared 5 mm · Narrow ruled 7 mm with margin · **Answer sheet** (header fields *Course / Sheet / Q*, 5 mm squares, and a 30 mm right margin for supervisor comments). Paper colour can be white, cream or **dark**. Dark paper shows light ink on screen and still exports and prints as black on white.
- **Template lines are drawn by the app, not baked into the page.** That's why *print without lines* is possible (§3.8).
- **Page operations** (Pages grid or the page's context menu): insert before/after (template or a PDF page) · duplicate · move (drag in the grid) · delete (to Trash) · change template · bookmark · rotate (PDF pages).
- **Real size:** a 13″ Air in portrait shows A4 at fit-width at about **94 % of real size**; an 11″ shows it at about **76 %** (screen widths of about 197 mm and 158 mm against A4's 210 mm). So the default zoom is *fit width* and you can zoom in to write small. A "margin-to-margin" double-tap zoom is planned for the 11″.

### 3.6 PDF specifics (lecture notes)

- **Sidecar storage:** `LA notes.pdf` ↔ `LA notes.pdf.ink/` (page list, one drawing file per page, bookmarks). The original PDF is never rewritten.
- **The lecturer updates the notes:** *Replace PDF…* keeps your ink and matches pages by index. If the page count changed, a page-offset tool appears (*"Your ink from p. 40 onwards: shift by +2"*). This is common mid-term and must not lose work.
- **The PDF's own outline and links** (from LaTeX `hyperref`) work, and the outline is merged into the Bookmarks list.
- **Text highlight:** everything is ink, including the highlighter. A long-press text selection is only for copy, search and cards. This keeps one mental model.

### 3.7 Example-sheet mode

An example sheet is the most-used document during term, so it gets a dedicated layout (mockup 03):

- **Left:** the question PDF in the reference pane. **Right:** your answers notebook (*Answer sheet* template).
- **Question navigator:** questions are auto-detected from the PDF's text (`1.`, `2.`, `3.` at line starts, with their positions) and can be fixed by hand. Tapping *Q4* scrolls the questions to Q4 and the answers to the first page tagged Q4, creating one if needed.
- **Per-question status:** *Not started · Attempted · Done · ⚑ Stuck*, set with one tap from a pill in the top bar. These statuses drive *Today → Up next* and the course page chips.
- **Supervision date** per sheet (drives Up next) and **Feedback:** attach the supervisor's marked PDF or a scan, which opens in the reference pane.
- **Hand-in export:** answers in question order, a header with name, course and sheet, optionally without template lines, and the file name `Surname, Linear Algebra Sheet 3.pdf`. One tap to share or save to `Exports/`.

### 3.8 Printing and PDF export

- **Print** (`UIPrintInteractionController`, AirPrint) and **Export PDF** share one options sheet: pages (all / current / range / questions) · *include template lines* (default **off** for notebooks; dots and grids become invisible on paper) · *include highlighter* · *ink colour: as drawn / all black* · *header and page numbers* · 1-up / 2-up.
- **Rendering:** the background is drawn as vector (the PDF page or the template). Ink is first rasterised at **300 dpi** from `PKDrawing.image(from:scale:)`, which is crisp on paper and simple. A later polish step renders ink as **vector paths from `PKStroke`** (tapered outlines) for tiny files and infinite zoom.
- Exports go to the share sheet *and* to `MathsMaster/Exports/`, which also appears on the Windows PC through iCloud for Windows, so you can print from there too.

### 3.9 Linking regions to cards

**Decision:** cards can point at a place, and places show their cards.

- **Making one:** the *Region → card* tool, or lasso → *Make card*. Draw a rectangle over a theorem in the lecture notes or over your handwritten working. A sheet opens with three options:
  - **Image card:** the region becomes the card front or back (a snapshot at 2×).
  - **Occlusion card** (Phase 5): draw masks over parts of the region, one card per mask.
  - **Transcribe** ✨: AI turns the region into Markdown + LaTeX and pre-fills a typed card, with the image kept as a fallback.
- **Anchor:** `{documentID, pageID, rect}` in page coordinates, so it survives zoom, reflow and renames.
- **On the page:** a small **card badge** in the margin beside each anchored rect (*🂠 2*). Tap it to preview those cards, edit them, or review them now.
- **On the card:** a **Source** chip (*Linear Algebra notes · p. 61*). Tapping it opens the editor at that page with the rect briefly highlighted, and *Back* returns to the review.

### 3.10 Ink-quality checklist (acceptance criteria for every editor change)

- [ ] Pencil-to-ink latency and smoothness are indistinguishable from Apple Notes side by side on the iPad Air (60 Hz, no ProMotion; rely on PencilKit's prediction and never block the main thread during a stroke).
- [ ] No canvas is ever recreated by a SwiftUI update. Canvases live in UIKit and are wrapped once, with stable identity, and `updateUIView` never reassigns `drawing` while you're writing.
- [ ] Autosave is debounced (about 2 s after the last stroke ends, and on page change, backgrounding and close). Encoding happens on the main actor and writing is coordinated off it.
- [ ] Ink stays crisp at 400 % zoom. Strokes are stored in page coordinates (1 pt = 1/72 in), whatever the zoom.
- [ ] Canvases on white paper force `overrideUserInterfaceStyle = .light`, because in dark mode PencilKit otherwise inverts black ink to white.
- [ ] Drawings load lazily (visible pages ±2). Scrolling a 120-page annotated PDF holds 60 fps.
- [ ] Scribble is disabled over canvases, and system edge gestures don't steal Pencil strokes that start near an edge.

---

## 4. Flashcards

### 4.1 Card model and types

```
Card
  id, courseID (= deck), kind, label
  front, back, extra      Markdown + LaTeX ($…$ inline, $$…$$ display)
  frontInk?, backInk?     optional PencilKit drawings (handwritten sides)
  image?                  region snapshot (image and occlusion cards)
  masks?                  occlusion rects (Phase 5)
  source?                 anchor {documentID, pageID, rect?}
  lecture?                integer, e.g. 16 (filled automatically from bookmarks when made from a page)
  tags[], flagged, suspended
  origin                  you | gemini | claude (+ job ID)
  createdAt, updatedAt, deletedAt?   (tombstones for sync)
```

- **Kinds:** *Basic* · *Basic + reversed* (definitions both ways) · *Cloze* (`{{c1::…}}`) · *Image* (a region from notes) · *Occlusion* (Phase 5).
- **Labels** (maths-specific, for colour and filtering, with no behaviour of their own): *Definition · Theorem · Proof idea · Example / Counterexample · Formula · Technique*. The AI is asked to produce these, and the review screen shows them as a small chip.
- **Handwriting on cards: yes, but typed is primary.** Typed LaTeX is searchable, editable by AI and scales to any size. Ink sides exist for diagrams and for when you can't be bothered to typeset; AI can transcribe them later. Image cards keep a direct link to your notes.

### 4.2 Decks and queues

- **One deck per course**, and nothing nested. Where you might want sub-decks, use filters instead: *lectures 1–8*, *label = Theorem*, *tag = #compactness*, *flagged*.
- **The global queue** (Today → *Start review*, Cards → *Review all*) **interleaves courses**: learning cards that are due come first, then reviews ordered by lowest retrievability, round-robin across courses so that you never get 40 Methods cards in a row (interleaving helps learning), with new cards spread evenly through the session.
- **The queue is term-aware.** New cards are introduced for **current-term courses**. Past-term courses get reviews only, unless you explicitly *Learn new* in them, so the Christmas vacation doesn't flood you with new Michaelmas cards next to Lent's.
- **Custom study:** any filter or search result can start a session (*Review 14 cards tagged #eigenvalues*, *Cram lectures 13–16*). Cram sessions don't affect scheduling unless you choose to let them.

### 4.3 Review flow

![Card review: write first, then reveal](mockups/04-review.svg)

1. **The session opens full screen** (the sidebar slides away). The top bar shows × End · scope (*All courses*) · a thin progress bar · *New 3 · Learning 5 · Review 56* · ↶ Undo · ⋯.
2. **The card** sits centred, at most 760 pt wide. It shows a course-colour chip and label (*Linear Algebra · Theorem · L19*), then the front, typeset at 26 pt.
3. **The scratch area:** the rest of the card surface below the question is a Pencil canvas with the hint *Write your attempt*. Just start writing. It's cleared for the next card. *Write first* mode (a setting) hides the *Show answer* button until you've written something.
4. **Reveal** (the *Show answer* button, Space, or a finger tap outside the scratch area): **the answer slides in below your attempt**, so you compare like with like. *Extra* (proof sketch, notes) starts collapsed. There's no 3D flip: maths answers need you to see the question and the answer together.
5. **Grade:** four buttons in a glass bar, **Again · Hard · Good · Easy**, each showing the next interval (*<10m · 2d · 6d · 14d*). Again and Good are visually dominant (most reviews are one of the two). Keys 1–4; Space = Good after reveal. There are no swipe-to-grade gestures, because accidental grades are worse than one extra tap.
6. **The side rail** (right of the card): **✨ Explain** (AI side panel, §5) · **↗ Source** (jumps to the page; *Back* returns) · **✎ Edit** (in-place editor; the session continues) · **⚑ Flag** · ⋯ (suspend, bury, delete, copy LaTeX).
7. **The end card:** time spent, cards reviewed, retention today, the streak, *Review the 6 you failed again?*, and *What's due tomorrow*.

Small things that matter: grading an image card zooms the region to fill the card; **undo** restores the previous card *and* its scratch ink; leaving mid-session keeps your place for an hour; every review records its duration (for stats; FSRS doesn't need it).

### 4.4 Card editor

![Card editor with live preview, and AI inbox triage](mockups/05-cards.svg)

- **Layout:** fields on the left (*Front*, *Back*, *Extra*), a **live KaTeX preview** on the right (side by side on 13″ and landscape; stacked with a preview toggle on 11″ portrait).
- **The LaTeX accessory bar** above the keyboard: `$ $`, `$$ $$`, `\mathbb{}`, `\forall`, `\exists`, `\to`, `\subseteq`, `^{}`, `_{}`, `\frac{}{}`, `\sum`, `\int`, `\begin{pmatrix}`, `cases`, plus your own snippets. Errors show inline in the preview (red source span) and never as a blank card.
- **Write it** ✍︎: a Pencil pad that opens in place. Write the formula by hand, and ✨ transcribes it to LaTeX, inserts it at the cursor, and shows the rendering to confirm. Scribble in the text fields also works for plain words, for free.
- **Metadata row:** course, kind, label, lecture, tags, source (with *Pick region…*).
- **AI edit strip:** *"Ask AI to change this card…"* (§5).

### 4.5 The Inbox (AI triage)

Everything AI generates arrives in the **Inbox**, grouped by job (*"Linear Algebra, lectures 13–16 · 18 cards"*). Nothing enters a deck until you accept it.

- Each card shows its rendered front and back, label, tags, source thumbnail and a **possible duplicate** warning (text similarity to existing cards in the deck).
- Actions: **Accept** (A or →) · **Edit** (E) · **Reject** (R or ←) · **Accept all remaining**. Accepted cards go into the deck as *new*. Rejections are kept (for 30 days) to improve future prompts (*"don't make cards like these"*).

### 4.6 Scheduling

- **FSRS-6** with default parameters and **desired retention 0.90**. One learning step (10 min) and one relearning step (10 min); FSRS handles the rest, including same-day reviews. We vendor a Swift port of the open-source reference implementation as source (no dependency risk, §8).
- **Card state is derived, not stored:** it's a fold over the append-only review log (§7.4). It's cached for speed and is always reproducible.
- **Defaults:** 15 new cards a day in total (split across current-term courses by their backlog), no review cap (a warning appears above 200), interval fuzz and load balancing on, siblings buried until the next day, **leech** at 8 lapses (flagged, not suspended, shown in *Leeches* with *Fix with AI*).
- **Exam mode:** set the exam start date (default: the first Monday of June, editable). In the last 6 weeks, intervals are capped so every card comes round at least once before the exam, and desired retention rises to 0.93 for current-year courses.
- **Optimiser:** after about 1,000 reviews, the VPS runs the official FSRS optimiser on the review log and offers new parameters (*"predicted to save 12 % of your time"*). Phase 5.

### 4.7 Stats

Swift Charts, one scrolling page, filterable by course:

1. **Heatmap**: reviews per day for the year (GitHub-style), plus the streak.
2. **Due forecast**: bars for the next 30 days.
3. **True retention** by course over the last 30 days, against the 90 % target line.
4. **Maturity**: new / learning / young / mature stacked bars per course.
5. **Time**: minutes per day, and average seconds per card.
6. **Exam readiness** ★: *predicted recall on 1 June* per course. FSRS can compute each card's retrievability at a future date, so this is the share of cards above 90 % on exam day *if you keep reviewing*. It's the number a Tripos student actually cares about.
7. **Hardest cards**: leeches and cards with the highest difficulty, with *Fix with AI* (split or rewrite).

---

## 5. Where AI fits in the UI

### 5.1 Principles

1. **AI is a verb on your content.** It appears as a ✨ action *next to* the thing it acts on: a region, a card, a lecture range. There's no separate "AI chat" tab.
2. **Everything goes through review.** Generated cards land in the **Inbox**. Edits show as a **diff** with *Accept / Reject*. AI-made content keeps an *origin* badge until you've edited or accepted it.
3. **Cheap and instant where it can be; batch where it's big.** Small interactive tasks use Gemini directly from the iPad. Turning whole lectures into cards runs as a job on the VPS with Claude Code.
4. **It degrades gracefully.** Offline: the action queues (*"will run when you're online"*). Daily quota hit: *"Gemini's free limit is used up for today. Send this to the VPS queue instead?"* Bad output: one automatic retry, then the raw text is shown.

### 5.2 AI surfaces

| Where | Action | Result | Engine |
|---|---|---|---|
| Editor: region / lasso | ✨ **Make cards** | 1–5 suggested cards in a sheet (accept inline) or sent to the Inbox | Gemini, vision |
| Editor: region / page | ✨ **Transcribe** | Markdown + LaTeX of your handwriting or of the PDF region; copy, use as a card, and it's indexed for search | Gemini, vision |
| Editor: region / page | ✨ **Explain** | Side panel with an explanation and follow-up chips | Gemini |
| Review (after reveal) | ✨ **Explain** | Side panel. Chips: *Why is this true? · Example · Counterexample · Common mistakes · Simpler*. *Save to Extra* keeps the answer on the card. | Gemini |
| Card editor | **Ask AI to change…** | Structured patch → diff → Accept (*"split into two cards"*, *"use $\ker$ notation"*) | Gemini (light model) |
| Card editor | ✍︎ **Write it** | Handwritten formula → LaTeX at the cursor | Gemini, vision |
| Course page / outline / notes | ✨ **Generate cards from lectures 13–16…** | Batch job → VPS → Claude Code → Inbox (with a notification badge) | Claude Code (VPS) |
| Leeches / hardest cards | **Fix with AI** | Rewrite or split suggestions → Inbox | Gemini or Claude |
| Inbox | (automatic) | Tag suggestions, duplicate warnings | local + Gemini |

### 5.3 Engines, keys and quotas

- **Gemini (instant).** You paste your own API key into *Settings → AI*. It's stored in the **Keychain** of that app copy and is never in the repo (the repo is public) or in the synced folder. Models are chosen per task from a list fetched from the API (a vision-capable *Flash* model for transcription and cards; a *Flash-Lite* model for text edits and explanations), because the free lineup changes often. **The free tier is small and shrinking.** Late-2026 reports put it at about 20 requests a day on the top Flash model and a few hundred a day on Flash-Lite, counted per Google Cloud project, and free-tier prompts may be used by Google to improve its products. So the app shows a **"today's AI budget" meter**, routes text-only work to the light model, and never spends requests in the background.
- **On-device model (opportunistic).** The iOS 26 SDK has Apple's Foundation Models framework and the M4 Air supports Apple Intelligence, but forum reports say it's unavailable in Playgrounds builds. If it works in the SideStore build, it takes over *text-only* edits (rephrase, split, tag) for free and offline. We never depend on it.
- **Claude Code (batch).** It runs **on the VPS**, logged in with your subscription on the server. The app never sees that credential. The app talks to a small job API on the VPS with a per-device token (§7.7). It **won't** use GitHub Actions for this: the repo is public, so workflow logs and artifacts would expose your notes.
- **Prompts are files in the repo** (`Resources/Prompts/*.md`): a card style guide (atomic, one idea per card, the course's notation, `$…$` LaTeX, a label on each card, ≤ 40 words a side) plus JSON output schemas. Better cards are a PR away.
- **Context sent with requests:** course name, nearby page text, bookmarks (lecture number), and the deck's existing card fronts (to avoid duplicates). Nothing else.

### 5.4 Batch job flow

```
iPad (app)                          VPS                               iPad (app)
──────────                          ───                               ──────────
Select lectures 13–16 ──render──▶  POST /v1/jobs (flattened PDF of   ◀── poll on launch/foreground
pages with ink to one PDF           the pages + course + instructions)    GET /v1/jobs/{id}
                                    queue → `claude -p` worker reads       → cards JSON → Inbox/
                                    the PDF, writes cards JSON,            → badge "18 cards ready"
                                    validates against the schema
```

---

## 6. Visual design

### 6.1 Personality

*A well-made notebook on a good desk.* Warm paper neutrals, real ink colours, typeset maths, and one accent. Chrome recedes; content (pages, cards) is the brightest thing on screen. It follows iPadOS 26 conventions, so it feels native next to Notes and Files.

### 6.2 Typography

| Use | Face | Notes |
|---|---|---|
| UI chrome | **SF Pro** (system), Dynamic Type text styles | Large titles (34 pt bold) only on top-level pages (Today, course pages) |
| Numbers (due counts, stats, streak) | **SF Pro Rounded**, monospaced digits | `fontDesign(.rounded)` + `monospacedDigit()` so counts don't jiggle |
| Card text and all typeset maths | **KaTeX fonts (Computer Modern look)** for *both* text and maths | Cards read like the lecture notes. Base size 24 pt on 11″, 26 pt on 13″, following Dynamic Type |
| LaTeX source in the editor | **SF Mono** | With light syntax colouring: commands, braces, `$` delimiters |

### 6.3 Colour

Tokens, defined once in the asset catalog with light and dark values:

| Token | Light | Dark | Use |
|---|---|---|---|
| `bg` | `#F4F2EE` warm paper grey | `#121214` | window background |
| `surface` | `#FFFFFF` | `#1C1C1F` | cards, sheets, sidebar |
| `surface-2` | `#EEEBE5` | `#26262A` | wells, inactive chips |
| `ink` (text) | `#1C1B19` | `#F2F1EE` | primary text |
| `ink-2` | `#6B6862` | `#A3A09A` | secondary text |
| `line` | `#E2DED6` | `#34343A` | separators |
| `accent` | `#1F7F74` teal | `#5CC8B8` | selection, primary buttons, links |
| grade colours | Again `#E5484D` · Hard `#E8930C` · Good `#2E9E62` · Easy `#3B7BF5` | same hues, lifted for dark | always paired with labels, never colour alone |

**Course colours:** each course picks one of 12 harmonious, muted hues (indigo `#5B6CF0`, teal `#1F9E8F`, amber `#D69A00`, coral `#E0645A`, violet `#9A5BD8`, sky `#2F9BDB`, green `#4AA35A`, rose `#D9578A`, slate `#5F7389`, orange `#E07B2E`, olive `#8C9A2E`, plum `#8E4F7A`). The colour appears as the sidebar dot, the course header band, the card chip and the document thumbnail edge, and nowhere larger. The Part IB template pre-assigns distinct colours.

**Ink defaults:** black `#1A1A1A`, blue `#1E4FD8`, red `#D7263D`, green `#13865B`, highlighter yellow `#FFE45C` at about 40 %.

### 6.4 Dark mode

- **The UI is fully dark.** **Paper stays white by default** (lecture PDFs are white, and ink colours should look like ink), with a slightly dimmed page edge so it isn't a lightbox.
- **Canvases on white paper are forced to the light style.** Otherwise PencilKit's automatic dark-mode adaptation renders black ink as white.
- **Dark paper** (a notebook setting) lets PencilKit adapt the ink, and templates draw in light grey. Ink is stored in its light-mode colours, so **export and print are always black on white**.
- Cards in dark mode: a dark surface, KaTeX in light ink, and grade colours lifted for contrast.

### 6.5 Motion and feedback

- **Springs everywhere** (≈ 0.35 s response, 0.85 damping). Nothing bounces more than once.
- **Thumbnail → editor** uses the zoom transition. **Answer reveal**: the answer fades in and rises 12 pt (180 ms). **Grade**: the card slides left and fades as the next card comes in from the right (220 ms). Counts tick with a numeric content transition.
- **Liquid Glass** (iOS 26 SDK) only on *floating* controls over content: the editor top bar, the tool palette, the grade bar and the side rail. It's never used for content surfaces or behind text you read.
- **Haptics:** the iPad itself has no haptic engine. **Pencil Pro haptics** (`UICanvasFeedbackGenerator`) fire for ruler snapping, lasso selection and dropping a page in the page grid.
- **Reduce Motion** swaps slides for cross-fades. **Reduce Transparency** swaps glass for solid surfaces.

### 6.6 Gestures and keyboard

| Where | Gesture / key | Action |
|---|---|---|
| Everywhere | ⌘K | Search |
| Everywhere | ⌘1 / ⌘2 / ⌘3 | Today / Cards / Inbox |
| Everywhere | ⌘N · ⇧⌘N · ⌘O | New notebook · New card · Import PDF |
| Everywhere | swipe from the left edge / ⌘[ | Back |
| Library | pinch on a shelf | Change thumbnail size |
| Library | drag a document onto a course in the sidebar | Move it to that course |
| Editor | 2-finger tap / 3-finger tap | Undo / Redo |
| Editor | ⌘F · ⌘B · ⌘P | Find in document · Bookmark page · Print |
| Editor | drag a lasso selection onto the Inbox or a card badge | Make a card from it |
| Review | Space · 1–4 · ⌘Z · E · S | Reveal (or Good) · Grade · Undo · Edit · Source |
| Inbox | → / A · ← / R · E | Accept · Reject · Edit |

All shortcuts are declared through SwiftUI `.commands` / `.keyboardShortcut`, so they appear in the iPadOS 26 menu bar and in the ⌘-hold overlay.

### 6.7 11″ versus 13″, orientation

| | 11″ (1180 × 820 pt) | 13″ (1366 × 1024 pt) |
|---|---|---|
| Landscape library | sidebar 280 + 2–3-column shelves | sidebar 300 + 3-column shelves |
| Portrait library | sidebar as overlay, 2-column shelves | sidebar as overlay, 3-column shelves |
| Editor, landscape | one page at fit width, reference pane 35 % | two-page spread *or* reference pane 40 % + page; page strip visible |
| Editor, portrait | one page at fit width (A4 at 76 % of real size) | one page at fit width (A4 at 94 %), close to writing on paper |
| Review | card fills the width with margins; side rail becomes a bottom row | card 760 pt centred, side rail on the right |

![11″ portrait: Today and the editor at narrow width](mockups/06-compact.svg)

### 6.8 Stage Manager, windowing and multitasking

- **iPadOS 26 lets windows be any size**, so we design by *width breakpoints* (§2.2), not by device. The minimum supported width is about 375 pt, where everything collapses to a stack. The editor and review screens never assume a full screen.
- **Two documents at once:** the built-in **reference pane** is the primary answer. It works in every mode, including inside Playgrounds.
- **Multiple windows** (e.g. lecture notes in one window, the notebook in another) are a bonus for the SideStore build, *if* the multi-scene Info.plist key survives (§8). The app must not depend on it.
- **Drag and drop between apps** (PDFs in from Files/Safari/Mail; exported PDFs and card images out) works in every mode, because it needs no extension.

### 6.9 Accessibility

Dynamic Type across all chrome; VoiceOver labels on every control; KaTeX also produces MathML, so typeset cards read aloud; state is never shown by colour alone; hit targets ≥ 44 pt, and grade buttons ≥ 64 pt tall.

---

## 7. Data model, storage and sync

### 7.1 Principle: files are the truth, everything else is a cache

**Decision:** the source of truth is a **plain folder of human-readable files** in iCloud Drive (`iCloud Drive › MathsMaster`). You pick it once in each app copy through the document picker, and the app keeps a **security-scoped bookmark** to it. Everything else is derived and disposable: in-memory models, thumbnails, the search index, cached FSRS state, rendered KaTeX snapshots.

Why not SwiftData, Core Data or SQLite as the store?

- **CloudKit sync needs an iCloud entitlement.** Playgrounds can't add one, and neither can a free Apple ID (§8).
- **A SQLite file inside an iCloud Drive folder is a known way to corrupt data.** The database and its WAL sync separately, and two app copies write to it.
- **At our scale, memory is enough.** About 5,000 cards (~4 MB of JSON) load in well under a second on an M4. A database can be added later purely as a cache, e.g. full-text search, if it's ever needed.
- **Files are inspectable.** You can see and back up your work from the Files app or the Windows PC, and the app being broken never means your work is unreachable.

### 7.2 Folder layout

```
MathsMaster/                               ← the folder you pick (iCloud Drive)
├── library.json                           years, terms + dates, courses (id, name, colour, folder), schemaVersion
├── settings.json                          shared, non-secret settings (scheduler, templates, AI model choices)
├── devices.json                           install IDs → names ("iPad · Playgrounds", "iPad · SideStore")
├── Courses/
│   └── Linear Algebra/
│       ├── course.json                    id, exam date, outline cache
│       ├── Lecture notes/
│       │   ├── LA notes 2026.pdf          the original, never modified
│       │   └── LA notes 2026.pdf.ink/
│       │       ├── document.json          page list, bookmarks, card links, last position
│       │       └── pages/<pageID>.drawing one PKDrawing per page
│       ├── Example sheets/
│       │   ├── Sheet 3.pdf
│       │   └── Sheet 3.sheet/             document.json (+ questions, statuses, supervision date),
│       │                                  pages/*.drawing, feedback/*.pdf
│       ├── Notebooks/
│       │   └── Lecture 16 working.mmnote/ document.json, pages/*.drawing
│       ├── cards.json                     the course deck
│       └── cards-media/<cardID>.png|.drawing
├── Reviews/<installID>/2026-11.jsonl      append-only review log (one file per app install per month)
├── Inbox/Import/                          drop PDFs here from Files or the PC
├── Inbox/jobs/<jobID>.json                AI card batches + triage state
├── Exports/                               hand-ins and print PDFs
├── Logs/<installID>.log                   rolling diagnostics (there's no Xcode console, §8)
└── .trash/                                deleted items, purged after 30 days
```

- **IDs, not paths, are identity.** Every course, document, page and card has a UUID. Folder and file names are just for humans, so renaming in the app (or in Files) never breaks a link. On launch the app rebuilds an `ID → path` index by scanning.
- **Every JSON file carries a `schemaVersion`.** Migrations run on load and write back lazily.
- **The local cache** (`Library/Caches/` in each app copy's own sandbox) holds thumbnails, OCR text and boxes, the search index, FSRS state, and KaTeX snapshots. It's always safe to delete.

### 7.3 Main records (shape only)

```jsonc
// library.json
{ "schemaVersion": 1,
  "years": [{ "id": "…", "name": "Part IB 2026–27",
              "terms": [{ "name": "Michaelmas", "start": "2026-10-06", "end": "2026-12-04" }, …] }],
  "courses": [{ "id": "…", "name": "Linear Algebra", "term": "Michaelmas", "year": "…",
                "colour": "indigo", "folder": "Courses/Linear Algebra", "lectures": 24 }] }

// Reviews/<installID>/2026-11.jsonl — one line per review, never rewritten
{"id":"…","card":"…","t":"2026-11-22T09:14:03Z","rating":3,"ms":8400,"session":"…"}
```

### 7.4 Reads, writes and change detection

- **All file I/O goes through one `FileStore` actor**, using `NSFileCoordinator` for coordinated reads and writes. Each write goes to a temp file, then an atomic replace.
- **Autosave** is debounced (ink: about 2 s after a stroke ends; cards: on field blur). Everything flushes when the app is backgrounded, using `beginBackgroundTask` (about 30 s, no entitlement needed).
- **Evicted iCloud files:** a coordinated read triggers the download, and the UI shows a ☁︎ placeholder with progress meanwhile. Setup tip shown on first run: in Files, long-press *MathsMaster → Keep Downloaded*.
- **Seeing changes from elsewhere:** `NSMetadataQuery` is off the table (it needs an iCloud container entitlement). Instead the app rescans modification dates on launch and on returning to the foreground (cheap), polls every 30 s while active, and uses an `NSFilePresenter` for the document that's open (verify in the spike).

### 7.5 Conflicts

| Data | Strategy |
|---|---|
| Review logs | **Can't conflict:** one file per install per month, append-only. Card state = all logs merged and sorted by time, then folded through FSRS. |
| `cards.json` | Per-card `updatedAt`, and the newest wins *per card*. Deletions are tombstones (purged after 60 days). iCloud conflict copies (`cards 2.json`) are detected, merged card by card, and removed. |
| Ink pages | One file per page, so a conflict needs the *same page* edited in two places. The newer one is kept and the older goes to `.trash/conflicts/`, with a banner: *"Page 7 was edited in two places. Compare?"* |
| `document.json`, `library.json` | Merged by ID. Unknown pages or courses are appended, never dropped. |
| Same library open in both app copies | Each copy writes a heartbeat file (`.open-<installID>`). If another copy's heartbeat is fresh, a quiet banner appears: *"Also open in the SideStore copy. Avoid editing the same page in both."* |

### 7.6 Two app copies (Playgrounds and SideStore)

- **Each copy has its own sandbox, bookmark and Keychain.** So: a one-time *Choose library folder* screen in each, a Gemini key and VPS token entered in each (both are in the Keychain and never synced), and an `installID` per copy.
- **Everything else is shared through the folder,** including non-secret settings, so both copies behave identically.
- The **first-run screen** explains this in one paragraph and offers *Create a new MathsMaster folder* or *Open existing*.

### 7.7 The VPS: backup and AI jobs (Phase 4)

A small HTTPS service (behind Caddy) with a per-device bearer token:

| Endpoint | Purpose |
|---|---|
| `GET /v1/manifest` · `PUT/GET /v1/files/{path}` | **Backup mirror**: the app uploads changed files (content hash; debounced; optionally Wi-Fi only). The server takes nightly snapshots (e.g. restic, 90 days). *Settings → Backups → Restore* always restores into a **new** folder, never over your library. |
| `POST /v1/jobs` · `GET /v1/jobs/{id}` | **AI batch jobs** (§5.4): the upload is a flattened PDF plus a JSON request. A worker runs Claude Code headless, validates the cards JSON, and the app fetches it into `Inbox/jobs/`. |
| `POST /v1/fsrs/optimize` | (Phase 5) runs the FSRS optimiser on uploaded review logs. |

The VPS is deliberately **not** the live sync: iCloud Drive already syncs files between the two app copies and the PC, and works offline. If iCloud storage is a problem (open question 1), the same folder layout can be synced to the VPS instead.

### 7.8 Scale (one year of Part IB)

About 15 courses · 30 lecture PDFs (1–10 MB each) · 60 example sheets · 1,500 handwritten pages (50–200 KB each) · 3,000–5,000 cards (4 MB) · 50,000 reviews (5 MB). That's **roughly 0.5–1 GB a year**, mostly PDFs and ink.

---

## 8. What Swift Playgrounds can and can't do (and the workarounds)

**Baseline (as of Nov 2026):** Swift Playground **4.7** (17 Mar 2026) ships **Swift 6 and the iOS 26 SDK**. It hasn't been updated for the iOS 27 SDK yet, even though iPadOS 27 is out. App projects are `.swiftpm` packages using the `AppleProductTypes` `.iOSApplication` product. **Key: ✅ works · ⚠️ works with a workaround, or needs a check on the device · ❌ not possible.**

| Capability | Status | How we handle it |
|---|---|---|
| SwiftUI, UIKit via representables, Swift concurrency, Observation | ✅ | The core stack. Canvases and the PDF view are UIKit, wrapped once. |
| **PencilKit** (`PKCanvasView`, `PKToolPicker`, iOS 18 configurable tool items, iOS 26 reed pen) | ✅ | The ink engine (§3). |
| **PDFKit** (`PDFView`, overlay view provider, markup mode, text, PDF generation) | ✅ | Page engine plan A, export. |
| PaperKit (iOS 26: Apple's markup with shapes, text boxes, images) | ⚠️ in the SDK | Deferred. We may adopt it for text boxes and shapes after v1. |
| Vision (text recognition, incl. handwriting) · VisionKit document camera | ✅ | Handwriting search, *Scan paper*. The camera needs the **Camera** capability (Playgrounds' *App Settings → Capabilities* adds the usage string). |
| WebKit (`WKWebView`) | ✅ | KaTeX rendering. KaTeX's JS, CSS and fonts are bundled as resources and loaded with `loadFileURL(_:allowingReadAccessTo:)`. |
| Swift Charts | ✅ | Stats. |
| SwiftData | ✅ | Not used as the store (§7.1); possible cache later. |
| Foundation Models (on-device LLM) | ⚠️ | In the iOS 26 SDK, but reported as unavailable in Playgrounds. Optional, never relied on (§5.3). |
| **iCloud container, CloudKit, `NSUbiquitousKeyValueStore`, `NSMetadataQuery`** | ❌ | All need an iCloud entitlement, which Playgrounds can't add and a free Apple ID can't sign. **Workaround: a user-picked iCloud Drive folder** (next row). |
| **Document picker folder access + security-scoped bookmark** | ✅ | `.fileImporter(allowedContentTypes: [.folder])` → `startAccessingSecurityScopedResource()` → `bookmarkData()`. Resolved each launch; re-prompt if stale. *Check that the bookmark persists across Playgrounds runs (spike).* |
| `NSFileCoordinator` on iCloud Drive files (triggers downloads) | ✅ | All I/O (§7.4). |
| App Groups, Keychain sharing | ❌ | The two copies can't share secrets, so keys are entered in each (§7.6). |
| **App extensions** (widgets, share extension, Quick Look, File Provider, Live Activities) | ❌ | No "due cards" widget. Instead: drag and drop, the `Inbox/Import/` drop folder, local notifications. |
| Custom Info.plist keys (document types, multi-window, background modes) | ⚠️ | `additionalInfoPlistContentFilePath` in `Package.swift` works when **CI/Xcode** builds the app (the SideStore build). Playgrounds has historically **dropped** it whenever it rewrote the manifest. Nothing essential may depend on it. |
| Background execution (`BGTaskScheduler`) | ⚠️ | Needs Info.plist keys, so SideStore build only and optional. We don't need it: AI batch runs on the VPS, and `beginBackgroundTask` (✅) is enough to finish saves. |
| Push notifications | ❌ | Needs an entitlement. Not needed. |
| Local notifications (daily "cards due" reminder) | ✅/⚠️ | Standard `UNUserNotificationCenter`. Check that delivery works when run from Playgrounds; it's fine in the SideStore build. |
| Multiple windows (scenes) | ⚠️ | Depends on the Info.plist key above. The in-app reference pane covers the need everywhere. |
| Menu bar commands, keyboard shortcuts, pointer | ✅ | `.commands`, `.keyboardShortcut`. |
| Apple Pencil Pro squeeze, double-tap, hover, barrel roll, haptics | ✅ | System tool picker + `UIPencilInteraction` / SwiftUI `onPencilSqueeze` / `onPencilDoubleTap` (17.5+) + `UICanvasFeedbackGenerator`. |
| Swift packages from Git | ✅/⚠️ | Source packages work. **Avoid packages with macros, build plugins or binary targets** (third-party macro plugins aren't reliable in Playgrounds). We vendor small libraries (the FSRS port) as source. Target: **≤ 2 external packages.** |
| Resources (`Resources/`, asset catalog, app icon, accent colour) | ✅ | Access processed resources with `Bundle.module`. |
| Custom fonts in native UI | ⚠️ | No `UIAppFonts`; register at runtime with `CTFontManagerRegisterFontsForURL`. We barely need it: native UI uses SF, and KaTeX fonts load through CSS inside the web view. |
| Networking (`URLSession`), Keychain, printing (`UIPrintInteractionController`) | ✅ | Gemini, VPS, print. |
| Debugger, crash logs | ⚠️ minimal | Built-in **Diagnostics** screen: a log viewer, a "last session ended cleanly?" breadcrumb, and *Export logs*. Logs are also written to `Logs/` in the library so they can be attached to a bug report. |
| Optimised builds | ⚠️ | Playgrounds builds for development (unoptimised). Ink and PDF rendering are system code, so they're unaffected. The SideStore build from CI is a Release build. |

**Build and CI rules that follow from this:**

1. **CI compiles with Xcode 26.x (the iOS 26 SDK), the same SDK as Playground 4.7.** If CI used Xcode 27, code calling iOS 27 APIs would pass CI and then fail to build on the iPad. The deployment target is **iPadOS 26.0**.
2. CI runs `xcodebuild … -destination 'generic/platform=iOS Simulator' build` on every PR. A second job archives an **unsigned Release `.ipa`** (`CODE_SIGNING_ALLOWED=NO`) as an artifact for SideStore to sign with your free Apple ID. That means 7-day re-signing (SideStore refreshes it automatically) and a limit of 3 apps / 10 App IDs a week, which is fine for one app.
3. **Keep files small and type-checking cheap.** Playgrounds recompiles the whole module on the iPad. Avoid giant view bodies and deeply nested generic builders.
4. **Leave `Package.swift` to code, not to Playgrounds' settings UI.** Change capabilities in the repo, so Playgrounds never rewrites the manifest and drops keys.

---

## 9. Roadmap

Each milestone ends with something **you can run on the iPad from Playgrounds** and a concrete test. The term dates are approximate and editable in Settings.

### Phase 0: foundations and spikes (≈ 1 week · now → end of Michaelmas Full Term)

- `.swiftpm` scaffold: an app shell with the sidebar and placeholders; Package.swift configured in code (§8).
- CI: Xcode 26.x compile on every PR. Pure logic (FSRS, merging, parsing) lives in a UIKit-free folder that a **CI-only root `Package.swift`** also builds as a library, so `swift test` runs unit tests on macOS runners even though Playgrounds app projects have no test targets.
- The Working Copy → Playgrounds loop, written up step by step in the README.
- First-run *Choose library folder* screen, bookmark, `FileStore` actor, and a **Diagnostics** screen (logs).
- **Ink spike:** plan A versus plan B (§3.1) with a real lecture-notes PDF. Measure crispness, latency and scrolling, then decide.
- **Device checks:** bookmark persistence across Playgrounds runs, `NSFilePresenter` on an iCloud Drive folder, local notifications from Playgrounds, Foundation Models availability, and whether `additionalInfoPlistContentFilePath` survives.

**Test:** run in Playgrounds → pick `iCloud Drive/MathsMaster` → open a sample PDF → write on it → quit and relaunch → the ink is still there, and `….pdf.ink/` is visible in Files.

### Phase 1: MVP, write on everything (≈ 2–3 weeks · in daily use by Christmas)

| Milestone | Contents | You can test |
|---|---|---|
| 1.1 Library | Courses (Part IB template, colours, terms), sidebar, course page shelves, import PDFs (picker + drag and drop), rename / move / Trash | Set up all your Michaelmas courses and drop in their notes |
| 1.2 Editor | Page engine, tool picker, Pencil/finger rules, 2-/3-finger undo/redo, autosave, zoom memory, page grid (insert / reorder / delete), bookmarks | Annotate a whole lecture's notes; compare the ink with Notes side by side |
| 1.3 Notebooks | Templates (dot, squared, ruled, blank, answer sheet), paper colours, dark mode | Do an example-sheet question on the answer template |
| 1.4 Two-up | Reference pane, recents → *Continue*, title search | Sheet on the left, answers on the right |
| 1.5 Out | Print and export PDF with options; example-sheet pairing + per-question status + hand-in export | Print a notebook without the grid; produce a hand-in PDF |

### Phase 2: flashcards v1 (≈ 2–3 weeks · target: early January, for revising Michaelmas courses before Lent term)

- Card model, `cards.json`, review logs, FSRS-6 port with unit tests.
- KaTeX renderer (web view + snapshot cache), card editor with live preview and the LaTeX bar.
- Review screen (scratch pad, reveal, grades, undo, end card), global and per-course queues, **Today** for real.
- Region → image card, source links, page badges.
- Stats v1 (heatmap, forecast, retention).
- *Parallel track:* the SideStore pipeline (unsigned Release `.ipa` from CI) and a first-run screen in the installed copy.

**Test:** make 30 Linear Algebra cards (typed and from regions), review daily for a week, then install via SideStore and see the same library and the same due counts.

### Phase 3: instant AI with Gemini (≈ 2 weeks · start of Lent)

Settings → AI (key in the Keychain, model pickers, budget meter) · Transcribe region → LaTeX · Make cards from a region · Explain (review and editor) · Ask AI to change a card (diff) · Write it (handwriting → LaTeX) · Inbox triage.
**Test:** turn a page of lecture notes into five good cards in under a minute; get an explanation of a failed card mid-review.

### Phase 4: VPS backup and Claude batch (≈ 2 weeks · Lent)

The VPS service (job API, backup mirror, nightly snapshots, deploy script) · Settings → VPS (URL + token) · backup status in the sidebar · *Generate cards from lectures…* → job → Inbox.
**Test:** queue cards for four lectures, find them in the Inbox later; restore yesterday's backup into a new folder.

### Phase 5: depth and polish (Lent → Easter vacation, ready for Tripos revision)

Example-sheet question auto-detection, feedback import and a richer *Up next* · ⌘K search with handwriting OCR and scopes · cloze and occlusion cards · exam mode and **exam readiness** · Stats v2 · FSRS optimiser on the VPS · vector ink export · PaperKit evaluation (text boxes, shapes) · possibly: past Tripos questions by course, Anki import, an iPhone review companion (see questions).

---

## 10. Open questions for the owner

1. **Storage: is iCloud Drive OK as the home of your library?** It needs roughly 0.5–1 GB a year; the free 5 GB fills up quickly if iPad backups also go to iCloud. *Recommendation: iCloud Drive (with iCloud+ if needed), with the VPS as backup.* The alternative is the VPS as the primary store, which means more complexity and needing a connection to sync.
2. **Order of the roadmap: ink and PDFs first, or flashcards first?** *Recommendation: ink first (Phase 1), cards immediately after (Phase 2), aiming at Christmas-vacation revision.* If you'd rather have cards for the vacation above everything else, Phases 1.3–1.5 can move after Phase 2.
3. **AI and privacy: may handwritten notes go to Gemini's free tier?** Google may use free-tier prompts to improve its products. *Recommendation: Gemini only for small regions you explicitly select; whole-lecture batches only through Claude on your VPS.*
4. **How do your supervisors take work?** On paper, emailed PDFs, or an upload site (e.g. Moodle)? This decides how much polish the hand-in export and the *Answer sheet* template get, and how early.
5. **Anything to bring in?** Existing Anki decks, GoodNotes, Notability or Notes notebooks, or a folder of PDFs? This decides whether an importer (e.g. Anki `.apkg`) goes on the roadmap.
6. **iPhone too?** Would you want to review cards on an iPhone later? It would be a SideStore-only build, since Playgrounds doesn't run on iPhone. If yes, we keep the review and card code free of iPad-only layouts from day one, which costs almost nothing now.

---

## 11. Risks and how we retire them

| Risk | Impact | Mitigation |
|---|---|---|
| Ink in PDF overlays is blurry when zoomed, or gestures conflict | Core experience | Phase-0 spike; plan B (custom page stack) uses the same data model |
| iCloud Drive: evicted files, slow sync, two copies writing | Data access | Coordinated I/O, *Keep Downloaded*, per-install logs, per-page files, conflict banners (§7.5) |
| Playgrounds quirks: manifest rewrites, package support, slow compiles on the iPad | Velocity | Manifest owned by the repo, ≤ 2 packages, small files, CI on the same SDK |
| Gemini free tier shrinks or changes models | AI features | Pluggable providers, per-task model choice, budget meter, VPS fallback |
| SideStore re-signing lapses (7 days) | The installed copy stops launching | SideStore refreshes it in the background; the Playgrounds copy always works; the data lives in the shared folder |
| KaTeX web views are slow in long lists | Card browser smoothness | One shared renderer that caches snapshots; lists show snapshots, and live web views only appear on the focused card |

---

## Appendix A: mockups

| File | Shows |
|---|---|
| [`mockups/01-library.svg`](mockups/01-library.svg) | Main split view: sidebar + Linear Algebra course page (13″ landscape) |
| [`mockups/02-today.svg`](mockups/02-today.svg) | Today: review hero, Up next, Continue, Inbox, heatmap |
| [`mockups/03-editor.svg`](mockups/03-editor.svg) | Editor in example-sheet mode: question PDF reference pane, answer page, tool picker, lasso → *Make card* |
| [`mockups/04-review.svg`](mockups/04-review.svg) | Card review: scratch area with handwriting, revealed answer, grade bar, side rail |
| [`mockups/05-cards.svg`](mockups/05-cards.svg) | Card editor with live LaTeX preview + AI inbox triage |
| [`mockups/06-compact.svg`](mockups/06-compact.svg) | 11″ portrait: Today and the editor at narrow width |
| [`mockups/design-plan.html`](mockups/design-plan.html) | This document rendered with all the mockups inline |

## Appendix B: sources checked (Nov 2026)

- Swift Playground 4.7 (17 Mar 2026): Swift 6 + iOS 26 SDK: [App Store listing](https://apps.apple.com/us/app/swift-playground/id908519492), [Paul Hudson on 4.7](https://x.com/twostraws/status/2034011131526644104), [release notes](https://developer.apple.com/swift-playgrounds/release-notes/)
- Entitlement-based services (iCloud/CloudKit, push) aren't supported in Playgrounds: [Apple forums 697378](https://developer.apple.com/forums/thread/697378), [Apple forums 772424](https://developer.apple.com/forums/thread/772424)
- `additionalInfoPlistContentFilePath` and Playgrounds dropping it: [rambo.codes](https://www.rambo.codes/posts/2021-12-28-a-document-based-app-in-swift-playgrounds-for-ipad), [FB9824864](https://github.com/feedback-assistant/reports/issues/269)
- iPad Air (M4, 2026) specs: [Apple Support 126471](https://support.apple.com/en-us/126471)
- PencilKit reed pen in iPadOS 26: [Apple Newsroom](https://www.apple.com/newsroom/2025/06/ipados-26-introduces-powerful-new-features-that-push-ipad-even-further/) · PaperKit: [WWDC25 session 285](https://developer.apple.com/videos/play/wwdc2025/285/)
- Gemini API free tier, late 2026 (third-party reports; check AI Studio for your real limits): [apidog](https://apidog.com/blog/gemini-api-free-tier/), [aifreeapi](https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier)
- SideStore free-account limits: [SideStore FAQ](https://docs.sidestore.io/docs/faq)
