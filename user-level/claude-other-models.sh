# Run Claude Code with a non-Anthropic model through the provider's Anthropic-compatible endpoint.
# Source this file in a shell (do not commit keys):  . user-level/claude-other-models.sh deepseek
# Not supported by Anthropic; documented by the providers. Model names and URLs change often:
# check the provider page. Keep CLAUDE.md as '@AGENTS.md' (native AGENTS.md reading may not work here).
case "${1:-}" in
  deepseek)
    export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
    export ANTHROPIC_AUTH_TOKEN="${DEEPSEEK_API_KEY:?set DEEPSEEK_API_KEY}"
    export ANTHROPIC_MODEL="${MODEL:-deepseek-chat}" ;;
  kimi)
    # Kimi Code subscription endpoint; for pay-as-you-go use the Moonshot platform URL from its docs.
    export ANTHROPIC_BASE_URL="https://api.kimi.com/coding/"
    export ANTHROPIC_AUTH_TOKEN="${KIMI_API_KEY:?set KIMI_API_KEY}"
    export ANTHROPIC_MODEL="${MODEL:-kimi-for-coding}" ;;
  glm)
    export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
    export ANTHROPIC_AUTH_TOKEN="${ZAI_API_KEY:?set ZAI_API_KEY}"
    export ANTHROPIC_MODEL="${MODEL:-glm-4.6}" ;;
  *) echo "usage: . claude-other-models.sh deepseek|kimi|glm   (override the model with MODEL=...)"; return 1 2>/dev/null || exit 1 ;;
esac
unset ANTHROPIC_API_KEY
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL" ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL" CLAUDE_CODE_SUBAGENT_MODEL="$ANTHROPIC_MODEL"
echo "Claude Code -> $ANTHROPIC_BASE_URL ($ANTHROPIC_MODEL). Run the cold-start test after switching."
