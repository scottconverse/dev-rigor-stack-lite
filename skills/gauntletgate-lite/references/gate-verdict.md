# GauntletGate — the gate verdict

GauntletGate is a **stage-gate**: a product runs the gauntlet to earn the right to
advance to the next stage / sprint / release. The verdict is the whole point. It
must be honest about *what was actually run* — a cheap partial check can never
masquerade as the full gate.

---

## The two verdict types

### CLEAR TO ADVANCE

Emit **CLEAR TO ADVANCE** only when **all** of the following hold:

- The **full** lane ran (`lite` is a feeder, not part of the advancement bar).
- Walkthrough ran when the changed scope includes UI, onboarding, acquisition,
  installer, or another first-run surface. It may be marked N/A only with a concrete
  reason that none of those surfaces changed.
- `blocking_findings` is empty under the default policy: Blocker/Critical block;
  Major blocks when it violates acceptance criteria or creates material release risk;
  Minor blocks only when it violates acceptance criteria; Nit never blocks.
- When Walkthrough applies, **first-run coverage is VALID** (the environment
  attestation is filled with verified facts) **and a brand-new user can reach the
  core feature.**

Every confirmed finding remains in the severity roll-up and findings report. Unresolved
nonblocking findings go to the existing watchlist with an owner or explicit disposition.
Literal `0/0/0/0/0` is an optional owner-selected stricter policy, not the default.

### PARTIAL CHECK  (any run missing a required lane)

Any run that omits the full lane, or omits an applicable Walkthrough — e.g. `lite`,
`walkthrough`, or `lite walkthrough` — emits a **PARTIAL CHECK** verdict, never CLEAR
TO ADVANCE. A `full` run is also partial unless Walkthrough ran or was explicitly
classified N/A from the changed scope. The report must say, in the first line:

> ⚠️ PARTIAL CHECK — lanes run: `<list>`. This is **not** an advancement gate.
> Run the missing applicable lane(s) for a clear-to-advance decision.

A PARTIAL CHECK still reports its findings and its own pass/fail *within the lanes
it ran* — it just cannot greenlight advancement.

### DO NOT ADVANCE

Any run with an unresolved blocking finding, or whose first-run coverage is **INVALID**
while a UI/onboarding/dependency surface is in scope, emits **DO NOT ADVANCE** with the
blocking punch list that must be cleared before a re-run.

---

## What every verdict carries

1. **The verdict line** — CLEAR TO ADVANCE / PARTIAL CHECK / DO NOT ADVANCE — plus
   the lanes that ran and the lanes that did not.
2. **First-run line** — reaches core feature ✅ / dead-ends a new user ❌ / NOT
   VERIFIED (with first-run coverage VALID/INVALID).
3. **Severity roll-up** — Blocker / Critical / Major / Minor / Nit across all lanes
   that ran.
4. **The environment-provisioning attestation** (from the shared backbone), **with
   its linked on-disk evidence artifacts** — or an explicit statement that it could
   not be produced and why. An attestation with no linked artifact is UNVERIFIED →
   first-run coverage INVALID → the run cannot be CLEAR TO ADVANCE.
5. **The blocking punch list** (what must clear to advance) and the **watchlist**
   (what to fix next).

---

## Honesty rules (do not violate)

- A `lite`-only or any partial run is **never** CLEAR TO ADVANCE. Label it PARTIAL.
- Never classify Walkthrough N/A when changed UI, onboarding, acquisition, installer,
  or first-run behavior is in scope.
- Under the default policy, classify `blocking_findings` by acceptance and material
  release risk. Keep every nonblocking finding visible in the roll-up/watchlist.
  Classify false positives out with evidence; do not hide or downgrade real findings.
- Never report CLEAR TO ADVANCE off an environment whose first-run state was not
  verified, when the product has a first-run surface. INVALID first-run coverage
  caps the verdict.
- If a lane could not run (app won't start, dependency couldn't be removed, no
  multi-agent budget for `full`), say so plainly and mark that coverage as a gap —
  a gap is not a pass.
- The gate is **adversarial by default**: its job is to *block* advancement, not to
  find reasons to wave it through. Credit what works (honest signal), but the bar is
  the bar.
