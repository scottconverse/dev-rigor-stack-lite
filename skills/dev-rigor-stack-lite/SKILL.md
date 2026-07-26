---
name: dev-rigor-stack-lite
description: >
  Proportional delivery discipline for coding work and releases. Apply
  whenever writing, changing, reviewing, verifying, merging, or releasing code, or
  when the user says "dev rigor stack", "apply the rigor stack", "the gates", "run
  this through the stack", "release gate", or asks for systematic/thorough delivery.
  Routes work through Micro, Standard, or Critical by named risk; applies only the
  matching PLAN, BUILD, VERIFY, REVIEW, MERGE, and release evidence; keeps durable
  state when continuity risk exists; and holds an evidence-over-claims honesty line.
  Not for non-code work.
license: MIT
---

# Standing dev rigor stack Lite v0.4.1

Route every unit before choosing its process. Micro work takes the short path below.
Standard work uses the proportionate per-unit loop. Critical work uses the complete
independent proof path. A release adds exact-candidate and owner-authority controls,
then runs only the gates applicable to what changed. A red result returns to the phase
that owns it; never route around a selected gate or merge/tag past it.

## Route by named risk

- **Micro:** localized copy, documentation, formatting, or mechanical work with no
  named Critical trigger. Flow: inspect → change → one relevant runnable check → receipt.
- **Standard:** the default for ordinary bugs, features, refactors, and shared-code
  changes. Use brief acceptance criteria, witnessed RED/GREEN for bugs or changed logic
  when practical, affected-suite verification, focused review, and a receipt.
- **Critical:** use the full stack when work touches authentication, authorization,
  permissions, secrets, money, persisted data, migrations, deletion/recovery,
  security/privacy/trust boundaries, concurrency/order/idempotency/shared mutable state,
  install/update/uninstall/deployment/rollback mechanics, irreversible operations, or
  broad public compatibility/API contracts.

File count, file type, `medium+`, and release status do not select a lane. A config or
documentation change can be Critical. A multi-file mechanical change can remain Micro
when its effects stay local and one check covers them. The
selected lane is also a ceremony ceiling: escalate only after naming the trigger or
uncertainty that creates the added risk.

## Standalone entrypoints

Every functional section is independently invokable and also routed by this coordinator:

- `$dev-rigor-stack-lite-continuity`
- `$dev-rigor-stack-lite-plan`
- `$dev-rigor-stack-lite-build` (backward-compatible `$coder-tdd-qa-lite`)
- `$dev-rigor-stack-lite-proof-gate` (backward-compatible `$proof-gate-lite`)
- `$dev-rigor-stack-lite-audit-lite` (short name `$quick-audit-lite`)
- `$dev-rigor-stack-lite-audit-team` (backward-compatible `$audit-team-lite`)
- `$dev-rigor-stack-lite-walkthrough`
- `$dev-rigor-stack-lite-visitor-audit` (backward-compatible `$visitor-audit-lite`)
- `$dev-rigor-stack-lite-gauntletgate` (backward-compatible `$gauntletgate-lite`)
- `$dev-rigor-stack-lite-merge-gate`
- `$dev-rigor-stack-lite-docs-gate`
- `$dev-rigor-stack-lite-release`

Namespaced entrypoints load the complete canonical sibling contract; they are not compact
rewrites. Missing or unreadable required skills make the affected gate INVALID rather than
silently degrading to a weaker approximation.

Read `references/artifact-contracts.md` before a Critical/release run or any standalone
stage that emits its shapes. Micro needs only its receipt. Standard uses structured
artifacts only when a handoff, durable decision, or selected gate needs them. Never
change upstream evidence or lose artifact identity.

## Session & machine continuity

Standalone: `$dev-rigor-stack-lite-continuity`.

Continuity, not a gate — a bookend on each side of the loop, sitting above it. Nothing
passes or fails here; it ensures only that durable project state outlives a session or
machine switch. Use it only for real continuity risk: cross-session work, a handoff,
parallel agents, or an external wait. A short same-session unit needs no durable ledger.

Durable state — locked decisions, done-criteria, and killed approaches (each with the
reason it was rejected) — lives in a **remote-tracked, append-safe artifact**, never
only in context:

- **The artifact** — remote-tracked (survives session/machine changes) and append-safe,
  so interleaved clients, sessions, and machines don't clobber each other; that's
  why a comment-append store beats a lone in-repo file that merge-conflicts. Mechanism is
  the project's to pick, not the skill's — point at one that already exists (a
  project-memory vault such as the `claude-dev-loop` skill if present, a pinned decision
  Issue, or a grep-able in-repo file), never a second store beside one you already have.
- **Start** — pull and read state before entering the loop. Honor settled decisions as
  defaults, but re-validate any resting on a fact that can go stale before relying on it
  — recalled state reflects what was true when written. Don't blindly re-plan what's
  settled; don't blindly obey a rejection whose blocker is now gone.
- **During** — append each locked decision and dead end as it happens; an unlogged
  rejected spike gets re-proposed next session on another machine.
- **End** — writing state, pushing it, and confirming the remote moved is the session's
  LAST action. An unconfirmed push is worse than none — the next machine pulls stale
  state believing it's current; the next Start's clean pull is the proof.

State lives for the project's duration and purges at project retirement — not per release
tag (a decision killed in 0.1 is still worth not reopening in 0.4).

## Per-unit loop (Standard and Critical)

Micro work does not run this formal loop. It stops after inspect, change, one relevant
runnable check, and a concise receipt.

1. PLAN (main-thread coordinator)
   Standalone: `$dev-rigor-stack-lite-plan`.
   Trace the real path, challenge unnecessary work, state brief acceptance criteria and
   the affected test list, then select Standard or Critical from the named triggers.
   Inventory manifests, lockfiles, CI commands, version readers, and external harnesses
   only when relevant. Diff size is not a risk trigger.

2. BUILD — `$dev-rigor-stack-lite-build` / `$coder-tdd-qa-lite`
   For a bug fix or changed logic, write or reproduce the smallest meaningful failure
   and witness RED before GREEN. Then implement the minimum change, refactor green, and
   run the affected suite/static checks. Do not manufacture RED for copy-only or
   mechanical work. Coverage is a gap diagnostic, not a threshold. Fan-out is a
   Critical option, not a Standard requirement.

3. VERIFY — `$dev-rigor-stack-lite-proof-gate` / `$proof-gate-lite`
   Standard uses a focused falsification pass and may combine VERIFY with REVIEW.
   Critical uses independent adversarial verification of the exact candidate. If the
   host cannot provide an independent worker, use an explicitly fresh adversarial
   serial pass and disclose the limitation.

   **Deterministic-detector harness (when present):** require randomized/pollution
   evidence only for shared mutable fixtures, global state, order dependence,
   concurrency, or a known pollution-prone area. Require mutation evidence only for
   Critical changed logic or genuine test-sensitivity uncertainty. Record replayable
   seeds and survivor dispositions. Neither tool is required merely because work is
   called `medium`, spans several files, or is being released. Never alter required
   status checks or branch protection; those remain owner-only.

4. REVIEW — use `$dev-rigor-stack-lite-audit-lite` / `$quick-audit-lite` as the
   Standard focused review. Use `$dev-rigor-stack-lite-audit-team` /
   `$audit-team-lite` for Critical work, with an independent reviewer when authorized
   and available. Add `$dev-rigor-stack-lite-walkthrough` only for changed UI,
   onboarding, acquisition, or installer journeys. Add
   `$dev-rigor-stack-lite-visitor-audit` / `$visitor-audit-lite` only for changed
   public pages, rendered docs, release assets, or announcements.

   A finding is a real defect. Classify a false positive OUT with evidence; never
   contort correct code to satisfy a wrong tool or pass a real defect by relabeling it.

5. MERGE — green-path decision and execution only when authorized.
   Standalone evidence decision: `$dev-rigor-stack-lite-merge-gate`.
   Prefer units landing on the integration line through a green PR. Passing gates proves
   readiness; it does not grant permission to merge. Execute a merge only when the user or
   host policy authorizes it. Never use admin override or bypass branch protection.

## Evaluator-owned exits (goal loops)

Start `rigor-goals` only when the work has real continuity risk: it crosses sessions,
needs a handoff, uses parallel agents, or waits on an external event. The number of
sequential steps alone is not a trigger. Give each persisted goal a deterministic exit
and try cap. Criteria a model must interpret ("make it good") do not qualify; route
those through the applicable VERIFY/REVIEW lane.

## Release overlay (once per version, before the tag)

The complete standalone coordinator is `$dev-rigor-stack-lite-release`.

Every release requires exact commit, version, and artifact identity; proof that the
artifact came from that source state; valid results for every check claimed; a complete
finding inventory; and human go/no-go authority. Define a rollback trigger and owner when
deployment or another hard-to-reverse action is in scope.

Select extra gates by applicability:

- Run the `$dev-rigor-stack-lite-gauntletgate` full lane only for Critical or broad
  releases. Add its walkthrough lane only when the Walkthrough trigger below applies;
  `all` is shorthand only when every lane applies. Standard releases use the focused
  review/gate evidence selected for their change.
- Run `$dev-rigor-stack-lite-proof-gate` for Critical changes or material changed claims.
- Run `$dev-rigor-stack-lite-visitor-audit` when public pages, rendered docs, release
  assets, or announcements changed.
- Run `$dev-rigor-stack-lite-walkthrough` when UI, onboarding, acquisition, or installer
  journeys changed. Require a verified clean machine for install/update/uninstall changes.
- Run `$dev-rigor-stack-lite-docs-gate` only for affected deliverables.
- Run randomized and mutation evidence only under the named detector triggers above.

Release PASS means every applicable required check is valid, evidence is bound to the
exact candidate, and `blocking_findings` is empty. Default closure is zero unresolved
release blockers:

- Blocker and Critical findings block the affected release.
- Major findings block when they violate acceptance criteria or create material release risk.
- Minor findings block only when they violate acceptance criteria.
- Nit findings never block.

Report every finding. Put unresolved nonblocking findings in the existing next-sprint
watchlist with an owner or explicit disposition. Literal `0/0/0/0/0` remains available
only when the owner selects it for that release.

Stop the loop:

- Allow no more than two broad release reviews of one candidate. Later review is focused
  on changed or previously failing areas unless scope materially changes.
- Freeze optional polish once acceptance criteria and applicable gates pass. New
  nonblocking observations go to the watchlist rather than reopening the candidate.
- If the same final-style execution fails twice for one cause, stop retrying and diagnose.
- Re-run evidence invalidated by a candidate change. Retain unaffected evidence only when
  its scope and identity chain prove the changed candidate did not alter what it covered.

After authorized publication, run only applicable live checks against the actual public
artifact. Changed release pages/assets require a cache-busted Visitor Audit. Changed
acquisition, UI, onboarding, or installer behavior requires the matching published
Walkthrough. Keep rollback readiness active until live `blocking_findings` is empty.

## Owner vs coordinator decisions

The coordinator (main-thread) decides everything reversible, in-spec, and
in-sandbox, and **never originates an owner decision** on its own initiative. The line
is a principle, not just a list: a decision is the owner's when it is **irreversible,
crosses a trust boundary, or exposes external value** — i.e. being wrong costs
something the model can't take back or wasn't authorized to spend. Instances:
1. **Scope & intent** — what to build, what "done" means, changing acceptance criteria.
2. **Crossing into the world** — publishing, tagging/releasing, deploying,
   sending/posting externally, spending money, deleting data the model didn't create.
   (Merging a reviewed green PR to the integration line is NOT this; a direct push
   bypassing PR/CI is.)
3. **Risk acceptance / gate overrides** — shipping with a known blocker, merging red,
   bypassing a gate.
4. **Trust-boundary & value calls** — security, privacy, licensing, legal/ethical/
   reputational weight.
5. **Go / no-go / priority / budget.**

Reconciliation (keeps this from meaning "ask permission constantly") — it's about who
**originates** the call:
- **Explicit request** ("tag 1.7.0") = the owner deciding live → execute now, no "are
  you sure."
- **Standing authorization** (green-path unit merges are pre-approved) = decided ahead
  → proceed.
- **Neither** = surface with a recommendation, and hold.
Concretely: green-path unit merge = standing authorization; the release tag = owner
decision, every time.

## Documentation discipline

Standalone gate: `$dev-rigor-stack-lite-docs-gate`.

- **Deliverable docs — accurate where affected.** Update the README, manual,
  architecture, landing page, or other public surface only when the change affects it
  or acceptance criteria require it. Do not manufacture a manual, landing page, or
  architecture drawing for an unrelated release.
- **Process artifacts — ephemeral, never hoarded.** Audits, status docs, handoffs,
  scratch — keep out of the repo (or a transient dir) and purge them. Over-documenting
  the wrong thing buries a repo in stale audits; YAGNI applies to docs too.
- **Exception — evidence outlives its decision, not the model's convenience.** The
  aggregate gauntlet report is not a purgeable process artifact while a live decision
  rests on it: it persists through the tag and the rollback window, then purges. A
  go/no-go must run on evidence in hand, not memory of it.

## Dependencies & degrade-if-missing

The bundle contains Markdown skills plus their scripts, references, and templates. It has
no lifecycle hooks, background runtime, trust activator, Stop interception, or private state
ledger. Enforcement is therefore instructional: the active agent must run the checks and
retain ordinary evidence artifacts. If a lane is missing or unreadable, mark that lane
INVALID; do not silently claim the complete stack ran. Host capabilities and higher-priority
instructions always govern tool use, delegation, approvals, merges, and publication.

An external harness, such as a real-organization workflow, contributes evidence but never
replaces the evidence required by the selected lane: one runnable check for Micro,
applicable RED/GREEN plus focused review for Standard, or the full Critical proof path.
Classify unavailable or supplemental evidence honestly; do not promote it into a gate.

**audit-lite / audit-team-lite vs. gauntletgate-lite** overlap by design — the same review
discipline in two packagings. The standalone audits are the per-unit *review reports*
(gate 4); gauntletgate-lite is the release-altitude *advancement gate*, and its `lite`/`full`
lanes re-run that same discipline self-contained (a gate can't invoke a separate skill
mid-run) plus a pass/fail verdict, a first-run attestation, and the `walkthrough` lane.
Same discipline, different altitude — a report vs. a gate.

## Cross-cutting, always on

- Use bounded leaf workers for Critical work only when the host provides them and
  delegation is authorized. Workers do not delegate or spawn sub-workers. Keep
  synthesis and the final gate decision with the coordinator. Otherwise use a fresh
  serial adversarial pass.
- Critical independent reviewers receive the acceptance contract, exact candidate
  identity, and raw evidence artifacts. Exclude the builder's narrative or explanation
  from their context. Standard uses a focused review without mandatory independence.
- Worker tier calibration (fan-out only): every worker states its tier and moderates
  rigor by it — the paste-in wording is the fan-out preamble below.
- Open-source-first: verify licenses; prefer MIT/Apache/MPL over BUSL/SSPL/closed.
- Evidence over claims: reproduce before fixing, verify with numbers, never claim
  beyond the evidence, own mistakes plainly.
- Code and process minimalism both apply: use the shortest working diff and do not add
  ceremony above the selected lane. Never skip evidence that lane requires.

The stack routes to the unit: Micro stops after one relevant check, Standard combines
focused VERIFY/REVIEW when useful, and Critical keeps the full path. Selected gates are
not optional; unselected gates need only the lane/applicability reason, not a fake artifact.

---

Fan-out worker preamble (paste the matching line at the top of each agent() prompt):

[worker] You are a bounded leaf worker. Do not delegate or spawn sub-workers. Your known
failure mode is passing your own "looks right" review instead of running a check that can
fail. For every claim, run the real check and paste the exact command and its verbatim
output.

[mechanical worker] You are a bounded leaf worker on a mechanical task. Do not delegate
or spawn sub-workers. Every result needs a named artifact — exact command + output. Do
not claim "verified" from inspection. If this task turns out to need judgment or
synthesis, stop and say so; do not guess.
