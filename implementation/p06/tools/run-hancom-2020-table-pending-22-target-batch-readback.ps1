[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$MergeSplitManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedMergeSplitManifestSha256,
    [Parameter(Mandatory)][string]$LayoutPlacementManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedLayoutPlacementManifestSha256,
    [Parameter(Mandatory)][string]$RemainingManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRemainingManifestSha256,
    [Parameter(Mandatory)][string]$AccessControlPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedAccessControlSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(300, 7200)][int]$TimeoutSeconds = 3600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedManifestSha256 = [ordered]@{
    merge_split = '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
    layout_placement = '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf'
    remaining = '1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e'
}
$expectedCaseOrder = [ordered]@{
    merge_split = @('TABLE-016', 'TABLE-017')
    layout_placement = @(
        'TABLE-018', 'TABLE-019', 'TABLE-050', 'TABLE-051', 'TABLE-052',
        'TABLE-053', 'TABLE-034', 'TABLE-036', 'TABLE-037', 'TABLE-038'
    )
    remaining = @(
        'TABLE-020', 'TABLE-021', 'TABLE-032', 'TABLE-033', 'TABLE-049',
        'TABLE-054', 'TABLE-056', 'TABLE-057', 'TABLE-058', 'TABLE-060'
    )
}
$pinnedAccessControlSha256 =
    '04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c'
$engine = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-pending-22-target-batch-engine.ps1'
)).Path

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) {
        throw 'TABLE_PENDING_22_TARGET_PROCESS_ARGUMENT_CONTAINS_QUOTE'
    }
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

function Resolve-ExactManifest {
    param(
        [Parameter(Mandatory)][string]$GroupId,
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    if ($ExpectedSha256 -cne [string]$expectedManifestSha256[$GroupId]) {
        throw 'TABLE_PENDING_22_TARGET_MANIFEST_IDENTITY_MISMATCH'
    }
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith(
        $TargetRoot + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'TABLE_PENDING_22_TARGET_MANIFEST_OUTSIDE_TARGET_ROOT'
    }
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt 1048576 -or
        (Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_PENDING_22_TARGET_MANIFEST_INVALID'
    }
    try {
        $manifest = Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        throw 'TABLE_PENDING_22_TARGET_MANIFEST_JSON_INVALID'
    }
    $cases = @($manifest.cases)
    $expectedFeatures = @($expectedCaseOrder[$GroupId])
    if ($cases.Count -ne $expectedFeatures.Count) {
        throw 'TABLE_PENDING_22_TARGET_CASE_SET_INVALID'
    }
    $directory = (Resolve-Path -LiteralPath (
        Split-Path -Parent $item.FullName
    )).Path.TrimEnd('\')
    $directoryItem = Get-Item -LiteralPath $directory -Force
    if (($directoryItem.Attributes -band
            [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'TABLE_PENDING_22_TARGET_FIXTURE_BOUNDARY_REPARSE_POINT'
    }
    $prepared = @()
    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        if ([string]$case.feature_id -cne $expectedFeatures[$index] -or
            [string]$case.case_id -notmatch '^table-[0-9]{3}-[a-z0-9-]+$' -or
            [string]$case.file -cne ([string]$case.case_id + '.hwpx') -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$') {
            throw 'TABLE_PENDING_22_TARGET_CASE_BINDING_INVALID'
        }
        $input = [System.IO.Path]::GetFullPath((
            Join-Path $directory ([string]$case.file)
        ))
        $output = [System.IO.Path]::GetFullPath((
            Join-Path $directory (
                [string]$case.case_id + '.hancom-2020-readback.hwpx'
            )
        ))
        $pdf = [System.IO.Path]::GetFullPath((
            Join-Path $directory (
                [string]$case.case_id + '.hancom-2020-render.pdf'
            )
        ))
        foreach ($candidate in @($input, $output, $pdf)) {
            if (-not $candidate.StartsWith(
                $directory + '\',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
                throw 'TABLE_PENDING_22_TARGET_PATH_OUTSIDE_FIXTURE_BOUNDARY'
            }
        }
        $inputItem = Get-Item -LiteralPath $input -Force
        if ($inputItem.PSIsContainer -or
            ($inputItem.Attributes -band
                [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $inputItem.Length -le 0 -or
            $inputItem.Length -gt 8388608 -or
            (Get-Sha256File -Path $input) -cne [string]$case.sha256) {
            throw 'TABLE_PENDING_22_TARGET_INPUT_INVALID'
        }
        foreach ($candidate in @($output, $pdf)) {
            if (Test-Path -LiteralPath $candidate) {
                throw 'TABLE_PENDING_22_TARGET_OUTPUT_ALREADY_EXISTS'
            }
        }
        $prepared += [ordered]@{
            group_id = $GroupId
            group_case_index = $index + 1
            case_id = [string]$case.case_id
            feature_id = [string]$case.feature_id
            capability_id = [string]$case.capability_id
            manifest_sha256 = $ExpectedSha256
            input_file = [string]$case.file
            input_path = $input
            input_sha256 = [string]$case.sha256
            output_path = $output
            pdf_path = $pdf
        }
    }
    return [ordered]@{
        path = $item.FullName
        directory = $directory
        cases = $prepared
    }
}

function Resolve-ExactAccessControl {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    if ($ExpectedSha256 -cne $pinnedAccessControlSha256) {
        throw 'TABLE_PENDING_22_TARGET_ACCESS_CONTROL_IDENTITY_MISMATCH'
    }
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith(
        $TargetRoot + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'TABLE_PENDING_22_TARGET_ACCESS_CONTROL_OUTSIDE_TARGET_ROOT'
    }
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt 8388608 -or
        [System.IO.Path]::GetExtension($item.FullName) -cne '.hwpx' -or
        (Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_PENDING_22_TARGET_ACCESS_CONTROL_INVALID'
    }
    return [ordered]@{
        path = $item.FullName
        file = $item.Name
        sha256 = $ExpectedSha256
    }
}

function Read-ProgressJournal {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][int]$ExpectedWorkerProcessId
    )

    $summary = [ordered]@{
        present = $false
        valid = $false
        event_count = 0
        last_phase = $null
        last_state = $null
        observed_phase = $null
        observed_feature_id = $null
        worker_process_id = $null
        hwp_process_id = $null
        window_visible_for_user_access = $false
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $summary
    }
    $summary.present = $true
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt 262144) {
        return $summary
    }
    $lines = @(Get-Content -LiteralPath $item.FullName -Encoding UTF8)
    if ($lines.Count -eq 0 -or $lines.Count -gt 400) {
        return $summary
    }
    $allowed = @(
        'schema_version', 'sequence', 'recorded_at_utc', 'worker_process_id',
        'hwp_process_id', 'global_case_index', 'group_case_index', 'group_id',
        'feature_id', 'phase', 'state', 'raw_document_text_present'
    )
    $expectedSequence = 1
    $observedHwpProcessId = $null
    foreach ($line in $lines) {
        try {
            $event = $line | ConvertFrom-Json
        }
        catch { return $summary }
        $names = @($event.PSObject.Properties.Name)
        if ($names.Count -ne $allowed.Count) { return $summary }
        foreach ($name in $names) {
            if ($allowed -cnotcontains $name) { return $summary }
        }
        if ([string]$event.schema_version -cne
                'hwpx-agent.p06-09-table-pending-22-batch-progress/v1' -or
            [long]$event.sequence -ne $expectedSequence -or
            [long]$event.worker_process_id -ne $ExpectedWorkerProcessId -or
            [bool]$event.raw_document_text_present -or
            [string]$event.state -notmatch '^(running|pass|failed)$') {
            return $summary
        }
        if ($null -ne $event.hwp_process_id) {
            if ($null -eq $observedHwpProcessId) {
                $observedHwpProcessId = [long]$event.hwp_process_id
            }
            elseif ([long]$event.hwp_process_id -ne $observedHwpProcessId) {
                return $summary
            }
        }
        if ($expectedSequence -eq 1 -and
            [string]$event.phase -cne 'preflight') {
            return $summary
        }
        if ($expectedSequence -eq 2 -and
            [string]$event.phase -cne 'com_create') {
            return $summary
        }
        if ($expectedSequence -eq 3 -and
            [string]$event.phase -ceq 'access_control_open' -and
            [string]$event.state -ceq 'running') {
            $summary.window_visible_for_user_access = $true
        }
        $summary.event_count += 1
        $summary.last_phase = [string]$event.phase
        $summary.last_state = [string]$event.state
        if ([long]$event.global_case_index -gt 0) {
            $summary.observed_phase = [string]$event.phase
            $summary.observed_feature_id = [string]$event.feature_id
        }
        $expectedSequence += 1
    }
    $summary.worker_process_id = $ExpectedWorkerProcessId
    $summary.hwp_process_id = $observedHwpProcessId
    $summary.valid = $true
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
            try {
                $identityMatches = (
                    Get-Sha256File -Path $processPath
                ) -ceq $ExpectedSha256
            }
            catch { }
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
    return [ordered]@{
        cleaned = $cleaned
        refused = $refused
        errors = $errors
    }
}

function Test-PdfEvidence {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][object]$CaseTrace
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -lt 5 -or
        $item.Length -gt 33554432 -or
        [long]$CaseTrace.render_pdf_bytes -ne $item.Length -or
        [string]$CaseTrace.render_pdf_sha256 -cne (Get-Sha256File -Path $Path) -or
        -not [bool]$CaseTrace.render_pdf_signature_valid) {
        return $false
    }
    $stream = [System.IO.File]::OpenRead($item.FullName)
    try {
        $signature = [byte[]]::new(5)
        return $stream.Read($signature, 0, 5) -eq 5 -and
            [System.Text.Encoding]::ASCII.GetString($signature) -ceq '%PDF-'
    }
    finally { $stream.Dispose() }
}

function Test-BoundedAccessControlEvidence {
    param([Parameter(Mandatory)][object]$AccessControl)

    $attemptProperty = $AccessControl.PSObject.Properties['open_attempt_count']
    $firstFalseProperty = $AccessControl.PSObject.Properties['first_open_returned_false']
    if ($null -eq $attemptProperty -or $null -eq $firstFalseProperty) {
        return $false
    }
    try { $attemptCount = [long]$AccessControl.open_attempt_count }
    catch { return $false }
    return [string]$AccessControl.retry_policy -ceq
        'one_same_session_retry_after_first_false' -and
        $attemptCount -ge 0 -and $attemptCount -le 2 -and
        ($AccessControl.first_open_returned_false -is [bool])
}

function Test-SuccessAccessControlEvidence {
    param([Parameter(Mandatory)][object]$AccessControl)

    if (-not (Test-BoundedAccessControlEvidence -AccessControl $AccessControl)) {
        return $false
    }
    $attemptCount = [long]$AccessControl.open_attempt_count
    $firstOpenReturnedFalse = [bool]$AccessControl.first_open_returned_false
    return ($attemptCount -eq 1 -and -not $firstOpenReturnedFalse) -or
        ($attemptCount -eq 2 -and $firstOpenReturnedFalse)
}

function Test-SuccessEvidence {
    param(
        [Parameter(Mandatory)][object]$Trace,
        [Parameter(Mandatory)][object[]]$Cases
    )

    if ([string]$Trace.state -cne 'pass' -or
        [long]$Trace.case_count -ne 22 -or
        [long]$Trace.completed_case_count -ne 22 -or
        @($Trace.cases).Count -ne 22 -or
        $null -ne $Trace.failed_feature_id -or
        $null -ne $Trace.error_code -or
        $null -ne $Trace.failed_phase -or
        [string]$Trace.access_control.source -cne
            'verified_hancom_saved_table_012_control' -or
        [string]$Trace.access_control.input_file -cne
            [string]$script:accessControl.file -or
        [string]$Trace.access_control.input_sha256 -cne
            [string]$script:accessControl.sha256 -or
        (Get-Sha256File -Path ([string]$script:accessControl.path)) -cne
            [string]$script:accessControl.sha256 -or
        -not [bool]$Trace.access_control.input_unchanged -or
        -not (Test-SuccessAccessControlEvidence -AccessControl $Trace.access_control) -or
        [string]$Trace.access_control.open_state -cne 'pass' -or
        [string]$Trace.access_control.close_state -cne 'pass') {
        return $false
    }
    $traceCases = @($Trace.cases)
    $requiredPhases = @(
        'open_input', 'read_input', 'save_as_hwpx', 'close_input',
        'reopen_output', 'read_output', 'export_pdf', 'close_output'
    )
    for ($index = 0; $index -lt 22; $index += 1) {
        $caseTrace = $traceCases[$index]
        $case = $Cases[$index]
        if ([string]$caseTrace.group_id -cne [string]$case.group_id -or
            [long]$caseTrace.group_case_index -ne [long]$case.group_case_index -or
            [string]$caseTrace.case_id -cne [string]$case.case_id -or
            [string]$caseTrace.feature_id -cne [string]$case.feature_id -or
            [string]$caseTrace.capability_id -cne [string]$case.capability_id -or
            [string]$caseTrace.manifest_sha256 -cne [string]$case.manifest_sha256 -or
            [string]$caseTrace.input_file -cne [string]$case.input_file -or
            [string]$caseTrace.input_sha256 -cne [string]$case.input_sha256 -or
            -not [bool]$caseTrace.input_unchanged -or
            [string]$caseTrace.input_text_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$caseTrace.output_text_sha256 -cne
                [string]$caseTrace.input_text_sha256 -or
            -not [bool]$caseTrace.output_saved -or
            [string]$caseTrace.output_file -cne
                [System.IO.Path]::GetFileName([string]$case.output_path) -or
            [string]$caseTrace.output_sha256 -cne
                (Get-Sha256File -Path ([string]$case.output_path)) -or
            -not (Test-PdfEvidence -Path ([string]$case.pdf_path) -CaseTrace $caseTrace) -or
            $null -ne $caseTrace.error_code -or
            $null -ne $caseTrace.failed_phase) {
            return $false
        }
        foreach ($phase in $requiredPhases) {
            if ([string]$caseTrace.phases.$phase -cne 'pass') {
                return $false
            }
        }
    }
    return $true
}

$repoRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\..'
)).Path.TrimEnd('\')
$targetRoot = (Resolve-Path -LiteralPath (
    Join-Path $repoRoot 'fixtures\target-build'
)).Path.TrimEnd('\')
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
if (-not $traceFile.StartsWith(
    $targetRoot + '\',
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw 'TABLE_PENDING_22_TARGET_TRACE_OUTSIDE_TARGET_ROOT'
}
$traceParent = Split-Path -Parent $traceFile
if (-not [System.IO.Directory]::Exists($traceParent)) {
    throw 'TABLE_PENDING_22_TARGET_TRACE_PARENT_MISSING'
}
$traceParentItem = Get-Item -LiteralPath $traceParent -Force
if (($traceParentItem.Attributes -band
        [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'TABLE_PENDING_22_TARGET_TRACE_PARENT_REPARSE_POINT'
}
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
$progressFile = $traceFile + '.progress.jsonl'
foreach ($candidate in @($traceFile, $innerTrace, $progressFile)) {
    if (Test-Path -LiteralPath $candidate) {
        throw 'TABLE_PENDING_22_TARGET_OUTPUT_ALREADY_EXISTS'
    }
}

$mergeRecord = Resolve-ExactManifest -GroupId 'merge_split' -Path (
    $MergeSplitManifestPath
) -ExpectedSha256 $ExpectedMergeSplitManifestSha256 -TargetRoot $targetRoot
$layoutRecord = Resolve-ExactManifest -GroupId 'layout_placement' -Path (
    $LayoutPlacementManifestPath
) -ExpectedSha256 $ExpectedLayoutPlacementManifestSha256 -TargetRoot $targetRoot
$remainingRecord = Resolve-ExactManifest -GroupId 'remaining' -Path (
    $RemainingManifestPath
) -ExpectedSha256 $ExpectedRemainingManifestSha256 -TargetRoot $targetRoot
$script:accessControl = Resolve-ExactAccessControl -Path $AccessControlPath `
    -ExpectedSha256 $ExpectedAccessControlSha256 -TargetRoot $targetRoot
$allCases = @($mergeRecord.cases) + @($layoutRecord.cases) + @($remainingRecord.cases)
if ($allCases.Count -ne 22) {
    throw 'TABLE_PENDING_22_TARGET_TOTAL_CASE_COUNT_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TABLE_PENDING_22_TARGET_PREEXISTING_HWP_PROCESS'
}

$systemX86 = [System.Environment]::GetFolderPath(
    [System.Environment+SpecialFolder]::SystemX86
)
if ([string]::IsNullOrWhiteSpace($systemX86)) {
    throw 'TABLE_PENDING_22_TARGET_X86_POWERSHELL_UNAVAILABLE'
}
$powerShellItem = Get-Item -LiteralPath (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Force
if ($powerShellItem.PSIsContainer -or
    ($powerShellItem.Attributes -band
        [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $powerShellItem.Length -le 0 -or
    $powerShellItem.Length -gt 16777216) {
    throw 'TABLE_PENDING_22_TARGET_X86_POWERSHELL_UNAVAILABLE'
}

$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $engine,
    '-MergeSplitManifestPath', $mergeRecord.path,
    '-ExpectedMergeSplitManifestSha256', $ExpectedMergeSplitManifestSha256,
    '-LayoutPlacementManifestPath', $layoutRecord.path,
    '-ExpectedLayoutPlacementManifestSha256', $ExpectedLayoutPlacementManifestSha256,
    '-RemainingManifestPath', $remainingRecord.path,
    '-ExpectedRemainingManifestSha256', $ExpectedRemainingManifestSha256,
    '-AccessControlPath', $script:accessControl.path,
    '-ExpectedAccessControlSha256', $ExpectedAccessControlSha256,
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
$cleanup = Stop-OwnedHancomProcesses -StartedAt $startedAt -SessionId $currentSessionId -ExpectedSha256 $ExpectedExecutableSha256
Start-Sleep -Milliseconds 250
$remainingHwp = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
$progress = Read-ProgressJournal -Path $progressFile -ExpectedWorkerProcessId $child.Id

$inner = $null
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    $innerItem = Get-Item -LiteralPath $innerTrace -Force
    if (($innerItem.Attributes -band
            [System.IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $innerItem.Length -gt 0 -and
        $innerItem.Length -le 1048576) {
        try {
            $inner = Get-Content -LiteralPath $innerTrace -Raw -Encoding UTF8 |
                ConvertFrom-Json
        }
        catch { $inner = $null }
    }
}
$innerValid = $null -ne $inner -and
    [string]$inner.schema_version -ceq
        'hwpx-agent.p06-09-hancom-2020-table-pending-22-target-batch-engine/v1' -and
    [string]$inner.target.prog_id -ceq $ProgId -and
    [string]$inner.target.registry_view -ceq 'Registry32' -and
    [string]$inner.target.client -ceq 'windows_powershell_x86_sta' -and
    [string]$inner.target.file_version -ceq $ExpectedBuild -and
    [string]$inner.target.executable_sha256 -ceq $ExpectedExecutableSha256 -and
    [string]$inner.session_strategy -ceq 'single_hwp_process_for_22_cases' -and
    [string]$inner.access_approval_strategy -ceq
        'user_selects_allow_all_once' -and
    [string]$inner.access_control.source -ceq
        'verified_hancom_saved_table_012_control' -and
    [string]$inner.access_control.input_file -ceq
        [string]$script:accessControl.file -and
    [string]$inner.access_control.input_sha256 -ceq
        [string]$script:accessControl.sha256 -and
    ($inner.access_control.input_unchanged -is [bool]) -and
    (Test-BoundedAccessControlEvidence -AccessControl $inner.access_control) -and
    [string]$inner.access_control.open_state -match
        '^(not_run|running|pass|failed)$' -and
    [string]$inner.access_control.close_state -match
        '^(not_run|running|pass|failed)$' -and
    [long]$inner.case_count -eq 22 -and
    -not [bool]$inner.raw_document_text_present -and
    -not [bool]$inner.user_document_scanned -and
    -not [bool]$inner.external_network_invoked -and
    -not [bool]$inner.registry_or_system_setting_changed -and
    -not [bool]$inner.computer_use_click_or_type_invoked
if (-not $innerValid) { $inner = $null }

$successEvidence = $null -ne $inner -and
    (Test-SuccessEvidence -Trace $inner -Cases $allCases)
$wrapperError = if (-not $exitedWithinTimeout) {
    'TABLE_PENDING_22_TARGET_TIMEOUT'
}
elseif (-not $outputDrained) {
    'TABLE_PENDING_22_TARGET_CHILD_OUTPUT_DRAIN_TIMEOUT'
}
elseif ($null -eq $inner) {
    'TABLE_PENDING_22_TARGET_INNER_TRACE_MISSING_OR_INVALID'
}
elseif ($childExitCode -ne 0 -or [string]$inner.state -cne 'pass') {
    if ($null -ne $inner.error_code) {
        [string]$inner.error_code
    }
    else { 'TABLE_PENDING_22_TARGET_CHILD_FAILED' }
}
elseif (-not $successEvidence) {
    'TABLE_PENDING_22_TARGET_CASE_EVIDENCE_INVALID'
}
elseif (-not [bool]$progress.valid -or
    [string]$progress.last_phase -cne 'terminal' -or
    [string]$progress.last_state -cne 'pass') {
    'TABLE_PENDING_22_TARGET_PROGRESS_INVALID'
}
elseif ([int]$cleanup.refused -ne 0 -or
    [int]$cleanup.errors -ne 0 -or
    $remainingHwp.Count -ne 0) {
    'TABLE_PENDING_22_TARGET_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

if ($null -eq $inner) {
    $stubCases = @()
    foreach ($case in $allCases) {
        $stubCases += ,[ordered]@{
            group_id = [string]$case.group_id
            group_case_index = [int]$case.group_case_index
            case_id = [string]$case.case_id
            feature_id = [string]$case.feature_id
            capability_id = [string]$case.capability_id
            manifest_sha256 = [string]$case.manifest_sha256
            input_file = [string]$case.input_file
            input_sha256 = [string]$case.input_sha256
            input_unchanged = (
                Get-Sha256File -Path ([string]$case.input_path)
            ) -ceq [string]$case.input_sha256
            input_text_sha256 = $null
            output_file = [System.IO.Path]::GetFileName([string]$case.output_path)
            output_sha256 = if (Test-Path -LiteralPath ([string]$case.output_path) -PathType Leaf) {
                Get-Sha256File -Path ([string]$case.output_path)
            }
            else { $null }
            output_text_sha256 = $null
            output_saved = Test-Path -LiteralPath ([string]$case.output_path) -PathType Leaf
            render_pdf_file = [System.IO.Path]::GetFileName([string]$case.pdf_path)
            render_pdf_saved = Test-Path -LiteralPath ([string]$case.pdf_path) -PathType Leaf
            render_pdf_sha256 = if (Test-Path -LiteralPath ([string]$case.pdf_path) -PathType Leaf) {
                Get-Sha256File -Path ([string]$case.pdf_path)
            }
            else { $null }
            render_pdf_bytes = if (Test-Path -LiteralPath ([string]$case.pdf_path) -PathType Leaf) {
                [long](Get-Item -LiteralPath ([string]$case.pdf_path)).Length
            }
            else { $null }
            render_pdf_signature_valid = $false
            render_pdf_export_method = $null
            phases = $null
            error_code = $wrapperError
            failed_phase = $progress.observed_phase
        }
    }
    $trace = [pscustomobject][ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-pending-22-target-batch-readback/v1'
        state = 'failed'
        delegated_engine_schema = $null
        target = $null
        session_strategy = 'single_hwp_process_for_22_cases'
        access_approval_strategy = 'user_selects_allow_all_once'
        access_approval_user_owned = $true
        access_control = [ordered]@{
            source = 'verified_hancom_saved_table_012_control'
            input_file = [string]$script:accessControl.file
            input_sha256 = [string]$script:accessControl.sha256
            input_unchanged = (
                Get-Sha256File -Path ([string]$script:accessControl.path)
            ) -ceq [string]$script:accessControl.sha256
            retry_policy = 'one_same_session_retry_after_first_false'
            open_attempt_count = 0
            first_open_returned_false = $false
            open_state = 'not_run'
            close_state = 'not_run'
        }
        manifest_sha256 = [ordered]@{
            merge_split = $ExpectedMergeSplitManifestSha256
            layout_placement = $ExpectedLayoutPlacementManifestSha256
            remaining = $ExpectedRemainingManifestSha256
        }
        case_count = 22
        completed_case_count = 0
        cases = $stubCases
        failed_feature_id = $progress.observed_feature_id
        error_code = $wrapperError
        failed_phase = $progress.observed_phase
        exception_type = $null
        exception_hresult = $null
        raw_document_text_present = $false
        user_document_scanned = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
        window_visible_for_user_access = [bool]$progress.window_visible_for_user_access
    }
}
else {
    $engineSchema = [string]$inner.schema_version
    $inner.schema_version =
        'hwpx-agent.p06-09-table-pending-22-target-batch-readback/v1'
    $inner | Add-Member -NotePropertyName delegated_engine_schema -NotePropertyValue $engineSchema -Force
    $inner | Add-Member -NotePropertyName access_approval_user_owned -NotePropertyValue $true -Force
    for ($index = 0; $index -lt @($inner.cases).Count; $index += 1) {
        $inner.cases[$index].input_unchanged = (
            Get-Sha256File -Path ([string]$allCases[$index].input_path)
        ) -ceq [string]$allCases[$index].input_sha256
    }
    if ($null -ne $wrapperError) {
        $inner.state = if ($wrapperError.EndsWith(
            '_PROCESS_CLEANUP_UNVERIFIED'
        )) { 'unverified' } else { 'failed' }
        $inner.error_code = $wrapperError
        if ($childExitCode -eq 0) {
            $inner.failed_phase = 'watchdog'
        }
    }
    $trace = $inner
}

$trace | Add-Member -NotePropertyName watchdog -NotePropertyValue ([ordered]@{
    timeout_seconds = $TimeoutSeconds
    timed_out = -not $exitedWithinTimeout
    child_exit_code = $childExitCode
    output_drained = $outputDrained
    cleaned_process_count = [int]$cleanup.cleaned
    cleanup_refused_count = [int]$cleanup.refused
    cleanup_error_count = [int]$cleanup.errors
    remaining_hwp_process_count = $remainingHwp.Count
    progress_present = [bool]$progress.present
    progress_valid = [bool]$progress.valid
    progress_event_count = [int]$progress.event_count
    progress_last_phase = $progress.last_phase
    progress_last_state = $progress.last_state
    progress_observed_phase = $progress.observed_phase
    progress_observed_feature_id = $progress.observed_feature_id
    progress_worker_process_id = $progress.worker_process_id
    progress_hwp_process_id = $progress.hwp_process_id
    window_visible_for_user_access = [bool]$progress.window_visible_for_user_access
}) -Force

$json = $trace | ConvertTo-Json -Depth 14
Write-NewUtf8File -Path $traceFile -Content $json
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    [System.IO.File]::Delete($innerTrace)
}
$child.Dispose()
$json
if ($null -ne $wrapperError -or [string]$trace.state -cne 'pass') {
    exit 2
}
exit 0
