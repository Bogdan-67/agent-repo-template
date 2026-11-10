#!/usr/bin/env python3
"""docs_guard: keep the repository the single source of truth for coding agents.

One core, thin adapters per agent harness. Standard library only, Python 3.8+.

Usage
  docs_guard.py start  --harness H [--session ID] [--cwd PATH]   session start: baseline + context
  docs_guard.py prompt --harness kimi ...                        Kimi: context on first prompt
  docs_guard.py stop   --harness H [--session ID] [--cwd PATH]   end of turn: block if docs not updated
  docs_guard.py commit                                           git pre-commit gate (staged files)
  docs_guard.py commit-msg FILE                                  git commit-msg gate: no AI attribution
  docs_guard.py ci [--base REF]                                  CI gate (diff BASE...HEAD)
  docs_guard.py check [--hours N]                                manual check of recent edits
  docs_guard.py self-test                                        run built-in scenarios in a temp repo

Harnesses (H): claude, codex, cursor, gemini, copilot, kimi, opencode.
Hook payload is read from stdin as JSON (session_id/sessionId, cwd, stop_hook_active, loop_count);
--session/--cwd override it. Settings: .agents/guard.json. Rules: AGENTS.md, "Session protocol".

Exit codes: 0 allow; 2 block (kimi only); 1 gate failed (commit/ci/check/self-test).
A hook must never break the agent: unexpected errors are reported on stderr and allowed.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESSES = ("claude", "codex", "cursor", "gemini", "copilot", "kimi", "opencode")
DEFAULTS = {
    "status_file": "STATUS.md", "status_max_lines": 150,
    "open_questions_file": "OPEN_QUESTIONS.md", "open_questions_max_lines": 200,
    "agents_md_max_bytes": 32768, "journal_dir": "docs/journal", "adr_dir": "docs/adr",
    "handoff_dir": "docs/handoff",
    "doc_files": ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "STATUS.md", "OPEN_QUESTIONS.md",
                  "GLOSSARY.md", "STRUCTURE.md", "README.md", "CHANGELOG.md"],
    "doc_prefixes": ["docs/", ".agents/", ".claude/", ".codex/", ".opencode/", ".gemini/",
                     ".github/", ".githooks/", ".cursor/"],
    "significant_extensions": [".py", ".ts", ".js", ".sh", ".yaml", ".yml", ".toml", ".json", ".md", ".sql"],
    "significant_names": ["Dockerfile", "Makefile"],
    "ignore_patterns": [], "state_patterns": [], "decision_patterns": [],
    "frozen_globs": [], "freeze_past_journal_months": True,
    "require_journal_mentions_changed_file": True, "max_consecutive_blocks": 1,
    "context_files": ["STATUS.md", "docs/adr/README.md"], "context_journal_tail_lines": 30,
    "context_cap_chars": 12000,
    "forbidden_commit_patterns": ["(?im)^co-authored-by:.*(claude|anthropic|openai|chatgpt|codex|\\bgpt|copilot|gemini|google-labs|jules|kimi|moonshot|deepseek|qwen|glm|zhipu|z\\.ai|cursor|windsurf|devin|cline|aider|opencode|\\bamp\\b|junie|bot@|noreply@anthropic\\.com)", "(?im)^.*generated (with|by) .*(claude|codex|copilot|gemini|cursor|kimi|opencode|aider|ai)\\b", "(?im)^claude-session:", "(?i)claude\\.ai/code/session"],
}


# --------------------------------------------------------------------------- helpers

def git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false", *args],
                         capture_output=True, text=True)
    return out.stdout


def repo_root(start: str) -> Path:
    top = git(Path(start), "rev-parse", "--show-toplevel").strip()
    return Path(top or start).resolve()


def load_cfg(root: Path) -> dict:
    cfg = dict(DEFAULTS)
    f = root / ".agents" / "guard.json"
    if f.exists():
        try:
            cfg.update({k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                        if not k.startswith("_")})
        except (OSError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"docs_guard: cannot read {f}: {exc}\n")
    return cfg


def state_dir(root: Path) -> Path:
    gitdir = git(root, "rev-parse", "--absolute-git-dir").strip()
    d = Path(gitdir or root / ".git") / "agent-guard"
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_id(s) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(s or "nosession"))[:100]


def mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def dirty_paths(root: Path) -> list:
    """Modified, added, untracked and deleted files of the work tree (git-ignored files excluded)."""
    out = git(root, "status", "--porcelain=v1", "-z", "-uall", "--no-renames")
    return [rec[3:] for rec in out.split("\0") if len(rec) > 3]


def now() -> dt.datetime:
    return dt.datetime.now()


# --------------------------------------------------------------------------- classification

class Rules:
    def __init__(self, root: Path, cfg: dict):
        self.root, self.cfg = root, cfg
        self.ignore = [re.compile(p) for p in cfg["ignore_patterns"]]
        self.state = [re.compile(p) for p in cfg["state_patterns"]]
        self.decision = [re.compile(p) for p in cfg["decision_patterns"]]
        self.exts = {e.lower() for e in cfg["significant_extensions"]}
        self.names = set(cfg["significant_names"])
        self.journal_dir = cfg["journal_dir"].rstrip("/")

    def is_doc(self, p: str) -> bool:
        return p in self.cfg["doc_files"] or p.startswith(tuple(self.cfg["doc_prefixes"]))

    def is_significant(self, p: str) -> bool:
        if self.is_doc(p) or any(r.search(p) for r in self.ignore):
            return False
        name = Path(p).name
        return Path(p).suffix.lower() in self.exts or name in self.names

    def is_state(self, p: str) -> bool:
        return any(r.search(p) for r in self.state)

    def is_decision(self, p: str) -> bool:
        return any(r.search(p) for r in self.decision)

    def journal_rel(self, when: dt.datetime) -> str:
        return f"{self.journal_dir}/{when:%Y-%m}.md"

    def is_frozen(self, p: str, when: dt.datetime) -> bool:
        if any(fnmatch.fnmatch(p, g) for g in self.cfg["frozen_globs"]):
            return True
        if self.cfg["freeze_past_journal_months"]:
            m = re.fullmatch(re.escape(self.journal_dir) + r"/(\d{4})-(\d{2})\.md", p)
            if m and (int(m.group(1)), int(m.group(2))) < (when.year, when.month):
                return True
        return False


def today_section(text: str, day: str) -> str:
    """Text under every '## <today>...' heading of the journal (until the next '## ' heading)."""
    out, take = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            take = line[3:].strip().startswith(day)
            continue
        if take:
            out.append(line)
    return "\n".join(out)


def journal_problems(rules: Rules, changed: list, journal_text: str, when: dt.datetime) -> list:
    rel = rules.journal_rel(when)
    day = f"{when:%Y-%m-%d}"
    section = today_section(journal_text, day)
    if f"## {day}" not in journal_text:
        return [f"`{rel}` has no entry heading starting with `## {day}`. Add one: what was done, "
                f"paths of changed files and artifacts, review status."]
    if rules.cfg["require_journal_mentions_changed_file"] and changed:
        if not any(p in section or Path(p).name in section for p in changed):
            sample = ", ".join(f"`{p}`" for p in changed[:5])
            return [f"Today's entry in `{rel}` does not mention any changed file ({sample}). "
                    f"Name the files or artifacts the work touched."]
    return []


def size_problems(rules: Rules) -> list:
    cfg, probs = rules.cfg, []
    for key_file, key_max in (("status_file", "status_max_lines"),
                              ("open_questions_file", "open_questions_max_lines")):
        f = rules.root / cfg[key_file]
        n = len(read(f).splitlines())
        if f.exists() and n > cfg[key_max]:
            probs.append(f"`{cfg[key_file]}` has {n} lines (limit {cfg[key_max]}). It is a snapshot, not a "
                         f"log: move outdated blocks to `{rules.journal_rel(now())}` and shorten it.")
    agents = rules.root / "AGENTS.md"
    if agents.exists() and agents.stat().st_size > cfg["agents_md_max_bytes"]:
        probs.append(f"`AGENTS.md` is {agents.stat().st_size} bytes (limit {cfg['agents_md_max_bytes']}, "
                     f"Codex truncates the AGENTS.md chain at 32 KiB). Move details to linked docs.")
    return probs


def adr_notes(rules: Rules, paths: list, root: Path) -> list:
    adr = rules.cfg["adr_dir"].rstrip("/") + "/"
    tracked = set(git(root, "ls-files", adr).split("\n"))
    edited = [p for p in paths if p.startswith(adr) and p in tracked and not p.endswith("README.md")]
    if edited:
        return ["Existing ADRs were edited (" + ", ".join(f"`{p}`" for p in edited[:5]) + "). Accepted ADRs "
                "are immutable: only the status line may change (e.g. `superseded by ADR-NNNN`); "
                "record a new decision as a new ADR."]
    return []


def evaluate_paths(rules: Rules, changed_sig: list, state_changed: list, decision_changed: list,
                   frozen_touched: list, journal_text: str, journal_updated: bool,
                   status_updated: bool, adr_touched: bool, when: dt.datetime) -> tuple:
    problems, notes = [], []
    for p in frozen_touched:
        problems.append(f"Frozen file `{p}` was modified. It is append-protected history: restore it "
                        f"(`git checkout -- {p}`) and write the entry to `{rules.journal_rel(when)}`.")
    if changed_sig:
        rel = rules.journal_rel(when)
        if not journal_updated:
            sample = ", ".join(f"`{p}`" for p in changed_sig[:8])
            more = f" and {len(changed_sig) - 8} more" if len(changed_sig) > 8 else ""
            problems.append(f"Files changed ({sample}{more}) but the journal `{rel}` was not updated "
                            f"after them. Append an entry under `## {when:%Y-%m-%d} <topic>`: what was done, "
                            f"paths, review status.")
        else:
            problems += journal_problems(rules, changed_sig, journal_text, when)
        if state_changed and not status_updated:
            problems.append("Results or experiment configuration changed (" +
                            ", ".join(f"`{p}`" for p in state_changed[:5]) +
                            f") but `{rules.cfg['status_file']}` was not updated. Rewrite the affected block; "
                            "if the state truly did not change, say so in the journal entry and bump the "
                            "date line in STATUS.")
        if decision_changed and not adr_touched:
            notes.append("Configuration that often encodes decisions changed (" +
                         ", ".join(f"`{p}`" for p in decision_changed[:5]) +
                         "). If a user decision or a choice between alternatives was made, record an ADR "
                         f"in `{rules.cfg['adr_dir']}/` and reference it instead of restating it.")
    problems += size_problems(rules)
    return problems, notes


# --------------------------------------------------------------------------- session (hooks)

def baseline_file(root: Path, sid: str) -> Path:
    return state_dir(root) / f"{safe_id(sid)}.json"


def make_baseline(root: Path, sid: str) -> dict:
    data = {"start": now().timestamp(), "dirty": {p: mtime(root / p) for p in dirty_paths(root)}}
    baseline_file(root, sid).write_text(json.dumps(data), encoding="utf-8")
    return data


def context_text(root: Path, rules: Rules) -> str:
    cfg, when = rules.cfg, now()
    parts = [f"[docs_guard] Project memory lives in this repository. Read AGENTS.md before working. "
             f"Before you finish a turn that changed code, configs or reports, append an entry to "
             f"`{rules.journal_rel(when)}` under `## {when:%Y-%m-%d} <topic>` naming the changed files, "
             f"update `{cfg['status_file']}` if results changed, and record decisions as ADRs. "
             f"A hook will check this."]
    warn = state_dir(root) / "pending_warnings.md"
    if read(warn).strip():
        parts.append("## Not done in a previous session (fix first)\n" + read(warn).strip())
        try:
            warn.unlink()
        except OSError:
            pass
    for rel in cfg["context_files"]:
        txt = read(root / rel)
        if txt.strip():
            parts.append(f"## {rel}\n{txt.strip()}")
    hand = root / cfg["handoff_dir"]
    if hand.is_dir():
        opened = [p for p in sorted(hand.glob("*.md")) if p.name.upper() != "TEMPLATE.MD"
                  and re.search(r"(?im)^\s*-?\s*status:\s*open", read(p)[:800])]
        for p in opened[-2:]:
            parts.append(f"## Open handoff: {p.relative_to(root).as_posix()}\n{read(p).strip()}")
    tail = cfg["context_journal_tail_lines"]
    jt = read(root / rules.journal_rel(when)).splitlines()
    if tail and jt:
        parts.append(f"## Tail of {rules.journal_rel(when)}\n" + "\n".join(jt[-tail:]))
    text = "\n\n".join(parts)
    cap = cfg["context_cap_chars"]
    return text if len(text) <= cap else text[:cap] + "\n\n[truncated by docs_guard; read the files]"


def emit_context(harness: str, text: str) -> None:
    if harness in ("kimi", "opencode"):
        print(text)
    elif harness == "copilot":
        print(json.dumps({"additionalContext": text}, ensure_ascii=False))
    else:  # claude, codex, cursor, gemini
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": text}}, ensure_ascii=False))


def cmd_start(p: dict, harness: str) -> int:
    root = repo_root(p.get("cwd") or os.getcwd())
    rules = Rules(root, load_cfg(root))
    sid = p.get("session_id")
    if not baseline_file(root, sid).exists():  # resume/compact keep the original baseline
        make_baseline(root, sid)
    if harness == "kimi":  # Kimi SessionStart is observe-only; context goes via UserPromptSubmit
        return 0
    emit_context(harness, context_text(root, rules))
    return 0


def cmd_prompt(p: dict, harness: str) -> int:
    root = repo_root(p.get("cwd") or os.getcwd())
    rules = Rules(root, load_cfg(root))
    sid = p.get("session_id")
    if not baseline_file(root, sid).exists():
        make_baseline(root, sid)
    marker = state_dir(root) / f"{safe_id(sid)}.ctx"
    if marker.exists():
        return 0
    marker.write_text("1", encoding="utf-8")
    print(context_text(root, rules))
    return 0


def session_eval(root: Path, rules: Rules, base: dict) -> tuple:
    start, base_dirty, when = base["start"], base.get("dirty", {}), now()
    changed, state, decision, frozen, all_touched = [], [], [], [], []
    for p in dirty_paths(root):
        full = root / p
        touched = mtime(full) > start if full.exists() else p not in base_dirty
        if not touched:
            continue
        all_touched.append(p)
        if rules.is_frozen(p, when):
            frozen.append(p)
        elif rules.is_significant(p):
            changed.append((p, mtime(full) if full.exists() else when.timestamp()))
            if rules.is_state(p):
                state.append(p)
            if rules.is_decision(p):
                decision.append(p)
    jpath = root / rules.journal_rel(when)
    last = max((t for _, t in changed), default=0.0)
    adr_dir = root / rules.cfg["adr_dir"]
    adr_touched = any(mtime(f) > start for f in adr_dir.glob("*.md")) if adr_dir.is_dir() else False
    problems, notes = evaluate_paths(
        rules, [p for p, _ in sorted(changed)], state, decision, frozen, read(jpath),
        journal_updated=mtime(jpath) >= last and mtime(jpath) > start,
        status_updated=mtime(root / rules.cfg["status_file"]) > start,
        adr_touched=adr_touched, when=when)
    notes += adr_notes(rules, all_touched, root)
    return problems, notes


def cmd_stop(p: dict, harness: str) -> int:
    root = repo_root(p.get("cwd") or os.getcwd())
    rules = Rules(root, load_cfg(root))
    sid = p.get("session_id")
    bf = baseline_file(root, sid)
    if not bf.exists():  # hook enabled mid-session: start counting now
        make_baseline(root, sid)
        return 0
    problems, notes = session_eval(root, rules, json.loads(read(bf) or "{}"))
    counter = state_dir(root) / f"{safe_id(sid)}.blocks"
    if not problems:
        if counter.exists():
            counter.unlink()
        return 0
    blocks = int(read(counter) or 0)
    # stop_hook_active / loop_count mean the harness is already retrying; the own counter covers
    # harnesses without such a flag (Kimi, OpenCode) and makes the limit identical everywhere.
    if blocks >= rules.cfg["max_consecutive_blocks"]:
        # Already blocked and still not fixed: release to avoid a loop, hand the debt to the next session.
        if counter.exists():
            counter.unlink()
        with (state_dir(root) / "pending_warnings.md").open("a", encoding="utf-8") as fh:
            fh.write(f"### {now():%Y-%m-%d %H:%M} session {safe_id(sid)} ({harness})\n"
                     + "\n".join(f"- {x}" for x in problems) + "\n\n")
        return 0
    counter.write_text(str(blocks + 1), encoding="utf-8")
    reason = ("Documentation is not up to date, so this turn is not finished "
              "(AGENTS.md, Session protocol; checked by .agents/hooks/docs_guard.py):\n"
              + "\n".join(f"{i}. {x}" for i, x in enumerate(problems, 1)))
    if notes:
        reason += "\n\nAlso consider:\n" + "\n".join(f"- {n}" for n in notes)
    reason += ("\n\nFix these and then finish. Write real content: an entry that does not describe the "
               "work defeats the purpose of the check.")
    if harness == "kimi":
        sys.stderr.write(reason + "\n")
        return 2
    if harness == "opencode":
        print(reason)
    elif harness == "gemini":
        print(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
    else:
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- gates (commit, ci, check)

def gate_from_paths(root: Path, rules: Rules, paths: list, modified_existing: set, label: str) -> int:
    when = now()
    jrel = rules.journal_rel(when)
    sig = sorted(p for p in paths if rules.is_significant(p) and not rules.is_frozen(p, when))
    frozen = sorted(p for p in paths if rules.is_frozen(p, when) and p in modified_existing)
    journal_changed = any(p.startswith(rules.journal_dir + "/") and not rules.is_frozen(p, when)
                          for p in paths)
    problems, notes = evaluate_paths(
        rules, sig, [p for p in sig if rules.is_state(p)], [p for p in sig if rules.is_decision(p)],
        frozen, read(root / jrel), journal_updated=journal_changed or not sig,
        status_updated=rules.cfg["status_file"] in paths,
        adr_touched=any(p.startswith(rules.cfg["adr_dir"].rstrip("/") + "/") for p in paths), when=when)
    if label == "ci" and journal_changed:  # in CI the entry may be dated earlier than today
        problems = [x for x in problems if "has no entry heading" not in x and "does not mention" not in x]
    notes += adr_notes(rules, [p for p in paths if p in modified_existing], root)
    for x in problems:
        print(f"docs_guard [{label}] FAIL: {x}")
    for n in notes:
        print(f"docs_guard [{label}] note: {n}")
    if problems:
        print(f"docs_guard [{label}]: see AGENTS.md, Session protocol. Do not bypass with --no-verify.")
    return 1 if problems else 0


def cmd_commit() -> int:
    root = repo_root(os.getcwd())
    rules = Rules(root, load_cfg(root))
    out = git(root, "diff", "--cached", "--name-status", "--no-renames")
    paths, modified = [], set()
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            paths.append(path)
            if status[:1] in ("M", "D"):
                modified.add(path)
    return gate_from_paths(root, rules, paths, modified, "commit")


def attribution_problems(cfg: dict, message: str) -> list:
    """Lines of a commit message that attribute the commit to an AI agent or model."""
    body = "\n".join(l for l in message.splitlines() if not l.startswith("#"))  # drop git comments
    found = []
    for pat in cfg["forbidden_commit_patterns"]:
        for m in re.finditer(pat, body):
            line = body[body.rfind("\n", 0, m.start()) + 1:].split("\n", 1)[0].strip()
            if line and line not in found:
                found.append(line)
    return found


def cmd_commit_msg(path: str) -> int:
    root = repo_root(os.getcwd())
    cfg = load_cfg(root)
    bad = attribution_problems(cfg, read(Path(path)))
    for line in bad:
        print(f"docs_guard [commit-msg] FAIL: AI attribution is forbidden in commit messages: {line!r}")
    if bad:
        print("docs_guard [commit-msg]: remove these lines (AGENTS.md, Hard rules). Commits are the user's; "
              "do not bypass with --no-verify.")
    return 1 if bad else 0


def cmd_ci(base: str) -> int:
    root = repo_root(os.getcwd())
    rules = Rules(root, load_cfg(root))
    out = git(root, "diff", "--name-status", "--no-renames", f"{base}...HEAD")
    paths, modified = [], set()
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            paths.append(path)
            if status[:1] in ("M", "D"):
                modified.add(path)
    rc = gate_from_paths(root, rules, paths, modified, "ci")
    log = git(root, "log", "--format=%H%x00%B%x01", f"{base}..HEAD")
    for rec in log.split("\x01"):
        sha, _, msg = rec.strip().partition("\x00")
        for line in attribution_problems(rules.cfg, msg):
            print(f"docs_guard [ci] FAIL: commit {sha[:10]} has AI attribution: {line!r}")
            rc = 1
    return rc


def cmd_check(hours: float) -> int:
    root = repo_root(os.getcwd())
    rules = Rules(root, load_cfg(root))
    base = {"start": now().timestamp() - hours * 3600, "dirty": {}}
    problems, notes = session_eval(root, rules, base)
    for x in problems:
        print("FAIL:", x)
    for n in notes:
        print("note:", n)
    if not problems and not notes:
        print(f"OK: nothing to report for edits in the last {hours:g} h")
    return 1 if problems else 0


# --------------------------------------------------------------------------- self-test

def cmd_self_test() -> int:
    import time
    me = Path(__file__).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="docs_guard_selftest_"))
    ok = True

    def sh(*a):
        return subprocess.run(a, cwd=tmp, capture_output=True, text=True, stdin=subprocess.DEVNULL)

    def run(*a):
        return sh(sys.executable, str(tmp / ".agents/hooks/docs_guard.py"), *a)

    def expect(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok &= bool(cond)

    try:
        sh("git", "init", "-q")
        sh("git", "config", "user.email", "t@t")
        sh("git", "config", "user.name", "t")
        (tmp / ".agents/hooks").mkdir(parents=True)
        shutil.copy(me, tmp / ".agents/hooks/docs_guard.py")
        (tmp / "docs/journal").mkdir(parents=True)
        (tmp / "src").mkdir()
        (tmp / "STATUS.md").write_text("# Status\n", encoding="utf-8")
        (tmp / "src/app.py").write_text("x = 1\n", encoding="utf-8")
        old = tmp / "docs/journal/2000-01.md"
        old.write_text("# old\n", encoding="utf-8")
        sh("git", "add", "-A")
        sh("git", "commit", "-qm", "init")
        day, month = f"{now():%Y-%m-%d}", f"{now():%Y-%m}"
        jfile = tmp / f"docs/journal/{month}.md"

        def session(sid, harness="claude"):
            r = run("start", "--harness", harness, "--session", sid, "--cwd", str(tmp))
            time.sleep(1.1)
            return r

        def stop(sid, harness="claude"):
            return run("stop", "--harness", harness, "--session", sid, "--cwd", str(tmp))

        r = session("a")
        expect("start emits additionalContext", "additionalContext" in r.stdout)
        expect("stop with no edits passes", stop("a").stdout.strip() == "")
        (tmp / "src/app.py").write_text("x = 2\n", encoding="utf-8")
        expect("code edit without journal blocks (claude)", '"decision": "block"' in stop("a").stdout)
        expect("second failure releases (anti-loop)", stop("a").stdout.strip() == "")
        r = session("b")
        expect("debt handed to next session", "Not done in a previous session" in r.stdout)
        (tmp / "src/app.py").write_text("x = 3\n", encoding="utf-8")
        r = stop("b", "kimi")
        expect("kimi blocks with exit 2", r.returncode == 2 and "journal" in r.stderr)
        expect("gemini without baseline passes", stop("never-started", "gemini").stdout.strip() == "")
        session("c")
        (tmp / "src/app.py").write_text("x = 4\n", encoding="utf-8")
        time.sleep(1.1)
        jfile.write_text(f"# J\n\n## {day} vague\nstuff\n", encoding="utf-8")
        expect("entry must mention changed file", "does not mention" in stop("c", "opencode").stdout)
        session("d")
        (tmp / "src/app.py").write_text("x = 5\n", encoding="utf-8")
        time.sleep(1.1)
        jfile.write_text(f"# J\n\n## {day} app fix\nChanged `src/app.py`.\n", encoding="utf-8")
        expect("journal mentioning the file passes", stop("d", "codex").stdout.strip() == "")
        session("e")
        old.write_text("# old\nedited\n", encoding="utf-8")
        expect("past-month journal is frozen", "Frozen file" in stop("e", "copilot").stdout)
        sh("git", "checkout", "--", "docs/journal/2000-01.md")
        session("f")
        (tmp / "STATUS.md").write_text("x\n" * 200, encoding="utf-8")
        r = stop("f", "gemini")
        expect("oversized STATUS blocks (gemini deny)", "lines (limit" in r.stdout and '"deny"' in r.stdout)
        (tmp / "STATUS.md").write_text("# Status\n", encoding="utf-8")
        sh("git", "add", "src/app.py")
        r = sh(sys.executable, str(tmp / ".agents/hooks/docs_guard.py"), "commit")
        expect("pre-commit fails without staged journal", r.returncode == 1)
        sh("git", "add", f"docs/journal/{month}.md")
        r = sh(sys.executable, str(tmp / ".agents/hooks/docs_guard.py"), "commit")
        expect("pre-commit passes with staged journal", r.returncode == 0)
        msg = tmp / "msg.txt"
        msg.write_text("Fix app\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>\n", encoding="utf-8")
        r = sh(sys.executable, str(tmp / ".agents/hooks/docs_guard.py"), "commit-msg", str(msg))
        expect("commit-msg rejects AI co-author", r.returncode == 1 and "noreply@anthropic.com" in r.stdout)
        msg.write_text("Fix app\n\nCo-authored-by: Jane Doe <jane@example.com>\n", encoding="utf-8")
        r = sh(sys.executable, str(tmp / ".agents/hooks/docs_guard.py"), "commit-msg", str(msg))
        expect("commit-msg keeps human co-author", r.returncode == 0)
        r = run("prompt", "--harness", "kimi", "--session", "k1", "--cwd", str(tmp))
        r2 = run("prompt", "--harness", "kimi", "--session", "k1", "--cwd", str(tmp))
        expect("kimi context only on first prompt", "[docs_guard]" in r.stdout and r2.stdout == "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("self-test:", "OK" if ok else "FAILED")
    return 0 if ok else 1


# --------------------------------------------------------------------------- entry point

def parse(argv: list) -> tuple:
    opts, pos, it = {}, [], iter(argv)
    for a in it:
        if a.startswith("--"):
            key = a[2:]
            if "=" in key:
                key, val = key.split("=", 1)
            else:
                val = next(it, "")
            opts[key] = val
        else:
            pos.append(a)
    return pos, opts


def main() -> int:
    pos, opts = parse(sys.argv[1:])
    cmd = pos[0] if pos else "check"
    try:
        if cmd == "self-test":
            return cmd_self_test()
        if cmd == "commit":
            return cmd_commit()
        if cmd == "commit-msg":
            return cmd_commit_msg(pos[1] if len(pos) > 1 else ".git/COMMIT_EDITMSG")
        if cmd == "ci":
            return cmd_ci(opts.get("base") or "origin/HEAD")
        if cmd == "check":
            return cmd_check(float(opts.get("hours") or 12))
        harness = opts.get("harness", "claude")
        if harness not in HARNESSES:
            sys.stderr.write(f"docs_guard: unknown harness {harness}\n")
            return 0
        payload = {}
        if "session" not in opts and not sys.stdin.isatty():
            raw = sys.stdin.read()
            try:
                payload = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                payload = {}
        payload.setdefault("session_id", payload.get("sessionId") or os.environ.get("GEMINI_SESSION_ID"))
        if opts.get("session"):
            payload["session_id"] = opts["session"]
        if opts.get("cwd"):
            payload["cwd"] = opts["cwd"]
        if cmd == "start":
            return cmd_start(payload, harness)
        if cmd == "prompt":
            return cmd_prompt(payload, harness)
        if cmd == "stop":
            return cmd_stop(payload, harness)
        sys.stderr.write(f"docs_guard: unknown command {cmd}\n")
        return 0
    except Exception as exc:  # never break the agent
        sys.stderr.write(f"docs_guard: internal error {exc!r}\n")
        return 0 if cmd in ("start", "prompt", "stop") else 1


if __name__ == "__main__":
    sys.exit(main())
