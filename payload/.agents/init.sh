#!/usr/bin/env bash
# Environment check + smoke test. Run at the start of a session before changing code.
# Keep it fast (< 2 min). The installer replaces the placeholders with real project commands.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "== environment"
{{SETUP_CHECK}}          # e.g. uv sync --frozen  |  npm ci  |  test -d .venv

echo "== smoke test"
{{SMOKE_TEST}}           # e.g. pytest -q -x tests/smoke  |  python train.py --max-steps 1 --dry-run

echo "== docs"
python3 .agents/bin/sync.py --check >/dev/null || echo "warning: harness wrappers out of sync (run .agents/bin/sync.py)"
echo "init: ok"
