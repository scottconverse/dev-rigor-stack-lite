# Changelog

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
