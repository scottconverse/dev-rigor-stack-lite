---
name: dev-rigor-stack-lite-brainstorm
description: >
  Turn an unresolved product or engineering idea into an approved design brief before
  planning implementation. Use when the user explicitly asks to brainstorm, or when
  purpose, success criteria, material constraints, or consequential product choices are
  genuinely unresolved. Also use for "$dev-rigor-stack-lite-brainstorm" and
  "/dev-rigor-stack-lite-brainstorm". Without explicit invocation, skip a
  decision-complete brief.
---

# Dev Rigor Stack — BRAINSTORM

BRAINSTORM is **Optional discovery**, not a mandatory gate for every Standard or Critical
unit. Its job is to resolve consequential ambiguity before PLAN traces implementation.
It produces a text-first design brief and takes no implementation action.

## Activate or skip

Activate when the user explicitly invokes BRAINSTORM, even if the supplied brief appears
complete; the owner may want to reopen or critique settled choices. Otherwise, activate
automatically when one or more of these are materially unresolved:

- the problem, target user, or desired outcome;
- measurable success criteria or meaningful non-goals;
- constraints that could change the design;
- a consequential product, workflow, data, security, or compatibility choice.

Do not activate automatically merely because work is creative, Standard, Critical, large,
or described informally. When the owner has not invoked BRAINSTORM, a decision-complete
brief routes directly to `$dev-rigor-stack-lite-plan`. Micro work does not require an
approval gate, though the owner may explicitly invoke BRAINSTORM for it.

## Discovery method

Read available project context before asking. Never ask the user to repeat a fact already
present in the request, repository, durable project state, or supplied brief.

Use guided discovery by default:

1. Resolve one material decision at a time. Prefer a closed question when the real choice
   is known, put the recommended answer first, and explain its tradeoff briefly.
2. Offer two or three approaches only when they are genuinely viable. Put the recommended
   approach first. If only one approach is viable, recommend it directly and explain why
   the apparent alternatives fail instead of manufacturing choices.
3. Present the proposed design in small, coherent sections. Combine trivial dependent
   details rather than forcing artificial approvals for each paragraph.
4. After the material design is visible, request one consolidated decision:
   **Approve / Revise / Pause**.

For an expert user or latency-sensitive exchange, offer a fast or batch pass. Even then,
keep decisions explicit and do not bury the recommendation.

Any lane named during discovery is a **provisional lane**. PLAN remains authoritative
after tracing the actual implementation and named risks.

## Approval and change control

Approval is required only when BRAINSTORM was warranted and produced a material design.
Do not hand unresolved or unapproved material design choices to implementation. If the
owner revises a material assumption, constraint, or outcome after approval, invalidate
the affected portion, return to BRAINSTORM, and seek approval for the changed design.
Never label a proposed revision approved or owner-approved before the owner gives that approval.

Approval means the design may proceed to planning. It does not authorize implementation,
merging, publishing, or bypassing any selected gate.

## PLAN handoff

The approved handoff must record:

- problem and target user;
- goals and non-goals;
- constraints and success criteria;
- chosen approach and why;
- rejected alternatives and reasons;
- assumptions and open questions;
- approval state and the owner-approved revision, if any.

End by routing only to `$dev-rigor-stack-lite-plan`. PLAN consumes this record, validates
it against the repository, selects the authoritative lane, and defines acceptance and
tests. Do not edit files, dispatch implementation, or claim the feature is ready from
BRAINSTORM.

## Invalid outcomes

The result is invalid if it asks already-answered questions, invents false alternatives,
treats a provisional lane as final, routes implementation directly, or hands PLAN an
unapproved material design.

The scenarios in `references/behavior-scenarios.md` are an evaluation rubric. They make
the intended model behavior reviewable; packaging checks do not prove a model follows it.
