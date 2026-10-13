# P310: 독립 진단용 한 번의 읽기 전용 PerfProc snapshot. 기존 runtime guard를 바꾸지 않는다.
function Read-HwpxProcessCpuCounterSnapshot {
    [CmdletBinding()]
    param()
    $taskStarted=[DateTime]::UtcNow.ToString('o')
    $taskRows=[Collections.Generic.List[object]]::new()
    $taskProperties=@('Name','IDProcess','CreatingProcessID','ElapsedTime','PercentProcessorTime',
        'Timestamp_Sys100NS','Frequency_Sys100NS','PrivateBytes','WorkingSet')
    Get-CimInstance -ClassName Win32_PerfRawData_PerfProc_Process -Property $taskProperties -OperationTimeoutSec 5 -ErrorAction Stop |
        ForEach-Object {
            if($taskRows.Count -ge 4096){throw 'PERFPROC_ROW_BUDGET'}
            if([string]::IsNullOrEmpty($_.Name) -or $_.Name.Length -gt 128 -or $_.Name -match '[\\/:\r\n\t]'){
                throw 'PERFPROC_INSTANCE_NOT_PATH'
            }
            # uint64은 JS/JSON 부동소수점 왕복 손실을 피하기 위해 원 십진 문자열로 보존.
            $taskRows.Add([pscustomobject]@{
                pid=[int64]$_.IDProcess
                name=[string]$_.Name
                creating_pid=[int64]$_.CreatingProcessID
                raw_elapsed_token=([uint64]$_.ElapsedTime).ToString([Globalization.CultureInfo]::InvariantCulture)
                cpu_100ns=([uint64]$_.PercentProcessorTime).ToString([Globalization.CultureInfo]::InvariantCulture)
                sys_100ns=([uint64]$_.Timestamp_Sys100NS).ToString([Globalization.CultureInfo]::InvariantCulture)
                frequency_sys100ns=([uint64]$_.Frequency_Sys100NS).ToString([Globalization.CultureInfo]::InvariantCulture)
                private_bytes=([uint64]$_.PrivateBytes).ToString([Globalization.CultureInfo]::InvariantCulture)
                working_set_bytes=([uint64]$_.WorkingSet).ToString([Globalization.CultureInfo]::InvariantCulture)
            })
        }
    $taskSnapshot=[pscustomobject]@{
        schema_version='hwpx-agent.p09-perfproc-raw-snapshot/v1'
        counter_class='Win32_PerfRawData_PerfProc_Process'
        query_started_utc=$taskStarted
        query_finished_utc=[DateTime]::UtcNow.ToString('o')
        operation_timeout_seconds=5
        rows=$taskRows.ToArray()
    }
    if([Text.Encoding]::UTF8.GetByteCount(($taskSnapshot | ConvertTo-Json -Depth 4 -Compress)) -gt 4194304){
        throw 'PERFPROC_BYTE_BUDGET'
    }
    return $taskSnapshot
}
