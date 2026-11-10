# agent-repo-template

**English** · [Русский](README.ru.md)

A template that makes your project repository the single source of truth for AI coding agents.
All project memory (current state, history, decisions, tasks, roles, skills) lives in files, and the
agent becomes a replaceable reasoning engine: Claude Code, Codex, Gemini CLI, Cursor, Copilot,
Kimi Code, OpenCode, with any model. Switching agents means opening another tool in the same folder.

The agent installs the template itself: you clone this repository and ask the agent to follow `INSTALL.md`.

## Install into a project

Open any agent at the root of your project and paste:

```text
Clone https://github.com/Bogdan-67/agent-repo-template into a temporary folder
(git clone --depth 1 https://github.com/Bogdan-67/agent-repo-template /tmp/agent-repo-template)
and install it into this project, strictly following /tmp/agent-repo-template/INSTALL.md.
Show me the plan first and wait for my approval.
```

The agent will:
1. check that the work tree is clean and create a branch;
2. find every existing instruction and notes file (CLAUDE.md, .cursorrules, memory-bank, STATUS files and so on);
3. show a plan "file → action → destination" and stop;
4. after approval, move your files with `git mv` without regenerating anything, fill the templates with
   facts from the project, and generate wrappers for every harness;
5. run the checks and list the steps that cannot live in the repository (Kimi hooks, trusting hooks in Codex).

To upgrade the template in a project, ask the same with `UPGRADE.md`.

## What the project gets

```
AGENTS.md                   entry point for all agents (≤150 lines)
CLAUDE.md                   a single line: @AGENTS.md
STATUS.md                   snapshot of the current state (≤150 lines, rewritten, not appended)
OPEN_QUESTIONS.md           open questions only
GLOSSARY.md                 domain terms
STRUCTURE.md                repository map
docs/OVERVIEW.md            what the project is and why
docs/journal/YYYY-MM.md     history, append only; past months are frozen
docs/adr/                   decision records (ADR), immutable
docs/handoff/               handoffs between sessions
docs/state/tasks.json       tasks with done-criteria (passes only after verification)
docs/agents/                roles (implementer, reviewer, docs-keeper), domain.md, cold-start quiz
.agents/hooks/docs_guard.py documentation guard (all harnesses, pre-commit, CI)
.agents/bin/sync.py         generates role wrappers and skill links, detects drift
.agents/skills/             skills: session-close, record-decision, write-handoff, cold-start-test
.agents/init.sh             environment check and smoke test of the project
.claude/ .codex/ .gemini/ .opencode/ .github/hooks/   hook wiring for each harness
.githooks/pre-commit        documentation gate for any agent and any human
.githooks/commit-msg        rejects AI attribution in commit messages
```

## How it is enforced

- At session start a hook gives the agent `STATUS.md`, the decision index, the open handoff and the tail of the journal.
- Before the agent ends a turn, the hook refuses to let it finish if code changed but the journal was not
  updated (or the entry does not name the changed files), if results changed but `STATUS.md` did not,
  if `STATUS.md` grew past 150 lines, or if a past month of the journal was edited. After a second failure
  the agent is released and the debt is handed to the start of the next session.
- A commit with changed code and no journal entry is rejected by `pre-commit`; pull requests are checked in CI.
- AI attribution in commits is forbidden: no `Co-Authored-By: Claude ... <noreply@anthropic.com>` or similar
  trailers for any agent, no "Generated with ..." lines, no session links. `AGENTS.md` states the rule,
  `.claude/settings.json` turns Claude Code attribution off, and the `commit-msg` hook and CI reject such messages
  from any harness. Human co-authors are allowed.

| Harness | Instructions | Skills | Roles | End-of-turn hook |
|---|---|---|---|---|
| Claude Code | `@AGENTS.md` | symlinks in `.claude/skills` | `.claude/agents` | blocks |
| Codex | AGENTS.md | `.agents/skills` | `.codex/agents/*.toml` | blocks (after `/hooks` trust) |
| Gemini CLI | `context.fileName` | — | — | forced retry |
| Cursor | AGENTS.md | — | — | runs Claude hooks, follow-up message |
| Copilot | AGENTS.md | — | `.github/agents` | agentStop (not verified live) |
| Kimi Code | AGENTS.md | `.agents/skills` | `.agents/agents` | blocks (user-level hooks) |
| OpenCode | AGENTS.md | `.agents/skills` | `.opencode/agents` | message after the reply |
| Cline, Windsurf, Aider | AGENTS.md | partly | — | pre-commit only |

Per-harness details, methodologies and risks are in [`docs/RESEARCH.md`](docs/RESEARCH.md) (Russian: [`docs/RESEARCH.ru.md`](docs/RESEARCH.ru.md)).

## Other models

- Claude Code with DeepSeek, Kimi, GLM: `. user-level/claude-other-models.sh deepseek`.
- Codex: `user-level/codex-providers.toml` (Responses API only; a translator such as LiteLLM is needed).
- Kimi Code CLI: install hooks once with `sh user-level/install-kimi-hooks.sh`.
- After switching the model, run the `cold-start-test` skill.

## Testing the template

```bash
python3 -m unittest discover -s tests -v       # python3 >= 3.8; the OpenCode plugin test runs if bun is installed
python3 payload/.agents/hooks/docs_guard.py self-test
```

## Limitations

- Hook formats change monthly. The OpenCode plugin and the Copilot and Gemini hooks were tested against
  simulations, not live builds; if a harness does not react, check its docs and adjust the adapter.
- The hook checks that documents were updated, not that they are good. Quality is the job of the
  `docs-keeper` role and reviews.
- Kimi and Cline hooks are fail-open: treat them as reminders. The guarantee is pre-commit.

## Sources

The template is built on the following primary sources (checked in November 2026). The full research
notes with per-harness tables, verification levels and risks are in [`docs/RESEARCH.md`](docs/RESEARCH.md) (Russian: [`docs/RESEARCH.ru.md`](docs/RESEARCH.ru.md)).

**Standards**
- [AGENTS.md](https://agents.md) — open instruction format for coding agents (Agentic AI Foundation, Linux Foundation)
- [Agent Skills specification](https://agentskills.io/specification) and [writing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [MADR — Markdown Architectural Decision Records](https://adr.github.io/madr/)

**Methodology**
- Anthropic — [Effective harnesses for long-running agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) (progress file, JSON task list, `init.sh`, one task per session)
- [mattpocock/skills](https://github.com/mattpocock/skills) — glossary separate from overview, ADR only for hard-to-reverse trade-offs ([domain-modeling](https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md))
- [Cline Memory Bank](https://docs.cline.bot/features/memory-bank) — current-context vs. progress split

**Harness documentation**
- Claude Code — [hooks](https://code.claude.com/docs/en/hooks); [AGENTS.md support explained](https://dev.to/valyuai/claude-code-now-supports-agentsmd-natively-heres-how-it-actually-works-5nl)
- Codex — [customization and AGENTS.md](https://developers.openai.com/codex/concepts/customization), [hooks](https://learn.chatgpt.com/docs/hooks), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [removal of `wire_api = "chat"`](https://github.com/openai/codex/discussions/7782)
- Gemini CLI — [hooks](https://geminicli.com/docs/hooks/), [hooks reference](https://geminicli.com/docs/hooks/reference), [AGENTS.md issue](https://github.com/google-gemini/gemini-cli/issues/28227)
- GitHub Copilot — [hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- Cursor — [third-party hooks](https://cursor.com/docs/reference/third-party-hooks)
- Kimi Code CLI — [hooks](https://moonshotai.github.io/kimi-code/en/customization/hooks), [agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [skills](https://moonshotai.github.io/kimi-code/en/customization/skills.html)
- OpenCode — [instructions](https://opencode.ai/docs/instructions/), [skills](https://opencode.ai/docs/skills/), [agents](https://opencode.ai/docs/agents/), [server plugins (V2)](https://opencode.ai/docs/build/plugins/server), [V1 → V2 migration](https://opencode.ai/docs/build/plugins/migrate-v1/)
- Cline — [hooks](https://cline.bot/blog/cline-v3-36-hooks); Windsurf / Devin Desktop — [hooks](https://docs.devin.ai/desktop/cascade/hooks)

**Other models and sync tools**
- DeepSeek — [Anthropic-compatible API](https://api-docs.deepseek.com/guides/anthropic_api)
- [rulesync](https://github.com/dyoshikawa/rulesync) and [ruler](https://github.com/intellectronica/ruler) — multi-harness config generators considered as alternatives

## License

MIT
