# GauntletGate report — sample-app — Stage 1 → Stage 2

**Date:** 2026-06-17 · **Build/commit:** `eval-fixture` · **Run by:** GauntletGate (walkthrough)
**Lanes run:** walkthrough · **Lanes NOT run:** lite, full
**How run / environment:** local — `python eval/sample-app/app.py 8799`, dependency genuinely absent (see attestation)

> This is a real example, produced from this repo's own golden eval fixture
> (`eval/`). It shows what a first-run dead-end looks like through the gate.

---

## Verdict (read first)

> **⛔ DO NOT ADVANCE**
> ⚠️ Also a PARTIAL CHECK — only `walkthrough` ran; this is not a full advancement gate. But a Blocker was found, so the product does not advance regardless.

- **First-run:** dead-ends a new user ❌ — (first-run coverage: **VALID**)
- **Severity roll-up (lanes run):** Blocker 1 · Critical 0 · Major 0 · Minor 0 · Nit 0
- **One-line why:** a brand-new user with no backend configured cannot reach the core feature — the primary action is disabled and the setup step says "install it yourself" with no in-product path.

---

## Environment provisioning — verified (attestation)

| What | State used | How VERIFIED — not assumed |
|---|---|---|
| Profile / app-data isolation | n/a (stateless sample) | served fresh per request; no persisted state |
| First-run flags | unset | no prior-run markers exist |
| External dependency: backend (`GAUNTLET_SAMPLE_BACKEND`) | **ABSENT** | env var scrubbed before launch; confirmed unset in the launched process env |
| Data store | empty | n/a |
| Network | online (loopback) | fetched `http://127.0.0.1:8799/` |

**Isolation verified?** YES · **First-run coverage:** VALID
**Evidence artifacts (required):** `eval/artifacts/first-run-absent.html` (the served dead-end), `eval/artifacts/returning-present.html` (dependency-present control), `eval/artifacts/verdict.json`

---

## Lane results

### Walkthrough
**First-run verdict:** dead-ends a new user ❌. Provisioning-matrix cells walked:
first-run × dependency-ABSENT × empty × online (the new-user reality) and
returning × dependency-present × empty × online (control). The ABSENT cell is the
mandatory one and it is where the dead-end lives.

Readiness by area:

| Area | Finished | Partially wired | Cosmetic | Broken |
|---|---|---|---|---|
| Core "Create" action (dependency absent) | | | | ❌ |
| Core "Create" action (dependency present) | ✅ | | | |

---

### F-001 — Blocker — New user cannot reach the core feature with the backend absent
- **Route / screen:** `GET /` (first run, `GAUNTLET_SAMPLE_BACKEND` unset)
- **Element / workflow:** the "Create your first thing" primary action
- **Expected:** a new user can get to first value, or is guided to a working state
- **Actual:** the button renders **disabled**; status reads "No backend found. Install it yourself and restart — see the docs." No in-product path resolves it.
- **Evidence:** `eval/artifacts/first-run-absent.html` — `<button id='core-action' disabled>` and `<p ... data-deadend='true'>`
- **Likely cause:** the core action is gated on a dependency the onboarding flow neither installs nor configures.
- **Suggested fix:** give the setup step an in-product path (bundled/managed backend, or a guided installer), or degrade the core feature gracefully instead of disabling it.
- **Suggested test:** the repo's golden eval (`eval/run_eval.py`) already asserts this dead-end; keep it green by fixing the onboarding, not the test.

---

## Blocking punch list (must clear to advance)

| ID | Title | Severity | Lane | What to do | Size |
|----|-------|----------|------|------------|------|
| F-001 | New user dead-ended on core feature (backend absent) | Blocker | walkthrough | add an in-product setup path or graceful degradation | M |

## Next-stage watchlist
(none this run)

## What's working (credited, specific)
- With the dependency present, the core action is enabled and the path is clean
  (`returning-present.html`) — the dead-end is specifically a *first-run/dependency-absent*
  failure, not a broken feature.

---

## Sign-off checklist
- [x] Verdict matches the lanes actually run (PARTIAL CHECK noted; Blocker → DO NOT ADVANCE).
- [x] Environment attestation filled with verified facts and linked to on-disk artifacts.
- [x] First-run reachability stated; the dead-end on the core feature is filed as a Blocker.
- [ ] full/all ran — N/A this run (walkthrough only).
- [x] The Blocker has evidence, impact scope (the whole new-user funnel), and a fix path.
- [x] What's-working is present.
