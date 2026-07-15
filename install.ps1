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

# Default-on: the full stack installs unless the owner opts out.
if (-not $NoGoals -and -not $Goals) {
  $parent = Split-Path -Parent $Target
  if (-not $parent) { $parent = '.' }
  $Goals = Join-Path $parent 'tools'
}
if (-not $NoAnchor -and -not $Anchor) {
  if ($Target -like '*.claude*') { $Anchor = 'CLAUDE.md' }
  elseif ($Target -like '*.gemini*') { $Anchor = 'GEMINI.md' }
  else { $Anchor = 'AGENTS.md' }
}

# Resolve relative paths against PowerShell's ACTUAL working directory ($PWD).
# [IO.Path]::GetFullPath alone resolves against the process CurrentDirectory,
# which Set-Location/cd never updates — the documented install commands would
# silently write into the wrong folder. (Gate finding, 0.2.1.)
function Resolve-UserPath([string]$p) {
  return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
}

$source = Join-Path $PSScriptRoot 'skills'
$targetPath = Resolve-UserPath $Target
New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

# Migration (0.3.2): remove the stale lite-owned audit-lite left by upgrades over
# a pre-0.3.1 lite install. Only lite's own old copy (identified by its
# audit-team-lite escalation) is removed; the full dev-rigor-stack's audit-lite
# must never be touched — protecting it is why the rename exists.
$oldAudit = Join-Path $targetPath 'audit-lite'
$oldSkillMd = Join-Path $oldAudit 'SKILL.md'
if (Test-Path -LiteralPath $oldSkillMd) {
  if (Select-String -LiteralPath $oldSkillMd -SimpleMatch 'audit-team-lite' -Quiet) {
    Remove-Item -LiteralPath $oldAudit -Recurse -Force
    Write-Host 'Migrated: removed stale lite-owned audit-lite (renamed to quick-audit-lite in 0.3.1)'
  } else {
    Write-Host "Note: $oldAudit is not lite's old copy (likely the full dev-rigor-stack's) - left untouched"
  }
}

foreach ($skill in Get-ChildItem -LiteralPath $source -Directory) {
  $destination = Join-Path $targetPath $skill.Name
  if (Test-Path -LiteralPath $destination) {
    if (-not $Force) { throw "Skill already exists: $destination (use -Force to replace)" }
    Remove-Item -LiteralPath $destination -Recurse -Force
  }
  Copy-Item -LiteralPath $skill.FullName -Destination $destination -Recurse
}
Write-Host "Installed 19 hook-free skills to $targetPath"

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
