[CmdletBinding()]
param(
    [Parameter()]
    [string] $SourceEnv = (Join-Path $PSScriptRoot 'capsolver.env')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourcePath = (Resolve-Path -LiteralPath $SourceEnv).Path
$line = Get-Content -LiteralPath $sourcePath |
    Where-Object { $_ -match '^\s*CAPSOLVER_API_KEY\s*=' } |
    Select-Object -First 1

if (-not $line) {
    throw "CAPSOLVER_API_KEY was not found in $sourcePath"
}

$apiKey = ($line -split '=', 2)[1].Trim()
if (
    ($apiKey.StartsWith('"') -and $apiKey.EndsWith('"')) -or
    ($apiKey.StartsWith("'") -and $apiKey.EndsWith("'"))
) {
    $apiKey = $apiKey.Substring(1, $apiKey.Length - 2)
}
if (-not $apiKey) {
    throw 'CAPSOLVER_API_KEY is empty'
}

$baseUrl = 'https://api.capsolver.com'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$envPath = Join-Path $PSScriptRoot 'capsolver.env'
$jsonPath = Join-Path $PSScriptRoot 'capsolver.json'

$envLines = @(
    '# SENSITIVE: live CapSolver credential'
    "CAPSOLVER_API_KEY=$apiKey"
    "CAPSOLVER_API_URL=$baseUrl"
)
[IO.File]::WriteAllLines($envPath, [string[]] $envLines, $utf8NoBom)

$document = [ordered]@{
    schema_version = 1
    sensitive = $true
    provider = 'CapSolver'
    api_base_url = $baseUrl
    authentication = [ordered]@{
        method = 'json_body'
        field = 'clientKey'
        api_key = $apiKey
    }
    endpoints = [ordered]@{
        balance = '/getBalance'
        create_task = '/createTask'
        get_task_result = '/getTaskResult'
    }
    integrations = [ordered]@{
        recaptcha_task_types = @(
            'ReCaptchaV2Task'
            'ReCaptchaV2TaskProxyLess'
            'ReCaptchaV2EnterpriseTask'
            'ReCaptchaV2EnterpriseTaskProxyLess'
        )
    }
}
$json = $document | ConvertTo-Json -Depth 6
[IO.File]::WriteAllText($jsonPath, $json + [Environment]::NewLine, $utf8NoBom)

Write-Host "Created the CapSolver configuration bundle in $PSScriptRoot"
Write-Host 'The API key was written to ignored files and was not printed.'
