# Notice

`dev-rigor-stack-lite` is derived from `scottconverse/codex-dev-rigor-stack` version
1.7.0, commit `a1a738881d63a3c62b516db5ed748be084e37967`, which is MIT licensed.

The Lite adaptation removes the Codex hook runtime and Desktop trust machinery, renames
the package and entrypoints, makes authorization host-controlled, and replaces private
hook-ledger requirements with portable evidence artifacts.

`tools/rigor_goals.py` is adapted from the goal engine (`scripts/goals.py`) of
[`fivetaku/fablize`](https://github.com/fivetaku/fablize), MIT licensed. The adaptation
renames the tool and its state directory (`./.fablize/` → `./.rigor/`), restricts all
output to plain ASCII so stock Windows consoles render it correctly, and keeps the
behavioral contract — sequential stories, evidence checkpoints, and a final verification
gate — intact.
