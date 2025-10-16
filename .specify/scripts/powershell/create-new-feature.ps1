#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create a new feature specification with Speckit infrastructure
.DESCRIPTION
    Creates a new git branch, initializes spec files, and outputs JSON for integration
.PARAMETER Description
    Feature description for the specification
.PARAMETER ShortName
    Short name for the branch (2-4 words, kebab-case)
.PARAMETER AsJson
    Output results as JSON
#>

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$Description,

    [Parameter(Mandatory = $true)]
    [string]$ShortName,

    [switch]$AsJson
)

# Configuration
$RepoRoot = (Get-Location).Path
$SpecDir = "$RepoRoot\.specify"
$FeatureDir = "$SpecDir\features\$ShortName"
$SpecFile = "$FeatureDir\spec.md"
$ChecklistDir = "$FeatureDir\checklists"
$ChecklistFile = "$ChecklistDir\requirements.md"
$BranchName = "spec/$ShortName"
$Date = Get-Date -Format "yyyy-MM-dd"

# Ensure directories exist
@($FeatureDir, $ChecklistDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Copy template files
$SpecTemplate = "$SpecDir\templates\spec-template.md"
$ChecklistTemplate = "$SpecDir\templates\checklist-template.md"

if (Test-Path $SpecTemplate) {
    Copy-Item $SpecTemplate $SpecFile -Force
}

if (Test-Path $ChecklistTemplate) {
    Copy-Item $ChecklistTemplate $ChecklistFile -Force
}

# Generate feature name from short name (convert kebab-case to Title Case)
$FeatureName = ($ShortName -split '-' | ForEach-Object { (Get-Culture).TextInfo.ToTitleCase($_) }) -join ' '

# Update spec file with basic information
if (Test-Path $SpecFile) {
    $SpecContent = Get-Content $SpecFile -Raw
    $SpecContent = $SpecContent -replace '\[FEATURE_NAME\]', $FeatureName
    $SpecContent = $SpecContent -replace '\[DATE\]', $Date
    $SpecContent = $SpecContent -replace '\[AUTHOR\]', $env:USERNAME
    Set-Content $SpecFile -Value $SpecContent -Force
}

# Update checklist file
if (Test-Path $ChecklistFile) {
    $ChecklistContent = Get-Content $ChecklistFile -Raw
    $ChecklistContent = $ChecklistContent -replace '\[FEATURE_NAME\]', $FeatureName
    $ChecklistContent = $ChecklistContent -replace '\[DATE\]', $Date
    $ChecklistContent = $ChecklistContent -replace '\[Link to spec.md\]', "[$SpecFile]($SpecFile)"
    Set-Content $ChecklistFile -Value $ChecklistContent -Force
}

# Create git branch
try {
    # Check if branch already exists
    $ExistingBranch = git rev-parse --verify $BranchName 2>$null
    if (-not $ExistingBranch) {
        git checkout -b $BranchName | Out-Null
    } else {
        git checkout $BranchName | Out-Null
    }
} catch {
    Write-Warning "Could not create/checkout git branch: $_"
}

# Prepare output
$Output = @{
    SUCCESS      = $true
    BRANCH_NAME  = $BranchName
    FEATURE_NAME = $FeatureName
    SHORT_NAME   = $ShortName
    SPEC_FILE    = $SpecFile
    CHECKLIST_FILE = $ChecklistFile
    FEATURE_DIR  = $FeatureDir
    DESCRIPTION  = $Description
    CREATED_DATE = $Date
}

# Output as JSON if requested
if ($AsJson) {
    $Output | ConvertTo-Json -Depth 3
} else {
    # Human-readable output
    Write-Host "✅ Feature specification created successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Branch: $BranchName"
    Write-Host "Feature: $FeatureName"
    Write-Host "Spec File: $SpecFile"
    Write-Host "Checklist: $ChecklistFile"
}
