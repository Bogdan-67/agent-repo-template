---
name: record-decision
description: Records a decision as an Architecture Decision Record in docs/adr. Use when the user decides something, when a choice between real alternatives was made, or when a config or protocol encodes a decision that is not yet documented.
---

# Record a decision

Write an ADR only if all three hold: the decision is hard to reverse, it is not obvious without
context, and it resulted from a real trade-off. Otherwise a journal line is enough.

1. Next number: highest `NNNN` in `docs/adr/` plus one. File: `docs/adr/NNNN-short-slug.md`.
2. Copy `docs/adr/0000-template.md`; fill Context (facts with paths), Decision (checkable statement),
   Considered options (why each was rejected), Consequences, Where it is applied.
3. Status `accepted` only if the user decided or approved it; otherwise `proposed` and add the
   question to `OPEN_QUESTIONS.md`.
4. If it replaces an earlier decision: in the old ADR change only the status line to
   `superseded by ADR-NNNN`; never rewrite its body.
5. Add a row to `docs/adr/README.md`.
6. In configs, protocols and code, reference `ADR-NNNN` instead of restating the decision.
7. Mention the ADR in today's journal entry.
