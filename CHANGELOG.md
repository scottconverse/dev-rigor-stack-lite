# Changelog

## 0.3.2 - 2026-07-15

Repairs the 0.3.1 rename, from a Codex-side compatibility report (both findings
reproduced before fixing):

- **The standalone audit entrypoint works again**: `dev-rigor-stack-lite-audit-lite`
  still read the deleted `../audit-lite/SKILL.md`, and the coordinator still
  advertised `$audit-lite`. Both now point at `quick-audit-lite`.
- **Upgrades migrate safely**: installing over a pre-0.3.1 lite install left the
  stale `audit-lite` behind, still routable. The installers now remove it — but
  ONLY when it is identifiably lite's own old copy (its `audit-team-lite`
  escalation); the full dev-rigor-stack's richer `audit-lite` is never touched.
  Both branches CI-pinned.
- **Validator checks internal references resolve**: dangling `../name/SKILL.md`
  reads and `$name` entrypoint tokens naming no skill in the bundle now fail
  validation (this check was run red against the broken tree first).
- README precision (also from the report): `rigor-goals` records verification
  evidence, it does not run the command — a workflow-completeness gate, not
  proof enforcement; and one active plan per working tree.
- **Antigravity anchor path fixed** (Antigravity compatibility report):
  `.gemini/config` targets now get `AGENTS.md` beside the skills directory —
  Antigravity reads `AGENTS.md`, not `GEMINI.md` (verified from its own system
  prompt). Plain `.gemini` targets (Gemini CLI) still get `GEMINI.md`. Both
  CI-pinned.

## 0.3.1 - 2026-07-15

- Rename `audit-lite` to `quick-audit-lite`. It was the only skill whose name
  collided with the full dev-rigor-stack's skills: installing lite over a full
  install with `--force` would silently overwrite the richer full-stack
  `audit-lite`. No other entrypoint collides.

## 0.3.0 - 2026-07-15

**The anchor block and rigor-goals now install by default.** They are part of
the stack, not extras: a plain `install.sh TARGET` / `install.ps1 -Target`
installs skills + the rigor-goals tool (default `<TARGET>/../tools/`) + the
anchor block (default `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` in the current
directory, inferred from the target). `--no-goals`/`-NoGoals` and
`--no-anchor`/`-NoAnchor` are owner-only opt-outs; the anchor text itself now
states that only the human owner may disable the discipline.

Also fixes everything found by the independent fix-wave review and the gate
incident:

- **User-supplied non-ASCII text no longer crashes the tool** (critical,
  fix-wave review): the 0.2.1 ASCII change removed the stream guard entirely,
  so an emoji in `--brief`/`--goal`/`--evidence` hard-crashed with
  UnicodeEncodeError on cp1252 consoles — worse than the mojibake it replaced.
  Corrected design: the tool's own strings are pure ASCII; user text passes
  through and degrades to `?` instead of crashing. Test forces cp1252 via
  PYTHONIOENCODING.
- **Validator scans every shipped file** (fix-wave review): the 0.2.1 scan
  skipped scripts/extensionless files and nested `SKILL.md`s; now all files at
  all depths are checked, only the canonical top-level SKILL.md exempt.
- **Plan replacement is loud and traceable** (gate incident): during the
  release gate an agent sharing the checkout deleted `./.rigor/` and a later
  `create` silently planted a new plan. `create --force` now prints the plan
  it destroys (brief, plan id, progress, created); every plan gets a
  `plan_id` carried on every ledger event. README documents the physical
  limit: in-repo state cannot survive a deletion that also takes the ledger —
  shared-checkout users should commit `./.rigor/` or back it up.
- CHANGELOG/NOTICE wording corrected where 0.2.1 overstated the ASCII fix
  ("all output" — true only of the tool's own strings).

## 0.2.1 - 2026-07-15

Release-gate fixes. 0.2.0 was run through the stack's own gates (independent
multi-agent audit + visitor pass + journey walkthrough); 10 findings, all
independently reproduced, all fixed here:

- **rigor-goals no longer claims false completion** (critical): a plan whose
  stories ended failed/blocked printed "all stories complete"; the wrap-up line
  is now honest ("N/M complete, X failed, Y blocked ... NOT complete") in both
  `next` and `checkpoint`. Tests assert the message, not just the exit code.
- **install.ps1 resolves relative paths correctly** (critical): `-Target`,
  `-Goals`, `-Anchor` resolved against the process start directory instead of
  the shell's `$PWD`, silently installing into the wrong folder for the
  documented usage. Now resolved via the PowerShell provider path API; CI
  covers the cd-then-relative-path pattern.
- **Validator's hook-free check now covers every shipped file** (critical): a
  `hooks.json` dropped anywhere in a skill directory installed wholesale and
  still validated. Hook/config files anywhere under `skills/` now fail the
  bundle, and forbidden hook terms are checked in all text files, not just
  SKILL.md.
- **Anchor idempotency survives CRLF checkouts** (major): with Git for
  Windows' `core.autocrlf=true`, the first `--anchor` refresh always reported
  a spurious change. Line endings are pinned via `.gitattributes` and both
  install paths normalize CRs; CI exercises a CRLF anchor source.
- **All rigor-goals output is plain ASCII** (major): the 0.2.0 "encoding
  guard" only suppressed crashes; on cp1252 consoles most output rendered as
  mojibake. Glyphs replaced with ASCII; a test enforces ASCII-only output.
- **Empty `description: >` frontmatter no longer validates** (minor).
- `.rigor/` gitignored for in-repo dogfooding; NOTICE wording corrected.

## 0.2.0 - 2026-07-15

- Add `rigor-goals` (`tools/rigor_goals.py`): stdlib-only multi-story loop whose final
  story cannot complete without `--verify-cmd` and `--verify-evidence`. State in
  `./.rigor/` survives session death and context compaction. Adapted from fablize's
  goal engine (fivetaku/fablize, MIT) — see NOTICE.md. 10-case test suite.
- Add `anchor/anchor.md`: a marker-fenced ≤15-line discipline block for the host's
  persistent instructions file (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`).
- Installers gain `--goals DIR` / `-Goals` and `--anchor FILE` / `-Anchor`; the anchor
  install is idempotent and replaces the managed block in place on upgrade, preserving
  hand edits outside the markers. Guard against a missing end marker.
- `validate_bundle.py` now also checks the anchor (markers, 15-line cap, rigor-goals
  reference) and smoke-tests the rigor-goals exit gate (must refuse without verify flags).
- CI runs the rigor-goals suite and exercises the new installer flags on both OSes,
  including idempotent re-run.

## 0.1.0 - 2026-07-14

- Fork all 19 skill entrypoints from codex-dev-rigor-stack 1.7.0.
- Remove lifecycle hooks, hook installers, runtime state, trust activation, and Stop gates.
- Rename the product and canonical entrypoints under `dev-rigor-stack-lite`.
- Add portable Codex, Claude Code, and Antigravity installation targets.
- Make merge, publication, delegation, and approvals subject to user and host policy.
