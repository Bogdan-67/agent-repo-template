---
name: session-close
description: Closes a work session so the repository stays the single source of truth. Use before finishing any turn that changed code, configs, data or reports, or when the docs_guard hook blocked the turn.
---

# Session close

1. List what changed: `git status --porcelain` and `git diff --stat`.
2. Append to `docs/journal/<YYYY-MM>.md` (create it with a `# Journal YYYY-MM` title if missing):

   ```markdown
   ## YYYY-MM-DD <topic>

   - What was done and why.
   - Changed: `path/a.py`, `path/b.yaml`; artifacts: `reports/x.md`.
   - Checks: <tests/commands run and result> | not verified.
   - Decisions: ADR-NNNN | none. STATUS.md: updated | not changed because <reason>.
   ```

   Name the real changed files: the guard checks that at least one is mentioned.
3. If the state or results changed, rewrite the affected block of `STATUS.md` (do not append history;
   keep it ≤150 lines; bump the `Updated:` date).
4. If the user decided something, or you chose between real alternatives, use the `record-decision` skill.
5. Update `docs/state/tasks.json`: `passes: true` only with evidence from a check you ran.
6. `OPEN_QUESTIONS.md`: add new questions; delete answered ones and log `closed: ...` in the journal.
7. If the work continues later, use the `write-handoff` skill.
8. Run `python3 .agents/hooks/docs_guard.py check --hours 12` and fix what it reports.
9. Tell the user which documentation files changed.

Never write filler to satisfy the guard. Never edit past-month journals or accepted ADRs.
