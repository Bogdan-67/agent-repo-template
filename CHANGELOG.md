# Changelog

Entries marked `seed-change` describe changes to user-owned files (AGENTS.md, STATUS.md, docs templates):
the upgrading agent applies them in place after the user approves. Everything else is template machinery.

## 0.1.0 — 2026-11-10

- First release: AGENTS.md entry point, STATUS snapshot, monthly append-only journal, ADRs, handoffs,
  JSON task state, neutral roles (implementer, reviewer, docs-keeper), skills (session-close,
  record-decision, write-handoff, cold-start-test).
- `docs_guard.py`: one core with adapters for Claude Code, Codex, Cursor, Gemini CLI, Copilot, Kimi Code,
  OpenCode; git pre-commit and CI gates; built-in self-test.
- `sync.py`: role wrappers for Claude Code, Codex, Kimi Code, OpenCode, Copilot; skill symlinks for
  Claude Code; validation of skills and AGENTS.md size; install lock.
- OpenCode plugin with V2 and V1 entry points (not verified on a live build).
- Ban on AI attribution in commits: rule in AGENTS.md, `attribution` off in `.claude/settings.json`,
  `.githooks/commit-msg` and a CI check of commit messages (`docs_guard.py commit-msg`).
- User-level snippets: Kimi hooks installer, Codex providers, Claude Code with DeepSeek/Kimi/GLM.
