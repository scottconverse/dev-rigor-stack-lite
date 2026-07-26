---
name: dev-rigor-stack-lite-docs-gate
description: Run the dev-rigor-stack-lite gate for affected deliverable documentation independently. Use for "$dev-rigor-stack-lite-docs-gate", "/dev-rigor-stack-lite-docs-gate", changed release documentation, README/manual/architecture/landing-page readiness, or proof that changed user-facing claims match the product.
---

# Dev Rigor Stack — documentation gate

Verify that every user-facing behavior, setup step, configuration option, supported
platform, public interface, installer path, limitation, and release claim is documented
accurately at the affected surface. Inventory changed behavior/claims and the deliverables
that own them. Require a plain-language README, two-voice manual, architecture diagrams,
or public landing page only when project scope, an existing contract, or acceptance
criteria warrants that deliverable. Do not create unrelated documentation to pass a release.

Consume Proof Gate claim refutation, Walkthrough newcomer observations, and Visitor Audit
public-surface evidence. Read rendered deliverables, not source alone; follow their links
and compare current-state claims against the exact release artifact. Historical documents
may describe the past. Process reports remain ephemeral except while a live decision rests
on them.

Return missing deliverables, false/stale/ambiguous claims, newcomer documentation gaps,
rendering defects, link evidence, severity counts, and `blocking_findings` under the
default zero-release-blocker policy.
