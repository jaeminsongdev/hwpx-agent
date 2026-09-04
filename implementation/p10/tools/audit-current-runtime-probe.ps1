[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [string]$DotNetPath = 'dotnet',
    [string]$PythonPath = 'python',
    [ValidateRange(30, 300)][int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$evidenceRoot = [System.IO.Path]::GetFullPath((Join-Path $root 'implementation\p10\evidence'))
$outputFull = [System.IO.Path]::GetFullPath(
    $(if ([System.IO.Path]::IsPathRooted($OutputPath)) { $OutputPath } else { Join-Path $root $OutputPath })
)
$evidencePrefix = $evidenceRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
if (-not $outputFull.StartsWith($evidencePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'P10-10 audit output must be a named file below implementation/p10/evidence.'
}
if (Test-Path -LiteralPath $outputFull) {
    throw 'P10-10 audit output already exists; no-overwrite policy refused the run.'
}

$policyRelative = 'implementation/p10/probe/p10-current-pc-runtime-probe-policy.json'
$isolationRelative = 'implementation/p10/isolation/p10-current-pc-local-worker-policy.json'
$policyPath = (Resolve-Path -LiteralPath (Join-Path $root $policyRelative)).Path
$isolationPath = (Resolve-Path -LiteralPath (Join-Path $root $isolationRelative)).Path
$agentProject = (Resolve-Path -LiteralPath (
    Join-Path $root 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\HwpxAgent.WindowsAgent.Smoke.csproj'
)).Path
$agentDll = [System.IO.Path]::GetFullPath((
    Join-Path $root 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\bin\Release\net10.0\HwpxAgent.WindowsAgent.Smoke.dll'
))
$runId = [Guid]::NewGuid().ToString('N')
$baselineRelative = "implementation/p10/evidence/.p10-10-host-baseline-$runId.json"
$baselinePath = Join-Path $root $baselineRelative
$partialPath = "$outputFull.partial-$runId"
$legacyMarker = 'process-tree recycle, fencing, upload and auth smoke passed (28/28)'
$probeMarker = 'runtime probe, routability admission and profile mismatch smoke passed (4/4; total 32/32)'

function Get-TextSha256([Parameter(Mandatory)][string]$Value) {
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Value)
    try {
        return [Convert]::ToHexStringLower([System.Security.Cryptography.SHA256]::HashData($bytes))
    }
    finally {
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($bytes)
    }
}

function Stop-OwnedProcess([Parameter(Mandatory)][System.Diagnostics.Process]$Process) {
    if (-not $Process.HasExited) {
        $Process.Kill($true)
        if (-not $Process.WaitForExit(10000)) {
            throw 'P10-10 audit could not terminate its owned process tree.'
        }
    }
}

function Invoke-BoundedProcess(
    [Parameter(Mandatory)][string]$FileName,
    [Parameter(Mandatory)][string[]]$Arguments,
    [Parameter(Mandatory)][int]$BoundSeconds
) {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.WorkingDirectory = $root
    foreach ($argument in $Arguments) { $startInfo.ArgumentList.Add($argument) }
    $owned = [System.Diagnostics.Process]::new()
    $owned.StartInfo = $startInfo
    $started = $false
    try {
        if (-not $owned.Start()) { throw 'The bounded P10-10 child process did not start.' }
        $started = $true
        $stdoutTask = $owned.StandardOutput.ReadToEndAsync()
        $stderrTask = $owned.StandardError.ReadToEndAsync()
        if (-not $owned.WaitForExit($BoundSeconds * 1000)) {
            Stop-OwnedProcess -Process $owned
            throw 'The bounded P10-10 child process timed out.'
        }
        return [pscustomobject]@{
            exit_code = $owned.ExitCode
            stdout = $stdoutTask.GetAwaiter().GetResult()
            stderr = $stderrTask.GetAwaiter().GetResult()
        }
    }
    finally {
        if ($started -and -not $owned.HasExited) { Stop-OwnedProcess -Process $owned }
        $owned.Dispose()
    }
}

try {
    [System.IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null
    $hwpBefore = @(Get-Process -Name 'Hwp' -ErrorAction SilentlyContinue).Count
    if ($hwpBefore -ne 0) { throw 'P10-10 current-host audit requires zero running Hwp.exe processes.' }

    & (Join-Path $root 'implementation\p00\tools\Test-CurrentHostBaseline.ps1') `
        -ProjectRoot $root `
        -BaselinePath 'implementation/p00/evidence/current-host-baseline.20260901.json' `
        -OutputPath $baselineRelative | Out-Null
    if (-not $? -or -not (Test-Path -LiteralPath $baselinePath)) {
        throw 'The live current-host baseline verification did not complete.'
    }
    $baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
    if ($baseline.state -ne 'pass') { throw 'The live current-host baseline verification did not pass.' }

    & $PythonPath (Join-Path $root 'tools\p10\validate_runtime_probe.py') --policy $policyPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'The P10-10 runtime probe policy validation failed.' }

    $dotnetCommand = Get-Command -Name $DotNetPath -CommandType Application -ErrorAction Stop |
        Select-Object -First 1
    $build = Invoke-BoundedProcess `
        -FileName $dotnetCommand.Source `
        -Arguments @('build', '--configuration', 'Release', '--no-restore', $agentProject) `
        -BoundSeconds $TimeoutSeconds
    if ($build.exit_code -ne 0 -or -not [string]::IsNullOrWhiteSpace($build.stderr)) {
        throw 'The P10-10 Release build did not pass.'
    }

    $smoke = Invoke-BoundedProcess `
        -FileName $dotnetCommand.Source `
        -Arguments @($agentDll) `
        -BoundSeconds $TimeoutSeconds
    $smokeStdout = [string]$smoke.stdout
    if ($smoke.exit_code -ne 0 -or
        -not [string]::IsNullOrWhiteSpace([string]$smoke.stderr) -or
        -not $smokeStdout.Contains($legacyMarker, [System.StringComparison]::Ordinal) -or
        -not $smokeStdout.Contains($probeMarker, [System.StringComparison]::Ordinal)) {
        throw 'The P10-10 Agent smoke did not produce both exact passing markers.'
    }

    $actual = Invoke-BoundedProcess `
        -FileName $dotnetCommand.Source `
        -Arguments @($agentDll, '--p10-10-current-host-runtime-probe', $policyPath, $isolationPath) `
        -BoundSeconds $TimeoutSeconds
    if ($actual.exit_code -ne 0 -or -not [string]::IsNullOrWhiteSpace([string]$actual.stderr)) {
        throw 'The actual P10-10 current-host probe failed.'
    }
    try { $observation = ([string]$actual.stdout).Trim() | ConvertFrom-Json }
    catch { throw 'The actual P10-10 current-host probe returned invalid JSON.' }
    if ($observation.state -ne 'pass_current_pc_development_only' -or
        $observation.report_probe_calls -ne 1 -or
        $observation.acquire_lease_calls -ne 0 -or
        $observation.executor_calls -ne 0) {
        throw 'The actual P10-10 current-host probe lost its no-lease invariant.'
    }

    $hwpAfter = @(Get-Process -Name 'Hwp' -ErrorAction SilentlyContinue).Count
    if ($hwpAfter -ne 0) { throw 'The P10-10 audit left an Hwp.exe process.' }
    $policySha256 = (Get-FileHash -LiteralPath $policyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceRevision = (& git -C $root rev-parse HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $sourceRevision -notmatch '^[0-9a-f]{40}$') {
        throw 'The P10-10 audit could not bind the source revision.'
    }
    $sourceStatus = (& git -C $root status --short --untracked-files=all) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not [string]::IsNullOrWhiteSpace($sourceStatus)) {
        throw 'The P10-10 audit requires a clean source tree.'
    }

    $audit = [ordered]@{
        schema_version = 'hwpx-agent.p10-10-runtime-probe-audit/v1'
        generated_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        state = 'pass_current_pc_development_only'
        policy_relative_path = $policyRelative
        policy_sha256 = $policySha256
        host_baseline_verification = [ordered]@{
            state = [string]$baseline.state
            baseline_digest_sha256 = [string]$baseline.baseline_digest_sha256
            verification_sha256 = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        execution = [ordered]@{
            agent_smoke_assembly_sha256 = (Get-FileHash -LiteralPath $agentDll -Algorithm SHA256).Hash.ToLowerInvariant()
            source_revision = $sourceRevision
            source_tree_clean = $true
            release_build_succeeded = $true
            full_smoke_exit_code = $smoke.exit_code
            full_smoke_stdout_sha256 = Get-TextSha256 -Value $smokeStdout
            p10_10_marker_present = $true
            agent_test_count = 32
            actual_probe_exit_code = $actual.exit_code
            actual_probe_stdout_sha256 = Get-TextSha256 -Value ([string]$actual.stdout)
        }
        observation = $observation
        scope = [ordered]@{
            current_pc_local_development_qualified = $true
            production_or_provider_qualified = $false
            another_hancom_version_qualified = $false
            another_host_qualified = $false
        }
        privacy = [ordered]@{
            raw_path_present = $false
            raw_document_content_present = $false
            user_document_scanned = $false
            external_network_invoked = $false
            system_setting_changed = $false
            hancom_process_started = $false
        }
    }
    $json = $audit | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($partialPath, $json + "`n", [System.Text.UTF8Encoding]::new($false))
    & $PythonPath (Join-Path $root 'tools\p10\validate_runtime_probe.py') `
        --policy $policyPath --audit $partialPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'The P10-10 runtime probe audit validation failed.' }
    [System.IO.File]::Move($partialPath, $outputFull)
    Get-Content -LiteralPath $outputFull -Raw
}
finally {
    foreach ($temporary in @($baselinePath, $partialPath)) {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}
