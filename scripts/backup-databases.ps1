<#
.SYNOPSIS
    Automated PostgreSQL backup to Google Drive via Docker and rclone.

.DESCRIPTION
    Creates atomic, compressed custom-format dumps (pg_dump -Fc) of PostgreSQL
    databases running in the scraper container and uploads them to Google Drive.
    Supports retention rotation and optional local disk cleanup.

.PARAMETER Databases
    Array of database names to dump. Defaults to 'lead_warehouse' and 'gmaps_scraper'.

.PARAMETER ContainerName
    Name of the Docker container running PostgreSQL. Defaults to 'googlemapsscraping-postgres-1'.

.PARAMETER User
    PostgreSQL user for pg_dump. Defaults to 'gmaps_scraper'.

.PARAMETER OutputDir
    Local destination directory for dump archives. Defaults to 'backups' in workspace root.

.PARAMETER RemoteDir
    Destination folder on Google Drive. Defaults to 'gdrive:PostgresBackups'.

.PARAMETER CleanLocal
    If specified, deletes the local .dump file after successful upload to conserve disk space.

.PARAMETER RetentionDays
    Number of days to keep remote backups on Google Drive. Older files are pruned. Default is 30. Set to 0 to disable pruning.

.EXAMPLE
    .\scripts\backup-databases.ps1
    Dumps all databases, compresses them, and uploads to Google Drive.

.EXAMPLE
    .\scripts\backup-databases.ps1 -CleanLocal -RetentionDays 14
    Dumps databases, uploads to Google Drive, prunes files older than 14 days, and removes local copies.
#>

[CmdletBinding()]
param (
    [string[]]$Databases = @('lead_warehouse', 'gmaps_scraper'),
    [string]$ContainerName = 'googlemapsscraping-postgres-1',
    [string]$User = 'gmaps_scraper',
    [string]$OutputDir = '',
    [string]$RemoteDir = 'gdrive:PostgresBackups',
    [switch]$CleanLocal,
    [int]$RetentionDays = 30
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

function Write-Warn {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [WARN] $Message" -ForegroundColor Yellow
}

# 1. Validate environment
Write-Step "Checking prerequisites..."

$rcloneCmd = Get-Command rclone -ErrorAction SilentlyContinue
if (-not $rcloneCmd) {
    throw "rclone is not found in PATH. Please install rclone or ensure it is in your system PATH."
}

$remoteCheck = rclone listremotes 2>&1
if ($remoteCheck -notmatch 'gdrive:') {
    throw "rclone remote 'gdrive:' is not configured. Run 'rclone config' to set up Google Drive."
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $scriptDir) { $scriptDir = '.' }
    $OutputDir = Join-Path $scriptDir '..\backups'
}
$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
$containerRunning = docker ps --filter "name=$ContainerName" --filter "status=running" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Step "Container '$ContainerName' is not running. Attempting to start with docker compose..."
    $composeDir = Join-Path $PSScriptRoot '..\Google Maps Scraping'
    Push-Location $composeDir
    try {
        docker compose up -d postgres
    } finally {
        Pop-Location
    }
    Start-Sleep -Seconds 3
}

$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
if (-not (Test-Path $resolvedOutputDir)) {
    New-Item -ItemType Directory -Path $resolvedOutputDir -Force | Out-Null
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$results = [System.Collections.Generic.List[PSObject]]::new()
$totalSw = [System.Diagnostics.Stopwatch]::StartNew()

foreach ($db in $Databases) {
    Write-Host ""
    Write-Step "Processing database '$db'..."
    
    $dumpFilename = "${db}_${timestamp}.dump"
    $containerDumpPath = "/tmp/$dumpFilename"
    $localDumpPath = Join-Path $resolvedOutputDir $dumpFilename
    $remoteFilePath = "$RemoteDir/$dumpFilename"

    # Step A: Dump inside container (compressed custom format -Fc)
    $dumpSw = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Step "  -> Running pg_dump -Fc inside container..."
    $dumpOutput = docker exec $ContainerName pg_dump -U $User -Fc -d $db -f $containerDumpPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        docker exec $ContainerName rm -f $containerDumpPath 2>&1 | Out-Null
        throw "pg_dump failed for database '$db': $dumpOutput"
    }
    $dumpSw.Stop()

    # Step B: Copy dump from container to local disk
    Write-Step "  -> Copying dump to local staging directory..."
    docker cp "$($ContainerName):$containerDumpPath" $localDumpPath | Out-Null
    docker exec $ContainerName rm -f $containerDumpPath | Out-Null

    if (-not (Test-Path $localDumpPath)) {
        throw "Failed to copy dump file to local path '$localDumpPath'."
    }

    $fileInfo = Get-Item $localDumpPath
    $sizeMb = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Success "  -> Local dump ready: $sizeMb MB in $($dumpSw.Elapsed.TotalSeconds.ToString('F1'))s"

    # Step C: Upload to Google Drive via rclone
    $uploadSw = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Step "  -> Uploading to Google Drive ($RemoteDir)..."
    $rcloneOut = rclone copyto $localDumpPath $remoteFilePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "rclone upload failed: $rcloneOut"
    }
    $uploadSw.Stop()

    # Step D: Verify remote file
    $verifyOut = rclone lsf $remoteFilePath 2>&1
    if ($verifyOut -notmatch [regex]::Escape($dumpFilename)) {
        throw "Verification failed: '$dumpFilename' not found on remote '$RemoteDir'."
    }
    Write-Success "  -> Upload verified in $($uploadSw.Elapsed.TotalSeconds.ToString('F1'))s"

    # Step E: Clean local file if requested
    if ($CleanLocal) {
        Remove-Item $localDumpPath -Force
        Write-Step "  -> Local staging file removed (-CleanLocal)."
    }

    $results.Add([PSCustomObject]@{
        Database = $db
        SizeMB = $sizeMb
        DumpTimeSec = [math]::Round($dumpSw.Elapsed.TotalSeconds, 1)
        UploadTimeSec = [math]::Round($uploadSw.Elapsed.TotalSeconds, 1)
        RemotePath = $remoteFilePath
        LocalPath = if ($CleanLocal) { '<removed>' } else { $localDumpPath }
        Status = 'Success'
    })
}

# 3. Apply retention policy if enabled
if ($RetentionDays -gt 0) {
    Write-Host ""
    Write-Step "Applying retention policy (deleting backups on Google Drive older than $RetentionDays days)..."
    $pruneAge = "${RetentionDays}d"
    $pruneOut = rclone delete --min-age $pruneAge $RemoteDir 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Retention policy applied."
    } else {
        Write-Warn "Retention pruning returned an advisory notice: $pruneOut"
    }
}

$totalSw.Stop()

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "                  BACKUP SUMMARY REPORT                           " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green

$results | Format-Table -Property Database, SizeMB, DumpTimeSec, UploadTimeSec, RemotePath -AutoSize

Write-Success "All databases backed up successfully in $([math]::Round($totalSw.Elapsed.TotalSeconds, 1))s."
