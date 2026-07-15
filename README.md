# dev-rigor-stack-lite

A portable, skills-only evidence-first development and release workflow for AI coding
agents. It contains the complete 19-skill workflow from `codex-dev-rigor-stack`, adapted
to run without lifecycle hooks, a background runtime, trust activation, Stop interception,
or a private evidence ledger.

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
