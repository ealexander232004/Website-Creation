<#
.SYNOPSIS
    Restore a PostgreSQL database from a Google Drive or local backup archive.

.DESCRIPTION
    Lists available backup archives on Google Drive, downloads the selected
    dump if needed, and executes pg_restore --clean inside the Docker container.

.PARAMETER Database
    Target database name ('lead_warehouse' or 'gmaps_scraper'). Defaults to 'lead_warehouse'.

.PARAMETER DumpFile
    Specific dump filename (e.g. 'lead_warehouse_20260902_143000.dump'). If omitted, lists available backups.

.PARAMETER ContainerName
    PostgreSQL Docker container name. Defaults to 'googlemapsscraping-postgres-1'.

.PARAMETER User
    PostgreSQL user. Defaults to 'gmaps_scraper'.

.PARAMETER RemoteDir
    Google Drive remote path. Defaults to 'gdrive:PostgresBackups'.

.PARAMETER LocalDir
    Local directory where dump is downloaded/staged. Defaults to 'backups' in workspace root.

.EXAMPLE
    .\scripts\restore-database.ps1 -ListOnly
    Lists all available backup dumps on Google Drive.

.EXAMPLE
    .\scripts\restore-database.ps1 -Database lead_warehouse -DumpFile lead_warehouse_20260902_183000.dump
#>

[CmdletBinding()]
param (
    [string]$Database = 'lead_warehouse',
    [string]$DumpFile,
    [string]$ContainerName = 'googlemapsscraping-postgres-1',
    [string]$User = 'gmaps_scraper',
    [string]$RemoteDir = 'gdrive:PostgresBackups',
    [string]$LocalDir = '',
    [switch]$ListOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [SUCCESS] $Message" -ForegroundColor Green
}

if ($ListOnly -or [string]::IsNullOrWhiteSpace($DumpFile)) {
    Write-Step "Fetching available backups from Google Drive ($RemoteDir)..."
    $files = rclone lsf --format "tsp" $RemoteDir 2>&1
    Write-Host ""
    Write-Host "Available Backups on Google Drive:" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------"
    $files | ForEach-Object { Write-Host "  $_" }
    Write-Host "--------------------------------------------------------"
    if ($ListOnly) { return }
    throw "Specify a -DumpFile from the list above to proceed with restoration."
}

if ([string]::IsNullOrWhiteSpace($LocalDir)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $scriptDir) { $scriptDir = '.' }
    $LocalDir = Join-Path $scriptDir '..\backups'
}
$resolvedLocalDir = [System.IO.Path]::GetFullPath($LocalDir)
if (-not (Test-Path $resolvedLocalDir)) {
    New-Item -ItemType Directory -Path $resolvedLocalDir -Force | Out-Null
}

$localPath = Join-Path $resolvedLocalDir $DumpFile
if (-not (Test-Path $localPath)) {
    Write-Step "Downloading '$DumpFile' from Google Drive ($RemoteDir)..."
    $remoteFile = "$RemoteDir/$DumpFile"
    rclone copyto $remoteFile $localPath
    if (-not (Test-Path $localPath)) {
        throw "Failed to download '$DumpFile' from Google Drive."
    }
    Write-Success "Download complete."
}

Write-Step "Copying dump into PostgreSQL container..."
$containerDump = "/tmp/$DumpFile"
docker cp $localPath "${ContainerName}:${containerDump}"

Write-Step "Executing pg_restore on database '$Database'..."
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$restoreOut = docker exec $ContainerName pg_restore -U $User -d $Database --clean --if-exists --no-owner --no-privileges $containerDump 2>&1
docker exec $ContainerName rm -f $containerDump
$sw.Stop()

Write-Success "Database '$Database' restored successfully in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s."
