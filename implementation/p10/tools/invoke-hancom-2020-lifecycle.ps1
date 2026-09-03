[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$EvidencePath,
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 600)][int]$TimeoutSeconds = 300
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

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) { throw 'P10_04_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
    return '"' + $Value + '"'
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
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

function Stop-OwnedHancomProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExecutableSha256
    )

    $result = [ordered]@{ cleaned = 0; refused = 0; errors = 0 }
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        $runtime = Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtime) { continue }
        $path = [string]$candidate.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($path)) {
            try { $path = [string]$runtime.Path } catch { $path = '' }
        }
        $createdAt = if ($null -ne $candidate.CreationDate) {
            [datetime]$candidate.CreationDate
        }
        else { [datetime]::MinValue }
        $matches =
            $candidate.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            -not [string]::IsNullOrWhiteSpace($path) -and
            (Test-Path -LiteralPath $path -PathType Leaf) -and
            (Get-Sha256File -Path $path) -ceq $ExecutableSha256 -and
            [string]$candidate.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $matches) {
            $result.refused += 1
            continue
        }
        try {
            Stop-Process -Id $candidate.ProcessId -PassThru | Wait-Process -Timeout 10
            $result.cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue)) {
                $result.cleaned += 1
            }
            else { $result.errors += 1 }
        }
    }
    return [pscustomobject]$result
}

$sourceItem = Get-Item -LiteralPath $InputPath -Force
if ($sourceItem.PSIsContainer -or
    ($sourceItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $sourceItem.Length -le 0 -or $sourceItem.Length -gt 8388608 -or
    $sourceItem.Extension -cne '.hwpx') {
    throw 'P10_04_INPUT_NOT_BOUNDED_HWPX'
}
$source = $sourceItem.FullName
$boundary = $sourceItem.Directory.FullName.TrimEnd('\')
$evidence = [System.IO.Path]::GetFullPath($EvidencePath)
$staged = $evidence + '.staged.hwpx'
if (-not $evidence.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
    [System.IO.Path]::GetExtension($evidence) -cne '.json') {
    throw 'P10_04_EVIDENCE_OUTSIDE_FIXTURE_BOUNDARY'
}
foreach ($candidate in @($evidence, $staged)) {
    if (Test-Path -LiteralPath $candidate) { throw 'P10_04_OUTPUT_ALREADY_EXISTS' }
}
$sourceHashBefore = Get-Sha256File -Path $source
if ($sourceHashBefore -cne $ExpectedInputSha256) { throw 'P10_04_INPUT_DIGEST_MISMATCH' }
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'P10_04_PREEXISTING_HWP_PROCESS'
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$workerDll = Join-Path $repoRoot (
    'workers\windows-hancom-worker\tests\HwpxAgent.WindowsWorker.LifecycleSmoke\' +
    'bin\Release\net10.0-windows\HwpxAgent.WindowsWorker.LifecycleSmoke.dll'
)
$workerItem = Get-Item -LiteralPath $workerDll -Force
if ($workerItem.PSIsContainer -or
    ($workerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $workerItem.Length -le 0 -or $workerItem.Length -gt 4194304) {
    throw 'P10_04_WORKER_NOT_BOUNDED'
}
$x86Dotnet = Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe'
$dotnetItem = Get-Item -LiteralPath $x86Dotnet -Force
if ($dotnetItem.PSIsContainer -or
    ($dotnetItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $dotnetItem.Length -le 0 -or $dotnetItem.Length -gt 1048576) {
    throw 'P10_04_X86_DOTNET_NOT_BOUNDED'
}

$sourceStream = [System.IO.File]::OpenRead($source)
$stagedStream = [System.IO.File]::Open(
    $staged,
    [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write,
    [System.IO.FileShare]::None
)
try {
    $sourceStream.CopyTo($stagedStream)
    $stagedStream.Flush($true)
}
finally {
    $stagedStream.Dispose()
    $sourceStream.Dispose()
}
[System.IO.File]::SetAttributes($staged, [System.IO.FileAttributes]::ReadOnly)
$stagedItem = Get-Item -LiteralPath $staged -Force
$stagedHash = Get-Sha256File -Path $staged
if ($stagedItem.Length -ne $sourceItem.Length -or $stagedHash -cne $ExpectedInputSha256) {
    throw 'P10_04_STAGING_MISMATCH'
}

$arguments = @(
    $workerItem.FullName,
    '--actual',
    '--input', $staged,
    '--sha256', $ExpectedInputSha256,
    '--size', [string]$stagedItem.Length
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $dotnetItem.FullName
$startInfo.Arguments = (($arguments | ForEach-Object {
    ConvertTo-ProcessArgument -Value ([string]$_)
}) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$child = [System.Diagnostics.Process]::new()
$child.StartInfo = $startInfo
$startedAt = Get-Date
$sessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()
$exited = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exited) {
    $child.Kill()
    $child.WaitForExit()
}
$exitCode = $child.ExitCode
$outputDrained = $false
try {
    $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
        [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
        5000
    )
}
catch { $outputDrained = $false }
$stdout = if ($outputDrained) { $stdoutTask.GetAwaiter().GetResult().Trim() } else { '' }
$stderr = if ($outputDrained) { $stderrTask.GetAwaiter().GetResult().Trim() } else { '' }

Start-Sleep -Milliseconds 500
$cleanup = Stop-OwnedHancomProcesses `
    -StartedAt $startedAt `
    -SessionId $sessionId `
    -ExecutableSha256 $ExpectedExecutableSha256
Start-Sleep -Milliseconds 250
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count
$sourceUnchanged = (Get-Sha256File -Path $source) -ceq $sourceHashBefore
$stagedUnchanged = (Get-Sha256File -Path $staged) -ceq $stagedHash
$stagedRemoved = $false
try {
    [System.IO.File]::SetAttributes($staged, [System.IO.FileAttributes]::Normal)
    Remove-Item -LiteralPath $staged -Force
    $stagedRemoved = -not (Test-Path -LiteralPath $staged)
}
catch { $stagedRemoved = $false }

$passed =
    $exited -and $outputDrained -and $exitCode -eq 0 -and
    $stdout -ceq 'HANCOM_LIFECYCLE_PASS cycles=3 input_unchanged=true remaining=0' -and
    [string]::IsNullOrEmpty($stderr) -and
    $sourceUnchanged -and $stagedUnchanged -and $stagedRemoved -and
    [int]$cleanup.refused -eq 0 -and [int]$cleanup.errors -eq 0 -and $remaining -eq 0
$result = [ordered]@{
    schema_version = 'hwpx-agent.p10-04-hancom-2020-lifecycle/v1'
    state = if ($passed) { 'pass' } else { 'failed' }
    target_profile_id = 'hancom-hangul-2020-secondary'
    product_build = '11.0.0.9136'
    process_architecture = 'x86'
    input_sha256 = $ExpectedInputSha256
    input_unchanged = $sourceUnchanged
    staged_input_unchanged = $stagedUnchanged
    staged_input_removed = $stagedRemoved
    timed_out = -not $exited
    child_exit_code = $exitCode
    output_drained = $outputDrained
    exact_safe_stdout = $stdout -ceq 'HANCOM_LIFECYCLE_PASS cycles=3 input_unchanged=true remaining=0'
    stderr_empty = [string]::IsNullOrEmpty($stderr)
    cleaned_process_count = [int]$cleanup.cleaned
    cleanup_refused_count = [int]$cleanup.refused
    cleanup_error_count = [int]$cleanup.errors
    remaining_hwp_process_count = $remaining
    raw_document_text_present = $false
    user_document_scanned = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}
Write-NewUtf8File -Path $evidence -Content (($result | ConvertTo-Json -Depth 5) + "`n")
$result | ConvertTo-Json -Depth 5
if (-not $passed) { exit 2 }
