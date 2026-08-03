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

`skills/dev-rigor-stack-lite-brainstorm/SKILL.md` is adapted from
`skills/brainstorming/SKILL.md` in [`obra/superpowers`](https://github.com/obra/superpowers),
tag v5.0.7, peeled commit `1f20bef3f59b85ad7b52718f822e37c4478a3ff5`.
The adaptation keeps the elicitation and approval concepts, rewrites them as a
host-neutral proportional workflow, and adds an explicit PLAN handoff. The Visual
Companion is not included. The upstream source is MIT licensed:

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
