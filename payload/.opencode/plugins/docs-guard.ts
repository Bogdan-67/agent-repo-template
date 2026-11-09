// agent-repo-template: documentation guard for OpenCode (V2 and V1).
//
// OpenCode cannot refuse to end a turn, so the plugin works after the fact:
// - when a root session is created, it adds the project context (STATUS, ADR index, open handoff)
//   to the session instructions (V2) or as a no-reply message (V1);
// - when the session goes idle, it runs `.agents/hooks/docs_guard.py stop --harness opencode` and, if
//   documentation was not updated, sends the findings to the model as a new prompt.
// Loop protection lives in docs_guard.py (one block, then release and hand over to the next session).
//
// Export shape: a V2 plugin object `{ id, setup }` plus a V1 `server()` function, as documented for
// V1-compatible plugins. V2 decodes the default export structurally, so no runtime import of the SDK.
// Not verified against a live OpenCode build: if events are named differently in your version,
// adjust IDLE_TYPES / CREATED_TYPES below.

import { execFileSync } from "node:child_process"

const IDLE_TYPES = ["session.idle"]
const CREATED_TYPES = ["session.created"]

function guard(root: string, mode: "start" | "stop", sessionID: string): string {
  try {
    return execFileSync(
      "python3",
      [`${root}/.agents/hooks/docs_guard.py`, mode, "--harness", "opencode", "--session", sessionID, "--cwd", root],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 60_000 },
    ).trim()
  } catch {
    return "" // a guard failure must never break the session
  }
}

function fields(ev: any) {
  const data = ev?.data ?? ev?.properties ?? {}
  const info = data.info ?? data.session ?? {}
  const status = data.status?.type ?? data.status
  return {
    type: String(ev?.type ?? ""),
    sessionID: String(data.sessionID ?? info.id ?? data.id ?? ""),
    parentID: info.parentID ?? data.parentID,
    idle: IDLE_TYPES.includes(ev?.type) || (ev?.type === "session.status" && status === "idle"),
  }
}

// ---------------------------------------------------------------- V2
const v2 = {
  id: "agent-repo-template.docs-guard",
  setup(ctx: any) {
    const root: string = ctx?.location?.directory ?? process.cwd()
    const children = new Set<string>()
    const abort = new AbortController()
    ;(async () => {
      for await (const ev of ctx.event.subscribe({ signal: abort.signal })) {
        const f = fields(ev)
        if (!f.sessionID) continue
        if (CREATED_TYPES.includes(f.type)) {
          if (f.parentID) {
            children.add(f.sessionID)
            continue
          }
          const text = guard(root, "start", f.sessionID)
          if (text) {
            await ctx.session.instructions?.entry
              ?.put({ sessionID: f.sessionID, key: "docs-guard", value: text })
              .catch(() => {})
          }
        } else if (f.idle && !children.has(f.sessionID)) {
          const reason = guard(root, "stop", f.sessionID)
          if (reason) await ctx.session.prompt({ sessionID: f.sessionID, text: reason }).catch(() => {})
        }
      }
    })().catch(() => {})
    return () => abort.abort()
  },
}

// ---------------------------------------------------------------- V1
async function server({ client, directory, worktree }: any) {
  const root: string = worktree || directory || process.cwd()
  const children = new Set<string>()
  const send = (id: string, text: string, noReply: boolean) =>
    client.session.prompt({ path: { id }, body: { noReply, parts: [{ type: "text", text }] } }).catch(() => {})
  return {
    event: async ({ event }: any) => {
      const f = fields(event)
      if (!f.sessionID) return
      if (CREATED_TYPES.includes(f.type)) {
        if (f.parentID) return void children.add(f.sessionID)
        const text = guard(root, "start", f.sessionID)
        if (text) send(f.sessionID, text, true)
      } else if (f.idle && !children.has(f.sessionID)) {
        const reason = guard(root, "stop", f.sessionID)
        if (reason) send(f.sessionID, reason, false)
      }
    },
  }
}

export default { ...v2, server }
