[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_DIAGNOSTIC_MODELS_ONLY'}
foreach ($name in @('crossref-owned-active-source','crossref-case-flow','crossref-fixed-batch')) {. (Join-Path $PSScriptRoot ($name+'.ps1'))}
function New-FailureModel([string]$Code) {
    $r=[ordered]@{}
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefCaseFlow $index {param($step,$state) if ($step -ceq 'source_bind') {throw $Code}} {} ([ordered]@{}) $flow
        $flow.host_finish_error_code=$null
    } $r
    return $r
}
try {
    $r=New-FailureModel 'P09_XREF_BIND_SINGLE_DOCUMENT_REQUIRED';$d=Get-P09XrefBatchFailureSummary $r
    Assert-P09XrefBinding ($d.case_index -eq 1 -and $d.phase -ceq 'source_bind' -and $d.callback_steps -eq 4 -and
        $d.callback_steps_returned -eq 3 -and $d.error_code -ceq 'P09_XREF_BIND_SINGLE_DOCUMENT_REQUIRED' -and
        $r.completed_callback_cases -eq 0 -and $r.cases.Count -eq 1 -and -not $r.native_execution_authorized) 'MODEL_FAILED_STEP_CODE_AND_NO_RETRY'
    [Console]::WriteLine('test case_failure::source_bind_error_step_prefix_and_no_retry ... ok')
    $r.cases[0]['cleanup_error_code']='P09_XREF_BIND_PORTS_COMPLETION_FAILED';$r.cases[0]['host_finish_error_code']='P09_XREF_BIND_HOST_FINISH_FAILED'
    $d=Get-P09XrefBatchFailureSummary $r
    Assert-P09XrefBinding ($d.cleanup_error_code -ceq 'P09_XREF_BIND_PORTS_COMPLETION_FAILED' -and $d.host_finish_error_code -ceq 'P09_XREF_BIND_HOST_FINISH_FAILED') 'MODEL_PRIMARY_AND_CLEANUP'
    [Console]::WriteLine('test case_failure::primary_cleanup_and_finish_failures_remain_separate ... ok')
    $r.cases[0]['phase']='PRIVATE-DOCUMENT-PATH';$r.cases[0]['error_code']='PRIVATE-DOCUMENT-PATH'
    $r.cases[0]['cleanup_error_code']='PRIVATE-DOCUMENT-PATH';$r.cases[0]['host_finish_error_code']='PRIVATE-DOCUMENT-PATH'
    $r.cases[0]['untrusted_extra']='PRIVATE-DOCUMENT-PATH';$d=Get-P09XrefBatchFailureSummary $r
    $json=$d|ConvertTo-Json -Depth 4 -Compress
    Assert-P09XrefBinding ($d.Count -eq 7 -and $d.phase -ceq 'unknown_callback_phase' -and -not $json.Contains('PRIVATE-') -and
        $d.error_code -ceq 'P09_XREF_BIND_BATCH_CASE_FAILED_NO_RAW_VALUES') 'MODEL_CLOSED_PROJECTION_NO_RAW'
    [Console]::WriteLine('test case_failure::only_seven_closed_fields_no_source_or_extra_values ... ok')
    $r.cases[0]=[ordered]@{error_code='P09_XREF_BIND_BATCH_CALLBACK_FAILED_NO_RAW_VALUES';original_error_code='P58_OPEN_FAILED';original_cleanup_error_code='P58_CLOSE_FAILED'}
    $d=Get-P09XrefBatchFailureSummary $r
    Assert-P09XrefBinding ($d.error_code -ceq 'P58_OPEN_FAILED' -and $d.cleanup_error_code -ceq 'P58_CLOSE_FAILED' -and
        $d.callback_steps -eq 0 -and $d.phase -ceq 'unknown_callback_phase') 'MODEL_ORIGINAL_CONVERSION_ERROR'
    [Console]::WriteLine('test case_failure::summary_conversion_preserves_original_closed_errors ... ok')
    $bad=[ordered]@{stopped_case_index=[int]2;cases=@([ordered]@{})};$rejected=$false
    try {[void](Get-P09XrefBatchFailureSummary $bad)} catch {$rejected=$true}
    Assert-P09XrefBinding $rejected 'MODEL_BAD_CASE_PREFIX_REJECTED'
    [Console]::WriteLine('test case_failure::inconsistent_case_prefix_is_rejected ... ok')
    $all=[ordered]@{}
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefCaseFlow $index {} {} ([ordered]@{}) $flow;$flow.host_finish_error_code=$null
    } $all
    Assert-P09XrefBinding ($all.completed_callback_cases -eq 8 -and $null -eq (Get-P09XrefBatchFailureSummary $all) -and -not $all.native_execution_authorized) 'MODEL_ALL_UNATTESTED_NOT_FAILURE'
    [Console]::WriteLine('test case_failure::successful_model_has_no_failure_or_native_attestation ... ok')
    [Console]::WriteLine('test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out')
} catch {[Console]::WriteLine('Error: CASE_FAILURE_PROJECTION_MODEL_FAILED');exit 1}
