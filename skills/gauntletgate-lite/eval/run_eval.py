#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""GauntletGate golden eval — proves the first-run dead-end is REAL and detected.

This is the sprint's exit gate and GauntletGate dogfooding itself. It:

  1. Constructs the GENUINE dependency-ABSENT state (the new-user reality) — it
     scrubs the dependency env var, it does not mock it.
  2. Serves the sample app and fetches it as a brand-new user.
  3. Asserts the core action is DISABLED and a dead-end marker is present — the
     exact condition a correct Walkthrough lane reports as a Blocker / DO NOT
     ADVANCE.
  4. Then constructs the dependency-PRESENT state and asserts the core action is
     reachable.
  5. Guards against testing theater: if the ABSENT state is NOT a dead-end, or the
     PRESENT state IS one, the fixture is broken and the eval FAILS.
  6. Writes an artifact bundle to eval/artifacts/ (captured HTML for both states +
     a verdict JSON) — the same kind of observable proof the attestation must link
     to.

stdlib only; no browser required. Exit 0 = eval passed (the gate would correctly
return DO NOT ADVANCE for the first-run state).
"""

from __future__ import annotations

import contextlib
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
APP = HERE / "sample-app" / "app.py"
ARTIFACTS = HERE / "artifacts"


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _serve_and_fetch(backend_present: bool) -> str:
    """Launch the sample app with the dependency present/absent and fetch the page."""
    port = _free_port()
    env = dict(os.environ)
    if backend_present:
        env["GAUNTLET_SAMPLE_BACKEND"] = "http://127.0.0.1:9/configured"  # a real, set value
    else:
        env.pop("GAUNTLET_SAMPLE_BACKEND", None)  # genuinely ABSENT — scrubbed, not mocked
    proc = subprocess.Popen([sys.executable, str(APP), str(port)], env=env)
    try:
        url = f"http://127.0.0.1:{port}/"
        deadline = time.monotonic() + 10
        last_err: Exception | None = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    return r.read().decode("utf-8")
            except Exception as e:  # server not up yet
                last_err = e
                time.sleep(0.1)
        raise RuntimeError(f"sample app never became reachable on {url}: {last_err}")
    finally:
        proc.terminate()
        with contextlib.suppress(Exception):
            proc.wait(timeout=5)


def _is_dead_end(html: str) -> bool:
    """A new user is dead-ended: core action disabled AND a dead-end marker shown."""
    core_disabled = "id='core-action' disabled" in html
    deadend_marker = "data-deadend='true'" in html
    return core_disabled and deadend_marker


def _core_reachable(html: str) -> bool:
    return "id='core-action'>" in html and "disabled" not in html.split("core-action")[1][:20]


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    failures: list[str] = []

    # 1. The new-user reality: dependency ABSENT.
    absent_html = _serve_and_fetch(backend_present=False)
    (ARTIFACTS / "first-run-absent.html").write_text(absent_html, encoding="utf-8")
    absent_deadend = _is_dead_end(absent_html)
    if not absent_deadend:
        failures.append(
            "THEATER GUARD: dependency-absent state is NOT a dead-end — the fixture "
            "doesn't reproduce a real first-run dead-end, so it proves nothing."
        )

    # 2. The provisioned reality: dependency PRESENT.
    present_html = _serve_and_fetch(backend_present=True)
    (ARTIFACTS / "returning-present.html").write_text(present_html, encoding="utf-8")
    present_reachable = _core_reachable(present_html)
    if not present_reachable:
        failures.append(
            "THEATER GUARD: dependency-present state is ALSO blocked — the dead-end "
            "isn't dependency-driven, so the fixture is invalid."
        )

    # 3. The gate assertion: the absent (new-user) state must be DO NOT ADVANCE.
    gate_would_block = absent_deadend
    verdict = {
        "fixture": "sample-app first-run dead-end",
        "dependency_absent_is_dead_end": absent_deadend,
        "dependency_present_is_reachable": present_reachable,
        "expected_gate_verdict_for_first_run": "DO NOT ADVANCE",
        "gate_would_block_first_run": gate_would_block,
        "eval_passed": not failures,
        "note": (
            "Deterministically proves the first-run dead-end is REAL and detectable "
            "by a new-user fetch with the dependency genuinely absent — i.e. a "
            "correctly-executed Walkthrough lane WOULD return DO NOT ADVANCE. It does "
            "not exercise an LLM agent's judgment; see eval/README.md for the live "
            "agent eval."
        ),
    }
    (ARTIFACTS / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    print(json.dumps(verdict, indent=2))
    if failures:
        print("\nEVAL FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(
        "\nEVAL PASSED: a brand-new user with the dependency absent is dead-ended on the "
        "core feature; a correct Walkthrough lane returns DO NOT ADVANCE. Artifacts in "
        f"{ARTIFACTS}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
