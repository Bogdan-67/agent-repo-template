# INSTALL — instructions for the agent

You are installing **agent-repo-template** into the user's current project. Goal: the repository
becomes the single source of truth for any coding agent, **without losing a single line** of the
project's existing content. Follow the phases in order. Write all new project documentation in the
project's primary language (detect it from existing docs and commits; ask if unclear).

`$T` below is the directory where this template was cloned; `$P` is the project root
(`git rev-parse --show-toplevel`).

## Phase 0. Preconditions

1. `$P` must be a git repository with a clean work tree (`git status --porcelain` empty).
   If not, stop and ask the user to commit or stash.
2. Create a branch: `git switch -c chore/agent-template-$(cat $T/VERSION)`.
3. If `$P/.agents/template.lock` exists, this is an **upgrade**: follow `$T/UPGRADE.md` instead.
4. Requirements: `python3` ≥ 3.8 and `git`. Nothing else is installed.

## Phase 1. Discover and plan (change nothing)

1. Find every existing instruction and memory file:
   `AGENTS.md` (also nested), `CLAUDE.md`, `CLAUDE.local.md`, `.claude/` (agents, skills, settings),
   `GEMINI.md`, `.gemini/`, `.cursorrules`, `.cursor/rules/`, `.github/copilot-instructions.md`,
   `.github/instructions/`, `.github/agents/`, `.github/hooks/`, `.windsurf/rules/`, `.clinerules/`,
   `CONVENTIONS.md`, `.aider.conf.yml`, `.codex/`, `.opencode/`, `opencode.json(c)`, `.kimi-code/`,
   `.agents/`, `memory-bank/`, `.specify/`, and STATUS/TODO/NOTES/PROGRESS/CHANGELOG-like files,
   `docs/adr/`, `docs/decisions/`, existing git hooks (`.git/hooks/pre-commit`, `.husky/`,
   `.pre-commit-config.yaml`, `core.hooksPath`).
2. Read the project: README, build files (`pyproject.toml`, `package.json`, `Makefile`, `Dockerfile`,
   CI workflows) to learn the real setup, test and lint commands. Never invent commands.
3. For each payload file in `$T/MANIFEST.json` and each discovered file, choose one action:
   - **CREATE** — target does not exist: copy from `$T/payload/`.
   - **KEEP** — target exists and already serves the purpose: leave untouched.
   - **MOVE** — `git mv` to the template location (e.g. `docs/decisions/` → `docs/adr/`).
   - **MERGE** — copy content verbatim into the target with
     `<!-- migrated from <path> on <date> -->`, then replace the source with a one-line pointer
     or `git rm` it only after the content is preserved.
   - **SPLIT** — an oversized STATUS/NOTES/PROGRESS file: `git mv` it into `docs/journal/archive/`
     unchanged, then write a new ≤150-line `STATUS.md` that summarises the current state and links it.
4. Show the user a plan table `file → action → destination → reason` and the list of
   **user-level steps** (Phase 4). **Stop and wait for approval.**

## Phase 2. Apply (after the user approves)

Rules that always hold:
- Never overwrite or regenerate an existing user file. Moves are `git mv`; merges are verbatim inserts.
- Template-owned machinery (`owner: template` in MANIFEST.json) may be copied over a previous copy of
  itself only during an upgrade.
- Fill every `{{PLACEHOLDER}}` from facts in the repository. If a fact is unknown, write
  `TODO(user): <what is needed>` and add it to `OPEN_QUESTIONS.md`. Never invent.
- One logical step per commit only if the user asked for commits; otherwise leave changes unstaged.

Steps:
1. Copy `CREATE` files from `$T/payload/` preserving paths and executable bits
   (`.agents/hooks/docs_guard.py`, `.agents/bin/sync.py`, `.agents/init.sh`, `.githooks/pre-commit`).
2. `AGENTS.md`: if it existed, keep it and append the template sections it lacks (Read order, Where
   things are written, Session protocol, Roles) adapted to existing content. If not, create from payload
   and fill placeholders. Keep it ≤150 lines; move long sections to linked docs.
3. `CLAUDE.md`: move its non-trivial content into `AGENTS.md` (section "Migrated from CLAUDE.md"),
   then make `CLAUDE.md` start with `@AGENTS.md` and keep only Claude-specific notes.
   Do the same for `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, `CONVENTIONS.md`
   when they duplicate project rules (keep files the tool needs, reduced to a pointer).
4. Existing `.claude/agents/*.md` or other role files: move their bodies to `docs/agents/<name>.md` with
   the neutral frontmatter (`name`, `description`, `when_to_use`, `read_only`), delete the originals
   only after moving, then run `python3 .agents/bin/sync.py`.
5. Existing skills in `.claude/skills/<n>/`: `git mv` to `.agents/skills/<n>/`; `sync.py` recreates
   `.claude/skills/<n>` as a symlink.
6. Hooks: if the project already has `.claude/settings.json`, `.codex/hooks.json`, `.gemini/settings.json`
   or `.github/hooks/`, **merge** the template hook entries into the existing JSON; do not replace.
   If `.cursor/hooks.json` exists with a stop hook, do not add another: Cursor also runs
   `.claude/settings.json` hooks when third-party configs are enabled (the default).
7. Git hook: if a local pre-commit hook exists, move it to `.githooks/pre-commit.local` (the template
   hook chains to it). If the project uses the pre-commit framework or husky, add
   `python3 .agents/hooks/docs_guard.py commit` as a local hook there instead of `core.hooksPath`.
   Otherwise run `git config core.hooksPath .githooks`.
8. Fill `docs/OVERVIEW.md`, `STATUS.md`, `STRUCTURE.md`, `.agents/init.sh`, `docs/agents/domain.md`,
   the two project-specific questions in `docs/agents/cold-start-quiz.md`, and initial tasks in
   `docs/state/tasks.json` from the repository. Seed `GLOSSARY.md` with terms you had to look up.
9. Create `docs/journal/<YYYY-MM>.md` with the first entry `## <date> install agent-repo-template`
   listing every moved, merged and created file.
10. Replace `{{DATE}}` in `docs/adr/0001-*.md` and `docs/adr/README.md`; add ADRs for any existing
    decisions found in old notes only if the user confirms them.
11. Run `python3 .agents/bin/sync.py` then
    `python3 .agents/bin/sync.py lock --template-dir $T`.

## Phase 3. Verify

1. `python3 .agents/bin/sync.py --check` → OK.
2. `python3 .agents/hooks/docs_guard.py self-test` → OK.
3. `bash .agents/init.sh` → runs (or report what is missing).
4. `AGENTS.md` ≤150 lines and <32 KiB; `STATUS.md` ≤150 lines; no `{{` left except `TODO(user)`.
5. `git diff --stat` shows no deleted user content that was not moved or merged.
6. Ask the user to run the cold-start test (skill `cold-start-test`) in a different harness or model.

## Phase 4. Report to the user

Summarise what was created, moved and merged, then list the steps that cannot live in the repo:

- **Codex**: run `/hooks` once and trust the project hooks (new or changed hooks are skipped until trusted).
- **Kimi Code CLI**: hooks exist only in `~/.kimi-code/config.toml`; run
  `sh $T/user-level/install-kimi-hooks.sh` (idempotent, makes a backup).
- **Gemini CLI**: hooks must be enabled in settings if disabled; `.gemini/settings.json` also makes it read AGENTS.md.
- **GitHub Copilot**: repository hooks need workspace admission; the cloud agent reads hooks from the default branch.
- **Cursor**: keep "Include third-party plugins, skills and other configs" on, or copy the hooks to `.cursor/hooks.json`.
- **Cline, Windsurf**: no blocking end-of-turn hook; the git pre-commit gate is the guarantee.
- **Other models in Claude Code or Codex**: see `$T/user-level/` (env and provider snippets).
- Every clone of the project must run `git config core.hooksPath .githooks` once.
