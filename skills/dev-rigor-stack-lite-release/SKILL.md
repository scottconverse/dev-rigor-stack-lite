---
name: dev-rigor-stack-lite-release
description: Run the dev-rigor-stack-lite release protocol independently from exact candidate evidence through applicable gates, zero-release-blocker closure, owner go/no-go, publication, and applicable live verification. Use for "$dev-rigor-stack-lite-release", "/dev-rigor-stack-lite-release", prepare or verify a release, publish a version, or close a deployment.
---

# Dev Rigor Stack — RELEASE gate

Bind every check to the exact candidate commit and artifacts. Before owner go/no-go:

1. Record the exact commit, version, artifact hashes/signatures, platform scope, and proof
   that each artifact came from that source state.
2. Verify version consistency, changelog, license, secrets, dependencies, and all checks
   claimed. Define rollback trigger/owner when deployment or hard-to-reverse work applies.
3. Select gates from the changed risk:
   - The `$dev-rigor-stack-lite-gauntletgate` full lane only for Critical or broad
     releases. Add walkthrough only when its trigger below applies; use `all` only
     when every lane applies.
   - `$dev-rigor-stack-lite-proof-gate` for Critical changes or material changed claims.
   - `$dev-rigor-stack-lite-docs-gate` for affected deliverables.
   - Candidate `$dev-rigor-stack-lite-visitor-audit` for changed public surfaces/assets.
   - `$dev-rigor-stack-lite-walkthrough` for changed UI, onboarding, acquisition, or
     installer journeys; use a verified clean machine for install lifecycle changes.
   - Randomized/mutation evidence only when its named risk trigger applies.
4. Inventory every finding and classify `blocking_findings`: Blocker/Critical block;
   Major blocks for acceptance violations or material release risk; Minor blocks only
   for acceptance violations; Nit never blocks. Keep nonblocking findings visible in the
   existing watchlist with an owner or explicit disposition.
5. PASS only when applicable coverage/evidence is valid, exact candidate identity holds,
   and `blocking_findings` is empty. Literal `0/0/0/0/0` applies only when owner-selected.
6. Freeze optional polish after PASS and stop for owner go/no-go unless already granted.

After authorized publication, the release remains OPEN:

1. Run cache-busted Visitor Audit when release pages/assets changed.
2. Run the published Walkthrough when acquisition, UI, onboarding, or installer behavior changed.
3. Run focused Proof/Docs/Gauntlet lanes only for changed post-release scope.
4. Announce and close only when applicable live evidence is VALID and
   `blocking_findings` is empty. Otherwise correct or invoke rollback.

Never rewrite or delete a published tag silently. Never use candidate, source, CI, or
developer-machine evidence as a substitute for the final public artifact.

Allow at most two broad reviews of one candidate. After that, review only changed or
previously failing scope unless the candidate materially changes. If the same final-style
execution fails twice for one cause, stop retrying and diagnose it.
