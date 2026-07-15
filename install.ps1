param(
  [Parameter(Mandatory = $true)][string]$Target,
  [switch]$Force,
  [string]$Goals,
  [string]$Anchor
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'skills'
$targetPath = [IO.Path]::GetFullPath($Target)
New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

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
  $goalsDir = [IO.Path]::GetFullPath($Goals)
  New-Item -ItemType Directory -Force -Path $goalsDir | Out-Null
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tools\rigor_goals.py') -Destination (Join-Path $goalsDir 'rigor_goals.py') -Force
  Write-Host "Installed rigor-goals to $goalsDir\rigor_goals.py (run: python $goalsDir\rigor_goals.py)"
}

if ($Anchor) {
  $anchorFile = [IO.Path]::GetFullPath($Anchor)
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
