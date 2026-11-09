#!/usr/bin/env sh
# Adds agent-repo-template hooks to Kimi Code CLI. Kimi has no project-level hook file: hooks live only
# in ~/.kimi-code/config.toml. Idempotent; backs up the config. The hooks do nothing in repositories
# without .agents/hooks/docs_guard.py. Kimi hooks are fail-open: treat them as a reminder; the git
# pre-commit gate is the guarantee.
set -eu
home="${KIMI_CODE_HOME:-$HOME/.kimi-code}"
cfg="$home/config.toml"
marker="# agent-repo-template docs_guard"
mkdir -p "$home"; touch "$cfg"
if grep -qF "$marker" "$cfg"; then echo "already installed: $cfg"; exit 0; fi
if grep -qE '^[[:space:]]*hooks[[:space:]]*=' "$cfg"; then
  echo "$cfg defines hooks inline (hooks = [...]); add the entries from kimi-hooks.toml manually." >&2; exit 1
fi
cp "$cfg" "$cfg.bak.$(date +%Y%m%d%H%M%S)"
{ echo; cat "$(dirname "$0")/kimi-hooks.toml"; } >> "$cfg"
echo "installed into $cfg (backup saved next to it)"
