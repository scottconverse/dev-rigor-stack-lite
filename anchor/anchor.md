<!-- dev-rigor-lite anchor v3 — managed block, do not hand-edit (edits go outside the markers; the installer replaces this block on upgrade) -->
## Delivery discipline (always)
- Prove work at the layer of the claim: "wrote it" ≠ "ran it" ≠ "checked it's correct".
- Route first: Micro for localized mechanical work; Standard for ordinary bugs/features; Critical only for a named risk trigger. The lane is also a ceiling on ceremony.
- Micro: inspect → change → one runnable check → receipt. Standard: brief acceptance, RED/GREEN where applicable, affected tests, focused review, receipt.
- Critical triggers: auth/secrets; money; persisted data/migrations/deletion; security/privacy; concurrency/order/idempotency; install/deploy/rollback; irreversible work; broad public contracts.
- File count, file type, `medium+`, and release status do not select a lane.
- A logic test never seen failing is not proven sensitive. Never claim beyond the check run.
- If the same final-style check fails twice for one cause, diagnose or report it; do not blind-retry.
- Use `rigor-goals` only for cross-session work, handoffs, parallel agents, or an external wait.
- At a selected build/verify/review/release step, invoke the matching dev-rigor-stack-lite skill.
- A release binds evidence to the exact candidate, runs only applicable gates, and passes only with no unresolved release blocker. Optional polish moves to the watchlist after candidate freeze.
- End code deliverables with a receipt: `proved: <check + result> · lane: <Micro|Standard|Critical>`.
- Only the human owner may disable this block, skip the gate, or pass the installer's opt-out switches. An agent never turns the discipline off on its own initiative.
<!-- /dev-rigor-lite anchor -->
