# Closed preparation ONLY: prewarm+fixed source lease+new controller, first denial.
# No parameter/response can enable Native; a positive first reply is rejected.
[CmdletBinding()]
param([switch]$InspectPreparationOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$lease=$null;$gate=$null;$result=$null;$phase='closed_mode'
try {
    if (-not $InspectPreparationOnly) {throw 'P09_XREF_BIND_PREASSIGNED_PREPARATION_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
        'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch',
        'crossref-dual-owner-identity','crossref-canonical-runtime','crossref-preassigned-host-channel',
        'crossref-preassigned-owner','crossref-preassigned-case-ports','crossref-preassigned-controller','crossref-preassigned-preparation-gate')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefPreassignedCasePorts
    Initialize-P09XrefFrozenWindowBridge;Initialize-P09XrefHeldIdentityBridge
    Assert-P09XrefOriginalOwnerFunction
    $phase='fixed_probe_lease';$lease=New-P09XrefProbeLease
    $gate=[P09PreassignedPreparationDenyReader]::new([Console]::In)
    $channel=New-P09XrefPreassignedHostChannel $gate ([Console]::Out)
    $states=[Collections.Generic.List[object]]::new();$batch=[ordered]@{}
    $phase='closed_successor_batch';Invoke-P09XrefPreassignedFixedHostBatch $channel $lease $batch $states
    Assert-P09XrefBinding ($gate.FirstReplyChecked -and $batch.planned_cases -eq 8 -and $batch.cases.Count -eq 1 -and
        $batch.completed_callback_cases -eq 0 -and $batch.stopped_case_index -eq 1 -and $batch.cases[0].phase -ceq 'prepare_slot' -and
        $batch.cases[0].callback_steps -eq 1 -and $null -eq $batch.cases[0].host_finish_error_code -and
        $channel.sequence -eq 2 -and $channel.finish_attempted -and $states.Count -eq 1 -and
        $null -eq $states[0].owner -and -not $states[0].slot_created -and -not $states[0].trace_written -and
        -not $states[0].canonical_sidecar_written -and $states[0].dual_identity_evidence.Count -eq 0) 'PREASSIGNED_PREPARATION_NO_SLOT_OWNER_OR_TRACE'
    for ($index=1;$index -le 8;$index++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'PREASSIGNED_PREPARATION_NATIVE_DIRECTORY_CREATED'
    }
    $result=[ordered]@{schema_version='hwpx-agent.private.crossref-preassigned-preparation/v1';
        state='closed_preassigned_worker_controller_prepared_not_native';planned_cases=8;callback_cases_entered=1;
        stopped_phase='prepare_slot';host_messages=2;retained_case_states=1;first_reply_checked=$gate.FirstReplyChecked;
        positive_reply_blocked=$gate.FirstReplyRejected;adapter_and_window_identity_prewarmed=$true;
        original_probe_lease_held=$true;native_directory_or_owner_or_trace_created=$false;
        actual_Hangul_ROT_or_COM=$false;native_execution_authorized=$false;native_startup_qualified=$false;p09_complete=$false}
} catch {
    $result=[ordered]@{schema_version='hwpx-agent.private.crossref-preassigned-preparation/v1';state='preassigned_preparation_failed';phase=$phase;
        source_line=$_.InvocationInfo.ScriptLineNumber;error_type=$_.Exception.GetType().Name;
        error_code=if ($_.Exception.GetBaseException().Message -cmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$_.Exception.GetBaseException().Message} else {'P09_XREF_BIND_PREASSIGNED_PREPARATION_FAILED_NO_RAW_VALUES'};
        actual_Hangul_ROT_or_COM=$false;native_execution_authorized=$false;native_startup_qualified=$false;p09_complete=$false}
} finally {
    if ($null -ne $lease) {Close-P09XrefProbeLease $lease}
    if ($null -ne $gate) {$gate.Dispose()}
}
$result['probe_lease_closed']=($null -eq $lease -or $lease.closed)
$result | ConvertTo-Json -Depth 5 -Compress
if ($result.state -cne 'closed_preassigned_worker_controller_prepared_not_native') {exit 2}
