# dev-rigor-stack-lite commands reference

Moved verbatim from CLAUDE.md.

## Commands

Python 3.12, stdlib only. No package manager. Two test entrypoints:

```bash
python tools/validate_bundle.py
python tools/test_rigor_goals.py
```

`validate_bundle.py` prints `BUNDLE_VALID` / `BUNDLE_INVALID` and exits nonzero on failure.
It is both the bundle contract check and a live smoke test of the goals gate.

There is no test framework and no per-test selection — each file is a single runnable script.
Use `python3` on systems where Python 3 is named that.

Install to a scratch project (never install over this repo's own `CLAUDE.md` while testing):

```bash
./install.sh .claude/skills
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills"
```

Exercise the goals CLI:

```bash
python3 tools/rigor_goals.py create --brief "ship X" --goal "api::add the endpoint"
python3 tools/rigor_goals.py next
python3 tools/rigor_goals.py checkpoint --id G001 --status complete --evidence "4 passed" --verify-cmd "pytest" --verify-evidence "12 passed"
python3 tools/rigor_goals.py status
```
