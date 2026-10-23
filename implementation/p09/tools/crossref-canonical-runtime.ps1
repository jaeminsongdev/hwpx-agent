# Function-only canonical route. A qualified, trusted session factory is required;
# no CLI, fallback COM creation, native authority, timeout or forced termination.
Set-StrictMode -Version Latest

function Get-P09XrefCanonicalEvidenceRelativePath([int]$CaseIndex,[string]$Kind) {
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8 -and $Kind -cin @('trace','sidecar')) 'CANONICAL_FIXED_EVIDENCE_PATH'
    $name=if ($Kind -ceq 'trace') {'target-trace.json'} else {'owner-identities.json'}
    return ('implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c'+
        $CaseIndex.ToString('00')+'-attempt01/'+$name)
}

function New-P09XrefCanonicalSidecar([int]$CaseIndex,$TracePin,$Evidence) {
    $path=Get-P09XrefCanonicalEvidenceRelativePath $CaseIndex 'trace'
    Assert-P09XrefBinding ($Evidence -is [Collections.Generic.List[object]] -and $Evidence.Count -le 2) 'CANONICAL_ADMISSION_PREFIX'
    if ($null -ne $TracePin) {
        Assert-P09XrefBinding ($TracePin -is [Collections.IDictionary] -and $TracePin.Count -eq 3 -and
            $TracePin.path -ceq $path -and ($TracePin.bytes -is [int] -or $TracePin.bytes -is [long]) -and
            $TracePin.bytes -gt 0 -and $TracePin.bytes -le 1048576 -and
            $TracePin.sha256 -is [string] -and $TracePin.sha256 -cmatch '^[0-9a-f]{64}$') 'CANONICAL_ORIGINAL_TRACE_PIN'
    }
    $admissions=[Collections.Generic.List[object]]::new()
    for ($i=0;$i -lt $Evidence.Count;$i++) {
        [void]$admissions.Add([ordered]@{session_label=(@('save','reopen')[$i]);evidence=$Evidence[$i]})
    }
    return [ordered]@{schema_version='hwpx-agent.private.crossref-owner-identity-sidecar/v1';
        case_id=('P09-XREF-BOOK-C'+$CaseIndex.ToString('00'));state='owner_identity_sidecar_unqualified';
        original_trace=$TracePin;admissions=$admissions;native_provenance_qualified=$false;
        native_execution_authorized=$false;p09_complete=$false}
}

function Write-P09XrefCanonicalSidecar($State,$Evidence) {
    Assert-P09XrefBinding (-not $State.canonical_sidecar_attempted) 'CANONICAL_NO_SIDECAR_RETRY'
    $State.canonical_sidecar_attempted=$true
    if (-not $State.slot_created) {return}
    $expected=Split-Path -Parent (Get-P09XrefCaseArtifactPath $State.case_index 'opened')
    Assert-P09XrefBinding ($State.run -ceq $expected) 'CANONICAL_FIXED_OUTPUT_DIRECTORY'
    $directory=Get-Item -LiteralPath $State.run -Force
    while ($null -ne $directory) {
        Assert-P09XrefBinding ($directory -is [IO.DirectoryInfo] -and
            ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'CANONICAL_OUTPUT_ANCESTOR'
        $directory=$directory.Parent
    }
    $source=Join-Path $State.run 'target-trace.json';$pin=$null
    if (Test-Path -LiteralPath $source) {
        $observed=Assert-P58File $source 1048576
        $pin=[ordered]@{path=(Get-P09XrefCanonicalEvidenceRelativePath $State.case_index 'trace');
            bytes=$observed.bytes;sha256=$observed.sha256}
    }
    $value=New-P09XrefCanonicalSidecar $State.case_index $pin $Evidence
    # Existing exact CreateNew/fsync helper; never rewrites the raw CIM trace.
    Write-P58Trace (Join-Path $State.run 'owner-identities.json') $value
    $State.canonical_sidecar_written=$true
}

function Invoke-P09XrefCanonicalCaseStep([string]$Step,$State,[scriptblock]$SessionFactory) {
    if ($Step -cnotin @('create_save_session','create_reopen_session')) {
        Invoke-P09XrefNativeCaseStep $Step $State;return
    }
    $steps=Get-P09XrefCaseFlowSteps
    Assert-P09XrefBinding (-not $State.failed -and $State.next_step_index -lt $steps.Count -and
        $Step -ceq $steps[$State.next_step_index]) 'CANONICAL_SESSION_ORDER_NO_RETRY'
    try {
        [void](& $State.host_checkpoint $Step $State)
        if ($Step -ceq 'create_reopen_session') {Assert-P09XrefNativeSessionsClean $State}
        Initialize-P09XrefFrozenWindowBridge
        $label=if ($Step -ceq 'create_save_session') {'save'} else {'reopen'}
        $before=$State.trace.sessions.Count
        # Trusted program factory, not data or an approval flag. It must preserve
        # original P58 compatibility/cleanup while creating an already-protected owner.
        $State.owner=& $SessionFactory $label $State.trace $State
        $State.close_attempted=$false
        Assert-P09XrefBinding ($null -ne $State.owner -and $State.trace.sessions.Count -eq ($before+1) -and
            $State.trace.sessions[$before].label -ceq $label -and $State.owner.verified -eq $true) 'CANONICAL_FACTORY_OWNER_REQUIRED'
        [void](& $State.admit_owned_process $State.owner $State)
        $State.next_step_index++
    } catch {$State.failed=$true;throw}
}

function Complete-P09XrefCanonicalCase($State,$Evidence,$Flow) {
    Assert-P09XrefBinding (-not $State.canonical_completion_attempted) 'CANONICAL_NO_COMPLETION_RETRY'
    $State.canonical_completion_attempted=$true
    $Flow.original_completion_error_code=$null;$Flow.canonical_sidecar_error_code=$null
    try {Complete-P09XrefNativeCasePorts $State} catch {
        $Flow.original_completion_error_code=Get-P09XrefBatchSafeCode $_.Exception.Message 'P09_XREF_BIND_CANONICAL_ORIGINAL_COMPLETION_FAILED'
    }
    try {Write-P09XrefCanonicalSidecar $State $Evidence} catch {
        $Flow.canonical_sidecar_error_code='P09_XREF_BIND_CANONICAL_SIDECAR_WRITE_FAILED'
    }
    if ($null -ne $Flow.original_completion_error_code -or $null -ne $Flow.canonical_sidecar_error_code) {
        throw 'P09_XREF_BIND_CANONICAL_COMPLETION_FAILED'
    }
}

function Invoke-P09XrefCanonicalHostBoundCase($Channel,[int]$CaseIndex,$ProbeLease,
    [Collections.IDictionary]$FlowRecord,[scriptblock]$SessionFactory) {
    Assert-P09XrefBinding ($null -ne $SessionFactory) 'CANONICAL_QUALIFIED_SESSION_FACTORY_REQUIRED'
    $evidence=[Collections.Generic.List[object]]::new();$state=$null;$status='failed'
    try {
        $state=New-P09XrefNativeCaseState $CaseIndex $ProbeLease `
            {param($step,$s) Invoke-P09XrefHostMessage $Channel $s.case_index 'checkpoint' -Step $step} `
            {param($owner,$s) Invoke-P09XrefCanonicalHostAdmission $Channel $s.case_index $owner $evidence}
        $state.canonical_sidecar_attempted=$false;$state.canonical_sidecar_written=$false
        $state.canonical_completion_attempted=$false
        Invoke-P09XrefCaseFlow $CaseIndex `
            {param($step,$s) Invoke-P09XrefCanonicalCaseStep $step $s $SessionFactory} `
            {param($s) Complete-P09XrefCanonicalCase $s $evidence $FlowRecord} $state $FlowRecord
        if ($null -eq $FlowRecord.error_code -and $null -eq $FlowRecord.cleanup_error_code -and $FlowRecord.steps.Count -eq 16) {
            $status='returned'
        }
    } catch {$FlowRecord.error_code='P09_XREF_BIND_CANONICAL_CASE_FAILED_NO_RAW_VALUES'}
    finally {
        $FlowRecord.host_finish_error_code=$null
        try {Invoke-P09XrefHostMessage $Channel $CaseIndex 'finish' -CaseStatus $status}
        catch {$FlowRecord.host_finish_error_code='P09_XREF_BIND_HOST_FINISH_FAILED'}
        $FlowRecord.canonical_admission_records=$evidence.Count
        $FlowRecord.canonical_sidecar_written=($null -ne $state -and $state.canonical_sidecar_written)
        $FlowRecord.native_execution_authorized=$false;$FlowRecord.p09_complete=$false;$FlowRecord.accepted_count_delta=0
    }
}

function Invoke-P09XrefCanonicalFixedHostBatch($Channel,$ProbeLease,[Collections.IDictionary]$Record,[scriptblock]$SessionFactory) {
    Assert-P09XrefBinding ($null -ne $SessionFactory -and $Channel.case_index -eq 1 -and $Channel.sequence -eq 0 -and
        -not $Channel.failed -and -not $Channel.finish_attempted) 'CANONICAL_FRESH_CHANNEL_AND_FACTORY'
    Assert-P09XrefBinding (-not $ProbeLease.closed -and $ProbeLease.stream -is [IO.FileStream] -and
        $ProbeLease.stream.CanRead -and -not $ProbeLease.stream.CanWrite -and
        $ProbeLease.binary_sha256 -ceq '0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb') 'CANONICAL_LIVE_FIXED_PROBE'
    $first=Get-P09XrefFixedSdkCase 1
    Assert-P09XrefBinding ($first.case_id -ceq 'P09-XREF-BOOK-C01') 'CANONICAL_FIXED_EIGHT_PACKET'
    for ($index=1;$index -le 8;$index++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'CANONICAL_ATTEMPT_ALREADY_EXISTS'
    }
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefCanonicalHostBoundCase $Channel $index $ProbeLease $flow $SessionFactory
    } $Record
}
