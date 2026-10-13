# P137: SQL22 registry 읽기 제품 연결. CPU1; 실제 DB/UI/키 설치는 실행하지 않는다.
[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('Build','List','Test')][string]$Mode,
      [Parameter(Mandatory)][ValidateSet('Registry','Revision','Product','Artifact')][string]$Suite,
      [Parameter(Mandatory)][string]$ReceiptPath,
      [string]$ListReceiptPath,
      [ValidatePattern('^r[1-9][0-9]*$')][string]$Variant='r1',
      [ValidateRange(30,1800)][int]$MaximumSeconds=600)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target=Join-Path $root 'target/p09-121-resource-optimized'
$selection=switch($Suite){
 'Registry'{@{Package='hwpx-agent-cli';Test='form_stored_provider';Count=7;Kind='test';Filter='actual_import::formula_policy_issuer::registry::';Filtered=234}}
 'Revision'{@{Package='revision-service';Test='revision_service';Count=0;Kind='lib';Filter='';Filtered=0}}
 'Product'{@{Package='hwpx-agent-cli';Test='hwpx_agent_cli';Count=0;Kind='lib';Filter='';Filtered=0}}
 'Artifact'{@{Package='artifact-service';Test='artifact_service';Count=0;Kind='lib';Filter='';Filtered=0}}
}
$currentExe=Join-Path $target ('debug/deps/'+$selection.Test+'-p137-'+$Variant+'.exe')
if($Mode -eq 'Build' -and (Test-Path -LiteralPath $currentExe)){throw 'current_executable_already_exists'}
$protectedPins=@((Get-Content -LiteralPath (Join-Path $target 'p135-case-001-attempt-001.json') -Raw | ConvertFrom-Json).protected_executables)
function Test-ProtectedPins {
 if($protectedPins.Count -ne 21){throw 'protected_executable_coverage_drift'}
 foreach($row in $protectedPins){
  $file=Join-Path $root $row.path
  if((Get-Item -LiteralPath $file).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $row.sha256){throw 'protected_executable_drift'}
 }
}
Test-ProtectedPins
$listNames=@()
if($Mode -eq 'Test'){
 $listFile=if($ListReceiptPath){[IO.Path]::GetFullPath((Join-Path $root $ListReceiptPath))}else{Join-Path $target ('p137-'+$Suite.ToLowerInvariant()+'-list-a.json')}
 if(-not $listFile.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($listFile) -ne '.json'){throw 'list_receipt_outside_target'}
 $listDoc=Get-Content -LiteralPath $listFile -Raw | ConvertFrom-Json
 if($listDoc.state -ne 'PASS_SOURCE_ONLY_NOT_GATE' -or $listDoc.suite -ne $Suite -or ($selection.Count -gt 0 -and $listDoc.inventory.Count -ne $selection.Count) -or
    $listDoc.executable_pin.sha256 -ne (Get-FileHash -LiteralPath $currentExe).Hash.ToLowerInvariant()){throw 'current_list_binding_missing'}
 $listNames=@($listDoc.inventory)
 if($selection.Kind -eq 'lib'){$selection.Count=$listNames.Count}
}
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) {throw 'new_receipt_required'}
if (@(Get-Process -Name 'form_stored_provider*','comment_style_section_protection*','comment_model-*','comment_operation-*','stored_comment_provider-*','table_create_hwpx*','review_table_create_context*','review_table_output*','review_filled_table_output*' -ErrorAction SilentlyContinue).Count -gt 0) {throw 'test_already_running'}
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
$sources=$indexed+@('Cargo.toml','Cargo.lock',
 'implementation/p04/trust/p04-direct-route-attestation.json','implementation/p04/trust/p04-direct-route-attestation.sig',
 'tools/p09/run_formula_issuer_registry_reads.ps1','tools/p09/resource_bounded_test_support.ps1',
 'implementation/p09/tests/p09_132_comment_catalog_index.rs',
 'implementation/p09/source-archive/p09-132-pre-comment-catalog-index/crates/domain-ir/src/comment_model.rs',
 'implementation/p09/source-archive/p09-132-pre-comment-catalog-index/crates/domain-ir/tests/comment_style_section_protection.rs',
 'implementation/p09/source-archive/p09-134-pre-formula-revocation/crates/revision-service/src/postgres/source_formula_policy.rs',
 'implementation/p09/source-archive/p09-134-pre-formula-revocation/crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs',
 'implementation/p09/source-archive/p09-134-pre-formula-revocation/crates/product-cli/tests/form_stored_provider/actual_import.rs')
$sources+=@('implementation/p09/source-archive/p09-137-pre-registry-reads/parent-preimages.v1.json','implementation/p09/evidence/p09-136-formula-issuer-registry.source-progress.v1.json')
$sources+=@(Get-ChildItem -LiteralPath (Join-Path $root 'migrations/postgres') -Filter '*.up.sql' | Sort-Object Name | ForEach-Object {[IO.Path]::GetRelativePath($root,$_.FullName).Replace('\','/')})
Write-Output ('P137_SOURCE_INDEX:'+(@{exit_code=$indexExit;source_count=$sources.Count}|ConvertTo-Json -Compress))
if($indexExit -ne 0 -or $indexError.Length -ne 0 -or $sources.Count -lt 808 -or @($sources|Select-Object -Unique).Count -ne $sources.Count){throw 'compiled_source_inventory_drift'}
$freeze=@($sources|ForEach-Object {[ordered]@{path=$_;bytes=(Get-Item -LiteralPath (Join-Path $root $_)).Length;
    sha256=(Get-FileHash -LiteralPath (Join-Path $root $_)).Hash.ToLowerInvariant()}})
$before=Get-P09ResourceSample
if ($before.system_cpu_percent -ge 85 -or $before.available_ram_mib -lt 4096) {
    @{state='DEFERRED_RESOURCE_PRESSURE_NOT_STARTED';samples=@($before);product_complete=$false;P09_gate='OPEN'}|
        ConvertTo-Json -Depth 5|Set-Content -LiteralPath $receipt -Encoding utf8
    exit 2
}
$mask=Get-P09CpuMask -AllowedMask ([Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()) -Count 1
$proc=[Diagnostics.Process]::new()
$proc.StartInfo.WorkingDirectory=$root
$proc.StartInfo.UseShellExecute=$false
$proc.StartInfo.CreateNoWindow=$true
$proc.StartInfo.RedirectStandardOutput=$true
$proc.StartInfo.RedirectStandardError=$true
$exePin=$null
if($Mode -eq 'Build') {
    $proc.StartInfo.FileName=(Get-Command cargo -CommandType Application | Select-Object -First 1).Source
    $arguments=@('rustc','-p',$selection.Package)
    if($selection.Kind -eq 'test'){$arguments+=@('--test',$selection.Test)}else{$arguments+=@('--lib')}
    $arguments+=@('--profile','test','--locked','--offline','--jobs','1','--target-dir',$target,'--message-format=json','--')
    $arguments+=@('-C',('extra-filename=-p137-'+$Variant))
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_OPT_LEVEL']='1'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS']='true'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_OVERFLOW_CHECKS']='true'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_CODEGEN_UNITS']='1'
} else {
    $exe=Get-Item -LiteralPath $currentExe
    $proc.StartInfo.FileName=$exe.FullName
    $exePin=@{path=[IO.Path]::GetRelativePath($root,$exe.FullName).Replace('\','/');bytes=$exe.Length;
        sha256=(Get-FileHash -LiteralPath $exe.FullName).Hash.ToLowerInvariant()}
    $arguments=if($Mode -eq 'List'){@('--list')}else{@('--show-output','--test-threads=1')}
    if($selection.Filter){$arguments=@($selection.Filter)+$arguments}
}
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($before);$hot=0;$reason=$null;$safe=$null;$sourceExact=$false;$started=$false;$buildMarker=$false
$descendantChecks=0;$inventory=@();$oldExact=$false;$profile=$null;$diagnostics=@();$buildFinished=$false;$cargoFailure=@()
try {
    if(-not $proc.Start()){throw 'start_failed'}
    $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
    if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'limits_not_applied'}
    $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
    Write-Output ('P137_STARTED:'+(@{pid=$proc.Id;mode=$Mode;cpu_limit=1;priority='BelowNormal'}|ConvertTo-Json -Compress))
    while(-not $proc.WaitForExit(2000)) {
        if($Mode -eq 'Build') {
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
        if(($samples.Count-1)%6 -eq 0){Write-Output ('P137_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
    }
    $proc.WaitForExit()
    $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
    if($Mode -eq 'Test'){
        $safe=ConvertTo-P09SafeTestResult -Output ($out+"`n"+$err)

    }
    elseif($Mode -eq 'Build'){
      $cargoFailure=@($err -split '\r?\n' | Where-Object {$_ -cmatch '^error: [A-Za-z -]+.*$'} | Select-Object -First 2)
      foreach($buildLine in ($out -split '\r?\n')){
       if(-not $buildLine.StartsWith('{')){continue}
       $buildItem=$buildLine | ConvertFrom-Json
       if($buildItem.reason -eq 'build-finished'){$buildFinished=$buildItem.success}
       if($buildItem.reason -eq 'compiler-message' -and $buildItem.message.level -eq 'error'){
        $diagnostics+=@([ordered]@{code=$buildItem.message.code.code;spans=@($buildItem.message.spans|Where-Object {$_.is_primary}|ForEach-Object {[ordered]@{file=$_.file_name;line=$_.line_start}})})
       }
      }
      $buildMarker=$buildFinished -and (Test-Path -LiteralPath $currentExe)
    }
    else{
        $inventory=@($out -split '\r?\n' | Where-Object {$_ -cmatch '^[A-Za-z0-9_:]+: test$'} | ForEach-Object {$_.Substring(0,$_.Length-6)})
        if($selection.Kind -eq 'lib'){$selection.Count=$inventory.Count}
        if($inventory.Count -eq 0 -or $inventory.Count -ne $selection.Count -or @($inventory|Select-Object -Unique).Count -ne $selection.Count){throw 'inventory_count_drift'}
    }
    Test-ProtectedPins
    $oldExact=$true
    foreach($row in $freeze) {
        $file=Join-Path $root $row.path
        if((Get-Item -LiteralPath $file).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $row.sha256){throw 'source_drift'}
    }
    if($exePin -and (Get-FileHash -LiteralPath $proc.StartInfo.FileName).Hash.ToLowerInvariant() -ne $exePin.sha256){throw 'executable_drift'}
    $sourceExact=$true
} catch {if(-not $reason){$reason='RUNNER_OR_OBSERVATION_FAILURE'}}
finally {
    if($started -and -not $proc.HasExited){$proc.Kill($true);$proc.WaitForExit()}
    $watch.Stop()
    $exitCode=if($started){$proc.ExitCode}else{$null}
    $pass=$sourceExact -and $oldExact -and -not $reason -and $exitCode -eq 0 -and
        (($Mode -eq 'List' -and $inventory.Count -eq $selection.Count) -or ($Mode -eq 'Build' -and $buildMarker) -or ($Mode -eq 'Test' -and $safe -and $safe.terminal_summary -and
         $safe.terminal_summary.outcome -eq 'ok' -and $safe.terminal_summary.passed -eq $selection.Count -and $safe.terminal_summary.failed -eq 0 -and $safe.terminal_summary.ignored -eq 0 -and $safe.terminal_summary.filtered -eq $selection.Filtered -and $safe.terminal_summary.measured -eq 0 -and @($safe.passed_test_names|Select-Object -Unique).Count -eq $selection.Count -and @($safe.passed_test_names).Count -eq $selection.Count -and @(Compare-Object $listNames @($safe.passed_test_names) -CaseSensitive).Count -eq 0))
    $state=if($pass){'PASS_SOURCE_ONLY_NOT_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
    @{schema_version='hwpx-agent.p09-formula-issuer-registry-reads-runtime/v1';state=$state;mode=$Mode;suite=$Suite;inventory=$inventory;catalog_profile=$profile;protected_executables=$protectedPins;protected_executables_exact_after=$oldExact;expected_test_count=$selection.Count;filtered_test_count=$selection.Filtered;source_freeze=$freeze;
      source_freeze_exact_after=$sourceExact;executable_pin=$exePin;tests=$safe;exit_code=$exitCode;stop_reason=$reason;
      elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;
      priority='BelowNormal';cargo_jobs=1;sample_seconds=2;cpu_stop_percent=85;cpu_stop_consecutive_samples=3;
      minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;maximum_seconds=$MaximumSeconds;
      observed_build_child_limit_checks=$descendantChecks;build_marker=$buildMarker;build_diagnostics=$diagnostics;cargo_failure=$cargoFailure;product_complete=$false;P09_gate='OPEN'}|
        ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P137_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
    $proc.Dispose()
}
if(-not $pass){exit 1}
