# GauntletGate report — <project> — <stage/sprint/release>

**Date:** <YYYY-MM-DD> · **Build/commit:** <sha> · **Run by:** <agent>
**Lanes run:** <lite | walkthrough | full | combination> · **Lanes NOT run:** <list>
**How run / environment:** <local dev server, command; first-run-clean vs provisioned — see attestation>

---

## Verdict (read first)

> **<CLEAR TO ADVANCE | PARTIAL CHECK | DO NOT ADVANCE>**
> <If PARTIAL CHECK: "lanes run: X — this is NOT an advancement gate; run `gauntletgate-lite all` for a clear-to-advance decision.">

- **First-run:** reaches core feature ✅ / dead-ends a new user ❌ / NOT VERIFIED /
  N/A — (first-run coverage: VALID / INVALID / N/A with reason)
- **Severity roll-up (lanes run):** Blocker N · Critical N · Major N · Minor N · Nit N
- **Coverage ledger:** screens N/N · controls N/N · paths N/N · visual states N/N · public surfaces N/N · links N/N — VALID / INVALID
- **One-line why:** <the single most important thing the reader must know>

---

## Environment provisioning — verified (attestation)

> Gates the first-run verdict. If not fillable with *verified* facts, first-run coverage is INVALID and the verdict says so. (See `references/shared-backbone.md` §2.)

| What | State used | How VERIFIED — not assumed |
|---|---|---|
| Profile / HOME / app-data isolation | <…> | <confirmed app wrote config+first-run marker to the isolated path …> |
| First-run flags | <unset / cleared> | <…> |
| External dependency: <name> | <ABSENT / present vX> | <how probed> |
| Data store | <empty / populated> | <…> |
| Network | <online / offline> | <…> |

**Isolation verified?** <YES / NO> · **First-run coverage:** <VALID / INVALID>
**Evidence artifacts (required):** <list the on-disk files backing the "verified" cells — e.g. `artifacts/first-run-absent.html`, `artifacts/isolation-path.txt`, a Playwright trace. No artifact → UNVERIFIED → first-run coverage INVALID.>

---

## Lane results

Include only the lanes that ran.

### Lite (if run)
TL;DR verdict; severity; key findings; escalation recommendation.

### Walkthrough (if run)
First-run verdict; zero-state / provisioning-matrix results (which cells walked);
acquisition/installer lifecycle; complete screen/control/path/state coverage ledger;
visual/accessibility results; readiness-by-area table; numbered findings (route ·
expected · actual · evidence · cause · fix · test).

### Visitor Audit (when public surfaces are in scope)
Candidate/live label; public-surface/link/control/visual coverage ledger; release asset,
checksum, version, and claim results; acquisition handoff to Walkthrough.

### Full (if run)
Per-role severity roll-up and top findings: Engineering · UI/UX · Technical Writer ·
Test · QA. Cross-role (multi-lane) findings called out. Pointers to the five
deep-dive files.

---

## Blocking punch list (must clear to advance)

Every Blocker/Critical; each Major that violates acceptance or creates material release
risk; each Minor that violates acceptance. Each: ID, title, severity, lane/role,
one-line "what to do," size (S/M/L). **The product does not advance until
`blocking_findings` is empty.**

## Next-stage watchlist

Every unresolved nonblocking finding, including structural Majors, architectural/design
debt, scaling/perf not-yet-acute, and Minor/Nit observations. Give each an owner or
explicit disposition.

## What's working (credited, specific)

Honest signal — not filler.

---

## Sign-off checklist

- [ ] The verdict matches the lanes actually run (Full ran; Walkthrough ran when
      applicable or is N/A with a changed-scope reason; no partial run is labeled
      CLEAR TO ADVANCE).
- [ ] Environment attestation filled with verified facts **and linked to on-disk
      evidence artifacts**, or first-run is N/A because no applicable surface changed
      (no artifact for an applicable surface = unverified = INVALID).
- [ ] First-run reachability for a brand-new user is stated; a dead-end on the core feature is a Blocker.
- [ ] Full/release Walkthrough used a verified clean machine where applicable and accounted for every inventoried screen, control, distinct path, visual state, and lifecycle operation.
- [ ] Public release scope includes Visitor Audit and its exact acquisition handoff was consumed by Walkthrough.
- [ ] `blocking_findings` is empty; every nonblocking finding remains in the roll-up/watchlist.
- [ ] If `full`/`all` ran: all 5 in-scope roles ran (or the gap is documented); deep-dives exist; cross-role findings noted.
- [ ] Every Blocker/Critical has evidence, blast radius, and a fix path.
- [ ] What's-working is present (the report isn't all-red).
