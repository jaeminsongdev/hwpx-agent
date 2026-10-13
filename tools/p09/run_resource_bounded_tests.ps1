# 단일 테스트 worker + 두 logical CPU + BelowNormal. 원본/운영 설정은 수정하지 않는다.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$TestExecutable,
    [Parameter(Mandatory)][string]$ReceiptPath,
    [string]$SourceFreezePath = 'implementation/p09/evidence/p09-120-signed-original-corpus.source-regression.v1.json',
    [ValidatePattern('^[a-zA-Z0-9_:]+$')][string]$TestFilter,
    [ValidateRange(1,2)][int]$LogicalCpuLimit = 2,
    [ValidateRange(2,30)][int]$SampleSeconds = 5,
    [ValidateRange(30,14400)][int]$MaximumSeconds = 7200,
    [switch]$DryRun
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$exe = [IO.Path]::GetFullPath((Join-Path $root $TestExecutable))
$receipt = [IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
$targetPrefix = (Join-Path $root 'target') + [IO.Path]::DirectorySeparatorChar
if (-not $exe.StartsWith($targetPrefix,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($exe) -cnotmatch '^form_stored_provider-[0-9a-f]{16}\.exe$') { throw 'executable_outside_allowed_test_scope' }
if (-not $receipt.StartsWith($targetPrefix,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) { throw 'receipt_must_be_new_target_json' }
if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($receipt)))) { throw 'receipt_parent_missing' }
$freeze = (Get-Content -LiteralPath (Join-Path $root $SourceFreezePath) -Raw | ConvertFrom-Json).source_freeze
function Test-SourceFreeze {
    foreach ($row in $freeze) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $row.path))
        if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
            (Get-Item -LiteralPath $path).Length -ne $row.bytes -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw 'frozen_source_drift' }
    }
    if ($freeze.Count -ne 11) { throw 'incomplete_source_freeze' }
}
$mask = Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count $LogicalCpuLimit
$argsList = @()
if ($TestFilter) { $argsList += $TestFilter }
$argsList += @('--nocapture','--test-threads=1')
$plan = [ordered]@{executable=$TestExecutable;test_arguments=$argsList;logical_cpu_limit=$LogicalCpuLimit;
    affinity_mask=$mask;priority='BelowNormal';sample_seconds=$SampleSeconds;cpu_stop_percent=85;
    cpu_stop_consecutive_samples=3;minimum_available_ram_mib=4096;maximum_test_working_set_mib=2048;maximum_seconds=$MaximumSeconds}
if ($DryRun) { $plan | ConvertTo-Json -Compress -Depth 4; exit 0 }
$before = Get-P09ResourceSample
if ($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096) {
    [ordered]@{schema_version='hwpx-agent.p09-resource-bounded-tests/v1';state='DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED';
        plan=$plan;samples=@($before);test_process_started=$false;product_complete=$false;P09_gate='OPEN'} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P09_RESOURCE_DEFERRED:' + ($before | ConvertTo-Json -Compress))
    exit 2
}
Test-SourceFreeze
if (@(Get-Process -Name 'form_stored_provider*' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe }).Count -gt 0) { throw 'same_test_executable_already_running' }
$proc = [Diagnostics.Process]::new()
$proc.StartInfo.FileName = $exe
$proc.StartInfo.WorkingDirectory = $root
$proc.StartInfo.UseShellExecute = $false
$proc.StartInfo.CreateNoWindow = $true
$proc.StartInfo.RedirectStandardOutput = $true
$proc.StartInfo.RedirectStandardError = $true
foreach ($arg in $argsList) { $proc.StartInfo.ArgumentList.Add($arg) }
$watch = [Diagnostics.Stopwatch]::StartNew()
$samples = @($before)
$hot = 0
$reason = $null
$safeResult = $null
$sourceExact = $false
$runError = $false
$started = $false
$exePin = [ordered]@{path=$TestExecutable;bytes=(Get-Item -LiteralPath $exe).Length;sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()}
try {
    if (-not $proc.Start()) { throw 'test_start_failed' }
    $started = $true
    $proc.ProcessorAffinity = [IntPtr]$mask
    $proc.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
    if ($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal') { throw 'process_resource_limits_not_applied' }
    $stdout = $proc.StandardOutput.ReadToEndAsync()
    $stderr = $proc.StandardError.ReadToEndAsync()
    Write-Output ('P09_RESOURCE_STARTED:' + (@{pid=$proc.Id;logical_cpu_limit=$LogicalCpuLimit;test_threads=1;priority='BelowNormal'} | ConvertTo-Json -Compress))
    while (-not $proc.WaitForExit($SampleSeconds * 1000)) {
        $sample = Get-P09ResourceSample -TestProcess $proc
        $samples += $sample
        if (-not $proc.HasExited -and ($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal')) { throw 'process_limits_changed_during_run' }
        if ($sample.system_cpu_percent -ge 85) { $hot++ } else { $hot = 0 }
        $decision = Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_working_set_mib -HotSamples $hot
        if ($watch.Elapsed.TotalSeconds -ge $MaximumSeconds) { $decision = 'STOP_DURATION_LIMIT' }
        if ($decision -ne 'CONTINUE') { $reason = $decision; $proc.Kill($true); break }
        # 매 샘플은 receipt에 남기고 콘솔에는 약 30초마다 자원 상태만 출력한다.
        if (($samples.Count - 1) % 6 -eq 0) { Write-Output ('P09_RESOURCE_SAMPLE:' + ($sample | ConvertTo-Json -Compress)) }
    }
    $proc.WaitForExit()
    $safeResult = ConvertTo-P09SafeTestResult -Output ($stdout.GetAwaiter().GetResult() + "`n" + $stderr.GetAwaiter().GetResult())
    Test-SourceFreeze
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $exePin.sha256) { throw 'tested_executable_changed' }
    $sourceExact = $true
} catch {
    $runError = $true
    if (-not $reason) { $reason = 'RUNNER_OR_RESOURCE_OBSERVATION_FAILURE' }
} finally {
    if ($started -and -not $proc.HasExited) { $proc.Kill($true); $proc.WaitForExit() }
    $watch.Stop()
    $exitCode = if ($started -and $proc.HasExited) { $proc.ExitCode } else { $null }
    $pass = -not $reason -and -not $runError -and $exitCode -eq 0 -and $sourceExact -and
        $null -ne $safeResult -and $null -ne $safeResult.terminal_summary -and
        $safeResult.terminal_summary.outcome -eq 'ok' -and $safeResult.terminal_summary.failed -eq 0 -and
        $safeResult.terminal_summary.passed -gt 0
    $state = if ($pass) { 'PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate' } else { 'NOT_ACCEPTED_STOP_OR_FAILURE' }
    $result = [ordered]@{schema_version='hwpx-agent.p09-resource-bounded-tests/v1';state=$state;plan=$plan;
        executable_pin=$exePin;source_freeze=$freeze;source_freeze_exact_after=$sourceExact;exit_code=$exitCode;
        stop_reason=$reason;elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;tests=$safeResult;
        full_workspace_run=$false;native_or_SQL_run=$false;product_complete=$false;P09_gate='OPEN'}
    # 런타임 측정 산출물만 기록한다. 원문 stdout/stderr, key, package 내용은 저장하지 않는다.
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P09_RESOURCE_TERMINAL:' + (@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath;elapsed_seconds=$result.elapsed_seconds} | ConvertTo-Json -Compress))
    $proc.Dispose()
}
if (-not $pass) { exit 1 }
