# User and operator manual

This manual has two voices. The first is for a human owner who wants a safe,
direct setup. The second is for an operator or maintainer who needs exact
identity, placement, verification, repair, and removal procedures.

## Part I: human owner

### What this installs

A default installation adds three local tiers:

1. the 19 directories named in `manifest.json`;
2. `rigor_goals.py` in a tools directory beside the skills directory; and
3. one marker-fenced anchor block in the host's instructions file.

It does not install a service, background process, lifecycle hook, or private
ledger. The goals tool writes its current plan to `./.rigor/` only when you run
it from a project.

### Acquire a pinned release

Clone the repository and detach at the release tag:

```sh
git clone https://github.com/scottconverse/dev-rigor-stack-lite.git
cd dev-rigor-stack-lite
git fetch --tags --force
git checkout --detach v0.5.1
git rev-parse HEAD
git rev-list -n 1 v0.5.1
```

The last two commit IDs must match. `git status --short` should print nothing,
and `manifest.json` should report `0.5.0`. For a later release, replace the tag
and expected manifest version together. If you use a release archive, compare
its SHA-256 to the checksum published with that release. If no archive checksum
is published, prefer the pinned Git checkout.

This confirms which bytes you are using; it is not a claim that the tag is
cryptographically signed.

### Choose the destination

For a project install, run the installer from that project and use a relative
hidden-host target. For a user install, use the rooted target shown below. The
anchor is derived from that target, not independently from the shell's current
directory. If the source checkout lives elsewhere, invoke the installer by its
absolute path.

| Host and scope | Skills target | Default goals file | Default anchor |
|---|---|---|---|
| Codex user | `$HOME/.codex/skills` | `$HOME/.codex/tools/rigor_goals.py` | `$HOME/.codex/AGENTS.md` |
| Claude project | `.claude/skills` | `.claude/tools/rigor_goals.py` | `CLAUDE.md` in the containing project |
| Antigravity project | `.agents/skills` | `.agents/tools/rigor_goals.py` | `AGENTS.md` in the containing project |
| Antigravity user/config | `$HOME/.gemini/config/skills` | `$HOME/.gemini/config/tools/rigor_goals.py` | `$HOME/.gemini/config/AGENTS.md`, adjacent to `skills` |
| Gemini CLI project | `.gemini/skills` | `.gemini/tools/rigor_goals.py` | `GEMINI.md` in the containing project |

`-Goals`/`--goals` and `-Anchor`/`--anchor` override these defaults. Record any
override because repair and removal need the same exact paths.

### Install on Windows

From the pinned source checkout, these commands configure that checkout as the
current project:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target "$HOME\.codex\skills"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".agents\skills"
```

The bypass is scoped to the child PowerShell process. It does not change the
user, machine, registry, or organization execution policy.

To configure a different project, resolve the installer first, then change
directory. The installer keeps using its own source tree while relative target
and default anchor paths resolve from the project:

```powershell
$Installer = (Resolve-Path "C:\path\to\dev-rigor-stack-lite\install.ps1").Path
Set-Location "C:\path\to\your-project"
powershell -NoProfile -ExecutionPolicy Bypass -File $Installer -Target ".claude\skills"
```

### Install from Bash

From the pinned source checkout:

```sh
./install.sh "$HOME/.codex/skills"
./install.sh .claude/skills
./install.sh .agents/skills
```

For another project, keep the installer path absolute:

```sh
installer=$(cd /path/to/dev-rigor-stack-lite && pwd -P)/install.sh
cd /path/to/your-project
"$installer" .claude/skills
```

The default install creates all three tiers. `-NoGoals`/`--no-goals` and
`-NoAnchor`/`--no-anchor` are human-owner opt-outs, not shortcuts for automated
agents.

### Verify the result

Before using the stack, confirm:

- every one of the 19 manifest names exists under the skills target;
- the expected `rigor_goals.py` file exists;
- the expected host instructions file contains exactly one anchor begin marker
  and one end marker; and
- `python tools/validate_bundle.py` passes in the pinned source checkout.

Exact commands are in [Technical verification](#technical-verification).

### Upgrade or repair

Acquire and verify the desired release first. Back up any locally modified
skill, goals, or host instructions file, then rerun the same command with
`-Force` or `--force`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ".claude\skills" -Force
```

```sh
./install.sh .claude/skills --force
```

Force replaces the 19 manifest-named skill directories, refreshes the goals
file, and replaces the single managed anchor span. It preserves unrelated
target entries and text outside the markers. The same-version command is a
repair; a newer pinned source is an upgrade.

### Remove the stack

Do not remove the whole skills target, tools directory, or host instructions
file. They may contain unrelated owner data. Do not use wildcards.

Use the audited procedure in [Safe three-tier removal](#safe-three-tier-removal).
It derives exactly 19 names from the matching pinned manifest, verifies that
installed skill bytes still match that source, refuses symbolic links, backs up
and refuses a changed goals file, and removes only one verified marker-fenced
anchor span. It preserves `./.rigor/` by default so project history is not
silently destroyed.

## Part II: technical operator or maintainer

### Identity and acquisition

`manifest.json` is the product version authority and owns the 19-skill
inventory. For a Git acquisition, bind the work to all of the following:

```sh
git rev-parse HEAD
git rev-list -n 1 v0.5.1
git status --short
python3 -c "import json; print(json.load(open('manifest.json', encoding='utf-8'))['version'])"
```

On Windows, the manifest check is:

```powershell
(Get-Content -Raw -LiteralPath .\manifest.json | ConvertFrom-Json).version
```

The head and tag commits must match, the worktree output must be empty, and the
manifest must print the intended version. Record the exact commit and any
archive SHA-256 in release-sensitive evidence.

### Placement and installer behavior

The skills target is always explicit. The goals directory defaults to the
skills target's sibling `tools` directory. The installer resolves the target
before selecting the default anchor:

- a rooted target places the inferred host file beside its `skills` directory:
  `CLAUDE.md` for `.claude`, `GEMINI.md` for `.gemini`, and `AGENTS.md`
  otherwise;
- a relative `.claude`, `.gemini`, `.agents`, or `.codex` target places that
  host file in the hidden directory's containing project;
- a `.gemini/config` target always uses `AGENTS.md` beside its `skills`
  directory; and
- another relative target uses `AGENTS.md` beside its `skills` directory.

Explicit `-Anchor`/`--anchor` and `-Goals`/`--goals` values take precedence.
The shell's working directory resolves relative inputs but never independently
selects an anchor for a rooted target. Quote paths containing spaces.

Without force, the first existing manifest-named skill makes installation fail.
With force, each of those exact directories is removed and recopied. The goals
file is copied with overwrite enabled. The installer adds or replaces the
managed anchor span while preserving content outside the markers.

### Technical verification

Set the three paths to the installation you are checking. This PowerShell check
counts manifest-owned skills rather than assuming the target contains nothing
else:

```powershell
$Target = ".claude\skills"
$GoalsFile = ".claude\tools\rigor_goals.py"
$AnchorFile = "CLAUDE.md"

$manifest = Get-Content -Raw -LiteralPath .\manifest.json | ConvertFrom-Json
$names = @($manifest.skills)
if ($manifest.skill_count -ne 19 -or $names.Count -ne 19) {
  throw "manifest does not authorize exactly 19 skills"
}
$missing = @($names | Where-Object {
  -not (Test-Path -LiteralPath (Join-Path $Target $_) -PathType Container)
})
if ($missing.Count) { throw "missing skills: $($missing -join ', ')" }
if (-not (Test-Path -LiteralPath $GoalsFile -PathType Leaf)) {
  throw "missing goals file: $GoalsFile"
}
$anchorText = [IO.File]::ReadAllText(
  $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($AnchorFile)
)
$begin = ([regex]::Matches($anchorText, [regex]::Escape('<!-- dev-rigor-lite anchor'))).Count
$end = ([regex]::Matches($anchorText, [regex]::Escape('<!-- /dev-rigor-lite anchor -->'))).Count
if ($begin -ne 1 -or $end -ne 1) {
  throw "expected one anchor marker pair; found begin=$begin end=$end"
}
Write-Host "Verified 19 manifest skills, goals file, and one anchor pair"
```

The equivalent Bash-hosted check uses Python's standard library:

```sh
TARGET=.claude/skills
GOALS_FILE=.claude/tools/rigor_goals.py
ANCHOR_FILE=CLAUDE.md
python3 - "$TARGET" "$GOALS_FILE" "$ANCHOR_FILE" <<'PY'
import json
import pathlib
import sys

target, goals, anchor = map(pathlib.Path, sys.argv[1:])
manifest = json.loads(pathlib.Path("manifest.json").read_text(encoding="utf-8"))
names = manifest["skills"]
assert manifest["skill_count"] == 19
assert len(names) == len(set(names)) == 19
missing = [name for name in names if not (target / name).is_dir()]
assert not missing, f"missing skills: {missing}"
assert goals.is_file(), f"missing goals file: {goals}"
text = anchor.read_text(encoding="utf-8-sig")
assert text.count("<!-- dev-rigor-lite anchor") == 1
assert text.count("<!-- /dev-rigor-lite anchor -->") == 1
print("Verified 19 manifest skills, goals file, and one anchor pair")
PY
```

Then validate the source and exercise the installed goals tool from the project
whose state you intend to use:

```sh
python3 tools/validate_bundle.py
python3 .claude/tools/rigor_goals.py status
```

`status` reports that no plan exists until the tool has been used; that is
expected on a fresh project.

### Durable engagement lifecycle

Create a plan only when work crosses sessions or machines, uses handoffs or parallel
agents, or waits on an external event. Pin the engagement mode separately from the
Micro/Standard/Critical lane used for each unit:

```sh
# Bounded program; the backward-compatible default.
python3 .claude/tools/rigor_goals.py create --brief "ship two units" \
  --mode finite_program \
  --goal "api::implement and test" --goal "docs::document behavior"
```

Or, in a different working tree (one active plan is allowed per tree), start ongoing
ownership:

```sh
python3 .claude/tools/rigor_goals.py create --brief "take over development" \
  --mode continuous_development \
  --terminal "owner pauses, cancels, or explicitly changes the engagement mode" \
  --goal "triage::select the first accepted backlog unit"
python3 .claude/tools/rigor_goals.py next
python3 .claude/tools/rigor_goals.py checkpoint --id G001 --status complete \
  --evidence "first unit green" --verify-cmd "pytest" --verify-evidence "35 passed"
```

The four modes are `single_unit`, `finite_program`, `continuous_development`, and
`release_workflow`. Release mode also requires `--release-intent candidate` or
`--release-intent publish`. Continuing language without a bounded end resolves to
continuous development. The persisted mode governs later turns; downgrade is an owner
decision, not a coordinator inference.

After each green unit, checkpoint, reconcile the accepted scope and evidence, and select
the next authorized unit. Queue changes are explicit and ledger-stamped:

```sh
python3 .claude/tools/rigor_goals.py add \
  --goal "repair::address verified regression" \
  --authorization-source "accepted corrective finding F-12"
python3 .claude/tools/rigor_goals.py set-next --id G002 \
  --reason "dependency of the next accepted backlog item"
python3 .claude/tools/rigor_goals.py next
python3 .claude/tools/rigor_goals.py checkpoint --id G002 --status complete \
  --evidence "repair green" --verify-cmd "pytest" --verify-evidence "35 passed"
```

`waiting_external` and `blocked_owner` remain unresolved; independent in-scope work may
continue. Use `reopen --id G001 --reason "dependency recovered"` to return a failed,
blocked, `waiting_external`, or `blocked_owner` goal to the pending queue. `cancelled`
and `out_of_scope` require both evidence and an authorization-source receipt; reopening
them requires another authorization-source receipt.
`close` refuses any unresolved goal. Continuous and release closure also requires an
authorization source plus non-empty terminal evidence, verification-command, and result
fields. Those fields are receipts: the tool neither runs the command nor establishes
that the terminal predicate is true.

```sh
python3 .claude/tools/rigor_goals.py close \
  --evidence "recorded terminal predicate is satisfied" \
  --verify-cmd "command already run" --verify-evidence "observed result" \
  --authorization-source "owner instruction 2026-07-31"
```

The CLI stores the authorization source as unattributed text; it does not authenticate
the person named by that receipt. `set-mode` is the loud, ledger-stamped path for an
owner-authorized mode change. A custom terminal on a single or finite plan requires
explicit `close`; only the default all-goals-complete terminal auto-closes.

Existing schema 1 plans migrate once to schema 2 as `finite_program`, preserving goal
IDs, statuses, and evidence and appending a `plan_migrated` event. Unsupported schemas or
modes stop with an error instead of being reinterpreted. Migration cannot infer whether
an old brief was ongoing, so review the conservative `finite_program` result and use
authorization-receipted `set-mode` if the owner intended continuous work. Plan schema 2
is unrelated to run-manifest schema 1.1: the former stores engagement state; the latter
identifies stage evidence.

Executable tests cover these CLI transitions and the anchor/skill bundle contract.
Worker-local `DONE`, coordinator reconciliation after merge, and receipt-shape discipline
are advisory scenario contracts because Lite has no host-level behavior harness; do not
cite them as CI-enforced model adherence.

### Upgrade and repair evidence

For an upgrade, capture:

1. the old installed version and source identity;
2. hashes of the installed skills, goals file, and host instructions file;
3. a sentinel line of owner text outside the anchor markers;
4. the force command and complete output;
5. the new pinned source identity;
6. a byte comparison of installed skills and goals against the new source; and
7. proof that the sentinel survives and exactly one marker pair remains.

A no-force overwrite refusal should leave a before/after byte inventory
unchanged. A same-version force repair should be byte-idempotent. The CI
lifecycle jobs exercise these properties on Ubuntu and macOS; Windows CI covers
the process-scoped README path and default-on contract.

### Safe three-tier removal

The repository intentionally does not ship an uninstaller. Removal is an owner
operation because targets and host policy files vary. Start from the exact
pinned source version that produced the installation, and set absolute paths
when the install lives outside the source checkout.

Both procedures below enforce these preconditions before deletion:

- `manifest.json` contains 19 unique, path-safe names and `skill_count` is 19;
- each exact installed skill tree byte-matches the corresponding pinned source
  tree and is not a symbolic link or junction;
- the skills target, goals file, and anchor file are real, non-linked entries;
  the two files are not hard links; and none aliases the pinned source
  `skills/`, `tools/rigor_goals.py`, or `anchor/anchor.md`; PowerShell refuses
  a link or junction in any existing path component, while Bash resolves
  ancestor aliases before its same-file checks;
- the installed goals file byte-matches `tools/rigor_goals.py`;
- the host instructions file is valid UTF-8 and contains exactly one ordered
  marker pair; and
- the human types `REMOVE 19` after previewing every exact path.

If the goals file has changed, it is copied to an owner-backup path and the
procedure stops before any removal. Any skill mismatch or marker defect also
stops before deletion. Reconcile or back up the changed content; never broaden
the deletion.

#### PowerShell removal

Run this from the matching pinned source root after setting the three paths.
For safety, the procedure refuses a link or junction anywhere in the source,
target, goals, or anchor path:

The Windows fence compares filesystem identity, so alternate spellings such as
localhost UNC aliases cannot bypass its pinned-source refusal.

```powershell
$Target = ".claude\skills"
$GoalsFile = ".claude\tools\rigor_goals.py"
$AnchorFile = "CLAUDE.md"
$ErrorActionPreference = "Stop"

function Resolve-UserPath([string]$Path) {
  $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
}
function Assert-PlainPath([string]$Path, [string]$Label) {
  $cursor = Resolve-UserPath $Path
  while ($null -ne $cursor) {
    $item = Get-Item -LiteralPath $cursor -Force
    $linkType = if ($item.PSObject.Properties["LinkType"]) {
      [string]$item.LinkType
    } else {
      ""
    }
    if (
      ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
      -not [string]::IsNullOrEmpty($linkType)
    ) {
      throw "refusing linked $Label path component: $cursor"
    }
    $parent = [IO.Directory]::GetParent($cursor)
    $cursor = if ($null -eq $parent) { $null } else { $parent.FullName }
  }
}
if (-not ("DevRigorLiteRemovalFileIdentity" -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public static class DevRigorLiteRemovalFileIdentity
{
    private const uint ShareAll = 0x00000001 | 0x00000002 | 0x00000004;
    private const uint OpenExisting = 3;
    private const uint BackupSemantics = 0x02000000;

    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime
    {
        public uint Low;
        public uint High;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FileInformation
    {
        public uint Attributes;
        public FileTime CreationTime;
        public FileTime LastAccessTime;
        public FileTime LastWriteTime;
        public uint VolumeSerialNumber;
        public uint FileSizeHigh;
        public uint FileSizeLow;
        public uint NumberOfLinks;
        public uint FileIndexHigh;
        public uint FileIndexLow;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFileW(
        string path,
        uint access,
        uint share,
        IntPtr securityAttributes,
        uint creationDisposition,
        uint flags,
        IntPtr template);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileInformationByHandle(
        SafeFileHandle handle,
        out FileInformation information);

    private static SafeFileHandle Open(string path)
    {
        SafeFileHandle handle = CreateFileW(
            path,
            0,
            ShareAll,
            IntPtr.Zero,
            OpenExisting,
            BackupSemantics,
            IntPtr.Zero);
        if (handle.IsInvalid)
        {
            int error = Marshal.GetLastWin32Error();
            handle.Dispose();
            throw new Win32Exception(error, "cannot open path for identity: " + path);
        }
        return handle;
    }

    private static FileInformation Read(SafeFileHandle handle, string path)
    {
        FileInformation information;
        if (!GetFileInformationByHandle(handle, out information))
        {
            throw new Win32Exception(
                Marshal.GetLastWin32Error(),
                "cannot read path identity: " + path);
        }
        if (information.FileIndexHigh == 0 && information.FileIndexLow == 0)
        {
            throw new InvalidOperationException(
                "filesystem returned no usable file ID for: " + path);
        }
        return information;
    }

    public static bool Same(string left, string right)
    {
        using (SafeFileHandle leftHandle = Open(left))
        using (SafeFileHandle rightHandle = Open(right))
        {
            FileInformation leftInfo = Read(leftHandle, left);
            FileInformation rightInfo = Read(rightHandle, right);
            return
                leftInfo.VolumeSerialNumber == rightInfo.VolumeSerialNumber &&
                leftInfo.FileIndexHigh == rightInfo.FileIndexHigh &&
                leftInfo.FileIndexLow == rightInfo.FileIndexLow;
        }
    }
}
'@
}
function Test-SamePath([string]$Left, [string]$Right) {
  [DevRigorLiteRemovalFileIdentity]::Same(
    (Resolve-UserPath $Left),
    (Resolve-UserPath $Right)
  )
}
function Get-TreeInventory([string]$Root) {
  Assert-PlainPath $Root "tree root"
  $base = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\', '/') +
    [IO.Path]::DirectorySeparatorChar
  @(
    Get-ChildItem -LiteralPath $Root -Recurse -Force |
      Sort-Object FullName |
      ForEach-Object {
        if (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
          throw "refusing linked tree content: $($_.FullName)"
        }
        $relative = $_.FullName.Substring($base.Length).Replace('\', '/')
        if ($_.PSIsContainer) {
          "DIR|$relative"
        } else {
          $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
          "FILE|$relative|$hash"
        }
      }
  )
}

$root = (Resolve-Path -LiteralPath .).Path
$manifestPath = Join-Path $root "manifest.json"
$sourceSkills = Join-Path $root "skills"
$sourceGoals = Join-Path $root "tools\rigor_goals.py"
$sourceAnchor = Join-Path $root "anchor\anchor.md"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "run from the matching pinned source root"
}
Assert-PlainPath $root "pinned source root"
Assert-PlainPath $manifestPath "pinned manifest"
Assert-PlainPath $sourceGoals "pinned goals file"
Assert-PlainPath $sourceAnchor "pinned anchor file"
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$names = @($manifest.skills)
$unique = @($names | Sort-Object -Unique)
if ($manifest.skill_count -ne 19 -or $names.Count -ne 19 -or $unique.Count -ne 19) {
  throw "manifest does not authorize exactly 19 unique skills"
}
foreach ($name in $names) {
  if ($name -cnotmatch '^[a-z0-9][a-z0-9-]*$') {
    throw "unsafe manifest skill name: $name"
  }
}

$targetInput = Resolve-UserPath $Target
if (-not (Test-Path -LiteralPath $targetInput -PathType Container)) {
  throw "missing skills target: $targetInput"
}
Assert-PlainPath $targetInput "skills target"
$targetPath = (Resolve-Path -LiteralPath $targetInput).Path
if (Test-SamePath $targetPath $sourceSkills) {
  throw "refusing skills target that aliases pinned source: $targetPath"
}
$skillPaths = @()
foreach ($name in $names) {
  $source = Join-Path $sourceSkills $name
  $installed = Join-Path $targetPath $name
  if (-not (Test-Path -LiteralPath $installed -PathType Container)) {
    throw "missing installed skill directory: $installed"
  }
  $item = Get-Item -LiteralPath $installed
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "refusing linked skill directory: $installed"
  }
  $sourceInventory = @(Get-TreeInventory $source)
  $installedInventory = @(Get-TreeInventory $installed)
  if (@(Compare-Object $sourceInventory $installedInventory).Count -ne 0) {
    throw "installed skill differs from pinned source: $installed"
  }
  $skillPaths += $installed
}

$goalsPath = Resolve-UserPath $GoalsFile
$anchorPath = Resolve-UserPath $AnchorFile
if (-not (Test-Path -LiteralPath $goalsPath -PathType Leaf)) {
  throw "missing goals file: $goalsPath"
}
if (-not (Test-Path -LiteralPath $anchorPath -PathType Leaf)) {
  throw "missing anchor file: $anchorPath"
}
Assert-PlainPath $goalsPath "goals file"
Assert-PlainPath $anchorPath "anchor file"
if (Test-SamePath $goalsPath $sourceGoals) {
  throw "refusing goals file that aliases pinned source: $goalsPath"
}
if (Test-SamePath $anchorPath $sourceAnchor) {
  throw "refusing anchor file that aliases pinned source: $anchorPath"
}

$sourceGoalsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceGoals).Hash
$installedGoalsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $goalsPath).Hash
if ($sourceGoalsHash -cne $installedGoalsHash) {
  $backup = "$goalsPath.owner-backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
  Copy-Item -LiteralPath $goalsPath -Destination $backup
  throw "changed goals file backed up to $backup; no installed files were removed"
}

$bytes = [IO.File]::ReadAllBytes($anchorPath)
$hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and
  $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
$offset = if ($hasBom) { 3 } else { 0 }
$strictUtf8 = New-Object Text.UTF8Encoding($false, $true)
$anchorText = $strictUtf8.GetString($bytes, $offset, $bytes.Length - $offset)
$beginMarker = '<!-- dev-rigor-lite anchor'
$endMarker = '<!-- /dev-rigor-lite anchor -->'
$canonicalAnchorLines = [IO.File]::ReadAllText($sourceAnchor) -split '\r?\n'
$canonicalBeginLine = $canonicalAnchorLines[0]
$canonicalEndLine = @($canonicalAnchorLines | Where-Object { $_ -ne '' })[-1]
$beginCount = ([regex]::Matches($anchorText, [regex]::Escape($beginMarker))).Count
$endCount = ([regex]::Matches($anchorText, [regex]::Escape($endMarker))).Count
if ($beginCount -ne 1 -or $endCount -ne 1) {
  throw "expected exactly one anchor pair; found begin=$beginCount end=$endCount"
}
$lines = [regex]::Split($anchorText, '(?<=\n)')
$beginIndex = -1
$endIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
  $lineText = $lines[$i].TrimEnd([char[]]"`r`n")
  if ($lineText.Contains($beginMarker)) {
    if ($lineText -cne $canonicalBeginLine) {
      throw "begin-marker line contains changed or owner text"
    }
    $beginIndex = $i
  }
  if ($lineText.Contains($endMarker)) {
    if ($lineText -cne $canonicalEndLine) {
      throw "end-marker line contains changed or owner text"
    }
    $endIndex = $i
  }
}
if ($beginIndex -lt 0 -or $endIndex -le $beginIndex) {
  throw "anchor markers are not one ordered span"
}
$builder = New-Object Text.StringBuilder
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($i -lt $beginIndex -or $i -gt $endIndex) {
    [void]$builder.Append($lines[$i])
  }
}
$anchorWithoutManagedSpan = $builder.ToString()

Write-Host "The following exact skill directories will be removed:"
$skillPaths | ForEach-Object { Write-Host "  $_" }
Write-Host "The exact goals file will be removed: $goalsPath"
Write-Host "Only the verified managed span will be removed from: $anchorPath"
Write-Host "The target directory, tools directory, host file, and .rigor will remain."
$confirmation = Read-Host "Type REMOVE 19 to continue"
if ($confirmation -cne "REMOVE 19") { throw "removal cancelled" }

foreach ($path in $skillPaths) {
  Remove-Item -LiteralPath $path -Recurse -Force
}
Remove-Item -LiteralPath $goalsPath -Force
$outputEncoding = New-Object Text.UTF8Encoding($hasBom)
[IO.File]::WriteAllText($anchorPath, $anchorWithoutManagedSpan, $outputEncoding)

if (@($skillPaths | Where-Object { Test-Path -LiteralPath $_ }).Count -ne 0) {
  throw "one or more manifest-owned skill directories remain"
}
if (Test-Path -LiteralPath $goalsPath) { throw "goals file remains" }
$after = [IO.File]::ReadAllText($anchorPath)
if ($after.Contains($beginMarker) -or $after.Contains($endMarker)) {
  throw "managed marker remains"
}
Write-Host "Removed exactly 19 verified skill directories, one goals file, and one anchor span."
Write-Host ".rigor and all parent directories were preserved."
```

#### Bash removal

This procedure uses the installed Python 3 interpreter for byte-safe,
manifest-driven checks. Set absolute paths if the installation is outside the
matching pinned source root:

```sh
set -eu

ROOT=$(pwd -P)
TARGET=.claude/skills
GOALS_FILE=.claude/tools/rigor_goals.py
ANCHOR_FILE=CLAUDE.md
export ROOT TARGET GOALS_FILE ANCHOR_FILE

# Read-only preview from manifest authority.
python3 - <<'PY'
import json
import os
import pathlib
import re

root = pathlib.Path(os.environ["ROOT"]).resolve(strict=True)

def operator_path(value, label):
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = pathlib.Path.cwd() / path
    path = pathlib.Path(os.path.abspath(path))
    if path.is_symlink():
        raise SystemExit(f"refusing linked {label}: {path}")
    return path

target_input = operator_path(os.environ["TARGET"], "skills target")
goals_input = operator_path(os.environ["GOALS_FILE"], "goals file")
anchor_input = operator_path(os.environ["ANCHOR_FILE"], "anchor file")
if not target_input.is_dir():
    raise SystemExit(f"missing skills target: {target_input}")
if not goals_input.is_file():
    raise SystemExit(f"missing goals file: {goals_input}")
if not anchor_input.is_file():
    raise SystemExit(f"missing anchor file: {anchor_input}")
if os.lstat(goals_input).st_nlink != 1:
    raise SystemExit(f"refusing hard-linked goals file: {goals_input}")
if os.lstat(anchor_input).st_nlink != 1:
    raise SystemExit(f"refusing hard-linked anchor file: {anchor_input}")

target = target_input.resolve(strict=True)
goals = goals_input.resolve(strict=True)
anchor = anchor_input.resolve(strict=True)
source_skills = (root / "skills").resolve(strict=True)
source_goals = (root / "tools" / "rigor_goals.py").resolve(strict=True)
source_anchor = (root / "anchor" / "anchor.md").resolve(strict=True)
if os.path.samefile(target, source_skills):
    raise SystemExit(f"refusing skills target that aliases pinned source: {target}")
if os.path.samefile(goals, source_goals):
    raise SystemExit(f"refusing goals file that aliases pinned source: {goals}")
if os.path.samefile(anchor, source_anchor):
    raise SystemExit(f"refusing anchor file that aliases pinned source: {anchor}")

manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
names = manifest["skills"]
assert manifest["skill_count"] == 19
assert len(names) == len(set(names)) == 19
assert all(re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in names)
print("The following exact skill directories will be removed:")
for name in names:
    print(f"  {target / name}")
print(f"The exact goals file will be removed: {goals}")
print(f"Only the verified managed span will be removed from: {anchor}")
print("The target directory, tools directory, host file, and .rigor will remain.")
PY

printf 'Type REMOVE 19 to continue: '
IFS= read -r CONFIRMATION
[ "$CONFIRMATION" = "REMOVE 19" ] || { echo "removal cancelled" >&2; exit 1; }
export CONFIRMATION

python3 - <<'PY'
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys

if os.environ.get("CONFIRMATION") != "REMOVE 19":
    raise SystemExit("removal cancelled")

root = pathlib.Path(os.environ["ROOT"]).resolve(strict=True)

def operator_path(value, label):
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = pathlib.Path.cwd() / path
    path = pathlib.Path(os.path.abspath(path))
    if path.is_symlink():
        raise SystemExit(f"refusing linked {label}: {path}")
    return path

target_input = operator_path(os.environ["TARGET"], "skills target")
goals_input = operator_path(os.environ["GOALS_FILE"], "goals file")
anchor_input = operator_path(os.environ["ANCHOR_FILE"], "anchor file")
if not target_input.is_dir():
    raise SystemExit(f"missing skills target: {target_input}")
if not goals_input.is_file():
    raise SystemExit(f"missing goals file: {goals_input}")
if not anchor_input.is_file():
    raise SystemExit(f"missing anchor file: {anchor_input}")
if os.lstat(goals_input).st_nlink != 1:
    raise SystemExit(f"refusing hard-linked goals file: {goals_input}")
if os.lstat(anchor_input).st_nlink != 1:
    raise SystemExit(f"refusing hard-linked anchor file: {anchor_input}")

target = target_input.resolve(strict=True)
goals = goals_input.resolve(strict=True)
anchor = anchor_input.resolve(strict=True)
source_skills = (root / "skills").resolve(strict=True)
source_goals = (root / "tools" / "rigor_goals.py").resolve(strict=True)
source_anchor = (root / "anchor" / "anchor.md").resolve(strict=True)
if os.path.samefile(target, source_skills):
    raise SystemExit(f"refusing skills target that aliases pinned source: {target}")
if os.path.samefile(goals, source_goals):
    raise SystemExit(f"refusing goals file that aliases pinned source: {goals}")
if os.path.samefile(anchor, source_anchor):
    raise SystemExit(f"refusing anchor file that aliases pinned source: {anchor}")

manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
names = manifest["skills"]
if manifest.get("skill_count") != 19 or len(names) != 19 or len(set(names)) != 19:
    raise SystemExit("manifest does not authorize exactly 19 unique skills")
if not all(re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in names):
    raise SystemExit("manifest contains an unsafe skill name")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def inventory(tree):
    if not tree.is_dir() or tree.is_symlink():
        raise SystemExit(f"refusing missing or linked skill directory: {tree}")
    result = []
    for member in sorted(tree.rglob("*")):
        if member.is_symlink():
            raise SystemExit(f"refusing linked content: {member}")
        if member.is_file():
            result.append((member.relative_to(tree).as_posix(), digest(member)))
    return result

skill_paths = []
for name in names:
    source = root / "skills" / name
    installed = target / name
    if inventory(source) != inventory(installed):
        raise SystemExit(f"installed skill differs from pinned source: {installed}")
    skill_paths.append(installed)

if not goals.is_file() or goals.is_symlink():
    raise SystemExit(f"refusing missing or linked goals file: {goals}")
if not anchor.is_file() or anchor.is_symlink():
    raise SystemExit(f"refusing missing or linked anchor file: {anchor}")

raw = anchor.read_bytes()
bom = raw.startswith(b"\xef\xbb\xbf")
try:
    text = raw.decode("utf-8-sig")
except UnicodeDecodeError as exc:
    raise SystemExit(f"anchor is not valid UTF-8: {exc}")
begin = "<!-- dev-rigor-lite anchor"
end = "<!-- /dev-rigor-lite anchor -->"
canonical_lines = (root / "anchor" / "anchor.md").read_text(
    encoding="utf-8"
).splitlines()
canonical_begin = canonical_lines[0]
canonical_end = canonical_lines[-1]
if text.count(begin) != 1 or text.count(end) != 1:
    raise SystemExit("anchor does not contain exactly one marker pair")
lines = text.splitlines(keepends=True)
begin_indexes = [i for i, line in enumerate(lines) if begin in line]
end_indexes = [i for i, line in enumerate(lines) if end in line]
if len(begin_indexes) != 1 or len(end_indexes) != 1 or begin_indexes[0] >= end_indexes[0]:
    raise SystemExit("anchor markers are not one ordered span")
if lines[begin_indexes[0]].rstrip("\r\n") != canonical_begin:
    raise SystemExit("begin-marker line contains changed or owner text")
if lines[end_indexes[0]].rstrip("\r\n") != canonical_end:
    raise SystemExit("end-marker line contains changed or owner text")
updated = "".join(
    line for i, line in enumerate(lines)
    if i < begin_indexes[0] or i > end_indexes[0]
)
updated_bytes = (b"\xef\xbb\xbf" if bom else b"") + updated.encode("utf-8")

if digest(source_goals) != digest(goals):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%SZ")
    backup = goals.with_name(goals.name + ".owner-backup." + stamp)
    if backup.exists():
        raise SystemExit(f"backup path already exists: {backup}")
    shutil.copy2(goals, backup)
    raise SystemExit(f"changed goals file backed up to {backup}; no installed files were removed")

for path in skill_paths:
    shutil.rmtree(path)
goals.unlink()
with anchor.open("wb") as stream:
    stream.write(updated_bytes)

if any(path.exists() for path in skill_paths):
    raise SystemExit("one or more manifest-owned skill directories remain")
if goals.exists():
    raise SystemExit("goals file remains")
after = anchor.read_text(encoding="utf-8-sig")
if begin in after or end in after:
    raise SystemExit("managed marker remains")
print("Removed exactly 19 verified skill directories, one goals file, and one anchor span.")
print(".rigor and all parent directories were preserved.")
PY
```

An intentionally owner-opted-out install may lack the goals file or anchor. Do
not weaken these checks in place. Confirm the original install evidence, then
remove only the components that were actually installed with an equally narrow
procedure.

### What removal preserves

The procedures never remove:

- the skills target or its unrelated entries;
- the parent tools directory or unrelated tools;
- the host instructions file or owner text outside the managed span;
- the source checkout; or
- any project's `./.rigor/` directory.

Archive or delete `./.rigor/` only as a separate, explicit project-state
decision. It may contain continuity evidence that outlives the installation.

For operational failures, see [Troubleshooting](troubleshooting.md). For
component boundaries, see [Architecture](architecture.md). For security limits
and reporting, see [SECURITY.md](../SECURITY.md).
