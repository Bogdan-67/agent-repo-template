---
name: write-handoff
description: Writes a handoff so another agent or model can continue the work without this conversation. Use when a task will continue in a later session, before context runs out, or when switching harness or model.
---

# Write a handoff

1. Create `docs/handoff/YYYY-MM-DD-<topic>.md` from `docs/handoff/TEMPLATE.md` with `Status: open`.
2. Make it self-sufficient: goal, files to read (beyond the AGENTS.md read order), what is verified
   (with paths), numbered next steps each with a done-criterion, constraints, open questions.
3. Do not copy large content: link files and line ranges.
4. Link it from `STATUS.md` ("In progress / open handoff") and mention it in the journal.
5. When a later session finishes the work, set `Status: done YYYY-MM-DD` and remove the STATUS link.
