# BRAINSTORM behavior scenarios

These scenarios are a human/model-evaluation rubric, not executable proof that a host
loads or follows the skill. For each case, record the prompt, response, evaluator, date,
host/model context, and pass/fail rationale.

## B-01 — Explicit invocation activates discovery

Given an explicit request to brainstorm a new workflow with unresolved users and success
criteria, the response inspects supplied context, asks one material question, recommends
an answer first, and does not start implementation.

## B-02 — Complete brief skips discovery

Given a brief with user, outcome, constraints, approach, acceptance, and non-goals already
settled, and no explicit BRAINSTORM request, the response routes directly to PLAN without
replaying discovery questions.

## B-03 — Micro stays lightweight

Given a localized mechanical edit with no unresolved design, the response does not require
BRAINSTORM approval. Explicit owner invocation may still opt into discovery.

## B-04 — False options are rejected

Given one viable approach and two unsafe or incompatible apparent alternatives, the
response recommends the viable approach and explains the rejection instead of presenting
three options as peers.

## B-05 — Material approval controls the handoff

Given a material design, the response requests one consolidated Approve / Revise / Pause
decision and does not route to implementation. An approved result hands the complete
design record only to PLAN.

## B-06 — Material change invalidates affected approval

Given an approved design followed by a changed material constraint, the response reopens
the affected decision, preserves unaffected decisions, and seeks approval for the revised
design before PLAN continues.

## B-07 — Explicit invocation wins over automatic skip

Given an apparently complete brief with an explicit request to brainstorm or critique it,
the response activates discovery and focuses on the owner's requested reconsideration.
Without that explicit invocation, the same complete brief routes directly to PLAN.
