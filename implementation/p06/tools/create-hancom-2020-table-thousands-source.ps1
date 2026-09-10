[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BaselinePath,
    [Parameter(Mandatory)][string]$RemovedPath,
    [Parameter(Mandatory)][string]$AddedPath,
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
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-thousands-progress/v1'
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

function Assert-ActionEnabled {
    param([Parameter(Mandatory)][object]$Hwp, [Parameter(Mandatory)][string]$Action)
    if ($Hwp.IsActionEnable($Action) -eq $false) {
        throw ('ACTION_DISABLED_' + $Action.ToUpperInvariant())
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

function Assert-VisibleOperandsAndResult {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory)][ValidateSet('grouped', 'plain')][string]$Mode
    )
    $first = $Text.IndexOf('1200', [System.StringComparison]::Ordinal)
    $second = $Text.IndexOf('3400', [System.StringComparison]::Ordinal)
    $plain = $Text.IndexOf('4600', [System.StringComparison]::Ordinal)
    $grouped = $Text.IndexOf('4,600', [System.StringComparison]::Ordinal)
    $resultValid = if ($Mode -ceq 'grouped') {
        $grouped -gt $second -and $plain -lt 0
    }
    else {
        $plain -gt $second -and $grouped -lt 0
    }
    if ($first -lt 0 -or $second -le $first -or -not $resultValid) {
        throw 'THOUSANDS_VISIBLE_TEXT_MISMATCH'
    }
}

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }

$baseline = [System.IO.Path]::GetFullPath($BaselinePath)
$removed = [System.IO.Path]::GetFullPath($RemovedPath)
$added = [System.IO.Path]::GetFullPath($AddedPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $baseline)).TrimEnd('\')
$uniquePaths = @($baseline, $removed, $added, $traceFile, $script:progressFile) |
    Sort-Object -Unique
if ($uniquePaths.Count -ne 5) {
    throw 'OUTPUT_PATH_COLLISION'
}
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'OUTPUT_BOUNDARY_INVALID'
}
foreach ($candidate in @($baseline, $removed, $added, $traceFile, $script:progressFile)) {
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
    [System.IO.Path]::GetExtension($removed) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($added) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json' -or
    -not $script:progressFile.EndsWith('.jsonl', [System.StringComparison]::Ordinal)) {
    throw 'OUTPUT_EXTENSION_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'PREEXISTING_HWP_PROCESS'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-thousands-source/v2'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    hwp_process_id = $null
    active_document_bound = $false
    table_create = 'not_run'
    operand_cells_written = 0
    formula_action = 'not_run'
    formula_cell_selection = 'not_run'
    baseline_visible_text_sha256 = $null
    delete_thousands_action = 'not_run'
    removed_visible_text_sha256 = $null
    insert_thousands_action = 'not_run'
    added_visible_text_sha256 = $null
    baseline_hwpx_sha256 = $null
    removed_hwpx_sha256 = $null
    added_hwpx_sha256 = $null
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
    $creation.Rows = 1
    $creation.Cols = 3
    if ($hwp.HAction.Execute('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_EXECUTE_FAILED'
    }
    $trace.table_create = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'formula_operands'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Write-ExactText -Hwp $hwp -Text '1200'
    $trace.operand_cells_written += 1
    Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
    Write-ExactText -Hwp $hwp -Text '3400'
    $trace.operand_cells_written += 1
    Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'formula_author'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Invoke-ActionRun -Hwp $hwp -Action 'TableFormulaSumHor'
    $trace.formula_action = 'pass'
    $baselineText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleOperandsAndResult -Text $baselineText -Mode 'grouped'
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

    $phase = 'formula_cell_select'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlock'
    Assert-ActionEnabled -Hwp $hwp -Action 'TableDeleteComma'
    Assert-ActionEnabled -Hwp $hwp -Action 'TableInsertComma'
    $trace.formula_cell_selection = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'delete_thousands'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Assert-ActionEnabled -Hwp $hwp -Action 'TableDeleteComma'
    Invoke-ActionRun -Hwp $hwp -Action 'TableDeleteComma'
    $trace.delete_thousands_action = 'pass'
    $removedText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleOperandsAndResult -Text $removedText -Mode 'plain'
    $trace.removed_visible_text_sha256 = Get-Sha256String -Value $removedText
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'removed_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($removed, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $removed -PathType Leaf)) {
        throw 'REMOVED_HWPX_MISSING'
    }
    $trace.removed_hwpx_sha256 = Get-Sha256File -Path $removed
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'insert_thousands'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Assert-ActionEnabled -Hwp $hwp -Action 'TableInsertComma'
    Invoke-ActionRun -Hwp $hwp -Action 'TableInsertComma'
    $trace.insert_thousands_action = 'pass'
    $addedText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleOperandsAndResult -Text $addedText -Mode 'grouped'
    $trace.added_visible_text_sha256 = Get-Sha256String -Value $addedText
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'added_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($added, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $added -PathType Leaf)) {
        throw 'ADDED_HWPX_MISSING'
    }
    $trace.added_hwpx_sha256 = Get-Sha256File -Path $added
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_THOUSANDS_SOURCE_EXCEPTION' }
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
        $trace.error_code = 'TABLE_THOUSANDS_SOURCE_CLEANUP_FAILED'
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
