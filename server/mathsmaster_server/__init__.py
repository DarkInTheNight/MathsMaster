"""MathsMaster companion service (runs on the owner's VPS).

Three jobs, as in docs/DESIGN.md §7.7:
  * a backup mirror of the library folder (plain files),
  * the one-off Anki import (.apkg/.colpkg -> cards + review history),
  * the Claude runtime: batch jobs and per-card threads via headless Claude Code.
"""

__version__ = "0.1.0"
