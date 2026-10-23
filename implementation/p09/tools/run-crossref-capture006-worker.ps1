# Private fixed006 target. Host qualification/release still required; no subset or retry mode.
[CmdletBinding()]
param([switch]$FixedEightAfterSession)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
try {
    if (-not $FixedEightAfterSession) {throw 'P09_XREF_BIND_CAPTURE_SIX_FIXED_MODE_REQUIRED'}
    . (Join-Path $PSScriptRoot 'crossref-capture006-worker-program.ps1')
    $projection=Get-P09XrefCapture006WorkerProgram
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_CAPTURE_SIX_WORKER_PREPARATION_FAILED_NO_RAW_VALUES'}
    [ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-result/v1';state='fixed_eight_worker_failed_or_uncertain';
        phase='closed_mode';error_code=$code;planned_cases=8;completed_callback_cases=0;retained_live_or_uncertain_owners=0;
        probe_lease_closed=$true;native_execution_authorized=$false;native_startup_qualified=$false;p09_complete=$false}|ConvertTo-Json -Compress
    exit 2
}
# Fixed script context/parameters retained. Original program owns result/EOF/cleanup.
. $projection.program -FixedEightAfterSession
