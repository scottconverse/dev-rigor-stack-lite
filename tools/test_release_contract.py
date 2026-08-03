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
            "Never label a proposed revision approved or owner-approved before the owner gives that approval.",
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

    def test_release_preserves_frozen_removal_confirmation(self):
        expected_occurrences = {
            "docs/manual.md": 6,
            ".github/workflows/ci.yml": 8,
        }
        for relative, expected in expected_occurrences.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertEqual(text.count("REMOVE 19"), expected)
                self.assertNotIn("REMOVE ALL MANIFEST SKILLS", text)

    def test_public_brainstorm_copy_preserves_explicit_invocation_precedence(self):
        precedence = (
            "Explicit invocation always activates BRAINSTORM, even when the brief "
            "is decision-complete."
        )
        for relative in (
            "README.md",
            "CHANGELOG.md",
            "docs/architecture.md",
            "docs/index.html",
            "docs/manual.md",
        ):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(precedence, text)

    def test_maintainer_commands_include_release_contract_suite(self):
        commands = (
            "python tools/test_release_contract.py",
            "python tools/test_installer_preflight.py",
        )
        for relative in ("CONTRIBUTING.md", "docs/manual.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for command in commands:
                with self.subTest(path=relative, command=command):
                    self.assertIn(command, text)

    def test_ci_covers_successful_removal_and_clean_rollback(self):
        text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("SUCCESSFUL_REMOVAL_OWNER_CONTENT_PRESERVED=True", text)
        self.assertIn("python tools/test_windows_rollback.py", text)
        self.assertIn("rollback_v0.6.0_only_skill_absent=true", text)
        self.assertIn("d3d4592b12e689140d589b09d10c2bec63658b60", text)
        self.assertIn("python tools/test_installer_preflight.py", text)
        windows_rollback = (ROOT / "tools" / "test_windows_rollback.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("WINDOWS_ROLLBACK_V0.6.0_ONLY_SKILL_ABSENT=True", windows_rollback)

    def test_documented_windows_removal_has_no_cmdlet_autoload_dependency(self):
        manual = (ROOT / "docs" / "manual.md").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^#### PowerShell removal\s+.*?^```powershell\r?\n(?P<body>.*?)^```\s*$",
            manual,
        )
        self.assertIsNotNone(match)
        removal = match.group("body")
        self.assertIn("function Get-Sha256", removal)
        self.assertNotIn("Get-FileHash", removal)

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
        authoritative_markers = {
            "README.md": (
                "for 20 skills total",
                "git clone --branch v0.6.0",
            ),
            "docs/manual.md": (
                "owns the 20-skill",
                "git checkout --detach v0.6.0",
            ),
            "docs/index.html": (
                '<span class="v">v0.6.0</span>',
                "<h3>The 20 skills</h3>",
            ),
        }
        legacy_count = str(MANIFEST["skill_count"] - 1)
        for relative, markers in authoritative_markers.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                for marker in markers:
                    self.assertIn(marker, text)
                self.assertNotIn("all " + legacy_count + " skills", text)
                self.assertNotIn("exactly " + legacy_count + " skills", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
