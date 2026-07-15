#!/usr/bin/env python3
"""Tests for rigor-goals — the multi-story loop with a verification exit gate.

Drives the CLI as a subprocess in a temp directory (the real usage shape).
Covers the full happy cycle and every refusal path the gate promises.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "rigor_goals.py"


def run(cwd, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=cwd, capture_output=True, text=True,
    )


class RigorGoalsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cwd = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _create_two(self):
        return run(self.cwd, "create", "--brief", "test job",
                   "--goal", "one::first thing", "--goal", "two::second thing")

    def test_create_writes_state_in_dot_rigor(self):
        r = self._create_two()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2 stories", r.stdout)
        self.assertIn("G001", r.stdout)
        self.assertTrue((Path(self.cwd) / ".rigor" / "goals.json").is_file(),
                        "state must live in ./.rigor/")

    def test_create_refuses_overwrite_without_force(self):
        self._create_two()
        r = self._create_two()
        self.assertNotEqual(r.returncode, 0)
        r = run(self.cwd, "create", "--brief", "again", "--goal", "x::y", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_create_requires_a_goal_and_valid_format(self):
        r = run(self.cwd, "create", "--brief", "empty")
        self.assertNotEqual(r.returncode, 0)
        r = run(self.cwd, "create", "--brief", "bad", "--goal", "no-separator")
        self.assertNotEqual(r.returncode, 0)

    def test_next_activates_in_order_and_flags_final(self):
        self._create_two()
        r = run(self.cwd, "next")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("G001", r.stdout)
        self.assertNotIn("Final story", r.stdout)
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
            "--evidence", "did it")
        r = run(self.cwd, "next")
        self.assertIn("G002", r.stdout)
        self.assertIn("Final story", r.stdout, "final story must announce the gate")

    def test_checkpoint_refuses_inactive_story(self):
        self._create_two()
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
                "--evidence", "x")
        self.assertNotEqual(r.returncode, 0, "checkpoint before `next` must refuse")

    def test_complete_refuses_empty_evidence(self):
        self._create_two()
        run(self.cwd, "next")
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete")
        self.assertNotEqual(r.returncode, 0)
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
                "--evidence", "   ")
        self.assertNotEqual(r.returncode, 0, "whitespace evidence must refuse")

    def test_final_story_gate_requires_verify_cmd_and_evidence(self):
        self._create_two()
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
            "--evidence", "done")
        run(self.cwd, "next")
        # evidence alone is NOT enough on the final story
        r = run(self.cwd, "checkpoint", "--id", "G002", "--status", "complete",
                "--evidence", "done")
        self.assertNotEqual(r.returncode, 0, "final story must refuse without verify flags")
        # verify-cmd without verify-evidence still refuses
        r = run(self.cwd, "checkpoint", "--id", "G002", "--status", "complete",
                "--evidence", "done", "--verify-cmd", "pytest")
        self.assertNotEqual(r.returncode, 0)
        # both present -> accepted, loop closes
        r = run(self.cwd, "checkpoint", "--id", "G002", "--status", "complete",
                "--evidence", "done", "--verify-cmd", "pytest",
                "--verify-evidence", "4 passed")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("all stories complete", r.stdout)

    def test_failed_and_blocked_do_not_need_verify(self):
        self._create_two()
        run(self.cwd, "next")
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "failed",
                "--evidence", "test exploded")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_status_resumes_after_session_death(self):
        self._create_two()
        run(self.cwd, "next")
        # a "fresh session" only runs status — it must see the live plan
        r = run(self.cwd, "status")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("0/2", r.stdout)
        self.assertIn("in_progress", r.stdout)

    def test_status_without_plan_explains_itself(self):
        r = run(self.cwd, "status")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("create", (r.stderr + r.stdout).lower())

    def test_no_false_completion_when_stories_failed_or_blocked(self):
        # Gate finding (critical): a plan whose stories all ended failed/blocked
        # must never be reported as complete — by checkpoint OR by next.
        self._create_two()
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "blocked",
            "--evidence", "stuck")
        run(self.cwd, "next")
        r = run(self.cwd, "checkpoint", "--id", "G002", "--status", "failed",
                "--evidence", "broke")
        self.assertNotIn("all stories complete", r.stdout,
                         "failed/blocked plan reported as complete (checkpoint)")
        self.assertIn("failed", r.stdout.lower())
        r = run(self.cwd, "next")
        self.assertNotIn("all stories complete", r.stdout,
                         "failed/blocked plan reported as complete (next)")

    def test_output_is_pure_ascii(self):
        # Gate finding (major): non-ASCII output turns into cp1252 mojibake on
        # stock Windows consoles. The tool's own output must be plain ASCII.
        self._create_two()
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
            "--evidence", "did it")
        run(self.cwd, "next")
        chunks = [
            run(self.cwd, "status").stdout,
            run(self.cwd, "next").stdout,
            run(self.cwd, "checkpoint", "--id", "G002", "--status", "complete",
                "--evidence", "e", "--verify-cmd", "c",
                "--verify-evidence", "r").stdout,
            run(self.cwd, "status").stdout,
        ]
        # error paths write to stderr — those must be ASCII too
        chunks.append(run(self.cwd, "checkpoint", "--id", "G001", "--status",
                          "complete", "--evidence", "x").stderr)  # not active
        fresh = tempfile.TemporaryDirectory()
        self.addCleanup(fresh.cleanup)
        chunks.append(run(fresh.name, "status").stderr)  # no plan
        for chunk in chunks:
            self.assertTrue(all(ord(ch) < 128 for ch in chunk),
                            f"non-ASCII in output: {chunk!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
