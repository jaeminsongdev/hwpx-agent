# Only the completion-latch delta. No prior eight tests, native session or output creation.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe','crossref-case-flow','crossref-native-case-ports')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
$lease=$null;$passed=0
function Assert-P09XrefCompletionReject([scriptblock]$Body,[string]$Expected) {
    $actual=$null;try {& $Body} catch {$actual=$_.Exception.Message}
    Assert-P09XrefBinding ($actual -ceq $Expected) 'TEST_COMPLETION_REJECT'
}
try {
    $lease=New-P09XrefProbeLease
    $deny={throw 'STOP_PORTS_TEST_HOST_DENIED'};$admit={throw 'STOP_PORTS_TEST_NATIVE_MUST_NOT_REACH'}
    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit
    Assert-P09XrefBinding (-not $state.completion_attempted) 'TEST_COMPLETION_INITIAL'
    [void]$state.trace.sessions.Add([ordered]@{process=$null;cleanup_error='P58_OWNER_UNVERIFIED_NO_BLANKET_QUIT';
        quit_invoked=$false;close_without_dirty_prompt_returned=$false;remaining_owned_process_count=-1})
    Assert-P09XrefCompletionReject {Complete-P09XrefNativeCasePorts $state} 'P09_XREF_BIND_PORTS_COMPLETION_FAILED'
    $original=$state.trace.completion
    Assert-P09XrefBinding ($state.completion_attempted -and
        $original.cleanup_error_code -ceq 'P09_XREF_BIND_PORTS_SESSION_CLEANUP_UNCONFIRMED') 'TEST_COMPLETION_FAILURE_LATCH'
    Assert-P09XrefCompletionReject {Complete-P09XrefNativeCasePorts $state} 'P09_XREF_BIND_PORTS_NO_COMPLETION_RETRY'
    Assert-P09XrefBinding ([object]::ReferenceEquals($original,$state.trace.completion) -and
        $original.cleanup_error_code -ceq 'P09_XREF_BIND_PORTS_SESSION_CLEANUP_UNCONFIRMED' -and
        -not $state.trace_written -and -not (Test-Path -LiteralPath $state.run)) 'TEST_COMPLETION_ERROR_NOT_RESET'
    $passed++

    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit;$record=[ordered]@{}
    Invoke-P09XrefNativeCaseWorkflow $state $record
    Assert-P09XrefBinding ($state.completion_attempted -and $state.failed -and $record.cleanup_callback_returned -and
        $record.steps.Count -eq 1 -and $record.error_code -ceq 'STOP_PORTS_TEST_HOST_DENIED' -and
        -not $record.native_execution_attested -and -not $record.native_cleanup_attested) 'TEST_COMPLETION_WORKFLOW_LATCH'
    $original=$state.trace.completion
    Assert-P09XrefCompletionReject {Complete-P09XrefNativeCasePorts $state} 'P09_XREF_BIND_PORTS_NO_COMPLETION_RETRY'
    Assert-P09XrefBinding ([object]::ReferenceEquals($original,$state.trace.completion) -and
        $null -eq $original.cleanup_error_code -and -not $state.trace_written -and
        -not (Test-Path -LiteralPath $state.run)) 'TEST_COMPLETION_NO_SECOND_WRITE_OR_RESET'
    $passed++
    [ordered]@{state='two_completion_latch_contracts_pass_native_not_run';passed=$passed;failed=0;
        prior_eight_not_reexecuted=$true;native_session_started=$false;native_execution_authorized=$false;
        native_case_or_document_created=$false;p09_complete=$false} | ConvertTo-Json -Depth 4 -Compress
} catch {
    [ordered]@{state='completion_latch_contract_failed';passed=$passed;failed=1;error_type=$_.Exception.GetType().Name;
        source_line=$_.InvocationInfo.ScriptLineNumber;error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|STOP_[A-Z_]+)$') {
            $_.Exception.Message
        } else {'COMPLETION_TEST_FAILED_NO_RAW_VALUES'};native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Depth 4 -Compress
    exit 2
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
