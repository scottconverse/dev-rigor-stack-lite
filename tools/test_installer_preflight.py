#!/usr/bin/env python3
"""Cross-platform regression tests for mutation-free installer refusal."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- dev-rigor-lite anchor"
END = "<!-- /dev-rigor-lite anchor -->"
LEGACY_BEGIN_V2 = (
    "<!-- dev-rigor-lite anchor v2 — managed block, do not hand-edit "
    "(edits go outside the markers; the installer replaces this block on upgrade) -->"
)


def link_target(path: Path) -> Path:
    """Use Windows' extended spelling so alias checks cover runner-created links."""
    if os.name == "nt":
        return Path("\\\\?\\" + str(path))
    return path


def snapshot(root: Path) -> dict[str, tuple[str, str]]:
    """Return a byte-sensitive inventory that also records empty directories."""
    result: dict[str, tuple[str, str]] = {}
    if not root.exists():
        return result
    for path in sorted((root, *root.rglob("*")), key=lambda item: item.as_posix()):
        relative = "." if path == root else path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("link", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("dir", "")
        else:
            result[relative] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result


def copy_installer_source(destination: Path) -> None:
    destination.mkdir()
    shutil.copy2(ROOT / "install.ps1", destination / "install.ps1")
    shutil.copy2(ROOT / "install.sh", destination / "install.sh")
    shutil.copytree(ROOT / "skills", destination / "skills")
    shutil.copytree(ROOT / "anchor", destination / "anchor")
    (destination / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "rigor_goals.py", destination / "tools" / "rigor_goals.py")


class InstallerPreflightTests(unittest.TestCase):
    def run_installer(
        self,
        source: Path,
        project: Path,
        target: str = ".claude/skills",
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        if os.name == "nt":
            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(source / "install.ps1"),
                "-Target",
                target.replace("/", "\\"),
                *extra,
            ]
        else:
            command = ["sh", str(source / "install.sh"), target, *extra]
        return subprocess.run(
            command,
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def assert_refusal_is_mutation_free(
        self,
        source: Path,
        project: Path,
        observed_root: Path,
        target: str = ".claude/skills",
        *extra: str,
    ) -> None:
        before = snapshot(observed_root)
        result = self.run_installer(source, project, target, *extra)
        self.assertNotEqual(
            result.returncode,
            0,
            msg=f"installer unexpectedly succeeded\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertEqual(
            snapshot(observed_root),
            before,
            msg=(
                "refused installer mutated the fixture\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            ),
        )

    def test_no_force_collision_is_preflighted_before_copy(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-collision-") as raw:
            project = Path(raw)
            owner = project / ".claude" / "skills" / "visitor-audit-lite" / "owner.txt"
            owner.parent.mkdir(parents=True)
            owner.write_text("OWNER\n", encoding="utf-8")
            self.assert_refusal_is_mutation_free(ROOT, project, project)

    def test_force_replaces_dangling_skill_link_without_partial_install(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-dangling-skill-") as raw:
            project = Path(raw)
            initial = self.run_installer(ROOT, project)
            self.assertEqual(
                initial.returncode,
                0,
                msg=f"initial install failed\n{initial.stdout}\n{initial.stderr}",
            )

            target = project / ".claude" / "skills"
            earlier = target / "audit-team-lite" / "SKILL.md"
            earlier.write_bytes(earlier.read_bytes() + b"OWNER_MUTATION\n")
            dangling = target / "dev-rigor-stack-lite-brainstorm"
            shutil.rmtree(dangling)
            try:
                dangling.symlink_to(
                    link_target(project / "missing-skill-target"),
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(f"directory links unavailable: {error}")

            force = "-Force" if os.name == "nt" else "--force"
            repaired = self.run_installer(ROOT, project, ".claude/skills", force)
            self.assertEqual(
                repaired.returncode,
                0,
                msg=(
                    "forced repair failed or stopped after partial replacement\n"
                    f"stdout:\n{repaired.stdout}\nstderr:\n{repaired.stderr}"
                ),
            )
            self.assertFalse(dangling.is_symlink())

            manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
            for name in manifest["skills"]:
                with self.subTest(skill=name):
                    installed = target / name
                    self.assertTrue(installed.is_dir())
                    self.assertFalse(installed.is_symlink())
                    self.assertEqual(snapshot(installed), snapshot(ROOT / "skills" / name))

    def test_force_replaces_linked_skill_without_touching_link_target(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-linked-skill-") as raw:
            project = Path(raw)
            owner = project / "owner-skill"
            owner.mkdir()
            (owner / "owner.txt").write_text("OWNER\n", encoding="utf-8")
            destination = (
                project / ".claude" / "skills" / "dev-rigor-stack-lite-brainstorm"
            )
            destination.parent.mkdir(parents=True)
            try:
                destination.symlink_to(link_target(owner), target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory links unavailable: {error}")
            owner_before = snapshot(owner)
            force = "-Force" if os.name == "nt" else "--force"
            result = self.run_installer(ROOT, project, ".claude/skills", force)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"forced install failed\n{result.stdout}\n{result.stderr}",
            )
            self.assertEqual(snapshot(owner), owner_before)
            self.assertFalse(destination.is_symlink())
            self.assertEqual(
                snapshot(destination),
                snapshot(ROOT / "skills" / "dev-rigor-stack-lite-brainstorm"),
            )

    def test_malformed_anchor_is_preflighted_before_copy(self):
        for label, text in (
            ("begin-only", f"OWNER\n{BEGIN}\n"),
            ("end-only", f"OWNER\n{END}\n"),
            ("out-of-order", f"{END}\n{BEGIN}\n"),
            ("duplicate", f"{BEGIN}\n{END}\n{BEGIN}\n{END}\n"),
            ("inline-owner-text", f"OWNER {BEGIN}\n{END} OWNER\n"),
        ):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(prefix=f"rigor-installer-{label}-") as raw:
                    project = Path(raw)
                    (project / "CLAUDE.md").write_text(text, encoding="utf-8")
                    self.assert_refusal_is_mutation_free(ROOT, project, project)

    def test_legacy_v2_anchor_is_replaced_without_losing_owner_text(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-legacy-anchor-") as raw:
            project = Path(raw)
            current = (ROOT / "anchor" / "anchor.md").read_text(encoding="utf-8")
            current_begin = current.splitlines()[0]
            legacy = current.replace(current_begin, LEGACY_BEGIN_V2, 1)
            anchor = project / "CLAUDE.md"
            anchor.write_text(
                "OWNER_BEFORE\n" + legacy + "OWNER_AFTER\n",
                encoding="utf-8",
                newline="\n",
            )
            result = self.run_installer(ROOT, project)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"legacy upgrade failed\n{result.stdout}\n{result.stderr}",
            )
            upgraded = anchor.read_text(encoding="utf-8-sig")
            self.assertIn(current_begin, upgraded)
            self.assertNotIn(LEGACY_BEGIN_V2, upgraded)
            self.assertTrue(upgraded.startswith("OWNER_BEFORE\n"))
            self.assertTrue(upgraded.endswith("OWNER_AFTER\n"))

    def test_target_cannot_alias_bundled_skill_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-source-alias-") as raw:
            source = Path(raw) / "source"
            copy_installer_source(source)
            force = "-Force" if os.name == "nt" else "--force"
            self.assert_refusal_is_mutation_free(
                source,
                source,
                source,
                "skills",
                force,
            )

    def test_case_variant_target_cannot_alias_bundled_skill_source(self):
        with tempfile.TemporaryDirectory(
            prefix="rigor-installer-case-alias-", dir=ROOT.parent
        ) as raw:
            source = Path(raw) / "source"
            copy_installer_source(source)
            alternate_target = source / "SKILLS"
            try:
                if not os.path.samefile(alternate_target, source / "skills"):
                    self.skipTest("fixture filesystem is case-sensitive")
            except FileNotFoundError:
                self.skipTest("fixture filesystem is case-sensitive")
            force = "-Force" if os.name == "nt" else "--force"
            no_goals = "-NoGoals" if os.name == "nt" else "--no-goals"
            no_anchor = "-NoAnchor" if os.name == "nt" else "--no-anchor"
            self.assert_refusal_is_mutation_free(
                source,
                source,
                source,
                str(alternate_target),
                force,
                no_goals,
                no_anchor,
            )

    def test_goals_and_anchor_output_collision_is_preflighted(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-output-alias-") as raw:
            project = Path(raw)
            options = (
                ("-Goals", ".claude\\tools", "-Anchor", ".claude\\tools\\rigor_goals.py")
                if os.name == "nt"
                else ("--goals", ".claude/tools", "--anchor", ".claude/tools/rigor_goals.py")
            )
            self.assert_refusal_is_mutation_free(
                ROOT, project, project, ".claude/skills", *options
            )

    def test_dot_segments_cannot_bypass_output_topology(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-dot-segments-") as raw:
            project = Path(raw)
            options = (
                (
                    "-Goals", ".claude\\tools", "-Anchor",
                    ".claude\\missing\\..\\tools\\rigor_goals.py",
                )
                if os.name == "nt"
                else (
                    "--goals", ".claude/tools", "--anchor",
                    ".claude/missing/../tools/rigor_goals.py",
                )
            )
            self.assert_refusal_is_mutation_free(
                ROOT, project, project, ".claude/skills", *options
            )

    def test_companion_outputs_cannot_be_inside_skills_target(self):
        cases = (
            (
                "goals",
                ("-Goals", ".claude\\skills\\tools")
                if os.name == "nt"
                else ("--goals", ".claude/skills/tools"),
            ),
            (
                "anchor",
                ("-Anchor", ".claude\\skills\\AGENTS.md")
                if os.name == "nt"
                else ("--anchor", ".claude/skills/AGENTS.md"),
            ),
        )
        for label, options in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(
                    prefix=f"rigor-installer-{label}-inside-target-"
                ) as raw:
                    project = Path(raw)
                    self.assert_refusal_is_mutation_free(
                        ROOT, project, project, ".claude/skills", *options
                    )

    def test_missing_anchor_parent_is_created_before_component_copy(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-anchor-parent-") as raw:
            project = Path(raw)
            options = (
                ("-Anchor", "nested\\host\\AGENTS.md")
                if os.name == "nt"
                else ("--anchor", "nested/host/AGENTS.md")
            )
            result = self.run_installer(ROOT, project, ".claude/skills", *options)
            self.assertEqual(
                result.returncode,
                0,
                msg=f"install failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
            self.assertTrue((project / "nested" / "host" / "AGENTS.md").is_file())
            self.assertEqual(
                len([path for path in (project / ".claude" / "skills").iterdir() if path.is_dir()]),
                20,
            )

    def test_blocked_companion_parent_chain_is_preflighted(self):
        cases = (
            (
                "goals",
                ("-Goals", "blocked\\tools")
                if os.name == "nt"
                else ("--goals", "blocked/tools"),
            ),
            (
                "anchor",
                ("-Anchor", "blocked\\host\\AGENTS.md")
                if os.name == "nt"
                else ("--anchor", "blocked/host/AGENTS.md"),
            ),
        )
        for label, options in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(
                    prefix=f"rigor-installer-blocked-{label}-parent-"
                ) as raw:
                    project = Path(raw)
                    (project / "blocked").write_text("OWNER\n", encoding="utf-8")
                    self.assert_refusal_is_mutation_free(
                        ROOT, project, project, ".claude/skills", *options
                    )

    def test_target_link_cannot_alias_bundled_skill_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-linked-source-") as raw:
            fixture = Path(raw)
            source = fixture / "source"
            project = fixture / "project"
            copy_installer_source(source)
            (project / ".claude").mkdir(parents=True)
            linked_target = project / ".claude" / "skills"
            try:
                linked_target.symlink_to(
                    link_target(source / "skills"), target_is_directory=True
                )
            except OSError as error:
                self.skipTest(f"directory links unavailable: {error}")
            force = "-Force" if os.name == "nt" else "--force"
            self.assert_refusal_is_mutation_free(
                source,
                project,
                fixture,
                ".claude/skills",
                force,
            )

    def test_goals_destination_cannot_alias_bundled_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-goals-alias-") as raw:
            source = Path(raw) / "source"
            copy_installer_source(source)
            options = ("-Goals", "tools") if os.name == "nt" else ("--goals", "tools")
            self.assert_refusal_is_mutation_free(
                source,
                source,
                source,
                ".claude/skills",
                *options,
            )

    def test_linked_goals_directory_cannot_alias_bundled_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-linked-goals-") as raw:
            fixture = Path(raw)
            source = fixture / "source"
            project = fixture / "project"
            copy_installer_source(source)
            (project / ".claude").mkdir(parents=True)
            linked_tools = project / ".claude" / "tools"
            try:
                linked_tools.symlink_to(
                    link_target(source / "tools"), target_is_directory=True
                )
            except OSError as error:
                self.skipTest(f"directory links unavailable: {error}")
            self.assert_refusal_is_mutation_free(source, project, fixture)

    def test_linked_companion_files_cannot_redirect_owner_writes(self):
        cases = ("goals", "anchor")
        for label in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(
                    prefix=f"rigor-installer-linked-{label}-owner-"
                ) as raw:
                    project = Path(raw)
                    owner = project / "owner" / f"{label}.txt"
                    owner.parent.mkdir()
                    owner.write_text("OWNER\n", encoding="utf-8")
                    if label == "goals":
                        linked = project / ".claude" / "tools" / "rigor_goals.py"
                        linked.parent.mkdir(parents=True)
                    else:
                        linked = project / "CLAUDE.md"
                    try:
                        linked.symlink_to(link_target(owner))
                    except OSError as error:
                        self.skipTest(f"file links unavailable: {error}")
                    self.assert_refusal_is_mutation_free(ROOT, project, project)

    def test_anchor_destination_cannot_alias_bundled_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-anchor-alias-") as raw:
            source = Path(raw) / "source"
            copy_installer_source(source)
            options = (
                ("-Anchor", "anchor\\anchor.md")
                if os.name == "nt"
                else ("--anchor", "anchor/anchor.md")
            )
            self.assert_refusal_is_mutation_free(
                source,
                source,
                source,
                ".claude/skills",
                *options,
            )

    def test_linked_anchor_cannot_alias_bundled_source(self):
        with tempfile.TemporaryDirectory(prefix="rigor-installer-linked-anchor-") as raw:
            fixture = Path(raw)
            source = fixture / "source"
            project = fixture / "project"
            copy_installer_source(source)
            project.mkdir()
            try:
                (project / "CLAUDE.md").symlink_to(
                    link_target(source / "anchor" / "anchor.md")
                )
            except OSError as error:
                self.skipTest(f"file links unavailable: {error}")
            self.assert_refusal_is_mutation_free(source, project, fixture)


if __name__ == "__main__":
    unittest.main(verbosity=2)
