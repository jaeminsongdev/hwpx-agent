Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]1
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
. "$PSScriptRoot/../native_resource_crosscheck_support.ps1"
function Assert-P122($condition){if(-not $condition){throw 'resource_crosscheck_assertion_failed'}}
function Reject-P122([scriptblock]$action){$rejected=$false;try{&$action|Out-Null}catch{$rejected=$true};Assert-P122 $rejected}
Assert-P122 ((Get-P122CpuPercent 100 200 50 200 400 150 16)-eq [math]::Round(100*(1-100/300),2))
Assert-P122 ((Get-P122CpuPercent 0 0 0 100 100 0 16)-eq 0)
Assert-P122 ((Get-P122CpuPercent 0 0 0 0 100 0 16)-eq 100)
Reject-P122 {Get-P122CpuPercent 10 0 0 9 10 0 16}
Reject-P122 {Get-P122CpuPercent 0 0 0 0 0 0 16}
Reject-P122 {Get-P122CpuPercent 0 0 0 20 10 0 16}
Reject-P122 {Get-P122CpuPercent 0 0 0 0 10 0 65}
Assert-P122 ((Get-P122MemoryMiB 4GB 32GB 80).available_ram_mib-eq 4096)
Reject-P122 {Get-P122MemoryMiB 33GB 32GB 1}
Reject-P122 {Get-P122MemoryMiB 0 0 0}
Reject-P122 {Get-P122MemoryMiB 4GB 32GB 101}
$safe=Get-P122ConservativeInputs 90 12 8192 4095
Assert-P122 ($safe.system_cpu_percent-eq 90 -and $safe.available_ram_mib-eq 4095)
Reject-P122 {Get-P122ConservativeInputs ([double]::NaN) 10 4096 8192}
Reject-P122 {Get-P122ConservativeInputs 10 101 4096 8192}
Reject-P122 {Get-P122ConservativeInputs 10 20 -1 8192}
Assert-P122 ((ConvertTo-P122MachineCpuPercent ([ulong]97) 16) -eq 6.0625)
Assert-P122 ((ConvertTo-P122MachineCpuPercent 1600 16) -eq 100)
Assert-P122 ((ConvertTo-P122MachineCpuPercent 0 16) -eq 0)
Reject-P122 {ConvertTo-P122MachineCpuPercent $true 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent '97' 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent ([double]::NaN) 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent ([double]::PositiveInfinity) 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent -1 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent 1601 16}
Reject-P122 {ConvertTo-P122MachineCpuPercent 97 0}
Reject-P122 {ConvertTo-P122MachineCpuPercent 97 65}
# 기본 테스트는 WMI 조회를 하지 않는다. 실패 경로만 mock으로 검증한다.
function Get-CimInstance {throw 'mock provider unavailable'}
$missing=Get-P122ProcessCounterSnapshot 16
Assert-P122 (-not $missing.available -and $missing.processes.Count -eq 0)
Assert-P122 (-not $missing.windows_identical_to_native_guard -and -not $missing.causal_trigger_established)
function Get-CimInstance {
    [pscustomobject]@{Name='MsMpEng';IDProcess=123;PercentProcessorTime=[ulong]97;WorkingSetPrivate=1MB;IOReadBytesPersec=0;IOWriteBytesPersec=0}
    [pscustomobject]@{Name='python#2';IDProcess=124;PercentProcessorTime=[ulong]1600;WorkingSetPrivate=2MB;IOReadBytesPersec=100;IOWriteBytesPersec=0}
    [pscustomobject]@{Name='arbitrary_name_not_exported';IDProcess=125;PercentProcessorTime=[ulong]0;WorkingSetPrivate=0;IOReadBytesPersec=0;IOWriteBytesPersec=0}
}
$known=Get-P122ProcessCounterSnapshot 16
Assert-P122 ($known.available -and $known.processes.Count -eq 2)
Assert-P122 ($known.processes[0].role -eq 'defender' -and $known.processes[0].machine_cpu_percent -eq 6.0625)
Assert-P122 ($known.processes[1].role -eq 'python' -and $known.processes[1].machine_cpu_percent -eq 100)
function Get-CimInstance {1..65 | ForEach-Object {[pscustomobject]@{Name='System'}}}
$overflow=Get-P122ProcessCounterSnapshot 16
Assert-P122 (-not $overflow.available -and $overflow.processes.Count -eq 0)
Remove-Item Function:\Get-CimInstance
Initialize-P122NativeMetrics
Assert-P122 ([Runtime.InteropServices.Marshal]::SizeOf([P122.MemoryStatus]::new())-eq 64)
Write-Output 'PASS: P122 metrics/layout/conservative inputs and optional process-counter guards; native metric API and real WMI not called, no stored test execution'
