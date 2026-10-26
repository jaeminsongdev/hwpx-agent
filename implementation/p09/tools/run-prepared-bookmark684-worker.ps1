# Fixed new prepared-eight worker. Never launches COM or performs SDK insertion.
[CmdletBinding()]
param([switch]$PreparedBlockEightAfterCurrentSession)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
$states=[Collections.Generic.List[object]]::new();$phase='closed_mode';$errorCode=$null;$completed=0;$caseFailure=$null
try {
    if (-not $PreparedBlockEightAfterCurrentSession) {throw 'P09_XREF_BIND_PREPARED_FIXED_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-dual-owner-identity',
        'crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-save-reopen',
        'crossref-capture008-application-binding','prepared-bookmark684-channel','prepared-bookmark684-ports')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefFrozenWindowBridge
    Initialize-P09XrefHeldIdentityBridge;Import-P09XrefFrozenIoHelpers;Assert-P09XrefOriginalOwnerFunction
    Initialize-P09XrefCapture008ApplicationBinding;Initialize-P09Prepared684Channel
    $self=[P09CrossrefExisting.ExistingOwner]::InspectCurrentProcessOnly()
    $expected=Join-Path ([Environment]::GetFolderPath('Windows')) 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    Assert-P09XrefBinding ([string]::Equals($self.Image,$expected,[StringComparison]::OrdinalIgnoreCase)) 'PREPARED_FIXED_WORKER_IMAGE'
    $identity=[ordered]@{process_id=[int]$self.Pid;session_id=[int]$self.Session;created_at_utc=[datetime]::FromFileTimeUtc($self.Birth).ToString('o');
        executable_sha256=(Get-P09XrefFreshDigest ([IO.File]::ReadAllBytes($expected)))}
    $ready=[ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-ready/v1';worker_identity=$identity}
    [Console]::WriteLine(($ready|ConvertTo-Json -Depth 5 -Compress));[Console]::Out.Flush()
    $channel=New-P09XrefPreassignedHostChannel ([Console]::In) ([Console]::Out)
    $phase='current_live_release';$raw=Read-P09XrefBoundedHostReply $channel;$reply=$raw|ConvertFrom-Json
    $canonical=[ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-release/v1';acknowledged=$true;
        error_code=$null;native_execution_authorized=$false;p09_complete=$false}
    Assert-P09XrefBinding ($raw -ceq ($canonical|ConvertTo-Json -Compress)) 'PREPARED_CURRENT_LIVE_RELEASE_REQUIRED'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $manifestPath=Join-Path $root 'implementation/p09/evidence/p09-361-block-bookmark681-prepared-batch.v1.json'
    $manifestBytes=[IO.File]::ReadAllBytes($manifestPath)
    Assert-P09XrefBinding ($manifestBytes.Length -gt 0 -and $manifestBytes.Length -le 16384) 'PREPARED_MANIFEST_LIMIT'
    Assert-P09XrefBinding ((Get-P09XrefFreshDigest $manifestBytes) -ceq 'bec2b5d3a244c5e7975a5b1c904d8f5ea631bf9e3679f57ea70fac474500fb13') 'PREPARED_EXACT_681_MANIFEST'
    $manifest=[Text.UTF8Encoding]::new($false,$true).GetString($manifestBytes)|ConvertFrom-Json
    Assert-P09XrefBinding ($manifest.cases.Count -eq 8) 'PREPARED_WHOLE_EIGHT'
    $phase='fixed_eight'
    foreach ($case in @($manifest.cases)) {
        $index=$completed+1;$sourceIndex=$index
        Assert-P09XrefBinding ($case.case_index -is [int] -and $case.case_index -eq $sourceIndex -and
            $case.output.path -ceq ('implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001/case-'+$sourceIndex.ToString('00')+'.hwpx') -and
            $case.output.sha256 -cmatch '^[0-9a-f]{64}$') 'PREPARED_FIXED_CANDIDATE'
        $trace=[ordered]@{schema_version='hwpx-agent.private.prepared-bookmark684-trace/v1';case_index=$index;source_case_index=$sourceIndex;
            state='capture_started_semantics_unqualified';phase=$null;error_code=$null;cleanup_error=$null;
            sessions=[Collections.ArrayList]::new();dual_identity_evidence=[Collections.Generic.List[object]]::new();
            artifacts=[ordered]@{};source_identity_preserved=$false;input_leases_closed=$false;initial_open_observed=$false;
            initial_calculated_result_qualified=$false;hyperlink_navigation_qualified=$false;PDF_render_diff_qualified=$false;
            SDK_insertion_invoked=$false;native_execution_authorized=$false;P09_complete=$false}
        $state=[ordered]@{case_index=$index;preassigned_channel=$channel;current_descriptor=$null;
            owner=$null;document=$null;close_attempted=$false;failed=$false;cursor=0;slot_created=$false;trace=$trace;
            run=(Join-Path $root ('implementation/p09/evidence/private/p09-361-prepared-bookmark684-native001-c'+$sourceIndex.ToString('00')));
            candidate=(Join-Path $root $case.output.path);candidate_sha=$case.output.sha256;
            original=(Join-Path $root 'implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001/source.hwpx');
            leases=[Collections.Generic.List[object]]::new();dual_identity_evidence=$trace.dual_identity_evidence;
            previous_identity=$null;initial=$null;saved=$null;reopened=$null}
        [void]$states.Add($state)
        try {foreach ($step in (Get-P09Prepared684Steps)) {Invoke-P09Prepared684Step $state $step}}
        catch {$trace.error_code=Get-P09Prepared684SafeCode $_;$state.failed=$true}
        finally {
            try {Complete-P09Prepared684Case $state}
            catch {$trace.cleanup_error=Get-P09Prepared684SafeCode $_;$state.failed=$true}
        }
        $status=if ($state.failed) {'failed'} else {'returned'}
        if ($state.failed) {
            $errorCode=$trace.error_code
            if ($null -eq $errorCode) {$errorCode=$trace.cleanup_error}
            $caseFailure=[ordered]@{case_index=$index;phase=$trace.phase;error_code=$errorCode}
        }
        # Preserve the primary failure BEFORE a failed finish/owner retirement
        # acknowledgement can throw. Never hide it behind a generic host denial.
        [void](Invoke-P09XrefPreassignedHostMessage $channel $index finish -CaseStatus $status)
        if ($state.failed) {break}
        $completed++
    }
} catch {
    if ($null -eq $errorCode) {
        $errorCode=$_.Exception.GetBaseException().Message
        if ($errorCode -cnotmatch '^P09_XREF_(BIND|ROT)_[A-Z0-9_]{1,120}$') {$errorCode='P09_XREF_BIND_PREPARED_WORKER_FAILED_NO_RAW_VALUES'}
    }
}
$retained=@($states|Where-Object {$null -ne $_.owner -and -not $_.owner.preassigned_closed}).Count
$stateName=if ($completed -eq 8 -and $null -eq $errorCode -and $retained -eq 0) {'block_eight_callbacks_returned_semantics_unqualified'} else {'block_eight_callbacks_failed_or_partial'}
[ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-result/v1';state=$stateName;phase=$phase;error_code=$errorCode;
    case_failure=$caseFailure;planned_cases=8;completed_callback_cases=$completed;retained_live_or_uncertain_owners=$retained;
    SDK_insertion_invoked=$false;native_execution_authorized=$false;native_startup_qualified=$false;p09_complete=$false}|ConvertTo-Json -Depth 5 -Compress
if ($retained -gt 0) {
    [void][Console]::In.Read() # Parent sends EOF only after the SAME exact Native exit.
    foreach ($state in $states) {foreach ($lease in $state.leases) {$lease.Dispose()};$state.leases.Clear()}
}
if ($stateName -cne 'block_eight_callbacks_returned_semantics_unqualified') {exit 2}

