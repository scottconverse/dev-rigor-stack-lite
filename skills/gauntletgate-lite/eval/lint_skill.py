#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Structural lint for the GauntletGate skill — a cheap conformance check.

Verifies the contract between the skill files so an edit can't silently break it:
- SKILL.md exists and has YAML frontmatter with `name: gauntletgate-lite`.
- The three lanes and the three references exist.
- Every `lanes/...md` / `references/...md` path SKILL.md points at actually exists.

stdlib only. Exit 0 = the skill structure is intact.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT

REQUIRED = [
    "SKILL.md",
    "lanes/lite.md",
    "lanes/walkthrough.md",
    "lanes/full.md",
    "references/shared-backbone.md",
    "references/gate-verdict.md",
    "references/report-template.md",
]


def main() -> int:
    errs: list[str] = []

    for rel in REQUIRED:
        if not (SKILL_DIR / rel).is_file():
            errs.append(f"missing required file: {rel}")

    skill_md = SKILL_DIR / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errs.append("SKILL.md has no YAML frontmatter")
        if not re.search(r"^name:\s*gauntletgate-lite\s*$", text, re.MULTILINE):
            errs.append("SKILL.md frontmatter is missing `name: gauntletgate-lite`")
        # Every lanes/ or references/ path mentioned must exist.
        for ref in re.findall(r"`?((?:lanes|references)/[A-Za-z0-9_.-]+\.md)`?", text):
            if not (SKILL_DIR / ref).is_file():
                errs.append(f"SKILL.md references a missing file: {ref}")

    if errs:
        print("SKILL LINT FAILED:")
        for e in errs:
            print("  -", e)
        return 1
    print("SKILL LINT PASSED: structure intact, all referenced files present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
