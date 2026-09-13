[CmdletBinding()]
param(
    [ValidateRange(300, 3600)][int]$TimeoutSeconds = 1200,
    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedRequestSha256 = '8ad49a2a9f1057fd3e474fd5a56b4ff838e383f821a09f525ce9d9d72a2cbfd4'
$expectedFixtureControlsSha256 = 'f491e8651ffc84c215b929779afaffa0dd99a4cfa3171f6a8e55928412af7e8a'
$expectedChildSourceSha256 = '4c6ecb8e422b88ce44e43c03403afa438c29d8fe0c7f0973d01658e524cdfb30'
$expectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$expectedProgId = 'HWPFrame.HwpObject.2'
$expectedBuild = '11.0.0.9136'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object {
            $_.ToString('x2')
        }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object {
            $_.ToString('x2')
        }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Get-NormalizedTextSha256 {
    param([Parameter(Mandatory)][string]$Path)
    $text = [IO.File]::ReadAllText($Path, [Text.UTF8Encoding]::new($false, $true))
    if ($text.Replace("`r`n", '').Contains("`r")) {
        throw 'CANDIDATE_32_CHILD_SOURCE_BARE_CR'
    }
    return Get-Sha256String -Value $text.Replace("`r`n", "`n")
}

function Resolve-BoundedRegularFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][long]$MaximumBytes
    )
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($Boundary + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'CANDIDATE_32_FILE_OUTSIDE_BOUNDARY'
    }
    $item = Get-Item -LiteralPath $full -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt $MaximumBytes) {
        throw 'CANDIDATE_32_FILE_INVALID'
    }
    return $item.FullName
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$ProgId)
    $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $progIdKey = $null
    $clsidKey = $null
    $serverKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($ProgId)
        if ($null -eq $progIdKey) { throw 'CANDIDATE_32_PROGID_NOT_REGISTERED' }
        $clsid = [string]$progIdKey.GetValue('CLSID')
        if ([string]::IsNullOrWhiteSpace($clsid)) {
            $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
            try { $clsid = [string]$clsidSubKey.GetValue('') }
            finally { if ($null -ne $clsidSubKey) { $clsidSubKey.Dispose() } }
        }
        if ([string]::IsNullOrWhiteSpace($clsid)) { throw 'CANDIDATE_32_CLSID_MISSING' }
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        if ($null -eq $clsidKey) { throw 'CANDIDATE_32_CLSID_MISSING' }
        $serverKey = $clsidKey.OpenSubKey('LocalServer32')
        if ($null -eq $serverKey) { throw 'CANDIDATE_32_LOCALSERVER32_MISSING' }
        $command = [string]$serverKey.GetValue('')
    }
    finally {
        foreach ($key in @($serverKey, $clsidKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'CANDIDATE_32_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path -Force
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    if ($Value.Contains('"')) { throw 'CANDIDATE_32_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
    return '"' + $Value + '"'
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function Stop-OwnedHwpProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )
    $stopped = @()
    foreach ($record in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
            -ErrorAction SilentlyContinue)) {
        $process = Get-Process -Id ([int]$record.ProcessId) -ErrorAction SilentlyContinue
        if ($null -eq $process -or $process.SessionId -ne $SessionId) { continue }
        try { $processStartedAt = $process.StartTime }
        catch { continue }
        if ($processStartedAt -lt $StartedAt.AddSeconds(-2)) { continue }
        $path = [string]$record.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($path) -or -not [IO.File]::Exists($path)) {
            continue
        }
        if ((Get-Sha256File -Path $path) -cne $ExpectedSha256) { continue }
        Stop-Process -Id $process.Id -Force -ErrorAction Stop
        $stopped += $process.Id
    }
    return @($stopped)
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path.TrimEnd('\')
$targetRoot = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'fixtures\target-build')).Path.TrimEnd('\')
$attemptDirectory = Join-Path $targetRoot 'p06-09-table-automation-candidate-32-20260914-02'
$attemptItem = Get-Item -LiteralPath $attemptDirectory -Force
if (-not $attemptItem.PSIsContainer -or
    ($attemptItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
    -not $attemptItem.FullName.StartsWith($targetRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'CANDIDATE_32_ATTEMPT_DIRECTORY_INVALID'
}
$requestPath = Resolve-BoundedRegularFile -Path (Join-Path $attemptDirectory 'request.json') `
    -Boundary $targetRoot -MaximumBytes 1048576
$fixtureControlsPath = Resolve-BoundedRegularFile `
    -Path (Join-Path $attemptDirectory 'fixture-controls.private.json') `
    -Boundary $targetRoot -MaximumBytes 1048576
$childPath = Resolve-BoundedRegularFile -Path (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-automation-candidate-32-surface-child.ps1'
) -Boundary $repoRoot -MaximumBytes 1048576
if ((Get-NormalizedTextSha256 -Path $childPath) -cne $expectedChildSourceSha256) {
    throw 'CANDIDATE_32_CHILD_SOURCE_IDENTITY_MISMATCH'
}
if ((Get-Sha256File -Path $requestPath) -cne $expectedRequestSha256) {
    throw 'CANDIDATE_32_REQUEST_IDENTITY_MISMATCH'
}
if ((Get-Sha256File -Path $fixtureControlsPath) -cne $expectedFixtureControlsSha256) {
    throw 'CANDIDATE_32_FIXTURE_CONTROLS_IDENTITY_MISMATCH'
}
$request = Get-Content -LiteralPath $requestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$fixtureControls = Get-Content -LiteralPath $fixtureControlsPath -Raw -Encoding UTF8 |
    ConvertFrom-Json
if ([string]$request.schema_version -cne
        'hwpx-agent.p06-09-table-automation-candidate-32-request/v1' -or
    [string]$request.state -cne 'planned' -or
    [int]$request.case_count -ne 32 -or
    [string]$request.target.prog_id -cne $expectedProgId -or
    [string]$request.target.build -cne $expectedBuild -or
    [string]$request.target.executable_sha256 -cne $expectedExecutableSha256 -or
    [string]$request.target.registry_view -cne 'Registry32' -or
    [string]$request.session_strategy -cne
        'one_hwp_session_32_isolated_disposable_documents' -or
    [bool]$request.policy.candidate_under_probe_execute_allowed -or
    [string]$request.policy.preexisting_hwp_process_policy -cne 'refuse') {
    throw 'CANDIDATE_32_REQUEST_CONTRACT_MISMATCH'
}
$server = Get-ComServerIdentity -ProgId $expectedProgId
if ([string]$server.file_version -cne $expectedBuild -or
    [string]$server.sha256 -cne $expectedExecutableSha256) {
    throw 'CANDIDATE_32_COM_SERVER_IDENTITY_MISMATCH'
}
$systemX86 = [Environment]::GetFolderPath([Environment+SpecialFolder]::SystemX86)
if ([string]::IsNullOrWhiteSpace($systemX86)) {
    throw 'CANDIDATE_32_X86_POWERSHELL_UNAVAILABLE'
}
$powerShellPath = Resolve-BoundedRegularFile -Path (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Boundary $systemX86.TrimEnd('\') -MaximumBytes 16777216

if ($ValidateConfigurationOnly) {
    [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-automation-candidate-32-surface-config/v1'
        state = 'pass'
        case_count = 32
        request_sha256 = $expectedRequestSha256
        fixture_controls_sha256 = $expectedFixtureControlsSha256
        child_source_sha256 = $expectedChildSourceSha256
        target_build = $expectedBuild
        target_executable_sha256 = $expectedExecutableSha256
        client = 'windows_powershell_x86_sta'
        candidate_under_probe_execute_allowed = $false
        table_create_fixture_action_execute_count = 30
        fixture_control_action_execute_count = 176
        hwp_invoked = $false
        output_written = $false
    } | ConvertTo-Json -Depth 5
    exit 0
}

$tracePath = Join-Path $attemptDirectory 'trace.json'
$progressPath = Join-Path $attemptDirectory 'trace.json.progress.jsonl'
$receiptPath = Join-Path $attemptDirectory 'receipt.json'
foreach ($path in @($tracePath, $progressPath, $receiptPath)) {
    if ([IO.File]::Exists($path) -or [IO.Directory]::Exists($path)) {
        throw 'CANDIDATE_32_OUTPUT_ALREADY_EXISTS'
    }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'CANDIDATE_32_PREEXISTING_HWP_PROCESS'
}

$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $childPath,
    '-RequestPath', $requestPath,
    '-ExpectedRequestSha256', $expectedRequestSha256,
    '-FixtureControlsPath', $fixtureControlsPath,
    '-ExpectedFixtureControlsSha256', $expectedFixtureControlsSha256,
    '-TracePath', $tracePath,
    '-ProgressPath', $progressPath
)
$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powerShellPath
$startInfo.Arguments = (($arguments | ForEach-Object {
    ConvertTo-ProcessArgument -Value ([string]$_)
}) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$child = [Diagnostics.Process]::new()
$child.StartInfo = $startInfo
$startedAt = Get-Date
$sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()
$exitedWithinTimeout = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exitedWithinTimeout) {
    $child.Kill()
    $child.WaitForExit()
}
$childExitCode = $child.ExitCode
try {
    [void][Threading.Tasks.Task]::WaitAll(
        [Threading.Tasks.Task[]]@($stdoutTask, $stderrTask), 5000
    )
} catch { }
$stdout = if ($stdoutTask.IsCompleted) { [string]$stdoutTask.Result } else { '' }
$stderr = if ($stderrTask.IsCompleted) { [string]$stderrTask.Result } else { '' }
Start-Sleep -Milliseconds 300
$stoppedProcessIds = @(Stop-OwnedHwpProcesses -StartedAt $startedAt -SessionId $sessionId `
    -ExpectedSha256 $expectedExecutableSha256)
Start-Sleep -Milliseconds 200
$remainingHwpCount = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
    -ErrorAction SilentlyContinue).Count

$trace = $null
if (Test-Path -LiteralPath $tracePath -PathType Leaf) {
    $traceItem = Get-Item -LiteralPath $tracePath -Force
    if (($traceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $traceItem.Length -gt 0 -and $traceItem.Length -le 4194304) {
        try { $trace = Get-Content -LiteralPath $tracePath -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { $trace = $null }
    }
}
$rawIdentifiersAbsent = $false
if ($null -ne $trace) {
    $traceText = Get-Content -LiteralPath $tracePath -Raw -Encoding UTF8
    $rawIdentifiers = @(
        $request.cases | ForEach-Object {
            [string]$_.action_id
            if ($null -ne $_.parameter_set_id) { [string]$_.parameter_set_id }
        }
        $fixtureControls.PSObject.Properties | Where-Object { $_.Name -cne 'schema_version' } |
            ForEach-Object { [string]$_.Value }
    ) | Sort-Object -Unique
    $rawIdentifiersAbsent = @($rawIdentifiers | Where-Object {
        -not [string]::IsNullOrWhiteSpace($_) -and $traceText.Contains($_)
    }).Count -eq 0
}
$traceValid = $null -ne $trace -and
    [string]$trace.schema_version -ceq
        'hwpx-agent.p06-09-table-automation-candidate-32-surface-trace/v1' -and
    [string]$trace.state -ceq 'pass' -and
    [int]$trace.case_count -eq 32 -and
    [int]$trace.completed_case_count -eq 32 -and
    [int]$trace.default_read_passed -eq 14 -and
    [int]$trace.table_create_fixture_action_execute_count -eq 30 -and
    [int]$trace.fixture_control_action_execute_count -eq 176 -and
    [int]$trace.candidate_under_probe_execute_count -eq 0 -and
    @($trace.cases).Count -eq 32 -and
    @($trace.cases | Where-Object {
        [string]$_.state -notin @(
            'surface_present_enabled', 'surface_present_disabled_in_context'
        ) -or [string]$_.candidate_under_probe_execute_state -cne 'not_run'
    }).Count -eq 0 -and
    $rawIdentifiersAbsent
$state = if ($exitedWithinTimeout -and $childExitCode -eq 0 -and $traceValid -and
    $remainingHwpCount -eq 0) { 'pass' } else { 'failed' }
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-candidate-32-surface-receipt/v1'
    state = $state
    scope = 'read_only_candidate_surface_batch_not_runtime_support'
    request_sha256 = $expectedRequestSha256
    fixture_controls_sha256 = $expectedFixtureControlsSha256
    trace_sha256 = if ($null -ne $trace) { Get-Sha256File -Path $tracePath } else { $null }
    case_count = 32
    completed_case_count = if ($null -ne $trace) { [int]$trace.completed_case_count } else { 0 }
    enabled_case_count = if ($null -ne $trace) { [int]$trace.enabled_case_count } else { 0 }
    default_read_passed = if ($null -ne $trace) { [int]$trace.default_read_passed } else { 0 }
    table_create_fixture_action_execute_count = if ($null -ne $trace) {
        [int]$trace.table_create_fixture_action_execute_count
    } else { 0 }
    fixture_control_action_execute_count = if ($null -ne $trace) {
        [int]$trace.fixture_control_action_execute_count
    } else { 0 }
    candidate_under_probe_execute_count = if ($null -ne $trace) {
        [int]$trace.candidate_under_probe_execute_count
    } else { 0 }
    child_exit_code = $childExitCode
    exited_within_timeout = $exitedWithinTimeout
    timeout_seconds = $TimeoutSeconds
    trace_valid = $traceValid
    raw_action_or_parameter_identifier_present_in_trace = -not $rawIdentifiersAbsent
    stopped_owned_hwp_process_ids = $stoppedProcessIds
    remaining_hwp_process_count = $remainingHwpCount
    stdout_sha256 = if ([string]::IsNullOrEmpty($stdout)) { $null } else {
        Get-Sha256String -Value $stdout
    }
    stderr_sha256 = if ([string]::IsNullOrEmpty($stderr)) { $null } else {
        Get-Sha256String -Value $stderr
    }
    runtime_support_state = 'not_eligible'
    routing_enabled = $false
}
Write-NewUtf8File -Path $receiptPath `
    -Content (($receipt | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
$receipt | ConvertTo-Json -Depth 8
if ($state -cne 'pass') { exit 1 }
