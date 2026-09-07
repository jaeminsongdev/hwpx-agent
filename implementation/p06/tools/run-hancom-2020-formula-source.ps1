[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$PdfPath,
    [Parameter(Mandatory)][string]$TracePath,
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
    try { return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value.Contains('"')) { throw 'FORMULA_SOURCE_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
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
    }
    if (-not $summary.present) { return $summary }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 65536) {
        return $summary
    }
    $allowedProperties = @(
        'schema_version', 'sequence', 'recorded_at_utc', 'worker_process_id',
        'hwp_process_id', 'phase', 'state', 'raw_document_text_present',
        'raw_formula_or_command_present'
    )
    $allowedPhases = @(
        'preflight', 'com_create', 'table_create', 'formula_source',
        'pre_save_semantic', 'save_hwpx', 'close_before_reopen',
        'reopen_hwpx', 'save_pdf', 'terminal'
    )
    $expectedSequence = 1
    $workerProcessId = $null
    $hwpProcessId = $null
    foreach ($line in @(Get-Content -LiteralPath $Path -Encoding UTF8)) {
        if ($expectedSequence -gt 32 -or [string]::IsNullOrWhiteSpace($line)) { return $summary }
        try {
            $progressRecord = if ($PSVersionTable.PSVersion.Major -ge 7) {
                $line | ConvertFrom-Json -DateKind String
            }
            else { $line | ConvertFrom-Json }
        }
        catch { return $summary }
        $properties = @($progressRecord.PSObject.Properties.Name)
        if ($properties.Count -ne $allowedProperties.Count) { return $summary }
        foreach ($property in $properties) {
            if ($allowedProperties -cnotcontains $property) { return $summary }
        }
        $sequenceIsInteger = $progressRecord.sequence -is [int] -or
            $progressRecord.sequence -is [long]
        $workerIsInteger = $progressRecord.worker_process_id -is [int] -or
            $progressRecord.worker_process_id -is [long]
        $hwpIsValid = $null -eq $progressRecord.hwp_process_id -or
            $progressRecord.hwp_process_id -is [int] -or
            $progressRecord.hwp_process_id -is [long]
        if (-not $sequenceIsInteger -or -not $workerIsInteger -or -not $hwpIsValid -or
            [string]$progressRecord.schema_version -cne 'hwpx-agent.p06-06-hancom-2020-formula-progress/v1' -or
            [long]$progressRecord.sequence -ne $expectedSequence -or
            [string]$progressRecord.recorded_at_utc -notmatch '^\d{4}-\d{2}-\d{2}T' -or
            [long]$progressRecord.worker_process_id -le 0 -or
            ($null -ne $progressRecord.hwp_process_id -and
                [long]$progressRecord.hwp_process_id -le 0) -or
            $allowedPhases -cnotcontains [string]$progressRecord.phase -or
            [string]$progressRecord.state -notin @('running', 'pass', 'failed') -or
            -not ($progressRecord.raw_document_text_present -is [bool]) -or
            [bool]$progressRecord.raw_document_text_present -or
            -not ($progressRecord.raw_formula_or_command_present -is [bool]) -or
            [bool]$progressRecord.raw_formula_or_command_present) {
            return $summary
        }
        if ($null -eq $workerProcessId) {
            $workerProcessId = [long]$progressRecord.worker_process_id
        }
        elseif ($workerProcessId -ne [long]$progressRecord.worker_process_id) { return $summary }
        if ($null -ne $progressRecord.hwp_process_id) {
            if ($null -eq $hwpProcessId) {
                $hwpProcessId = [long]$progressRecord.hwp_process_id
            }
            elseif ($hwpProcessId -ne [long]$progressRecord.hwp_process_id) { return $summary }
        }
        $summary.event_count += 1
        $summary.last_phase = [string]$progressRecord.phase
        $summary.last_state = [string]$progressRecord.state
        $expectedSequence += 1
    }
    $summary.valid = $summary.event_count -gt 0
    return $summary
}

function Stop-OwnedHancomProcess {
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Low')]
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
            try { $identityMatches = (Get-Sha256File -Path $processPath) -ceq $ExpectedSha256 }
            catch { $identityMatches = $false }
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
        if (-not $PSCmdlet.ShouldProcess(
            ('Hwp.exe PID ' + [string]$candidate.ProcessId),
            'Stop owned timed-out automation process'
        )) {
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

if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'FORMULA_SOURCE_PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'FORMULA_SOURCE_BUILD_NOT_ALLOWED' }
$worker = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'create-hancom-2020-formula-source.ps1'
)).Path
$output = [System.IO.Path]::GetFullPath($OutputPath)
$pdf = [System.IO.Path]::GetFullPath($PdfPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $output)).TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'FORMULA_SOURCE_BOUNDARY_INVALID'
}
if ([System.IO.Path]::GetExtension($output) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($pdf) -cne '.pdf' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json') {
    throw 'FORMULA_SOURCE_OUTPUT_EXTENSION_INVALID'
}
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
$progressFile = $traceFile + '.progress.jsonl'
foreach ($candidate in @($output, $pdf, $traceFile, $innerTrace, $progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'FORMULA_SOURCE_PATH_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'FORMULA_SOURCE_OUTPUT_ALREADY_EXISTS' }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'FORMULA_SOURCE_PREEXISTING_HWP_PROCESS'
}

$systemX86 = [System.Environment]::GetFolderPath(
    [System.Environment+SpecialFolder]::SystemX86
)
if ([string]::IsNullOrWhiteSpace($systemX86)) {
    throw 'FORMULA_SOURCE_X86_POWERSHELL_UNAVAILABLE'
}
$powerShellItem = Get-Item -LiteralPath (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Force
if ($powerShellItem.PSIsContainer -or
    ($powerShellItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $powerShellItem.Length -le 0 -or $powerShellItem.Length -gt 16777216) {
    throw 'FORMULA_SOURCE_X86_POWERSHELL_UNAVAILABLE'
}
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $worker,
    '-OutputPath', $output,
    '-PdfPath', $pdf,
    '-TracePath', $innerTrace,
    '-ProgressPath', $progressFile,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powerShellItem.FullName
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
$cleanup = Stop-OwnedHancomProcess `
    -StartedAt $startedAt `
    -SessionId $currentSessionId `
    -ExpectedSha256 $ExpectedExecutableSha256 `
    -Confirm:$false
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
    @($trace.PSObject.Properties.Name) -ccontains 'target_build' -and
    @($trace.PSObject.Properties.Name) -ccontains 'executable_sha256' -and
    @($trace.PSObject.Properties.Name) -ccontains 'raw_document_text_present' -and
    @($trace.PSObject.Properties.Name) -ccontains 'raw_formula_or_command_present' -and
    [string]$trace.schema_version -ceq 'hwpx-agent.p06-06-hancom-2020-formula-source/v1' -and
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
    [long]$trace.operand_cells_written -eq 2 -and
    [string]$trace.formula_action -ceq 'pass' -and
    ($trace.pre_save_visible_formula -is [bool]) -and
    [bool]$trace.pre_save_visible_formula -and
    [string]$trace.pre_save_text_sha256 -match '^[0-9a-f]{64}$' -and
    [string]$trace.save_hwpx -ceq 'pass' -and
    [string]$trace.reopen_hwpx -ceq 'pass' -and
    ($trace.reopen_visible_formula -is [bool]) -and
    [bool]$trace.reopen_visible_formula -and
    [string]$trace.reopen_text_sha256 -ceq [string]$trace.pre_save_text_sha256 -and
    [string]$trace.save_pdf -ceq 'pass'
$artifactsValid = $successSemanticsValid -and
    (Test-BoundedFile -Path $output -MaximumBytes 8388608 -ExpectedSha256 ([string]$trace.output_hwpx_sha256)) -and
    (Test-BoundedFile -Path $pdf -MaximumBytes 33554432 -ExpectedSha256 ([string]$trace.output_pdf_sha256))
if ($artifactsValid) {
    $pdfStream = [System.IO.File]::OpenRead($pdf)
    try {
        $signature = [byte[]]::new(5)
        $artifactsValid = $pdfStream.Read($signature, 0, 5) -eq 5 -and
            [System.Text.Encoding]::ASCII.GetString($signature) -ceq '%PDF-'
    }
    finally { $pdfStream.Dispose() }
}

$wrapperError = if (-not $exitedWithinTimeout) { 'FORMULA_SOURCE_TIMEOUT' }
elseif (-not $outputDrained) { 'FORMULA_SOURCE_CHILD_OUTPUT_DRAIN_TIMEOUT' }
elseif ($null -eq $trace) { 'FORMULA_SOURCE_INNER_TRACE_MISSING_OR_INVALID' }
elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    if ($null -ne $trace.error_code) { [string]$trace.error_code }
    else { 'FORMULA_SOURCE_CHILD_FAILED' }
}
elseif (-not $successSemanticsValid) { 'FORMULA_SOURCE_SEMANTIC_RECEIPT_INVALID' }
elseif (-not [bool]$progress.valid -or
    [string]$progress.last_phase -cne 'terminal' -or
    [string]$progress.last_state -cne 'pass') {
    'FORMULA_SOURCE_PROGRESS_INVALID'
}
elseif (-not $artifactsValid) { 'FORMULA_SOURCE_ARTIFACT_INVALID' }
elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) {
    'FORMULA_SOURCE_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

if ($null -eq $trace) {
    $trace = [pscustomobject][ordered]@{
        schema_version = 'hwpx-agent.p06-06-hancom-2020-formula-source-watchdog/v1'
        delegated_worker_schema = $null
        target_build = $ExpectedBuild
        expected_executable_sha256 = $ExpectedExecutableSha256
        executable_sha256 = $null
        state = 'failed'
        failed_phase = 'watchdog'
        error_code = $wrapperError
        output_hwpx_present = Test-Path -LiteralPath $output -PathType Leaf
        output_pdf_present = Test-Path -LiteralPath $pdf -PathType Leaf
        raw_document_text_present = $false
        raw_formula_or_command_present = $false
        user_document_opened = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
    }
}
else {
    $innerSchema = [string]$trace.schema_version
    $trace.schema_version = 'hwpx-agent.p06-06-hancom-2020-formula-source-watchdog/v1'
    $trace | Add-Member -NotePropertyName delegated_worker_schema -NotePropertyValue $innerSchema -Force
    $trace | Add-Member -NotePropertyName expected_executable_sha256 `
        -NotePropertyValue $ExpectedExecutableSha256 -Force
    if ($null -ne $wrapperError) {
        $trace.state = if ($wrapperError.EndsWith('_PROCESS_CLEANUP_UNVERIFIED')) {
            'unverified'
        }
        else { 'failed' }
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
exit 0
