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
    # A description must have actual content: either inline text, or a block
    # scalar (>/|) followed by at least one non-empty indented line. A bare
    # 'description: >' passed the old check. (Gate finding, 0.2.1.)
    desc = re.search(r"(?m)^description:\s*(.*)$", frontmatter)
    desc_ok = False
    if desc:
        inline = desc.group(1).strip()
        if inline and inline not in (">", "|", ">-", "|-"):
            desc_ok = True
        else:
            after = frontmatter[desc.end():]
            desc_ok = bool(re.search(r"(?m)^[ \t]+\S", after))
    if not desc_ok:
        errors.append(f"{name}: missing or empty description")
    forbidden = ["DevRigorSTATUS", "DevRigorREPAIR", "evidence-v4-", "hooks.json"]
    for term in forbidden:
        if term in text:
            errors.append(f"{name}: hook-only term remains: {term}")
    # The hook-free claim covers EVERY file the installers copy, not just
    # SKILL.md: a hooks.json dropped anywhere in a skill dir would install
    # wholesale and still validate. Scan ALL files (any extension, any depth);
    # only the canonical top-level SKILL.md is exempt (already checked above).
    # (Gate findings, 0.2.1 + fix-wave review.)
    canonical = SKILLS / name / "SKILL.md"
    for member in sorted((SKILLS / name).rglob("*")):
        if not member.is_file() or member == canonical:
            continue
        if member.name in ("hooks.json", "settings.json", "settings.local.json"):
            errors.append(f"{name}: hook/config file must not ship in a skill dir: {member.relative_to(ROOT)}")
            continue
        body = member.read_text(encoding="utf-8", errors="replace")
        for term in forbidden:
            if term in body:
                errors.append(f"{name}: hook-only term in {member.relative_to(ROOT)}: {term}")

# --- version sync: every version label in skills/ must match the manifest ---
manifest_version = manifest.get("version", "")
if not manifest_version:
    errors.append("manifest: missing version")
for path in sorted(SKILLS.rglob("*.md")):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for found in re.findall(r"\bv(\d+\.\d+\.\d+)\b", line):
            if found != manifest_version:
                rel = path.relative_to(ROOT)
                errors.append(f"{rel}:{line_no}: version v{found} != manifest {manifest_version}")

# --- anchor block (Tier 2) ---
ANCHOR = ROOT / "anchor" / "anchor.md"
if not ANCHOR.is_file():
    errors.append("anchor/anchor.md missing")
else:
    anchor_text = ANCHOR.read_text(encoding="utf-8")
    if not anchor_text.startswith("<!-- dev-rigor-lite anchor"):
        errors.append("anchor: must start with the begin marker")
    if "<!-- /dev-rigor-lite anchor -->" not in anchor_text:
        errors.append("anchor: end marker missing")
    if "rigor-goals" not in anchor_text:
        errors.append("anchor: must reference the rigor-goals tool (Tier 3 entry point)")
    content_lines = [
        line for line in anchor_text.splitlines()
        if line.strip() and not line.lstrip().startswith("<!--")
    ]
    if len(content_lines) > 15:
        errors.append(f"anchor: {len(content_lines)} content lines — the cap is 15, keep it an anchor not an essay")

# --- rigor-goals tool (Tier 3) — the exit gate must actually refuse ---
GOALS_TOOL = ROOT / "tools" / "rigor_goals.py"
if not GOALS_TOOL.is_file():
    errors.append("tools/rigor_goals.py missing")
else:
    import subprocess
    import tempfile

    def goals(cwd, *args):
        return subprocess.run([sys.executable, str(GOALS_TOOL), *args],
                              cwd=cwd, capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        if goals(tmp, "create", "--brief", "validator smoke", "--goal", "only::story").returncode != 0:
            errors.append("rigor-goals: create failed in validator smoke")
        else:
            goals(tmp, "next")
            gate = goals(tmp, "checkpoint", "--id", "G001", "--status", "complete",
                         "--evidence", "smoke")
            if gate.returncode == 0:
                errors.append("rigor-goals: exit gate accepted a final story WITHOUT verify flags — the gate is broken")
            accepted = goals(tmp, "checkpoint", "--id", "G001", "--status", "complete",
                             "--evidence", "smoke", "--verify-cmd", "true", "--verify-evidence", "ok")
            if accepted.returncode != 0:
                errors.append("rigor-goals: exit gate refused a fully-evidenced completion")

if errors:
    print("BUNDLE_INVALID")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"BUNDLE_VALID: {len(expected)} skills, hook-free manifest, matching frontmatter, anchor ok, goals gate ok")
