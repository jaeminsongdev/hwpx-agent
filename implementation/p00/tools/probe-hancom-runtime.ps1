[CmdletBinding()]
param(
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$TargetProfileId = 'hancom-hangul-2020-secondary',
    [string]$ExpectedFileVersion = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(5, 120)]
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$startedAt = Get-Date
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($before.Count -ne 0) {
    throw 'Refusing runtime probe because an Hwp process is already running.'
}

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

$classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::ClassesRoot,
    [Microsoft.Win32.RegistryView]::Registry32
)
try {
    $progIdKey = $classesRoot.OpenSubKey($ProgId)
    if ($null -eq $progIdKey) {
        throw "32-bit COM ProgID is not registered: $ProgId"
    }
    $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
    if ($null -eq $clsidSubKey) {
        throw "32-bit COM ProgID has no CLSID: $ProgId"
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
    $classesRoot.Dispose()
}

$serverMatch = [regex]::Match(
    $serverCommand.Trim(),
    '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)
if (-not $serverMatch.Success) {
    throw "Unable to parse COM LocalServer32 executable: $serverCommand"
}
$serverPath = (Resolve-Path -LiteralPath $serverMatch.Groups['path'].Value).Path
$serverItem = Get-Item -LiteralPath $serverPath
$observedFileVersion = [string]$serverItem.VersionInfo.FileVersion
$observedExecutableSha256 = (Get-FileHash -LiteralPath $serverPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($observedFileVersion -ne $ExpectedFileVersion) {
    throw "Target file version mismatch. Expected $ExpectedFileVersion, observed $observedFileVersion."
}
if ($observedExecutableSha256 -ne $ExpectedExecutableSha256.ToLowerInvariant()) {
    throw 'Target executable SHA-256 mismatch.'
}

$x86PowerShell = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $x86PowerShell -PathType Leaf)) {
    throw "32-bit Windows PowerShell was not found: $x86PowerShell"
}

$escapedProgId = $ProgId.Replace("'", "''")
$childScript = @"
`$ErrorActionPreference = 'Stop'
`$hwp = `$null
`$result = [ordered]@{
    state = 'failed'
    error_code = `$null
    automation_version = `$null
    quit_invoked = `$false
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    exception_type = `$null
    exception_hresult = `$null
}
try {
    `$hwp = New-Object -ComObject '$escapedProgId'
    `$result.automation_version = [string]`$hwp.Version
    `$hwp.Quit()
    `$result.quit_invoked = `$true
    `$result.state = 'pass'
}
catch {
    `$result.error_code = 'COM_CLIENT_EXCEPTION'
    `$result.exception_type = `$_.Exception.GetType().FullName
    `$result.exception_hresult = `$_.Exception.HResult
}
finally {
    if (`$null -ne `$hwp) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject(`$hwp)
    }
}
`$result | ConvertTo-Json -Compress
if (`$result.state -ne 'pass') { exit 2 }
"@

$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($childScript))
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $x86PowerShell
$startInfo.Arguments = "-NoProfile -NonInteractive -STA -EncodedCommand $encodedCommand"
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

$beforeIds = @($before | Select-Object -ExpandProperty ProcessId)
$observedProcesses = @{}
function Add-ObservedHwpProcess {
    param([Microsoft.Management.Infrastructure.CimInstance]$CimProcess)

    $key = [string]$CimProcess.ProcessId
    if ($observedProcesses.ContainsKey($key)) {
        return
    }
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
        executable_path_match = $processPath.Equals($serverPath, [System.StringComparison]::OrdinalIgnoreCase)
        automation_command_line = [bool]($CimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$')
        main_window_handle = if ($null -ne $runtimeProcess) { [int64]$runtimeProcess.MainWindowHandle } else { $null }
        responding = if ($null -ne $runtimeProcess) { [bool]$runtimeProcess.Responding } else { $null }
        thread_count = if ($null -ne $runtimeProcess) { [int]$runtimeProcess.Threads.Count } else { $null }
    }
}

$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$exitedWithinTimeout = $false
while ((Get-Date) -lt $deadline) {
    foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -notin $beforeIds })) {
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

foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -notin $beforeIds })) {
    Add-ObservedHwpProcess -CimProcess $process
}

$cleanedProcessIds = @()
$cleanupRefusedProcessIds = @()
$cleanupErrors = @()
$newProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -notin $beforeIds })
foreach ($cimProcess in $newProcesses) {
    $runtimeProcess = Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $runtimeProcess) {
        continue
    }
    $processPath = [string]$cimProcess.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($processPath)) {
        try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
    }
    $createdAt = if ($null -ne $cimProcess.CreationDate) { [datetime]$cimProcess.CreationDate } else { [datetime]::MinValue }
    $identityMatches =
        $cimProcess.SessionId -eq $currentSessionId -and
        $createdAt -ge $startedAt.AddSeconds(-2) -and
        $processPath.Equals($serverPath, [System.StringComparison]::OrdinalIgnoreCase) -and
        $cimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$' -and
        $runtimeProcess.MainWindowHandle -eq 0

    if (-not $identityMatches) {
        $cleanupRefusedProcessIds += [int]$cimProcess.ProcessId
        continue
    }
    try {
        Stop-Process -Id $cimProcess.ProcessId -PassThru | Wait-Process -Timeout 10
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
if ($stdout) {
    try {
        $childResult = $stdout | ConvertFrom-Json
    }
    catch {
        $stderr = "Invalid child JSON: $($_.Exception.GetType().FullName)"
    }
}

Start-Sleep -Milliseconds 500
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -notin $beforeIds })
$expectedAutomationVersionNormalized = ConvertTo-NormalizedHancomVersion -Value $ExpectedFileVersion
$automationVersionNormalized = if ($null -ne $childResult -and $null -ne $childResult.automation_version) {
    ConvertTo-NormalizedHancomVersion -Value ([string]$childResult.automation_version)
}
else {
    $null
}
$versionMatches =
    $null -ne $expectedAutomationVersionNormalized -and
    $null -ne $automationVersionNormalized -and
    $automationVersionNormalized -eq $expectedAutomationVersionNormalized
$timedOut = -not $exitedWithinTimeout

$state = if ($timedOut) {
    'failed'
}
elseif (-not $outputDrained) {
    'failed'
}
elseif ($childExitCode -ne 0 -or $null -eq $childResult) {
    'failed'
}
elseif (-not $versionMatches) {
    'failed'
}
elseif ($remaining.Count -ne 0 -or $cleanupRefusedProcessIds.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
    'unverified'
}
else {
    [string]$childResult.state
}

$errorCode = if ($timedOut) {
    'AUTOMATION_INITIALIZATION_TIMEOUT'
}
elseif (-not $outputDrained) {
    'PROBE_OUTPUT_DRAIN_TIMEOUT'
}
elseif ($null -eq $childResult) {
    'AUTOMATION_RESULT_INVALID'
}
elseif ($childExitCode -ne 0) {
    if ($childResult.error_code) { [string]$childResult.error_code } else { 'AUTOMATION_CHILD_FAILED' }
}
elseif (-not $versionMatches) {
    'AUTOMATION_VERSION_MISMATCH'
}
elseif ($remaining.Count -ne 0 -or $cleanupRefusedProcessIds.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
    'AUTOMATION_PROCESS_REMAINED'
}
else {
    $null
}

$probeReceipt = [ordered]@{
    schema_version = 'hwpx-agent.runtime-probe/v2'
    target_profile_id = $TargetProfileId
    started_at = $startedAt.ToString('o')
    completed_at = (Get-Date).ToString('o')
    state = $state
    error_code = $errorCode
    prog_id = $ProgId
    clsid = $clsid
    com_registry_view = 'Registry32'
    client_apartment_state = 'STA'
    expected_file_version = $ExpectedFileVersion
    observed_file_version = $observedFileVersion
    expected_executable_sha256 = $ExpectedExecutableSha256.ToLowerInvariant()
    observed_executable_sha256 = $observedExecutableSha256
    executable_path = $serverPath
    automation_version = if ($null -ne $childResult) { [string]$childResult.automation_version } else { $null }
    expected_automation_version_normalized = $expectedAutomationVersionNormalized
    automation_version_normalized = $automationVersionNormalized
    automation_version_matches_expected = $versionMatches
    timeout_seconds = $TimeoutSeconds
    timed_out = $timedOut
    output_drained = $outputDrained
    child_process_id = $childProcessId
    child_exit_code = $childExitCode
    child_exception_type = if ($null -ne $childResult) { $childResult.exception_type } else { $null }
    child_exception_hresult = if ($null -ne $childResult) { $childResult.exception_hresult } else { $null }
    preexisting_hwp_processes = $before.Count
    observed_hwp_processes = @($observedProcesses.Values | Sort-Object process_id)
    cleaned_probe_process_ids = @($cleanedProcessIds)
    cleanup_refused_process_ids = @($cleanupRefusedProcessIds)
    cleanup_errors = @($cleanupErrors)
    remaining_probe_processes = $remaining.Count
    document_opened = $false
    file_opened = $false
    register_module_invoked = $false
    child_error_stream_present = [bool]$stderr
}

$probeReceipt | ConvertTo-Json -Depth 7
if ($state -ne 'pass') {
    exit 2
}
