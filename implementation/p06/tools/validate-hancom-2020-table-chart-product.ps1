[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][string]$ExpectedInputSha256,
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
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object {
            $_.ToString('x2')
        }) -join '')
    }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object {
            $_.ToString('x2')
        }) -join '')
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
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-chart-product-progress/v1'
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

function Assert-VisibleSourceText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text)
    $expected = @('Series-A', 'Series-B', 'Category-A', '1', '2', 'Category-B', '3', '4')
    $offset = -1
    foreach ($value in $expected) {
        $next = $Text.IndexOf($value, $offset + 1, [System.StringComparison]::Ordinal)
        if ($next -le $offset) { throw 'TABLE_CHART_VISIBLE_TEXT_MISMATCH' }
        $offset = $next
    }
}

function Assert-BoundedLeaf {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$MaximumBytes
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'BOUNDED_FILE_MISSING'
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt $MaximumBytes) {
        throw 'BOUNDED_FILE_INVALID'
    }
    return $item
}

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }
if ($ExpectedInputSha256 -cnotmatch '^[0-9a-f]{64}$' -or
    $ExpectedExecutableSha256 -cnotmatch '^[0-9a-f]{64}$') {
    throw 'EXPECTED_DIGEST_INVALID'
}

$input = [System.IO.Path]::GetFullPath($InputPath)
$output = [System.IO.Path]::GetFullPath($OutputPath)
$pdf = [System.IO.Path]::GetFullPath($PdfPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0

if ([System.IO.Path]::GetExtension($input) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($output) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($pdf) -cne '.pdf' -or
    [System.IO.Path]::GetExtension($traceFile) -cne '.json' -or
    -not $script:progressFile.EndsWith('.jsonl', [System.StringComparison]::Ordinal)) {
    throw 'PATH_EXTENSION_INVALID'
}
$inputItem = Assert-BoundedLeaf -Path $input -MaximumBytes 16777216
if ((Get-Sha256File -Path $input) -cne $ExpectedInputSha256) {
    throw 'INPUT_DIGEST_MISMATCH'
}
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $output)).TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (-not $boundaryItem.PSIsContainer -or
    ($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'OUTPUT_BOUNDARY_INVALID'
}
$outputs = @($output, $pdf, $traceFile, $script:progressFile)
if (($outputs | Sort-Object -Unique).Count -ne $outputs.Count) {
    throw 'OUTPUT_PATH_COLLISION'
}
foreach ($candidate in $outputs) {
    $parent = [System.IO.Path]::GetFullPath((Split-Path -Parent $candidate)).TrimEnd('\')
    if (-not $parent.Equals($boundary, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not $candidate.StartsWith(
            $boundary + '\',
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        throw 'OUTPUT_OUTSIDE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) { throw 'OUTPUT_ALREADY_EXISTS' }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'PREEXISTING_HWP_PROCESS'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-chart-product/v1'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    input_hwpx_sha256 = $ExpectedInputSha256
    input_hwpx_size = [long]$inputItem.Length
    output_hwpx_sha256 = $null
    output_hwpx_size = $null
    render_pdf_sha256 = $null
    render_pdf_size = $null
    hwp_process_id = $null
    hwp_process_identity_bound = $false
    window_visible_for_user_access = $false
    input_open = 'not_run'
    hwp_save_as = 'not_run'
    saved_reopen = 'not_run'
    pdf_export = 'not_run'
    input_visible_text_sha256 = $null
    output_visible_text_sha256 = $null
    source_text_preserved = $false
    save_reopen_verified = $false
    actual_hangul_2020 = $false
    actual_hwpx_open = $false
    actual_hwpx_save_reopen = $false
    actual_pdf_export = $false
    render_visual_verified = $false
    user_attested_visual = $false
    automation_differential = 'not_run'
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
    progress_write_failed = $false
    document_close_failed = $false
    hwp_quit_failed = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
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
        (Get-Sha256File -Path ([string]$process.ExecutablePath)) -cne
            $ExpectedExecutableSha256) {
        throw 'HWP_EXECUTABLE_IDENTITY_MISMATCH'
    }
    $trace.executable_sha256 = $ExpectedExecutableSha256
    $trace.hwp_process_id = [int]$process.ProcessId
    $trace.hwp_process_identity_bound = $true
    $trace.actual_hangul_2020 = $true
    $hwpProcessId = [int]$process.ProcessId

    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.window_visible_for_user_access = $true
    [void]$document.SetActive_XHwpDocument()
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'input_open'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    if ($document.Open($input, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'INPUT_OPEN_FAILED'
    }
    $inputText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleSourceText -Text $inputText
    $trace.input_visible_text_sha256 = Get-Sha256String -Value $inputText
    $trace.input_open = 'pass'
    $trace.actual_hwpx_open = $true
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'save_as'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($output, 'HWPX', '')
    [void](Assert-BoundedLeaf -Path $output -MaximumBytes 16777216)
    $trace.output_hwpx_sha256 = Get-Sha256File -Path $output
    $trace.output_hwpx_size = (Get-Item -LiteralPath $output -Force).Length
    $trace.hwp_save_as = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'saved_reopen'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.Close($false)
    Clear-ComObject $document
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'REOPEN_DOCUMENT_ADD_FAILED' }
    [void]$document.SetActive_XHwpDocument()
    if ($document.Open($output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'SAVED_REOPEN_FAILED'
    }
    $outputText = [string]$hwp.GetTextFile('UNICODE', '')
    Assert-VisibleSourceText -Text $outputText
    $trace.output_visible_text_sha256 = Get-Sha256String -Value $outputText
    $trace.source_text_preserved =
        $trace.output_visible_text_sha256 -ceq $trace.input_visible_text_sha256
    if (-not $trace.source_text_preserved) { throw 'SAVED_VISIBLE_TEXT_DRIFT' }
    $trace.saved_reopen = 'pass'
    $trace.save_reopen_verified = $true
    $trace.actual_hwpx_save_reopen = $true
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'pdf_export'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($pdf, 'PDF', '')
    [void](Assert-BoundedLeaf -Path $pdf -MaximumBytes 67108864)
    $trace.render_pdf_sha256 = Get-Sha256File -Path $pdf
    $trace.render_pdf_size = (Get-Item -LiteralPath $pdf -Force).Length
    $trace.pdf_export = 'pass'
    $trace.actual_pdf_export = $true
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_CHART_PRODUCT_EXCEPTION' }
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    try { Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId }
    catch { $trace.progress_write_failed = $true }
}
finally {
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
        $trace.error_code = 'TABLE_CHART_PRODUCT_CLEANUP_FAILED'
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
