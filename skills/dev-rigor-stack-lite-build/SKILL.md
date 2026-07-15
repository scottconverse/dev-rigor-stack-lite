---
name: dev-rigor-stack-lite-build
description: >
  Run the dev-rigor-stack-lite BUILD gate using the complete coder-tdd-qa-lite contract:
  baseline evidence, real RED-GREEN-REFACTOR TDD, security and UI state checks,
  falsification, and verification reporting. Use for "$dev-rigor-stack-lite-build",
  "/dev-rigor-stack-lite-build", implementing a planned unit, or invoking the build
  section independently.
---

# Dev Rigor Stack — BUILD gate

Read `../coder-tdd-qa-lite/SKILL.md` completely and follow it without abbreviation. That
sibling is the canonical BUILD implementation and remains the backward-compatible
`$coder-tdd-qa-lite` entrypoint. This namespaced entrypoint must never substitute a summary,
weaker test-after workflow, or inspection-only pass.

When the coordinator supplied plan artifacts, consume its acceptance criteria, test list,
blast radius, public-surface impact, user-journey impact, and deterministic exit. When
invoked alone, create those missing inputs before modifying code. Return exact baseline,
RED, GREEN, widened-suite, falsification, security, documentation, and version-control
evidence for Proof Gate.
