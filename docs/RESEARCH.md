# Research: the repository as the single source of truth for coding agents (November 2026)

**English** · [Русский](RESEARCH.ru.md)

This document collects the knowledge the template is built on: which files each harness reads, where it
looks for skills and roles, how hooks work, which repo-memory methods hold up, and where the pitfalls are.
Harness formats change every month, so each item carries a verification level:
**[docs]** official documentation, **[secondary]** secondary sources with quotes, **[unverified]** not checked.

## 1. Key findings

- File formats are standardised, agent behaviour is not. AGENTS.md (under the Agentic AI Foundation at
  the Linux Foundation since December 2025) and Agent Skills (`SKILL.md`, agentskills.io) are read by
  almost every harness. Roles and hooks are harness-specific, hence the scheme: neutral source →
  generated wrappers → drift check (`.agents/bin/sync.py --check`).
- A harness hook is a convenience; git is the guarantee. Every harness keeps the agent from finishing in a
  different way, and some hooks are fail-open or cannot block at all. A pre-commit hook and a CI step running
  the same script work with any harness and any model.
- A minimal core instead of "read everything". `AGENTS.md` and a short `STATUS.md` are always loaded; the
  rest is read through a "which file answers which question" map. Making the agent read every document at
  start bloats the context, and the documents go stale.
- What agents tend to corrupt is kept in JSON (task state) or made append-only (journal, ADRs).
- The agent installs the template itself in two passes (plan → approval → apply), with a manifest and a
  cold-start test at the end.

## 2. Instruction files

| Harness | Native file | AGENTS.md | What to do | Level |
|---|---|---|---|---|
| Codex CLI | AGENTS.md (+ override, `~/.codex/AGENTS.md`) | yes; chain from root to cwd, 32 KiB limit for the whole chain | nothing | [docs] |
| Claude Code | CLAUDE.md, `.claude/CLAUDE.md`, CLAUDE.local.md | since v2.1.277 only if no CLAUDE.md exists up the tree; not on Bedrock/Vertex | `CLAUDE.md` containing `@AGENTS.md` | [secondary] |
| OpenCode V2 | AGENTS.md | yes; no longer reads CLAUDE.md; nested files load lazily | nothing; extra files via `instructions` | [docs] |
| Gemini CLI | GEMINI.md | not by default | `.gemini/settings.json`: `context.fileName: ["AGENTS.md","GEMINI.md"]` | [secondary] |
| Cursor | `.cursor/rules/*.mdc` | yes, nested too | nothing | [secondary] |
| GitHub Copilot | `.github/copilot-instructions.md` | yes | nothing | [secondary] |
| Windsurf / Devin Desktop | `.windsurf/rules/` | yes | nothing | [secondary] |
| Cline | `.clinerules/` | yes | nothing | [secondary] |
| Kimi Code CLI | AGENTS.md (`/init`) | yes, injected via `${agents_md}` | nothing | [docs] |
| Aider | CONVENTIONS.md | only via `read:` | `.aider.conf.yml`: `read: AGENTS.md` | [secondary] |

Claude Code trap: any CLAUDE.md higher up the tree (in the home directory, in a parent monorepo) silently
disables native AGENTS.md reading. The `@AGENTS.md` import is more reliable. Native reading may also fail
when Claude Code runs third-party models.

## 3. Skills (Agent Skills)

Frontmatter per the agentskills.io specification: `name` (≤64 characters, lowercase letters, digits,
single hyphens, **equal to the directory name**), `description` (1–1024 characters, what the skill does
and when to use it; the model selects skills by this field); optional `license`, `compatibility`,
`metadata`, `allowed-tools`. Body up to ~500 lines, details in `references/`, `scripts/`, `assets/` by link.
Harness extensions (Kimi `whenToUse`, OpenCode-specific keys) are not portable. [docs]

| Harness | Project | User |
|---|---|---|
| Codex | `.agents/skills` | `~/.agents/skills` |
| OpenCode | `.opencode/skills`, `.agents/skills`, `.claude/skills` | `~/.config/opencode/skills`, `~/.agents/skills`, `~/.claude/skills` |
| Kimi Code | `.kimi-code/skills`, `.agents/skills` | `~/.kimi-code/skills`, `~/.agents/skills` |
| Gemini CLI | `.gemini/skills` | `~/.gemini/skills` |
| Copilot | `.github/skills` | — |
| Cursor | `.cursor/skills` | — |
| Claude Code | `.claude/skills` | `~/.claude/skills` |

The canonical location is `.agents/skills/`; Claude Code gets symlinks
`.claude/skills/<n> → ../../.agents/skills/<n>`. OpenCode may list a skill twice (it reads both folders).

## 4. Roles (subagents)

There is no common standard. [docs for Codex, Kimi, OpenCode; secondary for the rest]

| Harness | Where | Format |
|---|---|---|
| Claude Code | `.claude/agents/*.md` | YAML: `name`, `description`, `tools`, `model`; the body is the system prompt |
| Codex | `.codex/agents/*.toml` | TOML: `name`, `description`, `developer_instructions`; `sandbox_mode` and the provider cannot be overridden from the agent file |
| Kimi Code | `.agents/agents/`, `.kimi-code/agents/` | `name`, `description`, `whenToUse`, `tools`, `disallowedTools`; a body without `${base_prompt}` replaces the whole system prompt |
| OpenCode V2 | `.opencode/agents/*.md` | `description`, `mode: subagent`, `permissions` (V2), `model`; do not mix V1 fields |
| Copilot | `.github/agents/*.agent.md` | Markdown + frontmatter |

In the template the role lives in `docs/agents/<role>.md`; `sync.py` generates the wrappers
(a pointer: "read the role file in full").

## 5. Hooks

| Harness | Where | Context at start | Keep the agent from finishing | Loop guard | Trust |
|---|---|---|---|---|---|
| Claude Code | `.claude/settings.json` | SessionStart → `hookSpecificOutput.additionalContext` | Stop → `{"decision":"block","reason"}` or exit 2 | `stop_hook_active`, built-in cap | immediate [docs] |
| Codex | `.codex/hooks.json` | SessionStart → `additionalContext` | Stop → `decision: block` (JSON only) | `stop_hook_active` | `/hooks`, otherwise skipped [docs] |
| Kimi Code | `~/.kimi-code/config.toml` only | SessionStart only observes; context via UserPromptSubmit | Stop → exit 2, reason on stderr | not documented | fail-open [docs] |
| OpenCode V2 | `.opencode/plugins/*.ts` | `ctx.session.instructions.entry.put` | cannot block: on `session.idle` send `ctx.session.prompt` | own counter | V1 plugins do not run in V2 [docs; the idle event is inferred] |
| Gemini CLI | `.gemini/settings.json` | SessionStart → `hookSpecificOutput.additionalContext` | AfterAgent → `{"decision":"deny","reason"}` (forced retry) | `stop_hook_active` | hooks must be enabled in settings [docs] |
| Cursor | `.cursor/hooks.json` + Claude hooks | sessionStart (context loss bugs reported) | stop cannot block: `followup_message`, limit 5 | `loop_count` | Claude hooks run by default [secondary] |
| Copilot | `.github/hooks/*.json` | sessionStart → `additionalContext` | agentStop can "block and force continuation"; output format not read | `stop_hook_active` | workspace admission [docs, partial] |
| Cline | `.clinerules/hooks/` | TaskStart | no end-of-turn blocking | — | toggle, fail-open [secondary] |
| Windsurf | `.windsurf/hooks.json` | none | post hooks do not block | — | — [secondary] |

`docs_guard.py` is one core with output adapters (`--harness`). Decisions are made from git state
(a snapshot at session start in `.git/agent-guard/`), not from the transcript. The loop guard has two
layers: the harness flag and the guard's own block counter; after a repeated failure the agent is released
and the violations are injected at the start of the next session.

## 6. Repo-memory methods

| Approach | Taken into the template | Risk |
|---|---|---|
| Anthropic, "Effective harnesses for long-running agents" | progress file (`STATUS.md` + journal), JSON task list with verification status (`docs/state/tasks.json`), `init.sh` with a smoke test, one task per session, "passes only after verification" | a list of hundreds of items bloats: it is a state file, not context |
| Matt Pocock skills (GLOSSARY.md, docs/adr) | glossary separate from the overview, ADR only when three conditions hold, files created lazily | the convention was renamed CONTEXT.md → GLOSSARY.md; older skill versions write to CONTEXT.md |
| ADR (Nygard, MADR) | immutable records, `superseded by` status | agents rewrite old ADRs: the guard flags it |
| Cline Memory Bank | split into foundation / current context / progress, "activeContext holds only the present" | many files to read every time [unverified against primary sources] |
| Spec Kit, BMAD, Kiro specs | the "constitution" = the Hard rules section of AGENTS.md | feature-driven ceremony, heavy for research projects |
| "Ralph loop" | state outside the context, AGENTS.md grows with lessons | junk in AGENTS.md: needs a size limit and review |

## 7. Third-party models

- Claude Code: set `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` to the provider's
  Anthropic-compatible endpoint (DeepSeek, Kimi, GLM). Anthropic does not support this; some features may
  behave differently. See `user-level/claude-other-models.sh`.
- Codex: only `wire_api = "responses"`; providers are read only from `~/.codex/config.toml`; providers that
  offer only Chat Completions need a translator (LiteLLM). See `user-level/codex-providers.toml`.
- OpenCode: works with Chat Completions providers natively; the simplest route.
- After switching the model, the cold-start test is mandatory.

## 8. Existing sync tools

- **rulesync** (dyoshikawa): generates rules, MCP, commands, subagents, skills and hooks for 40+ harnesses
  from `.rulesync/`. A strong fallback; downsides are an extra abstraction layer and npm, Kimi support unverified.
- **ruler** (intellectronica): `.ruler/` → rules and skills, with a CI drift check; does not cover hooks.
- The template's choice: the source of truth is the project's neutral files; wrappers are generated by a
  small dependency-free `sync.py`. With more than 6–7 harnesses, switching to rulesync makes sense.

## 9. Risks

- Fast obsolescence: OpenCode V1→V2 broke plugins, Cursor changed its hook schema, Kimi moved from
  `~/.kimi` to `~/.kimi-code`. The OpenCode plugin and the Copilot/Gemini formats in the template were not
  tested on live builds.
- Double execution: Cursor runs `.claude/settings.json`; do not duplicate the hook in `.cursor/hooks.json`.
- Fail-open hooks (Kimi, Cline) are reminders, not protection.
- An overly strict hook provokes token entries. The guard therefore requires the journal entry to name the
  changed files, and AGENTS.md explicitly forbids writing entries just to pass the check.
- Steps that cannot live in the repository: Kimi hooks, Codex providers, trusting hooks in Codex and Copilot,
  enabling hooks in Gemini and Cline, `git config core.hooksPath` in every clone.

## Sources

- [AGENTS.md](https://agents.md) · [Codex: AGENTS.md and customization](https://developers.openai.com/codex/concepts/customization)
- [Agent Skills: specification](https://agentskills.io/specification) · [skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Claude Code: hooks](https://code.claude.com/docs/en/hooks) · [AGENTS.md in Claude Code (explainer)](https://dev.to/valyuai/claude-code-now-supports-agentsmd-natively-heres-how-it-actually-works-5nl)
- [Codex: hooks](https://learn.chatgpt.com/docs/hooks) · [Codex: subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) · [Codex: removal of wire_api chat](https://github.com/openai/codex/discussions/7782)
- [Kimi Code: hooks](https://moonshotai.github.io/kimi-code/en/customization/hooks) · [Kimi Code: agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html) · [Kimi Code: skills](https://moonshotai.github.io/kimi-code/en/customization/skills.html)
- [OpenCode: instructions](https://opencode.ai/docs/instructions/) · [OpenCode: skills](https://opencode.ai/docs/skills/) · [OpenCode: agents](https://opencode.ai/docs/agents/) · [OpenCode: server plugins V2](https://opencode.ai/docs/build/plugins/server) · [OpenCode: V1→V2 migration](https://opencode.ai/docs/build/plugins/migrate-v1/)
- [Gemini CLI: hooks](https://geminicli.com/docs/hooks/) · [Gemini CLI: hooks reference](https://geminicli.com/docs/hooks/reference) · [Gemini CLI: AGENTS.md issue](https://github.com/google-gemini/gemini-cli/issues/28227)
- [GitHub Copilot: hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Cursor: third-party hooks](https://cursor.com/docs/reference/third-party-hooks) · [forum: additional_context lost](https://forum.cursor.com/t/sessionstart-hook-additional-context-is-never-injected-into-agents-initial-system-context/158452)
- [Cline: hooks](https://cline.bot/blog/cline-v3-36-hooks) · [Devin Desktop / Windsurf: hooks](https://docs.devin.ai/desktop/cascade/hooks)
- [Anthropic: Effective harnesses for long-running agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [mattpocock/skills](https://github.com/mattpocock/skills) · [domain-modeling](https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md)
- [MADR](https://adr.github.io/madr/) · [Cline Memory Bank](https://docs.cline.bot/features/memory-bank)
- [rulesync](https://github.com/dyoshikawa/rulesync) · [ruler](https://github.com/intellectronica/ruler)
- [DeepSeek: Anthropic API](https://api-docs.deepseek.com/guides/anthropic_api) · [Kimi Code CLI: getting started](https://www.kimi.com/en/help/kimi-code/cli-getting-started)
