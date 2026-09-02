[CmdletBinding()]
param(
    [Parameter()]
    [int] $TimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$proxyFile = Join-Path $PSScriptRoot 'proxy-urls.txt'
if (-not (Test-Path -LiteralPath $proxyFile)) {
    throw "proxy-urls.txt is missing. Run build-proxy-files.ps1 first."
}

$proxyUrls = @(Get-Content -LiteralPath $proxyFile | Where-Object { $_.Trim() })
if ($proxyUrls.Count -lt 1) {
    throw "Expected at least 1 proxy URL; found $($proxyUrls.Count)."
}

$results = for ($index = 0; $index -lt $proxyUrls.Count; $index++) {
    $proxyUrl = $proxyUrls[$index]
    $port = ([Uri] $proxyUrl).Port
    try {
        $ip = (& curl.exe --silent --show-error --fail --max-time $TimeoutSeconds `
            --proxy $proxyUrl https://ip.oxylabs.io/).Trim()
        [pscustomobject]@{
            Route = ('proxy-{0:D2}' -f ($index + 1))
            Port = $port
            PublicIP = $ip
            Status = 'OK'
        }
    }
    catch {
        [pscustomobject]@{
            Route = ('proxy-{0:D2}' -f ($index + 1))
            Port = $port
            PublicIP = ''
            Status = 'FAILED'
        }
    }
}

$results | Format-Table -AutoSize
$successfulIps = @($results | Where-Object Status -eq 'OK' | Select-Object -ExpandProperty PublicIP)
$distinctCount = @($successfulIps | Sort-Object -Unique).Count
Write-Host "Successful routes: $($successfulIps.Count)/$($proxyUrls.Count); distinct public IPs: $distinctCount"

if ($successfulIps.Count -ne $proxyUrls.Count -or $distinctCount -ne $proxyUrls.Count) {
    exit 1
}

