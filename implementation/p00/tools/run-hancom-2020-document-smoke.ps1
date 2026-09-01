[CmdletBinding()]
param(
    [string]$OutputRoot,

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$TargetProfileId = 'hancom-hangul-2020-secondary',

    [string]$ExpectedFileVersion = '11.0.0.9136',

    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',

    [ValidateRange(30, 300)]
    [int]$TimeoutSeconds = 120,

    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-NormalizedHancomVersion {
    param([Parameter(Mandatory)][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) {
        return $null
    }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function Assert-PathInsideBoundary {
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Boundary
    )

    $candidateFull = [System.IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (
        -not $candidateFull.Equals($boundaryFull, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $candidateFull.StartsWith($boundaryFull + '\', [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        throw 'OUTPUT_ROOT_OUTSIDE_ALLOWED_BOUNDARY'
    }
    return $candidateFull
}

function Assert-NotReparsePoint {
    param([Parameter(Mandatory)][string]$Path)

    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'OUTPUT_ROOT_REPARSE_POINT_REFUSED'
        }
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) {
        throw 'PROCESS_ARGUMENT_CONTAINS_QUOTE'
    }
    return '"' + $Value + '"'
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
    $localServerKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($RequestedProgId)
        if ($null -eq $progIdKey) {
            throw "32-bit COM ProgID is not registered: $RequestedProgId"
        }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) {
            throw "32-bit COM ProgID has no CLSID: $RequestedProgId"
        }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $localServerKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $localServerKey) {
            throw "32-bit COM CLSID has no LocalServer32: $clsid"
        }
        $serverCommand = [string]$localServerKey.GetValue('')
    }
    finally {
        foreach ($key in @($localServerKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }

    $serverMatch = [regex]::Match(
        $serverCommand.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $serverMatch.Success) {
        throw 'Unable to parse COM LocalServer32 executable.'
    }

    $serverPath = (Resolve-Path -LiteralPath $serverMatch.Groups['path'].Value).Path
    $serverItem = Get-Item -LiteralPath $serverPath
    return [ordered]@{
        clsid = $clsid
        path = $serverPath
        file_version = [string]$serverItem.VersionInfo.FileVersion
        sha256 = (Get-FileHash -LiteralPath $serverPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Test-HwpxPackage {
    param([Parameter(Mandatory)][string]$Path)

    $result = [ordered]@{
        valid = $false
        error_code = $null
        entry_count = 0
        mimetype = $null
        mimetype_stored = $false
        required_entries_present = $false
        section_entry_present = $false
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $result.error_code = 'HWPX_FILE_MISSING'
        return $result
    }

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $stream = $null
    $archive = $null
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Read, $false)
        $entries = @($archive.Entries)
        $result.entry_count = $entries.Count
        $names = @($entries | ForEach-Object { $_.FullName })
        $required = @('mimetype', 'version.xml', 'Contents/content.hpf', 'Contents/header.xml')
        $result.required_entries_present = @($required | Where-Object { $_ -notin $names }).Count -eq 0
        $result.section_entry_present = @($names | Where-Object { $_ -match '^Contents/section\d+\.xml$' }).Count -gt 0

        $mimetypeEntry = $archive.GetEntry('mimetype')
        if ($null -ne $mimetypeEntry) {
            $reader = New-Object System.IO.StreamReader($mimetypeEntry.Open(), [System.Text.Encoding]::ASCII)
            try { $result.mimetype = $reader.ReadToEnd() } finally { $reader.Dispose() }
            $result.mimetype_stored = $mimetypeEntry.CompressedLength -eq $mimetypeEntry.Length
        }

        if (-not $result.required_entries_present) {
            $result.error_code = 'HWPX_REQUIRED_ENTRY_MISSING'
        }
        elseif (-not $result.section_entry_present) {
            $result.error_code = 'HWPX_SECTION_ENTRY_MISSING'
        }
        elseif ($result.mimetype -cne 'application/hwp+zip') {
            $result.error_code = 'HWPX_MIMETYPE_MISMATCH'
        }
        elseif (-not $result.mimetype_stored) {
            $result.error_code = 'HWPX_MIMETYPE_COMPRESSED'
        }
        else {
            $result.valid = $true
        }
    }
    catch {
        $result.error_code = 'HWPX_ZIP_INVALID'
    }
    finally {
        if ($null -ne $archive) { $archive.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
    return $result
}

function Test-PdfArtifact {
    param([Parameter(Mandatory)][string]$Path)

    $result = [ordered]@{
        valid = $false
        error_code = $null
        byte_length = 0
        header = $null
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $result.error_code = 'PDF_FILE_MISSING'
        return $result
    }

    $item = Get-Item -LiteralPath $Path
    $result.byte_length = [int64]$item.Length
    if ($item.Length -lt 5) {
        $result.error_code = 'PDF_FILE_TOO_SHORT'
        return $result
    }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $bytes = New-Object byte[] 5
        $null = $stream.Read($bytes, 0, 5)
        $result.header = [System.Text.Encoding]::ASCII.GetString($bytes)
    }
    finally {
        $stream.Dispose()
    }
    if ($result.header -cne '%PDF-') {
        $result.error_code = 'PDF_HEADER_INVALID'
        return $result
    }
    $result.valid = $true
    return $result
}

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$allowedOutputRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $projectRoot 'implementation\p00\evidence\document-smoke-runs')
).TrimEnd('\')
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = $allowedOutputRoot
}
$resolvedOutputRoot = Assert-PathInsideBoundary -Candidate $OutputRoot -Boundary $allowedOutputRoot
Assert-NotReparsePoint -Path $resolvedOutputRoot

$childScriptPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-document-smoke-child.ps1')).Path
$x86PowerShell = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $x86PowerShell -PathType Leaf)) {
    throw "32-bit Windows PowerShell was not found: $x86PowerShell"
}

$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedFileVersion) {
    throw "Target file version mismatch. Expected $ExpectedFileVersion, observed $($identity.file_version)."
}
if ($identity.sha256 -cne $ExpectedExecutableSha256.ToLowerInvariant()) {
    throw 'Target executable SHA-256 mismatch.'
}

if ($ValidateConfigurationOnly) {
    [ordered]@{
        schema_version = 'hwpx-agent.hancom-document-smoke-config/v1'
        state = 'pass'
        output_boundary = $allowedOutputRoot
        configured_output_root = $resolvedOutputRoot
        child_script = $childScriptPath
        client = 'windows_powershell_x86_sta'
        target_file_version = $identity.file_version
        target_executable_sha256 = $identity.sha256
        document_or_com_opened = $false
    } | ConvertTo-Json -Depth 5
    exit 0
}

$startedAt = Get-Date
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($before.Count -ne 0) {
    throw 'Refusing document smoke because an Hwp process is already running.'
}

[void][System.IO.Directory]::CreateDirectory($allowedOutputRoot)
[void][System.IO.Directory]::CreateDirectory($resolvedOutputRoot)
Assert-NotReparsePoint -Path $allowedOutputRoot
Assert-NotReparsePoint -Path $resolvedOutputRoot

$runId = [guid]::NewGuid().ToString('N')
$runDirectory = Join-Path $resolvedOutputRoot $runId
if (Test-Path -LiteralPath $runDirectory) {
    throw 'Generated smoke run directory already exists.'
}
[void][System.IO.Directory]::CreateDirectory($runDirectory)

$childResultPath = Join-Path $runDirectory 'child-result.json'
$hwpxPath = Join-Path $runDirectory 'synthetic-p00-2020.hwpx'
$pdfPath = Join-Path $runDirectory 'synthetic-p00-2020.pdf'
$receiptPath = Join-Path $runDirectory 'receipt.json'

$argumentValues = @(
    '-NoProfile',
    '-NonInteractive',
    '-STA',
    '-File', $childScriptPath,
    '-RunDirectory', $runDirectory,
    '-ProgId', $ProgId,
    '-ExpectedAutomationVersion', $ExpectedFileVersion,
    '-FixtureId', $runId
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $x86PowerShell
$startInfo.Arguments = (($argumentValues | ForEach-Object { ConvertTo-ProcessArgument -Value ([string]$_) }) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true

$child = [System.Diagnostics.Process]::new()
$child.StartInfo = $startInfo
[void]$child.Start()
$childProcessId = $child.Id
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()

$observedProcesses = @{}
function Add-ObservedHwpProcess {
    param([Microsoft.Management.Infrastructure.CimInstance]$CimProcess)

    $key = [string]$CimProcess.ProcessId
    if ($observedProcesses.ContainsKey($key)) { return }
    $runtimeProcess = Get-Process -Id $CimProcess.ProcessId -ErrorAction SilentlyContinue
    $processPath = [string]$CimProcess.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($processPath) -and $null -ne $runtimeProcess) {
        try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
    }
    $observedProcesses[$key] = [ordered]@{
        process_id = [int]$CimProcess.ProcessId
        parent_process_id = [int]$CimProcess.ParentProcessId
        session_id = [int]$CimProcess.SessionId
        created_at = if ($null -ne $CimProcess.CreationDate) { ([datetime]$CimProcess.CreationDate).ToString('o') } else { $null }
        executable_path_match = $processPath.Equals($identity.path, [System.StringComparison]::OrdinalIgnoreCase)
        automation_command_line = [bool]($CimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$')
        main_window_handle = if ($null -ne $runtimeProcess) { [int64]$runtimeProcess.MainWindowHandle } else { $null }
    }
}

$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$exitedWithinTimeout = $false
while ((Get-Date) -lt $deadline) {
    foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        Add-ObservedHwpProcess -CimProcess $process
    }
    if ($child.WaitForExit(250)) {
        $exitedWithinTimeout = $true
        break
    }
}
if (-not $exitedWithinTimeout -and $child.HasExited) {
    $exitedWithinTimeout = $true
}
if (-not $exitedWithinTimeout) {
    $child.Kill()
    $child.WaitForExit()
}
$childExitCode = $child.ExitCode

foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
    Add-ObservedHwpProcess -CimProcess $process
}

$outputDrained = $false
try {
    $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
        [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
        5000
    )
}
catch {
    $outputDrained = $false
}
$stdout = if ($outputDrained) { $stdoutTask.GetAwaiter().GetResult().Trim() } else { '' }
$stderr = if ($outputDrained) { $stderrTask.GetAwaiter().GetResult().Trim() } else { '' }

$childResult = $null
if (Test-Path -LiteralPath $childResultPath -PathType Leaf) {
    try {
        $childResult = Get-Content -LiteralPath $childResultPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        $childResult = $null
    }
}

Start-Sleep -Milliseconds 1000
$cleanedProcessIds = @()
$cleanupRefusedProcessIds = @()
$cleanupErrors = @()
$remainingBeforeCleanup = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
foreach ($cimProcess in $remainingBeforeCleanup) {
    $runtimeProcess = Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $runtimeProcess) { continue }
    $processPath = [string]$cimProcess.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($processPath)) {
        try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
    }
    $createdAt = if ($null -ne $cimProcess.CreationDate) { [datetime]$cimProcess.CreationDate } else { [datetime]::MinValue }
    $identityMatches =
        $cimProcess.SessionId -eq $currentSessionId -and
        $createdAt -ge $startedAt.AddSeconds(-2) -and
        $processPath.Equals($identity.path, [System.StringComparison]::OrdinalIgnoreCase) -and
        $cimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'

    if (-not $identityMatches) {
        $cleanupRefusedProcessIds += [int]$cimProcess.ProcessId
        continue
    }
    try {
        Stop-Process -Id $cimProcess.ProcessId -Force -ErrorAction Stop
        Wait-Process -Id $cimProcess.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
        $cleanedProcessIds += [int]$cimProcess.ProcessId
    }
    catch {
        if ($null -eq (Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue)) {
            $cleanedProcessIds += [int]$cimProcess.ProcessId
        }
        else {
            $cleanupErrors += "PID $($cimProcess.ProcessId): $($_.Exception.GetType().FullName)"
        }
    }
}

Start-Sleep -Milliseconds 500
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
$hwpxVerification = Test-HwpxPackage -Path $hwpxPath
$pdfVerification = Test-PdfArtifact -Path $pdfPath
$expectedAutomationVersionNormalized = ConvertTo-NormalizedHancomVersion -Value $ExpectedFileVersion
$automationVersionNormalized = if ($null -ne $childResult -and $null -ne $childResult.automation_version) {
    ConvertTo-NormalizedHancomVersion -Value ([string]$childResult.automation_version)
}
else { $null }
$versionMatches =
    $null -ne $expectedAutomationVersionNormalized -and
    $null -ne $automationVersionNormalized -and
    $automationVersionNormalized -ceq $expectedAutomationVersionNormalized
$timedOut = -not $exitedWithinTimeout

$state = if ($timedOut) {
    'failed'
}
elseif (-not $outputDrained) {
    'failed'
}
elseif ($childExitCode -ne 0 -or $null -eq $childResult -or $childResult.state -ne 'pass') {
    'failed'
}
elseif (-not $versionMatches -or -not $hwpxVerification.valid -or -not $pdfVerification.valid) {
    'failed'
}
elseif ($remaining.Count -ne 0 -or $cleanupRefusedProcessIds.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
    'unverified'
}
else {
    'pass'
}

$errorCode = if ($timedOut) {
    'DOCUMENT_SMOKE_TIMEOUT'
}
elseif (-not $outputDrained) {
    'CHILD_OUTPUT_DRAIN_TIMEOUT'
}
elseif ($null -eq $childResult) {
    'CHILD_RESULT_INVALID'
}
elseif ($childExitCode -ne 0 -or $childResult.state -ne 'pass') {
    if ($null -ne $childResult.error_code) { [string]$childResult.error_code } else { 'DOCUMENT_SMOKE_CHILD_FAILED' }
}
elseif (-not $versionMatches) {
    'AUTOMATION_VERSION_MISMATCH'
}
elseif (-not $hwpxVerification.valid) {
    [string]$hwpxVerification.error_code
}
elseif (-not $pdfVerification.valid) {
    [string]$pdfVerification.error_code
}
elseif ($remaining.Count -ne 0 -or $cleanupRefusedProcessIds.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
    'AUTOMATION_PROCESS_REMAINED'
}
else { $null }

$hwpxSha256 = if (Test-Path -LiteralPath $hwpxPath -PathType Leaf) {
    (Get-FileHash -LiteralPath $hwpxPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
else { $null }
$pdfSha256 = if (Test-Path -LiteralPath $pdfPath -PathType Leaf) {
    (Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
else { $null }

$relativeRunRoot = "implementation/p00/evidence/document-smoke-runs/$runId"
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.hancom-document-smoke-receipt/v1'
    target_profile_id = $TargetProfileId
    run_id = $runId
    started_at = $startedAt.ToString('o')
    completed_at = (Get-Date).ToString('o')
    state = $state
    error_code = $errorCode
    host_classification = 'non_clean_development_reference'
    clean_image_gate_satisfied = $false
    use_scope = 'personal_noncommercial_local_validation'
    product_seat_confirmation = 'confirmed_genuine_valid_by_user_2026-09-01'
    prog_id = $ProgId
    clsid = $identity.clsid
    com_registry_view = 'Registry32'
    client_apartment_state = 'STA'
    expected_file_version = $ExpectedFileVersion
    observed_file_version = $identity.file_version
    expected_executable_sha256 = $ExpectedExecutableSha256.ToLowerInvariant()
    observed_executable_sha256 = $identity.sha256
    automation_version = if ($null -ne $childResult) { $childResult.automation_version } else { $null }
    expected_automation_version_normalized = $expectedAutomationVersionNormalized
    automation_version_normalized = $automationVersionNormalized
    automation_version_matches_expected = $versionMatches
    timeout_seconds = $TimeoutSeconds
    timed_out = $timedOut
    child_process_id = $childProcessId
    child_exit_code = $childExitCode
    child_result_state = if ($null -ne $childResult) { $childResult.state } else { $null }
    child_error_code = if ($null -ne $childResult) { $childResult.error_code } else { $null }
    child_failed_phase = if ($null -ne $childResult) { $childResult.failed_phase } else { $null }
    child_exception_type = if ($null -ne $childResult) { $childResult.exception_type } else { $null }
    child_exception_hresult = if ($null -ne $childResult) { $childResult.exception_hresult } else { $null }
    child_exception_message_sha256 = if ($null -ne $childResult) { $childResult.exception_message_sha256 } else { $null }
    phases = if ($null -ne $childResult) { $childResult.phases } else { $null }
    fixture_id = if ($null -ne $childResult) { $childResult.fixture_id } else { $runId }
    fixture_sha256 = if ($null -ne $childResult) { $childResult.fixture_sha256 } else { $null }
    fixture_utf16_length = if ($null -ne $childResult) { $childResult.fixture_utf16_length } else { $null }
    readback_sha256 = if ($null -ne $childResult) { $childResult.readback_sha256 } else { $null }
    readback_utf16_length = if ($null -ne $childResult) { $childResult.readback_utf16_length } else { $null }
    text_exact_match_after_document_separator_normalization = if ($null -ne $childResult) {
        [bool]$childResult.text_exact_match_after_document_separator_normalization
    }
    else { $false }
    hwpx = [ordered]@{
        relative_path = "$relativeRunRoot/synthetic-p00-2020.hwpx"
        sha256 = $hwpxSha256
        package_verification = $hwpxVerification
    }
    pdf = [ordered]@{
        relative_path = "$relativeRunRoot/synthetic-p00-2020.pdf"
        sha256 = $pdfSha256
        export_method = if ($null -ne $childResult) { $childResult.pdf_export_method } else { $null }
        file_verification = $pdfVerification
    }
    receipt_relative_path = "$relativeRunRoot/receipt.json"
    preexisting_hwp_processes = $before.Count
    observed_hwp_processes = @($observedProcesses.Values | Sort-Object process_id)
    cleaned_smoke_process_ids = @($cleanedProcessIds)
    cleanup_refused_process_ids = @($cleanupRefusedProcessIds)
    cleanup_errors = @($cleanupErrors)
    remaining_hwp_processes = $remaining.Count
    quit_invoked = if ($null -ne $childResult) { [bool]$childResult.quit_invoked } else { $false }
    register_module_invoked = $false
    user_document_opened = $false
    generated_document_only = $true
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    child_stdout_present = [bool]$stdout
    child_stderr_present = [bool]$stderr
}

$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 10), $utf8WithoutBom)
$receipt | ConvertTo-Json -Depth 10

if ($state -ne 'pass') {
    exit 2
}

