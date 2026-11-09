# UPGRADE — instructions for the agent

Use when `.agents/template.lock` exists in the project. `$T` is the new template clone, `$P` the project.

1. Clean work tree; branch `chore/agent-template-$(cat $T/VERSION)`.
2. Read `$P/.agents/template.lock` (installed version and sha256 of template-owned files) and
   `$T/CHANGELOG.md` for every version after it. Show the user what changes.
3. For each file with `owner: template` in `$T/MANIFEST.json`:
   - not in the project → copy it;
   - in the project and its sha256 equals the lock → the user did not modify it: replace with the new version;
   - sha256 differs from the lock → the user modified it: **do not overwrite**; show a diff between the
     project file and the new template file and ask how to merge.
4. Files with `owner: seed` (AGENTS.md, STATUS.md, docs content) belong to the user: never replace them.
   Apply CHANGELOG items marked `seed-change` by editing the relevant section in place, after approval.
5. Hook JSON files (`.claude/settings.json`, `.codex/hooks.json`, `.gemini/settings.json`,
   `.github/hooks/docs-guard.json`): merge entries; keep the user's other hooks.
6. Run `python3 .agents/bin/sync.py`, `python3 .agents/hooks/docs_guard.py self-test`,
   `python3 .agents/bin/sync.py --check`, then `python3 .agents/bin/sync.py lock --template-dir $T`.
7. Journal entry `## <date> upgrade agent-repo-template <old> → <new>` listing replaced, merged and
   skipped files. Remind the user of user-level steps if `user-level/` changed (Codex: re-trust hooks).
