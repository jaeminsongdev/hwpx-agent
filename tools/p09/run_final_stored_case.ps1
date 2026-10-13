# P135: P134 최종 EXE의 정확한 사례 하나. 재빌드/앱/DB/UI 실행 없음.
[CmdletBinding()]
param([Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_:]+$')][string]$TestName,
      [Parameter(Mandatory)][string]$ReceiptPath,
      [ValidateRange(30,1800)][int]$MaximumSeconds=600)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/changed_formula_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target=Join-Path $root 'target/p09-121-resource-optimized'
$checkpointPath='implementation/p09/evidence/p09-134-formula-policy-revocation.source-progress.v1.json'
if((Get-Item -LiteralPath (Join-Path $root $checkpointPath)).Length -ne 18919 -or
   (Get-FileHash -LiteralPath (Join-Path $root $checkpointPath)).Hash.ToLowerInvariant() -ne 'f2d54f2a66c23cd3f2c8cc6049935bd33b735bdf608e99a6f0dd375b63ba89dd'){throw 'P134_checkpoint_drift'}
$checkpoint=Get-Content -Raw -LiteralPath (Join-Path $root $checkpointPath) | ConvertFrom-Json
$listed=Get-Content -Raw -LiteralPath (Join-Path $target 'p134-stored-list-b.json') | ConvertFrom-Json
$exePin=@($checkpoint.current_executables | Where-Object {$_.path -ceq 'target/p09-121-resource-optimized/debug/deps/form_stored_provider-p134-final.exe'})[0]
if($listed.state -ne 'PASS_SOURCE_ONLY_NOT_GATE' -or $listed.inventory.Count -ne 234 -or
   @($listed.inventory|Select-Object -Unique).Count -ne 234 -or
   @($listed.inventory|Where-Object {$_ -ceq $TestName}).Count -ne 1 -or
   $listed.executable_pin.sha256 -ne $exePin.sha256){throw 'exact_final_case_not_admitted'}
$protectedPins=@($listed.protected_executables)+@($checkpoint.current_executables)+@($checkpoint.earlier_executables)
function Test-P135Pins {
 if($protectedPins.Count -ne 21){throw 'protected_executable_inventory_drift'}
 foreach($row in $protectedPins){
  $path=Join-Path $root $row.path
  if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256){throw 'protected_executable_drift'}
 }
}
Test-P135Pins
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if(-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
   [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)){throw 'new_scoped_receipt_required'}
if(@(Get-Process -Name 'form_stored_provider*' -ErrorAction SilentlyContinue).Count -gt 0){throw 'stored_test_already_running'}
$freeze=@($listed.source_freeze)
foreach($row in $freeze){
 $path=Join-Path $root $row.path
 if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256){throw 'compiled_P134_source_drift'}
}
$extras=@($checkpoint.migration_inputs.path)+@($checkpointPath,'tools/p09/run_final_stored_case.ps1',
 'tools/p09/run_final_stored_batch.py','tools/p09/changed_formula_test_support.ps1')
$freeze+=@($extras|ForEach-Object {$file=Join-Path $root $_;[ordered]@{path=$_;bytes=(Get-Item -LiteralPath $file).Length;sha256=(Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant()}})
if($freeze.Count -ne 806 -or @($freeze.path|Select-Object -Unique).Count -ne 806){throw 'final_case_input_inventory_drift'}
$before=Get-P09ResourceSample
if($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096){
 @{schema_version='hwpx-agent.p09-final-stored-case/v1';state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';
   test_name=$TestName;executable_pin=$exePin;source_freeze=$freeze;samples=@($before);product_complete=$false;P09_gate='OPEN'}|
     ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
 Write-Output 'P135_DEFERRED_RESOURCE_PRESSURE_NOT_STARTED'
 exit 2
}
$mask=Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 1
$proc=[Diagnostics.Process]::new()
$proc.StartInfo.FileName=Join-Path $root $exePin.path
$proc.StartInfo.WorkingDirectory=$root
$proc.StartInfo.UseShellExecute=$false
$proc.StartInfo.CreateNoWindow=$true
$proc.StartInfo.RedirectStandardOutput=$true
$proc.StartInfo.RedirectStandardError=$true
$arguments=@($TestName,'--exact','--show-output','--test-threads=1')
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($before);$hot=0;$reason=$null;$safe=$null;$sourceExact=$false;$started=$false;$pinsExact=$false
try {
 if(-not $proc.Start()){throw 'case_start_failed'}
 $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
 if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'case_limits_not_applied'}
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
 Write-Output ('P135_CASE_STARTED:'+(@{pid=$proc.Id;cpu_limit=1;priority='BelowNormal'}|ConvertTo-Json -Compress))
 while(-not $proc.WaitForExit(2000)){
  $sample=Get-P09ResourceSample -TestProcess $proc;$samples+=@($sample)
  if(-not $proc.HasExited -and ($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal')){throw 'case_limits_changed'}
  if($sample.system_cpu_percent -ge 85){$hot++}else{$hot=0}
  $decision=Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_working_set_mib -HotSamples $hot
  if($watch.Elapsed.TotalSeconds -ge $MaximumSeconds){$decision='STOP_DURATION_LIMIT'}
  if($decision -ne 'CONTINUE'){$reason=$decision;$proc.Kill($true);break}
  if(($samples.Count-1)%6 -eq 0){Write-Output ('P135_RESOURCE_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
 }
 $proc.WaitForExit()
 $raw=$stdout.GetAwaiter().GetResult()+"`n"+$stderr.GetAwaiter().GetResult()
 $safe=ConvertTo-P121SafeTestResult -Output $raw
 Test-P135Pins;$pinsExact=$true
 foreach($row in $freeze){
  $path=Join-Path $root $row.path
  if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256){throw 'case_input_drift'}
 }
 $sourceExact=$true
} catch {if(-not $reason){$reason='RUNNER_OR_OBSERVATION_FAILURE'}}
finally {
 if($started -and -not $proc.HasExited){$proc.Kill($true);$proc.WaitForExit()}
 $watch.Stop();$exitCode=if($started){$proc.ExitCode}else{$null}
 $pass=$sourceExact -and $pinsExact -and -not $reason -and $exitCode -eq 0 -and $safe -and $safe.terminal_summary -and
  $safe.terminal_summary.outcome -eq 'ok' -and $safe.terminal_summary.passed -eq 1 -and
  $safe.terminal_summary.failed -eq 0 -and $safe.terminal_summary.ignored -eq 0 -and $safe.terminal_summary.measured -eq 0 -and
  $safe.terminal_summary.filtered -eq 233 -and $safe.passed_test_names.Count -eq 1 -and
  $safe.passed_test_names[0] -ceq $TestName -and $safe.failed_test_names.Count -eq 0
 $state=if($pass){'PASS_SOURCE_ONLY_NOT_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
 @{schema_version='hwpx-agent.p09-final-stored-case/v1';state=$state;test_name=$TestName;executable_pin=$exePin;
   arguments=$arguments;source_freeze=$freeze;source_freeze_exact_after=$sourceExact;protected_executables=$protectedPins;
   protected_executables_exact_after=$pinsExact;tests=$safe;exit_code=$exitCode;stop_reason=$reason;elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);
   samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;priority='BelowNormal';test_threads=1;sample_seconds=2;cpu_stop_percent=85;
   cpu_stop_consecutive_samples=3;minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;maximum_seconds=$MaximumSeconds;
   product_complete=$false;P09_gate='OPEN';actual_sql_executed=$false;native_application_executed=$false}|
     ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8
 Write-Output ('P135_CASE_TERMINAL:'+(@{state=$state;exit_code=$exitCode;stop_reason=$reason}|ConvertTo-Json -Compress))
 $proc.Dispose()
}
if(-not $pass){exit 1}
