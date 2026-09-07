[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$PdfPath,
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

function ConvertTo-CanonicalText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC).TrimEnd([char]"`n")
}

function Write-NewJson {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][object]$Value)
    $content = $Value | ConvertTo-Json -Depth 10
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
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

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null
    )
    $script:progressSequence += 1
    $progressRecord = [ordered]@{
        schema_version = 'hwpx-agent.p06-06-hancom-2020-formula-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
        raw_formula_or_command_present = $false
    }
    $line = $progressRecord | ConvertTo-Json -Compress
    if ($script:progressSequence -eq 1) {
        Write-NewUtf8File -Path $script:progressFile -Content $line
    }
    else {
        $encoding = [System.Text.UTF8Encoding]::new($false)
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
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function Invoke-ActionRun {
    param([Parameter(Mandatory)][object]$Hwp, [Parameter(Mandatory)][string]$Action)
    $value = $Hwp.HAction.Run($Action)
    if ($value -eq $false) { throw ('ACTION_FAILED_' + $Action.ToUpperInvariant()) }
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

function Assert-FormulaVisibleText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text)

    $first = $Text.IndexOf('17', [System.StringComparison]::Ordinal)
    $second = $Text.IndexOf('25', [System.StringComparison]::Ordinal)
    $result = $Text.IndexOf('42', [System.StringComparison]::Ordinal)
    if ($first -lt 0 -or $second -le $first -or $result -le $second) {
        throw 'FORMULA_VISIBLE_TEXT_MISMATCH'
    }
}

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }
$output = [System.IO.Path]::GetFullPath($OutputPath)
$pdf = [System.IO.Path]::GetFullPath($PdfPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $output)).TrimEnd('\')
foreach ($candidate in @($output, $pdf, $traceFile, $script:progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'OUTPUT_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'OUTPUT_ALREADY_EXISTS' }
}
if ([System.IO.Path]::GetExtension($output) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($pdf) -cne '.pdf' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json') {
    throw 'OUTPUT_EXTENSION_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'PREEXISTING_HWP_PROCESS'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-06-hancom-2020-formula-source/v1'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    hwp_process_id = $null
    active_document_bound = $false
    table_create = 'not_run'
    operand_cells_written = 0
    formula_action = 'not_run'
    pre_save_visible_formula = $false
    pre_save_text_sha256 = $null
    save_hwpx = 'not_run'
    reopen_hwpx = 'not_run'
    reopen_visible_formula = $false
    reopen_text_sha256 = $null
    save_pdf = 'not_run'
    output_hwpx_sha256 = $null
    output_pdf_sha256 = $null
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
$phase = 'com_create'
$hwpProcessId = $null
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
    $trace.hwp_process_id = [int]$process.ProcessId
    $hwpProcessId = [int]$process.ProcessId
    $trace.executable_sha256 = $ExpectedExecutableSha256

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

    $phase = 'formula_source'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    Write-ExactText -Hwp $hwp -Text '17'
    $trace.operand_cells_written += 1
    Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
    Write-ExactText -Hwp $hwp -Text '25'
    $trace.operand_cells_written += 1
    Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell'
    Invoke-ActionRun -Hwp $hwp -Action 'TableFormulaSumHor'
    $trace.formula_action = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'pre_save_semantic'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $preSaveText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-FormulaVisibleText -Text $preSaveText
    $trace.pre_save_visible_formula = $true
    $trace.pre_save_text_sha256 = Get-Sha256String -Value (
        ConvertTo-CanonicalText -Value $preSaveText
    )
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'save_hwpx'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($output, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'HWPX_OUTPUT_MISSING' }
    $trace.output_hwpx_sha256 = Get-Sha256File -Path $output
    $trace.save_hwpx = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'close_before_reopen'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.Close($false)
    Clear-ComObject $document
    $document = $null
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'reopen_hwpx'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $document = $documents.Add($false)
    if ($null -eq $document -or $document.Open($output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'HWPX_REOPEN_FAILED'
    }
    [void]$document.SetActive_XHwpDocument()
    $reopenText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-FormulaVisibleText -Text $reopenText
    $trace.reopen_visible_formula = $true
    $trace.reopen_text_sha256 = Get-Sha256String -Value (
        ConvertTo-CanonicalText -Value $reopenText
    )
    $trace.reopen_hwpx = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'save_pdf'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($pdf, 'PDF', '')
    if (-not (Test-Path -LiteralPath $pdf -PathType Leaf)) { throw 'PDF_OUTPUT_MISSING' }
    $pdfStream = [System.IO.File]::OpenRead($pdf)
    try {
        $signature = [byte[]]::new(5)
        if ($pdfStream.Read($signature, 0, 5) -ne 5 -or
            [System.Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
            throw 'PDF_SIGNATURE_MISMATCH'
        }
    }
    finally { $pdfStream.Dispose() }
    $trace.output_pdf_sha256 = Get-Sha256File -Path $pdf
    $trace.save_pdf = 'pass'
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'FORMULA_SOURCE_EXCEPTION' }
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
        ($trace.progress_write_failed -or $trace.document_close_failed -or $trace.hwp_quit_failed)) {
        $trace.state = 'failed'
        $trace.failed_phase = 'cleanup'
        $trace.error_code = 'FORMULA_SOURCE_CLEANUP_FAILED'
    }
    Write-NewJson -Path $traceFile -Value $trace
}

Write-ProgressEvent -Phase 'terminal' -State $(if ($trace.state -ceq 'pass') { 'pass' } else { 'failed' }) `
    -HwpProcessId $hwpProcessId

if ($trace.state -cne 'pass') { exit 1 }
