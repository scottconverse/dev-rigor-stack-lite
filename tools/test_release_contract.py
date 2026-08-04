#!/usr/bin/env python3
"""Executable contract checks for the dev-rigor-stack-lite 0.7.0 release."""

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def tree_snapshot(root: Path) -> dict[str, tuple[str, str]]:
    result = {}
    for path in sorted((root, *root.rglob("*")), key=lambda item: item.as_posix()):
        relative = "." if path == root else path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("link", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("dir", "")
        else:
            result[relative] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result


def copy_removal_fixture_source(destination: Path) -> None:
    destination.mkdir()
    for name in ("install.ps1", "install.sh", "manifest.json"):
        shutil.copy2(ROOT / name, destination / name)
    shutil.copytree(ROOT / "skills", destination / "skills")
    shutil.copytree(ROOT / "anchor", destination / "anchor")
    (destination / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "rigor_goals.py", destination / "tools" / "rigor_goals.py")


class ReleaseContractTests(unittest.TestCase):
    def test_manifest_declares_0_7_0_and_twenty_skills(self):
        self.assertEqual(MANIFEST["version"], "0.7.0")
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

    def test_gauntlet_mutation_isolation_has_contract(self):
        full_lane = (
            ROOT / "skills" / "gauntletgate-lite" / "lanes" / "full.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "live-mutating the product's source",
            "isolated worktree/copy",
            "never the shared clone",
            "live-mutation roles need their own copy",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, full_lane)

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

        coordinator = (ROOT / "skills" / "dev-rigor-stack-lite" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("When BRAINSTORM was not explicitly invoked", coordinator)
        self.assertIn("When BRAINSTORM produces a material design", coordinator)

    def test_maintainer_commands_include_release_contract_suite(self):
        commands_by_file = {
            "CONTRIBUTING.md": (
                "python tools/test_release_contract.py",
                "python tools/test_installer_preflight.py",
            ),
            "docs/manual.md": (
                "python3 tools/test_release_contract.py",
                "python3 tools/test_installer_preflight.py",
            ),
        }
        for relative, commands in commands_by_file.items():
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
        self.assertIn("function Visit-Tree", removal)
        self.assertNotIn(".Substring($base.Length)", removal)

    def test_documented_bash_removal_inventory_includes_directories(self):
        manual = (ROOT / "docs" / "manual.md").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^#### Bash removal\s+.*?^```sh\r?\n(?P<body>.*?)^```\s*$",
            manual,
        )
        self.assertIsNotNone(match)
        removal = match.group("body")
        self.assertIn('result.append(("DIR", relative))', removal)
        self.assertIn('result.append(("FILE", relative, digest(member)))', removal)

    def test_documented_bash_removal_refuses_empty_directory_drift_without_mutation(self):
        manual = (ROOT / "docs" / "manual.md").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^#### Bash removal\s+.*?^```sh\r?\n(?P<body>.*?)^```\s*$",
            manual,
        )
        self.assertIsNotNone(match)
        python_bodies = re.findall(
            r"(?ms)^python3 - <<'PY'\r?\n(.*?)^PY\s*$", match.group("body")
        )
        self.assertEqual(len(python_bodies), 2)
        removal = python_bodies[1]

        for drift in ("extra", "missing"):
            with self.subTest(drift=drift):
                with tempfile.TemporaryDirectory(prefix=f"rigor-removal-{drift}-dir-") as raw:
                    fixture = Path(raw)
                    project = fixture / "project"
                    project.mkdir()
                    source = ROOT
                    empty_relative = Path(MANIFEST["skills"][0]) / "empty-contract-dir"
                    if drift == "missing":
                        source = fixture / "source"
                        copy_removal_fixture_source(source)
                        (source / "skills" / empty_relative).mkdir()

                    if os.name == "nt":
                        command = [
                            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(source / "install.ps1"), "-Target", ".claude\\skills",
                        ]
                    else:
                        command = ["sh", str(source / "install.sh"), ".claude/skills"]
                    installed = subprocess.run(
                        command, cwd=project, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                    )
                    self.assertEqual(
                        installed.returncode, 0,
                        msg=f"fixture install failed\n{installed.stdout}\n{installed.stderr}",
                    )

                    installed_empty = project / ".claude" / "skills" / empty_relative
                    if drift == "extra":
                        installed_empty.mkdir()
                    else:
                        installed_empty.rmdir()
                    before = tree_snapshot(project)
                    environment = os.environ.copy()
                    environment.update(
                        ROOT=str(source),
                        TARGET=str(project / ".claude" / "skills"),
                        GOALS_FILE=str(project / ".claude" / "tools" / "rigor_goals.py"),
                        ANCHOR_FILE=str(project / "CLAUDE.md"),
                        CONFIRMATION="REMOVE 19",
                    )
                    refused = subprocess.run(
                        [sys.executable, "-c", removal], cwd=source, env=environment,
                        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                    )
                    self.assertNotEqual(refused.returncode, 0)
                    self.assertIn("installed skill differs from pinned source", refused.stderr)
                    self.assertEqual(tree_snapshot(project), before)

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

    def test_notice_carries_complete_fivetaku_license_and_source_identity(self):
        notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        for phrase in (
            "e221f32b16f7b0ef39393ba47c37cb8345ffe749",
            "a8ea7996c320f9bf09759073ba832aa609e370ea",
            "Copyright (c) 2026 fivetaku",
            "The above copyright notice and this permission notice shall be included",
            "THE SOFTWARE IS PROVIDED \"AS IS\"",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, notice)

    def test_external_github_actions_are_immutable_and_least_privilege(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        external_uses = re.findall(r"(?m)^\s*uses:\s+(.+?)\s*$", workflow)
        self.assertTrue(external_uses)
        for use in external_uses:
            if use.startswith("./"):
                continue
            with self.subTest(use=use):
                self.assertRegex(use, r"^[^@]+@[0-9a-f]{40}\s+#\s+v\d+$")
        self.assertRegex(workflow, r"(?m)^permissions:\s*\n\s+contents:\s+read\s*$")
        self.assertEqual(workflow.count("persist-credentials: false"), 2)

    def test_current_public_version_and_count_are_not_stale(self):
        authoritative_markers = {
            "README.md": (
                "for 20 skills total",
                "git clone --branch v0.7.0",
            ),
            "docs/manual.md": (
                "owns the 20-skill",
                "git checkout --detach v0.7.0",
            ),
            "docs/index.html": (
                '<span class="v">v0.7.0</span>',
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

    def test_landing_install_journey_targets_the_owner_project(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn('$Installer = (Resolve-Path', text)
        self.assertIn('INSTALLER=$(cd dev-rigor-stack-lite', text)
        self.assertIn('Set-Location <span class="s">"C:\\path\\to\\your-project"</span>', text)
        self.assertIn('<span class="k">cd</span> /path/to/your-project', text)
        self.assertIn('.claude\\tools\\rigor_goals.py create', text)
        self.assertIn('.claude/tools/rigor_goals.py create', text)
        self.assertNotIn('python3</span> tools/rigor_goals.py', text)

    def test_landing_overflow_and_fragment_targets_are_keyboard_operable(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<main id="main" tabindex="-1">', text)
        self.assertIn('class="gate-row" tabindex="0" aria-label=', text)
        self.assertIn('class="tbl-wrap" tabindex="0" aria-label=', text)
        self.assertIn("pre.tabIndex=0", text)
        self.assertIn("region.scrollLeft+=48", text)
        self.assertIn("copy.className='copy-btn'", text)
        self.assertIn("target.focus({preventScroll:true})", text)
        self.assertIn("window.addEventListener('hashchange'", text)
        self.assertIn(".catch(fallback)", text)
        self.assertIn(".lanes,.limits{grid-template-columns:minmax(0,1fr)}", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
