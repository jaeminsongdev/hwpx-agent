[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BaselinePath,
    [Parameter(Mandatory)][string]$UngroupedPath,
    [Parameter(Mandatory)][string]$GroupedPath,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgressPath = '',
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
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

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Write-NewJson {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][object]$Value)
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes(
        ($Value | ConvertTo-Json -Depth 10)
    )
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null
    )
    $script:progressSequence += 1
    $record = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-number-format-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
        raw_formula_or_command_present = $false
    }
    $line = $record | ConvertTo-Json -Compress
    $encoding = [System.Text.UTF8Encoding]::new($false)
    if ($script:progressSequence -eq 1) {
        $stream = [System.IO.File]::Open(
            $script:progressFile,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::Read
        )
        try {
            $bytes = $encoding.GetBytes($line)
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush($true)
        }
        finally { $stream.Dispose() }
    }
    else {
        [System.IO.File]::AppendAllText($script:progressFile, "`n$line", $encoding)
    }
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)
    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'VERSION_FORMAT_INVALID' }
    return (@('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }) -join '.'
}

function Invoke-ActionRun {
    param([Parameter(Mandatory)][object]$Hwp, [Parameter(Mandatory)][string]$Action)
    if ($Hwp.HAction.Run($Action) -eq $false) {
        throw ('ACTION_FAILED_' + $Action.ToUpperInvariant())
    }
}

function Write-ExactText {
    param([Parameter(Mandatory)][object]$Hwp, [Parameter(Mandatory)][string]$Text)
    $parameter = $Hwp.HParameterSet.HInsertText
    $hset = $parameter.HSet
    try {
        if ($Hwp.HAction.GetDefault('InsertText', $hset) -eq $false) {
            throw 'INSERT_TEXT_GET_DEFAULT_FAILED'
        }
        $parameter.Text = $Text
        if ($Hwp.HAction.Execute('InsertText', $hset) -eq $false) {
            throw 'INSERT_TEXT_EXECUTE_FAILED'
        }
    }
    finally { Clear-ComObject $hset; Clear-ComObject $parameter }
}

function Assert-VisibleCaseRowSequence {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory)][ValidateSet('baseline', 'ungrouped', 'grouped')][string]$Mode,
        [Parameter(Mandatory)][object[]]$Cases
    )
    $cursor = -1
    foreach ($case in $Cases) {
        $left = $Text.IndexOf([string]$case.left, $cursor + 1, [System.StringComparison]::Ordinal)
        $right = $Text.IndexOf([string]$case.right, $left + 1, [System.StringComparison]::Ordinal)
        $result = if ($Mode -ceq 'ungrouped') {
            $Text.IndexOf([string]$case.ungrouped, $right + 1, [System.StringComparison]::Ordinal)
        }
        elseif ($Mode -ceq 'grouped') {
            $Text.IndexOf([string]$case.grouped, $right + 1, [System.StringComparison]::Ordinal)
        }
        else {
            $plain = $Text.IndexOf([string]$case.baseline_plain, $right + 1,
                [System.StringComparison]::Ordinal)
            $withGrouping = $Text.IndexOf([string]$case.baseline_grouped, $right + 1,
                [System.StringComparison]::Ordinal)
            if ($plain -ge 0 -and ($withGrouping -lt 0 -or $plain -lt $withGrouping)) {
                $plain
            }
            else { $withGrouping }
        }
        if ($left -le $cursor -or $right -le $left -or $result -le $right) {
            throw ('NUMBER_FORMAT_VISIBLE_TEXT_MISMATCH_' + $Mode.ToUpperInvariant())
        }
        $cursor = $result
    }
}

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }

$baseline = [System.IO.Path]::GetFullPath($BaselinePath)
$ungrouped = [System.IO.Path]::GetFullPath($UngroupedPath)
$grouped = [System.IO.Path]::GetFullPath($GroupedPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $baseline)).TrimEnd('\')
$uniquePaths = @($baseline, $ungrouped, $grouped, $traceFile, $script:progressFile) |
    Sort-Object -Unique
if ($uniquePaths.Count -ne 5) {
    throw 'OUTPUT_PATH_COLLISION'
}
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'OUTPUT_BOUNDARY_INVALID'
}
foreach ($candidate in @($baseline, $ungrouped, $grouped, $traceFile, $script:progressFile)) {
    $candidateParent = [System.IO.Path]::GetFullPath(
        (Split-Path -Parent $candidate)
    ).TrimEnd('\')
    if (-not $candidateParent.Equals(
        $boundary,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'OUTPUT_OUTSIDE_BOUNDARY'
    }
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'OUTPUT_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'OUTPUT_ALREADY_EXISTS' }
}
if ([System.IO.Path]::GetExtension($baseline) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($ungrouped) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($grouped) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json' -or
    -not $script:progressFile.EndsWith('.jsonl', [System.StringComparison]::Ordinal)) {
    throw 'OUTPUT_EXTENSION_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'PREEXISTING_HWP_PROCESS'
}

$formatCases = @(
    [pscustomobject][ordered]@{ id = 'general'; left = '1000'; right = '100';
        baseline_plain = '1100'; baseline_grouped = '1,100';
        ungrouped = '1100'; grouped = '1,100' },
    [pscustomobject][ordered]@{ id = 'integer'; left = '1010'; right = '101';
        baseline_plain = '1111'; baseline_grouped = '1,111';
        ungrouped = '1111'; grouped = '1,111' },
    [pscustomobject][ordered]@{ id = 'decimal_1'; left = '1020'; right = '102';
        baseline_plain = '1122'; baseline_grouped = '1,122';
        ungrouped = '1122.0'; grouped = '1,122.0' },
    [pscustomobject][ordered]@{ id = 'decimal_2'; left = '1030'; right = '103';
        baseline_plain = '1133'; baseline_grouped = '1,133';
        ungrouped = '1133.00'; grouped = '1,133.00' },
    [pscustomobject][ordered]@{ id = 'decimal_3'; left = '1040'; right = '104';
        baseline_plain = '1144'; baseline_grouped = '1,144';
        ungrouped = '1144.000'; grouped = '1,144.000' },
    [pscustomobject][ordered]@{ id = 'decimal_4'; left = '1050'; right = '105';
        baseline_plain = '1155'; baseline_grouped = '1,155';
        ungrouped = '1155.0000'; grouped = '1,155.0000' }
)

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-number-format-source/v1'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    hwp_process_id = $null
    active_document_bound = $false
    table_create = 'not_run'
    operand_cells_written = 0
    formula_actions_passed = 0
    manual_format_dialogs_passed = 0
    delete_grouping_actions_passed = 0
    insert_grouping_actions_passed = 0
    format_case_count = $formatCases.Count
    manual_ui_source_authoring_required = $true
    baseline_visible_text_sha256 = $null
    ungrouped_visible_text_sha256 = $null
    grouped_visible_text_sha256 = $null
    baseline_hwpx_sha256 = $null
    ungrouped_hwpx_sha256 = $null
    grouped_hwpx_sha256 = $null
    state = 'failed'
    failed_phase = $null
    error_code = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    raw_document_text_present = $false
    raw_formula_or_command_present = $false
    user_document_opened = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_user_access = $false
    progress_write_failed = $false
    document_close_failed = $false
    hwp_quit_failed = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$creation = $null
$creationHSet = $null
$hwpProcessId = $null
$phase = 'com_create'
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    Write-ProgressEvent -Phase $phase -State 'running'
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'STA_REQUIRED'
    }
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'AUTOMATION_VERSION_MISMATCH'
    }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction Stop)
    if ($processes.Count -ne 1) { throw 'OWNED_HWP_PROCESS_CARDINALITY' }
    $process = $processes[0]
    if ([string]::IsNullOrWhiteSpace([string]$process.ExecutablePath) -or
        (Get-Sha256File -Path ([string]$process.ExecutablePath)) -cne $ExpectedExecutableSha256) {
        throw 'HWP_EXECUTABLE_IDENTITY_MISMATCH'
    }
    $trace.executable_sha256 = $ExpectedExecutableSha256
    $trace.hwp_process_id = [int]$process.ProcessId
    $hwpProcessId = [int]$process.ProcessId

    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.window_visible_for_user_access = $true
    [void]$document.SetActive_XHwpDocument()
    $trace.active_document_bound = $true
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'table_create'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $creation = $hwp.HParameterSet.HTableCreation
    $creationHSet = $creation.HSet
    if ($hwp.HAction.GetDefault('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_GET_DEFAULT_FAILED'
    }
    $creation.Rows = $formatCases.Count
    $creation.Cols = 3
    if ($hwp.HAction.Execute('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_EXECUTE_FAILED'
    }
    $trace.table_create = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'formula_author'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    for ($index = 0; $index -lt $formatCases.Count; $index += 1) {
        $case = $formatCases[$index]
        Write-ExactText -Hwp $hwp -Text ([string]$case.left)
        $trace.operand_cells_written += 1
        Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
        Write-ExactText -Hwp $hwp -Text ([string]$case.right)
        $trace.operand_cells_written += 1
        Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
        Invoke-ActionRun -Hwp $hwp -Action 'TableFormulaSumHor'
        $trace.formula_actions_passed += 1
        if ($index -lt ($formatCases.Count - 1)) {
            Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
        }
    }
    $baselineText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleCaseRowSequence -Text $baselineText -Mode 'baseline' -Cases $formatCases
    $trace.baseline_visible_text_sha256 = Get-Sha256String -Value $baselineText
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'baseline_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($baseline, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $baseline -PathType Leaf)) {
        throw 'BASELINE_HWPX_MISSING'
    }
    $trace.baseline_hwpx_sha256 = Get-Sha256File -Path $baseline
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $rewindSteps = ($formatCases.Count - 1) * 3
    1..$rewindSteps | ForEach-Object {
        Invoke-ActionRun -Hwp $hwp -Action 'TableLeftCell'
    }
    for ($index = 0; $index -lt $formatCases.Count; $index += 1) {
        $case = $formatCases[$index]
        $phase = 'manual_format_' + [string]$case.id
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
        Invoke-ActionRun -Hwp $hwp -Action 'MoveLineBegin'
        Invoke-ActionRun -Hwp $hwp -Action 'ModifyCtrl'
        $trace.manual_format_dialogs_passed += 1
        Invoke-ActionRun -Hwp $hwp -Action 'DeleteThousandsSeparator'
        $trace.delete_grouping_actions_passed += 1
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
        if ($index -lt ($formatCases.Count - 1)) {
            1..3 | ForEach-Object {
                Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
            }
        }
    }
    $ungroupedText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleCaseRowSequence -Text $ungroupedText -Mode 'ungrouped' -Cases $formatCases
    $trace.ungrouped_visible_text_sha256 = Get-Sha256String -Value $ungroupedText

    $phase = 'ungrouped_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($ungrouped, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $ungrouped -PathType Leaf)) {
        throw 'UNGROUPED_HWPX_MISSING'
    }
    $trace.ungrouped_hwpx_sha256 = Get-Sha256File -Path $ungrouped
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    1..$rewindSteps | ForEach-Object {
        Invoke-ActionRun -Hwp $hwp -Action 'TableLeftCell'
    }
    for ($index = 0; $index -lt $formatCases.Count; $index += 1) {
        $case = $formatCases[$index]
        $phase = 'grouping_add_' + [string]$case.id
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
        Invoke-ActionRun -Hwp $hwp -Action 'MoveLineBegin'
        Invoke-ActionRun -Hwp $hwp -Action 'InsertThousandsSeparator'
        $trace.insert_grouping_actions_passed += 1
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
        if ($index -lt ($formatCases.Count - 1)) {
            1..3 | ForEach-Object {
                Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
            }
        }
    }
    $groupedText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleCaseRowSequence -Text $groupedText -Mode 'grouped' -Cases $formatCases
    $trace.grouped_visible_text_sha256 = Get-Sha256String -Value $groupedText

    $phase = 'grouped_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($grouped, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $grouped -PathType Leaf)) {
        throw 'GROUPED_HWPX_MISSING'
    }
    $trace.grouped_hwpx_sha256 = Get-Sha256File -Path $grouped
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_NUMBER_FORMAT_SOURCE_EXCEPTION' }
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    try { Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId }
    catch { $trace.progress_write_failed = $true }
}
finally {
    Clear-ComObject $creationHSet
    Clear-ComObject $creation
    if ($null -ne $document) {
        try { [void]$document.Close($false) }
        catch { $trace.document_close_failed = $true }
    }
    if ($null -ne $hwp) {
        try { $hwp.Quit() }
        catch { $trace.hwp_quit_failed = $true }
    }
    Clear-ComObject $window
    Clear-ComObject $document
    Clear-ComObject $documents
    Clear-ComObject $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    if ($trace.state -ceq 'pass' -and
        ($trace.progress_write_failed -or $trace.document_close_failed -or
            $trace.hwp_quit_failed)) {
        $trace.state = 'failed'
        $trace.failed_phase = 'cleanup'
        $trace.error_code = 'TABLE_NUMBER_FORMAT_SOURCE_CLEANUP_FAILED'
    }
}

try {
    Write-ProgressEvent -Phase 'terminal' -State $(
        if ($trace.state -ceq 'pass') { 'pass' } else { 'failed' }
    ) -HwpProcessId $hwpProcessId
}
catch { $trace.progress_write_failed = $true }
Write-NewJson -Path $traceFile -Value $trace
$trace | ConvertTo-Json -Depth 10
if ($trace.state -cne 'pass') { exit 1 }
