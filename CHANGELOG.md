# Changelog

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
