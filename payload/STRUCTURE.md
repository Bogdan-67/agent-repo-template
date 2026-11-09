# Repository map

Top-level map; update when files, entry points, or data flow change. Keep it short: link to
detailed docs instead of listing every file.

```
{{TREE}}
```

## Agent and documentation machinery

```
AGENTS.md, CLAUDE.md        agent entry point (CLAUDE.md imports AGENTS.md)
STATUS.md                   current state snapshot
OPEN_QUESTIONS.md, GLOSSARY.md
docs/OVERVIEW.md            what the project is and why
docs/journal/               append-only history, one file per month
docs/adr/                   decision records
docs/handoff/               session handoffs
docs/state/tasks.json       tasks with verified done-criteria
docs/agents/                neutral role definitions, domain rules, cold-start quiz
.agents/                    template machinery: guard, sync, skills, Kimi wrappers, init.sh
.claude/ .codex/ .gemini/ .opencode/ .github/hooks .github/agents   harness adapters (generated or fixed)
.githooks/pre-commit        documentation gate for any agent and any human
```
