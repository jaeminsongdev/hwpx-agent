Set-StrictMode -Version Latest

function Get-P122CpuPercent {
    param([ulong]$IdleBefore,[ulong]$KernelBefore,[ulong]$UserBefore,
          [ulong]$IdleAfter,[ulong]$KernelAfter,[ulong]$UserAfter,[int]$LogicalProcessors)
    if ($LogicalProcessors -lt 1 -or $LogicalProcessors -gt 64) { throw 'unsupported_processor_group_scope' }
    if ($IdleAfter -lt $IdleBefore -or $KernelAfter -lt $KernelBefore -or $UserAfter -lt $UserBefore) { throw 'non_monotonic_system_times' }
    [decimal]$idle=[decimal]$IdleAfter-$IdleBefore
    [decimal]$total=([decimal]$KernelAfter-$KernelBefore)+([decimal]$UserAfter-$UserBefore)
    if ($total -le 0 -or $idle -gt $total) { throw 'invalid_system_time_delta' }
    # Kernel time에는 idle이 포함된다. 문서: Microsoft GetSystemTimes.
    return [math]::Round([double](100*(1-$idle/$total)),2)
}

function Get-P122MemoryMiB {
    param([ulong]$AvailableBytes,[ulong]$TotalBytes,[uint]$MemoryLoad)
    if ($TotalBytes -eq 0 -or $AvailableBytes -gt $TotalBytes -or $MemoryLoad -gt 100) { throw 'invalid_native_memory_sample' }
    return [ordered]@{available_ram_mib=[math]::Round($AvailableBytes/1MB,2);total_ram_mib=[math]::Round($TotalBytes/1MB,2);memory_load_percent=$MemoryLoad}
}

function Get-P122ConservativeInputs {
    param([double]$NativeCpu,[double]$CimCpu,[double]$NativeAvailableMiB,[double]$CimAvailableMiB)
    foreach($value in @($NativeCpu,$CimCpu,$NativeAvailableMiB,$CimAvailableMiB)) {
        if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0) { throw 'invalid_crosscheck_number' }
    }
    if ($NativeCpu -gt 100 -or $CimCpu -gt 100) { throw 'invalid_crosscheck_cpu' }
    # 어느 지표도 기존 안전 조건을 완화하지 않도록 더 보수적인 값만 비교한다.
    return [ordered]@{system_cpu_percent=[math]::Max($NativeCpu,$CimCpu);available_ram_mib=[math]::Min($NativeAvailableMiB,$CimAvailableMiB)}
}

function Initialize-P122NativeMetrics {
    if ($null -ne ('P122.NativeMetrics' -as [type])) { return }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace P122 {
    [StructLayout(LayoutKind.Sequential)] public struct MemoryStatus {
        public uint Length, MemoryLoad;
        public ulong TotalPhys, AvailablePhys, TotalPageFile, AvailablePageFile;
        public ulong TotalVirtual, AvailableVirtual, AvailableExtendedVirtual;
    }
    public static class NativeMetrics {
        [DllImport("kernel32.dll", SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GetSystemTimes(out ulong idle, out ulong kernel, out ulong user);
        [DllImport("kernel32.dll", SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    }
}
'@
    if ([Runtime.InteropServices.Marshal]::SizeOf([P122.MemoryStatus]::new()) -ne 64) { throw 'native_memory_layout_drift' }
}
