[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RequestPath,

    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedRequestSha256,

    [string]$RegistryPath,

    [string]$ExpectedRegistrySha256 = '986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48',

    [string]$TargetProfilePath,

    [string]$ExpectedProfileSha256 = '538b7b2eb953ea81d95b30f46479e81983d309277f6d16ca6e6f8d0a24d48af2',

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',

    [ValidateRange(30, 300)]
    [int]$TimeoutSeconds = 120,

    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-PathInsideBoundary {
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Boundary
    )

    $candidateFull = [System.IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.Equals($boundaryFull, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $candidateFull.StartsWith($boundaryFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'RUNTIME_PROBE_PATH_OUTSIDE_PRIVATE_BOUNDARY'
    }
    return $candidateFull
}

function Assert-NotReparsePoint {
    param([Parameter(Mandatory)][string]$Path)

    $cursor = [System.IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'RUNTIME_PROBE_REPARSE_POINT_REFUSED'
            }
        }
        $parent = [System.IO.Directory]::GetParent($cursor)
        if ($null -eq $parent) { break }
        $cursor = $parent.FullName
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) { throw 'PROCESS_ARGUMENT_CONTAINS_QUOTE' }
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
        if ($null -eq $progIdKey) { throw 'RUNTIME_PROBE_PROGID_NOT_REGISTERED_32BIT' }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) { throw 'RUNTIME_PROBE_CLSID_MISSING' }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $localServerKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $localServerKey) { throw 'RUNTIME_PROBE_LOCALSERVER32_MISSING' }
        $serverCommand = [string]$localServerKey.GetValue('')
    }
    finally {
        foreach ($key in @($localServerKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $serverCommand.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'RUNTIME_PROBE_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$privateBoundary = [System.IO.Path]::GetFullPath(
    (Join-Path $projectRoot 'implementation\p02\evidence\runtime-probes')
).TrimEnd('\')
if ([string]::IsNullOrWhiteSpace($RegistryPath)) {
    $RegistryPath = Join-Path $projectRoot 'implementation\p02\evidence\bindings\automation-bindings.2020.v1.final.json'
}
if ([string]::IsNullOrWhiteSpace($TargetProfilePath)) {
    $TargetProfilePath = Join-Path $projectRoot 'implementation\p00\target-profile.yaml'
}
$resolvedRequestPath = (Resolve-Path -LiteralPath $RequestPath).Path
$resolvedRegistryPath = (Resolve-Path -LiteralPath $RegistryPath).Path
$resolvedProfilePath = (Resolve-Path -LiteralPath $TargetProfilePath).Path
$resolvedRequestPath = Assert-PathInsideBoundary -Candidate $resolvedRequestPath -Boundary $privateBoundary
$runDirectory = Split-Path -Parent $resolvedRequestPath
$resolvedRunDirectory = Assert-PathInsideBoundary -Candidate $runDirectory -Boundary $privateBoundary
Assert-NotReparsePoint -Path $resolvedRequestPath
Assert-NotReparsePoint -Path $resolvedRunDirectory

if ((Split-Path -Leaf $resolvedRequestPath) -cne 'request.json') {
    throw 'RUNTIME_PROBE_REQUEST_FILENAME_INVALID'
}
$requestSha256 = Get-Sha256File -Path $resolvedRequestPath
if ($requestSha256 -cne $ExpectedRequestSha256) { throw 'RUNTIME_PROBE_REQUEST_SHA256_MISMATCH' }
$registrySha256 = Get-Sha256File -Path $resolvedRegistryPath
if ($registrySha256 -cne $ExpectedRegistrySha256) { throw 'RUNTIME_PROBE_REGISTRY_SHA256_MISMATCH' }
$profileSha256 = Get-Sha256File -Path $resolvedProfilePath
if ($profileSha256 -cne $ExpectedProfileSha256) { throw 'RUNTIME_PROBE_PROFILE_SHA256_MISMATCH' }

$request = Get-Content -LiteralPath $resolvedRequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$request.schema_version -cne 'hwpx-agent.runtime-probe-request/v1' -or
    [string]$request.registry_sha256 -cne $registrySha256 -or
    [string]$request.profile_sha256 -cne $profileSha256 -or
    [string]$request.target.profile_id -cne 'hancom-hangul-2020-secondary' -or
    [string]$request.target.exact_build -cne '11.0.0.9136' -or
    [string]$request.target.locale -cne 'ko-KR' -or
    [string]$request.target.architecture -cne 'x86' -or
    [string]$request.target.prog_id -cne $ProgId -or
    [string]$request.target.registry_view -cne 'Registry32' -or
    [string]$request.target.client_apartment_state -cne 'STA' -or
    [string]$request.target.expected_executable_sha256 -cne $ExpectedExecutableSha256 -or
    [int]$request.policy.timeout_seconds -ne $TimeoutSeconds) {
    throw 'RUNTIME_PROBE_REQUEST_CONTRACT_MISMATCH'
}
if ((Split-Path -Leaf $resolvedRunDirectory) -cne [string]$request.request_id) {
    throw 'RUNTIME_PROBE_REQUEST_DIRECTORY_CORRELATION_MISMATCH'
}
if (@($request.probes).Count -ne [int]$request.coverage.candidate_count) {
    throw 'RUNTIME_PROBE_REQUEST_COVERAGE_MISMATCH'
}

$childScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-runtime-probe-child.ps1')).Path
$x86PowerShell = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $x86PowerShell -PathType Leaf)) {
    throw 'RUNTIME_PROBE_X86_POWERSHELL_MISSING'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne [string]$request.target.exact_build -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'RUNTIME_PROBE_TARGET_IDENTITY_MISMATCH'
}

if ($ValidateConfigurationOnly) {
    [ordered]@{
        schema_version = 'hwpx-agent.runtime-probe-config/v1'
        state = 'pass'
        request_id = [string]$request.request_id
        request_sha256 = $requestSha256
        registry_sha256 = $registrySha256
        profile_sha256 = $profileSha256
        target_profile_id = [string]$request.target.profile_id
        exact_build = $identity.file_version
        client = 'windows_powershell_x86_sta'
        candidate_count = @($request.probes).Count
        com_activation_performed = $false
        document_opened = $false
    } | ConvertTo-Json -Depth 6
    exit 0
}

$tracePath = Join-Path $resolvedRunDirectory 'trace.json'
$receiptPath = Join-Path $resolvedRunDirectory 'receipt.json'
foreach ($path in @($tracePath, $receiptPath)) {
    if (Test-Path -LiteralPath $path) { throw 'RUNTIME_PROBE_OUTPUT_ALREADY_EXISTS' }
}
$before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($before.Count -ne 0) { throw 'RUNTIME_PROBE_PREEXISTING_HWP_PROCESS' }

$startedAt = Get-Date
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$arguments = @(
    '-NoProfile',
    '-NonInteractive',
    '-STA',
    '-File', $childScript,
    '-RunDirectory', $resolvedRunDirectory,
    '-RequestPath', $resolvedRequestPath,
    '-ExpectedRequestSha256', $requestSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $x86PowerShell
$startInfo.Arguments = (($arguments | ForEach-Object { ConvertTo-ProcessArgument -Value ([string]$_) }) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$child = [System.Diagnostics.Process]::new()
$child.StartInfo = $startInfo
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()

$observed = @{}
$unexpectedWindowObserved = $false
function Add-ObservedProcess {
    param([Microsoft.Management.Infrastructure.CimInstance]$CimProcess)

    $key = [string]$CimProcess.ProcessId
    $runtimeProcess = Get-Process -Id $CimProcess.ProcessId -ErrorAction SilentlyContinue
    $pathMatches = $false
    $mainWindowHandle = 0
    if ($null -ne $runtimeProcess) {
        $processPath = [string]$CimProcess.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($processPath)) {
            try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
        }
        $pathMatches = $processPath.Equals($identity.path, [System.StringComparison]::OrdinalIgnoreCase)
        $mainWindowHandle = [int64]$runtimeProcess.MainWindowHandle
    }
    if ($mainWindowHandle -ne 0) { $script:unexpectedWindowObserved = $true }
    $script:observed[$key] = [ordered]@{
        path_matches = $pathMatches
        same_session = [int]$CimProcess.SessionId -eq $currentSessionId
        automation_command_line = [bool]($CimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$')
        main_window_present = $mainWindowHandle -ne 0
    }
}

$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$exitedWithinTimeout = $false
while ((Get-Date) -lt $deadline) {
    foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        Add-ObservedProcess -CimProcess $process
    }
    if ($child.WaitForExit(250)) {
        $exitedWithinTimeout = $true
        break
    }
}
if (-not $exitedWithinTimeout -and $child.HasExited) { $exitedWithinTimeout = $true }
if (-not $exitedWithinTimeout) {
    $child.Kill()
    $child.WaitForExit()
}
$childExitCode = $child.ExitCode
foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
    Add-ObservedProcess -CimProcess $process
}

$outputDrained = $false
try {
    $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
        [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
        5000
    )
}
catch { $outputDrained = $false }

Start-Sleep -Milliseconds 750
$cleanedCount = 0
$cleanupRefusedCount = 0
$cleanupErrorCount = 0
foreach ($cimProcess in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
    $runtimeProcess = Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $runtimeProcess) { continue }
    $processPath = [string]$cimProcess.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($processPath)) {
        try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
    }
    $createdAt = if ($null -ne $cimProcess.CreationDate) { [datetime]$cimProcess.CreationDate } else { [datetime]::MinValue }
    $safeToClean =
        [int]$cimProcess.SessionId -eq $currentSessionId -and
        $createdAt -ge $startedAt.AddSeconds(-2) -and
        $processPath.Equals($identity.path, [System.StringComparison]::OrdinalIgnoreCase) -and
        $cimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
    if (-not $safeToClean) {
        $cleanupRefusedCount += 1
        continue
    }
    try {
        Stop-Process -Id $cimProcess.ProcessId -Force -ErrorAction Stop
        Wait-Process -Id $cimProcess.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
        $cleanedCount += 1
    }
    catch {
        if ($null -eq (Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue)) {
            $cleanedCount += 1
        }
        else { $cleanupErrorCount += 1 }
    }
}
Start-Sleep -Milliseconds 500
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)

$trace = $null
$traceSha256 = $null
if (Test-Path -LiteralPath $tracePath -PathType Leaf) {
    $traceSha256 = Get-Sha256File -Path $tracePath
    try { $trace = Get-Content -LiteralPath $tracePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $trace = $null }
}
$timedOut = -not $exitedWithinTimeout
$correlatedTrace = $null -ne $trace -and
    [string]$trace.request_id -ceq [string]$request.request_id -and
    [string]$trace.request_sha256 -ceq $requestSha256 -and
    [string]$trace.registry_sha256 -ceq $registrySha256

$state = if ($timedOut -or -not $outputDrained -or -not $correlatedTrace -or
    $childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    'failed'
}
elseif ($unexpectedWindowObserved -or $cleanupRefusedCount -ne 0 -or
    $cleanupErrorCount -ne 0 -or $remaining.Count -ne 0) {
    'unverified'
}
else { 'pass' }

$errorCode = if ($timedOut) { 'RUNTIME_PROBE_TIMEOUT' }
elseif (-not $outputDrained) { 'RUNTIME_PROBE_CHILD_OUTPUT_DRAIN_TIMEOUT' }
elseif (-not $correlatedTrace) { 'RUNTIME_PROBE_TRACE_INVALID' }
elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    if ($null -ne $trace -and $null -ne $trace.error_code) { [string]$trace.error_code } else { 'RUNTIME_PROBE_CHILD_FAILED' }
}
elseif ($unexpectedWindowObserved) { 'RUNTIME_PROBE_UNEXPECTED_WINDOW_OBSERVED' }
elseif ($cleanupRefusedCount -ne 0 -or $cleanupErrorCount -ne 0 -or $remaining.Count -ne 0) {
    'RUNTIME_PROBE_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

$coverage = [ordered]@{
    candidate_count = @($request.probes).Count
    verified = 0
    failed = 0
    blocked_by_risk = 0
    not_run = @($request.probes).Count
}
if ($null -ne $trace) {
    $coverage.verified = @($trace.probe_results | Where-Object { $_.disposition -ceq 'verified' }).Count
    $coverage.failed = @($trace.probe_results | Where-Object { $_.disposition -ceq 'failed' }).Count
    $coverage.blocked_by_risk = @($trace.probe_results | Where-Object { $_.disposition -ceq 'blocked_by_risk' }).Count
    $coverage.not_run = @($trace.probe_results | Where-Object { $_.disposition -ceq 'not_run' }).Count
}

$receipt = [ordered]@{
    schema_version = 'hwpx-agent.runtime-probe-receipt/v1'
    request_id = [string]$request.request_id
    request_sha256 = $requestSha256
    trace_sha256 = $traceSha256
    registry_sha256 = $registrySha256
    profile_sha256 = $profileSha256
    state = $state
    error_code = $errorCode
    target = [ordered]@{
        profile_id = [string]$request.target.profile_id
        observed_file_version = $identity.file_version
        observed_executable_sha256 = $identity.sha256
        automation_version_normalized = if ($null -ne $trace) { $trace.automation_version_normalized } else { $null }
        identity_match = $identity.file_version -ceq [string]$request.target.exact_build -and
            $identity.sha256 -ceq [string]$request.target.expected_executable_sha256
        registry_view = 'Registry32'
        client_apartment_state = 'STA'
    }
    runtime = [ordered]@{
        timeout_seconds = $TimeoutSeconds
        timed_out = $timedOut
        child_exit_code = $childExitCode
        unexpected_window_observed = $unexpectedWindowObserved
        observed_process_count = $observed.Count
        cleaned_process_count = $cleanedCount
        cleanup_refused_count = $cleanupRefusedCount
        cleanup_error_count = $cleanupErrorCount
        remaining_hwp_process_count = $remaining.Count
    }
    coverage = $coverage
    privacy = [ordered]@{
        restricted_output = $true
        raw_identifiers_present = $false
        default_values_present = $false
        absolute_private_paths_present = $false
        user_document_opened = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
    }
}
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 10), $utf8WithoutBom)
$receipt | ConvertTo-Json -Depth 10
if ($state -ne 'pass') { exit 2 }
