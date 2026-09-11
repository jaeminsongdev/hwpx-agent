[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RequestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRequestSha256,
    [ValidateRange(30, 300)][int]$TimeoutSeconds = 180,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value.Contains('"')) { throw 'EQUATION_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
    return '"' + $Value + '"'
}

function Assert-PathInside {
    param([Parameter(Mandatory)][string]$Candidate, [Parameter(Mandatory)][string]$Boundary)
    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.StartsWith($boundaryFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'EQUATION_PROBE_PATH_OUTSIDE_PRIVATE_BOUNDARY'
    }
    $cursor = Split-Path -Parent $candidateFull
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'EQUATION_PROBE_REPARSE_POINT_REFUSED'
            }
        }
        if ($cursor.Equals($boundaryFull, [StringComparison]::OrdinalIgnoreCase)) { break }
        $next = Split-Path -Parent $cursor
        if ($next -eq $cursor) { throw 'EQUATION_PROBE_BOUNDARY_NOT_REACHED' }
        $cursor = $next
    }
    return $candidateFull
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)
    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $prog = $null; $clsidNode = $null; $clsidKey = $null; $server = $null
    try {
        $prog = $root.OpenSubKey($RequestedProgId)
        if ($null -eq $prog) { throw 'EQUATION_PROGID_NOT_REGISTERED_32BIT' }
        $clsidNode = $prog.OpenSubKey('CLSID')
        $clsid = [string]$clsidNode.GetValue('')
        $clsidKey = $root.OpenSubKey("CLSID\$clsid")
        $server = $clsidKey.OpenSubKey('LocalServer32')
        $command = [string]$server.GetValue('')
    }
    finally {
        foreach ($key in @($server, $clsidKey, $clsidNode, $prog, $root)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match($command.Trim(), '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)')
    if (-not $match.Success) { throw 'EQUATION_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{ path = $path; version = [string]$item.VersionInfo.FileVersion; sha256 = Get-Sha256File -Path $path }
}

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$boundary = Join-Path $root 'implementation\p07\evidence\private'
$resolvedRequest = Assert-PathInside -Candidate (Resolve-Path -LiteralPath $RequestPath).Path -Boundary $boundary
if ((Split-Path -Leaf $resolvedRequest) -cne 'request.json') { throw 'EQUATION_REQUEST_FILENAME_INVALID' }
$runDirectory = Split-Path -Parent $resolvedRequest
$request = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedRequest | ConvertFrom-Json
$parentHarnessSha256 = Get-Sha256File -Path $PSCommandPath
$childScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-equation-automation-probe-child.ps1')).Path
$childHarnessSha256 = Get-Sha256File -Path $childScript
if ((Split-Path -Leaf $runDirectory) -cne [string]$request.request_id -or
    [string]$request.schema_version -cne 'hwpx-agent.p07-06-equation-automation-probe-request/v1' -or
    [string]$request.target.prog_id -cne $ProgId -or
    [string]$request.target.exact_build -cne $ExpectedBuild -or
    [string]$request.target.expected_executable_sha256 -cne $ExpectedExecutableSha256 -or
    [int]$request.policy.timeout_seconds -ne $TimeoutSeconds -or
    [string]$request.harness.parent_sha256 -cne $parentHarnessSha256 -or
    [string]$request.harness.child_sha256 -cne $childHarnessSha256) {
    throw 'EQUATION_REQUEST_PARENT_CONTRACT_MISMATCH'
}
$requestSha256 = Get-Sha256File -Path $resolvedRequest
if ($requestSha256 -cne $ExpectedRequestSha256) { throw 'EQUATION_REQUEST_SHA256_MISMATCH' }
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.version -cne $ExpectedBuild -or $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'EQUATION_TARGET_IDENTITY_MISMATCH'
}
$tracePath = Join-Path $runDirectory 'trace.json'
$runtimeReceiptPath = Join-Path $runDirectory 'runtime-receipt.json'
foreach ($path in @($tracePath, $runtimeReceiptPath, (Join-Path $runDirectory 'inserted.hwpx'), (Join-Path $runDirectory 'edited.hwpx'))) {
    if (Test-Path -LiteralPath $path) { throw 'EQUATION_PROBE_OUTPUT_ALREADY_EXISTS' }
}
$before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($before.Count -ne 0) { throw 'EQUATION_PREEXISTING_HWP_PROCESS' }

$x86 = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
$arguments = @('-NoProfile', '-NonInteractive', '-STA', '-File', $childScript, '-RunDirectory', $runDirectory, '-RequestPath', $resolvedRequest, '-ExpectedRequestSha256', $requestSha256)
$start = Get-Date
$info = [Diagnostics.ProcessStartInfo]::new()
$info.FileName = $x86
$info.Arguments = (($arguments | ForEach-Object { ConvertTo-ProcessArgument -Value ([string]$_) }) -join ' ')
$info.UseShellExecute = $false; $info.CreateNoWindow = $true
$info.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
$info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
$child = [Diagnostics.Process]::new(); $child.StartInfo = $info; [void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync(); $stderrTask = $child.StandardError.ReadToEndAsync()
$exited = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exited) { $child.Kill(); $child.WaitForExit() }
$drained = $false
try { $drained = [Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdoutTask, $stderrTask), 5000) } catch { }
$childExit = $child.ExitCode

Start-Sleep -Milliseconds 750
$cleaned = 0; $cleanupRefused = 0; $cleanupErrors = 0
foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
    $runtime = Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $runtime) { continue }
    $path = [string]$process.ExecutablePath
    $created = if ($null -ne $process.CreationDate) { [datetime]$process.CreationDate } else { [datetime]::MinValue }
    $safe = $path.Equals([string]$identity.path, [StringComparison]::OrdinalIgnoreCase) -and
        $created -ge $start.AddSeconds(-2) -and $process.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
    if (-not $safe) { $cleanupRefused += 1; continue }
    try { Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop; $cleaned += 1 }
    catch { if ($null -ne (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) { $cleanupErrors += 1 } }
}
Start-Sleep -Milliseconds 500
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
$trace = $null
if (Test-Path -LiteralPath $tracePath -PathType Leaf) {
    try { $trace = Get-Content -Raw -Encoding UTF8 -LiteralPath $tracePath | ConvertFrom-Json } catch { }
}
$correlated = $null -ne $trace -and [string]$trace.request_id -ceq [string]$request.request_id -and [string]$trace.request_sha256 -ceq $requestSha256
$state = if (-not $exited -or -not $drained -or $childExit -ne 0 -or -not $correlated -or [string]$trace.state -cne 'pass' -or $cleanupRefused -ne 0 -or $cleanupErrors -ne 0 -or $remaining.Count -ne 0) { 'failed' } else { 'pass' }
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p07-06-equation-automation-probe-runtime-receipt/v1'
    request_id = [string]$request.request_id; request_sha256 = $requestSha256
    trace_sha256 = if ($null -ne $trace) { Get-Sha256File -Path $tracePath } else { $null }
    binding_set_sha256 = [string]$request.source.binding_set_sha256
    state = $state
    target = [ordered]@{ profile_id = [string]$request.target.profile_id; build = $identity.version; executable_sha256 = $identity.sha256; architecture = 'x86'; locale = 'ko-KR' }
    runtime = [ordered]@{ timeout_seconds = $TimeoutSeconds; timed_out = -not $exited; child_exit_code = $childExit; output_drained = $drained; cleaned_process_count = $cleaned; cleanup_refused_count = $cleanupRefused; cleanup_error_count = $cleanupErrors; remaining_hwp_process_count = $remaining.Count }
    outputs = [ordered]@{
        inserted_hwpx_sha256 = if (Test-Path -LiteralPath (Join-Path $runDirectory 'inserted.hwpx')) { Get-Sha256File -Path (Join-Path $runDirectory 'inserted.hwpx') } else { $null }
        edited_hwpx_sha256 = if (Test-Path -LiteralPath (Join-Path $runDirectory 'edited.hwpx')) { Get-Sha256File -Path (Join-Path $runDirectory 'edited.hwpx') } else { $null }
    }
    privacy = [ordered]@{ raw_identifiers_present = $false; absolute_private_paths_present = $false; user_document_opened = $false; external_network_invoked = $false; registry_or_system_setting_changed = $false; computer_use_click_or_type_invoked = $false }
}
$utf8 = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText($runtimeReceiptPath, ($receipt | ConvertTo-Json -Depth 10), $utf8)
$receipt | ConvertTo-Json -Depth 10
if ($state -ne 'pass') { exit 2 }
