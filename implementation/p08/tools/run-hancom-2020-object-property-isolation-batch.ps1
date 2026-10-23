[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [ValidateRange(10, 60)][int]$PerFeatureTimeoutSeconds = 15,
    [string[]]$FeatureIds = @(),
    [string]$FeatureIdsCsv = '',
    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'P08_OBJECT_PROPERTY_ISOLATION_BATCH'
$defaultFeatures = @(
    'OBJ-015', 'OBJ-016', 'OBJ-017', 'OBJ-018', 'OBJ-019', 'OBJ-020',
    'OBJ-021', 'OBJ-022', 'OBJ-023', 'OBJ-025', 'OBJ-032', 'OBJ-034', 'OBJ-047'
)
$allowedFeatures = @(
    'OBJ-001', 'OBJ-002', 'OBJ-003', 'OBJ-007', 'OBJ-010', 'OBJ-012', 'OBJ-014',
    'OBJ-015', 'OBJ-016', 'OBJ-017', 'OBJ-018', 'OBJ-019', 'OBJ-020',
    'OBJ-021', 'OBJ-022', 'OBJ-023', 'OBJ-024', 'OBJ-025', 'OBJ-027',
    'OBJ-028', 'OBJ-029', 'OBJ-030', 'OBJ-031', 'OBJ-032', 'OBJ-034',
    'OBJ-035', 'OBJ-036', 'OBJ-037', 'OBJ-039', 'OBJ-040', 'OBJ-041', 'OBJ-042',
    'OBJ-043', 'OBJ-047', 'OBJ-048'
)
[string[]]$csvFeatures = if ([string]::IsNullOrWhiteSpace($FeatureIdsCsv)) {
    @()
} else {
    @($FeatureIdsCsv.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
if ($FeatureIds.Count -ne 0 -and $csvFeatures.Count -ne 0) {
    throw ($errorPrefix + '_FEATURE_IDS_AMBIGUOUS')
}
[string[]]$features = if ($csvFeatures.Count -ne 0) {
    @($csvFeatures)
} elseif ($FeatureIds.Count -ne 0) {
    @($FeatureIds)
} else { $defaultFeatures }
if ($features.Count -eq 0 -or $features.Count -ne @($features | Select-Object -Unique).Count -or
    @($features | Where-Object { $allowedFeatures -cnotcontains $_ }).Count -ne 0) {
    throw ($errorPrefix + '_FEATURE_IDS')
}
$expectedOverlaySha256 = '8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f'
$expectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    if ($Value.Contains('"')) { throw ($errorPrefix + '_ARGUMENT_QUOTE') }
    return '"' + $Value + '"'
}
function Write-NewUtf8File {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Content)
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}
function Add-Progress {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][object]$Value)
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(
        (($Value | ConvertTo-Json -Compress -Depth 5) + "`n")
    )
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::Append, [IO.FileAccess]::Write, [IO.FileShare]::Read
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}
function Stop-OwnedHwpProcesses {
    param([Parameter(Mandatory)][datetime]$StartedAt, [Parameter(Mandatory)][int]$SessionId)
    $result = [ordered]@{ cleaned = 0; refused = 0; errors = 0; remaining_owned = 0 }
    foreach ($record in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
            -ErrorAction SilentlyContinue)) {
        $process = Get-Process -Id ([int]$record.ProcessId) -ErrorAction SilentlyContinue
        if ($null -eq $process -or $process.SessionId -ne $SessionId) {
            $result.refused += 1
            continue
        }
        try { $createdAt = $process.StartTime } catch { $result.refused += 1; continue }
        $path = [string]$record.ExecutablePath
        $owned = $createdAt -ge $StartedAt.AddSeconds(-2) -and
            -not [string]::IsNullOrWhiteSpace($path) -and
            (Test-Path -LiteralPath $path -PathType Leaf) -and
            (Get-Sha256File -Path $path) -ceq $expectedExecutableSha256 -and
            [string]$record.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $owned) { $result.refused += 1; continue }
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
            $result.cleaned += 1
        }
        catch {
            if ($null -ne (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
                $result.errors += 1
                $result.remaining_owned += 1
            }
        }
    }
    return $result
}
function Wait-NoHwpProcess {
    param([ValidateRange(1, 15)][int]$TimeoutSeconds = 10)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
                -ErrorAction SilentlyContinue).Count -eq 0) {
            return $true
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    return $false
}

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path.TrimEnd('\')
$privateRoot = Join-Path $root 'implementation\p08\evidence\private'
$overlayPath = Join-Path $root (
    'implementation\p02\evidence\bindings\p08-object-automation-binding-overlay.2020.v1.json'
)
$childPath = Join-Path $PSScriptRoot 'run-hancom-2020-object-property-isolation-child.ps1'
if ((Get-Sha256File -Path $overlayPath) -cne $expectedOverlaySha256 -or
    -not (Test-Path -LiteralPath $childPath -PathType Leaf)) {
    throw ($errorPrefix + '_INPUT_IDENTITY')
}
$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if (-not $run.StartsWith($privateRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $run) -cnotmatch '^p08-25-object-property-isolation-[a-z0-9-]{1,80}$') {
    throw ($errorPrefix + '_RUN_DIRECTORY')
}
if (Test-Path -LiteralPath $run) {
    if (@(Get-ChildItem -LiteralPath $run -Force).Count -ne 0) {
        throw ($errorPrefix + '_RUN_DIRECTORY_NOT_EMPTY')
    }
}
else { [void][IO.Directory]::CreateDirectory($run) }
$configuration = [ordered]@{
    state = 'configuration_valid'
    feature_count = $features.Count
    feature_ids = $features
    isolation = 'one_x86_sta_process_and_one_unsaved_document_per_feature'
    hwp_file_open_allowed = $true
    hwp_file_open_scope = 'project_owned_p08_20_readback_fixtures_only'
    document_save_allowed = $false
    candidate_execute_allowed = $true
    per_feature_timeout_seconds = $PerFeatureTimeoutSeconds
    overlay_sha256 = $expectedOverlaySha256
    child_sha256 = Get-Sha256File -Path $childPath
}
if ($ValidateConfigurationOnly) { $configuration | ConvertTo-Json -Depth 5; exit 0 }
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}

$progressPath = Join-Path $run 'progress.jsonl'
$receiptPath = Join-Path $run 'runtime-receipt.json'
$powershell = Join-Path ([Environment]::GetFolderPath(
    [Environment+SpecialFolder]::SystemX86
)) 'WindowsPowerShell\v1.0\powershell.exe'
$sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
$results = @()
$batchStartedAt = Get-Date
foreach ($featureId in $features) {
    if (-not (Wait-NoHwpProcess -TimeoutSeconds 10)) {
        throw ($errorPrefix + '_PREEXISTING_HWP_BETWEEN_FEATURES')
    }
    Add-Progress -Path $progressPath -Value ([ordered]@{
        event = 'feature_start'; feature_id = $featureId
        completed = $results.Count; total = $features.Count
    })
    $tracePath = Join-Path $run ($featureId.ToLowerInvariant() + '-trace.private.json')
    $arguments = @(
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA', '-File', $childPath,
        '-FeatureId', $featureId, '-OverlayPath', $overlayPath,
        '-ExpectedOverlaySha256', $expectedOverlaySha256, '-TracePath', $tracePath
    )
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $powershell
    $startInfo.Arguments = (($arguments | ForEach-Object {
        ConvertTo-ProcessArgument -Value ([string]$_)
    }) -join ' ')
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $child = [Diagnostics.Process]::new()
    $child.StartInfo = $startInfo
    $startedAt = Get-Date
    [void]$child.Start()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()
    $exited = $child.WaitForExit($PerFeatureTimeoutSeconds * 1000)
    if (-not $exited) { try { $child.Kill(); $child.WaitForExit() } catch { } }
    Start-Sleep -Milliseconds 1000
    $cleanup = Stop-OwnedHwpProcesses -StartedAt $startedAt -SessionId $sessionId
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $trace = if (Test-Path -LiteralPath $tracePath -PathType Leaf) {
        Get-Content -LiteralPath $tracePath -Raw -Encoding UTF8 | ConvertFrom-Json
    } else { $null }
    $result = [ordered]@{
        feature_id = $featureId
        state = if ($exited -and $child.ExitCode -eq 0 -and $null -ne $trace -and
            [string]$trace.state -ceq 'pass' -and $cleanup.errors -eq 0 -and
            $cleanup.remaining_owned -eq 0) { 'pass' } elseif (-not $exited) {
            'timed_out'
        } elseif ($null -ne $trace) { [string]$trace.state } else { 'child_failed' }
        child_exit_code = if ($exited) { $child.ExitCode } else { $null }
        timed_out = -not $exited
        duration_seconds = [math]::Round(((Get-Date) - $startedAt).TotalSeconds, 3)
        trace_sha256 = if ($null -ne $trace) { Get-Sha256File -Path $tracePath } else { $null }
        effect_observed = if ($null -ne $trace) { [bool]$trace.effect_observed } else { $false }
        undo_semantic_verified = if ($null -ne $trace) {
            [bool]$trace.undo_semantic_verified
        } else { $false }
        stderr = $stderr.Trim()
        cleanup = $cleanup
    }
    $results += $result
    Add-Progress -Path $progressPath -Value ([ordered]@{
        event = 'feature_complete'; feature_id = $featureId; state = $result.state
        completed = $results.Count; total = $features.Count
    })
    if ($cleanup.errors -ne 0 -or $cleanup.remaining_owned -ne 0) { break }
}
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p08-object-property-isolation-batch-receipt/v1'
    state = if ($results.Count -eq $features.Count -and
        @($results | Where-Object { $_.state -cne 'pass' }).Count -eq 0) {
        'pass'
    } else { 'completed_with_failures' }
    configuration = $configuration
    completed_feature_count = $results.Count
    passed_feature_count = @($results | Where-Object { $_.state -ceq 'pass' }).Count
    timed_out_feature_count = @($results | Where-Object { $_.timed_out }).Count
    duration_seconds = [math]::Round(((Get-Date) - $batchStartedAt).TotalSeconds, 3)
    progress_sha256 = Get-Sha256File -Path $progressPath
    results = $results
}
$json = $receipt | ConvertTo-Json -Depth 8
Write-NewUtf8File -Path $receiptPath -Content ($json + "`n")
$json
if ($receipt.state -cne 'pass') { exit 1 }
