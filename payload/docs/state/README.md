# Task state

`tasks.json` holds tasks with explicit done-criteria. JSON, not Markdown, because models are less
likely to rewrite structured state wholesale (Anthropic, "Effective harnesses for long-running agents").

Rules: work on one task at a time; set `"passes": true` only after the check in `verify` succeeded and
record how in `evidence`; never delete tasks, set `"status": "dropped"` with a reason instead.
