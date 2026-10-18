#!/usr/bin/env python3
"""Drift guard between SKILL.md (canonical) and SKILL-LITE.md (derived).

Four assertions:
  1. MATCH    - every sync block present in both files is identical.
  2. PRESENCE - every block marked lite:required in SKILL.md exists in
                SKILL-LITE.md, and every block in SKILL-LITE.md still exists
                in SKILL.md (no orphans).
  3. COVERAGE - every numbered rule in SKILL.md's HARD RULES section carries a
                sync annotation (lite:required or lite:excluded). Adding a rule
                without deciding its lite fate is a failure, not an oversight.
  4. PINS     - SKILL-LITE.md contains the safety-critical phrases that have no
                synced counterpart (the escalation tripwire). They may be
                reworded but never deleted.

Usage: python check_sync.py [path/to/SKILL.md] [path/to/SKILL-LITE.md]
Exit 0 = in sync. Exit 1 = drift; each problem printed on stderr.
Stdlib only.
"""
import re
import sys
from pathlib import Path

PINS = [
    "untrusted input",
    "auth",
    "secrets",
    "deserialization",
    "load the full standards",
]

BLOCK = re.compile(
    r"<!--\s*sync:([\w-]+)(?:\s+lite:(required|excluded))?\s*-->\n(.*?)<!--\s*/sync:\1\s*-->",
    re.S,
)


def read(path):
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")


def parse_blocks(text, filename):
    found, spans = {}, []
    for m in BLOCK.finditer(text):
        name, flag, body = m.group(1), m.group(2), m.group(3).strip("\n")
        if name in found:
            sys.exit(f"FATAL: duplicate sync block '{name}' in {filename}")
        found[name] = (flag, body)
        spans.append(m.span())
    return found, spans


def main(argv):
    here = Path(__file__).resolve().parent.parent / "skills" / "coder-tdd-qa-lite"
    full_path = Path(argv[1]) if len(argv) > 1 else here / "SKILL.md"
    lite_path = Path(argv[2]) if len(argv) > 2 else here / "SKILL-LITE.md"
    full_text, lite_text = read(full_path), read(lite_path)
    full_blocks, full_spans = parse_blocks(full_text, full_path.name)
    lite_blocks, _ = parse_blocks(lite_text, lite_path.name)
    errors = []

    # 1. MATCH
    for name, (_, body) in lite_blocks.items():
        if name in full_blocks and full_blocks[name][1] != body:
            errors.append(f"DRIFT: sync block '{name}' differs between the two files")

    # 2. PRESENCE + orphans
    for name, (flag, _) in full_blocks.items():
        if flag == "required" and name not in lite_blocks:
            errors.append(
                f"MISSING: block '{name}' is lite:required but absent from {lite_path.name}"
            )
    for name in lite_blocks:
        if name not in full_blocks:
            errors.append(
                f"ORPHAN: block '{name}' exists in {lite_path.name} but not in {full_path.name}"
            )

    # 3. COVERAGE
    section = re.search(r"^## HARD RULES\n.*?(?=^## )", full_text, re.S | re.M)
    if not section:
        errors.append(f"COVERAGE: no '## HARD RULES' section found in {full_path.name}")
    else:
        for rule in re.finditer(
            r"^\d+\.\s+\*\*", full_text[section.start() : section.end()], re.M
        ):
            pos = section.start() + rule.start()
            if not any(a <= pos < b for a, b in full_spans):
                line = full_text.count("\n", 0, pos) + 1
                errors.append(
                    f"COVERAGE: rule at {full_path.name}:{line} has no sync annotation "
                    f"(wrap it and mark lite:required or lite:excluded)"
                )

    # 4. PINS
    lite_lower = lite_text.lower()
    for phrase in PINS:
        if phrase not in lite_lower:
            errors.append(
                f"PIN: safety-critical phrase '{phrase}' missing from {lite_path.name}"
            )

    if errors:
        print(f"check_sync: {len(errors)} problem(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(
        f"check_sync: OK - {len(full_blocks)} sync blocks in {full_path.name}, "
        f"{len(lite_blocks)} in {lite_path.name}; match, presence, coverage, "
        f"and {len(PINS)} pins all pass"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
