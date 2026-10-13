# P141: 실제 DB adapter probe 빌드만 수행. CPU1/BelowNormal/jobs1, 과거 EXE와 receipt 보존.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath,
 [ValidatePattern('^r[1-9][0-9]*$')][string]$Variant='r1',
 [ValidateRange(30,900)][int]$MaximumSeconds=600)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if([IO.Path]::GetFullPath((Get-Location).Path) -ne $root){throw 'wrong_root'}
$target=Join-Path $root 'target/p09-121-resource-optimized'
$currentExe=Join-Path $target ('debug/examples/formula_issuer_registry_postgres_probe-p141-'+$Variant+'.exe')
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if(-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
 [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt) -or (Test-Path -LiteralPath $currentExe)){throw 'fresh_output_required'}
if(@(Get-Process -Name cargo,rustc,formula_issuer_registry_postgres_probe* -ErrorAction SilentlyContinue).Count){throw 'other_rust_workload_running'}
$previous=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json') -Raw|ConvertFrom-Json
$protected=@((Get-Content -LiteralPath (Join-Path $target 'p135-case-001-attempt-001.json') -Raw|ConvertFrom-Json).protected_executables)
$reads=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-137-formula-issuer-registry-reads.source-progress.v1.json') -Raw|ConvertFrom-Json
$management=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-138-formula-issuer-registry-management.source-progress.v1.json') -Raw|ConvertFrom-Json
$protected+=@($reads.current_executables)+@($reads.earlier_executables_preserved)+@($management.current_executable)
$protected+=@($previous.current_executable)+@($previous.earlier_executables_preserved)
$harness=Get-Content -LiteralPath (Join-Path $target 'p141-adapter-build-r2.json') -Raw|ConvertFrom-Json
$protected+=@($harness.executable_pin)
$earlierProbe=Get-Content -LiteralPath (Join-Path $target 'p141-adapter-build-r3.json') -Raw|ConvertFrom-Json
$protected+=@($earlierProbe.executable_pin)
$fullProbe=Get-Content -LiteralPath (Join-Path $target 'p141-adapter-build-r4.json') -Raw|ConvertFrom-Json
$protected+=@($fullProbe.executable_pin)
function Test-Pins($pins){foreach($p in $pins){$file=Join-Path $root $p.path
 if((Get-Item -LiteralPath $file).Length -ne $p.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $p.sha256){throw 'declared_pin_drift'}}}
if($protected.Count -ne 35 -or @($protected.path|Select-Object -Unique).Count -ne 35){throw 'protected_coverage_drift'}
Test-Pins $protected
$old=Get-Content -LiteralPath (Join-Path $target 'p139-provision-build-r7.json') -Raw|ConvertFrom-Json
if($old.state -ne 'PASS_SOURCE_ONLY_NOT_GATE' -or $old.source_freeze.Count -ne 817){throw 'predecessor_build_missing'}
Test-Pins $old.source_freeze
$sources=@($old.source_freeze.path|Where-Object {$_ -ne 'tools/p09/run_formula_issuer_registry_provision.ps1'})+@(
 'tools/p09/build_formula_issuer_registry_adapter.ps1',
 'crates/revision-service/examples/formula_issuer_registry_postgres_probe.rs',
 'implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json',
 'implementation/p09/evidence/p09-140-formula-issuer-registry-sql.source-progress.v1.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r2.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r3.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r4.json')
if($sources.Count -ne 823 -or @($sources|Select-Object -Unique).Count -ne 823){throw 'source_inventory_drift'}
$freeze=@($sources|ForEach-Object {[ordered]@{path=$_;bytes=(Get-Item -LiteralPath (Join-Path $root $_)).Length;
 sha256=(Get-FileHash -LiteralPath (Join-Path $root $_)).Hash.ToLowerInvariant()}})
$before=Get-P09ResourceSample
if($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096){
 @{state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';samples=@($before);P09_gate='OPEN';product_complete=$false}|
 ConvertTo-Json -Depth 5|Set-Content -LiteralPath $receipt -Encoding utf8
 exit 2
}
$mask=Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 1
$proc=[Diagnostics.Process]::new()
$proc.StartInfo.FileName=(Get-Command cargo -CommandType Application|Select-Object -First 1).Source
$proc.StartInfo.WorkingDirectory=$root
$proc.StartInfo.UseShellExecute=$false
$proc.StartInfo.CreateNoWindow=$true
$proc.StartInfo.RedirectStandardOutput=$true
$proc.StartInfo.RedirectStandardError=$true
$arguments=@('rustc','-p','revision-service','--example','formula_issuer_registry_postgres_probe','--profile','dev',
 '--locked','--offline','--jobs','1','--target-dir',$target,'--message-format=json','--','-C',('extra-filename=-p141-'+$Variant))
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$proc.StartInfo.Environment['CARGO_PROFILE_DEV_OPT_LEVEL']='1'
$proc.StartInfo.Environment['CARGO_PROFILE_DEV_DEBUG_ASSERTIONS']='true'
$proc.StartInfo.Environment['CARGO_PROFILE_DEV_OVERFLOW_CHECKS']='true'
$proc.StartInfo.Environment['CARGO_PROFILE_DEV_CODEGEN_UNITS']='1'
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($before);$hot=0;$reason=$null;$started=$false;$finished=$false;$exact=$false;$oldExact=$false
$diagnostics=@();$childChecks=0;$pin=$null;$profile=$null
try {
 if(-not $proc.Start()){throw 'start_failed'}
 $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
 if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'limits_not_applied'}
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
 Write-Output ('P141_BUILD_STARTED:'+(@{pid=$proc.Id;cpu_limit=1;priority='BelowNormal';sources=823}|ConvertTo-Json -Compress))
 while(-not $proc.WaitForExit(2000)){
  $parents=@($proc.Id)
  for($depth=0;$depth -lt 4 -and $parents.Count -gt 0;$depth++){
   $children=@(Get-CimInstance Win32_Process -Filter ('ParentProcessId='+($parents -join ' OR ParentProcessId=')))
   $parents=@()
   foreach($child in $children){$owned=Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
    if($owned -and -not $owned.HasExited){$owned.ProcessorAffinity=[IntPtr]$mask;$owned.PriorityClass='BelowNormal'
     if($owned.ProcessorAffinity.ToInt64() -ne $mask -or $owned.PriorityClass -ne 'BelowNormal'){throw 'child_limits_failed'}
     $childChecks++;$parents+=@($owned.Id)}}
  }
  $sample=Get-P09ResourceSample -TestProcess $proc;$samples+=@($sample)
  if(-not $proc.HasExited -and ($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal')){throw 'limits_changed'}
  if($sample.system_cpu_percent -ge 85){$hot++}else{$hot=0}
  $decision=Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_working_set_mib -HotSamples $hot
  if($watch.Elapsed.TotalSeconds -ge $MaximumSeconds){$decision='STOP_DURATION_LIMIT'}
  if($decision -ne 'CONTINUE'){$reason=$decision;$proc.Kill($true);break}
  if(($samples.Count-1)%6 -eq 0){Write-Output ('P141_BUILD_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
 }
 $proc.WaitForExit();$out=$stdout.GetAwaiter().GetResult();$null=$stderr.GetAwaiter().GetResult()
 foreach($line in ($out -split '\r?\n')){if(-not $line.StartsWith('{')){continue};$item=$line|ConvertFrom-Json
  if($item.reason -eq 'build-finished'){$finished=$item.success}
  if($item.reason -eq 'compiler-artifact' -and $item.target.name -eq 'formula_issuer_registry_postgres_probe'){$profile=$item.profile}
  if($item.reason -eq 'compiler-message' -and $item.message.level -in @('error','warning')){
   $diagnostics+=@([ordered]@{level=$item.message.level;code=$item.message.code.code;
    spans=@($item.message.spans|Where-Object {$_.is_primary}|ForEach-Object {@{file=$_.file_name;line=$_.line_start}})})}}
 Test-Pins $protected;$oldExact=$true;Test-Pins $freeze;$exact=$true
 if(Test-Path -LiteralPath $currentExe){$pin=@{path=[IO.Path]::GetRelativePath($root,$currentExe).Replace('\','/');
  bytes=(Get-Item -LiteralPath $currentExe).Length;sha256=(Get-FileHash -LiteralPath $currentExe).Hash.ToLowerInvariant()}}
} catch {if(-not $reason){$reason='BUILD_OR_OBSERVATION_FAILURE'}}
finally {
 if($started -and -not $proc.HasExited){$proc.Kill($true);$proc.WaitForExit()}
 $watch.Stop();$exitCode=if($started){$proc.ExitCode}else{$null}
 $pass=$exact -and $oldExact -and -not $reason -and $exitCode -eq 0 -and $finished -and $pin -and $diagnostics.Count -eq 0 -and $profile -and -not $profile.test
 $state=if($pass){'PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
 @{schema_version='hwpx-agent.p09-141-adapter-build/v1';state=$state;source_freeze=$freeze;
  source_freeze_exact_after=$exact;protected_executables=$protected;protected_executables_exact_after=$oldExact;
  executable_pin=$pin;catalog_profile=$profile;build_finished_success=$finished;diagnostics=$diagnostics;exit_code=$exitCode;stop_reason=$reason;
  elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;
  priority='BelowNormal';cargo_jobs=1;observed_build_child_limit_checks=$childChecks;maximum_seconds=$MaximumSeconds;
  cpu_stop_percent=85;cpu_stop_consecutive_samples=3;minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;
  actual_DB_executed=$false;P09_gate='OPEN';product_complete=$false}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
 Write-Output ('P141_BUILD_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
 $proc.Dispose()
}
if(-not $pass){exit 1}
