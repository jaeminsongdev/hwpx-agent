# 읽기 전용 독립 CPU/RAM 대조. 기존 test runner의 중단 기준/샘플링 코드는 수정하지 않는다.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ReceiptPath,[ValidateRange(1,8)][int]$Count=4,
      [ValidateRange(1,5)][int]$IntervalSeconds=2)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/native_resource_crosscheck_support.ps1"
. "$PSScriptRoot/resource_bounded_test_support.ps1"
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$target=[IO.Path]::GetFullPath((Join-Path $root 'target/p09-122-resource-crosscheck'))
$receipt=[IO.Path]::GetFullPath((Join-Path $root $ReceiptPath))
if (-not $receipt.StartsWith($target+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetExtension($receipt) -ne '.json' -or (Test-Path -LiteralPath $receipt)) { throw 'crosscheck_receipt_scope_or_existing_file' }
if (@(Get-Process -Name 'form_stored_provider*' -ErrorAction SilentlyContinue).Count -gt 0) { throw 'crosscheck_requires_no_stored_test' }
New-Item -ItemType Directory -Path $target -Force|Out-Null
$self=[Diagnostics.Process]::GetCurrentProcess()
$mask=Get-P09CpuMask -AllowedMask $self.ProcessorAffinity.ToInt64() -Count 1
$self.ProcessorAffinity=[IntPtr]$mask
$self.PriorityClass='BelowNormal'
Initialize-P122NativeMetrics
$cores=[Environment]::ProcessorCount
$samples=@()
for ($index=0;$index -lt $Count;$index++) {
    [ulong]$idleA=0; [ulong]$kernelA=0; [ulong]$userA=0
    if (-not [P122.NativeMetrics]::GetSystemTimes([ref]$idleA,[ref]$kernelA,[ref]$userA)) { throw 'native_system_times_read_failed' }
    $watch=[Diagnostics.Stopwatch]::StartNew()
    Start-Sleep -Seconds $IntervalSeconds
    $cim=Get-P09ResourceSample
    [ulong]$idleB=0; [ulong]$kernelB=0; [ulong]$userB=0
    if (-not [P122.NativeMetrics]::GetSystemTimes([ref]$idleB,[ref]$kernelB,[ref]$userB)) { throw 'native_system_times_read_failed' }
    $watch.Stop()
    $memory=[P122.MemoryStatus]::new()
    $memory.Length=64
    if (-not [P122.NativeMetrics]::GlobalMemoryStatusEx([ref]$memory)) { throw 'native_memory_read_failed' }
    $nativeCpu=Get-P122CpuPercent $idleA $kernelA $userA $idleB $kernelB $userB $cores
    $nativeMemory=Get-P122MemoryMiB $memory.AvailablePhys $memory.TotalPhys $memory.MemoryLoad
    $inputs=Get-P122ConservativeInputs $nativeCpu $cim.system_cpu_percent $nativeMemory.available_ram_mib $cim.available_ram_mib
    $sample=[ordered]@{index=$index;time_utc=[datetime]::UtcNow.ToString('o');native_interval_seconds=[math]::Round($watch.Elapsed.TotalSeconds,3);
        native_cpu_percent=$nativeCpu;cim_cpu_percent=$cim.system_cpu_percent;native_available_ram_mib=$nativeMemory.available_ram_mib;
        cim_available_ram_mib=$cim.available_ram_mib;native_total_ram_mib=$nativeMemory.total_ram_mib;
        conservative_inputs=$inputs;resource_decision=Get-P09ResourceDecision $inputs.system_cpu_percent $inputs.available_ram_mib 0 3}
    $samples+=$sample
    Write-Output ('P122_CROSSCHECK_SAMPLE:'+($sample|ConvertTo-Json -Depth 4 -Compress))
}
$result=[ordered]@{schema_version='hwpx-agent.p09-122-resource-crosscheck/v1';state='MEASURED_READ_ONLY_NOT_TEST_RUN_OR_MONITOR_REPLACEMENT';
    logical_processors=$cores;measurement_process_cpu_limit=1;priority='BelowNormal';samples=$samples;stored_test_started=$false;
    measurements_have_adjacent_not_identical_windows=$true;pressure_cause='NOT_DETERMINED';existing_runner_or_thresholds_modified=$false;
    native_API_is_metrics_only_not_Hangul_or_UI=$true;system_settings_changed=$false;P09_gate='OPEN';product_complete=$false}
$result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $receipt -Encoding utf8
Write-Output 'P122_CROSSCHECK_TERMINAL:MEASURED_READ_ONLY_NOT_TEST_OR_GATE'
