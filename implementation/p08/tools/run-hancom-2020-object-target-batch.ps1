[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$RunDirectory,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(300, 7200)][int]$TimeoutSeconds = 3600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$errorPrefix = 'OBJECT_TARGET_BATCH_WRAPPER'
$exactManifestSha256 = '2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    if ($Value.Length -gt 32767) { throw ($errorPrefix + '_ARGUMENT_TOO_LONG') }
    if ($Value.Contains('"')) {
        throw ($errorPrefix + '_PROCESS_ARGUMENT_CONTAINS_QUOTE')
    }
    return '"' + $Value + '"'
}

function Stop-OwnedHancomProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )

    $summary = [ordered]@{ cleaned = 0; refused = 0; errors = 0 }
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
            -ErrorAction SilentlyContinue)) {
        $runtime = Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtime) { continue }
        $processPath = [string]$candidate.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($processPath)) {
            try { $processPath = [string]$runtime.Path } catch { $processPath = '' }
        }
        $createdAt = if ($null -ne $candidate.CreationDate) {
            [datetime]$candidate.CreationDate
        }
        else { [datetime]::MinValue }
        $identityMatches = $false
        if (-not [string]::IsNullOrWhiteSpace($processPath) -and
            (Test-Path -LiteralPath $processPath -PathType Leaf)) {
            try {
                $identityMatches = (Get-Sha256File -Path $processPath) -ceq
                    $ExpectedSha256
            }
            catch { }
        }
        $safeToClean = [int]$candidate.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            $identityMatches -and
            [string]$candidate.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $safeToClean) {
            $summary.refused += 1
            continue
        }
        try {
            Stop-Process -Id $candidate.ProcessId -Force -ErrorAction Stop
            Wait-Process -Id $candidate.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            $summary.cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue)) {
                $summary.cleaned += 1
            }
            else { $summary.errors += 1 }
        }
    }
    return $summary
}

if ($ExpectedFixtureManifestSha256 -cne $exactManifestSha256) {
    throw ($errorPrefix + '_MANIFEST_IDENTITY_MISMATCH')
}
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$privateBoundary = Join-Path $root 'implementation\p08\evidence\private'
[void][System.IO.Directory]::CreateDirectory($privateBoundary)
$privateBoundary = (Resolve-Path -LiteralPath $privateBoundary).Path.TrimEnd('\')
$run = [System.IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if (-not $run.StartsWith(
        $privateBoundary + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    ) -or
    (Split-Path -Leaf $run) -cnotmatch '^p08-20-object-target-[a-z0-9-]{1,80}$') {
    throw ($errorPrefix + '_RUN_DIRECTORY_INVALID')
}
if (Test-Path -LiteralPath $run) {
    $runItem = Get-Item -LiteralPath $run -Force
    if (-not $runItem.PSIsContainer -or
        ($runItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        @(Get-ChildItem -LiteralPath $run -Force).Count -ne 0) {
        throw ($errorPrefix + '_RUN_DIRECTORY_NOT_EMPTY')
    }
}
else { [void][System.IO.Directory]::CreateDirectory($run) }

$manifest = (Resolve-Path -LiteralPath $FixtureManifestPath).Path
$manifestItem = Get-Item -LiteralPath $manifest -Force
if ($manifestItem.PSIsContainer -or
    ($manifestItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $manifestItem.Length -le 0 -or $manifestItem.Length -gt 131072 -or
    (Get-Sha256File -Path $manifest) -cne $ExpectedFixtureManifestSha256) {
    throw ($errorPrefix + '_MANIFEST_INVALID')
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}

$engine = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-object-target-batch-engine.ps1'
)).Path
$engineSha256 = Get-Sha256File -Path $engine
$wrapperSha256 = Get-Sha256File -Path $PSCommandPath
$engineTrace = Join-Path $run 'engine-trace.json'
$progress = Join-Path $run 'progress.jsonl'
$receiptPath = Join-Path $run 'runtime-receipt.json'
$systemX86 = [System.Environment]::GetFolderPath(
    [System.Environment+SpecialFolder]::SystemX86
)
if ([string]::IsNullOrWhiteSpace($systemX86)) {
    throw ($errorPrefix + '_X86_POWERSHELL_UNAVAILABLE')
}
$powershell = Get-Item -LiteralPath (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Force
if ($powershell.PSIsContainer -or
    ($powershell.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $powershell.Length -le 0 -or $powershell.Length -gt 16777216) {
    throw ($errorPrefix + '_X86_POWERSHELL_INVALID')
}

$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $engine,
    '-FixtureManifestPath', $manifest,
    '-ExpectedFixtureManifestSha256', $ExpectedFixtureManifestSha256,
    '-RunDirectory', $run,
    '-TracePath', $engineTrace,
    '-ProgressPath', $progress,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powershell.FullName
$startInfo.Arguments = (($arguments | ForEach-Object {
    ConvertTo-ProcessArgument -Value ([string]$_)
}) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$child = [System.Diagnostics.Process]::new()
$child.StartInfo = $startInfo
$startedAt = Get-Date
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()
$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$lastProgressAt = $startedAt
$lastProgressLength = -1L
$progressChangeCount = 0
$stalledHwpRecoveryCount = 0
$stalledHwpCleanupRefusedCount = 0
$stalledHwpCleanupErrorCount = 0
$exitedWithinTimeout = $false
$cleanup = [ordered]@{ cleaned = 0; refused = 0; errors = 0 }
try {
    while ((Get-Date) -lt $deadline) {
        if ($child.WaitForExit(1000)) {
            $exitedWithinTimeout = $true
            break
        }
        if (Test-Path -LiteralPath $progress -PathType Leaf) {
            $progressItem = Get-Item -LiteralPath $progress -Force
            if ($progressItem.Length -ne $lastProgressLength) {
                $lastProgressLength = [long]$progressItem.Length
                $progressChangeCount += 1
                $lastProgressAt = Get-Date
            }
        }
        # The exact 2020 build can reject the official FilePathCheckDLL and show one
        # user-approved access dialog on the first fixture open.  Keep only that
        # first open alive long enough for the explicit approval; all later stalls
        # remain bounded to 30 seconds.
        $inactivityLimitSeconds = if ($progressChangeCount -le 3) { 180 } else { 30 }
        if (((Get-Date) - $lastProgressAt).TotalSeconds -ge $inactivityLimitSeconds) {
            $stalledCleanup = Stop-OwnedHancomProcesses -StartedAt $startedAt `
                -SessionId $currentSessionId -ExpectedSha256 $ExpectedExecutableSha256
            $stalledHwpRecoveryCount += [int]$stalledCleanup.cleaned
            $stalledHwpCleanupRefusedCount += [int]$stalledCleanup.refused
            $stalledHwpCleanupErrorCount += [int]$stalledCleanup.errors
            $lastProgressAt = Get-Date
        }
    }
}
finally {
    if (-not $child.HasExited) {
        try {
            $child.Kill()
            $child.WaitForExit()
        }
        catch { }
    }
    Start-Sleep -Milliseconds 500
    $cleanup = Stop-OwnedHancomProcesses -StartedAt $startedAt `
        -SessionId $currentSessionId -ExpectedSha256 $ExpectedExecutableSha256
}
$childExitCode = $child.ExitCode
$outputDrained = $false
try {
    $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
        [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
        5000
    )
}
catch { $outputDrained = $false }
$stdout = if ($stdoutTask.IsCompleted) { [string]$stdoutTask.Result } else { '' }
$stderr = if ($stderrTask.IsCompleted) { [string]$stderrTask.Result } else { '' }
$stderrCodeMatch = [regex]::Match(
    $stderr,
    '\bOBJECT_TARGET_BATCH_[A-Z0-9_]+\b'
)
$engineStderrErrorCode = if ($stderrCodeMatch.Success) {
    [string]$stderrCodeMatch.Value
}
else { $null }

Start-Sleep -Milliseconds 250
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
    -ErrorAction SilentlyContinue)

$engineValue = $null
if (Test-Path -LiteralPath $engineTrace -PathType Leaf) {
    $traceItem = Get-Item -LiteralPath $engineTrace -Force
    if (($traceItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $traceItem.Length -gt 0 -and $traceItem.Length -le 1048576) {
        try {
            $engineValue = Get-Content -LiteralPath $engineTrace -Raw -Encoding UTF8 |
                ConvertFrom-Json
        }
        catch { $engineValue = $null }
    }
}
$engineTraceCaseShapeValid = $null -ne $engineValue -and
    @($engineValue.cases).Count -ge 0 -and
    @($engineValue.cases).Count -le 41 -and
    (([string]$engineValue.state -ceq 'pass' -and
            @($engineValue.cases).Count -eq 41) -or
        ([string]$engineValue.state -ceq 'failed'))
$engineTraceValid = $null -ne $engineValue -and
    [string]$engineValue.schema_version -ceq
        'hwpx-agent.p08-20-object-target-batch-engine/v1' -and
    [string]$engineValue.fixture_manifest_sha256 -ceq
        $ExpectedFixtureManifestSha256 -and
    [long]$engineValue.case_count -eq 41 -and
    $engineTraceCaseShapeValid -and
    [long]$engineValue.effective_completed_case_count -ge 0 -and
    [long]$engineValue.effective_completed_case_count -le 41 -and
    [long]$engineValue.recovered_case_count -ge 0 -and
    [long]$engineValue.session_restart_count -ge 0 -and
    [long]$engineValue.scheduled_session_restart_count -ge 0 -and
    [long]$engineValue.retry_session_restart_count -eq
        [long]$engineValue.retry_case_count -and
    @($engineValue.hwp_process_ids).Count -ge 1 -and
    [string]$engineValue.target.prog_id -ceq $ProgId -and
    [string]$engineValue.target.file_version -ceq $ExpectedBuild -and
    [string]$engineValue.target.executable_sha256 -ceq $ExpectedExecutableSha256 -and
    ($engineValue.raw_document_text_present -is [bool]) -and
    -not [bool]$engineValue.raw_document_text_present -and
    -not [bool]$engineValue.user_document_scanned -and
    -not [bool]$engineValue.external_network_invoked -and
    -not [bool]$engineValue.registry_or_system_setting_changed -and
    -not [bool]$engineValue.computer_use_click_or_type_invoked

$errorCode = if (-not $exitedWithinTimeout) { $errorPrefix + '_TIMEOUT' }
elseif (-not $outputDrained) { $errorPrefix + '_OUTPUT_DRAIN_TIMEOUT' }
elseif (-not $engineTraceValid) {
    if ($null -ne $engineStderrErrorCode) { $engineStderrErrorCode }
    else { $errorPrefix + '_ENGINE_TRACE_MISSING_OR_INVALID' }
}
elseif ($childExitCode -ne 0 -or [string]$engineValue.state -cne 'pass') {
    if ($null -ne $engineValue.error_code) { [string]$engineValue.error_code }
    else { $errorPrefix + '_ENGINE_FAILED' }
}
elseif ($stalledHwpCleanupRefusedCount -ne 0 -or $stalledHwpCleanupErrorCount -ne 0) {
    $errorPrefix + '_STALL_RECOVERY_UNVERIFIED'
}
elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or
    $remaining.Count -ne 0) {
    $errorPrefix + '_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p08-20-object-target-batch-runtime-receipt/v1'
    state = if ($null -eq $errorCode) { 'pass' } else { 'failed' }
    recorded_at_utc = [datetime]::UtcNow.ToString('o')
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    harness = [ordered]@{
        wrapper_sha256 = $wrapperSha256
        engine_sha256 = $engineSha256
        bundle_sha256 = Get-Sha256String -Value ($wrapperSha256 + ':' + $engineSha256)
    }
    target = [ordered]@{
        product = 'Hancom Hangul 2020'
        prog_id = $ProgId
        build = $ExpectedBuild
        executable_sha256 = $ExpectedExecutableSha256
        architecture = 'x86'
        locale = 'ko-KR'
    }
    engine_trace_sha256 = if ($engineTraceValid) {
        Get-Sha256File -Path $engineTrace
    }
    else { $null }
    progress_sha256 = if (Test-Path -LiteralPath $progress -PathType Leaf) {
        Get-Sha256File -Path $progress
    }
    else { $null }
    engine_state = if ($engineTraceValid) { [string]$engineValue.state } else { 'unavailable' }
    engine_stderr_error_code = $engineStderrErrorCode
    completed_case_count = if ($engineTraceValid) {
        [long]$engineValue.completed_case_count
    }
    else { 0 }
    effective_completed_case_count = if ($engineTraceValid) {
        [long]$engineValue.effective_completed_case_count
    }
    else { 0 }
    recovered_case_count = if ($engineTraceValid) {
        [long]$engineValue.recovered_case_count
    }
    else { 0 }
    session_restart_count = if ($engineTraceValid) {
        [long]$engineValue.session_restart_count
    }
    else { 0 }
    scheduled_session_restart_count = if ($engineTraceValid) {
        [long]$engineValue.scheduled_session_restart_count
    }
    else { 0 }
    retry_session_restart_count = if ($engineTraceValid) {
        [long]$engineValue.retry_session_restart_count
    }
    else { 0 }
    retry_case_count = if ($engineTraceValid) { [long]$engineValue.retry_case_count } else { 0 }
    retry_completed_case_count = if ($engineTraceValid) {
        [long]$engineValue.retry_completed_case_count
    }
    else { 0 }
    watchdog = [ordered]@{
        timeout_seconds = $TimeoutSeconds
        timed_out = -not $exitedWithinTimeout
        child_exit_code = $childExitCode
        output_drained = $outputDrained
        stdout_sha256 = Get-Sha256String -Value $stdout
        stdout_bytes = [System.Text.Encoding]::UTF8.GetByteCount($stdout)
        stderr_sha256 = Get-Sha256String -Value $stderr
        stderr_bytes = [System.Text.Encoding]::UTF8.GetByteCount($stderr)
        cleaned_process_count = [int]$cleanup.cleaned
        cleanup_refused_count = [int]$cleanup.refused
        cleanup_error_count = [int]$cleanup.errors
        remaining_hwp_process_count = $remaining.Count
        stalled_hwp_recovery_count = $stalledHwpRecoveryCount
        stalled_hwp_cleanup_refused_count = $stalledHwpCleanupRefusedCount
        stalled_hwp_cleanup_error_count = $stalledHwpCleanupErrorCount
    }
    error_code = $errorCode
    raw_document_text_present = $false
    user_document_scanned = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}
Write-NewUtf8File -Path $receiptPath -Content ($receipt | ConvertTo-Json -Depth 10)
$child.Dispose()
$receipt | ConvertTo-Json -Depth 10
if ($null -ne $errorCode) { exit 2 }
exit 0
