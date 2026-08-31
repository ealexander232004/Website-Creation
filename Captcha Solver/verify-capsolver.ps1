[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$envPath = Join-Path $PSScriptRoot 'capsolver.env'
if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
    throw 'capsolver.env is missing. Run build-config.ps1 first.'
}

$line = Get-Content -LiteralPath $envPath |
    Where-Object { $_ -match '^\s*CAPSOLVER_API_KEY\s*=' } |
    Select-Object -First 1
$apiKey = if ($line) { ($line -split '=', 2)[1].Trim() } else { '' }
if (-not $apiKey) {
    throw 'CAPSOLVER_API_KEY is missing or empty'
}

$payload = @{ clientKey = $apiKey } | ConvertTo-Json -Compress
try {
    $request = @{
        Method = 'Post'
        Uri = 'https://api.capsolver.com/getBalance'
        ContentType = 'application/json'
        Body = $payload
        TimeoutSec = 20
    }
    $response = Invoke-RestMethod @request
}
catch {
    throw 'CapSolver balance request failed; the API key was not printed.'
}

if ($response.errorId -and [int] $response.errorId -ne 0) {
    $code = if ($response.errorCode) { $response.errorCode } else { 'UNKNOWN_ERROR' }
    throw "CapSolver rejected the request: $code"
}

Write-Host 'CapSolver API key: valid'
Write-Host "Account balance: $($response.balance)"
