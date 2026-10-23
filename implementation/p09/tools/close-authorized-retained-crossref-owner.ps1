# Explicit user-authorized normal Quit of the exact old retained instance. No discard/Save/activation/force kill.
[CmdletBinding()]
param([switch]$CloseExactRetained29824Only)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if(-not $CloseExactRetained29824Only -or [IntPtr]::Size -ne 4 -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA'){throw 'P09_XREF_ROT_CLOSE_CLOSED_MODE'}
$process=$null;$lease=$null;$documents=$null;$quit=$false;$released=$false;$count=$null;$phase='compile'
try{
    Add-Type -Path (Join-Path $PSScriptRoot 'crossref-existing-owner.cs')
    $phase='same_retained_process';$process=[Diagnostics.Process]::GetProcessById(29824)
    $birth=[long]134370336727726967
    if($process.HasExited -or $process.StartTime.ToFileTimeUtc() -ne $birth -or $process.SessionId -ne 1 -or
        -not [string]::Equals($process.MainModule.FileName,[P09CrossrefExisting.ExistingOwner]::Image,[StringComparison]::OrdinalIgnoreCase)){throw 'P09_XREF_ROT_CLOSE_EXACT_RETAINED_PROCESS_REQUIRED'}
    $phase='exact_existing_owner';$lease=[P09CrossrefExisting.ExistingOwner]::Attach([P09CrossrefExisting.ExpectedOwner]::new(29824,1,$birth))
    $phase='document_count_only';$documents=$lease.Application.XHwpDocuments;$count=[int]$documents.Count
    if($count -lt 0 -or $count -gt 1){throw 'P09_XREF_ROT_CLOSE_UNEXPECTED_DOCUMENT_COUNT'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($documents);$documents=$null
    # Do not call Close(false): an unexpected dirty document must not be silently discarded.
    $phase='normal_quit_once';$lease.Application.Quit();$quit=$true
}catch{
    $errorCode=[string]$_.Exception.GetBaseException().Message
    if($errorCode -cnotmatch '^P09_XREF_ROT_[A-Z_]{1,120}$'){$errorCode='P09_XREF_ROT_CLOSE_FAILURE_NO_RAW_VALUES'}
}finally{
    try{if($null -ne $documents){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($documents)}
        if($null -ne $lease){$lease.Dispose()};$released=$true}catch{$released=$false}
}
$exited=$false
try{if($null -ne $process){$exited=$process.WaitForExit(10000)}}finally{if($null -ne $process){$process.Dispose()}}
$ok=($quit -and $released -and $exited)
[ordered]@{schema_version='hwpx-agent.authorized-retained-owner-close/v1';
    state=$(if($ok){'CLOSED_AUTHORIZED_EXACT_RETAINED_OWNER_NOT_NATIVE_QUALIFICATION'}else{'UNCONFIRMED_AUTHORIZED_RETAINED_OWNER_CLOSE_NO_RETRY'});
    expected_process_id=29824;expected_birth_filetime_100ns='134370336727726967';phase=$phase;document_count=$count;
    normal_quit_returned=$quit;references_released=$released;same_held_process_exited=$exited;
    activation_invoked=$false;new_Hancom_started=$false;document_open_save_or_discard_invoked=$false;
    force_termination_invoked=$false;native_startup_qualified=$false} | ConvertTo-Json -Compress
if(-not $ok){exit 2}
