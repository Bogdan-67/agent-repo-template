# ADR-0001. The repository is the single source of truth for agents

- Status: accepted
- Date: {{DATE}}
- Decided by: user

## Context and problem

Project knowledge spread across chat histories, tool-specific memories, and oversized notes cannot be
handed to another agent or model. Switching the agent must take minutes, not a re-explanation.

## Decision

Install agent-repo-template: `AGENTS.md` as the entry point, `STATUS.md` snapshot, append-only
journal, ADRs, handoffs, JSON task state, neutral roles and skills with generated harness wrappers,
and `docs_guard.py` enforcement through harness hooks and a git pre-commit hook.

## Considered options

- Tool-specific memory (claude.ai, Cursor memories): not portable.
- Heavy spec frameworks (Spec Kit, BMAD): more ceremony than needed for this project.

## Consequences

Every session ends with documentation updates; the guard blocks turns that skip them. Harness formats
change often: adapters are regenerated with `.agents/bin/sync.py` and upgraded via the template.
