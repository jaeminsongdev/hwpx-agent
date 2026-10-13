# P129: current EXE의 원본/변경/보호 수식 marker를 재수집한다. 동일 resource guard 및 폐쇄형 parser.
[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('Test')][string]$Mode,
      [ValidatePattern('^[a-zA-Z0-9_:]+$')][string]$TestName,
      [Parameter(Mandatory)][string]$ReceiptPath,
      [ValidateRange(30,1800)][int]$MaximumSeconds=600)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/changed_formula_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target=Join-Path $root 'target/p09-121-resource-optimized'
$selection=@{Package='hwpx-agent-cli';Test='form_stored_provider';Count=1}
$oldExe=Join-Path $target 'debug/deps/form_stored_provider-658c5ea10a96d565.exe'
$oldHash='04fefdf71582488f4490a5e572203994d89fbc890c1282b5336b3703a581a5ca'
$currentExe=Join-Path $target 'debug/deps/form_stored_provider-p129-current.exe'
if((Get-Item -LiteralPath $oldExe).Length -ne 10688512 -or (Get-FileHash -LiteralPath $oldExe).Hash.ToLowerInvariant() -ne $oldHash){throw 'historical_executable_drift'}
if($Mode -eq 'Build' -and (Test-Path -LiteralPath $currentExe)){throw 'current_executable_already_exists'}
if($Mode -eq 'Test' -and -not $TestName){throw 'exact_case_name_required'}
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) {throw 'new_receipt_required'}
if (@(Get-Process -Name 'form_stored_provider*','comment_style_section_protection*','comment_model-*','comment_operation-*','stored_comment_provider-*' -ErrorAction SilentlyContinue).Count -gt 0) {throw 'test_already_running'}
$sources=@(& rg --files crates | ForEach-Object {$_.Replace('\','/')})+@('Cargo.toml','Cargo.lock',
 'implementation/p04/trust/p04-direct-route-attestation.json','implementation/p04/trust/p04-direct-route-attestation.sig',
 'tools/p09/run_current_form_regression.ps1','tools/p09/run_current_formula_markers.ps1',
 'tools/p09/resource_bounded_test_support.ps1','tools/p09/changed_formula_test_support.ps1')
if($LASTEXITCODE -ne 0 -or $sources.Count -ne 764){throw 'compiled_source_inventory_drift'}
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
    $proc.StartInfo.FileName=(Get-Command cargo -CommandType Application).Source
    $arguments=@('rustc','-p',$selection.Package,'--test',$selection.Test,'--profile','test','--locked','--offline','--jobs','1','--target-dir',$target,'--','-C','extra-filename=-p129-current')
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_OPT_LEVEL']='1'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS']='true'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_OVERFLOW_CHECKS']='true'
    $proc.StartInfo.Environment['CARGO_PROFILE_TEST_CODEGEN_UNITS']='1'
} else {
    $exe=Get-Item -LiteralPath $currentExe
    $proc.StartInfo.FileName=$exe.FullName
    $exePin=@{path=[IO.Path]::GetRelativePath($root,$exe.FullName).Replace('\','/');bytes=$exe.Length;
        sha256=(Get-FileHash -LiteralPath $exe.FullName).Hash.ToLowerInvariant()}
    $arguments=if($Mode -eq 'List'){@('--list')}else{@($TestName,'--exact','--nocapture','--test-threads=1')}
}
foreach($argument in $arguments){$proc.StartInfo.ArgumentList.Add($argument)}
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=@($before);$hot=0;$reason=$null;$safe=$null;$sourceExact=$false;$started=$false;$buildMarker=$false
$descendantChecks=0;$inventory=@();$oldExact=$false
try {
    if(-not $proc.Start()){throw 'start_failed'}
    $started=$true;$proc.ProcessorAffinity=[IntPtr]$mask;$proc.PriorityClass='BelowNormal'
    if($proc.ProcessorAffinity.ToInt64() -ne $mask -or $proc.PriorityClass -ne 'BelowNormal'){throw 'limits_not_applied'}
    $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
    Write-Output ('P129_STARTED:'+(@{pid=$proc.Id;mode=$Mode;cpu_limit=1;priority='BelowNormal'}|ConvertTo-Json -Compress))
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
        if(($samples.Count-1)%6 -eq 0){Write-Output ('P129_SAMPLE:'+($sample|ConvertTo-Json -Compress))}
    }
    $proc.WaitForExit()
    $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
    if($Mode -eq 'Test'){$safe=ConvertTo-P121SafeTestResult -Output ($out+"`n"+$err)}
    elseif($Mode -eq 'Build'){$buildMarker=$err.Contains('Finished') -and (Test-Path -LiteralPath $currentExe)}
    else{
        $inventory=@($out -split '\r?\n' | Where-Object {$_ -cmatch '^[A-Za-z0-9_:]+: test$'} | ForEach-Object {$_.Substring(0,$_.Length-6)})
        if($inventory.Count -ne 228 -or @($inventory|Select-Object -Unique).Count -ne 228){throw 'inventory_count_drift'}
    }
    if((Get-Item -LiteralPath $oldExe).Length -ne 10688512 -or (Get-FileHash -LiteralPath $oldExe).Hash.ToLowerInvariant() -ne $oldHash){throw 'historical_executable_changed'}
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
        (($Mode -eq 'List' -and $inventory.Count -eq 228) -or ($Mode -eq 'Build' -and $buildMarker) -or ($Mode -eq 'Test' -and $safe -and $safe.terminal_summary -and
         $safe.terminal_summary.outcome -eq 'ok' -and $safe.terminal_summary.passed -eq $selection.Count -and $safe.terminal_summary.failed -eq 0 -and $safe.terminal_summary.ignored -eq 0 -and $safe.terminal_summary.filtered -eq 227 -and $safe.terminal_summary.measured -eq 0 -and @($safe.passed_test_names|Select-Object -Unique).Count -eq $selection.Count -and $safe.passed_test_names[0] -ceq $TestName))
    $state=if($pass){'PASS_SOURCE_ONLY_NOT_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
    @{schema_version='hwpx-agent.p09-current-form-markers/v1';state=$state;mode=$Mode;test_name=$TestName;inventory=$inventory;historical_executable_exact_after=$oldExact;expected_test_count=$selection.Count;source_freeze=$freeze;
      source_freeze_exact_after=$sourceExact;executable_pin=$exePin;tests=$safe;exit_code=$exitCode;stop_reason=$reason;
      elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);samples=$samples;logical_cpu_limit=1;affinity_mask=$mask;
      priority='BelowNormal';cargo_jobs=1;sample_seconds=2;cpu_stop_percent=85;cpu_stop_consecutive_samples=3;
      minimum_available_ram_mib=4096;maximum_root_working_set_mib=2048;maximum_seconds=$MaximumSeconds;
      observed_build_child_limit_checks=$descendantChecks;build_marker=$buildMarker;product_complete=$false;P09_gate='OPEN'}|
        ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receipt -Encoding utf8
    Write-Output ('P129_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
    $proc.Dispose()
}
if(-not $pass){exit 1}
