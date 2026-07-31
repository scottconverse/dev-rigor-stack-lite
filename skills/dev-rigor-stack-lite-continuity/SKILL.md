---
name: dev-rigor-stack-lite-continuity
description: Restore, reconcile, and persist durable dev-rigor-stack-lite project state across sessions, agents, and machines. Use for "$dev-rigor-stack-lite-continuity", "/dev-rigor-stack-lite-continuity", project handoff, resume work, record locked decisions, or close a rigor-stack session safely.
---

# Dev Rigor Stack — continuity

Use one existing remote-tracked, append-safe project record; never create a competing
memory store when the project already has one. Preserve locked decisions, acceptance
criteria, killed approaches with reasons, current gate evidence, unresolved findings,
release state, and exact artifact/build identities.

Continuity is an engagement checkpoint, not an engagement exit. Read and preserve the
pinned engagement mode, terminal predicate, authorized commitments, current unit/gate,
active workers/PRs/checks, external waits, and next deterministic action. For
`finite_program` and `continuous_development`, checkpoint after the unit-level MERGE
result, reconcile live state, and select the next authorized unit. Continuing language
without a bounded end remains `continuous_development` until the owner pins another
mode. A green merge, worker-local DONE, session end, or context change never closes the
engagement.

At start, pull/read the record and revalidate facts that can become stale. Reconcile
concurrent entries without overwriting either history. During work, append decisions and
dead ends when they become durable. At end, append the handoff, push or otherwise persist
it, confirm the remote moved, and record that confirmation. An unconfirmed write is not a
successful handoff. Never store secrets, credentials, or sensitive evidence in a public
record.

Return: pinned engagement mode; state source and revision read; stale facts revalidated;
decisions, conflicts, and entries reconciled; next unit or valid stop; remote revision
confirmed; and remaining work.
