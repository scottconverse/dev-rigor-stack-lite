# dev-rigor-stack-lite

**[Website](https://scottconverse.github.io/dev-rigor-stack-lite/)** ·
[Manual](docs/manual.md) ·
[Architecture](docs/architecture.md) ·
[Troubleshooting](docs/troubleshooting.md) ·
[Releases](https://github.com/scottconverse/dev-rigor-stack-lite/releases)

A portable, evidence-first development and release workflow for AI coding agents. It
contains the complete 19-skill workflow from `codex-dev-rigor-stack`, adapted to run
without lifecycle hooks, a background runtime, trust activation, Stop interception, or a
private evidence ledger — plus two drift-resistance layers that **install by default
with everything else**: a small **anchor block** for the host's persistent instructions
file, and **rigor-goals**, a stdlib-only CLI whose exit gate refuses to close a
continuity-sensitive multi-story job without verification evidence.

These are part of the stack, not extras. Skills alone are advice — a model can drift
off them in a long session and nothing pushes back; the anchor and the goals gate are
what make the discipline hold. There is no on-switch because they are never off. There
IS an off-switch (`--no-anchor` / `--no-goals`, or deleting the anchor block) — and it
belongs to the human owner alone. An agent never passes the opt-outs or disables the
block on its own initiative; the anchor text itself carries that rule.

## The three tiers

Model attention decays over a long session and dies at context compaction; hooks fight
that with per-turn injection but are host-specific. The Lite architecture instead moves
the discipline's memory into places that do not decay:

| Tier | What | Force | Why it resists drift |
|---|---|---|---|
| 1 | The 19 skills | none — invoked knowledge | — |
| 2 | Anchor block in `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` | reminder every turn | the host re-reads its instructions file each turn |
| 3 | `rigor-goals` CLI | one hard gate at "done" | state lives in `./.rigor/` on disk — survives compaction and session death; the *refusal* is a program, not a prompt (what it checks is that evidence is named and recorded — see the precision note below) |

The anchor routes work by risk and invokes `rigor-goals` only when work crosses sessions,
needs a handoff, uses parallel agents, or waits on an external event.

## What changes in Lite

- Skills, references, templates, and deterministic helper scripts remain.
- Evidence comes from ordinary commands, logs, CI, screenshots, traces, hashes, and reports.
- Host policies control delegation, approvals, merges, publishing, and available tools.
- Passing a gate establishes readiness; it never grants the agent authority to merge or publish.
- Missing capabilities are reported as blocked or unverifiable rather than silently passed.

## Proportional rigor

| Lane | Typical work | Required flow |
|---|---|---|
| Micro | Localized copy, docs, formatting, mechanical edit with no Critical trigger | Inspect → change → one runnable check → receipt |
| Standard | Ordinary bug, feature, refactor, or shared-code change | Brief acceptance; RED/GREEN where applicable; affected tests; focused review |
| Critical | Auth/secrets, money, persistence/migrations/deletion, security/privacy, concurrency/order/idempotency, install/deploy/rollback, irreversible work, broad public contracts | Full independent proof path |

File count, file type, labels such as `medium+`, and release status do not select a lane.
Release adds exact-candidate and owner-authority controls, then runs only applicable gates.
The default closure rule is zero unresolved release blockers; every nonblocking finding
remains visible in the watchlist.

## Compatibility

The bundle uses the portable Agent Skills layout: one directory per skill with a
`SKILL.md` containing `name` and `description` YAML frontmatter. It is designed for:

- OpenAI Codex: `~/.codex/skills`
- Claude Code: project `.claude/skills` or user `~/.claude/skills`
- Google Antigravity: project `.agents/skills` or user `~/.gemini/config/skills`
- Other Agent Skills-compatible hosts

The Markdown workflows are portable; tool availability and instruction adherence vary by
host and model. This repository does not claim mechanical enforcement.

## Fast start

Requirements: Git, Python 3, and either Windows PowerShell 5.1+ or a POSIX shell.

### 1. Acquire the pinned release source

```console
git clone --branch v0.4.2 --depth 1 https://github.com/scottconverse/dev-rigor-stack-lite.git
cd dev-rigor-stack-lite
```

### 2. Install

Choose one target below. Run project-local commands from the project you are configuring
so its default anchor lands in that project. The relative commands shown here configure
the pinned checkout itself. To configure a different project, change to that project and
invoke the pinned installer by its absolute path; the [manual](docs/manual.md) shows both
forms.

PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target "$HOME\.codex\skills"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".agents\skills"
```

`-ExecutionPolicy Bypass` applies only to that child PowerShell process; it does not
change the execution policy for the user or machine.

Bash:

```sh
./install.sh "$HOME/.codex/skills"
./install.sh .claude/skills
./install.sh .agents/skills
```

### 3. Verify

```console
python tools/validate_bundle.py
```

On systems where Python 3 is named `python3`, use that command instead.

### 4. Start a continuity-sensitive unit

```console
python .claude/tools/rigor_goals.py create --brief "ship the unit" --goal "build::implement and test"
```

Adjust the tool path for the target you installed. See the
[manual](docs/manual.md) for all hosts and the complete lifecycle.

Use `rigor-goals` only for cross-session work, handoffs, parallel agents, or an external
wait. Ordinary same-session work does not need a durable plan.

Installation copies only the 19 directories under `skills/`. Existing directories with
the same names are refused unless `-Force` or `--force` is supplied.

### The anchor block and rigor-goals install by default

A plain `./install.sh .claude/skills` (or the process-scoped PowerShell form above)
installs all three tiers: the 19 skills, the `rigor-goals` tool, and the anchor block.
Defaults are inferred from the target:

| Target pattern | Default goals location | Default anchor location |
|---|---|---|
| `$HOME/.codex/skills` | `$HOME/.codex/tools` | `AGENTS.md` in the current directory |
| `.claude/skills` | `.claude/tools` | `CLAUDE.md` in the current directory |
| `.agents/skills` (Antigravity project) | `.agents/tools` | `AGENTS.md` in the current directory |
| `$HOME/.gemini/config/skills` (Antigravity user) | `$HOME/.gemini/config/tools` | `$HOME/.gemini/config/AGENTS.md`, beside the skills directory |
| `.gemini/skills` (Gemini CLI) | `.gemini/tools` | `GEMINI.md` in the current directory |

`--anchor FILE` / `-Anchor` and `--goals DIR` / `-Goals` override the default locations.
The anchor install is idempotent: on upgrade the marker-fenced block is replaced in
place, hand edits outside the markers survive, and a diff is printed.

`--no-anchor` / `-NoAnchor` and `--no-goals` / `-NoGoals` are **owner-only opt-outs**.
They exist so the human who owns the machine can turn the discipline off; an agent
running the installer must never pass them on its own initiative.

For an upgrade or same-version repair, acquire the intended source version and rerun the
same command with `--force` or `-Force`. This replaces managed skill/tool bytes while
preserving text outside the anchor markers. Safe removal must delete only the 19
manifest-owned skill directories, the one managed tool file, and the single
marker-fenced anchor span; follow the preview-and-preserve procedure in the
[manual](docs/manual.md).

### rigor-goals in 30 seconds

```sh
python3 tools/rigor_goals.py create --brief "ship feature X" \
  --goal "api::add the endpoint" --goal "docs::update the manual"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G001 --status complete --evidence "test_api.py: 4 passed"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G002 --status complete --evidence "manual updated" \
  --verify-cmd "pytest && python tools/validate_bundle.py" --verify-evidence "12 passed; BUNDLE_VALID"
python3 tools/rigor_goals.py status
```

The final story refuses to complete without `--verify-cmd` and `--verify-evidence` —
that refusal is the point. State lives in `./.rigor/` (add it to `.gitignore` or commit
it; your choice). A fresh session resumes with `status`.

Be precise about what the gate is: `rigor-goals` **records** the verification command
and its result — it does not run the command or check the result is true. It is a
workflow-completeness gate (no story closes without named evidence), not independent
proof enforcement. The honesty of the evidence is the agent's obligation and the
reviewer's to check. One active plan per working tree: concurrent tasks sharing a
checkout will fight over `./.rigor/` — use separate worktrees.

**Known limitation — the state is a file, not a fortress.** Any process that can delete
files in the workspace can destroy the plan, and nothing in-repo can detect a deletion
that also removes the ledger. Replacing a plan is loud (`create --force` prints what it
destroys, and every ledger event carries a `plan_id`), but if other agents or tools share
the same checkout, commit `./.rigor/` or back it up externally — the gate is only as
durable as the files it lives in.

## Main entrypoints

- `dev-rigor-stack-lite` — route Micro, Standard, or Critical and coordinate applicable gates
- `dev-rigor-stack-lite-plan`
- `dev-rigor-stack-lite-build`
- `dev-rigor-stack-lite-proof-gate`
- `dev-rigor-stack-lite-audit-lite`
- `dev-rigor-stack-lite-audit-team`
- `dev-rigor-stack-lite-walkthrough`
- `dev-rigor-stack-lite-visitor-audit`
- `dev-rigor-stack-lite-gauntletgate`
- `dev-rigor-stack-lite-merge-gate`
- `dev-rigor-stack-lite-docs-gate`
- `dev-rigor-stack-lite-continuity`
- `dev-rigor-stack-lite-release`

Six short-name entrypoints are also included: `coder-tdd-qa-lite`, `proof-gate-lite`,
`quick-audit-lite`, `audit-team-lite`, `gauntletgate-lite`, and `visitor-audit-lite`.
(`quick-audit-lite` was `audit-lite` before 0.3.1 — renamed because it was the one name
that collided with, and could silently overwrite, a full dev-rigor-stack install sharing
the same skills directory.)

## Validate

```sh
python tools/validate_bundle.py
```

## Documentation

- [User and operator manual](docs/manual.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE) and [third-party notice](NOTICE.md)

## Provenance

This is a hook-free adaptation of the private upstream
`scottconverse/codex-dev-rigor-stack`, originally released under the MIT License.
See [NOTICE.md](NOTICE.md).

## License

MIT
