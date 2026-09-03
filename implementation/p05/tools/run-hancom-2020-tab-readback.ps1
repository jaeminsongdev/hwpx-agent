[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedTextSha256,
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
        return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
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

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null
    )

    $script:progressSequence += 1
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p05-hancom-readback-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
    }
    $line = $event | ConvertTo-Json -Compress
    if ($script:progressSequence -eq 1) {
        Write-NewUtf8File -Path $script:progressFile -Content $line
    }
    else {
        $encoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::AppendAllText($script:progressFile, "`n$line", $encoding)
    }
}

function ConvertTo-CanonicalText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC).TrimEnd([char]"`n")
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'TAB_READBACK_VERSION_PARSE_FAILED' }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)

    $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $progIdKey = $null
    $clsidSubKey = $null
    $clsidKey = $null
    $serverKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($RequestedProgId)
        if ($null -eq $progIdKey) { throw 'TAB_READBACK_PROGID_NOT_REGISTERED' }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) { throw 'TAB_READBACK_CLSID_MISSING' }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $serverKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $serverKey) { throw 'TAB_READBACK_LOCALSERVER32_MISSING' }
        $command = [string]$serverKey.GetValue('')
    }
    finally {
        foreach ($key in @($serverKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'TAB_READBACK_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

$inputItem = Get-Item -LiteralPath $InputPath -Force
if ($inputItem.PSIsContainer -or
    ($inputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $inputItem.Length -le 0 -or $inputItem.Length -gt 8388608) {
    throw 'TAB_READBACK_INPUT_NOT_BOUNDED_REGULAR_FILE'
}
$input = $inputItem.FullName
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $input)).Path.TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'TAB_READBACK_FIXTURE_BOUNDARY_REPARSE_POINT'
}
$output = [System.IO.Path]::GetFullPath($OutputPath)
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = if ([string]::IsNullOrWhiteSpace($ProgressPath)) {
    $traceFile + '.progress.jsonl'
}
else { [System.IO.Path]::GetFullPath($ProgressPath) }
$script:progressSequence = 0
foreach ($candidate in @($output, $traceFile, $script:progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'TAB_READBACK_PATH_OUTSIDE_FIXTURE_BOUNDARY'
    }
}
if ([System.IO.Path]::GetExtension($input) -cne '.hwpx' -or
    [System.IO.Path]::GetExtension($output) -cne '.hwpx') {
    throw 'TAB_READBACK_HWPX_EXTENSION_REQUIRED'
}
if ((Test-Path -LiteralPath $output) -or
    (Test-Path -LiteralPath $traceFile) -or
    (Test-Path -LiteralPath $script:progressFile)) {
    throw 'TAB_READBACK_OUTPUT_ALREADY_EXISTS'
}
if ((Get-Sha256File -Path $input) -cne $ExpectedInputSha256) {
    throw 'TAB_READBACK_INPUT_SHA256_MISMATCH'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TAB_READBACK_PREEXISTING_HWP_PROCESS'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'TAB_READBACK_TARGET_IDENTITY_MISMATCH'
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.p05-04-hancom-2020-tab-readback/v1'
    state = 'failed'
    target = [ordered]@{
        prog_id = $ProgId
        registry_view = 'Registry32'
        client = 'windows_powershell_x86_sta'
        file_version = $identity.file_version
        executable_sha256 = $identity.sha256
    }
    input_sha256 = $ExpectedInputSha256
    input_unchanged = $false
    input_text_sha256 = $null
    output_sha256 = $null
    output_text_sha256 = $null
    output_saved = $false
    phases = [ordered]@{
        com_create = 'not_run'
        open_input = 'not_run'
        read_input = 'not_run'
        save_as_hwpx = 'not_run'
        close_input = 'not_run'
        reopen_output = 'not_run'
        read_output = 'not_run'
        close_output = 'not_run'
        quit = 'not_run'
    }
    error_code = $null
    failed_phase = $null
    exception_type = $null
    exception_hresult = $null
    raw_document_text_present = $false
    user_document_scanned = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_user_access = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$phase = 'com_create'
$hwpProcessId = $null
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'TAB_READBACK_CLIENT_NOT_STA'
    }
    $result.phases.com_create = 'running'
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'TAB_READBACK_AUTOMATION_VERSION_MISMATCH'
    }
    $result.phases.com_create = 'pass'

    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -eq 1) { $hwpProcessId = [int]$hwpProcesses[0].ProcessId }
    Write-ProgressEvent -Phase 'com_create' -State 'pass' -HwpProcessId $hwpProcessId

    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'TAB_READBACK_DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $result.window_visible_for_user_access = $true

    $phase = 'open_input'
    $result.phases.open_input = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    if ($document.Open($input, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'TAB_READBACK_INPUT_OPEN_RETURNED_FALSE'
    }
    [void]$document.SetActive_XHwpDocument()
    $result.phases.open_input = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'read_input'
    $result.phases.read_input = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $inputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $result.input_text_sha256 = Get-Sha256String -Value $inputText
    if ($result.input_text_sha256 -cne $ExpectedTextSha256) {
        throw 'TAB_READBACK_INPUT_TEXT_MISMATCH'
    }
    $result.phases.read_input = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'save_as_hwpx'
    $result.phases.save_as_hwpx = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.SaveAs($output, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $output -PathType Leaf)) {
        throw 'TAB_READBACK_SAVE_OUTPUT_MISSING'
    }
    $result.output_saved = $true
    $result.output_sha256 = Get-Sha256File -Path $output
    $result.phases.save_as_hwpx = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'close_input'
    $result.phases.close_input = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $result.phases.close_input = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'reopen_output'
    $result.phases.reopen_output = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'TAB_READBACK_REOPEN_DOCUMENT_ADD_FAILED' }
    if ($document.Open($output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'TAB_READBACK_OUTPUT_OPEN_RETURNED_FALSE'
    }
    [void]$document.SetActive_XHwpDocument()
    $result.phases.reopen_output = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'read_output'
    $result.phases.read_output = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $outputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $result.output_text_sha256 = Get-Sha256String -Value $outputText
    if ($result.output_text_sha256 -cne $ExpectedTextSha256) {
        throw 'TAB_READBACK_OUTPUT_TEXT_MISMATCH'
    }
    $result.phases.read_output = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'close_output'
    $result.phases.close_output = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $result.phases.close_output = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'quit'
    $result.phases.quit = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $hwp.Quit()
    $result.phases.quit = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
    $result.input_unchanged = (Get-Sha256File -Path $input) -ceq $ExpectedInputSha256
    if (-not $result.input_unchanged) { throw 'TAB_READBACK_INPUT_CHANGED' }
    $result.state = 'pass'
}
catch {
    $result.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TAB_READBACK_EXCEPTION' }
    $result.failed_phase = $phase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    if ($result.phases.Contains($phase)) { $result.phases[$phase] = 'failed' }
    Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId
}
finally {
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
        Clear-ComObject -Value $document
    }
    Clear-ComObject -Value $documents
    Clear-ComObject -Value $window
    if ($null -ne $hwp -and $result.phases.quit -ne 'pass') {
        try {
            $hwp.Quit()
            $result.phases.quit = 'pass'
        }
        catch { $result.phases.quit = 'failed' }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-ProgressEvent -Phase 'terminal' -State $(if ($result.state -eq 'pass') { 'pass' } else { 'failed' }) -HwpProcessId $hwpProcessId
Write-NewUtf8File -Path $traceFile -Content ($result | ConvertTo-Json -Depth 8)
$result | ConvertTo-Json -Depth 8
if ($result.state -ne 'pass') { exit 2 }
