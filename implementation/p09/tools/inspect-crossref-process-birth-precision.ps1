# Read this inspection process only. No Hwp/COM activation, documents or writes.
[CmdletBinding()]
param([switch]$InspectOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $InspectOnly) {throw 'P09_XREF_PRECISION_INSPECT_ONLY'}
try {
    $process=[Diagnostics.Process]::GetCurrentProcess()
    try {
        $before=$process.StartTime.ToUniversalTime().ToFileTimeUtc()
        $rows=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$process.Id))
        if ($rows.Count -ne 1 -or [int]$rows[0].ProcessId -ne $process.Id -or
            [int]$rows[0].SessionId -ne $process.SessionId -or $null -eq $rows[0].CreationDate) {
            throw 'P09_XREF_PRECISION_OWN_PROCESS_ONLY'
        }
        $cim=([datetime]$rows[0].CreationDate).ToUniversalTime().ToFileTimeUtc()
        $after=$process.StartTime.ToUniversalTime().ToFileTimeUtc()
        if ($before -ne $after -or $process.HasExited) {throw 'P09_XREF_PRECISION_SAME_LIVE_PROCESS_REQUIRED'}
        [ordered]@{schema_version='hwpx-agent.private.crossref-own-process-birth-precision/v1';
            state='same_live_inspection_process_birth_precision_observed_not_hancom';
            process_id=$process.Id;process_session=$process.SessionId;
            native_creation_100ns=[string]$before;cim_creation_100ns=[string]$cim;
            native_minus_cim_100ns=[long]($before-$cim);
            native_tail_mod10=[int]($before%10);cim_tail_mod10=[int]($cim%10);
            exact_equal=($before -eq $cim);native_creation_before_after_equal=$true;
            process_queries=1;actual_Hangul_or_COM=$false;native_execution_authorized=$false;
            hancom_timestamp_precision_qualified=$false;p09_complete=$false} | ConvertTo-Json -Compress
    } finally {$process.Dispose()}
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_PRECISION_[A-Z_]+$') {$_.Exception.Message}
        else {'P09_XREF_PRECISION_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='own_process_precision_inspection_failed';error_code=$code;actual_Hangul_or_COM=$false;
        native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
