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

function ConvertTo-P122MachineCpuPercent {
    param([object]$Counter,[object]$LogicalProcessors)
    $numberTypes=@([byte],[uint16],[int16],[int],[uint32],[long],[ulong],[single],[double],[decimal])
    if ($null -eq $Counter -or $Counter.GetType() -notin $numberTypes -or
        $LogicalProcessors -isnot [int] -or $LogicalProcessors -lt 1 -or $LogicalProcessors -gt 64) {
        throw 'invalid_process_counter_type_or_processor_count'
    }
    $value=[double]$Counter
    if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or
        $value -lt 0 -or $value -gt 100*$LogicalProcessors) { throw 'invalid_process_counter_range' }
    # Process 계수는 모든 thread의 시간을 합산한다. 시스템 전체 백분율과 구분한다.
    return [math]::Round($value/$LogicalProcessors,4)
}

function Get-P122ProcessCounterSnapshot {
    param([int]$LogicalProcessors)
    $started=[datetime]::UtcNow
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $result=[ordered]@{available=$false;reason='CIM_PROCESS_COUNTER_UNAVAILABLE';processes=@();
        started_utc=$started.ToString('o');elapsed_seconds=0;provider='Win32_PerfFormattedData_PerfProc_Process';
        logical_processors=$LogicalProcessors;windows_identical_to_native_guard=$false;
        process_creation_identity_bound=$false;causal_trigger_established=$false;hard_preemption_guaranteed=$false}
    try {
        $filter="Name='MsMpEng' OR Name='System' OR Name LIKE 'ChatGPT%' OR Name LIKE 'codex%' OR Name LIKE 'python%' OR Name LIKE 'git%' OR Name LIKE 'Vmmem%' OR Name LIKE 'WmiPrvSE%'"
        $rows=@(Get-CimInstance Win32_PerfFormattedData_PerfProc_Process -Filter $filter -OperationTimeoutSec 2 -ErrorAction Stop)
        if ($rows.Count -lt 1 -or $rows.Count -gt 64) { throw 'bounded_process_counter_count' }
        $roles=@{msmpeng='defender';system='system';chatgpt='codex';codex='codex';python='python';git='git';vmmem='wsl';vmmemwsl='wsl';wmiprvse='wmi'}
        $selected=@()
        foreach($row in $rows) {
            # 역할과 PID만 보존한다. 임의 이름, 경로, command line은 수집하지 않는다.
            if ($row.Name -notmatch '^(MsMpEng|System|ChatGPT|codex|python|git|VmmemWSL|Vmmem|WmiPrvSE)(#[0-9]+)?$') { continue }
            $base=($row.Name -replace '#[0-9]+$','').ToLowerInvariant()
            $selected+=[ordered]@{role=$roles[$base];pid=[uint32]$row.IDProcess;
                process_counter_percent=[double]$row.PercentProcessorTime;
                machine_cpu_percent=ConvertTo-P122MachineCpuPercent $row.PercentProcessorTime $LogicalProcessors;
                private_working_set_bytes=[ulong]$row.WorkingSetPrivate;
                io_read_bytes_per_second=[ulong]$row.IOReadBytesPersec;io_write_bytes_per_second=[ulong]$row.IOWriteBytesPersec}
        }
        $result.available=$true;$result.reason=$null;$result.processes=$selected
    } catch {
        # 예외 메시지/원문을 출력하지 않고 조회 불가를 0%와 구분한다.
        $result.available=$false;$result.processes=@()
    } finally {$watch.Stop();$result.elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,4)}
    return $result
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
