#!/usr/bin/env python3
"""Tests for rigor-goals — the multi-story loop with a verification exit gate.

Drives the CLI as a subprocess in a temp directory (the real usage shape).
Covers the full happy cycle and every refusal path the gate promises.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "rigor_goals.py"


def run(cwd, *args, env=None):
    import os
    merged = {**os.environ, **(env or {})}
    # Explicit utf-8 + replace: when a test forces the child onto cp1252
    # (PYTHONIOENCODING), user text in its output is legitimately not UTF-8,
    # and the platform-default decoder must not blow up the harness.
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=cwd, capture_output=True, text=True, env=merged,
        encoding="utf-8", errors="replace",
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

    def _plan(self):
        return json.loads((Path(self.cwd) / ".rigor" / "goals.json").read_text(encoding="utf-8"))

    def _events(self):
        path = Path(self.cwd) / ".rigor" / "ledger.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

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

    def test_non_ascii_user_text_never_crashes_on_legacy_console(self):
        # Fix-wave review (critical): user-supplied emoji crashed the tool with
        # UnicodeEncodeError on cp1252 consoles after the guard was removed.
        # PYTHONIOENCODING forces the failing encoding on any platform.
        cp = {"PYTHONIOENCODING": "cp1252"}
        r = run(self.cwd, "create", "--brief", "emoji job \U0001f680",
                "--goal", "x—y::obj \U0001f680", env=cp)
        self.assertEqual(r.returncode, 0, f"create crashed: {r.stderr}")
        r = run(self.cwd, "status", env=cp)
        self.assertEqual(r.returncode, 0, f"status crashed: {r.stderr}")
        r = run(self.cwd, "next", env=cp)
        self.assertEqual(r.returncode, 0, f"next crashed: {r.stderr}")
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
                "--evidence", "done \U0001f680", "--verify-cmd", "c",
                "--verify-evidence", "r", env=cp)
        self.assertEqual(r.returncode, 0, f"checkpoint crashed: {r.stderr}")

    def test_force_replacement_is_loud_and_events_carry_plan_id(self):
        # Gate incident (0.2.2): a plan silently vanished and was silently
        # replaced. --force must announce what it destroys, and every ledger
        # event must carry the plan_id so mixed histories are detectable.
        import json
        self._create_two()
        r = run(self.cwd, "create", "--brief", "second", "--goal", "x::y", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("REPLACING", r.stdout, "--force replacement must be loud")
        self.assertIn("test job", r.stdout, "must name the plan being destroyed")
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "failed",
            "--evidence", "e")
        ledger = (Path(self.cwd) / ".rigor" / "ledger.jsonl").read_text(encoding="utf-8")
        events = [json.loads(line) for line in ledger.splitlines() if line]
        plan_ids = {e.get("plan_id") for e in events if e["event"] != "plan_created"}
        created_ids = [e["plan_id"] for e in events if e["event"] == "plan_created"]
        self.assertEqual(len(created_ids), 2, "both plans must be in the ledger")
        self.assertTrue(all(pid == created_ids[-1] for pid in plan_ids),
                        f"post-replacement events must carry the new plan_id: {events}")

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

    def test_create_defaults_to_schema_two_finite_program(self):
        r = self._create_two()
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = self._plan()
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(plan["mode"], "finite_program")
        self.assertFalse(plan["closed"])
        self.assertIn("finite_program", r.stdout)

    def test_create_persists_each_explicit_mode_and_pins_terminal(self):
        for mode in ("single_unit", "finite_program", "continuous_development", "release_workflow"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as cwd:
                args = ["create", "--brief", mode, "--mode", mode,
                        "--terminal", f"terminal for {mode}", "--goal", "one::work"]
                if mode == "release_workflow":
                    args.extend(["--release-intent", "candidate"])
                r = run(cwd, *args)
                self.assertEqual(r.returncode, 0, r.stderr)
                plan = json.loads((Path(cwd) / ".rigor" / "goals.json").read_text(encoding="utf-8"))
                self.assertEqual(plan["mode"], mode)
                self.assertEqual(plan["terminal_predicate"], f"terminal for {mode}")

    def test_continuing_modes_require_an_explicit_terminal(self):
        for mode in ("continuous_development", "release_workflow"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as cwd:
                args = ["create", "--brief", mode, "--mode", mode, "--goal", "one::work"]
                if mode == "release_workflow":
                    args.extend(["--release-intent", "candidate"])
                r = run(cwd, *args)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("terminal", (r.stderr + r.stdout).lower())

    def test_legacy_plan_migrates_once_and_preserves_goal_state(self):
        state = Path(self.cwd) / ".rigor"
        state.mkdir()
        legacy = {
            "plan_id": "legacy123",
            "brief": "legacy",
            "created": "2026-07-01T00:00:00+00:00",
            "goals": [{"id": "G001", "title": "old", "objective": "work",
                       "status": "blocked", "evidence": "owner wait"}],
        }
        (state / "goals.json").write_text(json.dumps(legacy), encoding="utf-8")
        first = run(self.cwd, "status")
        second = run(self.cwd, "status")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        plan = self._plan()
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(plan["mode"], "finite_program")
        self.assertEqual(plan["goals"], legacy["goals"])
        migrated = [event for event in self._events() if event["event"] == "plan_migrated"]
        self.assertEqual(len(migrated), 1)
        self.assertEqual(migrated[0]["plan_id"], "legacy123")

    def test_unknown_schema_or_mode_refuses_loudly(self):
        state = Path(self.cwd) / ".rigor"
        state.mkdir()
        bad = {"schema_version": 99, "mode": "finite_program", "plan_id": "bad", "goals": []}
        (state / "goals.json").write_text(json.dumps(bad), encoding="utf-8")
        r = run(self.cwd, "status")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("schema", (r.stderr + r.stdout).lower())

        bad["schema_version"] = 2
        bad["mode"] = "invented"
        bad["goals"] = [{"id": "G001", "title": "one", "objective": "work",
                         "status": "pending", "evidence": None}]
        bad.update({"terminal_predicate": "done", "release_intent": "none",
                    "next_goal_id": None, "next_action": None, "closed": False})
        (state / "goals.json").write_text(json.dumps(bad), encoding="utf-8")
        r = run(self.cwd, "status")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("mode", (r.stderr + r.stdout).lower())

    def test_continuous_last_known_story_is_nonterminal(self):
        r = run(self.cwd, "create", "--brief", "continue", "--mode", "continuous_development",
                "--terminal", "owner stops", "--goal", "one::work")
        self.assertEqual(r.returncode, 0, r.stderr)
        run(self.cwd, "next")
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
                "--evidence", "done", "--verify-cmd", "pytest", "--verify-evidence", "1 passed")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("all stories complete", r.stdout)
        self.assertIn("NOT COMPLETE", r.stdout)
        self.assertIn("reconcile", r.stdout.lower())

    def test_add_requires_authorization_without_mutating_state_or_ledger(self):
        self._create_two()
        goals_before = (Path(self.cwd) / ".rigor" / "goals.json").read_bytes()
        ledger_before = (Path(self.cwd) / ".rigor" / "ledger.jsonl").read_bytes()
        r = run(self.cwd, "add", "--goal", "three::third thing")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((Path(self.cwd) / ".rigor" / "goals.json").read_bytes(), goals_before)
        self.assertEqual((Path(self.cwd) / ".rigor" / "ledger.jsonl").read_bytes(), ledger_before)

    def test_add_is_loud_and_ledger_stamped_with_authorization(self):
        self._create_two()
        r = run(self.cwd, "add", "--goal", "three::third thing",
                "--authorization-source", "accepted roadmap item R3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ADDING G003", r.stdout)
        self.assertIn("accepted roadmap item R3", r.stdout)
        self.assertEqual(self._plan()["goals"][-1]["id"], "G003")
        event = self._events()[-1]
        self.assertEqual(event["event"], "goal_added")
        self.assertEqual(event["plan_id"], self._plan()["plan_id"])
        self.assertEqual(event["authorization_source"], "accepted roadmap item R3")

    def test_set_next_is_loud_persisted_and_ledger_stamped(self):
        self._create_two()
        r = run(self.cwd, "set-next", "--id", "G002", "--reason", "dependency ready")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SET-NEXT G002", r.stdout)
        self.assertEqual(self._plan()["next_goal_id"], "G002")
        event = self._events()[-1]
        self.assertEqual(event["event"], "next_goal_set")
        self.assertEqual(event["plan_id"], self._plan()["plan_id"])
        self.assertEqual(event["reason"], "dependency ready")
        r = run(self.cwd, "next")
        self.assertIn("G002", r.stdout)

    def test_nonterminal_checkpoint_statuses_are_accepted_and_remain_honest(self):
        for status in ("waiting_external", "blocked_owner"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as cwd:
                run(cwd, "create", "--brief", status, "--goal", "one::work")
                run(cwd, "next")
                r = run(cwd, "checkpoint", "--id", "G001", "--status", status,
                        "--evidence", f"evidence for {status}")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("NOT complete", r.stdout)

    def test_cancelled_and_out_of_scope_require_evidence_and_authorization(self):
        for status in ("cancelled", "out_of_scope"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as cwd:
                run(cwd, "create", "--brief", status,
                    "--goal", "one::work", "--goal", "two::finish")
                run(cwd, "next")
                state_before = (Path(cwd) / ".rigor" / "goals.json").read_bytes()
                r = run(cwd, "checkpoint", "--id", "G001", "--status", status)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual((Path(cwd) / ".rigor" / "goals.json").read_bytes(), state_before)
                r = run(cwd, "checkpoint", "--id", "G001", "--status", status,
                        "--evidence", "owner removed this unit")
                self.assertNotEqual(r.returncode, 0)
                r = run(cwd, "checkpoint", "--id", "G001", "--status", status,
                        "--evidence", "owner removed this unit",
                        "--authorization-source", "owner instruction 2026-07-31")
                self.assertEqual(r.returncode, 0, r.stderr)
                ledger = Path(cwd) / ".rigor" / "ledger.jsonl"
                event = json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(event["authorization_source"], "owner instruction 2026-07-31")
                run(cwd, "next")
                r = run(cwd, "checkpoint", "--id", "G002", "--status", "complete",
                        "--evidence", "finished remaining unit", "--verify-cmd", "pytest",
                        "--verify-evidence", "green")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("all stories complete", r.stdout)
                self.assertIn("all stories resolved", r.stdout)

    def test_close_checks_structure_requires_owner_source_and_never_runs_command(self):
        marker = Path(self.cwd) / "must-not-exist"
        run(self.cwd, "create", "--brief", "continue", "--mode", "continuous_development",
            "--terminal", "owner stops", "--goal", "one::work")
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
            "--evidence", "done", "--verify-cmd", "pytest", "--verify-evidence", "1 passed")
        command = f"python3 -c \"open({str(marker)!r}, 'w').write('bad')\""
        r = run(self.cwd, "close", "--evidence", "owner ended engagement",
                "--verify-cmd", command, "--verify-evidence", "receipt supplied")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("authorization", (r.stderr + r.stdout).lower())
        r = run(self.cwd, "close", "--evidence", "owner ended engagement",
                "--verify-cmd", command, "--verify-evidence", "receipt supplied",
                "--authorization-source", "owner instruction 2026-07-31")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(marker.exists(), "verify-cmd is a receipt and must never be executed")
        self.assertTrue(self._plan()["closed"])
        self.assertIn("does not verify truth", r.stdout)
        self.assertEqual(self._events()[-1]["event"], "plan_closed")

    def test_close_refuses_unresolved_work(self):
        self._create_two()
        r = run(self.cwd, "close", "--evidence", "not actually done",
                "--verify-cmd", "pytest", "--verify-evidence", "unknown")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unresolved", (r.stderr + r.stdout).lower())

    def test_custom_finite_terminal_requires_explicit_structural_close(self):
        r = run(self.cwd, "create", "--brief", "approval-bound", "--mode", "finite_program",
                "--terminal", "owner approves release notes", "--goal", "one::work")
        self.assertEqual(r.returncode, 0, r.stderr)
        run(self.cwd, "next")
        r = run(self.cwd, "checkpoint", "--id", "G001", "--status", "complete",
                "--evidence", "unit green", "--verify-cmd", "pytest",
                "--verify-evidence", "1 passed")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self._plan()["closed"])
        self.assertIn("requires explicit close", r.stdout)
        r = run(self.cwd, "close", "--evidence", "approval receipt recorded",
                "--verify-cmd", "inspect owner instruction", "--verify-evidence", "approved")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_status_exposes_terminal_and_release_intent(self):
        run(self.cwd, "create", "--brief", "publish", "--mode", "release_workflow",
            "--terminal", "published artifact verified", "--release-intent", "publish",
            "--goal", "one::work")
        r = run(self.cwd, "status")
        self.assertIn("Terminal: published artifact verified", r.stdout)
        self.assertIn("Release intent: publish", r.stdout)

    def test_reopen_recovers_blocked_or_waiting_goal_with_a_ledger_receipt(self):
        run(self.cwd, "create", "--brief", "recover", "--mode", "continuous_development",
            "--terminal", "owner stops", "--goal", "one::work")
        run(self.cwd, "next")
        run(self.cwd, "checkpoint", "--id", "G001", "--status", "blocked",
            "--evidence", "dependency missing")
        r = run(self.cwd, "reopen", "--id", "G001")
        self.assertNotEqual(r.returncode, 0)
        r = run(self.cwd, "reopen", "--id", "G001",
                "--reason", "dependency now available")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("REOPENING G001", r.stdout)
        self.assertEqual(self._plan()["goals"][0]["status"], "pending")
        self.assertEqual(self._events()[-1]["event"], "goal_reopened")

    def test_mode_change_is_loud_and_requires_an_authorization_receipt(self):
        self._create_two()
        before = (Path(self.cwd) / ".rigor" / "goals.json").read_bytes()
        r = run(self.cwd, "set-mode", "--mode", "continuous_development",
                "--terminal", "owner stops")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((Path(self.cwd) / ".rigor" / "goals.json").read_bytes(), before)
        r = run(self.cwd, "set-mode", "--mode", "continuous_development",
                "--terminal", "owner stops",
                "--authorization-source", "owner changed engagement 2026-07-31")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SET-MODE", r.stdout)
        self.assertEqual(self._plan()["mode"], "continuous_development")
        self.assertEqual(self._events()[-1]["event"], "mode_changed")

    def test_malformed_state_refuses_without_mutation(self):
        variants = [
            {"schema_version": 2, "mode": "finite_program", "goals": "bad"},
            {"schema_version": 2, "mode": "finite_program", "plan_id": "", "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "pending"}]},
            {"schema_version": 2, "mode": "finite_program", "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "invented"}]},
            {"schema_version": 2, "mode": "finite_program", "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "complete",
                 "evidence": None}]},
            {"schema_version": 2, "mode": "finite_program", "closed": True, "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "pending"}]},
            {"schema_version": 2, "mode": "continuous_development", "closed": True,
             "terminal_predicate": "owner stops", "closure_kind": "explicit_close",
             "closure": {"terminal_predicate": "owner stops", "evidence": "receipt",
                         "verify_cmd": "pytest", "verify_evidence": "green",
                         "authorization_source": None},
             "goals": [{"id": "G001", "title": "a", "objective": "b",
                        "status": "complete", "evidence": "done"}]},
            {"schema_version": 2, "mode": "finite_program", "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "pending"},
                {"id": "G001", "title": "c", "objective": "d", "status": "pending"}]},
            {"schema_version": 2, "mode": "finite_program", "goals": [
                {"id": "G001", "title": "a", "objective": "b", "status": "in_progress"},
                {"id": "G002", "title": "c", "objective": "d", "status": "in_progress"}]},
            {"schema_version": 2, "mode": "finite_program", "goals": [
                {"id": "not-an-id", "title": "a", "objective": "b", "status": "pending"}]},
        ]
        for bad in variants:
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as cwd:
                defaults = {"plan_id": "bad", "brief": "bad", "created": "now",
                            "terminal_predicate": "done", "release_intent": "none",
                            "next_goal_id": None, "next_action": None, "closed": False}
                for key, value in defaults.items():
                    bad.setdefault(key, value)
                state = Path(cwd) / ".rigor"
                state.mkdir()
                path = state / "goals.json"
                path.write_text(json.dumps(bad), encoding="utf-8")
                before = path.read_bytes()
                r = run(cwd, "status")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("invalid plan state", (r.stderr + r.stdout).lower())
                self.assertEqual(path.read_bytes(), before)

        with tempfile.TemporaryDirectory() as cwd:
            state = Path(cwd) / ".rigor"
            state.mkdir()
            path = state / "goals.json"
            path.write_text("[]", encoding="utf-8")
            r = run(cwd, "status")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("root must be an object", (r.stderr + r.stdout).lower())

    def test_force_replacing_active_continuing_plan_requires_and_logs_authorization(self):
        run(self.cwd, "create", "--brief", "continue", "--mode", "continuous_development",
            "--terminal", "owner stops", "--goal", "one::work")
        old = self._plan()
        state_before = (Path(self.cwd) / ".rigor" / "goals.json").read_bytes()
        ledger_before = (Path(self.cwd) / ".rigor" / "ledger.jsonl").read_bytes()
        r = run(self.cwd, "create", "--brief", "replacement", "--force",
                "--goal", "new::work")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((Path(self.cwd) / ".rigor" / "goals.json").read_bytes(), state_before)
        self.assertEqual((Path(self.cwd) / ".rigor" / "ledger.jsonl").read_bytes(), ledger_before)
        r = run(self.cwd, "create", "--brief", "replacement", "--force",
                "--authorization-source", "owner replaced engagement 2026-07-31",
                "--goal", "new::work")
        self.assertEqual(r.returncode, 0, r.stderr)
        event = [item for item in self._events() if item["event"] == "plan_replaced"][-1]
        self.assertEqual(event["old_plan_id"], old["plan_id"])
        self.assertEqual(event["new_plan_id"], self._plan()["plan_id"])

    def test_existing_mutation_lock_refuses_without_lost_update(self):
        self._create_two()
        state = Path(self.cwd) / ".rigor"
        goals_before = (state / "goals.json").read_bytes()
        ledger_before = (state / "ledger.jsonl").read_bytes()
        (state / "mutation.lock").write_text("simulated concurrent process", encoding="utf-8")
        r = run(self.cwd, "add", "--goal", "three::work",
                "--authorization-source", "accepted backlog")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("another rigor-goals process", (r.stderr + r.stdout).lower())
        self.assertEqual((state / "goals.json").read_bytes(), goals_before)
        self.assertEqual((state / "ledger.jsonl").read_bytes(), ledger_before)

    def test_force_replacement_of_malformed_state_refuses_without_traceback(self):
        state = Path(self.cwd) / ".rigor"
        state.mkdir()
        path = state / "goals.json"
        path.write_text('{"schema_version":2,"mode":"finite_program","goals":"bad"}',
                        encoding="utf-8")
        before = path.read_bytes()
        r = run(self.cwd, "create", "--brief", "replacement", "--force",
                "--goal", "one::work")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid plan state", (r.stderr + r.stdout).lower())
        self.assertNotIn("traceback", (r.stderr + r.stdout).lower())
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
