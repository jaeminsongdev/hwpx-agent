# Function-only fixed eight-case controller. No native CLI, subset or retry route.
# Callback return is never native execution, cleanup, semantics or acceptance evidence.
Set-StrictMode -Version Latest

function Get-P09XrefBatchSafeCode($Value,[string]$Fallback) {
    if ($Value -is [string] -and $Value -cmatch '^(P09_XREF_|P58_|STOP_|XREF_HOST_)[A-Z_]{1,120}$') {return $Value}
    return $Fallback
}

function Get-P09XrefBatchFailureSummary($Record) {
    # A closed diagnostic projection only; never source/SDK values, RCWs or an execution permit.
    if ($null -eq $Record.stopped_case_index) {return $null}
    $index=$Record.stopped_case_index
    Assert-P09XrefBinding ($index -is [int] -and $index -ge 1 -and $index -le 8 -and
        $Record.cases.Count -eq $index) 'BATCH_DIAGNOSTIC_CASE_PREFIX'
    $case=$Record.cases[$index-1]
    $phase=if ($case.Contains('phase') -and $case.phase -is [string] -and $case.phase -cin (Get-P09XrefCaseFlowSteps)) {
        $case.phase
    } else {'unknown_callback_phase'}
    $entered=if ($case.Contains('callback_steps') -and $case.callback_steps -is [int] -and $case.callback_steps -ge 0 -and $case.callback_steps -le 16) {$case.callback_steps} else {0}
    $returned=if ($case.Contains('callback_steps_returned') -and $case.callback_steps_returned -is [int] -and
        $case.callback_steps_returned -ge 0 -and $case.callback_steps_returned -le $entered) {$case.callback_steps_returned} else {0}
    $original=if ($case.Contains('original_error_code')) {$case.original_error_code} else {$case.error_code}
    return [ordered]@{case_index=$index;phase=$phase;callback_steps=$entered;callback_steps_returned=$returned;
        error_code=(Get-P09XrefBatchSafeCode $original 'P09_XREF_BIND_BATCH_CASE_FAILED_NO_RAW_VALUES');
        cleanup_error_code=if ($case.Contains('cleanup_error_code') -and $null -ne $case.cleanup_error_code) {
            Get-P09XrefBatchSafeCode $case.cleanup_error_code 'P09_XREF_BIND_BATCH_CLEANUP_FAILED_NO_RAW_VALUES'
        } elseif ($case.Contains('original_cleanup_error_code') -and $null -ne $case.original_cleanup_error_code) {
            Get-P09XrefBatchSafeCode $case.original_cleanup_error_code 'P09_XREF_BIND_BATCH_CLEANUP_FAILED_NO_RAW_VALUES'
        } else {$null};
        host_finish_error_code=if ($case.Contains('host_finish_error_code') -and $null -ne $case.host_finish_error_code) {
            'P09_XREF_BIND_HOST_FINISH_FAILED'
        } else {$null}}
}

function Convert-P09XrefBatchCaseSummary([int]$CaseIndex,$Flow) {
    $expected='P09-XREF-BOOK-C'+$CaseIndex.ToString('00')
    foreach ($key in @('schema_version','case_id','state','phase','steps','error_code','cleanup_error_code',
        'cleanup_callback_entered','cleanup_callback_returned','host_finish_error_code','native_execution_attested',
        'native_acceptance_attested','native_cleanup_attested','causal_insertion_or_preservation_proved','p09_complete','accepted_count_delta')) {
        Assert-P09XrefBinding ($Flow.Contains($key)) 'BATCH_INCOMPLETE_CASE_RECORD'
    }
    Assert-P09XrefBinding ($Flow.schema_version -ceq 'hwpx-agent.crossref-case-callback-flow/v1' -and
        $Flow.case_id -ceq $expected -and $Flow.steps.Count -ge 1 -and $Flow.steps.Count -le 16) 'BATCH_CASE_IDENTITY'
    foreach ($key in @('native_execution_attested','native_acceptance_attested','native_cleanup_attested',
            'causal_insertion_or_preservation_proved','p09_complete')) {
        Assert-P09XrefBinding ($Flow[$key] -is [bool] -and -not $Flow[$key]) 'BATCH_UNATTESTED_FIELDS_REQUIRED'
    }
    Assert-P09XrefBinding ($Flow.accepted_count_delta -is [int] -and $Flow.accepted_count_delta -eq 0) 'BATCH_NO_ACCEPTANCE_PROMOTION'
    $steps=Get-P09XrefCaseFlowSteps;$returned=0
    for ($i=0;$i -lt $Flow.steps.Count;$i++) {
        $entry=$Flow.steps[$i]
        Assert-P09XrefBinding ($entry.step -ceq $steps[$i] -and $entry.callback_entered -is [bool] -and $entry.callback_entered -and
            $entry.callback_returned -is [bool]) 'BATCH_CASE_STEP_PREFIX'
        if ($entry.callback_returned) {$returned++}
    }
    $success=($Flow.state -ceq 'all_callbacks_returned_native_effect_unattested' -and
        $Flow.steps.Count -eq 16 -and $returned -eq 16 -and $Flow.phase -ceq 'final_source_check' -and
        $null -eq $Flow.error_code -and $null -eq $Flow.cleanup_error_code -and $null -eq $Flow.host_finish_error_code -and
        $Flow.cleanup_callback_entered -is [bool] -and $Flow.cleanup_callback_entered -and
        $Flow.cleanup_callback_returned -is [bool] -and $Flow.cleanup_callback_returned)
    return [ordered]@{case_id=$expected;callback_flow_returned=$success;callback_steps=$Flow.steps.Count;
        callback_steps_returned=$returned;phase=if ($Flow.phase -cin $steps) {$Flow.phase} else {'unknown_callback_phase'};
        error_code=if ($null -eq $Flow.error_code) {$null} else {Get-P09XrefBatchSafeCode $Flow.error_code 'P09_XREF_BIND_BATCH_CASE_FAILED_NO_RAW_VALUES'};
        cleanup_error_code=if ($null -eq $Flow.cleanup_error_code) {$null} else {Get-P09XrefBatchSafeCode $Flow.cleanup_error_code 'P09_XREF_BIND_BATCH_CLEANUP_FAILED_NO_RAW_VALUES'};
        host_finish_error_code=if ($null -eq $Flow.host_finish_error_code) {$null} else {'P09_XREF_BIND_HOST_FINISH_FAILED'};
        native_execution_attested=$false;native_cleanup_attested=$false;accepted_count_delta=0;p09_complete=$false}
}

function Invoke-P09XrefFixedBatchCore {
    param([Parameter(Mandatory)][scriptblock]$CaseExecutor,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    Assert-P09XrefBinding ($Record.Count -eq 0) 'BATCH_FRESH_RECORD_REQUIRED'
    $Record.schema_version='hwpx-agent.crossref-fixed-eight-callback-batch/v1'
    $Record.state='callback_batch_started_unattested';$Record.planned_cases=8
    $Record.cases=[Collections.Generic.List[object]]::new();$Record.completed_callback_cases=0
    $Record.stopped_case_index=$null;$Record.error_code=$null;$Record.automatic_retry=$false
    try {
        for ($index=1;$index -le 8;$index++) {
            $flow=[ordered]@{}
            try {
                [void](& $CaseExecutor $index $flow)
                $summary=Convert-P09XrefBatchCaseSummary $index $flow
            } catch {
                $summary=[ordered]@{case_id=('P09-XREF-BOOK-C'+$index.ToString('00'));callback_flow_returned=$false;
                    error_code=(Get-P09XrefBatchSafeCode $_.Exception.Message 'P09_XREF_BIND_BATCH_CALLBACK_FAILED_NO_RAW_VALUES');
                    original_error_code=(Get-P09XrefBatchSafeCode $flow['error_code'] 'P09_XREF_BIND_BATCH_CASE_UNAVAILABLE');
                    original_cleanup_error_code=if ($null -eq $flow['cleanup_error_code']) {$null} else {
                        Get-P09XrefBatchSafeCode $flow['cleanup_error_code'] 'P09_XREF_BIND_BATCH_CLEANUP_FAILED_NO_RAW_VALUES'};
                    native_execution_attested=$false;native_cleanup_attested=$false;accepted_count_delta=0;p09_complete=$false}
            }
            [void]$Record.cases.Add($summary)
            if (-not $summary.callback_flow_returned) {
                $Record.state='callback_batch_stopped_partial_unattested';$Record.stopped_case_index=$index
                $Record.error_code='P09_XREF_BIND_BATCH_CASE_NOT_RETURNED';break
            }
            $Record.completed_callback_cases++
        }
        if ($Record.completed_callback_cases -eq 8) {$Record.state='all_eight_callback_flows_returned_unattested'}
    } finally {
        $Record.native_execution_attested=$false;$Record.native_cleanup_attested=$false
        $Record.native_execution_authorized=$false;$Record.causal_insertion_or_preservation_proved=$false
        $Record.accepted_count_delta=0;$Record.p09_complete=$false
    }
}

function Invoke-P09XrefFixedHostBatch {
    param([Parameter(Mandatory)]$Channel,[Parameter(Mandatory)]$ProbeLease,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    Assert-P09XrefBinding ($Channel.case_index -eq 1 -and $Channel.sequence -eq 0 -and
        -not $Channel.failed -and -not $Channel.finish_attempted) 'BATCH_FRESH_CHANNEL'
    Assert-P09XrefBinding (-not $ProbeLease.closed -and $ProbeLease.stream -is [IO.FileStream] -and
        $ProbeLease.stream.CanRead -and -not $ProbeLease.stream.CanWrite -and
        $ProbeLease.binary_sha256 -ceq '0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb') 'BATCH_LIVE_FIXED_PROBE'
    # The existing reader validates the COMPLETE fixed eight-row packet, once here.
    $first=Get-P09XrefFixedSdkCase 1
    Assert-P09XrefBinding ($first.case_id -ceq 'P09-XREF-BOOK-C01') 'BATCH_FIXED_PACKET'
    for ($index=1;$index -le 8;$index++) {
        $path=Get-P09XrefCaseArtifactPath $index 'opened'
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent $path))) 'BATCH_NATIVE_ATTEMPT_ALREADY_EXISTS'
    }
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefHostBoundCase $Channel $index $ProbeLease $flow
    } $Record
}
