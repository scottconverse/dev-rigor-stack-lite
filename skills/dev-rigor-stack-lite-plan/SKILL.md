---
name: dev-rigor-stack-lite-plan
description: >
  Run the dev-rigor-stack-lite PLAN stage independently: trace current behavior,
  challenge unnecessary work, select Micro, Standard, or Critical from named risk,
  define applicable acceptance/tests, and route required gates. Use for "$dev-rigor-stack-lite-plan",
  "/dev-rigor-stack-lite-plan", rigorous implementation planning, or planning one unit
  before BUILD.
---

# Dev Rigor Stack — PLAN

Read the real implementation, tests, configuration, documentation, and current durable
state before proposing changes. Trace the behavior end to end. Apply reuse-before-build:
ask whether the change needs to exist, already exists, belongs in the platform/standard
library, or can be smaller without losing requirements.

Select the lane first. Micro is localized mechanical work with no Critical trigger;
Standard is the default; Critical covers auth/secrets, money, persistence/migrations/
deletion, security/privacy, concurrency/order/idempotency, install/deploy/rollback,
irreversible operations, or broad public compatibility/API contracts. File count, file
type, `medium+`, and release status are not triggers.

For Micro, return only scope, confirmation that no Critical trigger applies, the planned
edit, and one relevant runnable check. Do not manufacture a test list or full artifact set.

For Standard or Critical, produce:

- scope and explicit non-scope;
- current behavior and evidence;
- when relevant, a proportional inventory of project/package manifests and lockfiles,
  CI workflows and canonical test/lint/type/build commands, the version authority and
  every version reader, and existing integration or real-organization harnesses;
- acceptance criteria and definition of done;
- an applicable test list with RED conditions for bugs/changed logic and deterministic exits;
- the selected lane, named triggers, and impact-based blast radius;
- security, data, compatibility, migration, performance, documentation, UI, public-surface,
  installer, and newcomer-journey impacts;
- required downstream gates and reasons for every conditional skip;
- rollback/checkpoint strategy for risky work;
- owner decisions required, without inventing the owner's answer.

The output must be directly consumable by `$dev-rigor-stack-lite-build`. Unknowns that could
materially change the implementation remain explicit; do not turn assumptions into facts.
