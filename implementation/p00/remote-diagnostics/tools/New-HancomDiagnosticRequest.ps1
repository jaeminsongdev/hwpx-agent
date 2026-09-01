[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Discover', 'Probe')]
    [string]$Mode,

    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9][a-z0-9._-]+$')]
    [string]$ProfileId,

    [ValidateRange(2020, 9999)]
    [int]$MinimumMajorRelease = 2020,

    [int]$ExpectedMajorRelease = 0,

    [string]$ExpectedFileVersion,

    [string]$ExpectedExecutableSha256,

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$CollectorPath = (Join-Path $PSScriptRoot 'Collect-HancomDiagnostics.ps1'),

    [Parameter(Mandatory)]
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ProgId -ne 'HWPFrame.HwpObject.2') {
    throw 'Only the canonical HWPFrame.HwpObject.2 ProgID is accepted.'
}
if ($ExpectedMajorRelease -ne 0 -and $ExpectedMajorRelease -lt $MinimumMajorRelease) {
    throw 'ExpectedMajorRelease must be zero or at least MinimumMajorRelease.'
}
if ($Mode -eq 'Probe') {
    if ($ExpectedMajorRelease -eq 0) {
        throw 'Probe mode requires ExpectedMajorRelease.'
    }
    if ($ExpectedFileVersion -notmatch '^\d+\.\d+\.\d+\.\d+$') {
        throw 'Probe mode requires a four-part ExpectedFileVersion.'
    }
    if ($ExpectedExecutableSha256 -notmatch '^[0-9a-fA-F]{64}$') {
        throw 'Probe mode requires ExpectedExecutableSha256.'
    }
}

$collector = (Resolve-Path -LiteralPath $CollectorPath).Path
$outputParent = Split-Path -Parent $OutputPath
if ([string]::IsNullOrWhiteSpace($outputParent)) {
    $outputParent = (Get-Location).Path
}
if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
    New-Item -ItemType Directory -Path $outputParent | Out-Null
}
$resolvedParent = (Resolve-Path -LiteralPath $outputParent).Path
$outputLeaf = Split-Path -Leaf $OutputPath
$resolvedOutput = Join-Path $resolvedParent $outputLeaf
if (Test-Path -LiteralPath $resolvedOutput) {
    throw "Refusing to overwrite request: $resolvedOutput"
}

$nonceBytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $rng.GetBytes($nonceBytes)
}
finally {
    $rng.Dispose()
}
$nonce = ([System.BitConverter]::ToString($nonceBytes) -replace '-', '').ToLowerInvariant()

$request = [ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-request/v1'
    request_id = [guid]::NewGuid().ToString()
    created_at = (Get-Date).ToString('o')
    challenge_nonce = $nonce
    mode = $Mode.ToLowerInvariant()
    collector_sha256 = (Get-FileHash -LiteralPath $collector -Algorithm SHA256).Hash.ToLowerInvariant()
    target = [ordered]@{
        profile_id = $ProfileId
        minimum_major_release = $MinimumMajorRelease
        expected_major_release = if ($ExpectedMajorRelease -eq 0) { $null } else { [string]$ExpectedMajorRelease }
        expected_file_version = if ([string]::IsNullOrWhiteSpace($ExpectedFileVersion)) { $null } else { $ExpectedFileVersion }
        expected_executable_sha256 = if ([string]::IsNullOrWhiteSpace($ExpectedExecutableSha256)) { $null } else { $ExpectedExecutableSha256.ToLowerInvariant() }
        prog_id = $ProgId
    }
    policy = [ordered]@{
        network_allowed = $false
        ui_automation_allowed = $false
        computer_use_mode = 'screenshot_only'
        user_documents_allowed = $false
        event_log_mode = 'metadata_allowlist'
        crash_dump_mode = 'metadata_only'
    }
}

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($resolvedOutput, ($request | ConvertTo-Json -Depth 8), $encoding)
[pscustomobject]@{
    state = 'created'
    path = $resolvedOutput
    request_id = $request.request_id
    challenge_nonce = $request.challenge_nonce
    collector_sha256 = $request.collector_sha256
} | ConvertTo-Json -Depth 4
