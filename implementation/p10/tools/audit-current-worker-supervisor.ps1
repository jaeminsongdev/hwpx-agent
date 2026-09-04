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
    throw 'P10-09 audit output must be a named file below implementation/p10/evidence.'
}
if (Test-Path -LiteralPath $outputFull) {
    throw 'P10-09 audit output already exists; no-overwrite policy refused the run.'
}

$policyRelative = 'implementation/p10/supervision/p10-current-pc-worker-supervisor-policy.json'
$policyPath = (Resolve-Path -LiteralPath (Join-Path $root $policyRelative)).Path
$agentProject = (Resolve-Path -LiteralPath (
    Join-Path $root 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\HwpxAgent.WindowsAgent.Smoke.csproj'
)).Path
$agentDll = [System.IO.Path]::GetFullPath((
    Join-Path $root 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\bin\Release\net10.0\HwpxAgent.WindowsAgent.Smoke.dll'
))
$runId = [Guid]::NewGuid().ToString('N')
$baselineRelative = "implementation/p10/evidence/.p10-09-host-baseline-$runId.json"
$baselinePath = Join-Path $root $baselineRelative
$partialPath = "$outputFull.partial-$runId"
$expectedMarker = 'process-tree recycle, fencing, upload and auth smoke passed (28/28)'

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
    try {
        if (-not $Process.HasExited) {
            $Process.Kill($true)
            if (-not $Process.WaitForExit(10000)) {
                throw 'P10-09 audit could not terminate its owned smoke process tree.'
            }
        }
    }
    catch {
        throw
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
    foreach ($argument in $Arguments) {
        $startInfo.ArgumentList.Add($argument)
    }
    $owned = [System.Diagnostics.Process]::new()
    $owned.StartInfo = $startInfo
    $started = $false
    try {
        if (-not $owned.Start()) {
            throw 'The bounded P10-09 child process did not start.'
        }
        $started = $true
        $stdoutTask = $owned.StandardOutput.ReadToEndAsync()
        $stderrTask = $owned.StandardError.ReadToEndAsync()
        if (-not $owned.WaitForExit($BoundSeconds * 1000)) {
            Stop-OwnedProcess -Process $owned
            throw 'The bounded P10-09 child process timed out.'
        }
        return [pscustomobject]@{
            exit_code = $owned.ExitCode
            stdout = $stdoutTask.GetAwaiter().GetResult()
            stderr = $stderrTask.GetAwaiter().GetResult()
        }
    }
    finally {
        if ($started -and -not $owned.HasExited) {
            Stop-OwnedProcess -Process $owned
        }
        $owned.Dispose()
    }
}

try {
    [System.IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null
    $hwpBefore = @(Get-Process -Name 'Hwp' -ErrorAction SilentlyContinue).Count
    if ($hwpBefore -ne 0) {
        throw 'P10-09 current-host audit requires zero running Hwp.exe processes.'
    }

    & (Join-Path $root 'implementation\p00\tools\Test-CurrentHostBaseline.ps1') `
        -ProjectRoot $root `
        -BaselinePath 'implementation/p00/evidence/current-host-baseline.20260901.json' `
        -OutputPath $baselineRelative | Out-Null
    if (-not $? -or -not (Test-Path -LiteralPath $baselinePath)) {
        throw 'The live current-host baseline verification did not complete.'
    }
    $baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
    if ($baseline.state -ne 'pass') {
        throw 'The live current-host baseline verification did not pass.'
    }

    $dotnetCommand = Get-Command -Name $DotNetPath -CommandType Application -ErrorAction Stop |
        Select-Object -First 1
    $build = Invoke-BoundedProcess `
        -FileName $dotnetCommand.Source `
        -Arguments @('build', '--configuration', 'Release', '--no-restore', $agentProject) `
        -BoundSeconds $TimeoutSeconds
    if ($build.exit_code -ne 0 -or -not [string]::IsNullOrWhiteSpace($build.stderr)) {
        throw 'The P10-09 clean Release build did not pass.'
    }
    $smoke = Invoke-BoundedProcess `
        -FileName $dotnetCommand.Source `
        -Arguments @($agentDll) `
        -BoundSeconds $TimeoutSeconds
    $stdout = [string]$smoke.stdout
    $stderr = [string]$smoke.stderr
    $unexpectedExit = $smoke.exit_code -ne 0
    $unexpectedError = -not [string]::IsNullOrWhiteSpace($stderr)
    $missingMarker = -not $stdout.Contains($expectedMarker, [System.StringComparison]::Ordinal)
    if ($unexpectedExit -or $unexpectedError -or $missingMarker) {
        throw 'The P10-09 supervisor smoke did not produce the exact passing marker.'
    }

    $hwpAfter = @(Get-Process -Name 'Hwp' -ErrorAction SilentlyContinue).Count
    if ($hwpAfter -ne 0) {
        throw 'The P10-09 supervisor smoke left an Hwp.exe process.'
    }
    $policySha256 = (Get-FileHash -LiteralPath $policyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceRevision = (& git -C $root rev-parse HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $sourceRevision -notmatch '^[0-9a-f]{40}$') {
        throw 'The P10-09 supervisor audit could not bind the source revision.'
    }
    $sourceStatus = (& git -C $root status --short --untracked-files=all) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not [string]::IsNullOrWhiteSpace($sourceStatus)) {
        throw 'The P10-09 supervisor audit requires a clean source tree.'
    }
    $baselineVerificationSha256 = (
        Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    $audit = [ordered]@{
        schema_version = 'hwpx-agent.p10-09-worker-supervisor-audit/v1'
        generated_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        state = 'pass_current_pc_development_only'
        policy_relative_path = $policyRelative
        policy_sha256 = $policySha256
        host_baseline_verification = [ordered]@{
            state = [string]$baseline.state
            baseline_digest_sha256 = [string]$baseline.baseline_digest_sha256
            verification_sha256 = $baselineVerificationSha256
        }
        execution = [ordered]@{
            agent_smoke_assembly_sha256 = (
                Get-FileHash -LiteralPath $agentDll -Algorithm SHA256
            ).Hash.ToLowerInvariant()
            source_revision = $sourceRevision
            source_tree_clean = $true
            release_build_succeeded = $true
            exit_code = $smoke.exit_code
            stdout_sha256 = Get-TextSha256 -Value $stdout
            expected_marker_present = $true
            test_count = 28
        }
        observed_invariants = [ordered]@{
            hancom_process_count_before = $hwpBefore
            hancom_process_count_after = $hwpAfter
            hard_timeout_exercised = $true
            unknown_outcome_reconciliation_exercised = $true
            proved_no_effect_retryable_exercised = $true
            same_execution_terminal_replay_exercised = $true
            duplicate_executor_effect_count = 0
            windows_job_object_tree_termination_exercised = $true
            owned_descendant_exit_verified = $true
            startup_quarantine_exercised = $true
            ambiguous_residue_fail_closed_exercised = $true
        }
        scope = [ordered]@{
            target_profile_id = 'hancom-hangul-2020-secondary'
            product_build = '11.0.0.9136'
            process_architecture = 'x86'
            current_pc_local_development_qualified = $true
            production_or_provider_qualified = $false
            another_hancom_version_qualified = $false
        }
        privacy = [ordered]@{
            raw_process_command_line_present = $false
            raw_document_text_present = $false
            user_document_scanned = $false
            external_network_invoked = $false
            system_setting_changed = $false
        }
    }
    $json = $audit | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText(
        $partialPath,
        $json + "`n",
        [System.Text.UTF8Encoding]::new($false))
    & $PythonPath (Join-Path $root 'tools\p10\validate_worker_supervision.py') `
        --policy $policyPath `
        --audit $partialPath | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'The P10-09 supervisor audit schema validation failed.'
    }
    [System.IO.File]::Move($partialPath, $outputFull)
    Get-Content -LiteralPath $outputFull -Raw
}
finally {
    foreach ($temporary in @($baselinePath, $partialPath)) {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}
