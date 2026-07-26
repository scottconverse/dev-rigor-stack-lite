---
name: dev-rigor-stack-lite-merge-gate
description: Run the dev-rigor-stack-lite green-path merge decision independently. Use for "$dev-rigor-stack-lite-merge-gate", "/dev-rigor-stack-lite-merge-gate", pre-merge evidence validation, or deciding whether a reviewed unit may merge without bypasses.
---

# Dev Rigor Stack — MERGE gate

Verify the exact head commit, target branch, CI state, review state, unresolved comments,
the selected lane's evidence, and conditional Walkthrough/Visitor results. Micro requires
its inspect/change/check receipt; Standard requires applicable PLAN/BUILD and focused
VERIFY/REVIEW; Critical requires the full independent path.
Re-run checks invalidated by changes after their evidence was captured. Evidence for a
different SHA, build, installer, environment, or public artifact does not transfer.

Allow only the configured green-path merge method under existing authorization. Never use
admin override, bypass branch protection, merge red, silently dismiss a finding, or treat
a partial/unverifiable gate as passed. Report READY TO MERGE or DO NOT MERGE with exact
blocking evidence. Executing the merge remains subject to the user's explicit or standing
authorization and the active GitHub workflow.
