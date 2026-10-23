# Model flow and real readonly probe rejection only; no Hangul/native action.
[CmdletBinding()]
param([switch]$LeaseContractsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-owned-artifact.ps1')
. (Join-Path $PSScriptRoot 'crossref-save-reopen.ps1')
. (Join-Path $PSScriptRoot 'crossref-stage-probe.ps1')
. (Join-Path $PSScriptRoot 'crossref-case-flow.ps1')
$script:passed=0;$script:declared=0;$script:filtered=0;$script:actualProbe=$null
function Invoke-P09XrefFlowTest([scriptblock]$Body) {
    $script:declared++
    if ($LeaseContractsOnly -and $script:declared -le 5) {$script:filtered++;return}
    & $Body;$script:passed++
}
function Assert-P09XrefFlowReject([scriptblock]$Body) {
    $rejected=$false;try {& $Body} catch {$rejected=$true}
    Assert-P09XrefBinding $rejected 'TEST_FLOW_EXPECTED_REJECTION'
}
try {
    Invoke-P09XrefFlowTest {
        $expected='prepare_slot,create_save_session,source_open,source_bind,opened_save,opened_probe,sdk_insert,saved_save,saved_probe,save_session_close,create_reopen_session,fresh_saved_open,reopened_save,reopened_probe,reopen_session_close,final_source_check'
        Assert-P09XrefBinding (((Get-P09XrefCaseFlowSteps) -join ',') -ceq $expected) 'TEST_FIXED_FLOW_SEQUENCE'
        for ($i=1;$i -le 8;$i++) {
            $state=[ordered]@{seen=[Collections.Generic.List[string]]::new();cleanup=0};$record=[ordered]@{}
            Invoke-P09XrefCaseFlow $i {param($step,$s) [void]$s.seen.Add($step)} {param($s) $s.cleanup++} $state $record
            Assert-P09XrefBinding (($state.seen -join ',') -ceq $expected -and $state.cleanup -eq 1 -and
                $record.state -ceq 'all_callbacks_returned_native_effect_unattested' -and
                -not $record.native_execution_attested -and -not $record.native_acceptance_attested) 'TEST_MODEL_FLOW_NOT_NATIVE'
        }
    }
    Invoke-P09XrefFlowTest {
        $steps=Get-P09XrefCaseFlowSteps
        for ($i=0;$i -lt $steps.Count;$i++) {
            $state=[ordered]@{fail=$steps[$i];seen=[Collections.Generic.List[string]]::new();cleanup=0};$record=[ordered]@{}
            Invoke-P09XrefCaseFlow 1 {param($step,$s) [void]$s.seen.Add($step);if ($step -ceq $s.fail) {throw 'P09_XREF_BIND_TEST_STEP_FAILURE'}} {param($s) $s.cleanup++} $state $record
            Assert-P09XrefBinding ($state.seen.Count -eq ($i+1) -and $state.cleanup -eq 1 -and
                $record.steps.Count -eq ($i+1) -and -not $record.steps[$i].callback_returned -and
                $record.phase -ceq $steps[$i] -and -not $record.automatic_retry) 'TEST_EACH_FAILURE_STOPS_WITH_ONE_CLEANUP'
        }
    }
    Invoke-P09XrefFlowTest {
        $state=[ordered]@{};$record=[ordered]@{}
        Invoke-P09XrefCaseFlow 1 {throw 'private synthetic callback data'} {throw 'P58_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL'} $state $record
        Assert-P09XrefBinding ($record.error_code -ceq 'P09_XREF_BIND_FLOW_CALLBACK_FAILED_NO_RAW_VALUES' -and
            $record.cleanup_error_code -ceq 'P58_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL' -and
            -not $record.cleanup_callback_returned -and $record.state -ceq 'callback_flow_failed_native_effect_unattested') 'TEST_PRIMARY_AND_CLEANUP_FAILURES_PRESERVED'
        Assert-P09XrefBinding (($record | ConvertTo-Json -Depth 5 -Compress) -cnotmatch 'private synthetic') 'TEST_PRIVATE_FAILURE_REDACTED'
    }
    Invoke-P09XrefFlowTest {
        $state=[ordered]@{};$record=[ordered]@{}
        Invoke-P09XrefCaseFlow 1 {param($step,$s) $record.native_execution_attested=$true;$record.native_acceptance_attested=$true;$record.accepted_count_delta=1} {} $state $record
        Assert-P09XrefBinding (-not $record.native_execution_attested -and -not $record.native_acceptance_attested -and
            -not $record.native_cleanup_attested -and -not $record.p09_complete -and $record.accepted_count_delta -eq 0) 'TEST_CALLBACK_RETURN_CANNOT_PROMOTE_NATIVE_CLAIMS'
        Assert-P09XrefFlowReject {Invoke-P09XrefCaseFlow 0 {} {} ([ordered]@{}) ([ordered]@{})}
        Assert-P09XrefFlowReject {Invoke-P09XrefCaseFlow 9 {} {} ([ordered]@{}) ([ordered]@{})}
    }
    Invoke-P09XrefFlowTest {
        $path=Join-Path $PSScriptRoot 'inspect-crossref-worker-composition.ps1'
        $text=[Text.UTF8Encoding]::new($false,$true).GetString([IO.File]::ReadAllBytes($path))
        $code=Get-P09XrefStageRunnerCode $text
        $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
        $function=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -ceq 'Invoke-P09XrefPreparationChild'},$false))[0]
        $marker='    $start=[Diagnostics.ProcessStartInfo]::new()';$original=$function.Extent.Text
        Assert-P09XrefBinding ($code.capture_suffix -ceq $original.Substring($original.IndexOf($marker,[StringComparison]::Ordinal)) -and
            $code.support.Count -eq 2 -and $code.runner.Contains("`$childArguments=@('case',`$CaseIndex.ToString(),`$Stage,`$ExpectedSha256)")) 'TEST_EXACT_QUALIFIED_CAPTURE_SUFFIX'
        Assert-P09XrefFlowReject {Get-P09XrefStageRunnerCode ($text+'changed')}
        Assert-P09XrefFlowReject {Get-P09XrefStageRunnerCode 'arbitrary code is not a template'}
    }
    $lease=New-P09XrefProbeLease
    try {
        Invoke-P09XrefFlowTest {
            Assert-P09XrefBinding (-not $lease.closed -and $lease.stream.CanRead -and -not $lease.stream.CanWrite) 'TEST_REAL_READ_LEASE'
            $writer=$null;$blocked=$false
            try {$writer=[IO.File]::Open($lease.binary,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)} catch {$blocked=$true}
            finally {if ($null -ne $writer) {$writer.Dispose()}}
            Assert-P09XrefBinding $blocked 'TEST_LEASE_DENIES_BINARY_WRITE_WITHOUT_WRITING'
        }
        Invoke-P09XrefFlowTest {
            $missing=0
            for ($i=1;$i -le 8;$i++) {if (-not (Test-Path -LiteralPath (Get-P09XrefCaseArtifactPath $i 'opened'))) {$missing=$i;break}}
            Assert-P09XrefBinding ($missing -gt 0) 'TEST_REAL_MISSING_ARTIFACT_REQUIRED'
            $record=[ordered]@{}
            Assert-P09XrefFlowReject {Invoke-P09XrefStageProbe $lease $missing 'opened' ('0'*64) $record}
            Assert-P09XrefBinding ($record.children.Count -eq 1 -and $record.children[0].exit_code -eq 2 -and
                $record.children[0].cleanup_confirmed -and $record.error_code -ceq 'P09_XREF_WORKER_PREPARATION_CHILD_FAILED') 'TEST_ACTUAL_MISSING_SOURCE_REJECTED_CHILD_CLEAN'
            Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Get-P09XrefCaseArtifactPath $missing 'opened'))) 'TEST_NO_ARTIFACT_FABRICATION'
            $script:actualProbe=[ordered]@{case_index=$missing;children=@($record.children.ToArray());error_code=$record.error_code;
                missing_artifact_still_missing=$true;native_or_producer_attestation=$false}
        }
        Invoke-P09XrefFlowTest {
            $record=[ordered]@{}
            Assert-P09XrefFlowReject {Invoke-P09XrefStageProbe $lease 1 '../saved' ('a'*64) $record}
            Assert-P09XrefBinding ($record.children.Count -eq 0) 'TEST_INVALID_SELECTOR_BEFORE_CHILD'
        }
    } finally {Close-P09XrefProbeLease $lease}
    Invoke-P09XrefFlowTest {
        Close-P09XrefProbeLease $lease
        $record=[ordered]@{}
        Assert-P09XrefFlowReject {Invoke-P09XrefStageProbe $lease 1 'saved' ('a'*64) $record}
        Assert-P09XrefBinding ($lease.closed -and -not $lease.stream.CanRead -and $record.children.Count -eq 0) 'TEST_CLOSED_LEASE_REJECTS_BEFORE_CHILD'
    }
    $expected=if ($LeaseContractsOnly) {4} else {9}
    Assert-P09XrefBinding ($script:passed -eq $expected -and $script:declared -eq 9 -and
        $script:filtered -eq (9-$expected)) 'TEST_EXACT_FLOW_PROBE'
    $state=if ($LeaseContractsOnly) {'four_remaining_lease_probe_contracts_pass_native_not_run'} else {'nine_case_flow_stage_probe_contracts_pass_native_not_run'}
    [ordered]@{state=$state;passed=$script:passed;failed=0;filtered=$script:filtered;declared=$script:declared;
        actual_readonly_missing_probe=$script:actualProbe;lease_closed=$lease.closed;
        native_session_started=$false;actual_native_case_executor_bound=$false;native_producer_qualified=$false;p09_complete=$false} | ConvertTo-Json -Depth 6 -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_(BIND|WORKER)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_FLOW_TEST_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='case_flow_probe_contract_failed';passed=$script:passed;failed=1;error_code=$code;
        actual_readonly_missing_probe=$script:actualProbe;native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Depth 6 -Compress
    exit 2
}
