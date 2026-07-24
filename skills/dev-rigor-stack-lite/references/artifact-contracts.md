# Dev Rigor Stack artifact contracts

Use these filenames and minimum fields so every standalone stage can hand evidence to
the next without reinterpretation. JSON artifacts supplement the human report; they do
not replace screenshots, traces, logs, commands, or other raw evidence.

## `run-manifest.json`

```json
{
  "schema_version": "1.1",
  "run_id": "unique-id",
  "stage": "plan|build|proof|review|walkthrough|visitor|merge|docs|release",
  "mode": "scoped|candidate|published|full",
  "project": "name",
  "commit": "sha-or-null",
  "artifact_ids": ["hash-or-release-asset-id"],
  "platform_scope": ["os/arch/version"],
  "started_at": "ISO-8601",
  "environment_artifacts": ["path"],
  "worktree_state": "clean",
  "dirty_diff_sha256": null,
  "dirty_diff_evidence": null,
  "lockfiles": [
    {"path": "path/to/lockfile", "sha256": "sha256-of-exact-file-bytes"}
  ],
  "seeds": [
    {"context": "randomized-suite", "seed": "seed-value", "evidence": "path"}
  ]
}
```

Schema 1.1 is additive. Existing 1.0 manifests remain valid inputs; consumers must
ignore unknown 1.1 fields. A 1.1 producer emits every identity field above, using empty
arrays when no lockfile or randomized run applies.

`worktree_state` is `clean` only when the recorded commit fully identifies the source.
For `clean`, both dirty-diff fields are null. For `dirty`, both are required:
`dirty_diff_evidence` points to a stable byte-for-byte artifact containing the complete
uncommitted delta, including staged, unstaged, and relevant untracked files, and
`dirty_diff_sha256` is the SHA-256 of that exact artifact. A dirty flag without the
artifact and matching hash is not reproducible identity.

Each detected dependency lockfile records its repository-relative path and the SHA-256
of its exact bytes. Each randomized execution records its context, replayable seed, and
raw evidence path. A 1.0 manifest cannot establish a claim that specifically depends on
these 1.1 fields; record that claim as untested or unverifiable rather than upgrading
the old evidence by inference.

## `claims.json`

```json
{
  "claims": [
    {
      "id": "CLAIM-001",
      "source": "URL/file/screen",
      "claim": "observable promise",
      "status": "survived|refuted|untested|unverifiable",
      "evidence": ["artifact/path"]
    }
  ]
}
```

## `findings.json`

```json
{
  "findings": [
    {
      "id": "FINDING-001",
      "stage": "walkthrough",
      "location": "screen/route/file",
      "severity": "Blocker|Critical|Major|Minor|Nit",
      "confirmed": true,
      "expected": "expected behavior",
      "actual": "observed behavior",
      "reproduction": ["step"],
      "evidence": ["artifact/path"],
      "suggested_fix": "fix path",
      "suggested_test": "regression test"
    }
  ]
}
```

## `coverage-ledger.json`

```json
{
  "coverage_valid": true,
  "invalid_reasons": [],
  "dimensions": {
    "screens": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0},
    "controls": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0},
    "paths": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0},
    "visual_states": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0},
    "public_surfaces": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0},
    "links": {"inventoried": 0, "tested": 0, "failed": 0, "blocked": 0, "excluded": 0}
  },
  "items": [
    {"id": "SCREEN-001", "result": "passed|failed|blocked|unverifiable|excluded", "reason": "", "evidence": ["path"]}
  ]
}
```

For every dimension: `inventoried == tested + blocked + excluded + unverifiable` after
failed items are included in tested. A missing denominator, unmatched item, contaminated
blind pass, or absent required artifact makes `coverage_valid` false.

## `handoff.json`

```json
{
  "from_stage": "visitor",
  "to_stage": "walkthrough",
  "run_id": "source-run",
  "commit": "sha-or-null",
  "artifact_ids": ["hash"],
  "inputs": {"installer_url": "https://...", "checksum": "..."},
  "open_findings": ["FINDING-001"],
  "unproven": [],
  "evidence": ["path"]
}
```

The receiving stage resolves `run_id` to the originating run manifest and verifies its
commit and artifact identity. For schema 1.1 it also compares the complete applicable
worktree, dirty-diff, lockfile, and seed identity and refuses missing, stale, or
mismatched evidence. It may add evidence; it may not rewrite the upstream record.

## `gate-result.json`

```json
{
  "stage": "release",
  "verdict": "PASS|FAIL|INVALID|BLOCKED|PARTIAL",
  "strict_zero": true,
  "severity": {"Blocker": 0, "Critical": 0, "Major": 0, "Minor": 0, "Nit": 0},
  "coverage_valid": true,
  "run_ids": ["input-run"],
  "blocking_findings": [],
  "evidence": ["path"]
}
```

PASS requires a compatible manifest schema, strict-zero, valid coverage, exact artifact
identity, and every mandatory stage for the selected scope. For schema 1.1, incomplete
dirty-worktree identity or an applicable lockfile/seed mismatch makes the result INVALID.
Missing/blocked coverage is not PASS.
