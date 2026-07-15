param(
  [Parameter(Mandatory = $true)][string]$Target,
  [switch]$Force
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
