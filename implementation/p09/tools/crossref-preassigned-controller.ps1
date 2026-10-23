# Function-only fixed-eight successor. Trusted program code only, no Native CLI.
# RetainedStates keeps uncertain owners reachable; never serialize those RCWs.
Set-StrictMode -Version Latest

function Complete-P09XrefPreassignedCanonicalCase($State,$Flow) {
    Assert-P09XrefBinding (-not $State.canonical_completion_attempted) 'PREASSIGNED_CONTROLLER_NO_COMPLETION_RETRY'
    $State.canonical_completion_attempted=$true
    $Flow.original_completion_error_code=$null;$Flow.canonical_sidecar_error_code=$null
    try {Complete-P09XrefPreassignedCasePorts $State} catch {
        $Flow.original_completion_error_code=Get-P09XrefBatchSafeCode $_.Exception.Message 'P09_XREF_BIND_PREASSIGNED_CONTROLLER_COMPLETION_FAILED'
    }
    try {Write-P09XrefCanonicalSidecar $State $State.dual_identity_evidence} catch {
        $Flow.canonical_sidecar_error_code='P09_XREF_BIND_CANONICAL_SIDECAR_WRITE_FAILED'
    }
    if ($null -ne $Flow.original_completion_error_code -or $null -ne $Flow.canonical_sidecar_error_code) {
        throw 'P09_XREF_BIND_PREASSIGNED_CANONICAL_COMPLETION_FAILED'
    }
}

function Invoke-P09XrefPreassignedHostBoundCase($Channel,[int]$CaseIndex,$ProbeLease,
    [Collections.IDictionary]$FlowRecord,[Collections.Generic.List[object]]$RetainedStates) {
    $state=$null;$status='failed'
    try {
        Assert-P09XrefBinding ($RetainedStates.Count -eq ($CaseIndex-1) -and $CaseIndex -ge 1 -and $CaseIndex -le 8) 'PREASSIGNED_CONTROLLER_STATE_ORDER'
        $state=New-P09XrefPreassignedCaseState $CaseIndex $ProbeLease $Channel
        [void]$RetainedStates.Add($state)
        $state['canonical_sidecar_attempted']=$false;$state['canonical_sidecar_written']=$false
        $state['canonical_completion_attempted']=$false
        Invoke-P09XrefCaseFlow $CaseIndex `
            {param($step,$s) Invoke-P09XrefPreassignedCaseStep $step $s} `
            {param($s) Complete-P09XrefPreassignedCanonicalCase $s $FlowRecord} $state $FlowRecord
        if ($null -eq $FlowRecord.error_code -and $null -eq $FlowRecord.cleanup_error_code -and $FlowRecord.steps.Count -eq 16) {$status='returned'}
    } catch {$FlowRecord.error_code='P09_XREF_BIND_PREASSIGNED_CONTROLLER_CASE_FAILED_NO_RAW_VALUES'}
    finally {
        $FlowRecord.host_finish_error_code=$null
        try {[void](Invoke-P09XrefPreassignedHostMessage $Channel $CaseIndex 'finish' -CaseStatus $status)}
        catch {$FlowRecord.host_finish_error_code='P09_XREF_BIND_HOST_FINISH_FAILED'}
        $FlowRecord.canonical_admission_records=if ($null -eq $state) {0} else {$state.dual_identity_evidence.Count}
        $FlowRecord.canonical_sidecar_written=($null -ne $state -and $state.canonical_sidecar_written)
        $FlowRecord.native_execution_authorized=$false;$FlowRecord.p09_complete=$false;$FlowRecord.accepted_count_delta=0
    }
}

function Invoke-P09XrefPreassignedFixedHostBatch($Channel,$ProbeLease,[Collections.IDictionary]$Record,
    [Collections.Generic.List[object]]$RetainedStates) {
    Assert-P09XrefExistingOwnerAdapterReady
    Assert-P09XrefBinding ($RetainedStates.Count -eq 0 -and $Channel.case_index -eq 1 -and $Channel.sequence -eq 0 -and
        -not $Channel.failed -and -not $Channel.finish_attempted -and $null -eq $Channel.pending_descriptor) 'PREASSIGNED_CONTROLLER_FRESH_BATCH'
    Assert-P09XrefBinding (-not $ProbeLease.closed -and $ProbeLease.stream -is [IO.FileStream] -and
        $ProbeLease.stream.CanRead -and -not $ProbeLease.stream.CanWrite -and
        $ProbeLease.binary_sha256 -ceq '0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb') 'PREASSIGNED_CONTROLLER_LIVE_FIXED_PROBE'
    $first=Get-P09XrefFixedSdkCase 1
    Assert-P09XrefBinding ($first.case_id -ceq 'P09-XREF-BOOK-C01') 'PREASSIGNED_CONTROLLER_FIXED_EIGHT_PACKET'
    for ($index=1;$index -le 8;$index++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'PREASSIGNED_CONTROLLER_ATTEMPT_ALREADY_EXISTS'
    }
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefPreassignedHostBoundCase $Channel $index $ProbeLease $flow $RetainedStates
    } $Record
}
