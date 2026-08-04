# dev-rigor-stack-lite

**[Website](https://scottconverse.github.io/dev-rigor-stack-lite/)** ·
[Manual](docs/manual.md) ·
[Architecture](docs/architecture.md) ·
[Troubleshooting](docs/troubleshooting.md) ·
[Releases](https://github.com/scottconverse/dev-rigor-stack-lite/releases)

A portable, evidence-first development and release workflow for AI coding agents. It
contains the original workflow skills adapted from `codex-dev-rigor-stack`, plus a
text-first BRAINSTORM entrypoint adapted from `obra/superpowers`, for 20 skills total. It runs without
lifecycle hooks, a background runtime, trust activation, Stop interception, or a private
evidence ledger. Two drift-resistance layers **install by default with everything else**:
a small **anchor block** for the host's persistent instructions file, and **rigor-goals**,
a stdlib-only CLI that pins the engagement mode and
refuses to mistake a finished unit or an exhausted queue for a finished ongoing job.

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
| 1 | The 20 skills | none — invoked knowledge | — |
| 2 | Anchor block in `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` | persistent reminder | the instructions remain in session context and reload at host-defined boundaries; Claude Code also re-injects root `CLAUDE.md` after compaction |
| 3 | `rigor-goals` CLI | hard state transitions at "done" | state lives in `./.rigor/` on disk — survives compaction and session death; the *refusal* is a program, not a prompt (what it checks is that evidence is named and recorded — see the precision note below) |

The anchor routes work by risk and invokes `rigor-goals` only when work crosses sessions,
needs a handoff, uses parallel agents, or waits on an external event.

## What changes in Lite

- Skills, references, templates, and deterministic helper scripts remain.
- Optional BRAINSTORM discovery resolves material design ambiguity before PLAN.
  Explicit invocation always activates BRAINSTORM, even when the brief is decision-complete.
  Without explicit invocation, a decision-complete brief skips discovery, and Micro
  never gains a mandatory approval gate.
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

The executable release checks prove inventory, prompt-contract markers, installer
lifecycle behavior, and documentation consistency. The BRAINSTORM scenarios are an
evaluation rubric, not a behavioral test: neither the validator nor CI proves that a
host loads the skill or that a model follows it.

## Fast start

Requirements: Git, Python 3, and either Windows PowerShell 5.1+ or a POSIX shell.

> **Alone, or as part of the set.** This stack is fully standalone. It also installs
> together with [tampercheck](https://github.com/scottconverse/tampercheck) (whose
> verification-integrity receipts the VERIFY and MERGE gates cite when the tool is
> present) and [deterministic-detector](https://github.com/scottconverse/deterministic-detector)
> via one pinned command: [rigor-suite](https://github.com/scottconverse/rigor-suite).
> The layers stay independent — installed together, never mixed.

### 1. Acquire the pinned release source

```console
git clone --branch v0.7.0 --depth 1 https://github.com/scottconverse/dev-rigor-stack-lite.git
cd dev-rigor-stack-lite
```

### 2. Install

Choose one target below. The default anchor follows that target: a rooted user-host
target keeps the instructions file beside its skills directory, while a relative hidden
host target puts it in the containing project. To configure a different project, change
to that project and invoke the pinned installer by its absolute path; the
[manual](docs/manual.md) shows both forms.

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

Installation copies only the 20 directories under `skills/`. Before writing anything, a
read-only preflight validates the target, all manifest-name collisions, the goals and anchor
destinations, and the managed marker structure. Existing directories with the same names
are refused unless `-Force` or `--force` is supplied; every preflight refusal leaves the
project unchanged.

### The anchor block and rigor-goals install by default

A plain `./install.sh .claude/skills` (or the process-scoped PowerShell form above)
installs all three tiers: the 20 skills, the `rigor-goals` tool, and the anchor block.
Defaults are inferred from the target:

| Target pattern | Default goals location | Default anchor location |
|---|---|---|
| `$HOME/.codex/skills` | `$HOME/.codex/tools` | `$HOME/.codex/AGENTS.md` |
| `.claude/skills` | `.claude/tools` | `CLAUDE.md` in the containing project |
| `.agents/skills` (Antigravity project) | `.agents/tools` | `AGENTS.md` in the containing project |
| `$HOME/.gemini/config/skills` (Antigravity user) | `$HOME/.gemini/config/tools` | `$HOME/.gemini/config/AGENTS.md`, beside the skills directory |
| `.gemini/skills` (Gemini CLI) | `.gemini/tools` | `GEMINI.md` in the containing project |

`--anchor FILE` / `-Anchor` and `--goals DIR` / `-Goals` override the default locations.
The anchor install is idempotent: on upgrade the marker-fenced block is replaced in
place, hand edits outside the markers survive, and a diff is printed.

`--no-anchor` / `-NoAnchor` and `--no-goals` / `-NoGoals` are **owner-only opt-outs**.
They exist so the human who owns the machine can turn the discipline off; an agent
running the installer must never pass them on its own initiative.

For an upgrade or same-version repair, acquire the intended source version and rerun the
same command with `--force` or `-Force`. This replaces managed skill/tool bytes while
preserving text outside the anchor markers. Safe removal must delete only the 20
manifest-owned skill directories, the one managed tool file, and the single
marker-fenced anchor span; follow the preview-and-preserve procedure in the
[manual](docs/manual.md).

### rigor-goals in 30 seconds

```sh
python3 tools/rigor_goals.py create --brief "ship feature X" --mode finite_program \
  --goal "api::add the endpoint" --goal "docs::update the manual"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G001 --status complete --evidence "test_api.py: 4 passed"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G002 --status complete --evidence "manual updated" \
  --verify-cmd "pytest && python tools/validate_bundle.py" --verify-evidence "12 passed; BUNDLE_VALID"
python3 tools/rigor_goals.py status
```

Choose and record one engagement mode when the plan is created:

- `single_unit` — one bounded unit.
- `finite_program` — a declared finite queue; this is the backward-compatible default.
- `continuous_development` — ongoing ownership. It requires an explicit `--terminal`
  predicate, and finishing the currently known queue remains `ACTIVE - NOT COMPLETE`.
- `release_workflow` — a candidate or publication engagement. It requires both an
  explicit `--terminal` and `--release-intent candidate|publish`.

The recorded mode governs later turns and machines. Continuing language such as “take
over,” “keep going,” or “work through the backlog” resolves toward
`continuous_development`; only the owner may downgrade it. `add` requires an explicit
authorization source, `set-next` records a deliberate ordering change, and `close`
refuses unresolved work. Use `waiting_external` or `blocked_owner` for nonterminal waits;
use `cancelled` or `out_of_scope` only when those outcomes are actually authorized.

For a separate active continuous plan, a complete queue-extension and closure sequence is:

```sh
python3 tools/rigor_goals.py create --brief "take over development" \
  --mode continuous_development --terminal "owner pauses, cancels, or changes mode" \
  --goal "baseline::complete the first accepted unit"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G001 --status complete \
  --evidence "first unit green" --verify-cmd "pytest" --verify-evidence "35 passed"
python3 tools/rigor_goals.py add --goal "repair::fix verified regression" \
  --authorization-source "accepted finding F-12"
python3 tools/rigor_goals.py set-next --id G002 --reason "next accepted unit"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G002 --status complete \
  --evidence "repair green" --verify-cmd "pytest" --verify-evidence "35 passed"
python3 tools/rigor_goals.py set-mode --mode continuous_development \
  --terminal "owner pauses, cancels, or changes mode" \
  --authorization-source "owner instruction 2026-07-31"
python3 tools/rigor_goals.py close --evidence "terminal receipt" \
  --verify-cmd "command already run" --verify-evidence "observed result" \
  --authorization-source "owner instruction 2026-07-31"
```

`--authorization-source` is an attributable text receipt, not authentication of the
person it names. It is required for continuous/release closure, mode changes,
`cancelled`/`out_of_scope` resolutions, and their reopening. A custom terminal on a
single or finite plan also requires explicit `close`; only the default “all declared
goals complete” terminal auto-closes after its final verified checkpoint.

The final active story refuses to complete without `--verify-cmd` and
`--verify-evidence`. In continuous and release modes that is a unit checkpoint, not an
engagement exit: reconcile the accepted scope, add or select the next authorized unit,
and continue. State lives in `./.rigor/` (add it to `.gitignore` or commit it; your
choice). A fresh session resumes with `status`. Version 1 plans migrate once to schema 2
as `finite_program`, preserving their goals and recording `plan_migrated` in the ledger;
unknown schemas or modes are refused rather than guessed. Migration cannot infer the
intent of an old brief, so the owner should review the recorded finite mode and use the
loud, authorization-receipted `set-mode` command if it was actually ongoing work.

Be precise about what the gate is: `rigor-goals` **records** the verification command
and its result — it does not run the command or check the result is true. It is a
workflow-completeness gate (no story closes without named evidence), not independent
proof enforcement. `close` checks that required receipt fields exist; it cannot establish
that the terminal predicate is true. The honesty of the evidence is the agent's obligation
and the reviewer's to check. One active plan per working tree: concurrent tasks sharing a
checkout will fight over `./.rigor/` — use separate worktrees.

Each CLI process takes `.rigor/mutation.lock`, so overlapping commands refuse instead of
silently losing an update. If a process crashes, confirm no `rigor-goals` process is
active before removing a stale lock. `goals.json` replacement is atomic, but the state
file and append-only ledger are two files, not one transaction: a process or storage
failure between them can leave the latest state ahead of its ledger event. Preserve both
files and reconcile that discrepancy; do not describe the ledger as tamper-proof or
crash-atomic.

**Known limitation — the state is a file, not a fortress.** Any process that can delete
files in the workspace can destroy the plan, and nothing in-repo can detect a deletion
that also removes the ledger. Replacing a plan is loud (`create --force` prints what it
destroys, and every ledger event carries a `plan_id`), but if other agents or tools share
the same checkout, commit `./.rigor/` or back it up externally — the gate is only as
durable as the files it lives in.

## Main entrypoints

- `dev-rigor-stack-lite` — route Micro, Standard, or Critical and coordinate applicable gates
- `dev-rigor-stack-lite-brainstorm` — optional discovery for materially unresolved designs
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
