[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedTextSha256,
    [Parameter(Mandatory)][ValidatePattern('^hwpx-agent\.[a-z0-9-]+/v1$')][string]$TraceSchema,
    [Parameter(Mandatory)][ValidatePattern('^[A-Z0-9_]+$')][string]$ErrorPrefix,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 900)][int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) { throw ($ErrorPrefix + '_PROCESS_ARGUMENT_CONTAINS_QUOTE') }
    return '"' + $Value + '"'
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

function Read-ProgressJournal {
    param([Parameter(Mandatory)][string]$Path)

    $summary = [ordered]@{
        present = Test-Path -LiteralPath $Path -PathType Leaf
        valid = $false
        event_count = 0
        last_phase = $null
        last_state = $null
    }
    if (-not $summary.present) { return $summary }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 65536) {
        return $summary
    }
    $allowedProperties = @(
        'schema_version', 'sequence', 'recorded_at_utc', 'worker_process_id',
        'hwp_process_id', 'phase', 'state', 'raw_document_text_present'
    )
    $allowedPhases = @(
        'preflight', 'com_create', 'open_input', 'read_input', 'save_as_hwpx',
        'close_input', 'reopen_output', 'read_output', 'close_output', 'quit', 'terminal'
    )
    $expectedSequence = 1
    $workerProcessId = $null
    $hwpProcessId = $null
    foreach ($line in @(Get-Content -LiteralPath $Path -Encoding UTF8)) {
        if ($expectedSequence -gt 32) { return $summary }
        if ([string]::IsNullOrWhiteSpace($line)) { return $summary }
        try { $event = $line | ConvertFrom-Json } catch { return $summary }
        $properties = @($event.PSObject.Properties.Name)
        if ($properties.Count -ne $allowedProperties.Count) { return $summary }
        foreach ($property in $properties) {
            if ($allowedProperties -cnotcontains $property) { return $summary }
        }
        $sequenceIsInteger = $event.sequence -is [int] -or $event.sequence -is [long]
        $workerIsInteger = $event.worker_process_id -is [int] -or $event.worker_process_id -is [long]
        $hwpIsValid = $null -eq $event.hwp_process_id -or
            $event.hwp_process_id -is [int] -or $event.hwp_process_id -is [long]
        $privacyIsBoolean = $event.raw_document_text_present -is [bool]
        if (-not $sequenceIsInteger -or -not $workerIsInteger -or -not $hwpIsValid -or
            -not $privacyIsBoolean -or
            [string]$event.schema_version -cne 'hwpx-agent.p05-hancom-readback-progress/v1' -or
            [long]$event.sequence -ne $expectedSequence -or
            [string]$event.recorded_at_utc -notmatch '^\d{4}-\d{2}-\d{2}T' -or
            [long]$event.worker_process_id -le 0 -or
            ($null -ne $event.hwp_process_id -and [long]$event.hwp_process_id -le 0) -or
            $allowedPhases -cnotcontains [string]$event.phase -or
            [string]$event.state -notin @('running', 'pass', 'failed') -or
            [bool]$event.raw_document_text_present) {
            return $summary
        }
        if ($null -eq $workerProcessId) { $workerProcessId = [long]$event.worker_process_id }
        elseif ($workerProcessId -ne [long]$event.worker_process_id) { return $summary }
        if ($null -ne $event.hwp_process_id) {
            if ($null -eq $hwpProcessId) { $hwpProcessId = [long]$event.hwp_process_id }
            elseif ($hwpProcessId -ne [long]$event.hwp_process_id) { return $summary }
        }
        $summary.event_count += 1
        $summary.last_phase = [string]$event.phase
        $summary.last_state = [string]$event.state
        $expectedSequence += 1
    }
    $summary.valid = $summary.event_count -gt 0
    return $summary
}

function Stop-OwnedHancomProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )

    $cleaned = 0
    $refused = 0
    $errors = 0
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
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
            try { $identityMatches = (Get-Sha256File -Path $processPath) -ceq $ExpectedSha256 } catch { }
        }
        $safeToClean =
            [int]$candidate.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            $identityMatches -and
            [string]$candidate.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $safeToClean) {
            $refused += 1
            continue
        }
        try {
            Stop-Process -Id $candidate.ProcessId -Force -ErrorAction Stop
            Wait-Process -Id $candidate.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            $cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue)) {
                $cleaned += 1
            }
            else { $errors += 1 }
        }
    }
    return [ordered]@{ cleaned = $cleaned; refused = $refused; errors = $errors }
}

$engine = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-tab-readback.ps1'
)).Path
$inputItem = Get-Item -LiteralPath $InputPath -Force
if ($inputItem.PSIsContainer -or
    ($inputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $inputItem.Length -le 0 -or $inputItem.Length -gt 8388608) {
    throw ($ErrorPrefix + '_INPUT_NOT_BOUNDED_REGULAR_FILE')
}
$input = $inputItem.FullName
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $input)).Path.TrimEnd('\')
$output = [System.IO.Path]::GetFullPath($OutputPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw ($ErrorPrefix + '_FIXTURE_BOUNDARY_REPARSE_POINT')
}
if ([System.IO.Path]::GetExtension($input) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($output) -cne '.hwpx') {
    throw ($ErrorPrefix + '_HWPX_EXTENSION_REQUIRED')
}
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
$progressFile = $traceFile + '.progress.jsonl'
foreach ($candidate in @($output, $traceFile, $innerTrace, $progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw ($ErrorPrefix + '_PATH_OUTSIDE_FIXTURE_BOUNDARY')
    }
    if (Test-Path -LiteralPath $candidate) { throw ($ErrorPrefix + '_OUTPUT_ALREADY_EXISTS') }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($ErrorPrefix + '_PREEXISTING_HWP_PROCESS')
}

$powerShell = Join-Path $PSHOME 'powershell.exe'
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $engine,
    '-InputPath', $input,
    '-ExpectedInputSha256', $ExpectedInputSha256,
    '-OutputPath', $output,
    '-TracePath', $innerTrace,
    '-ExpectedTextSha256', $ExpectedTextSha256,
    '-ProgressPath', $progressFile,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powerShell
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

$exitedWithinTimeout = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exitedWithinTimeout) {
    $child.Kill()
    $child.WaitForExit()
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

Start-Sleep -Milliseconds 500
$cleanup = Stop-OwnedHancomProcesses `
    -StartedAt $startedAt `
    -SessionId $currentSessionId `
    -ExpectedSha256 $ExpectedExecutableSha256
Start-Sleep -Milliseconds 250
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
$progress = Read-ProgressJournal -Path $progressFile

$trace = $null
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    $innerItem = Get-Item -LiteralPath $innerTrace -Force
    if (($innerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $innerItem.Length -gt 0 -and $innerItem.Length -le 131072) {
        try { $trace = Get-Content -LiteralPath $innerTrace -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { $trace = $null }
    }
}
$traceValid = $null -ne $trace -and
    @($trace.PSObject.Properties.Name) -ccontains 'schema_version' -and
    @($trace.PSObject.Properties.Name) -ccontains 'state' -and
    @($trace.PSObject.Properties.Name) -ccontains 'error_code' -and
    @($trace.PSObject.Properties.Name) -ccontains 'input_sha256' -and
    @($trace.PSObject.Properties.Name) -ccontains 'raw_document_text_present' -and
    [string]$trace.schema_version -ceq 'hwpx-agent.p05-04-hancom-2020-tab-readback/v1' -and
    [string]$trace.input_sha256 -ceq $ExpectedInputSha256 -and
    -not [bool]$trace.raw_document_text_present
if (-not $traceValid) { $trace = $null }
$wrapperError = if (-not $exitedWithinTimeout) { $ErrorPrefix + '_TIMEOUT' }
elseif (-not $outputDrained) { $ErrorPrefix + '_CHILD_OUTPUT_DRAIN_TIMEOUT' }
elseif ($null -eq $trace) { $ErrorPrefix + '_INNER_TRACE_MISSING_OR_INVALID' }
elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    if ($null -ne $trace.error_code) {
        ([string]$trace.error_code).Replace('TAB_READBACK_', $ErrorPrefix + '_')
    }
    else { $ErrorPrefix + '_CHILD_FAILED' }
}
elseif (-not [bool]$progress.valid -or
    [string]$progress.last_phase -cne 'terminal' -or
    [string]$progress.last_state -cne 'pass') {
    $ErrorPrefix + '_PROGRESS_INVALID'
}
elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) {
    $ErrorPrefix + '_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

if ($null -eq $trace) {
    $trace = [pscustomobject][ordered]@{
        schema_version = $TraceSchema
        state = 'failed'
        delegated_engine_schema = $null
        input_sha256 = $ExpectedInputSha256
        input_unchanged = (Get-Sha256File -Path $input) -ceq $ExpectedInputSha256
        input_text_sha256 = $null
        output_sha256 = $null
        output_text_sha256 = $null
        output_saved = (Test-Path -LiteralPath $output -PathType Leaf)
        phases = $null
        error_code = $wrapperError
        failed_phase = 'watchdog'
        raw_document_text_present = $false
        user_document_scanned = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
        window_visible_for_user_access = $false
    }
}
else {
    $innerSchema = [string]$trace.schema_version
    $trace.schema_version = $TraceSchema
    $trace | Add-Member -NotePropertyName delegated_engine_schema -NotePropertyValue $innerSchema -Force
    if ($null -ne $trace.error_code) {
        $trace.error_code = ([string]$trace.error_code).Replace('TAB_READBACK_', $ErrorPrefix + '_')
    }
    if ($null -ne $wrapperError) {
        $trace.state = if ($wrapperError.EndsWith('_PROCESS_CLEANUP_UNVERIFIED')) { 'unverified' } else { 'failed' }
        $trace.error_code = $wrapperError
        $trace.failed_phase = 'watchdog'
    }
}
$trace | Add-Member -NotePropertyName watchdog -NotePropertyValue ([ordered]@{
    timeout_seconds = $TimeoutSeconds
    timed_out = -not $exitedWithinTimeout
    child_exit_code = $childExitCode
    output_drained = $outputDrained
    cleaned_process_count = [int]$cleanup.cleaned
    cleanup_refused_count = [int]$cleanup.refused
    cleanup_error_count = [int]$cleanup.errors
    remaining_hwp_process_count = $remaining.Count
    progress_present = [bool]$progress.present
    progress_valid = [bool]$progress.valid
    progress_event_count = [int]$progress.event_count
    progress_last_phase = $progress.last_phase
    progress_last_state = $progress.last_state
}) -Force

$json = $trace | ConvertTo-Json -Depth 10
Write-NewUtf8File -Path $traceFile -Content $json
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    [System.IO.File]::Delete($innerTrace)
}
$child.Dispose()
$json
if ($null -ne $wrapperError -or [string]$trace.state -cne 'pass') { exit 2 }
