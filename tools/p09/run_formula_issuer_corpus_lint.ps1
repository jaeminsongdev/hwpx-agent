# P144: 현재 corpus selection/RAM derivative/signature consumer의 전체 workspace 엄격 lint. 테스트/DB/UI 실행 없음.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath,
      [string]$BuildReceiptPath='target/p09-121-resource-optimized/p143-issuer-product-build-r8.json',
      [string]$UnitBuildReceiptPath='target/p09-121-resource-optimized/p143-typed-route-unit-build-r3.json',
      [string]$UnitRunReceiptPath='target/p09-121-resource-optimized/p144-corpus-unit-run1.json',
      [string]$RuntimeReceiptPath='implementation/p09/evidence/p09-144-corpus-consumer-run01.v1.json',
      [ValidateRange(60,1800)][int]$MaximumSeconds=900)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if([IO.Path]::GetFullPath((Get-Location).Path) -ne $root){throw 'wrong_root'}
$runnerProcess=[Diagnostics.Process]::GetCurrentProcess()
$runnerMask=Get-P09CpuMask -AllowedMask $runnerProcess.ProcessorAffinity.ToInt64() -Count 1
$runnerProcess.ProcessorAffinity=[IntPtr]$runnerMask;$runnerProcess.PriorityClass='BelowNormal'
if($runnerProcess.ProcessorAffinity.ToInt64() -ne $runnerMask -or $runnerProcess.PriorityClass -ne 'BelowNormal'){throw 'runner_limits_not_applied'}
if(@(Get-Process -Name cargo,rustc,form_stored_provider*,formula_issuer_registry_postgres_probe*,formula_registry_crypto_postgres_probe*,artifact_service* -ErrorAction SilentlyContinue).Count){throw 'other_rust_workload_running'}
$target=Join-Path $root 'target/p09-121-resource-optimized'
$metadata=& cargo metadata --format-version 1 --no-deps --locked --offline | ConvertFrom-Json
if($LASTEXITCODE -ne 0 -or $metadata.workspace_members.Count -ne 32){throw 'workspace_inventory_drift'}
if(@($metadata.packages.targets|Where-Object {$_.kind -contains 'custom-build'}).Count -ne 0){throw 'workspace_build_script_not_admitted'}
$workspace=@($metadata.packages|ForEach-Object {$package=$_; foreach($item in $package.targets){[ordered]@{package_id=$package.id;package=$package.name;name=$item.name;kind=@($item.kind);src_path=[IO.Path]::GetRelativePath($root,$item.src_path).Replace('\','/')}}})
if($workspace.Count -ne 361){throw 'workspace_target_inventory_drift'}
if($BuildReceiptPath -cnotmatch '^target/p09-121-resource-optimized/p143-issuer-product-build-r[1-9][0-9]*\.json$'){throw 'probe_build_path_invalid'}
$probeBuild=Get-Content -LiteralPath (Join-Path $root $BuildReceiptPath) -Raw|ConvertFrom-Json
if($probeBuild.state -cne 'PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE' -or $probeBuild.exit_code -ne 0 -or
 -not $probeBuild.source_freeze_exact_after -or -not $probeBuild.protected_executables_exact_after -or
 $probeBuild.source_freeze.Count -ne 842 -or $probeBuild.catalog_profile.test -or $probeBuild.diagnostics.Count -ne 0 -or
 $probeBuild.logical_cpu_limit -ne 1 -or $probeBuild.cargo_jobs -ne 1 -or $probeBuild.priority -cne 'BelowNormal'){throw 'current_accepted_build_required'}
$unitBuildPath=$UnitBuildReceiptPath
$unitRunPath=$UnitRunReceiptPath
if($unitBuildPath -cnotmatch '^target/p09-121-resource-optimized/p143-typed-route-unit-build-r[1-9][0-9]*\.json$' -or
 $unitRunPath -cnotmatch '^target/p09-121-resource-optimized/p144-corpus-unit-run[1-9][0-9]*\.json$' -or
 $RuntimeReceiptPath -cnotmatch '^implementation/p09/evidence/p09-144-corpus-consumer-run[0-9]{2}\.v1\.json$'){throw 'evidence_path_scope'}
$unitBuild=Get-Content -LiteralPath (Join-Path $root $unitBuildPath) -Raw|ConvertFrom-Json
$unitRun=Get-Content -LiteralPath (Join-Path $root $unitRunPath) -Raw|ConvertFrom-Json
if($unitBuild.state -cne 'PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION' -or -not $unitBuild.catalog_profile.test -or
 $unitRun.state -cne 'PASS_TYPED_ROUTE_AND_SOURCE_INDEX_UNIT11_NOT_DB_NATIVE_OR_GATE' -or -not $unitRun.test_process_started -or
 -not $unitRun.source_freeze_exact_after -or -not $unitRun.protected_executables_exact_after){throw 'actual_typed_unit_evidence_required'}
$compiledPins=@{}
foreach($row in @($probeBuild.source_freeze)+@($unitBuild.source_freeze)+@($unitRun.source_freeze)){
 if($compiledPins.ContainsKey($row.path)){
  if($compiledPins[$row.path].bytes -ne $row.bytes -or $compiledPins[$row.path].sha256 -cne $row.sha256){throw 'conflicting_source_snapshots'}
 }else{$compiledPins[$row.path]=$row}
}
foreach($row in $compiledPins.Values){
 $file=Join-Path $root $row.path
 if((Get-Item -LiteralPath $file).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -cne $row.sha256){throw 'compiled_source_drift'}
}
$protectedPins=@($probeBuild.protected_executables)+@($probeBuild.executable_pin)+@($unitBuild.executable_pin)
$earlierUnitBuildPath='target/p09-121-resource-optimized/p143-typed-route-unit-build-r1.json'
$earlierUnitBuild=Get-Content -LiteralPath (Join-Path $root $earlierUnitBuildPath) -Raw|ConvertFrom-Json
if($earlierUnitBuild.state -cne 'PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION' -or
 $earlierUnitBuild.executable_pin.path -cne 'target/p09-121-resource-optimized/debug/examples/formula_issuer_product_postgres_probe-p143-unit-r1.exe'){throw 'earlier_unit_identity_drift'}
$protectedPins+=@($earlierUnitBuild.executable_pin)
$secondUnitBuildPath='target/p09-121-resource-optimized/p143-typed-route-unit-build-r2.json'
$secondUnitBuild=Get-Content -LiteralPath (Join-Path $root $secondUnitBuildPath) -Raw|ConvertFrom-Json
if($secondUnitBuild.state -cne 'PASS_TYPED_ROUTE_UNIT_BUILD_ONLY_NOT_EXECUTION' -or
 $secondUnitBuild.executable_pin.path -cne 'target/p09-121-resource-optimized/debug/examples/formula_issuer_product_postgres_probe-p143-unit-r2.exe'){throw 'second_unit_identity_drift'}
$protectedPins+=@($secondUnitBuild.executable_pin)
if($protectedPins.Count -ne 48 -or @($protectedPins.path|Select-Object -Unique).Count -ne $protectedPins.Count){throw 'protected_executable_coverage_drift'}
foreach($row in $protectedPins){
 $path=Join-Path $root $row.path
 if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256){throw 'protected_executable_drift'}
}
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    $ReceiptPath -cnotmatch '^target/p09-121-resource-optimized/p144-workspace-lint-r[1-9][0-9]*\.json$' -or (Test-Path -LiteralPath $receipt)) {throw 'new_receipt_required'}
if (@(Get-Process -Name 'form_stored_provider*','comment_style_section_protection*','comment_model-*','comment_operation-*','stored_comment_provider-*' -ErrorAction SilentlyContinue).Count -gt 0) {throw 'test_already_running'}
$indexProc=[Diagnostics.Process]::new()
$indexProc.StartInfo.FileName=(Get-Command rg -CommandType Application | Select-Object -First 1).Source
$indexProc.StartInfo.WorkingDirectory=$root
$indexProc.StartInfo.UseShellExecute=$false
$indexProc.StartInfo.CreateNoWindow=$true
$indexProc.StartInfo.RedirectStandardOutput=$true
$indexProc.StartInfo.RedirectStandardError=$true
$indexProc.StartInfo.StandardOutputEncoding=[Text.Encoding]::UTF8
foreach($indexArg in @('--threads','1','--files',(Join-Path $root 'crates'),(Join-Path $root 'protocol/generated/rust'),(Join-Path $root 'tools/xtask'))){$indexProc.StartInfo.ArgumentList.Add($indexArg)}
if(-not $indexProc.Start()){throw 'source_index_start_failed'}
try {
 $indexProc.ProcessorAffinity=[IntPtr](Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 1)
 $indexProc.PriorityClass='BelowNormal'
 $indexOut=$indexProc.StandardOutput.ReadToEndAsync();$indexErr=$indexProc.StandardError.ReadToEndAsync()
 if(-not $indexProc.WaitForExit(10000)){$indexProc.Kill($true);throw 'source_index_timeout'}
 $indexText=$indexOut.GetAwaiter().GetResult();$indexError=$indexErr.GetAwaiter().GetResult()
 $indexed=@($indexText -split '\r?\n'|Where-Object {$_}|ForEach-Object {[IO.Path]::GetRelativePath($root,$_).Replace('\','/')})
 $indexExit=$indexProc.ExitCode
} finally {
 if(-not $indexProc.HasExited){$indexProc.Kill($true);$indexProc.WaitForExit()}
 $indexProc.Dispose()
}
$sources=@(@($probeBuild.source_freeze.path)+@(
 'tools/p09/run_formula_issuer_corpus_lint.ps1','tools/p09/resource_bounded_test_support.ps1',$BuildReceiptPath,
 $unitBuildPath,$unitRunPath,$RuntimeReceiptPath,$earlierUnitBuildPath,$secondUnitBuildPath,
 'tools/p09/run_formula_issuer_corpus_probe.py',
 'tools/p09/run_formula_issuer_product_probe.py','tools/p09/idle_resource_admission.py',
 'tools/p09/check_idle_resource_window.py','tools/p09/run_formula_issuer_corpus_unit_probe.py',
 'tools/p09/build_formula_issuer_product_unit_probe.ps1')|Select-Object -Unique)
if($sources.Count -ne 855 -or @($sources|Select-Object -Unique).Count -ne 855 -or
 @($indexed|Where-Object {$_ -notin $sources}).Count -ne 0 -or $indexExit -ne 0 -or $indexError.Length -ne 0){throw 'compiled_source_inventory_drift'}
$freeze=@($sources|ForEach-Object {[ordered]@{path=$_;bytes=(Get-Item -LiteralPath (Join-Path $root $_)).Length;
 sha256=(Get-FileHash -LiteralPath (Join-Path $root $_)).Hash.ToLowerInvariant()}})
# 전체 source/EXE hash 완료 뒤 실행 직전 안정 구간 확인.
$idleSamples=@();$idleCount=0;$idleHot=0;$idleReason=$null;$idleWatch=[Diagnostics.Stopwatch]::StartNew()
while($idleWatch.Elapsed.TotalSeconds -lt 20){
 Start-Sleep -Seconds 2
 $before=Get-P09ResourceSample;$idleSamples+=@($before)
 if($before.system_cpu_percent -ge 85){$idleHot++}else{$idleHot=0}
 $idleDecision=Get-P09ResourceDecision -SystemCpuPercent $before.system_cpu_percent -FreeMemoryMiB $before.available_ram_mib -TestWorkingSetMiB 0 -HotSamples $idleHot
 if($idleDecision -ne 'CONTINUE'){$idleReason=$idleDecision;break}
 if($before.system_cpu_percent -le 50 -and $before.available_ram_mib -ge 8192){$idleCount++}else{$idleCount=0}
 if($idleCount -ge 3){break}
}
$idleWatch.Stop()
if($idleCount -lt 3 -or $idleReason){
 @{schema_version='hwpx-agent.p09-144-current-workspace-lint/v1';state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';
   samples=$idleSamples;stop_reason=$idleReason;test_or_app_executed=$false;lint_started=$false;
   product_complete=$false;P09_gate='OPEN'}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $receipt -Encoding utf8
 exit 2
}
$mask=Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 1
$proc=[Diagnostics.Process]::new()
$proc.StartInfo.WorkingDirectory=$root
$proc.StartInfo.UseShellExecute=$false
$proc.StartInfo.CreateNoWindow=$true
$proc.StartInfo.RedirectStandardOutput=$true
$proc.StartInfo.RedirectStandardError=$true
$proc.StartInfo.FileName=(Get-Command cargo -CommandType Application | Select-Object -First 1).Source
$arguments=@('clippy','--workspace','--all-targets','--locked','--offline','--jobs','1','--target-dir',$target,'--message-format','json','--','-D','warnings')
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($idleSamples);$hot=0;$reason=$null;$safe=$null;$sourceExact=$false;$started=$false;$buildMarker=$false
$descendantChecks=0;$artifacts=@();$diagnostics=@();$buildFinished=$false;$protectedExact=$false;$coverageExact=$false;$missingTargets=@();$unexpectedTargets=@()
try {
    if(-not $proc.Start()){throw 'start_failed'}
    $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
    if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'limits_not_applied'}
    $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
    Write-Output ('P144_STARTED:'+(@{pid=$proc.Id;mode='workspace_strict_lint';cpu_limit=1;priority='BelowNormal'}|ConvertTo-Json -Compress))
    while(-not $proc.WaitForExit(2000)) {
        if($true) {
            $parents=@($proc.Id)
            for($depth=0;$depth -lt 4 -and $parents.Count -gt 0;$depth++) {
                $children=@(Get-CimInstance Win32_Process -Filter ('ParentProcessId='+($parents -join ' OR ParentProcessId=')))
                $parents=@()
                foreach($child in $children) {
                    $owned=Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
                    if($owned -and -not $owned.HasExited) {
                        $owned.ProcessorAffinity=[IntPtr]$mask;$owned.PriorityClass='BelowNormal'
                        if($owned.ProcessorAffinity.ToInt64() -ne $mask -or $owned.PriorityClass -ne 'BelowNormal'){throw 'child_limits_failed'}
                        $descendantChecks++;$parents+=@($owned.Id)
                    }
                }
            }
        }
        $sample=Get-P09ResourceSample -TestProcess $proc;$samples+=@($sample)
        if(-not $proc.HasExited -and ($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal')){throw 'limits_changed'}
        if($sample.system_cpu_percent -ge 85){$hot++}else{$hot=0}
        $decision=Get-P09ResourceDecision -SystemCpuPercent $sample.system_cpu_percent -FreeMemoryMiB $sample.available_ram_mib -TestWorkingSetMiB $sample.test_working_set_mib -HotSamples $hot
        if($watch.Elapsed.TotalSeconds -ge $MaximumSeconds){$decision='STOP_DURATION_LIMIT'}
        if($decision -ne 'CONTINUE'){$reason=$decision;$proc.Kill($true);break}
        if(($samples.Count-1)%6 -eq 0){Write-Output ('P144_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
    }
    $proc.WaitForExit()
    $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
    foreach($line in ($out -split '\r?\n')) {
        if(-not $line.Trim()){continue}
        $message=$line|ConvertFrom-Json -ErrorAction Stop
        if($message.reason -eq 'build-finished'){$buildFinished=$message.success}
        if($message.reason -eq 'compiler-artifact' -and $metadata.workspace_members -ccontains $message.package_id) {
            $artifacts+=@([ordered]@{package_id=$message.package_id;name=$message.target.name;kind=@($message.target.kind);test_profile=$message.profile.test;fresh=$message.fresh})
        }
        if($message.reason -eq 'compiler-message') {
            $codeValue=if($message.message.code){$message.message.code.code}else{$null}
            $spans=@($message.message.spans|Where-Object {$_.is_primary}|ForEach-Object {
                $name=$_.file_name.Replace('\','/')
                if([IO.Path]::IsPathRooted($name)){$name=[IO.Path]::GetRelativePath($root,$name).Replace('\','/')}
                if($name -cmatch '^(crates|protocol/generated/rust|tools/xtask|implementation/p09/tests|implementation/p09/source-archive)/[A-Za-z0-9_/.-]+\.rs$') {
                    [ordered]@{path=$name;line_start=$_.line_start;line_end=$_.line_end;column_start=$_.column_start;column_end=$_.column_end}
                }
            })
            $diagnostics+=@([ordered]@{level=$message.message.level;code=$codeValue;spans=$spans})
        }
    }
    # exit0나 build-finished만으로 전체 target 커버리지를 대신하지 않는다.
    $expectedKeys=@($workspace|ForEach-Object {$_.package_id+'|'+$_.name+'|'+(($_.kind|Sort-Object)-join ',')}|Sort-Object -Unique)
    $actualKeys=@($artifacts|ForEach-Object {$_.package_id+'|'+$_.name+'|'+(($_.kind|Sort-Object)-join ',')}|Sort-Object -Unique)
    $missingTargets=@($expectedKeys|Where-Object {$_ -cnotin $actualKeys})
    $unexpectedTargets=@($actualKeys|Where-Object {$_ -cnotin $expectedKeys})
    $coverageExact=$expectedKeys.Count -eq 361 -and $actualKeys.Count -eq 361 -and $missingTargets.Count -eq 0 -and $unexpectedTargets.Count -eq 0
    foreach($row in $protectedPins) {
        $file=Join-Path $root $row.path
        if((Get-Item -LiteralPath $file).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $row.sha256){throw 'protected_executable_drift'}
    }
    $protectedExact=$true
    foreach($row in $freeze) {
        $file=Join-Path $root $row.path
        if((Get-Item -LiteralPath $file).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $row.sha256){throw 'source_drift'}
    }
    $sourceExact=$true
} catch {if(-not $reason){$reason='RUNNER_OR_OBSERVATION_FAILURE'}}
finally {
    if($started -and -not $proc.HasExited){$proc.Kill($true);$proc.WaitForExit()}
    $watch.Stop()
    $exitCode=if($started){$proc.ExitCode}else{$null}
    $pass=$sourceExact -and $protectedExact -and $coverageExact -and -not $reason -and $exitCode -eq 0 -and $buildFinished -and @($diagnostics|Where-Object {$_.level -in @('error','warning')}).Count -eq 0
    $state=if($pass){'PASS_SOURCE_ONLY_NOT_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
    @{schema_version='hwpx-agent.p09-144-current-workspace-lint/v1';state=$state;mode='workspace_strict_lint';workspace_inventory=$workspace;
      source_freeze=$freeze;source_freeze_exact_after=$sourceExact;protected_executables=$protectedPins;protected_executables_exact_after=$protectedExact;
      cargo_arguments=$arguments;workspace_artifacts=$artifacts;workspace_target_coverage_exact=$coverageExact;missing_targets=$missingTargets;unexpected_targets=$unexpectedTargets;diagnostics=$diagnostics;build_finished_success=$buildFinished;exit_code=$exitCode;stop_reason=$reason;
      elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;
      priority='BelowNormal';cargo_jobs=1;sample_seconds=2;cpu_stop_percent=85;cpu_stop_consecutive_samples=3;
      minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;maximum_seconds=$MaximumSeconds;
      post_hash_idle_policy=@{cpu_max_percent=50;free_ram_min_mib=8192;required_consecutive=3;maximum_seconds=20};
      observed_build_child_limit_checks=$descendantChecks;lint_started=$started;test_or_app_executed=$false;product_complete=$false;P09_gate='OPEN'}|
        ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P144_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
    $proc.Dispose()
}
if(-not $pass){exit 1}
