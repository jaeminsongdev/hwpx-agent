# Test profile opt-level=1만 프로세스 환경에 적용한다. debug/overflow 검사는 유지한다.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath, [ValidateRange(60,7200)][int]$MaximumSeconds=3600)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target = Join-Path $root 'target/p09-120-resource-optimized'
$receipt = [IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) { throw 'build_receipt_scope_or_existing_file' }
if (@(Get-Process -Name 'form_stored_provider*' -ErrorAction SilentlyContinue).Count -gt 0) { throw 'test_running_do_not_overlap_build' }
New-Item -ItemType Directory -Path $target -Force | Out-Null
$freeze = (Get-Content (Join-Path $root 'implementation/p09/evidence/p09-120-signed-original-corpus.source-regression.v1.json') -Raw | ConvertFrom-Json).source_freeze
function Test-BuildSourceFreeze {
    if ($freeze.Count -ne 11) { throw 'incomplete_build_source_freeze' }
    foreach ($row in $freeze) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $row.path))
        if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
            (Get-Item -LiteralPath $path).Length -ne $row.bytes -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw 'build_source_drift' }
    }
}
$before = Get-P09ResourceSample
if ($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096) {
    @{state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';samples=@($before);build_started=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output 'P09_BUILD_DEFERRED: baseline_resource_pressure'
    exit 2
}
Test-BuildSourceFreeze
$mask = Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 2
$proc = [Diagnostics.Process]::new()
$proc.StartInfo.FileName = (Get-Command cargo -CommandType Application -ErrorAction Stop).Source
$proc.StartInfo.WorkingDirectory = $root
$proc.StartInfo.UseShellExecute = $false
$proc.StartInfo.CreateNoWindow = $true
$proc.StartInfo.RedirectStandardOutput = $true
$proc.StartInfo.RedirectStandardError = $true
$argsList = @('test','-p','hwpx-agent-cli','--test','form_stored_provider','--no-run','--locked','--offline','--jobs','1','--target-dir',$target)
foreach ($arg in $argsList) { $proc.StartInfo.ArgumentList.Add($arg) }
$proc.StartInfo.Environment['CARGO_PROFILE_TEST_OPT_LEVEL'] = '1'
$proc.StartInfo.Environment['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'] = 'true'
$proc.StartInfo.Environment['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'] = 'true'
$proc.StartInfo.Environment['CARGO_PROFILE_TEST_CODEGEN_UNITS'] = '1'
$started = $false
$reason = $null
$samples = @($before)
$hot = 0
$sourceExact = $false
$compiledMarker = $false
$watch = [Diagnostics.Stopwatch]::StartNew()
$treeState = [pscustomobject]@{
    process_ids = [System.Collections.Generic.HashSet[int]]::new()
    descendant_limit_observations = 0
}
function Set-BuildTreeLimits {
    param([int[]]$ParentIds, [object]$State, [long]$AffinityMask, [datetime]$BuildStart)
    $parents = @($ParentIds)
    for ($depth = 0; $depth -lt 4 -and $parents.Count -gt 0; $depth++) {
        $children = @()
        foreach ($parent in $parents) {
            foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -Property ProcessId,CreationDate -ErrorAction Stop)) {
                if ($child.CreationDate -lt $BuildStart) { continue }
                $childProcess = Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
                if ($null -ne $childProcess -and -not $childProcess.HasExited) {
                    $childProcess.ProcessorAffinity = [IntPtr]$AffinityMask
                    $childProcess.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
                    if ($childProcess.ProcessorAffinity.ToInt64() -ne $AffinityMask -or
                        $childProcess.PriorityClass -ne 'BelowNormal') { throw 'child_resource_limits_not_applied' }
                    [void]$State.process_ids.Add([int]$childProcess.Id)
                    $State.descendant_limit_observations++
                    $children += $childProcess.Id
                }
            }
        }
        $parents = $children
    }
}
function Get-BuildTreeWorkingSetMiB {
    param([object]$State)
    [long]$bytes = 0
    foreach ($processId in $State.process_ids) {
        $childProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($null -ne $childProcess -and -not $childProcess.HasExited) {
            $childProcess.Refresh()
            $bytes += $childProcess.WorkingSet64
        }
    }
    return [math]::Round($bytes / 1MB, 2)
}
try {
    if (-not $proc.Start()) { throw 'build_start_failed' }
    $started = $true
    $proc.ProcessorAffinity = [IntPtr]$mask
    $proc.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
    [void]$treeState.process_ids.Add([int]$proc.Id)
    # 첫 5초 대기 전 Cargo가 이미 시작한 rustc 자식도 즉시 제한한다.
    Set-BuildTreeLimits -ParentIds @($proc.Id) -State $treeState -AffinityMask $mask -BuildStart $proc.StartTime
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    Write-Output ('P09_BUILD_STARTED:' + (@{pid=$proc.Id;cargo_jobs=1;logical_cpu_limit=2;opt_level=1;debug_assertions=$true;overflow_checks=$true} | ConvertTo-Json -Compress))
    while (-not $proc.WaitForExit(5000)) {
        # Cargo 소유 자식만 제한한다. 다른 사용자 앱은 변경하지 않는다.
        Set-BuildTreeLimits -ParentIds @($proc.Id) -State $treeState -AffinityMask $mask -BuildStart $proc.StartTime
        $sample = Get-P09ResourceSample -TestProcess $proc
        $sample['test_process_tree_working_set_mib'] = Get-BuildTreeWorkingSetMiB -State $treeState
        $samples += $sample
        if ($sample.system_cpu_percent -ge 85) { $hot++ } else { $hot=0 }
        $decision = Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_process_tree_working_set_mib -HotSamples $hot
        if ($watch.Elapsed.TotalSeconds -ge $MaximumSeconds) { $decision='STOP_BUILD_DURATION_LIMIT' }
        if ($decision -ne 'CONTINUE') { $reason=$decision; $proc.Kill($true); break }
        if (($samples.Count-1)%6 -eq 0) { Write-Output ('P09_BUILD_RESOURCE:' + ($sample | ConvertTo-Json -Compress)) }
    }
    $proc.WaitForExit()
    $output = $outTask.GetAwaiter().GetResult() + "`n" + $errTask.GetAwaiter().GetResult()
    $compiledMarker = $output -match 'Finished `test` profile \[optimized \+ debuginfo\]'
    Test-BuildSourceFreeze
    $sourceExact = $true
} catch { if (-not $reason) { $reason='BUILD_OR_RESOURCE_OBSERVATION_FAILURE' } }
finally {
    if ($started -and -not $proc.HasExited) { $proc.Kill($true); $proc.WaitForExit() }
    $watch.Stop()
    $exitCode = if ($started -and $proc.HasExited) { $proc.ExitCode } else { $null }
    $pass = -not $reason -and $exitCode -eq 0 -and $sourceExact -and $compiledMarker
    $result = [ordered]@{schema_version='hwpx-agent.p09-resource-optimized-test-build/v1';state=$(if($pass){'PASS_BUILD_NOT_TEST_EXECUTION'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'});
        exit_code=$exitCode;stop_reason=$reason;source_freeze=$freeze;source_freeze_exact_after=$sourceExact;
        optimized_test_profile=$compiledMarker;debug_assertions=$true;overflow_checks=$true;opt_level=1;cargo_jobs=1;
        logical_cpu_limit=2;priority='BelowNormal';descendant_limit_observations=$treeState.descendant_limit_observations;
        elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;product_complete=$false;P09_gate='OPEN'}
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P09_BUILD_TERMINAL:' + (@{state=$result.state;exit_code=$exitCode;stop_reason=$reason;receipt=$ReceiptPath} | ConvertTo-Json -Compress))
    $proc.Dispose()
}
if (-not $pass) { exit 1 }
