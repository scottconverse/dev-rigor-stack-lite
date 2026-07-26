# Architecture

dev-rigor-stack-lite is a portable set of Markdown workflows plus two small,
local persistence mechanisms. It does not run a service and it does not add
hooks, a background process, trust activation, Stop interception, or a private
evidence ledger.

## Installed components

```mermaid
flowchart LR
    Source["Pinned source or release archive"] --> Installer["install.ps1 or install.sh"]
    Owner["Human owner"] --> Installer
    Installer --> Skills["19 skill directories"]
    Installer --> Goals["tools/rigor_goals.py"]
    Installer --> Anchor["Managed block in host instructions"]
    Skills --> Host["Agent host"]
    Anchor --> Host
    Operator["Operator, when continuity risk exists"] --> Goals
    Goals --> State["./.rigor/goals.json and ledger.jsonl"]
    Host --> Gates["Micro - Standard - Critical routing"]
    Evidence["Tests, CI, logs, hashes, reports"] --> Gates
    Policy["Host policy and owner authority"] --> Gates
```

Text fallback: a human runs one of the installers from pinned source. The
installer copies the 19 skill directories, one Python tool, and one
marker-fenced block in a host instructions file. The host reads the skills and
anchor. For cross-session work, handoffs, parallel agents, or external waits, the
operator invokes the goals tool, which writes project-local state under `./.rigor/`.
Ordinary same-session work skips it. Tests, CI, and other raw artifacts feed the selected lane.
Host policy and human authority still control permissions, merges, and
publication.

| Component | Responsibility | Explicit limit |
|---|---|---|
| `skills/` | Portable workflow instructions and entrypoints | Instructions are not mechanical enforcement |
| `anchor/anchor.md` | A short, persistent reminder in the host instructions file | Only the marker-fenced span is managed |
| `tools/rigor_goals.py` | Sequential task state and a final evidence-recording gate | It records evidence; it does not execute or validate the recorded command |
| `./.rigor/` | Current worktree's plan and append-only event ledger | Ordinary local files, not tamper-resistant storage |
| `install.ps1` and `install.sh` | Copy the three tiers to explicit or inferred locations | Run only with the invoking user's permissions |

## Delivery control flow

```mermaid
flowchart TD
    Route{"Risk lane"}
    Route -- "Micro" --> Micro["MICRO: inspect - change - one check - receipt"]
    Route -- "Standard" --> Plan["STANDARD: brief PLAN and acceptance"]
    Route -- "Critical" --> Critical["CRITICAL: full PLAN and risk contract"]
    Plan --> Build["BUILD: applicable RED, GREEN, affected checks"]
    Critical --> Build
    Build --> Verify["VERIFY/REVIEW: focused for Standard, independent for Critical"]
    Verify --> Merge["MERGE: evaluate selected-lane evidence"]
    Micro --> Merge
    Verify -- "Refuted claim or failed check" --> Build
    Merge -- "Stale or mismatched evidence" --> Verify
    Merge --> Release["RELEASE OVERLAY: exact candidate + applicable gates + owner"]
    Harness["Optional external regression harness"] -. "Supplemental evidence" .-> Verify
```

Text fallback: localized mechanical work uses Micro. Ordinary work uses Standard.
Named risks such as auth, money, persisted data, security, concurrency, installers,
irreversible operations, or broad public contracts use Critical. Standard applies
RED/GREEN and focused review where relevant; Critical adds independent proof. Release
binds evidence to the exact candidate and selects only applicable gates. External
harnesses can add evidence but cannot replace the selected lane.

## Boundaries and trust

- The bundle has no long-running runtime and opens no network connection during
  normal use. CI and users may run their own networked tools outside this
  boundary.
- Host policy owns tool availability, filesystem and network permissions,
  delegation, approvals, and whether an agent may merge or publish. Passing a
  workflow gate grants none of those permissions.
- The installers trust the source tree, target paths, and explicit overrides
  supplied by the human operator. `-Force` or `--force` replaces only
  manifest-named skill directories, refreshes the installed goals file, and
  updates the managed anchor span.
- The anchor is ordinary text in a host instructions file. It can influence an
  agent that reads it, but it cannot override host policy or protect itself
  from a process with write access.
- `./.rigor/` is a continuity aid, not a security boundary. A process that can
  edit or delete worktree files can alter or remove it. Do not put secrets in
  the plan, ledger, or evidence.
- Evidence is valid only to the extent that its exact candidate identity,
  environment, command, and raw artifacts support the claim. The goals tool's
  recorded result is not independent proof.

For installation and lifecycle procedures, see the [manual](manual.md). For
security reporting and operational limits, see [SECURITY.md](../SECURITY.md).
