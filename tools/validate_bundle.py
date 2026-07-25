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

# GitHub compiles a run scalar containing ${{ ... }} into one format(...)
# expression, whose service-side ceiling is 21,000 characters. Keep a margin so
# ordinary edits cannot produce a candidate that only fails after it reaches CI.
RUN_EXPRESSION_LIMIT = 20_000
OPEN_EXPRESSION = "${{"


def utf16_code_units(value):
    """Return .NET-style UTF-16 String.Length for a Python string."""
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def split_github_template(raw):
    """Mirror GitHub's literal/expression segmentation for a scalar."""
    segments = []
    cursor = 0
    while True:
        start = raw.find(OPEN_EXPRESSION, cursor)
        if start < 0:
            if cursor < len(raw):
                segments.append(("literal", raw[cursor:]))
            return segments
        if start > cursor:
            segments.append(("literal", raw[cursor:start]))
        in_string = False
        index = start + len(OPEN_EXPRESSION)
        end = -1
        while index < len(raw):
            char = raw[index]
            if char == "'":
                in_string = not in_string
            elif not in_string and char == "}" and raw[index - 1] == "}":
                end = index
                index += 1
                break
            index += 1
        if end < start:
            raise ValueError("expression is not closed")
        expression = raw[start + len(OPEN_EXPRESSION):end - 1].strip()
        if not expression:
            raise ValueError("expression is empty")
        segments.append(("expression", expression))
        cursor = index


def github_run_expression_length(raw):
    """Return the service-side expression length (or scalar length if literal)."""
    if OPEN_EXPRESSION not in raw:
        return utf16_code_units(raw)
    parts = []
    arguments = []
    for kind, value in split_github_template(raw):
        if kind == "literal":
            parts.append(
                value.replace("'", "''").replace("{", "{{").replace("}", "}}")
            )
        else:
            parts.append("{" + str(len(arguments)) + "}")
            arguments.append(value)
    compiled = "format('" + "".join(parts) + "'"
    compiled += "".join(", " + argument for argument in arguments) + ")"
    return utf16_code_units(compiled)


def workflow_run_scalars(path):
    """Read run scalars without a YAML dependency; return (line, value) pairs."""
    lines = path.read_text(encoding="utf-8").splitlines()
    runs = []
    index = 0
    header = re.compile(
        r"^(?P<indent> *)(?P<item>-\s+)?(?P<key>[A-Za-z0-9_-]+):"
        r"\s*(?P<value>.*)$"
    )
    block = re.compile(
        r"^(?P<style>[|>])"
        r"(?P<mods>(?:[1-9][+-]?|[+-][1-9]?|))"
        r"(?:[ \t]+(?:#.*)?)?$"
    )
    while index < len(lines):
        match = header.match(lines[index])
        if not match:
            index += 1
            continue
        key = match.group("key")
        value = match.group("value")
        block_match = block.match(value)
        if key == "run" and value.startswith(("|", ">")) and not block_match:
            raise ValueError(
                f"line {index + 1}: invalid run block-scalar header {value!r}"
            )
        if not block_match:
            if key == "run":
                if value.startswith('"') and value.endswith('"'):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"line {index + 1}: invalid double-quoted run scalar: {exc}"
                        ) from exc
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1].replace("''", "'")
                runs.append((index + 1, value))
            index += 1
            continue

        header_indent = len(match.group("indent")) + len(match.group("item") or "")
        content_start = index + 1
        content_end = content_start
        while content_end < len(lines):
            candidate = lines[content_end]
            if candidate.strip() and len(candidate) - len(candidate.lstrip(" ")) <= header_indent:
                break
            content_end += 1

        if key == "run":
            content = lines[content_start:content_end]
            nonblank_indents = [
                len(line) - len(line.lstrip(" ")) for line in content if line.strip()
            ]
            modifiers = block_match.group("mods")
            indent_modifier = next(
                (int(char) for char in modifiers if char.isdigit()),
                None,
            )
            if indent_modifier is None:
                content_indent = min(nonblank_indents, default=header_indent + 1)
            else:
                content_indent = header_indent + indent_modifier
                if any(indent < content_indent for indent in nonblank_indents):
                    raise ValueError(
                        f"line {index + 1}: run block is less indented than "
                        f"its |{indent_modifier} or >{indent_modifier} indicator"
                    )
            if content_indent <= header_indent:
                raise ValueError(f"line {index + 1}: run block is not indented")
            scalar_lines = [
                line[content_indent:] if line.strip() else "" for line in content
            ]
            scalar = "\n".join(scalar_lines)
            if "-" in modifiers:
                scalar = scalar.rstrip("\n")
            elif "+" in modifiers:
                scalar += "\n"
            else:
                scalar = scalar.rstrip("\n") + "\n"
            runs.append((index + 1, scalar))
        index = content_end
    return runs


def run_expression_guard_self_tests():
    """Exercise the guard's boundary and YAML block-scalar edge cases."""
    failures = []
    expression = "${{ github.event_name }}"
    length_cases = [
        ("20,000 UTF-16 units pass", "a" * 19_968 + expression, 20_000, False),
        ("20,001 UTF-16 units reject", "a" * 19_969 + expression, 20_001, True),
        ("astral characters count as two units", "\U0001f600" * 10_500 + expression, 21_032, True),
    ]
    for label, raw, expected_length, expected_rejected in length_cases:
        actual_length = github_run_expression_length(raw)
        actual_rejected = actual_length > RUN_EXPRESSION_LIMIT
        if (actual_length, actual_rejected) != (expected_length, expected_rejected):
            failures.append(
                f"run-expression self-test {label}: expected length/rejected "
                f"{expected_length}/{expected_rejected}, got "
                f"{actual_length}/{actual_rejected}"
            )

    class MemoryWorkflow:
        def __init__(self, text):
            self.text = text

        def read_text(self, encoding):
            if encoding != "utf-8":
                raise AssertionError(f"unexpected encoding {encoding}")
            return self.text

    scalar_cases = [
        ("literal trailing whitespace", "- run: | \n    echo x\n", [(1, "echo x\n")]),
        ("literal inline comment", "- run: | # comment\n    echo x\n", [(1, "echo x\n")]),
        ("explicit indentation", "- run: |2\n      echo x\n", [(1, "  echo x\n")]),
        ("folded strip trailing whitespace", "- run: >-  \n    echo x\n", [(1, "echo x")]),
    ]
    for label, source, expected_runs in scalar_cases:
        actual_runs = workflow_run_scalars(MemoryWorkflow(source))
        if actual_runs != expected_runs:
            failures.append(
                f"run-expression self-test {label}: expected {expected_runs!r}, "
                f"got {actual_runs!r}"
            )

    invalid_cases = [
        ("duplicate indentation modifier", "- run: |22\n    echo x\n"),
        ("duplicate chomping modifier", "- run: |++\n    echo x\n"),
        ("zero indentation modifier", "- run: |0\n    echo x\n"),
    ]
    for label, source in invalid_cases:
        try:
            workflow_run_scalars(MemoryWorkflow(source))
        except ValueError:
            continue
        failures.append(f"run-expression self-test {label}: invalid header was accepted")

    return failures


errors.extend(run_expression_guard_self_tests())


workflow_paths = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
workflow_paths += sorted((ROOT / ".github" / "workflows").glob("*.yaml"))
for workflow_path in workflow_paths:
    try:
        run_scalars = workflow_run_scalars(workflow_path)
    except (OSError, ValueError) as exc:
        errors.append(f"{workflow_path.relative_to(ROOT)}: run-scalar parser error: {exc}")
        continue
    for line_no, run_scalar in run_scalars:
        try:
            checked_length = github_run_expression_length(run_scalar)
        except ValueError as exc:
            errors.append(
                f"{workflow_path.relative_to(ROOT)}:{line_no}: "
                f"run-expression parser error: {exc}"
            )
            continue
        if checked_length > RUN_EXPRESSION_LIMIT:
            errors.append(
                f"{workflow_path.relative_to(ROOT)}:{line_no}: run expression length "
                f"{checked_length} exceeds the {RUN_EXPRESSION_LIMIT}-character guard"
            )

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

# --- artifact contract: schema 1.1 candidate-identity fields ---
ARTIFACT_CONTRACT = SKILLS / "dev-rigor-stack-lite" / "references" / "artifact-contracts.md"
if not ARTIFACT_CONTRACT.is_file():
    errors.append("artifact contract missing")
else:
    contract_text = ARTIFACT_CONTRACT.read_text(encoding="utf-8")
    example = re.search(
        r"## `run-manifest\.json`\s*```json\s*(\{.*?\})\s*```",
        contract_text,
        re.S,
    )
    if not example:
        errors.append("artifact contract: run-manifest JSON example missing")
    else:
        try:
            run_manifest = json.loads(example.group(1))
        except json.JSONDecodeError as exc:
            errors.append(f"artifact contract: run-manifest example is invalid JSON: {exc}")
        else:
            if run_manifest.get("schema_version") != "1.1":
                errors.append("artifact contract: run-manifest schema_version must be 1.1")
            identity_fields = {
                "worktree_state",
                "dirty_diff_sha256",
                "dirty_diff_evidence",
                "lockfiles",
                "seeds",
            }
            missing_identity = sorted(identity_fields - run_manifest.keys())
            if missing_identity:
                errors.append(f"artifact contract: run-manifest missing identity fields {missing_identity}")
            if run_manifest.get("worktree_state") not in {"clean", "dirty"}:
                errors.append("artifact contract: worktree_state example must be clean or dirty")
            lockfiles = run_manifest.get("lockfiles")
            if not isinstance(lockfiles, list) or not lockfiles or not {
                "path", "sha256"
            }.issubset(lockfiles[0]):
                errors.append("artifact contract: lockfiles example must contain path and sha256")
            seeds = run_manifest.get("seeds")
            if not isinstance(seeds, list) or not seeds or not {
                "context", "seed", "evidence"
            }.issubset(seeds[0]):
                errors.append("artifact contract: seeds example must contain context, seed, and evidence")
    if "Existing 1.0 manifests remain valid" not in contract_text:
        errors.append("artifact contract: schema 1.0 compatibility note missing")

# --- internal references resolve (0.3.2, Codex report) ---
# A rename that leaves a dangling `../old-name/SKILL.md` read or a stale
# `$old-name` entrypoint token ships a broken skill that still validates.
entry_names = expected | {"dev-rigor-stack-lite"}  # $tokens must name real skills
for name in sorted(expected):
    body = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    for ref in re.findall(r"\.\./([A-Za-z0-9_-]+)/SKILL\.md", body):
        if ref not in expected:
            errors.append(f"{name}: dangling sibling reference ../{ref}/SKILL.md")
    # Entrypoint tokens always contain a hyphen (quick-audit-lite, proof-gate-lite,
    # ...); requiring one keeps ordinary shell variables in code examples ($rand,
    # $here) from tripping the check. (Review finding, 0.3.2.)
    for token in re.findall(r"\$([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", body):
        if token not in entry_names:
            errors.append(f"{name}: entrypoint token ${token} names no skill in the bundle")

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
