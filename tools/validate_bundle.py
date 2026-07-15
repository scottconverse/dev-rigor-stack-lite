#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
expected = set(manifest["skills"])
actual = {path.name for path in SKILLS.iterdir() if path.is_dir()}
errors = []

if manifest.get("hooks") is not False:
    errors.append("manifest must declare hooks=false")
if actual != expected:
    errors.append(f"skill inventory mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
if manifest.get("skill_count") != len(expected):
    errors.append("skill_count does not match manifest inventory")

for name in sorted(expected):
    skill_file = SKILLS / name / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"{name}: missing SKILL.md")
        continue
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append(f"{name}: invalid YAML frontmatter boundary")
        continue
    frontmatter = match.group(1)
    found_name = re.search(r"(?m)^name:\s*([^\n]+)$", frontmatter)
    if not found_name or found_name.group(1).strip(' \"\'') != name:
        errors.append(f"{name}: frontmatter name does not match directory")
    if not re.search(r"(?m)^description:\s*(?:>|[^\s].*)$", frontmatter):
        errors.append(f"{name}: missing description")
    forbidden = ["DevRigorSTATUS", "DevRigorREPAIR", "evidence-v4-", "hooks.json"]
    for term in forbidden:
        if term in text:
            errors.append(f"{name}: hook-only term remains: {term}")

if errors:
    print("BUNDLE_INVALID")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"BUNDLE_VALID: {len(expected)} skills, hook-free manifest, matching frontmatter")
