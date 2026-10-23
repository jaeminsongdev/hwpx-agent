# Model and fixed-denial tests only. All real channel input is hardcoded denial.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
    'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
$passed=0;$lease=$null
function New-P09XrefBatchModelFlow([int]$Index,$Flow) {
    Invoke-P09XrefCaseFlow $Index {} {} ([ordered]@{}) $Flow
    $Flow.host_finish_error_code=$null
}
try {
    $script:seen=[Collections.Generic.List[int]]::new();$record=[ordered]@{}
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        [void]$script:seen.Add($index);New-P09XrefBatchModelFlow $index $flow
    } $record
    Assert-P09XrefBinding (($script:seen -join ',') -ceq '1,2,3,4,5,6,7,8' -and $record.planned_cases -eq 8 -and
        $record.cases.Count -eq 8 -and $record.completed_callback_cases -eq 8 -and
        $record.state -ceq 'all_eight_callback_flows_returned_unattested' -and -not $record.native_execution_attested -and
        -not $record.native_cleanup_attested -and -not $record.p09_complete) 'TEST_BATCH_EIGHT_MODEL_CALLBACKS_NOT_NATIVE'
    $passed++

    for ($failure=1;$failure -le 8;$failure++) {
        $script:failedCase=$failure;$script:seen=[Collections.Generic.List[int]]::new();$record=[ordered]@{}
        Invoke-P09XrefFixedBatchCore {param($index,$flow)
            [void]$script:seen.Add($index)
            if ($index -eq $script:failedCase) {
                Invoke-P09XrefCaseFlow $index {throw 'STOP_BATCH_MODEL_CASE'} {} ([ordered]@{}) $flow
                $flow.host_finish_error_code=$null
            } else {New-P09XrefBatchModelFlow $index $flow}
        } $record
        Assert-P09XrefBinding ($script:seen.Count -eq $failure -and $record.cases.Count -eq $failure -and
            $record.completed_callback_cases -eq ($failure-1) -and $record.stopped_case_index -eq $failure -and
            $record.state -ceq 'callback_batch_stopped_partial_unattested' -and -not $record.automatic_retry -and
            $record.cases[$failure-1].error_code -ceq 'STOP_BATCH_MODEL_CASE') 'TEST_BATCH_EACH_FAILURE_STOPS_NO_RETRY'
    }
    $passed++

    $record=[ordered]@{}
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        Invoke-P09XrefCaseFlow $index {throw 'STOP_BATCH_MODEL_PRIMARY'} {throw 'STOP_BATCH_MODEL_CLEANUP'} ([ordered]@{}) $flow
        $flow.host_finish_error_code=$null
    } $record
    Assert-P09XrefBinding ($record.cases[0].error_code -ceq 'STOP_BATCH_MODEL_PRIMARY' -and
        $record.cases[0].cleanup_error_code -ceq 'STOP_BATCH_MODEL_CLEANUP' -and $record.cases.Count -eq 1) 'TEST_BATCH_ERRORS_SEPARATE'
    $passed++

    $record=[ordered]@{}
    Invoke-P09XrefFixedBatchCore {param($index,$flow)
        New-P09XrefBatchModelFlow $index $flow
        $flow.private_unknown_field='synthetic-private-command';$flow.native_execution_attested=$true
    } $record
    Assert-P09XrefBinding ($record.cases.Count -eq 1 -and $record.completed_callback_cases -eq 0 -and
        -not $record.native_execution_attested -and -not $record.p09_complete -and
        ($record | ConvertTo-Json -Depth 6 -Compress) -cnotmatch 'synthetic-private-command') 'TEST_BATCH_NO_CLAIM_PROMOTION_OR_PRIVATE_COPY'
    $passed++

    $existing=[ordered]@{keep=$true};$rejected=$false
    try {Invoke-P09XrefFixedBatchCore {} $existing} catch {$rejected=$true}
    Assert-P09XrefBinding ($rejected -and $existing.Count -eq 1 -and $existing.keep) 'TEST_BATCH_NO_OVERWRITE_EXISTING_RECORD'
    $passed++

    # Fixed in-memory responses: even external stdin cannot permit native work.
    $deny='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":1,"case_index":1,"acknowledged":false,"error_code":"XREF_HOST_TEST_BATCH_DENIED","native_execution_authorized":false,"p09_complete":false}'
    $finish='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":2,"case_index":1,"acknowledged":true,"error_code":null,"native_execution_authorized":false,"p09_complete":false}'
    $reader=[IO.StringReader]::new($deny+"`n"+$finish+"`n");$writer=[IO.StringWriter]::new()
    try {
        $channel=New-P09XrefHostChannel $reader $writer;$lease=New-P09XrefProbeLease;$record=[ordered]@{}
        Invoke-P09XrefFixedHostBatch $channel $lease $record
        Assert-P09XrefBinding ($record.planned_cases -eq 8 -and $record.cases.Count -eq 1 -and
            $record.completed_callback_cases -eq 0 -and $record.stopped_case_index -eq 1 -and
            $record.cases[0].error_code -ceq 'P09_XREF_BIND_HOST_DENIED' -and
            $record.cases[0].callback_steps -eq 1 -and $null -eq $record.cases[0].host_finish_error_code -and
            $channel.sequence -eq 2 -and $channel.finish_attempted -and -not $record.native_execution_attested -and
            $null -eq ('P58OwnedWindowProcess' -as [type])) 'TEST_BATCH_ACTUAL_CONCRETE_FIRST_CASE_DENIAL'
        for ($index=1;$index -le 8;$index++) {
            Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'TEST_BATCH_NO_NATIVE_DIR'
        }
    } finally {$reader.Dispose();$writer.Dispose()}
    $passed++
    [ordered]@{state='six_fixed_batch_contracts_pass_not_native';passed=$passed;failed=0;
        fixed_denial_not_external_input=$true;planned_native_cases=8;actual_Hangul_or_COM=$false;
        native_directories_created=$false;native_execution_authorized=$false;accepted_count_delta=0;p09_complete=$false} | ConvertTo-Json -Compress
} catch {
    [ordered]@{state='fixed_batch_contract_failed';passed=$passed;failed=1;source_line=$_.InvocationInfo.ScriptLineNumber;
        error_type=$_.Exception.GetType().Name;error_code=(Get-P09XrefBatchSafeCode $_.Exception.Message 'P09_XREF_BIND_BATCH_TEST_FAILED_NO_RAW_VALUES');
        actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
