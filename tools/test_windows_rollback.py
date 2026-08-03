#!/usr/bin/env python3
"""Exercise documented PowerShell removal followed by the pinned v0.5.1 installer."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLLBACK_SHA = "d3d4592b12e689140d589b09d10c2bec63658b60"


def powershell(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            *arguments,
        ],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def ps_literal(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


@unittest.skipUnless(os.name == "nt", "PowerShell rollback coverage runs on Windows")
class WindowsRollbackTests(unittest.TestCase):
    def test_current_removal_then_pinned_v051_install_is_clean(self):
        with tempfile.TemporaryDirectory(prefix="rigor-windows-rollback-") as raw:
            fixture = Path(raw)
            project = fixture / "project"
            rollback_source = fixture / "v0.5.1"
            project.mkdir()
            rollback_source.mkdir()

            current_install = powershell(
                "-File",
                str(ROOT / "install.ps1"),
                "-Target",
                ".claude\\skills",
                cwd=project,
            )
            self.assertEqual(
                current_install.returncode,
                0,
                msg=f"current install failed\n{current_install.stdout}\n{current_install.stderr}",
            )

            target = project / ".claude" / "skills"
            goals = project / ".claude" / "tools" / "rigor_goals.py"
            anchor = project / "CLAUDE.md"
            owner_files = {
                target / "owner-sentinel" / "keep.txt": b"OWNER_SKILL_SENTINEL\n",
                project / ".claude" / "tools" / "owner-tool.txt": b"OWNER_TOOL_SENTINEL\n",
                project / ".rigor" / "keep.txt": b"OWNER_RIGOR_SENTINEL\n",
            }
            for path, content in owner_files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            anchor.write_text(
                "OWNER_BEFORE\n" + anchor.read_text(encoding="utf-8") + "OWNER_AFTER\n",
                encoding="utf-8",
                newline="\n",
            )

            manual = (ROOT / "docs" / "manual.md").read_text(encoding="utf-8")
            match = re.search(
                r"(?ms)^#### PowerShell removal\s+.*?^```powershell\r?\n(?P<body>.*?)^```\s*$",
                manual,
            )
            self.assertIsNotNone(match, "documented PowerShell removal block not found")
            removal = match.group("body")
            replacements = {
                '$Target = ".claude\\skills"': f"$Target = {ps_literal(target)}",
                '$GoalsFile = ".claude\\tools\\rigor_goals.py"': (
                    f"$GoalsFile = {ps_literal(goals)}"
                ),
                '$AnchorFile = "CLAUDE.md"': f"$AnchorFile = {ps_literal(anchor)}",
                '$confirmation = Read-Host "Type REMOVE 19 to continue"': (
                    '$confirmation = "REMOVE 19"'
                ),
            }
            for old, new in replacements.items():
                self.assertEqual(removal.count(old), 1, f"expected one removal line: {old}")
                removal = removal.replace(old, new, 1)
            removal_path = fixture / "documented-removal.ps1"
            removal_path.write_text(removal, encoding="utf-8", newline="\n")

            removed = powershell("-File", str(removal_path), cwd=ROOT)
            self.assertEqual(
                removed.returncode,
                0,
                msg=f"documented removal failed\n{removed.stdout}\n{removed.stderr}",
            )
            current_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
            remaining = [name for name in current_manifest["skills"] if (target / name).exists()]
            self.assertEqual(remaining, [])
            self.assertFalse(goals.exists())
            self.assertEqual(anchor.read_text(encoding="utf-8"), "OWNER_BEFORE\nOWNER_AFTER\n")
            for path, content in owner_files.items():
                self.assertEqual(path.read_bytes(), content)

            resolved = subprocess.run(
                ["git", "rev-parse", "v0.5.1^{commit}"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(resolved.stdout.strip(), ROLLBACK_SHA)
            archive = fixture / "v0.5.1.zip"
            archived = subprocess.run(
                ["git", "archive", "--format=zip", f"--output={archive}", ROLLBACK_SHA],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(archived.returncode, 0, archived.stderr)
            with zipfile.ZipFile(archive) as source_zip:
                source_zip.extractall(rollback_source)

            rollback_install = powershell(
                "-File",
                str(rollback_source / "install.ps1"),
                "-Target",
                ".claude\\skills",
                cwd=project,
            )
            self.assertEqual(
                rollback_install.returncode,
                0,
                msg=f"rollback install failed\n{rollback_install.stdout}\n{rollback_install.stderr}",
            )
            rollback_manifest = json.loads(
                (rollback_source / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(rollback_manifest["version"], "0.5.1")
            self.assertEqual(rollback_manifest["skill_count"], len(rollback_manifest["skills"]))
            self.assertEqual(
                [name for name in rollback_manifest["skills"] if not (target / name).is_dir()],
                [],
            )
            self.assertFalse((target / "dev-rigor-stack-lite-brainstorm").exists())
            self.assertTrue(goals.is_file())
            for path, content in owner_files.items():
                self.assertEqual(path.read_bytes(), content)
            rollback_anchor = anchor.read_text(encoding="utf-8-sig")
            self.assertIn("OWNER_BEFORE", rollback_anchor)
            self.assertIn("OWNER_AFTER", rollback_anchor)
            self.assertEqual(rollback_anchor.count("<!-- dev-rigor-lite anchor"), 1)
            self.assertEqual(rollback_anchor.count("<!-- /dev-rigor-lite anchor -->"), 1)

            print(
                "WINDOWS_ROLLBACK_V0.6.0_ONLY_SKILL_ABSENT=True "
                f"source_sha={ROLLBACK_SHA} owner_content_preserved=True anchor_pairs=1"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
