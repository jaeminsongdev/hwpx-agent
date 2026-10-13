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
Initialize-P122NativeMetrics
Assert-P122 ([Runtime.InteropServices.Marshal]::SizeOf([P122.MemoryStatus]::new())-eq 64)
Write-Output 'PASS: P122 metrics/layout/conservative inputs 16 assertions; native metric API not called, no stored test execution'
