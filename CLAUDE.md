# CLAUDE.md

dev-rigor-stack-lite is a portable, hook-free adaptation of `codex-dev-rigor-stack` (v0.4.2, MIT): the same 19-skill evidence-first workflow with no lifecycle hooks, background runtime, trust activation, Stop interception or private evidence ledger, so it runs on any Agent Skills-compatible host. Two drift-resistance tiers replace the hooks and install by default: a marker-fenced anchor block in the host's instructions file, and the stdlib-only `tools/rigor_goals.py` CLI with state in `./.rigor/`. Treat both as part of the stack, not optional extras. The reasoning: model attention decays over a long session and dies at compaction, so the discipline's memory lives in places that do not decay.

Read `.claude/reference/commands.md` before running tests, installing, exercising the goals CLI, or reasoning about which instructions file an install writes (it holds the three-tier description and the install-target inference table). Never install over this repo's own `CLAUDE.md` while testing.

## Gotchas
- CI runs on ubuntu, windows and macos plus a separate `posix-installer-lifecycle` job. The contracts it protects:
  - `manifest.json` must declare `hooks: false`, `skill_count` must match the inventory, and all 19 directories must exist with a `SKILL.md` carrying `name` and `description` YAML frontmatter.
  - The goals gate must actually refuse: a final story completion without `--verify-cmd` and `--verify-evidence` is rejected, and with them it is accepted. Breaking either direction fails the bundle.
  - A bare `install.sh .claude/skills` must produce all three tiers: 19 skill dirs, `.claude/tools/rigor_goals.py`, and an anchor block in `CLAUDE.md`.
  - Anchor idempotency: re-running with `--force` leaves exactly one managed block, and hand edits outside the markers survive (CI includes a CRLF-checkout case).
  - Anchor target inference is case-insensitive: installing to `.CLAUDE/skills` must produce `CLAUDE.md`, not `AGENTS.md`.
  - Documented removal procedures must refuse source aliases, symlinks and links rather than following them.
  - Relative paths resolve against `$PWD`, not the installer's location.
- Owner-only controls: `--no-anchor` / `-NoAnchor` and `--no-goals` / `-NoGoals` exist so the human owner can turn the discipline off. An agent must never pass them on its own initiative and must never delete the anchor block on its own initiative. The anchor text carries this rule; preserve it.
- Claims discipline. Do not overstate what the repo enforces:
  - `rigor-goals` records the verification command and its result; it does not run the command or check the result is true. It is a workflow-completeness gate, not independent proof enforcement.
  - The state is a file, not a fortress: any process that can delete workspace files can destroy the plan. `create --force` prints what it destroys and every ledger event carries a `plan_id`, but that is detection, not protection.
  - One active plan per working tree; concurrent tasks sharing a checkout fight over `./.rigor/`. Use separate worktrees.
  - Tool availability and instruction adherence vary by host and model. The repo does not claim mechanical enforcement.
  - Passing a gate establishes readiness; it never grants authority to merge or publish. Missing capabilities are reported as blocked or unverifiable, never silently passed.
- `quick-audit-lite` was named `audit-lite` before 0.3.1. It was renamed because it collided with, and could silently overwrite, a full `dev-rigor-stack` install sharing the same skills directory. Do not rename it back.
- Installation copies only the 19 directories under `skills/`; existing same-named directories are refused without `-Force` or `--force`.
- Lane selection is by risk only. File count, file type, labels like `medium+` and release status do not select a lane.
