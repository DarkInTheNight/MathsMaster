# MathsMaster: code architecture and seams

The design is in [`DESIGN.md`](DESIGN.md). This file says where the code lives and how the workstreams plug together.

## Layout

```
MathsMaster.swiftpm/            the Swift Playgrounds app project (open this folder in Playgrounds)
  Package.swift                 owned by the repo; never edit it through Playgrounds' settings UI
  App/                          @main app, RootView (first run / loading / error / main)
  Core/                         Foundation-only models and pure logic; also built by the root Package.swift for `swift test`
    Models/                     LibraryManifest, Course, DocumentManifest, Page, Card, ReviewEntry, CalendarDate …
    Storage/                    LibraryLayout (folder and file names), JSONCoding (sorted keys, ISO dates, JSON lines)
    Logic/                      CambridgeCalendar (term weeks), Part IB course list, manifest edits
  Services/                     FileStore (actor, coordinated I/O), LibraryLocation (bookmark), LibraryStore (@Observable), AppLog
  UI/                           shell (split view, sidebar, routes), Today, course pages, settings, theme
  Features/
    Editor/                     WORKSTREAM B: notes and PDF editor
    Review/, Cards/             WORKSTREAM C: flashcards, review, Today's review block
Package.swift                   CI-only: builds Core as a library so unit tests run
Tests/MathsMasterCoreTests/     Swift Testing unit tests for Core
.github/workflows/ci.yml        Xcode 26.x build (Release, generic iOS, unsigned) + IPA artifact; `swift test`
```

## Rules

- **Swift 6 toolchain, Swift 5 language mode** (`swiftLanguageModes: [.v5]`), so UIKit/PencilKit/PDFKit delegate code doesn't fight strict concurrency while everything is compiled only on CI. UI types are `@MainActor`; `FileStore` is an actor.
- **Core imports Foundation only.** Anything that needs UIKit, PDFKit or SwiftUI goes in `Services/`, `UI/` or `Features/`. New Core logic should get a test in `Tests/MathsMasterCoreTests`.
- **CI uses Xcode 26.x (iOS 26 SDK)**, the SDK in Swift Playground 4.7. Don't use iOS 27 APIs.
- **All library I/O goes through `FileStore`** (coordinated, atomic). Never write with `Data.write` directly into the library folder.
- **Files are the truth.** Models are `Codable` with a `schemaVersion`; JSON is written with sorted keys and ISO-8601 dates (no fractional seconds).
- **No third-party packages** without a reason in the PR; never ones with macros, plugins or binary targets.
- Pushing a change to `.github/workflows/` needs the gh token (see project notes): `env -u GH_TOKEN -u GITHUB_TOKEN git -c credential.helper= -c credential.helper='!gh auth git-credential' push`.

## Seams

### App shell → features

- `AppRoute` (UI/Shell/AppRoute.swift) holds the full-screen destinations. Pushing one hides the sidebar.
  - `.document(DocumentSummary)` → `DocumentEditorView(document:)` (B)
  - `.review(ReviewScope)` → `ReviewSessionView(scope:)` (C)
  - `.cardBrowser(courseID:)` → `CardBrowserView(courseID:)` (C)
- Push from anywhere with `NavigationLink(value: AppRoute…)`, or `@Environment(\.openRoute) var openRoute; openRoute(.review(.all))`.
- Placeholder views that the workstreams replace (same names, same initialisers):
  - B: `DocumentEditorView`, `ReadOnlyPDFView` (Features/Editor)
  - C: `ReviewSessionView`, `ReviewHeroCard` (Today), `CourseDeckSummaryView` (course page), `CardsHomeView` (sidebar → Cards), `CardBrowserView` (Features/Review, Features/Cards)

### Data

- `LibraryStore` (@Observable, @MainActor, in the environment as `@Environment(LibraryStore.self)`):
  - `manifest` (courses, terms), `documentsByCourse`, `documents(in:kind:)`, `document(_:)`, `rescan(_:)`
  - `loadManifest(for:)` / `saveManifest(_:for:)`: a document's page list (`DocumentManifest`)
  - `importPDFs(_:into:kind:)`, `createNotebook(in:title:template:)`
  - `deckURL(course)`, `reviewLogURL(for:)`, `fileStore`, `noteOpened(_:pageIndex:)`, `recents`, `upcomingSheets`
- `FileStore` (actor): `readData`, `writeData`, `readJSON`, `writeJSON`, `append` (logs), `listDirectory` (handles iCloud placeholders), `importFile`, `moveToTrash`, `pdfPageSizes`, `url(_:)` (relative path → URL).
- On-disk layout: `LibraryLayout` and DESIGN.md §7.2.
  - Lecture notes: `Courses/<course>/Lecture notes/<name>.pdf` + `<name>.pdf.ink/document.json` + `pages/<pageID>.drawing`
  - Example sheets: `Example sheets/<name>.pdf` (questions) + `<name>.sheet/document.json` (answer pages, `ExampleSheetInfo`) + `pages/`
  - Notebooks: `Notebooks/<name>.mmnote/document.json` + `pages/`
  - Cards: `Courses/<course>/cards.json` (`DeckFile`); review logs: `Reviews/<installID>/<yyyy-MM>.jsonl` (`ReviewEntry` lines)

### Workstream D (VPS)

Talks to the app only through files and the HTTP API in DESIGN.md §5.5 and §7.7. Card JSON must decode as `Card` / `DeckFile` (Core/Models/Card.swift).
