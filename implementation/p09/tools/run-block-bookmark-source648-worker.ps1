# Private fixed worker. No COM activation or fallback launch; host owns startups.
[CmdletBinding()]
param([switch]$BlockSourceAfterCurrentSession)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
$phase='closed_mode';$errorCode=$null;$completed=0;$state=$null;$caseFailure=$null
try {
    if (-not $BlockSourceAfterCurrentSession) {throw 'P09_XREF_BIND_BLOCK648_FIXED_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-dual-owner-identity',
        'crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-save-reopen',
        'crossref-capture008-application-binding','prepared-bookmark631-ports','block-bookmark-source645-ports',
        'block-bookmark-source646-document','block-bookmark-source648-channel','block-bookmark-source648-flow')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefFrozenWindowBridge
    Initialize-P09XrefHeldIdentityBridge;Import-P09XrefFrozenIoHelpers;Assert-P09XrefOriginalOwnerFunction
    Initialize-P09XrefCapture008ApplicationBinding
    $self=[P09CrossrefExisting.ExistingOwner]::InspectCurrentProcessOnly()
    $expected=Join-Path ([Environment]::GetFolderPath('Windows')) 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    Assert-P09XrefBinding ([string]::Equals($self.Image,$expected,[StringComparison]::OrdinalIgnoreCase)) 'BLOCK648_WORKER_IMAGE'
    $identity=[ordered]@{process_id=[int]$self.Pid;session_id=[int]$self.Session;created_at_utc=[datetime]::FromFileTimeUtc($self.Birth).ToString('o');
        executable_sha256=(Get-P09XrefFreshDigest ([IO.File]::ReadAllBytes($expected)))}
    [Console]::WriteLine(([ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-ready/v1';worker_identity=$identity}|ConvertTo-Json -Depth 5 -Compress));[Console]::Out.Flush()
    $channel=New-P09XrefPreassignedHostChannel ([Console]::In) ([Console]::Out)
    $phase='current_live_release';$raw=Read-P09XrefBoundedHostReply $channel
    $release=[ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-release/v1';acknowledged=$true;
        error_code=$null;native_execution_authorized=$false;p09_complete=$false}
    Assert-P09XrefBinding ($raw -ceq ($release|ConvertTo-Json -Compress)) 'BLOCK648_CURRENT_RELEASE_REQUIRED'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $trace=[ordered]@{schema_version='hwpx-agent.private.block-bookmark-source648-trace/v1';case_index=1;
        state='source_capture_started_semantics_unqualified';phase=$null;error_code=$null;cleanup_error=$null;
        sessions=[Collections.ArrayList]::new();dual_identity_evidence=[Collections.Generic.List[object]]::new();
        artifacts=[ordered]@{};block_ranges=[Collections.Generic.List[object]]::new();
        source_identity_preserved=$false;input_leases_closed=$false;block_content_support_qualified=$false;P09_complete=$false}
    $state=[ordered]@{case_index=1;preassigned_channel=$channel;current_descriptor=$null;owner=$null;document=$null;
        close_attempted=$false;failed=$false;cursor=0;slot_created=$false;trace=$trace;
        run=(Join-Path $root 'implementation/p09/evidence/private/p09-361-block-bookmark643-source-document001');
        leases=[Collections.Generic.List[object]]::new();dual_identity_evidence=$trace.dual_identity_evidence;
        previous_identity=$null;created=$null;reopened=$null;seed_attempted=$false;seeded=$false;ranges_attempted=$false;
        completed_ranges=0;range_trace=$trace.block_ranges;cleanup_error_code=$null;checkpoint={param($Phase,$Index)
            [void](Invoke-P09Block648Message $script:P09Block648State.preassigned_channel pulse -Phase $Phase -RangeIndex $Index)
            return $true
        }}
    $script:P09Block648State=$state;$phase='fixed_source'
    try {foreach ($step in (Get-P09Block648Steps)) {Invoke-P09Block648Step $state $step}}
    catch {$trace.error_code=Get-P09Block648SafeCode $_;$state.failed=$true}
    finally {
        try {Complete-P09Prepared631Case $state}
        catch {$trace.cleanup_error=Get-P09Block648SafeCode $_;$state.failed=$true}
    }
    $status=if ($state.failed) {'failed'}else{'returned'}
    if ($state.failed) {
        $errorCode=$trace.error_code;if ($null -eq $errorCode) {$errorCode=$trace.cleanup_error}
        $caseFailure=[ordered]@{case_index=1;phase=$trace.phase;error_code=$errorCode}
    }
    [void](Invoke-P09Block648Message $channel finish -CaseStatus $status)
    if (-not $state.failed) {$completed=1}
} catch {
    if ($null -eq $errorCode) {
        $errorCode=$_.Exception.GetBaseException().Message
        if ($errorCode -cnotmatch '^P09_XREF_(BIND|ROT)_[A-Z0-9_]{1,120}$') {$errorCode='P09_XREF_BIND_BLOCK648_WORKER_FAILED_NO_RAW_VALUES'}
    }
}
$retained=if ($null -ne $state -and $null -ne $state.owner -and -not $state.owner.preassigned_closed) {1}else{0}
$returned=($completed -eq 1 -and $null -eq $errorCode -and $retained -eq 0)
$stateName=if ($returned) {'block_source_callbacks_returned_semantics_unqualified'}else{'block_source_callbacks_failed_or_partial'}
[ordered]@{schema_version='hwpx-agent.private.block-bookmark-source648-result/v1';state=$stateName;phase=$phase;error_code=$errorCode;
    case_failure=$caseFailure;planned_cases=1;planned_block_ranges=8;completed_callback_cases=$completed;
    retained_live_or_uncertain_owners=$retained;block_content_support_qualified=$false;
    native_execution_authorized=$false;native_startup_qualified=$false;P09_complete=$false}|ConvertTo-Json -Depth 5 -Compress
if ($retained -gt 0) {
    [void][Console]::In.Read() # EOF only after the SAME exact owned Native exit.
    foreach ($lease in $state.leases) {$lease.Dispose()};$state.leases.Clear()
}
if (-not $returned) {exit 2}
