#!/usr/bin/env python3
"""Executable contract checks for the dev-rigor-stack-lite 0.6.0 release."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


class ReleaseContractTests(unittest.TestCase):
    def test_manifest_declares_0_6_0_and_twenty_skills(self):
        self.assertEqual(MANIFEST["version"], "0.6.0")
        self.assertEqual(MANIFEST["skill_count"], 20)
        self.assertEqual(len(MANIFEST["skills"]), 20)
        self.assertIn("dev-rigor-stack-lite-brainstorm", MANIFEST["skills"])

    def test_brainstorm_contract_covers_activation_approval_and_handoff(self):
        path = ROOT / "skills" / "dev-rigor-stack-lite-brainstorm" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        required = (
            "Optional discovery",
            "Without explicit invocation",
            "Do not activate",
            "one material decision at a time",
            "Approve / Revise / Pause",
            "provisional lane",
            "$dev-rigor-stack-lite-plan",
            "goals and non-goals",
            "rejected alternatives",
            "assumptions and open questions",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_brainstorm_scenarios_cover_activate_skip_and_change_cases(self):
        path = (
            ROOT
            / "skills"
            / "dev-rigor-stack-lite-brainstorm"
            / "references"
            / "behavior-scenarios.md"
        )
        text = path.read_text(encoding="utf-8")
        for case_id in ("B-01", "B-02", "B-03", "B-04", "B-05", "B-06", "B-07"):
            with self.subTest(case_id=case_id):
                self.assertRegex(text, rf"(?m)^## {case_id}\b")

    def test_brainstorm_release_is_text_only(self):
        root = ROOT / "skills" / "dev-rigor-stack-lite-brainstorm"
        shipped = sorted(
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        )
        self.assertEqual(shipped, ["SKILL.md", "references/behavior-scenarios.md"])

    def test_debug_and_fanout_methods_are_present(self):
        coder = (ROOT / "skills" / "coder-tdd-qa-lite" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("nearest working equivalent", coder)
        self.assertIn("A third failed fix", coder)
        self.assertIn("a fourth is not", coder)
        orchestration = (
            ROOT / "skills" / "audit-team-lite" / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("same file or symbol", orchestration)
        self.assertIn("seeded random sample", orchestration)
        self.assertIn("sampled finding IDs", orchestration)

    def test_release_has_no_stale_numeric_removal_confirmation(self):
        legacy_count = str(20 - 1)
        candidates = [ROOT / "docs" / "manual.md", ROOT / ".github" / "workflows" / "ci.yml"]
        for path in candidates:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("REMOVE " + legacy_count, path.read_text(encoding="utf-8"))

    def test_ci_covers_successful_removal_and_clean_rollback(self):
        text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("SUCCESSFUL_REMOVAL_OWNER_CONTENT_PRESERVED=True", text)
        self.assertIn("rollback_v0.6.0_only_skill_absent=true", text)
        self.assertIn("d3d4592b12e689140d589b09d10c2bec63658b60", text)

    def test_portable_workflow_does_not_pin_a_worker_model(self):
        offenders = []
        for path in (ROOT / "skills").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if re.search(r"\bmodel\s*:\s*['\"]", text):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_notice_records_brainstorm_source_and_license(self):
        text = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("obra/superpowers", text)
        self.assertIn("1f20bef3f59b85ad7b52718f822e37c4478a3ff5", text)
        self.assertIn("Copyright (c) 2025 Jesse Vincent", text)

    def test_current_public_version_and_count_are_not_stale(self):
        legacy_count = str(20 - 1)
        for relative in ("README.md", "docs/manual.md", "docs/index.html"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertIn("0.6.0", text)
                self.assertNotIn("all " + legacy_count + " skills", text)
                self.assertNotIn("exactly " + legacy_count + " skills", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
