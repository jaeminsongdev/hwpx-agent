param([switch]$ReadOnlyOwnedCrossrefExclusion)
$ErrorActionPreference='Stop'
try {
    if (-not $ReadOnlyOwnedCrossrefExclusion) { throw 'CLOSED_MODE' }
    $own585=[Diagnostics.Process]::GetCurrentProcess()
    try { $own585.ProcessorAffinity=[IntPtr]4; $own585.PriorityClass=[Diagnostics.ProcessPriorityClass]::BelowNormal }
    finally { $own585.Dispose() }
    $pattern585='(?i)[\\/]hwpx-agent[\\/](?:tools[\\/]p09|implementation[\\/]p09[\\/]tools)[\\/][^\s"]*crossref[^\s"]*\.(?:py|ps1)(?=["\s]|$)'
    $native585=0; $hosts585=0
    foreach ($process585 in @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'powershell.exe' OR Name = 'pwsh.exe' OR Name = 'Hwp.exe' OR Name = 'HwpTray.exe'")) {
        if ($process585.ProcessId -eq $PID) { continue }
        if ($process585.Name -ieq 'Hwp.exe' -or $process585.Name -ieq 'HwpTray.exe') { $native585++; continue }
        if ($process585.CommandLine -match $pattern585) { $hosts585++ }
    }
    @{state='OBSERVED_READONLY_CROSSREF_SQL_EXCLUSION';native_processes=$native585;crossref_hosts=$hosts585;process_created_or_stopped=$false;COM_activated=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    @{state='FAILED_READONLY_CROSSREF_SQL_EXCLUSION';error_code='SQL585_READONLY_HOST_QUERY_FAILED';process_created_or_stopped=$false;COM_activated=$false} | ConvertTo-Json -Compress
    exit 2
}
