---
name: dev-rigor-stack-lite-build
description: >
  Run the dev-rigor-stack-lite BUILD stage using the complete coder-tdd-qa-lite contract,
  scaled to Micro, Standard, or Critical. Use for "$dev-rigor-stack-lite-build",
  "/dev-rigor-stack-lite-build", implementing a planned unit, or invoking the build
  section independently.
---

# Dev Rigor Stack — BUILD gate

Read `../coder-tdd-qa-lite/SKILL.md` completely and follow it without abbreviation. That
sibling is the canonical BUILD implementation and remains the backward-compatible
`$coder-tdd-qa-lite` entrypoint. Its lane router governs: Micro uses inspect, change, one
relevant check, and a receipt; Standard uses applicable RED/GREEN, affected verification,
and focused falsification; Critical adds the complete evidence and independent proof path.
Do not turn Micro into a formal artifact run or weaken Standard/Critical test sensitivity.

When the coordinator supplied plan artifacts, consume its acceptance criteria, test list,
lane, named triggers, public-surface impact, user-journey impact, and deterministic exit.
When invoked alone, create only the inputs required by the selected lane. Return Micro's
receipt, Standard's applicable baseline/RED/GREEN/affected-suite/falsification evidence, or
Critical's complete evidence for Proof Gate.
