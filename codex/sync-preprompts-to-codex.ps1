[CmdletBinding()]
param(
    [string]$SourcePath,
    [string]$CodexHome,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Resolve-SourcePath {
    param([string]$Path)

    if ($Path) {
        if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
            throw "Source path does not exist: $Path"
        }
        return (Resolve-Path -LiteralPath $Path).ProviderPath
    }

    $defaultSource = Join-Path $PSScriptRoot "prepromts"
    if (Test-Path -LiteralPath $defaultSource -PathType Container) {
        return (Resolve-Path -LiteralPath $defaultSource).ProviderPath
    }

    $fallbackSource = Join-Path $PSScriptRoot "preprompts"
    if (Test-Path -LiteralPath $fallbackSource -PathType Container) {
        return (Resolve-Path -LiteralPath $fallbackSource).ProviderPath
    }

    throw "Source path was not found. Expected '$defaultSource' or '$fallbackSource'."
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (Test-Path -LiteralPath $Path -PathType Container) {
        return
    }

    if ($DryRun) {
        Write-Host "DRY RUN mkdir $Path"
        return
    }

    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Sync-File {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $destinationParent = Split-Path -Parent $Destination
    Ensure-Directory $destinationParent

    if ($DryRun) {
        Write-Host "DRY RUN copy file $Source -> $Destination"
        return
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    Write-Host "Copied file $Destination"
}

function Sync-Directory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $destinationParent = Split-Path -Parent $Destination
    Ensure-Directory $destinationParent

    if ($DryRun) {
        Write-Host "DRY RUN replace dir $Destination from $Source"
        return
    }

    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    Write-Host "Copied directory $Destination"
}

function Test-SkillFrontmatter {
    param([Parameter(Mandatory = $true)][string]$SkillFile)

    $lines = Get-Content -LiteralPath $SkillFile -Encoding UTF8
    if (-not $lines -or $lines[0].Trim() -ne "---") {
        throw "Invalid skill frontmatter in ${SkillFile}: first line must be '---'."
    }

    $closingIndex = -1
    $maxHeaderLines = [Math]::Min($lines.Count, 20)
    for ($i = 1; $i -lt $maxHeaderLines; $i++) {
        if ($lines[$i].Trim() -eq "---") {
            $closingIndex = $i
            break
        }
    }

    if ($closingIndex -lt 0) {
        throw "Invalid skill frontmatter in ${SkillFile}: closing '---' was not found near the top of the file."
    }

    $fields = @{}
    for ($i = 1; $i -lt $closingIndex; $i++) {
        $line = $lines[$i].Trim()
        if (-not $line) {
            continue
        }

        if ($line -notmatch "^([A-Za-z_][A-Za-z0-9_-]*):\s*(.+)$") {
            $lineNumber = $i + 1
            throw "Invalid skill frontmatter in ${SkillFile}: line $lineNumber is not a simple 'key: value' pair."
        }

        $key = $Matches[1]
        $value = $Matches[2].Trim()
        if ($value.Contains(":") -and -not ($value.StartsWith('"') -or $value.StartsWith("'"))) {
            $lineNumber = $i + 1
            throw "Invalid skill frontmatter in ${SkillFile}: line $lineNumber contains ':' in an unquoted value."
        }

        $fields[$key] = $value
    }

    foreach ($requiredField in @("name", "description")) {
        if (-not $fields.ContainsKey($requiredField)) {
            throw "Invalid skill frontmatter in ${SkillFile}: '$requiredField' is required."
        }
    }
}

$sourceRoot = Resolve-SourcePath $SourcePath

if (-not $CodexHome) {
    $CodexHome = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex"
}

$codexHomeFull = Get-FullPath $CodexHome
$skillsHome = Join-Path $codexHomeFull "skills"

Ensure-Directory $codexHomeFull

foreach ($entry in Get-ChildItem -LiteralPath $sourceRoot -Force) {
    if (-not $entry.PSIsContainer) {
        continue
    }

    $skillFile = Join-Path $entry.FullName "SKILL.md"
    if (Test-Path -LiteralPath $skillFile -PathType Leaf) {
        Test-SkillFrontmatter $skillFile
    }
}

$syncedItems = 0
foreach ($entry in Get-ChildItem -LiteralPath $sourceRoot -Force) {
    if ($entry.PSIsContainer) {
        $skillFile = Join-Path $entry.FullName "SKILL.md"
        if (Test-Path -LiteralPath $skillFile -PathType Leaf) {
            $destination = Join-Path $skillsHome $entry.Name
            Sync-Directory $entry.FullName $destination
        }
        else {
            $destination = Join-Path $codexHomeFull $entry.Name
            Sync-Directory $entry.FullName $destination
        }
    }
    else {
        $destination = Join-Path $codexHomeFull $entry.Name
        Sync-File $entry.FullName $destination
    }

    $syncedItems += 1
}

Write-Host "Done. Synced $syncedItems item(s) from $sourceRoot to $codexHomeFull."
