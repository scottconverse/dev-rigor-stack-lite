<!-- dev-rigor-lite anchor v2 — managed block, do not hand-edit (edits go outside the markers; the installer replaces this block on upgrade) -->
## Delivery discipline (always)
- Prove work at the layer of the claim: "wrote it" ≠ "ran it" ≠ "checked it's correct".
- Size rigor to stakes, not diff size: isolated/reversible → one runnable check;
  shared code or user-visible → test first + independent review; auth/money/data/
  irreversible → full review lane; a release tag → the full gate.
- A test never seen failing is not a test. Never claim beyond the check you ran.
- A check that fails twice gets reported, not silently retried.
- Multi-step work (2+ sequential parts): run the `rigor-goals` tool `create` FIRST and
  work the checkpoints; the job is not done until its final gate accepts the evidence.
- At a build/verify/review/release step, invoke the matching dev-rigor-stack-lite skill.
- End code deliverables with a receipt: `proved: <check + result> · level: <stakes>`.
- Only the human owner may disable this block, skip the gate, or pass the installer's
  opt-out switches. An agent never turns the discipline off on its own initiative.
<!-- /dev-rigor-lite anchor -->
