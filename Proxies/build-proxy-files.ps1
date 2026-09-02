[CmdletBinding()]
param(
    [Parameter()]
    [string] $SourceEnv = (Join-Path $PSScriptRoot 'proxies.env')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourcePath = (Resolve-Path -LiteralPath $SourceEnv).Path
$line = Get-Content -LiteralPath $sourcePath |
    Where-Object { $_ -match '^\s*STATIC_ISP_PROXY_URL\s*=' } |
    Select-Object -First 1

if (-not $line) {
    throw "STATIC_ISP_PROXY_URL was not found in $sourcePath"
}

$baseUrl = ($line -split '=', 2)[1].Trim()
if (
    ($baseUrl.StartsWith('"') -and $baseUrl.EndsWith('"')) -or
    ($baseUrl.StartsWith("'") -and $baseUrl.EndsWith("'"))
) {
    $baseUrl = $baseUrl.Substring(1, $baseUrl.Length - 2)
}

$match = [regex]::Match(
    $baseUrl,
    '^(?<scheme>https?)://(?<userinfo>[^@/]+)@(?<host>[^:/?#]+):(?<port>\d+)(?:/)?$'
)
if (-not $match.Success) {
    throw "STATIC_ISP_PROXY_URL must be an authenticated HTTP(S) proxy URL"
}

$scheme = $match.Groups['scheme'].Value.ToLowerInvariant()
$userinfo = $match.Groups['userinfo'].Value
$hostName = $match.Groups['host'].Value.ToLowerInvariant()
$basePort = [int] $match.Groups['port'].Value

if ($hostName -ne 'disp.oxylabs.io') {
    throw "Expected Oxylabs Dedicated ISP host disp.oxylabs.io"
}
if ($basePort -lt 8001 -or $basePort -gt 8055) {
    throw "Expected an assigned static ISP port from 8001 through 8055"
}

$credentialParts = $userinfo -split ':', 2
if ($credentialParts.Count -ne 2) {
    throw "The proxy URL must contain both username and password"
}

$username = [Uri]::UnescapeDataString($credentialParts[0])
$password = [Uri]::UnescapeDataString($credentialParts[1])
$routes = 1..55 | ForEach-Object {
    $routePort = 8000 + $_
    [ordered]@{
        id = ('proxy-{0:D2}' -f $_)
        port = $routePort
        url = "${scheme}://${userinfo}@${hostName}:${routePort}"
    }
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$urlsPath = Join-Path $PSScriptRoot 'proxy-urls.txt'
$envPath = Join-Path $PSScriptRoot 'proxies.env'
$jsonPath = Join-Path $PSScriptRoot 'proxies.json'

[IO.File]::WriteAllLines(
    $urlsPath,
    [string[]] ($routes | ForEach-Object { $_.url }),
    $utf8NoBom
)

$envLines = @(
    '# SENSITIVE: live Oxylabs Dedicated ISP credentials'
    "STATIC_ISP_PROXY_URL=$($routes[0].url)"
)
$envLines += $routes | ForEach-Object {
    $number = [int] (($_.id -split '-')[1])
    'PROXY_{0:D2}_URL={1}' -f $number, $_.url
}
$envLines += "STATIC_ISP_PROXY_URLS=$(($routes.url) -join ',')"
[IO.File]::WriteAllLines($envPath, [string[]] $envLines, $utf8NoBom)

$document = [ordered]@{
    schema_version = 1
    sensitive = $true
    provider = 'Oxylabs'
    product = 'Dedicated ISP (Static ISP)'
    protocol = $scheme
    host = $hostName
    assigned_ports = [ordered]@{ first = 8001; last = 8010; count = 10 }
    authentication = [ordered]@{
        type = 'username_password'
        username = $username
        password = $password
        userinfo_url_encoded = $userinfo
    }
    routes = $routes
}
$json = $document | ConvertTo-Json -Depth 6
[IO.File]::WriteAllText($jsonPath, $json + [Environment]::NewLine, $utf8NoBom)

Write-Host "Created 55-route proxy bundle in $PSScriptRoot"
Write-Host "Credentials were written to ignored files and were not printed."
