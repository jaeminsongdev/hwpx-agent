# Test profile opt-level=1만 프로세스 환경에 적용한다. debug/overflow 검사는 유지한다.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath, [ValidateRange(60,7200)][int]$MaximumSeconds=3600, [switch]$Clippy)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target = Join-Path $root 'target/p09-121-resource-optimized'
$receipt = [IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) { throw 'build_receipt_scope_or_existing_file' }
if (@(Get-Process -Name 'form_stored_provider*' -ErrorAction SilentlyContinue).Count -gt 0) { throw 'test_running_do_not_overlap_build' }
New-Item -ItemType Directory -Path $target -Force | Out-Null
$freeze = (Get-Content (Join-Path $root 'implementation/p09/evidence/p09-121-signed-changed-original.source-regression.v1.json') -Raw | ConvertFrom-Json).source_freeze
function Test-BuildSourceFreeze {
    if ($freeze.Count -ne 14) { throw 'incomplete_build_source_freeze' }
    foreach ($row in $freeze) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $row.path))
        if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
            (Get-Item -LiteralPath $path).Length -ne $row.bytes -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw 'build_source_drift' }
    }
}
Test-BuildSourceFreeze
$before = Get-P09ResourceSample
if ($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096) {
    @{state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';samples=@($before);build_started=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output 'P09_BUILD_DEFERRED: baseline_resource_pressure'
    exit 2
}
$mask = Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 2
$proc = [Diagnostics.Process]::new()
$proc.StartInfo.FileName = (Get-Command cargo -CommandType Application -ErrorAction Stop).Source
$proc.StartInfo.WorkingDirectory = $root
$proc.StartInfo.UseShellExecute = $false
$proc.StartInfo.CreateNoWindow = $true
$proc.StartInfo.RedirectStandardOutput = $true
$proc.StartInfo.RedirectStandardError = $true
$argsList = @('test','-p','hwpx-agent-cli','--test','form_stored_provider','--no-run','--locked','--offline','--jobs','1','--target-dir',$target)
if ($Clippy) { $argsList = @('clippy','-p','hwpx-agent-cli','--test','form_stored_provider','--locked','--offline','--jobs','1','--target-dir',$target,'--','-D','warnings') }
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
$descendantChecks = 0
try {
    if (-not $proc.Start()) { throw 'build_start_failed' }
    $started = $true
    $proc.ProcessorAffinity = [IntPtr]$mask
    $proc.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    Write-Output ('P09_BUILD_STARTED:' + (@{pid=$proc.Id;cargo_jobs=1;logical_cpu_limit=2;mode=$(if($Clippy){'strict_clippy_dev'}else{'optimized_test_build'});opt_level=$(if($Clippy){$null}else{1});debug_assertions=$true;overflow_checks=$true} | ConvertTo-Json -Compress))
    while (-not $proc.WaitForExit(5000)) {
        # Cargo 소유 자식만 제한한다. 다른 사용자 앱은 변경하지 않는다.
        $parents = @($proc.Id)
        for ($depth=0; $depth -lt 4 -and $parents.Count -gt 0; $depth++) {
            $children = @()
            foreach ($parent in $parents) {
                foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -Property ProcessId,CreationDate -ErrorAction Stop)) {
                    if ($child.CreationDate -lt $proc.StartTime) { continue }
                    $p = Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
                    if ($null -ne $p -and -not $p.HasExited) {
                        $p.ProcessorAffinity = [IntPtr]$mask
                        $p.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
                        if ($p.ProcessorAffinity.ToInt64() -ne $mask) { throw 'child_affinity_not_applied' }
                        $descendantChecks++
                        $children += $p.Id
                    }
                }
            }
            $parents = $children
        }
        $sample = Get-P09ResourceSample -TestProcess $proc
        $samples += $sample
        if ($sample.system_cpu_percent -ge 85) { $hot++ } else { $hot=0 }
        $decision = Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_working_set_mib -HotSamples $hot
        if ($watch.Elapsed.TotalSeconds -ge $MaximumSeconds) { $decision='STOP_BUILD_DURATION_LIMIT' }
        if ($decision -ne 'CONTINUE') { $reason=$decision; $proc.Kill($true); break }
        if (($samples.Count-1)%6 -eq 0) { Write-Output ('P09_BUILD_RESOURCE:' + ($sample | ConvertTo-Json -Compress)) }
    }
    $proc.WaitForExit()
    $output = $outTask.GetAwaiter().GetResult() + "`n" + $errTask.GetAwaiter().GetResult()
    $compiledMarker = if ($Clippy) { $output -match 'Finished `dev` profile' } else { $output -match 'Finished `test` profile \[optimized \+ debuginfo\]' }
    Test-BuildSourceFreeze
    $sourceExact = $true
} catch { if (-not $reason) { $reason='BUILD_OR_RESOURCE_OBSERVATION_FAILURE' } }
finally {
    if ($started -and -not $proc.HasExited) { $proc.Kill($true); $proc.WaitForExit() }
    $watch.Stop()
    $exitCode = if ($started -and $proc.HasExited) { $proc.ExitCode } else { $null }
    $pass = -not $reason -and $exitCode -eq 0 -and $sourceExact -and $compiledMarker
    $result = [ordered]@{schema_version='hwpx-agent.p09-resource-optimized-test-build/v1';state=$(if($pass){if($Clippy){'PASS_STRICT_LINT_NOT_TEST_EXECUTION'}else{'PASS_BUILD_NOT_TEST_EXECUTION'}}else{'NOT_ACCEPTED_STOP_OR_FAILURE'});
        exit_code=$exitCode;stop_reason=$reason;source_freeze=$freeze;source_freeze_exact_after=$sourceExact;
        optimized_test_profile=($compiledMarker -and -not $Clippy);strict_lint_verified=($pass -and $Clippy);debug_assertions=$true;overflow_checks=$true;opt_level=$(if($Clippy){$null}else{1});cargo_jobs=1;
        logical_cpu_limit=2;priority='BelowNormal';descendant_limit_observations=$descendantChecks;
        elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;product_complete=$false;P09_gate='OPEN'}
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P09_BUILD_TERMINAL:' + (@{state=$result.state;exit_code=$exitCode;stop_reason=$reason;receipt=$ReceiptPath} | ConvertTo-Json -Compress))
    $proc.Dispose()
}
if (-not $pass) { exit 1 }
