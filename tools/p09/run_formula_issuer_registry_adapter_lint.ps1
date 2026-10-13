# P141: 신규 credential-bound adapter example 포함 전체 workspace 엄격 lint. 테스트/앱/DB/UI는 실행하지 않고 진단 code/span만 보존한다.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath,
      [ValidateRange(60,1800)][int]$MaximumSeconds=900)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target=Join-Path $root 'target/p09-121-resource-optimized'
$metadata=& cargo metadata --format-version 1 --no-deps --locked --offline | ConvertFrom-Json
if($LASTEXITCODE -ne 0 -or $metadata.workspace_members.Count -ne 32){throw 'workspace_inventory_drift'}
if(@($metadata.packages.targets|Where-Object {$_.kind -contains 'custom-build'}).Count -ne 0){throw 'workspace_build_script_not_admitted'}
$workspace=@($metadata.packages|ForEach-Object {$package=$_; foreach($item in $package.targets){[ordered]@{package_id=$package.id;package=$package.name;name=$item.name;kind=@($item.kind);src_path=[IO.Path]::GetRelativePath($root,$item.src_path).Replace('\','/')}}})
if($workspace.Count -ne 359){throw 'workspace_target_inventory_drift'}
$protectedPins=@((Get-Content -LiteralPath (Join-Path $target 'p135-case-001-attempt-001.json') -Raw | ConvertFrom-Json).protected_executables)
$previousRegistry=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-137-formula-issuer-registry-reads.source-progress.v1.json') -Raw|ConvertFrom-Json
$protectedPins+=@($previousRegistry.current_executables)+@($previousRegistry.earlier_executables_preserved)
$previousManagement=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-138-formula-issuer-registry-management.source-progress.v1.json') -Raw|ConvertFrom-Json
$protectedPins+=@($previousManagement.current_executable)
$previousProvision=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json') -Raw|ConvertFrom-Json
$protectedPins+=@($previousProvision.current_executable)+@($previousProvision.earlier_executables_preserved)
$probeBuild=Get-Content -LiteralPath (Join-Path $target 'p141-adapter-build-r5.json') -Raw|ConvertFrom-Json
$protectedPins+=@($probeBuild.protected_executables|Where-Object {$_.path -match '-p141-'})+@($probeBuild.executable_pin)
if($protectedPins.Count -ne 36){throw 'protected_executable_coverage_drift'}
foreach($row in $protectedPins){
 $path=Join-Path $root $row.path
 if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256){throw 'protected_executable_drift'}
}
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) {throw 'new_receipt_required'}
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
$sources=@($probeBuild.source_freeze.path|Where-Object {$_ -ne 'tools/p09/build_formula_issuer_registry_adapter.ps1'})+@(
 'tools/p09/run_formula_issuer_registry_adapter_lint.ps1','target/p09-121-resource-optimized/p141-adapter-build-r5.json')
if($sources.Count -ne 824 -or @($sources|Select-Object -Unique).Count -ne 824 -or
 @($indexed|Where-Object {$_ -notin $sources}).Count -ne 0 -or $indexExit -ne 0 -or $indexError.Length -ne 0){throw 'compiled_source_inventory_drift'}
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
$proc.StartInfo.FileName=(Get-Command cargo -CommandType Application | Select-Object -First 1).Source
$arguments=@('clippy','--workspace','--all-targets','--locked','--offline','--jobs','1','--target-dir',$target,'--message-format','json','--','-D','warnings')
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($before);$hot=0;$reason=$null;$safe=$null;$sourceExact=$false;$started=$false;$buildMarker=$false
$descendantChecks=0;$artifacts=@();$diagnostics=@();$buildFinished=$false;$protectedExact=$false
try {
    if(-not $proc.Start()){throw 'start_failed'}
    $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
    if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'limits_not_applied'}
    $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
    Write-Output ('P141_STARTED:'+(@{pid=$proc.Id;mode='workspace_strict_lint';cpu_limit=1;priority='BelowNormal'}|ConvertTo-Json -Compress))
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
        if(($samples.Count-1)%6 -eq 0){Write-Output ('P141_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
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
    $pass=$sourceExact -and $protectedExact -and -not $reason -and $exitCode -eq 0 -and $buildFinished -and @($diagnostics|Where-Object {$_.level -in @('error','warning')}).Count -eq 0
    $state=if($pass){'PASS_SOURCE_ONLY_NOT_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
    @{schema_version='hwpx-agent.p09-current-optimized-workspace-lint/v1';state=$state;mode='workspace_strict_lint';workspace_inventory=$workspace;
      source_freeze=$freeze;source_freeze_exact_after=$sourceExact;protected_executables=$protectedPins;protected_executables_exact_after=$protectedExact;
      cargo_arguments=$arguments;workspace_artifacts=$artifacts;diagnostics=$diagnostics;build_finished_success=$buildFinished;exit_code=$exitCode;stop_reason=$reason;
      elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;
      priority='BelowNormal';cargo_jobs=1;sample_seconds=2;cpu_stop_percent=85;cpu_stop_consecutive_samples=3;
      minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;maximum_seconds=$MaximumSeconds;
      observed_build_child_limit_checks=$descendantChecks;test_or_app_executed=$false;product_complete=$false;P09_gate='OPEN'}|
        ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P141_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
    $proc.Dispose()
}
if(-not $pass){exit 1}
