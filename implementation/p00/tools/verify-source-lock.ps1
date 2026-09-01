[CmdletBinding()]
param(
    [switch]$VerifyRemote,

    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

if (-not ('System.Net.Http.HttpClient' -as [type])) {
    Add-Type -AssemblyName System.Net.Http
}

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$lockPath = Join-Path $projectRoot 'implementation\p00\source-lock.json'
$archiveRoot = Join-Path $projectRoot 'implementation\p00\source-archive\original'
$lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json

function Get-Sha256Lower {
    param([Parameter(Mandatory)][string]$Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-BytesSha256Lower {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $algorithm.ComputeHash($Bytes)
        ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

$archiveByHash = @{}
foreach ($file in Get-ChildItem -LiteralPath $archiveRoot -Recurse -File) {
    $hash = Get-Sha256Lower -Path $file.FullName
    if ($archiveByHash.ContainsKey($hash)) {
        throw "Duplicate archive hash prevents unambiguous source mapping: $hash"
    }
    $archiveByHash[$hash] = $file.FullName
}

$installedRoot = 'C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin'
$installedPaths = @{
    'local-hwp-2020-executable' = Join-Path $installedRoot 'Hwp.exe'
    'local-hwp-2020-help-en-us' = Join-Path $installedRoot 'Resource\Hwp\Help\en-US\Hwp.chm'
    'local-hwp-2020-help-ko-kr' = Join-Path $installedRoot 'Resource\Hwp\Help\ko-KR\Hwp.chm'
    'local-hwp-2020-automation-dll' = Join-Path $installedRoot 'HwpAutomation.dll'
    'local-hwp-2020-automation-tlb' = Join-Path $installedRoot 'HwpAutomation.tlb'
    'local-hwp-2020-control-tlb' = Join-Path $installedRoot 'HwpCtrl.tlb'
}

$httpClient = $null
if ($VerifyRemote) {
    $httpClient = [System.Net.Http.HttpClient]::new()
    $httpClient.Timeout = [TimeSpan]::FromSeconds(30)
    $httpClient.DefaultRequestHeaders.UserAgent.ParseAdd('hwpx-agent-p00-source-verifier/1.0')
}

try {
    $results = foreach ($source in $lock.sources) {
        $localPath = $null
        $pathKind = 'unresolved'

        if ($source.origin.StartsWith('https://', [System.StringComparison]::OrdinalIgnoreCase)) {
            $localPath = $archiveByHash[$source.sha256]
            $pathKind = 'archived_remote_original'
        }
        elseif ($source.origin.StartsWith('implementation/', [System.StringComparison]::OrdinalIgnoreCase)) {
            $localPath = Join-Path $projectRoot $source.origin
            $pathKind = 'project_evidence'
        }
        elseif ($installedPaths.ContainsKey($source.source_id)) {
            $localPath = $installedPaths[$source.source_id]
            $pathKind = 'installed_fingerprint_only'
        }

        $localExists = $localPath -and (Test-Path -LiteralPath $localPath -PathType Leaf)
        $localHash = if ($localExists) { Get-Sha256Lower -Path $localPath } else { $null }
        $localMatch = $localExists -and $localHash -eq $source.sha256

        $remoteHash = $null
        $remoteBytes = $null
        $remoteState = if ($VerifyRemote -and $source.origin.StartsWith('https://')) { 'not_run' } else { 'not_requested' }
        $remoteError = $null
        if ($VerifyRemote -and $source.origin.StartsWith('https://')) {
            try {
                $revalidationMode = if ($source.revalidation -and $source.revalidation.mode) {
                    $source.revalidation.mode
                }
                else {
                    'byte_exact'
                }
                $remoteMethod = if ($source.revalidation -and $source.revalidation.method) {
                    $source.revalidation.method.ToUpperInvariant()
                }
                else {
                    'GET'
                }
                if ($remoteMethod -eq 'POST') {
                    $contentType = if ($source.revalidation.content_type) {
                        $source.revalidation.content_type
                    }
                    else {
                        'application/x-www-form-urlencoded'
                    }
                    $requestContent = [System.Net.Http.StringContent]::new(
                        [string]$source.revalidation.body,
                        [System.Text.Encoding]::UTF8,
                        $contentType
                    )
                    try {
                        $response = $httpClient.PostAsync([Uri]$source.origin, $requestContent).GetAwaiter().GetResult()
                        try {
                            $response.EnsureSuccessStatusCode() | Out-Null
                            $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
                        }
                        finally {
                            $response.Dispose()
                        }
                    }
                    finally {
                        $requestContent.Dispose()
                    }
                }
                elseif ($remoteMethod -eq 'GET') {
                    $bytes = $httpClient.GetByteArrayAsync([Uri]$source.origin).GetAwaiter().GetResult()
                }
                else {
                    throw "Unsupported remote revalidation method: $remoteMethod"
                }
                $remoteBytes = $bytes.Length
                $remoteHash = Get-BytesSha256Lower -Bytes $bytes
                if ($revalidationMode -eq 'semantic') {
                    $remoteText = [System.Text.Encoding]::UTF8.GetString($bytes)
                    $missingMarkers = @(
                        $source.revalidation.required_markers |
                            Where-Object { -not $remoteText.Contains($_) }
                    )
                    $remoteState = if ($missingMarkers.Count -eq 0) { 'semantic_match' } else { 'semantic_changed' }
                    if ($missingMarkers.Count -gt 0) {
                        $remoteError = "Missing semantic markers: $($missingMarkers -join ', ')"
                    }
                }
                else {
                    $remoteState = if ($remoteHash -eq $source.sha256) { 'match' } else { 'changed' }
                }
            }
            catch {
                $remoteState = 'fetch_failed'
                $remoteError = $_.Exception.Message
            }
        }

        [pscustomobject]@{
            source_id = $source.source_id
            path_kind = $pathKind
            local_exists = [bool]$localExists
            local_match = [bool]$localMatch
            local_sha256 = $localHash
            expected_sha256 = $source.sha256
            remote_state = $remoteState
            remote_sha256 = $remoteHash
            remote_bytes = $remoteBytes
            error = $remoteError
        }
    }
}
finally {
    if ($httpClient) {
        $httpClient.Dispose()
    }
}

$localFailures = @($results | Where-Object { -not $_.local_match })
$remoteFailures = if ($VerifyRemote) {
    @($results | Where-Object { $_.remote_state -in @('changed', 'semantic_changed', 'fetch_failed') })
}
else {
    @()
}

$report = [pscustomobject]@{
    schema_version = 'hwpx-agent.source-lock-verification/v1'
    checked_at = (Get-Date).ToString('o')
    source_lock_id = $lock.source_lock_id
    source_count = @($results).Count
    local_match_count = @($results | Where-Object local_match).Count
    remote_verification_requested = [bool]$VerifyRemote
    remote_match_count = @($results | Where-Object { $_.remote_state -in @('match', 'semantic_match') }).Count
    local_failure_count = $localFailures.Count
    remote_failure_count = $remoteFailures.Count
    state = if ($localFailures.Count -eq 0 -and $remoteFailures.Count -eq 0) { 'pass' } else { 'fail' }
    results = $results
}

$reportJson = $report | ConvertTo-Json -Depth 5
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $outputParent = Split-Path -Parent $OutputPath
    if ([string]::IsNullOrWhiteSpace($outputParent)) {
        $outputParent = (Get-Location).Path
    }
    if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
        New-Item -ItemType Directory -Path $outputParent | Out-Null
    }
    $resolvedOutput = Join-Path (Resolve-Path -LiteralPath $outputParent).Path (Split-Path -Leaf $OutputPath)
    if (Test-Path -LiteralPath $resolvedOutput) {
        throw "Refusing to overwrite source-lock verification evidence: $resolvedOutput"
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($resolvedOutput, $reportJson, $encoding)
}
$reportJson
if ($report.state -ne 'pass') {
    exit 1
}
