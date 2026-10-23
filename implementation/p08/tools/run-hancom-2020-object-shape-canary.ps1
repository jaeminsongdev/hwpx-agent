[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [ValidateRange(120, 900)][int]$TimeoutSeconds = 300,
    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'P08_OBJECT_SHAPE_CANARY_WRAPPER'
$expectedOverlaySha256 = '8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f'
$expectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}
function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    if ($Value.Contains('"')) { throw ($errorPrefix + '_ARGUMENT_QUOTE') }
    return '"' + $Value + '"'
}
function Write-NewUtf8File {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Content)
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}
function Stop-OwnedHwpProcesses {
    param([Parameter(Mandatory)][datetime]$StartedAt, [Parameter(Mandatory)][int]$SessionId)
    $result = [ordered]@{ cleaned = 0; refused = 0; errors = 0; remaining_owned = 0 }
    foreach ($record in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
            -ErrorAction SilentlyContinue)) {
        $process = Get-Process -Id ([int]$record.ProcessId) -ErrorAction SilentlyContinue
        if ($null -eq $process -or $process.SessionId -ne $SessionId) {
            $result.refused += 1
            continue
        }
        try { $createdAt = $process.StartTime } catch { $result.refused += 1; continue }
        $path = [string]$record.ExecutablePath
        $owned = $createdAt -ge $StartedAt.AddSeconds(-2) -and
            -not [string]::IsNullOrWhiteSpace($path) -and
            (Test-Path -LiteralPath $path -PathType Leaf) -and
            (Get-Sha256File -Path $path) -ceq $expectedExecutableSha256 -and
            [string]$record.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $owned) { $result.refused += 1; continue }
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
            $result.cleaned += 1
        }
        catch {
            if ($null -ne (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
                $result.errors += 1
                $result.remaining_owned += 1
            }
        }
    }
    return $result
}

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path.TrimEnd('\')
$privateRoot = Join-Path $root 'implementation\p08\evidence\private'
$overlayPath = Join-Path $root (
    'implementation\p02\evidence\bindings\p08-object-automation-binding-overlay.2020.v1.json'
)
$childPath = Join-Path $PSScriptRoot 'run-hancom-2020-object-shape-canary-child.ps1'
if ((Get-Sha256File -Path $overlayPath) -cne $expectedOverlaySha256 -or
    -not (Test-Path -LiteralPath $childPath -PathType Leaf)) {
    throw ($errorPrefix + '_INPUT_IDENTITY')
}
$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if (-not $run.StartsWith($privateRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $run) -cnotmatch '^p08-24-object-shape-canary-[a-z0-9-]{1,80}$') {
    throw ($errorPrefix + '_RUN_DIRECTORY')
}
if (Test-Path -LiteralPath $run) {
    if (@(Get-ChildItem -LiteralPath $run -Force).Count -ne 0) {
        throw ($errorPrefix + '_RUN_DIRECTORY_NOT_EMPTY')
    }
}
else { [void][IO.Directory]::CreateDirectory($run) }
$configuration = [ordered]@{
    state = 'configuration_valid'
    feature_count = 5
    feature_ids = @('OBJ-026', 'OBJ-033', 'OBJ-038', 'OBJ-045', 'OBJ-013')
    context = 'one_session_one_unsaved_document_two_setup_rectangles'
    hwp_file_open_allowed = $false
    document_save_allowed = $false
    candidate_execute_allowed = $true
    exact_undo_required = $true
    overlay_sha256 = $expectedOverlaySha256
    child_sha256 = Get-Sha256File -Path $childPath
}
if ($ValidateConfigurationOnly) { $configuration | ConvertTo-Json -Depth 4; exit 0 }
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}
$tracePath = Join-Path $run 'canary-trace.private.json'
$progressPath = Join-Path $run 'progress.jsonl'
$receiptPath = Join-Path $run 'runtime-receipt.json'
$powershell = Join-Path ([Environment]::GetFolderPath(
    [Environment+SpecialFolder]::SystemX86
)) 'WindowsPowerShell\v1.0\powershell.exe'
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA', '-File', $childPath,
    '-OverlayPath', $overlayPath, '-ExpectedOverlaySha256', $expectedOverlaySha256,
    '-TracePath', $tracePath, '-ProgressPath', $progressPath
)
$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powershell
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
$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$lastProgressAt = $startedAt
$lastLength = -1L
$timedOut = $false
$stalled = $false
while (-not $child.WaitForExit(500)) {
    if (Test-Path -LiteralPath $progressPath -PathType Leaf) {
        $length = (Get-Item -LiteralPath $progressPath -Force).Length
        if ($length -ne $lastLength) {
            $lastLength = $length
            $lastProgressAt = Get-Date
        }
    }
    if ((Get-Date) -ge $deadline) { $timedOut = $true; break }
    if (((Get-Date) - $lastProgressAt).TotalSeconds -ge 30) { $stalled = $true; break }
}
if (-not $child.HasExited) { try { $child.Kill(); $child.WaitForExit() } catch { } }
Start-Sleep -Milliseconds 1500
$cleanup = Stop-OwnedHwpProcesses -StartedAt $startedAt -SessionId $sessionId
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p08-object-shape-canary-wrapper-receipt/v1'
    state = if (-not $timedOut -and -not $stalled -and $child.ExitCode -eq 0 -and
        $cleanup.errors -eq 0 -and $cleanup.remaining_owned -eq 0) { 'pass' } else { 'failed' }
    configuration = $configuration
    child_exit_code = $child.ExitCode
    timed_out = $timedOut
    stalled = $stalled
    duration_seconds = [math]::Round(((Get-Date) - $startedAt).TotalSeconds, 3)
    progress_sha256 = if (Test-Path -LiteralPath $progressPath) {
        Get-Sha256File -Path $progressPath
    } else { $null }
    trace_sha256 = if (Test-Path -LiteralPath $tracePath) {
        Get-Sha256File -Path $tracePath
    } else { $null }
    stdout_sha256 = Get-Sha256String -Value $stdout
    stderr = $stderr.Trim()
    cleanup = $cleanup
}
$json = $receipt | ConvertTo-Json -Depth 6
Write-NewUtf8File -Path $receiptPath -Content $json
$json
if ($receipt.state -cne 'pass') { exit 2 }
