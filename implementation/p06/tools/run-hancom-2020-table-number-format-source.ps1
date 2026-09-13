[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BaselinePath,
    [Parameter(Mandatory)][string]$UngroupedPath,
    [Parameter(Mandatory)][string]$GroupedPath,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 900)][int]$TimeoutSeconds = 900
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value.Contains('"')) { throw 'TABLE_NUMBER_FORMAT_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
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
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
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
        worker_process_id = $null
        hwp_process_id = $null
    }
    if (-not $summary.present) { return $summary }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 65536) {
        return $summary
    }
    $allowedPhases = @(
        'preflight', 'com_create', 'table_create', 'formula_author', 'baseline_save',
        'manual_format_general', 'manual_format_integer', 'manual_format_decimal_1',
        'manual_format_decimal_2', 'manual_format_decimal_3', 'manual_format_decimal_4',
        'grouping_remove_general', 'grouping_remove_integer',
        'grouping_remove_decimal_1', 'grouping_remove_decimal_2',
        'grouping_remove_decimal_3', 'grouping_remove_decimal_4',
        'ungrouped_save', 'grouping_add_general', 'grouping_add_integer',
        'grouping_add_decimal_1', 'grouping_add_decimal_2', 'grouping_add_decimal_3',
        'grouping_add_decimal_4', 'grouped_save', 'terminal'
    )
    $expectedSequence = 1
    $workerProcessId = $null
    $hwpProcessId = $null
    foreach ($line in @(Get-Content -LiteralPath $Path -Encoding UTF8)) {
        if ($expectedSequence -gt 64 -or [string]::IsNullOrWhiteSpace($line)) { return $summary }
        try {
            $record = if ($PSVersionTable.PSVersion.Major -ge 7) {
                $line | ConvertFrom-Json -DateKind String
            }
            else { $line | ConvertFrom-Json }
        }
        catch { return $summary }
        $properties = @($record.PSObject.Properties.Name)
        $allowedProperties = @(
            'schema_version', 'sequence', 'recorded_at_utc', 'worker_process_id',
            'hwp_process_id', 'phase', 'state', 'raw_document_text_present',
            'raw_formula_or_command_present'
        )
        if ($properties.Count -ne $allowedProperties.Count -or
            @($properties | Where-Object { $allowedProperties -cnotcontains $_ }).Count -ne 0 -or
            [string]$record.schema_version -cne
                'hwpx-agent.p06-09-hancom-2020-table-number-format-progress/v1' -or
            [long]$record.sequence -ne $expectedSequence -or
            [string]$record.recorded_at_utc -notmatch '^\d{4}-\d{2}-\d{2}T' -or
            [long]$record.worker_process_id -le 0 -or
            ($null -ne $record.hwp_process_id -and [long]$record.hwp_process_id -le 0) -or
            $allowedPhases -cnotcontains [string]$record.phase -or
            [string]$record.state -notin @('running', 'pass', 'failed') -or
            -not ($record.raw_document_text_present -is [bool]) -or
            [bool]$record.raw_document_text_present -or
            -not ($record.raw_formula_or_command_present -is [bool]) -or
            [bool]$record.raw_formula_or_command_present) {
            return $summary
        }
        if ($null -eq $workerProcessId) { $workerProcessId = [long]$record.worker_process_id }
        elseif ($workerProcessId -ne [long]$record.worker_process_id) { return $summary }
        if ($null -ne $record.hwp_process_id) {
            if ($null -eq $hwpProcessId) { $hwpProcessId = [long]$record.hwp_process_id }
            elseif ($hwpProcessId -ne [long]$record.hwp_process_id) { return $summary }
        }
        $summary.event_count += 1
        $summary.last_phase = [string]$record.phase
        $summary.last_state = [string]$record.state
        $expectedSequence += 1
    }
    $summary.worker_process_id = $workerProcessId
    $summary.hwp_process_id = $hwpProcessId
    $summary.valid = $summary.event_count -gt 0
    return $summary
}

function Stop-OwnedHancomProcess {
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Low')]
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [AllowNull()][Nullable[int]]$ExpectedProcessId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )
    $result = [ordered]@{ cleaned = 0; refused = 0; errors = 0 }
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        $runtime = Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtime) { continue }
        $path = [string]$candidate.ExecutablePath
        $createdAt = if ($null -ne $candidate.CreationDate) {
            [datetime]$candidate.CreationDate
        }
        else { [datetime]::MinValue }
        $identityMatches = $false
        if (-not [string]::IsNullOrWhiteSpace($path) -and
            (Test-Path -LiteralPath $path -PathType Leaf)) {
            try { $identityMatches = (Get-Sha256File -Path $path) -ceq $ExpectedSha256 }
            catch { $identityMatches = $false }
        }
        $safe = $null -ne $ExpectedProcessId -and
            [int]$candidate.ProcessId -eq [int]$ExpectedProcessId -and
            [int]$candidate.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            $identityMatches -and
            [string]$candidate.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $safe) { $result.refused += 1; continue }
        if (-not $PSCmdlet.ShouldProcess(
            ('Hwp.exe PID ' + [string]$candidate.ProcessId),
            'Stop owned timed-out automation process'
        )) {
            $result.refused += 1
            continue
        }
        try {
            Stop-Process -Id $candidate.ProcessId -Force -ErrorAction Stop
            Wait-Process -Id $candidate.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            $result.cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue)) {
                $result.cleaned += 1
            }
            else { $result.errors += 1 }
        }
    }
    return $result
}

function Test-BoundedFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$MaximumBytes,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or
        $ExpectedSha256 -notmatch '^[0-9a-f]{64}$') {
        return $false
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt $MaximumBytes) {
        return $false
    }
    return (Get-Sha256File -Path $Path) -ceq $ExpectedSha256
}

if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'TABLE_NUMBER_FORMAT_PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'TABLE_NUMBER_FORMAT_BUILD_NOT_ALLOWED' }
$worker = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'create-hancom-2020-table-number-format-source.ps1'
)).Path
$baseline = [System.IO.Path]::GetFullPath($BaselinePath)
$ungrouped = [System.IO.Path]::GetFullPath($UngroupedPath)
$grouped = [System.IO.Path]::GetFullPath($GroupedPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
$progressFile = $traceFile + '.progress.jsonl'
$allPaths = @($baseline, $ungrouped, $grouped, $traceFile, $innerTrace, $progressFile)
if (($allPaths | Sort-Object -Unique).Count -ne $allPaths.Count) {
    throw 'TABLE_NUMBER_FORMAT_OUTPUT_PATH_COLLISION'
}
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $baseline)).TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'TABLE_NUMBER_FORMAT_BOUNDARY_INVALID'
}
foreach ($candidate in $allPaths) {
    $candidateParent = [System.IO.Path]::GetFullPath(
        (Split-Path -Parent $candidate)
    ).TrimEnd('\')
    if (-not $candidateParent.Equals(
        $boundary,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'TABLE_NUMBER_FORMAT_PATH_OUTSIDE_BOUNDARY'
    }
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'TABLE_NUMBER_FORMAT_PATH_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'TABLE_NUMBER_FORMAT_OUTPUT_ALREADY_EXISTS' }
}
if ([System.IO.Path]::GetExtension($baseline) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($ungrouped) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($grouped) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json') {
    throw 'TABLE_NUMBER_FORMAT_OUTPUT_EXTENSION_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TABLE_NUMBER_FORMAT_PREEXISTING_HWP_PROCESS'
}

$systemX86 = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::SystemX86)
$powerShell = Get-Item -LiteralPath (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Force
if ($powerShell.PSIsContainer -or
    ($powerShell.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $powerShell.Length -le 0 -or $powerShell.Length -gt 16777216) {
    throw 'TABLE_NUMBER_FORMAT_X86_POWERSHELL_UNAVAILABLE'
}
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $worker,
    '-BaselinePath', $baseline,
    '-UngroupedPath', $ungrouped,
    '-GroupedPath', $grouped,
    '-TracePath', $innerTrace,
    '-ProgressPath', $progressFile,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powerShell.FullName
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
$sessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()
$exited = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exited) { $child.Kill(); $child.WaitForExit() }
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
$progress = Read-ProgressJournal -Path $progressFile
$expectedOwnedHwpProcessId = if ([bool]$progress.valid -and
    [long]$progress.worker_process_id -eq [long]$child.Id) {
    $progress.hwp_process_id
}
else { $null }
$cleanup = Stop-OwnedHancomProcess -StartedAt $startedAt -SessionId $sessionId `
    -ExpectedProcessId $expectedOwnedHwpProcessId `
    -ExpectedSha256 $ExpectedExecutableSha256 -Confirm:$false
Start-Sleep -Milliseconds 250
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)

$trace = $null
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    $item = Get-Item -LiteralPath $innerTrace -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $item.Length -gt 0 -and $item.Length -le 131072) {
        try { $trace = Get-Content -LiteralPath $innerTrace -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { $trace = $null }
    }
}
$traceValid = $null -ne $trace -and
    [string]$trace.schema_version -ceq
        'hwpx-agent.p06-09-hancom-2020-table-number-format-source/v1' -and
    [string]$trace.target_build -ceq $ExpectedBuild -and
    [string]$trace.state -in @('pass', 'failed') -and
    ($null -eq $trace.executable_sha256 -or
        [string]$trace.executable_sha256 -ceq $ExpectedExecutableSha256) -and
    -not [bool]$trace.raw_document_text_present -and
    -not [bool]$trace.raw_formula_or_command_present
if (-not $traceValid) { $trace = $null }

$successSemanticsValid = $null -ne $trace -and [string]$trace.state -ceq 'pass' -and
    [string]$trace.executable_sha256 -ceq $ExpectedExecutableSha256 -and
    [string]$trace.table_create -ceq 'pass' -and
    [long]$trace.format_case_count -eq 6 -and
    [long]$trace.operand_cells_written -eq 12 -and
    [long]$trace.formula_actions_passed -eq 6 -and
    [long]$trace.manual_format_dialogs_passed -eq 6 -and
    [long]$trace.delete_grouping_actions_passed -eq 6 -and
    [long]$trace.insert_grouping_actions_passed -eq 6 -and
    ($trace.manual_ui_source_authoring_required -is [bool]) -and
    [bool]$trace.manual_ui_source_authoring_required -and
    [string]$trace.baseline_visible_text_sha256 -match '^[0-9a-f]{64}$' -and
    [string]$trace.ungrouped_visible_text_sha256 -match '^[0-9a-f]{64}$' -and
    [string]$trace.grouped_visible_text_sha256 -match '^[0-9a-f]{64}$'
$artifactsValid = $successSemanticsValid -and
    (Test-BoundedFile -Path $baseline -MaximumBytes 8388608 `
        -ExpectedSha256 ([string]$trace.baseline_hwpx_sha256)) -and
    (Test-BoundedFile -Path $ungrouped -MaximumBytes 8388608 `
        -ExpectedSha256 ([string]$trace.ungrouped_hwpx_sha256)) -and
    (Test-BoundedFile -Path $grouped -MaximumBytes 8388608 `
        -ExpectedSha256 ([string]$trace.grouped_hwpx_sha256))
$wrapperError = if (-not $exited) { 'TABLE_NUMBER_FORMAT_SOURCE_TIMEOUT' }
elseif (-not $outputDrained) { 'TABLE_NUMBER_FORMAT_CHILD_OUTPUT_DRAIN_TIMEOUT' }
elseif ($null -eq $trace) { 'TABLE_NUMBER_FORMAT_INNER_TRACE_MISSING_OR_INVALID' }
elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    if ($null -ne $trace.error_code) { [string]$trace.error_code }
    else { 'TABLE_NUMBER_FORMAT_SOURCE_CHILD_FAILED' }
}
elseif (-not $successSemanticsValid) { 'TABLE_NUMBER_FORMAT_SOURCE_SEMANTIC_RECEIPT_INVALID' }
elseif (-not [bool]$progress.valid -or [string]$progress.last_phase -cne 'terminal' -or
    [string]$progress.last_state -cne 'pass') {
    'TABLE_NUMBER_FORMAT_SOURCE_PROGRESS_INVALID'
}
elseif (-not $artifactsValid) { 'TABLE_NUMBER_FORMAT_SOURCE_ARTIFACT_INVALID' }
elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) {
    'TABLE_NUMBER_FORMAT_SOURCE_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

if ($null -eq $trace) {
    $trace = [pscustomobject][ordered]@{
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-number-format-source-watchdog/v1'
        delegated_worker_schema = $null
        target_build = $ExpectedBuild
        expected_executable_sha256 = $ExpectedExecutableSha256
        executable_sha256 = $null
        state = 'failed'
        failed_phase = 'watchdog'
        error_code = $wrapperError
        raw_document_text_present = $false
        raw_formula_or_command_present = $false
        user_document_opened = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
    }
}
else {
    $workerSchema = [string]$trace.schema_version
    $trace.schema_version = 'hwpx-agent.p06-09-hancom-2020-table-number-format-source-watchdog/v1'
    $trace | Add-Member -NotePropertyName delegated_worker_schema -NotePropertyValue $workerSchema -Force
    $trace | Add-Member -NotePropertyName expected_executable_sha256 `
        -NotePropertyValue $ExpectedExecutableSha256 -Force
    if ($null -ne $wrapperError) {
        $trace.state = if ($wrapperError.EndsWith('_PROCESS_CLEANUP_UNVERIFIED')) {
            'unverified'
        }
        else { 'failed' }
        $trace.failed_phase = 'watchdog'
        $trace.error_code = $wrapperError
    }
}
$trace | Add-Member -NotePropertyName watchdog -NotePropertyValue ([ordered]@{
    timeout_seconds = $TimeoutSeconds
    timed_out = -not $exited
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
    inner_trace_preserved = Test-Path -LiteralPath $innerTrace -PathType Leaf
}) -Force

$json = $trace | ConvertTo-Json -Depth 10
Write-NewUtf8File -Path $traceFile -Content $json
$child.Dispose()
$json
if ($null -ne $wrapperError -or [string]$trace.state -cne 'pass') { exit 2 }
exit 0
