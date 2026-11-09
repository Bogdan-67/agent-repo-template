---
name: cold-start-test
description: Tests that a fresh agent with no memory can work from the repository files alone, using docs/agents/cold-start-quiz.md. Use after installing the template, after large documentation changes, or after switching the agent harness or model.
---

# Cold-start test

1. Start a new session with no history, ideally another model and harness. Non-interactive examples:
   `claude -p "<prompt>"`, `codex exec "<prompt>"`, `gemini -p "<prompt>"`, `kimi -p "<prompt>"`,
   `opencode run "<prompt>"`.
2. Prompt: "Do not modify any files. Answer each question in docs/agents/cold-start-quiz.md and cite the
   file and section for every answer. Say 'not found' when the files do not contain the answer."
3. Compare with the expected sources in the quiz. Pass = every answer correct and cited.
4. Every miss is a documentation defect: write the missing fact into the right file (not into the chat),
   then rerun. Log the result in the journal.
