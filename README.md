# dev-rigor-stack-lite

A portable, evidence-first development and release workflow for AI coding agents. It
contains the complete 19-skill workflow from `codex-dev-rigor-stack`, adapted to run
without lifecycle hooks, a background runtime, trust activation, Stop interception, or a
private evidence ledger — plus two optional drift-resistance layers: a small **anchor
block** for the host's persistent instructions file, and **rigor-goals**, a stdlib-only
CLI whose exit gate refuses to close a multi-story job without verification evidence.

## The three tiers

Model attention decays over a long session and dies at context compaction; hooks fight
that with per-turn injection but are host-specific. Lite v2 instead moves the
discipline's memory into places that do not decay:

| Tier | What | Force | Why it resists drift |
|---|---|---|---|
| 1 | The 19 skills | none — invoked knowledge | — |
| 2 | Anchor block in `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` | reminder every turn | the host re-reads its instructions file each turn |
| 3 | `rigor-goals` CLI | one hard gate at "done" | state lives in `./.rigor/` on disk — survives compaction and session death; the gate is a program, not a prompt |

The anchor's one enforced habit — "multi-step work: run `rigor-goals create` FIRST" — is
what feeds Tier 3. One reminder feeding one gate, instead of continuous forcing.

## What changes in Lite

- Skills, references, templates, and deterministic helper scripts remain.
- Evidence comes from ordinary commands, logs, CI, screenshots, traces, hashes, and reports.
- Host policies control delegation, approvals, merges, publishing, and available tools.
- Passing a gate establishes readiness; it never grants the agent authority to merge or publish.
- Missing capabilities are reported as blocked or unverifiable rather than silently passed.

## Compatibility

The bundle uses the portable Agent Skills layout: one directory per skill with a
`SKILL.md` containing `name` and `description` YAML frontmatter. It is designed for:

- OpenAI Codex: `~/.codex/skills`
- Claude Code: project `.claude/skills` or user `~/.claude/skills`
- Google Antigravity: project `.agents/skills` or user `~/.gemini/config/skills`
- Other Agent Skills-compatible hosts

The Markdown workflows are portable; tool availability and instruction adherence vary by
host and model. This repository does not claim mechanical enforcement.

## Install

PowerShell:

```powershell
.\install.ps1 -Target "$HOME\.codex\skills"
.\install.ps1 -Target ".claude\skills"
.\install.ps1 -Target ".agents\skills"
```

Bash:

```sh
./install.sh "$HOME/.codex/skills"
./install.sh .claude/skills
./install.sh .agents/skills
```

Installation copies only the 19 directories under `skills/`. Existing directories with
the same names are refused unless `-Force` or `--force` is supplied.

### Optional: anchor block and rigor-goals

```sh
./install.sh .claude/skills --goals tools --anchor CLAUDE.md
```

```powershell
.\install.ps1 -Target ".claude\skills" -Goals tools -Anchor CLAUDE.md
```

`--anchor FILE` adds a marker-fenced block of the core discipline to the named
instructions file — or, on upgrade, replaces the existing block in place (hand edits
outside the markers survive; a diff is printed). `--goals DIR` copies the `rigor-goals`
tool there.

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

## Main entrypoints

- `dev-rigor-stack-lite` — coordinate PLAN → BUILD → VERIFY → REVIEW → MERGE
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

Six compatibility entrypoints are also included: `coder-tdd-qa-lite`, `proof-gate-lite`,
`audit-lite`, `audit-team-lite`, `gauntletgate-lite`, and `visitor-audit-lite`.

## Validate

```sh
python tools/validate_bundle.py
```

## Provenance

This is a hook-free adaptation of
[`scottconverse/codex-dev-rigor-stack`](https://github.com/scottconverse/codex-dev-rigor-stack),
originally released under the MIT License. See [NOTICE.md](NOTICE.md).

## License

MIT
