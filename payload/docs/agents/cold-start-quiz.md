# Cold-start quiz

A fresh agent (new session, ideally another model and harness, no memory) must answer every question
from the files alone and cite the file. Run after installing the template, after big changes, and after
switching the engine. A question that cannot be answered from files is a documentation defect.

Prompt to use:
> Do not modify any files. Answer each question in docs/agents/cold-start-quiz.md and cite the file
> (and section) for every answer. Say "not found" if the files do not contain it.

| # | Question | Answer is in |
|---|---|---|
| 1 | How do I set up the environment and run the tests? | `AGENTS.md` Commands |
| 2 | What is the project and who is it for? | `docs/OVERVIEW.md` |
| 3 | What is the current state and the next step? | `STATUS.md` |
| 4 | What was done in the last session? | `docs/journal/` (current month, last entry) |
| 5 | What is the most recent decision and why? | `docs/adr/README.md` |
| 6 | What must never be done in this repository? | `AGENTS.md` Hard rules, `docs/agents/domain.md` |
| 7 | Which task is next and how is it verified? | `docs/state/tasks.json` |
| 8 | What is unresolved and who decides? | `OPEN_QUESTIONS.md` |
| 9 | {{PROJECT_SPECIFIC_QUESTION}} | {{FILE}} |
| 10 | {{PROJECT_SPECIFIC_QUESTION}} | {{FILE}} |
