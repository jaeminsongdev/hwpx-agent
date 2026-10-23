# Callback control flow only; callback completion never attests a native operation.
# Trusted native ports, producer binding, admission and resource guards are separate.
Set-StrictMode -Version Latest

function Get-P09XrefCaseFlowSteps {
    return @('prepare_slot','create_save_session','source_open','source_bind','opened_save','opened_probe',
        'sdk_insert','saved_save','saved_probe','save_session_close','create_reopen_session','fresh_saved_open',
        'reopened_save','reopened_probe','reopen_session_close','final_source_check')
}

function Invoke-P09XrefCaseFlow {
    param([Parameter(Mandatory)][int]$CaseIndex,[Parameter(Mandatory)][scriptblock]$StepExecutor,
        [Parameter(Mandatory)][scriptblock]$CleanupExecutor,[Parameter(Mandatory)][System.Collections.IDictionary]$State,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8) 'FLOW_CASE_INDEX'
    $Record.schema_version='hwpx-agent.crossref-case-callback-flow/v1'
    $Record.case_id='P09-XREF-BOOK-C'+$CaseIndex.ToString('00')
    $Record.state='callback_flow_started_unattested';$Record.phase=$null
    $Record.steps=[Collections.Generic.List[object]]::new();$Record.error_code=$null;$Record.cleanup_error_code=$null
    $Record.cleanup_callback_entered=$false;$Record.cleanup_callback_returned=$false
    $Record.native_execution_attested=$false;$Record.native_acceptance_attested=$false
    $Record.causal_insertion_or_preservation_proved=$false;$Record.accepted_count_delta=0;$Record.automatic_retry=$false
    try {
        foreach ($step in (Get-P09XrefCaseFlowSteps)) {
            $Record.phase=$step
            $entry=[ordered]@{step=$step;callback_entered=$true;callback_returned=$false}
            [void]$Record.steps.Add($entry)
            [void](& $StepExecutor $step $State)
            $entry.callback_returned=$true
        }
        $Record.state='all_callbacks_returned_native_effect_unattested'
    } catch {
        $Record.state='callback_flow_failed_native_effect_unattested'
        $Record.error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+|STOP_[A-Z_]+)$') {
            $_.Exception.Message
        } else {'P09_XREF_BIND_FLOW_CALLBACK_FAILED_NO_RAW_VALUES'}
    } finally {
        $Record.cleanup_callback_entered=$true
        try {
            [void](& $CleanupExecutor $State)
            $Record.cleanup_callback_returned=$true
        } catch {
            $Record.cleanup_error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+|STOP_[A-Z_]+)$') {
                $_.Exception.Message
            } else {'P09_XREF_BIND_FLOW_CLEANUP_FAILED_NO_RAW_VALUES'}
            if ($null -eq $Record.error_code) {$Record.state='callback_cleanup_failed_native_effect_unattested'}
        }
    }
    $Record.native_execution_attested=$false;$Record.native_acceptance_attested=$false
    $Record.native_cleanup_attested=$false;$Record.causal_insertion_or_preservation_proved=$false
    $Record.accepted_count_delta=0;$Record.p09_complete=$false
    # No state/provider data, document values, SDK commands or ownership proof is serialized here.
    # In particular cleanup_callback_returned is NOT cleanup_confirmed.
}
