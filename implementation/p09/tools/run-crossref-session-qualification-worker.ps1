# Private worker entry for ONE session lifecycle candidate, never document IO or
# fixed-eight execution. Only a separately verified jobless host can create Native.
[CmdletBinding()]
param([switch]$QualifySessionOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$channel=$null;$state=$null;$observed=$null;$result=$null;$phase='closed_mode'
function Get-P09XrefSessionFailure($Failure) {
    $base=$Failure.Exception.GetBaseException();$code=$base.Message
    if ($code -cnotmatch '^P09_XREF_(BIND|ROT)_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_SESSION_WORKER_FAILED_NO_RAW_VALUES'}
    $kind=if ($base -is [Runtime.InteropServices.COMException]) {'COMException'}
        elseif ($base -is [InvalidOperationException]) {'InvalidOperationException'} else {'OtherException'}
    # Fixed kind and numeric HRESULT only; no arbitrary message, stack or path.
    return [ordered]@{state='session_worker_failed_or_uncertain';error_code=$code;
        error_kind=$kind;error_hresult=('0x{0:X8}' -f $base.HResult)}
}
function Get-SessionWorkerCleanup($Owner) {
    return [ordered]@{close_without_dirty_prompt_returned=($null -ne $Owner -and $Owner.trace.close_without_dirty_prompt_returned -eq $true);
        quit_invoked=($null -ne $Owner -and $Owner.trace.quit_invoked -eq $true);
        reference_release_returned=($null -ne $Owner -and $Owner.preassigned_release_returned -eq $true);
        remaining_owned_process_count=if ($null -eq $Owner -or $null -eq $Owner.trace.remaining_owned_process_count) {-1} else {[int]$Owner.trace.remaining_owned_process_count}}
}
try {
    if (-not $QualifySessionOnly) {throw 'P09_XREF_BIND_SESSION_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-dual-owner-identity',
        'crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-session-qualification-channel')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefFrozenWindowBridge
    Initialize-P09XrefHeldIdentityBridge;Import-P09XrefFrozenIoHelpers;Assert-P09XrefOriginalOwnerFunction
    $self=[P09CrossrefExisting.ExistingOwner]::InspectCurrentProcessOnly()
    $expected=Join-Path ([Environment]::GetFolderPath('Windows')) 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    Assert-P09XrefBinding ([string]::Equals($self.Image,$expected,[StringComparison]::OrdinalIgnoreCase)) 'SESSION_FIXED_WORKER_IMAGE'
    $item=Get-Item -LiteralPath $expected -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le 4194304 -and
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'SESSION_WORKER_IMAGE_BOUNDARY'
    $workerIdentity=[ordered]@{process_id=[int]$self.Pid;session_id=[int]$self.Session;
        created_at_utc=[datetime]::FromFileTimeUtc($self.Birth).ToString('o');executable_sha256=(Get-P09XrefFreshDigest ([IO.File]::ReadAllBytes($expected)))}
    $channel=New-P09XrefSessionQualificationChannel ([Console]::In) ([Console]::Out)
    $phase='host_ready';$d=Invoke-P09XrefSessionQualificationMessage $channel 'ready' -WorkerIdentity $workerIdentity
    $state=[ordered]@{case_index=1;owner=$null;current_descriptor=$d;preassigned_channel=$channel;
        trace=[ordered]@{sessions=[Collections.ArrayList]::new()}}
    $phase='exact_existing_owner';Connect-P09XrefPreassignedOwner $state 'save'
    $observed=Observe-P09XrefDualOwnedIdentity $state.owner
    $proxy=New-P09XrefPreassignedAdmissionProxy $state.owner $observed $state.current_descriptor
    $phase='host_exact_owner_admission';[void](Invoke-P09XrefSessionQualificationMessage $channel 'admit_owner' -Owner $proxy)
    $state.owner.preassigned_admitted=$true;$state.current_descriptor=$null
    # Qualification does NOT RegisterModule, make Visible, Open, Save, insert,
    # create an artifact directory, or consume a fixed-eight product attempt.
    $phase='verified_close';Close-P09XrefPreassignedOwner $state.owner
    $phase='host_kernel_close';[void](Invoke-P09XrefSessionQualificationMessage $channel 'closed' -Cleanup (Get-SessionWorkerCleanup $state.owner))
    $result=[ordered]@{state='session_worker_lifecycle_returned_source_and_native_qualification_pending';error_code=$null}
} catch {
    $result=Get-P09XrefSessionFailure $_
} finally {
    $owner=if ($null -eq $state) {$null} else {$state.owner}
    if ($null -ne $owner -and -not $owner.preassigned_close_attempted) {
        try {Close-P09XrefPreassignedOwner $owner} catch {}
    }
    if ($null -ne $channel -and -not $channel.finish_attempted) {
        try {[void](Invoke-P09XrefSessionQualificationMessage $channel 'failed' -ErrorCode 'P09_XREF_BIND_SESSION_WORKER_FAILED' -Cleanup (Get-SessionWorkerCleanup $owner))}
        catch {}
    }
}
$result['schema_version']='hwpx-agent.private.crossref-session-worker-result/v1'
$result['phase']=$phase;$result['COM_owner_observed']=($null -ne $observed)
$result['cleanup']=Get-SessionWorkerCleanup $(if ($null -eq $state) {$null} else {$state.owner})
$result['document_opened_or_saved']=$false;$result['fixed_eight_executed']=$false
$result['native_execution_authorized']=$false;$result['native_startup_qualified']=$false;$result['p09_complete']=$false
$result | ConvertTo-Json -Depth 5 -Compress
if ($result.state -cne 'session_worker_lifecycle_returned_source_and_native_qualification_pending') {exit 2}
