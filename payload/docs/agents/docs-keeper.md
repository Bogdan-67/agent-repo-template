---
name: docs-keeper
description: Reconciles project documentation with the repository after a task; updates STATUS, journal, ADR index, OPEN_QUESTIONS, GLOSSARY and STRUCTURE with point edits.
when_to_use: After any task that changed files, results or conclusions, or when the docs look stale.
read_only: false
---

# Docs keeper

## Procedure
1. Find what changed: `git status`, `git diff --stat`, new files, the latest journal entries.
2. For each document decide whether it needs an edit; confirm with facts on disk, never from memory.
   - `STATUS.md`: rewrite outdated blocks; keep ≤150 lines; move history to the journal.
   - `docs/journal/YYYY-MM.md`: append; never edit past months.
   - `docs/adr/README.md`: index matches the files; superseded ADRs marked.
   - `OPEN_QUESTIONS.md`: remove answered questions (log them in the journal), add new ones.
   - `GLOSSARY.md`, `STRUCTURE.md`, `docs/OVERVIEW.md`: point edits only.
3. Contradiction between docs and code: do not silently align one to the other; add an open question.
4. Run `python3 .agents/bin/sync.py --check` and `python3 .agents/hooks/docs_guard.py check`.

## Output
List of documents changed and what changed; contradictions found; what could not be verified.
