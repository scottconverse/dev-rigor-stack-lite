# Troubleshooting

Start from a pinned source checkout and record `git rev-parse HEAD` plus the
version in `manifest.json`. Paths below are examples; substitute the target,
goals file, and anchor file you actually installed.

## PowerShell says script execution is disabled

For an effective `Restricted` execution policy, invoke the installer in a
child Windows PowerShell process:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills"
```

`-ExecutionPolicy Bypass` applies only to that process. It does not change the
user, machine, registry, or organization policy. A policy enforced by
`MachinePolicy` or `UserPolicy` may still take precedence; do not evade an
organization's controls. Ask its administrator for the approved installation
route.

Confirm the active policies with:

```powershell
Get-ExecutionPolicy -List
```

## The installer refuses to overwrite a skill

Without `-Force` or `--force`, an existing manifest-named skill directory is a
hard stop. This protects local changes. Review or back up the target, then run a
deliberate repair or upgrade:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills" -Force
```

```sh
./install.sh .claude/skills --force
```

Force replaces the 19 manifest-named skill directories and the installed goals
file. It does not authorize deleting unrelated target entries or owner text
outside the anchor markers.

## The anchor has a missing or duplicate marker

The managed span begins with `<!-- dev-rigor-lite anchor` and ends with
`<!-- /dev-rigor-lite anchor -->`.

- If a begin marker exists without an end marker, the installer stops. Back up
  the host instructions file and repair the marker pair by hand.
- If either marker appears more than once, stop. Identify the single lite-owned
  span before changing anything.
- Never resolve a marker problem by deleting the whole `AGENTS.md`,
  `CLAUDE.md`, or `GEMINI.md`; those files can contain unrelated owner policy.
- Text outside the one verified marker pair is owner content and must survive
  refresh and removal.

After repair, rerun the installer with force and confirm exactly one begin and
one end marker.

## Antigravity and Gemini CLI use different locations

| Target | Product | Default anchor |
|---|---|---|
| `.agents/skills` | Antigravity project install | `AGENTS.md` in the containing project |
| `.gemini/config/skills` | Antigravity user/config install | `.gemini/config/AGENTS.md`, adjacent to the skills directory |
| `.gemini/skills` | Gemini CLI project | `GEMINI.md` in the containing project |

A rooted target keeps its inferred host file beside the target skills
directory. If a custom layout needs another location, rerun with an explicit
`-Anchor` or `--anchor`. Remove any obsolete managed span only with the
marker-safe procedure in the [manual](manual.md); do not delete the surrounding
host file.

## A stale `audit-lite` remains after upgrade

Version 0.3.1 renamed lite's old `audit-lite` to `quick-audit-lite`. A force
upgrade removes `audit-lite` only when its `SKILL.md` contains lite's exact,
case-sensitive identity sentence. Without force, the installer warns and leaves
it untouched. A full-stack `audit-lite` or a file that merely mentions the old
name is preserved.

Do not delete `audit-lite` based on its directory name alone. If the installer
does not recognize it, identify its source before deciding whether it belongs.

## Full and lite skills collide

Do not install the full and lite bundles into the same skills directory. Several
entrypoint names overlap, so force installation can replace the other bundle's
files and make routing nondeterministic.

Use separate host profiles or separate skills directories. If a collision has
already happened, stop both installers, preserve the mixed directory for
diagnosis, choose one bundle for that target, and restore it from pinned source.
The removal procedure intentionally refuses to remove skill trees whose bytes
do not match the pinned lite source.

## Two tasks fight over `./.rigor/`

The goals tool supports one active plan per working tree. Concurrent tasks in a
shared checkout read and write the same `./.rigor/goals.json` and
`./.rigor/ledger.jsonl`.

Use a separate Git worktree for each concurrent task. Before replacing a plan,
run `status`; `create --force` is intentionally loud but does not merge two
plans. Preserve important state in a protected project system of record.

Overlapping CLI processes now refuse while `.rigor/mutation.lock` exists. If the named
process crashed, verify that no `rigor-goals` process is active before removing the stale
lock and retrying. Do not blindly delete a live lock. `goals.json` replacement is atomic,
but state and ledger updates are not a single filesystem transaction; preserve and
compare both files if an OS or storage failure interrupts a mutation.

## A goals command refuses a lifecycle transition

The v0.5.0 CLI makes state changes explicit:

- `add` requires `--authorization-source`; it records that text but does not authenticate
  the person named by it.
- `set-next` accepts only a pending goal. Use `reopen --id G001 --reason "..."` to
  return a failed, blocked, `waiting_external`, or `blocked_owner` goal to pending first.
- `cancelled` and `out_of_scope` checkpoints require non-empty evidence and an
  authorization-source receipt. Reopening either requires another receipt.
- `close` refuses unresolved work. Continuous and release plans additionally require an
  authorization-source receipt. A custom terminal on a single or finite plan requires
  explicit close instead of automatic closure.
- `set-mode` is the loud path for an owner-authorized mode change and requires an
  authorization-source receipt. Continuing and release modes also require a terminal;
  release mode requires candidate or publish intent.

Run `status` to see the pinned mode, terminal predicate, release intent, and every goal
state. Receipts are structural records: the CLI does not execute verification commands,
authenticate authority, or judge whether a predicate is true.

## A legacy goals plan changed to `finite_program`

The first v0.5.0 read migrates plan schema 1 once to schema 2, preserves goal IDs,
statuses, and evidence, and appends a `plan_migrated` ledger event. Old plans did not
record engagement mode, so migration uses the conservative compatibility default
`finite_program`; it does not infer intent from the brief. Review the plan and use
authorization-receipted `set-mode` if the owner intended continuing work.

Unsupported schemas, modes, malformed IDs, duplicate goals, invalid statuses, or
multiple active goals are refused without mutation. Preserve the files and diagnose the
producer rather than editing state until it happens to parse.

## Python or `rigor_goals.py` is not found

By default the tool is installed in `<TARGET>/../tools/rigor_goals.py`.
For example, `.claude/skills` puts it at
`.claude/tools/rigor_goals.py`.

```powershell
Get-Command python
python ".claude\tools\rigor_goals.py" status
```

```sh
command -v python3
python3 .claude/tools/rigor_goals.py status
```

Run the tool from the project root whose `./.rigor/` state you intend to use.
If Python is installed under a different command, use the approved interpreter
path explicitly. Override the destination during installation with
`-Goals <directory>` or `--goals <directory>` and quote paths containing
spaces.

For lifecycle recovery and safe removal, see the [manual](manual.md). For a
non-sensitive defect not covered here, use the
[issue tracker](https://github.com/scottconverse/dev-rigor-stack-lite/issues).
