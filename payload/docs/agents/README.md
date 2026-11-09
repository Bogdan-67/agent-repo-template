# Roles

Neutral role definitions: the single source for every harness. Frontmatter fields read by
`.agents/bin/sync.py`: `name` (kebab-case), `description`, `when_to_use`, `read_only` (true/false).
After editing or adding a role run `python3 .agents/bin/sync.py`; it regenerates the wrappers in
`.claude/agents`, `.codex/agents`, `.agents/agents` (Kimi), `.opencode/agents`, `.github/agents`.

`domain.md` holds project rules every role and skill must respect. `cold-start-quiz.md` is the test
that a fresh agent can work from the files alone.
