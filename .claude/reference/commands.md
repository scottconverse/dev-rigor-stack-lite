# dev-rigor-stack-lite commands reference

Moved verbatim from CLAUDE.md.

## Commands

Python 3.12, stdlib only. No package manager. Two test entrypoints:

```bash
python tools/validate_bundle.py
python tools/test_rigor_goals.py
```

`validate_bundle.py` prints `BUNDLE_VALID` / `BUNDLE_INVALID` and exits nonzero on failure.
It is both the bundle contract check and a live smoke test of the goals gate.

There is no test framework and no per-test selection — each file is a single runnable script.
Use `python3` on systems where Python 3 is named that.

Install to a scratch project (never install over this repo's own `CLAUDE.md` while testing):

```bash
./install.sh .claude/skills
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills"
```

Exercise the goals CLI:

```bash
python3 tools/rigor_goals.py create --brief "ship X" --goal "api::add the endpoint"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G001 --status complete --evidence "4 passed" --verify-cmd "pytest" --verify-evidence "12 passed"
python3 tools/rigor_goals.py status
```

<!-- moved verbatim from CLAUDE.md, 2026-10-09 -->

## The three tiers

| Tier | What | Force |
|---|---|---|
| 1 | 19 skills under `skills/<name>/SKILL.md` | none — invoked knowledge |
| 2 | `anchor/anchor.md`, a marker-fenced block written into the host's `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` | reminder every turn (host re-reads its instructions file) |
| 3 | `tools/rigor_goals.py`, a stdlib-only CLI with a verification exit gate; state in `./.rigor/` | one hard refusal at "done", surviving compaction and session death |

The reasoning: model attention decays over a long session and dies at compaction. Hooks fight
that with per-turn injection but are host-specific, so Lite moves the discipline's memory into
places that do not decay — the instructions file and on-disk state.

## Install target inference

The installer infers the goals dir and anchor file from the skills target:

| Target | Goals | Anchor |
|---|---|---|
| `$HOME/.codex/skills` | `$HOME/.codex/tools` | `AGENTS.md` (cwd) |
| `.claude/skills` | `.claude/tools` | `CLAUDE.md` (cwd) |
| `.agents/skills` | `.agents/tools` | `AGENTS.md` (cwd) |
| `$HOME/.gemini/config/skills` | `$HOME/.gemini/config/tools` | `$HOME/.gemini/config/AGENTS.md` |
| `.gemini/skills` | `.gemini/tools` | `GEMINI.md` (cwd) |

Override with `--anchor FILE` / `-Anchor` and `--goals DIR` / `-Goals`.
