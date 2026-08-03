# Contributing

Contributions should be narrow, evidence-backed, and portable across supported
Agent Skills hosts.

## Change workflow

1. Open a focused issue or describe one bounded unit in the pull request.
2. Trace the current behavior and define observable acceptance cases.
3. Add or identify a regression check and witness it fail for the intended
   reason before production implementation starts.
4. Make the smallest implementation that turns the check green.
5. Run validation at the change's blast radius, then inspect the exact
   candidate diff and artifacts with fresh reviewer context.
6. Record unresolved risks and skipped checks explicitly. A skip is never
   silent.

Parallel contributors must own disjoint files. Test-first dependencies remain
sequential: the failing test is witnessed before implementation begins.

## Local validation

From the repository root, run:

```sh
python tools/validate_bundle.py
python tools/test_rigor_goals.py
git diff --check
```

Use `python3` in environments where that is the Python command. Installer,
anchor, host-placement, or lifecycle changes also require the relevant Windows,
Ubuntu, and macOS CI lanes. Documentation changes require a rendered Markdown
read, link check, and comparison against current behavior.

Do not make a failing test pass by weakening or deleting its assertion. Capture
the RED output, the GREEN output, the exact candidate commit, and hashes for
release artifacts or other identity-sensitive evidence.

## Bundle invariants

- `manifest.json` is the version authority. Version labels in shipped skills
  must agree with it.
- `manifest.json` owns the skill inventory, and that inventory must remain
  exactly 20 unless an explicitly planned release changes the contract.
- Keep portable workflow prose host-neutral. Do not encode model names or
  personal agent assignments in the bundle.
- Do not add hooks, background services, trust activation, Stop interception,
  or a private evidence ledger to the lite bundle.
- Owner-only installer opt-outs remain owner decisions. Automated agents must
  not add or pass them on their own initiative.

## Pull request evidence

A pull request should state:

- scope and explicit non-scope;
- acceptance cases and the witnessed RED;
- exact candidate SHA and worktree state;
- commands run, environments used, and raw log or artifact paths;
- checksums for archives or other release-sensitive artifacts;
- security, portability, documentation, and rollback considerations; and
- any evidence invalidated and rerun after a correction.

Keep builder explanation separate from independent review inputs. Reviewers
should receive the acceptance contract, exact candidate identity, raw evidence,
and exact diff rather than relying on the builder's narrative.

Report vulnerabilities according to [SECURITY.md](SECURITY.md). By
contributing, you agree that your work is provided under the
[MIT License](LICENSE).
