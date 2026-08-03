#!/usr/bin/env python3
"""Cross-platform regression tests for mutation-free installer refusal."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- dev-rigor-lite anchor"
END = "<!-- /dev-rigor-lite anchor -->"


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
