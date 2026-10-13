# P143: 원래 source/revision/policy/signature/consumer SQL22 연결. 실제 DB/Gate 검증은 별도.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath,
 [ValidatePattern('^r[1-9][0-9]*$')][string]$Variant='r1',
 [ValidateRange(30,600)][int]$MaximumSeconds=600)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if([IO.Path]::GetFullPath((Get-Location).Path) -ne $root){throw 'wrong_root'}
$target=Join-Path $root 'target/p09-121-resource-optimized'
$currentExe=Join-Path $target ('debug/examples/formula_issuer_product_postgres_probe-p143-'+$Variant+'.exe')
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if(-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
 [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt) -or (Test-Path -LiteralPath $currentExe)){throw 'fresh_output_required'}
if(@(Get-Process -Name cargo,rustc,formula_issuer_registry_postgres_probe*,formula_registry_crypto_postgres_probe*,formula_issuer_product_postgres_probe*,form_stored_provider*,artifact_service* -ErrorAction SilentlyContinue).Count){throw 'other_rust_workload_running'}
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
$adapter=Get-Content -LiteralPath (Join-Path $target 'p141-adapter-build-r5.json') -Raw|ConvertFrom-Json
$partial=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-142-artifact-schema22.implementation-progress.v1.json') -Raw|ConvertFrom-Json
$protected+=@($adapter.executable_pin)+@($partial.unit_runtime.executable_pin)
$priorBuilds=@(Get-ChildItem -LiteralPath $target -Filter 'p142-root-crypto-build-r*.json' -File)
foreach($priorFile in $priorBuilds){
 $prior=Get-Content -LiteralPath $priorFile.FullName -Raw|ConvertFrom-Json
 if($prior.state -eq 'PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE'){
  if($prior.executable_pin.path -cnotmatch '^target/p09-121-resource-optimized/debug/examples/formula_registry_crypto_postgres_probe-p142-r[1-9][0-9]*\.exe$'){throw 'prior_probe_path_invalid'}
  $protected+=@($prior.executable_pin)
 }
}
foreach($priorFile in @(Get-ChildItem -LiteralPath $target -Filter 'p143-issuer-product-build-r*.json' -File)){
 $prior=Get-Content -LiteralPath $priorFile.FullName -Raw|ConvertFrom-Json
 if($prior.state -eq 'PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE'){
  if($prior.executable_pin.path -cnotmatch '^target/p09-121-resource-optimized/debug/examples/formula_issuer_product_postgres_probe-p143-r[1-9][0-9]*\.exe$'){throw 'prior_product_probe_path_invalid'}
  $protected+=@($prior.executable_pin)
 }
}
if($protected.Count -lt 37 -or @($protected.path|Select-Object -Unique).Count -ne $protected.Count){throw 'protected_coverage_drift'}
Test-Pins $protected
$old=Get-Content -LiteralPath (Join-Path $target 'p139-provision-build-r7.json') -Raw|ConvertFrom-Json
if($old.state -ne 'PASS_SOURCE_ONLY_NOT_GATE' -or $old.source_freeze.Count -ne 817){throw 'predecessor_build_missing'}
# 원본 parent의 역사적 pin은 전체 preimage로 확인. 현재 변경은 module 한 줄만 허용한다.
$parent='crates/artifact-service/src/store/postgres_repository.rs'
$archive=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/source-archive/p09-142-pre-artifact-schema22/source-preimages.v1.json') -Raw|ConvertFrom-Json
$row=@($archive.files|Where-Object {$_.path -eq $parent})
if($row.Count -ne 1){throw 'original_parent_archive_missing'}
$raw=[Convert]::FromBase64String(($row[0].base64_chunks -join ''))
$originalPin=@($old.source_freeze|Where-Object {$_.path -eq $parent})
$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()
if($originalPin.Count -ne 1 -or $raw.Length -ne $originalPin[0].bytes -or $hash -ne $originalPin[0].sha256){throw 'historical_parent_archive_drift'}
$original=[Text.Encoding]::UTF8.GetString($raw).Replace("`r`n","`n")
$actual=[IO.File]::ReadAllText((Join-Path $root $parent)).Replace("`r`n","`n")
$expected=$original.Replace("pub mod source_formula_policy;`n","pub mod source_formula_policy;`npub mod schema22;`n")
if($actual -cne $expected){throw 'undeclared_original_parent_change'}
Test-Pins @($old.source_freeze|Where-Object {$_.path -ne $parent})
$sources=@($old.source_freeze.path|Where-Object {$_ -ne 'tools/p09/run_formula_issuer_registry_provision.ps1'})+@(
 'tools/p09/build_formula_issuer_registry_adapter.ps1',
 'crates/revision-service/examples/formula_issuer_registry_postgres_probe.rs',
 'implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json',
 'implementation/p09/evidence/p09-140-formula-issuer-registry-sql.source-progress.v1.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r2.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r3.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r4.json')
$sources+=@(
 'tools/p09/build_formula_registry_crypto_probe.ps1',
 'crates/product-cli/examples/formula_registry_crypto_postgres_probe.rs',
 'crates/artifact-service/src/store/postgres_repository/schema22.rs',
 'tools/p09/tests/test_artifact_schema22_admission.py',
 'implementation/p09/source-archive/p09-142-pre-artifact-schema22/source-preimages.v1.json',
 'implementation/p09/source-archive/p09-142-pre-replication-role-parity/source-preimages.v1.json',
 'implementation/p09/source-archive/p09-142-pre-root-probe-refactor/source-preimages.v1.json',
 'implementation/p09/evidence/p09-142-artifact-schema22.implementation-progress.v1.json',
 'implementation/p09/evidence/p09-141-formula-issuer-registry-adapter.source-progress.v1.json',
 'target/p09-121-resource-optimized/p141-adapter-build-r5.json')
$sources+=@(
 'tools/p09/build_formula_issuer_product_probe.ps1',
 'crates/product-cli/examples/formula_issuer_product_postgres_probe.rs',
 'crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs',
 'crates/product-cli/examples/formula_issuer_product_postgres_probe/worker.rs',
 'implementation/p09/evidence/p09-142-root-crypto.source-progress.v1.json',
 'implementation/p09/evidence/p09-142-root-crypto-run03.v1.json',
 'implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json',
 'fixtures/target-build/p06-09-table-aggregate-target-20260909-05/table-022-block-sum.hancom-2020-readback.hwpx',
 'implementation/p09/source-archive/p09-143-pre-compiler-fix/source-preimages.v1.json')
if($sources.Count -ne 842 -or @($sources|Select-Object -Unique).Count -ne 842){throw 'source_inventory_drift'}
$current=Get-Content -LiteralPath (Join-Path $root 'implementation/p09/evidence/p09-142-root-crypto.source-progress.v1.json') -Raw|ConvertFrom-Json
Test-Pins $current.verified_direct_pins
$localInputs=@(& rg --files crates protocol/generated/rust tools/xtask -g '*.rs' -g 'Cargo.toml')
if($LASTEXITCODE -ne 0 -or @($localInputs|Where-Object {$_.Replace('\','/') -notin $sources}).Count){throw 'whole_workspace_Rust_input_coverage_drift'}
$freeze=@($sources|ForEach-Object {[ordered]@{path=$_;bytes=(Get-Item -LiteralPath (Join-Path $root $_)).Length;
 sha256=(Get-FileHash -LiteralPath (Join-Path $root $_)).Hash.ToLowerInvariant()}})
# 역사적 pin/842 Rust 입력/protected EXE 검사는 위 원문 그대로 유지한다.
# Cargo는 Job 할당·kernel readback·GO 후에만 시작한다. 무제한 ReadToEndAsync 사용 금지.
$supervisorReceipt=Join-Path $target ('p149-issuer-product-build-supervisor-'+$Variant+'.json')
if(Test-Path -LiteralPath $supervisorReceipt){throw 'fresh_supervisor_receipt_required'}
$python=(Get-Command python -CommandType Application|Select-Object -First 1).Source
$supervisorRelative=[IO.Path]::GetRelativePath($root,$supervisorReceipt).Replace('\','/')
& $python (Join-Path $PSScriptRoot 'owned_probe_build.py') --variant $Variant --receipt $supervisorRelative --maximum-seconds $MaximumSeconds
$supervisorExit=$LASTEXITCODE
$supervisorFile=Get-Item -LiteralPath $supervisorReceipt
if($supervisorFile.Length -gt 4194304 -or $supervisorFile.LinkType){throw 'supervisor_receipt_scope_invalid'}
$supervisor=Get-Content -LiteralPath $supervisorReceipt -Raw|ConvertFrom-Json
if($supervisor.schema_version -ne 'hwpx-agent.p09-owned-probe-build/v1'){throw 'supervisor_schema_invalid'}
$exact=$false;$oldExact=$false;$pin=$null;$reason=$supervisor.stop_reason
try {
 Test-Pins $protected;$oldExact=$true;Test-Pins $freeze;$exact=$true
 if(Test-Path -LiteralPath $currentExe){
  $exeFile=Get-Item -LiteralPath $currentExe
  if($exeFile.LinkType){throw 'new_executable_link_invalid'}
  $pin=@{path=[IO.Path]::GetRelativePath($root,$currentExe).Replace('\','/');
   bytes=$exeFile.Length;sha256=(Get-FileHash -LiteralPath $currentExe).Hash.ToLowerInvariant()}
 }
} catch {if(-not $reason){$reason='BUILD_OR_OBSERVATION_FAILURE'}}
$supervised=$supervisorExit -eq 0 -and $supervisor.state -eq 'PASS_SUPERVISED_COMPILER_ONLY_NOT_SOURCE_DB_OR_GATE' -and
 $supervisor.helper_source_freeze_exact_after -and $supervisor.cleanup_confirmed -and
 $supervisor.owned_job_profile.owned_tree_empty -and $supervisor.owned_job_profile.job_handle_closed -and
 $supervisor.owned_job_profile.limits_readback.verified -and $supervisor.owned_job_profile.job_assigned -and
 $supervisor.owned_job_profile.target_authorized
$exitCode=$supervisor.exit_code;$finished=$supervisor.build_finished_success
$profile=$supervisor.catalog_profile;$diagnostics=@($supervisor.diagnostics)
$pass=$exact -and $oldExact -and $supervised -and -not $reason -and $exitCode -eq 0 -and
 $finished -and $pin -and $diagnostics.Count -eq 0 -and $profile -and -not $profile.test
$state=if($pass){'PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE'}else{'NOT_ACCEPTED_STOP_OR_FAILURE'}
$result=@{schema_version='hwpx-agent.p09-143-issuer-product-build/v1';state=$state;source_freeze=$freeze;
 source_freeze_exact_after=$exact;whole_workspace_Rust_input_coverage_enforced=$true;historical_parent_archive_verified=$true;
 protected_executables=$protected;protected_executables_exact_after=$oldExact;executable_pin=$pin;catalog_profile=$profile;
 build_finished_success=$finished;diagnostics=$diagnostics;exit_code=$exitCode;stop_reason=$reason;
 elapsed_seconds=$supervisor.elapsed_seconds;samples=@($supervisor.samples);logical_cpu_limit=1;affinity_mask=$supervisor.affinity_mask;
 priority='BelowNormal';cargo_jobs=1;maximum_seconds=$MaximumSeconds;
 probe_supervisor=$supervisor;probe_supervisor_receipt=$supervisorRelative;probe_supervisor_accepted=$supervised;
 cpu_stop_percent=98;cpu_stop_consecutive_samples=4;minimum_available_ram_percent=8;maximum_commit_used_percent=95;
 aggregate_job_memory_hard_percent=8;aggregate_job_memory_stop_percent=7;
 actual_DB_executed=$false;P09_gate='OPEN';product_complete=$false}
# 새 receipt는 CreateNew로만 생성하여 경합 중 기존 증거를 덮어쓰지 않는다.
$stream=[IO.FileStream]::new($receipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
$writer=$null
try {$writer=[IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($false));$writer.Write(($result|ConvertTo-Json -Depth 14));$writer.Flush()}
finally {if($writer){$writer.Dispose()}else{$stream.Dispose()}}
Write-Output ('P143_BUILD_TERMINAL:'+(@{state=$state;exit_code=$exitCode;reason=$reason;receipt=$ReceiptPath}|ConvertTo-Json -Compress))
if(-not $pass){exit 1}
