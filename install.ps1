param(
  [Parameter(Mandatory = $true)][string]$Target,
  [switch]$Force,
  [string]$Goals,
  [string]$Anchor,
  # OWNER-ONLY opt-outs: the anchor and rigor-goals are part of the stack and
  # install by default. These switches exist for the human owner; an agent must
  # never pass them on its own initiative.
  [switch]$NoGoals,
  [switch]$NoAnchor
)

$ErrorActionPreference = 'Stop'

# An opt-out combined with its own explicit override is a contradiction —
# refuse loudly rather than silently picking a winner. (Review finding, 0.3.0.)
if ($NoGoals -and $Goals) { throw 'conflicting flags: -NoGoals and -Goals cannot be combined' }
if ($NoAnchor -and $Anchor) { throw 'conflicting flags: -NoAnchor and -Anchor cannot be combined' }

# Resolve relative paths against PowerShell's ACTUAL working directory ($PWD).
# [IO.Path]::GetFullPath alone resolves against the process CurrentDirectory,
# which Set-Location/cd never updates — the documented install commands would
# silently write into the wrong folder. (Gate finding, 0.2.1.)
function Resolve-UserPath([string]$p) {
  return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
}

function Get-ComparablePath([string]$p, [int]$Depth = 0) {
  if ($Depth -gt 32) {
    throw "refusing path with excessive link depth: $p"
  }
  $fullPath = Resolve-UserPath $p
  $root = [IO.Path]::GetPathRoot($fullPath)
  $segments = @($fullPath.Substring($root.Length).Split(
    [char[]]'\/', [StringSplitOptions]::RemoveEmptyEntries
  ))
  $current = $root
  for ($index = 0; $index -lt $segments.Count; $index++) {
    $candidate = Join-Path $current $segments[$index]
    $item = Get-Item -LiteralPath $candidate -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) {
      for ($remainder = $index; $remainder -lt $segments.Count; $remainder++) {
        $current = Join-Path $current $segments[$remainder]
      }
      return $current.TrimEnd([char[]]'\/')
    }
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
      $targets = @($item.Target)
      if ($targets.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$targets[0])) {
        throw "refusing path with an unresolved link target: $candidate"
      }
      $linkTarget = [string]$targets[0]
      if (-not [IO.Path]::IsPathRooted($linkTarget)) {
        $linkTarget = Join-Path (Split-Path -Parent $candidate) $linkTarget
      }
      for ($remainder = $index + 1; $remainder -lt $segments.Count; $remainder++) {
        $linkTarget = Join-Path $linkTarget $segments[$remainder]
      }
      return Get-ComparablePath $linkTarget ($Depth + 1)
    }
    $current = $candidate
  }
  return $current.TrimEnd([char[]]'\/')
}

function Test-SamePath([string]$Left, [string]$Right) {
  return [StringComparer]::OrdinalIgnoreCase.Equals(
    (Get-ComparablePath $Left),
    (Get-ComparablePath $Right)
  )
}

function Test-PathEntry([string]$p) {
  return $null -ne (Get-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue)
}

function Get-DefaultAnchorPath([string]$ResolvedTarget, [bool]$RootedInput) {
  $targetParent = Split-Path -Parent $ResolvedTarget
  $hostDirectory = (Split-Path -Leaf $targetParent).ToLowerInvariant()
  $hostParent = Split-Path -Parent $targetParent

  # A rooted target names a user-host location, so its instructions file belongs
  # beside the skills directory. A relative hidden host directory names a project,
  # so its instructions file belongs in that directory's containing project.
  $anchorDirectory = $targetParent
  if (-not $RootedInput -and $hostDirectory -in @('.claude', '.gemini', '.agents', '.codex')) {
    $anchorDirectory = $hostParent
  }
  if ($hostDirectory -eq '.claude') { return Join-Path $anchorDirectory 'CLAUDE.md' }
  if ($hostDirectory -eq '.gemini') { return Join-Path $anchorDirectory 'GEMINI.md' }
  return Join-Path $anchorDirectory 'AGENTS.md'
}

$targetWasRooted = [IO.Path]::IsPathRooted($Target) -or $Target -match '^~(?:[\\/]|$)'
$source = Join-Path $PSScriptRoot 'skills'
$targetPath = Resolve-UserPath $Target

# Default-on: the full stack installs unless the owner opts out. Derive both
# companion locations from the resolved target; CWD only resolves a relative
# Target and never independently selects a host instructions file.
if (-not $NoGoals -and -not $Goals) {
  $Goals = Join-Path (Split-Path -Parent $targetPath) 'tools'
}
if (-not $NoAnchor -and -not $Anchor) {
  $Anchor = Get-DefaultAnchorPath $targetPath $targetWasRooted
}

# Preflight every known refusal before the first filesystem mutation. A failed
# install must not leave a mixed skill inventory or a goals-only partial install.
if ((Test-PathEntry $targetPath) -and
    -not (Test-Path -LiteralPath $targetPath -PathType Container)) {
  throw "skills target exists but is not a directory: $targetPath"
}
if (Test-SamePath $targetPath $source) {
  throw "refusing skills target that aliases bundled source: $targetPath"
}

$sourceSkills = @(Get-ChildItem -LiteralPath $source -Directory)
if (-not $Force) {
  $collisions = @($sourceSkills | Where-Object {
    Test-PathEntry (Join-Path $targetPath $_.Name)
  } | ForEach-Object { Join-Path $targetPath $_.Name })
  if ($collisions.Count -gt 0) {
    throw "Skills already exist (use -Force to replace): $($collisions -join ', ')"
  }
}

if ($Goals) {
  $goalsDir = Resolve-UserPath $Goals
  if ((Test-PathEntry $goalsDir) -and
      -not (Test-Path -LiteralPath $goalsDir -PathType Container)) {
    throw "goals destination exists but is not a directory: $goalsDir"
  }
  $sourceGoals = Join-Path $PSScriptRoot 'tools\rigor_goals.py'
  $goalsFile = Join-Path $goalsDir 'rigor_goals.py'
  if (Test-SamePath $goalsFile $sourceGoals) {
    throw "refusing goals destination that aliases bundled source: $goalsFile"
  }
}

if ($Anchor) {
  $anchorFile = Resolve-UserPath $Anchor
  $anchorSrc = Join-Path $PSScriptRoot 'anchor\anchor.md'
  if (Test-SamePath $anchorFile $anchorSrc) {
    throw "refusing anchor destination that aliases bundled source: $anchorFile"
  }
  if (Test-PathEntry $anchorFile) {
    if (-not (Test-Path -LiteralPath $anchorFile -PathType Leaf)) {
      throw "anchor destination exists but is not a file: $anchorFile"
    }
    $existingAnchor = [IO.File]::ReadAllText($anchorFile)
    $beginMarker = '<!-- dev-rigor-lite anchor'
    $endMarker = '<!-- /dev-rigor-lite anchor -->'
    $beginCount = ([regex]::Matches(
      $existingAnchor, [regex]::Escape($beginMarker)
    )).Count
    $endCount = ([regex]::Matches(
      $existingAnchor, [regex]::Escape($endMarker)
    )).Count
    if (($beginCount -eq 0) -xor ($endCount -eq 0)) {
      throw "anchor block in $anchorFile has an incomplete marker pair - fix it by hand first"
    }
    if ($beginCount -gt 1 -or $endCount -gt 1) {
      throw "anchor block in $anchorFile has duplicate markers - fix it by hand first"
    }
    if ($beginCount -eq 1 -and
        $existingAnchor.IndexOf($endMarker, [StringComparison]::Ordinal) -lt
        $existingAnchor.IndexOf($beginMarker, [StringComparison]::Ordinal)) {
      throw "anchor block in $anchorFile has markers out of order - fix it by hand first"
    }
    if ($beginCount -eq 1) {
      $canonicalLines = [IO.File]::ReadAllText($anchorSrc) -split '\r?\n'
      $canonicalBegin = $canonicalLines[0]
      $canonicalEnd = @($canonicalLines | Where-Object { $_ -ne '' })[-1]
      $existingLines = $existingAnchor -split '\r?\n'
      $actualBegin = @($existingLines | Where-Object { $_.Contains($beginMarker) })[0]
      $actualEnd = @($existingLines | Where-Object { $_.Contains($endMarker) })[0]
      if ($actualBegin -cne $canonicalBegin -or $actualEnd -cne $canonicalEnd) {
        throw "anchor markers in $anchorFile share a line with owner or changed text - fix it by hand first"
      }
    }
  }
}

New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

# Migration (0.3.2, review-hardened): remove the stale lite-owned audit-lite left
# by upgrades over a pre-0.3.1 lite install. Identity = lite's exact escalation
# sentence (case-sensitive, matching install.sh) — never a bare name mention.
# Destructive only under -Force, like every other destructive act here.
$oldAudit = Join-Path $targetPath 'audit-lite'
$oldSkillMd = Join-Path $oldAudit 'SKILL.md'
$liteMarker = 'Escalate to `audit-team-lite`'
if (Test-Path -LiteralPath $oldSkillMd) {
  if (Select-String -LiteralPath $oldSkillMd -SimpleMatch $liteMarker -CaseSensitive -Quiet) {
    if ($Force) {
      Remove-Item -LiteralPath $oldAudit -Recurse -Force
      Write-Host 'Migrated: removed stale lite-owned audit-lite (renamed to quick-audit-lite in 0.3.1)'
    } else {
      Write-Warning "stale lite-owned audit-lite detected at $oldAudit (renamed to quick-audit-lite in 0.3.1). Re-run with -Force to migrate it, or remove it by hand - until then both may route."
    }
  } else {
    Write-Host "Note: $oldAudit is not lite's old copy (likely the full dev-rigor-stack's) - left untouched"
  }
}

foreach ($skill in $sourceSkills) {
  $destination = Join-Path $targetPath $skill.Name
  if (Test-Path -LiteralPath $destination) {
    if (-not $Force) { throw "Skill already exists: $destination (use -Force to replace)" }
    Remove-Item -LiteralPath $destination -Recurse -Force
  }
  Copy-Item -LiteralPath $skill.FullName -Destination $destination -Recurse
}
Write-Host "Installed 20 hook-free skills to $targetPath"

if ($Goals) {
  $goalsDir = Resolve-UserPath $Goals
  New-Item -ItemType Directory -Force -Path $goalsDir | Out-Null
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tools\rigor_goals.py') -Destination (Join-Path $goalsDir 'rigor_goals.py') -Force
  Write-Host "Installed rigor-goals to $goalsDir\rigor_goals.py (run: python $goalsDir\rigor_goals.py)"
}

if ($Anchor) {
  $anchorFile = Resolve-UserPath $Anchor
  $anchorSrc = Join-Path $PSScriptRoot 'anchor\anchor.md'
  # UTF-8 without BOM: a BOM breaks some hosts' instructions-file parsing.
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $blockText = [IO.File]::ReadAllText($anchorSrc)
  $beginMarker = '<!-- dev-rigor-lite anchor'
  $endMarker = '<!-- /dev-rigor-lite anchor -->'

  if ((Test-Path -LiteralPath $anchorFile) -and (Select-String -LiteralPath $anchorFile -SimpleMatch $beginMarker -Quiet)) {
    if (-not (Select-String -LiteralPath $anchorFile -SimpleMatch $endMarker -Quiet)) {
      throw "anchor block in $anchorFile has a begin marker but no end marker - fix it by hand first"
    }
    # Replace the managed block in place; hand edits outside the markers survive.
    $existing = [IO.File]::ReadAllText($anchorFile)
    $pattern = '(?s)' + [regex]::Escape($beginMarker) + '.*?' + [regex]::Escape($endMarker) + '\r?\n?'
    $updated = [regex]::Replace($existing, $pattern, $blockText.Replace('$', '$$'), 1)
    if ($updated -eq $existing) {
      Write-Host "Anchor block in $anchorFile is already current"
    } else {
      Write-Host "Anchor block change (old vs new):"
      Compare-Object ($existing -split "`r?`n") ($updated -split "`r?`n") | Format-Table -AutoSize | Out-String | Write-Host
      [IO.File]::WriteAllText($anchorFile, $updated, $utf8NoBom)
      Write-Host "Anchor block refreshed in $anchorFile"
    }
  } else {
    $prefix = ''
    if ((Test-Path -LiteralPath $anchorFile) -and ((Get-Item -LiteralPath $anchorFile).Length -gt 0)) {
      $prefix = [IO.File]::ReadAllText($anchorFile)
      if (-not $prefix.EndsWith("`n")) { $prefix += "`n" }
      $prefix += "`n"
    }
    [IO.File]::WriteAllText($anchorFile, $prefix + $blockText, $utf8NoBom)
    Write-Host "Anchor block added to $anchorFile"
  }
}
