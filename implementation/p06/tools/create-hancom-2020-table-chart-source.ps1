[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BaselinePath,
    [Parameter(Mandatory)][string]$ChartPath,
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
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-chart-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
        raw_chart_payload_present = $false
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
        [System.IO.File]::AppendAllText(
            $script:progressFile,
            [Environment]::NewLine + $line,
            $encoding
        )
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

function Assert-VisibleSourceText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text)
    $expected = @('Series-A', 'Series-B', 'Category-A', '1', '2', 'Category-B', '3', '4')
    $offset = -1
    foreach ($value in $expected) {
        $next = $Text.IndexOf($value, $offset + 1, [System.StringComparison]::Ordinal)
        if ($next -le $offset) { throw 'CHART_SOURCE_VISIBLE_TEXT_MISMATCH' }
        $offset = $next
    }
}

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }

$baseline = [System.IO.Path]::GetFullPath($BaselinePath)
$chart = [System.IO.Path]::GetFullPath($ChartPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $baseline)).TrimEnd('\')
$uniquePaths = @($baseline, $chart, $traceFile, $script:progressFile) | Sort-Object -Unique
if ($uniquePaths.Count -ne 4) { throw 'OUTPUT_PATH_COLLISION' }
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'OUTPUT_BOUNDARY_INVALID'
}
foreach ($candidate in @($baseline, $chart, $traceFile, $script:progressFile)) {
    $candidateParent = [System.IO.Path]::GetFullPath(
        (Split-Path -Parent $candidate)
    ).TrimEnd('\')
    if (-not $candidateParent.Equals(
        $boundary,
        [System.StringComparison]::OrdinalIgnoreCase
    ) -or -not $candidate.StartsWith(
        $boundary + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'OUTPUT_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'OUTPUT_ALREADY_EXISTS' }
}
if ([System.IO.Path]::GetExtension($baseline) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($chart) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json' -or
    -not $script:progressFile.EndsWith('.jsonl', [System.StringComparison]::Ordinal)) {
    throw 'OUTPUT_EXTENSION_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'PREEXISTING_HWP_PROCESS'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-chart-source/v1'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    hwp_process_id = $null
    hwp_process_identity_bound = $false
    active_document_bound = $false
    table_create = 'not_run'
    source_cells_written = 0
    baseline_visible_text_sha256 = $null
    baseline_hwpx_sha256 = $null
    cell_block_action_count = 0
    chart_action = 'not_run'
    chart_group = 1
    chart_index = 3
    chart_visible_text_sha256 = $null
    chart_hwpx_sha256 = $null
    source_text_preserved = $false
    state = 'failed'
    failed_phase = $null
    error_code = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    raw_document_text_present = $false
    raw_chart_payload_present = $false
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
$chartAction = $null
$chartSet = $null
$hwpProcessId = $null
$phase = 'com_create'
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    Write-ProgressEvent -Phase $phase -State 'running'
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'STA_REQUIRED'
    }
    $comStartedAt = Get-Date
    $sessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'AUTOMATION_VERSION_MISMATCH'
    }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction Stop)
    if ($processes.Count -ne 1) { throw 'OWNED_HWP_PROCESS_CARDINALITY' }
    $process = $processes[0]
    $processCreatedAt = if ($null -ne $process.CreationDate) {
        [datetime]$process.CreationDate
    }
    else { [datetime]::MinValue }
    if ([int]$process.SessionId -ne $sessionId -or
        $processCreatedAt -lt $comStartedAt.AddSeconds(-2) -or
        [string]$process.CommandLine -notmatch '(?i)-Automation\s+-Embedding\s*$') {
        throw 'HWP_PROCESS_OWNERSHIP_MISMATCH'
    }
    if ([string]::IsNullOrWhiteSpace([string]$process.ExecutablePath) -or
        (Get-Sha256File -Path ([string]$process.ExecutablePath)) -cne $ExpectedExecutableSha256) {
        throw 'HWP_EXECUTABLE_IDENTITY_MISMATCH'
    }
    $trace.executable_sha256 = $ExpectedExecutableSha256
    $trace.hwp_process_id = [int]$process.ProcessId
    $trace.hwp_process_identity_bound = $true
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
    $creation.Rows = 3
    $creation.Cols = 3
    if ($hwp.HAction.Execute('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_EXECUTE_FAILED'
    }
    $trace.table_create = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'source_cells'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $values = @('Series-A', 'Series-B', 'Category-A', '1', '2', 'Category-B', '3', '4')
    Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
    foreach ($value in $values) {
        Write-ExactText -Hwp $hwp -Text $value
        $trace.source_cells_written += 1
        if ($trace.source_cells_written -lt $values.Count) {
            Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
        }
    }
    $baselineText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleSourceText -Text $baselineText
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

    $phase = 'cell_block'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    1..8 | ForEach-Object { Invoke-ActionRun -Hwp $hwp -Action 'TableLeftCell' }
    Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlock'
    $trace.cell_block_action_count += 1
    1..2 | ForEach-Object {
        Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlockExtend'
        $trace.cell_block_action_count += 1
    }
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'chart_create'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $chartAction = $hwp.CreateAction('InsertChart')
    if ($null -eq $chartAction) { throw 'CHART_ACTION_CREATE_FAILED' }
    $chartSet = $chartAction.CreateSet()
    if ($null -eq $chartSet) { throw 'CHART_SET_CREATE_FAILED' }
    if ($chartAction.GetDefault($chartSet) -eq $false) {
        throw 'CHART_GET_DEFAULT_FAILED'
    }
    [void]$chartSet.SetItem('ChartGroup', $trace.chart_group)
    [void]$chartSet.SetItem('ChartIndex', $trace.chart_index)
    if ($chartAction.Execute($chartSet) -eq $false) {
        throw 'CHART_EXECUTE_FAILED'
    }
    $trace.chart_action = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'chart_source_check'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $chartText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleSourceText -Text $chartText
    $trace.chart_visible_text_sha256 = Get-Sha256String -Value $chartText
    $trace.source_text_preserved =
        $trace.chart_visible_text_sha256 -ceq $trace.baseline_visible_text_sha256
    if (-not $trace.source_text_preserved) { throw 'CHART_SOURCE_TEXT_DRIFT' }
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'chart_save'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($chart, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $chart -PathType Leaf)) {
        throw 'CHART_HWPX_MISSING'
    }
    $trace.chart_hwpx_sha256 = Get-Sha256File -Path $chart
    if ($trace.chart_hwpx_sha256 -ceq $trace.baseline_hwpx_sha256) {
        throw 'CHART_HWPX_UNCHANGED'
    }
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_CHART_SOURCE_EXCEPTION' }
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    try { Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId }
    catch { $trace.progress_write_failed = $true }
}
finally {
    Clear-ComObject $chartSet
    Clear-ComObject $chartAction
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
        $trace.error_code = 'TABLE_CHART_SOURCE_CLEANUP_FAILED'
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
