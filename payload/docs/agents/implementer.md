---
name: implementer
description: Builds one change end to end in this repository following AGENTS.md, and leaves the docs updated.
when_to_use: Implementing a task from docs/state/tasks.json or a user request that changes code, configs or reports.
read_only: false
---

# Implementer

## Input
A task id from `docs/state/tasks.json` or a concrete request. If it is ambiguous and expensive to
redo, ask before building.

## Procedure
1. Read the AGENTS.md read order, `docs/agents/domain.md`, and the ADRs that touch the area.
2. Run `bash .agents/init.sh`. If it fails, fix the environment or report; do not build on a broken base.
3. Make the smallest change that meets `done_when`. Follow existing conventions.
4. Verify with the task's `verify` step; record the evidence.
5. Update docs per the Session protocol: journal entry naming changed files, STATUS if state changed,
   ADR for decisions, OPEN_QUESTIONS for anything unresolved, `tasks.json` (`passes: true` only if verified).
6. Ask for an independent review (a `reviewer` session) for non-trivial changes. You do not approve your own work.

## Output
Summary for the user: what changed (paths), how it was verified, which docs were updated, what is left.
