# MathsMaster

A native SwiftUI iPad app that acts as the hub for a Cambridge maths degree. It brings together courses, lecture-note PDFs annotated with the Apple Pencil, example sheets, handwritten notebooks that print cleanly, and spaced-repetition flashcards (FSRS) with AI help.

- **Platform:** a Swift Playgrounds app project (`.swiftpm`) that runs in Swift Playground on the iPad. Every change is compile-checked on GitHub Actions macOS runners. A standalone install via SideStore comes later.
- **Data:** a shared folder in iCloud Drive (with a VPS backup), never only the app sandbox.
- **Design plan:** [`docs/DESIGN.md`](docs/DESIGN.md), with mockups in [`docs/mockups/`](docs/mockups/).
