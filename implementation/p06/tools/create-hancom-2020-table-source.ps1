[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$PdfPath,
    [Parameter(Mandatory)][string]$TracePath,
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

function Insert-Marker {
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

if ([IntPtr]::Size -ne 4) { throw 'X86_POWERSHELL_REQUIRED' }
if ($ProgId -cne 'HWPFrame.HwpObject.2') { throw 'PROGID_NOT_ALLOWED' }
if ($ExpectedBuild -cne '11.0.0.9136') { throw 'BUILD_NOT_ALLOWED' }
$output = [System.IO.Path]::GetFullPath($OutputPath)
$pdf = [System.IO.Path]::GetFullPath($PdfPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$boundary = [System.IO.Path]::GetFullPath((Split-Path -Parent $output)).TrimEnd('\')
foreach ($candidate in @($output, $pdf, $traceFile)) {
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
    schema_version = 'hwpx-agent.p06-04-hancom-2020-table-source/v1'
    target_build = $ExpectedBuild
    executable_sha256 = $null
    hwp_process_id = $null
    table_create = 'not_run'
    cells_written = 0
    style_actions_executed = 0
    save_hwpx = 'not_run'
    reopen_hwpx = 'not_run'
    save_pdf = 'not_run'
    output_hwpx_sha256 = $null
    output_pdf_sha256 = $null
    reopen_text_sha256 = $null
    state = 'failed'
    failed_phase = $null
    error_code = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    raw_document_text_present = $false
    user_document_opened = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_user_access = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$creation = $null
$creationHSet = $null
$phase = 'com_create'
try {
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
    $trace.executable_sha256 = $ExpectedExecutableSha256

    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.window_visible_for_user_access = $true

    $phase = 'table_create'
    $creation = $hwp.HParameterSet.HTableCreation
    $creationHSet = $creation.HSet
    if ($hwp.HAction.GetDefault('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_GET_DEFAULT_FAILED'
    }
    $creation.Rows = 2
    $creation.Cols = 2
    if ($hwp.HAction.Execute('TableCreate', $creationHSet) -eq $false) {
        throw 'TABLE_CREATE_EXECUTE_FAILED'
    }
    $trace.table_create = 'pass'

    $phase = 'cell_content_and_style'
    $cases = @(
        [ordered]@{ marker = 'P06-04-A'; align = 'TableCellAlignLeftTop'; direction = 'TableCellTextHorz' },
        [ordered]@{ marker = 'P06-04-B'; align = 'TableCellAlignCenterCenter'; direction = 'TableCellTextHorz' },
        [ordered]@{ marker = 'P06-04-C'; align = 'TableCellAlignRightBottom'; direction = 'TableCellTextVert' },
        [ordered]@{ marker = 'P06-04-D'; align = 'TableCellAlignCenterTop'; direction = 'TableCellTextVertAll' }
    )
    for ($index = 0; $index -lt $cases.Count; $index++) {
        Insert-Marker -Hwp $hwp -Text ([string]$cases[$index].marker)
        $trace.cells_written += 1
        Invoke-ActionRun -Hwp $hwp -Action ([string]$cases[$index].align)
        Invoke-ActionRun -Hwp $hwp -Action ([string]$cases[$index].direction)
        $trace.style_actions_executed += 2
        if ($index -lt $cases.Count - 1) { Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell' }
    }

    $phase = 'save_hwpx'
    [void]$document.SaveAs($output, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'HWPX_OUTPUT_MISSING' }
    $trace.output_hwpx_sha256 = Get-Sha256File -Path $output
    $trace.save_hwpx = 'pass'

    $phase = 'close_before_reopen'
    [void]$document.Close($false)
    Clear-ComObject $document
    $document = $null

    $phase = 'reopen_hwpx'
    $document = $documents.Add($false)
    if ($null -eq $document -or $document.Open($output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'HWPX_REOPEN_FAILED'
    }
    [void]$document.SetActive_XHwpDocument()
    $reopenText = [string]$hwp.GetTextFile('UNICODE', '')
    foreach ($marker in @('P06-04-A', 'P06-04-B', 'P06-04-C', 'P06-04-D')) {
        if (-not $reopenText.Contains($marker)) { throw 'HWPX_REOPEN_MARKER_MISSING' }
    }
    $canonicalReopenText = ConvertTo-CanonicalText -Value $reopenText
    $trace.reopen_text_sha256 = Get-Sha256String -Value $canonicalReopenText
    $trace.reopen_hwpx = 'pass'

    $phase = 'save_pdf'
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
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'TABLE_SOURCE_EXCEPTION' }
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
}
finally {
    Clear-ComObject $creationHSet
    Clear-ComObject $creation
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
    }
    if ($null -ne $hwp) {
        try { $hwp.Quit() } catch { }
    }
    Clear-ComObject $window
    Clear-ComObject $document
    Clear-ComObject $documents
    Clear-ComObject $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Write-NewJson -Path $traceFile -Value $trace
}

if ($trace.state -cne 'pass') { exit 1 }
