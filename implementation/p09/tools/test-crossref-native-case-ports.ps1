# Actual source bindings and denial paths only. Never call a native session step.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe','crossref-case-flow','crossref-native-case-ports')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
$passed=0;$lease=$null
function Assert-P09XrefPortsReject([scriptblock]$Body,[string]$Code) {
    $actual=$null;try {& $Body} catch {$actual=$_.Exception.Message}
    Assert-P09XrefBinding ($actual -ceq $Code) 'TEST_PORTS_EXACT_REJECTION'
}
try {
    $source=Read-P09XrefFrozenNativeHarness
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
    Import-P09XrefFrozenIoHelpers
    foreach ($name in @('Assert-P58File','Write-P58Trace')) {
        $found=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$false))
        $inner=$found[0].Body.Extent.Text.Substring(1,$found[0].Body.Extent.Text.Length-2)
        Assert-P09XrefBinding ((Get-Command $name).ScriptBlock.ToString() -ceq $inner) 'TEST_PORTS_EXACT_FROZEN_IO'
    }
    Assert-P09XrefOriginalIoFunctions
    Assert-P09XrefBinding ($null -eq ('P58OwnedWindowProcess' -as [type])) 'TEST_PORTS_IMPORT_NO_WINDOW_BRIDGE'
    $passed++

    $lease=New-P09XrefProbeLease
    $deny={param($step,$state) throw 'STOP_PORTS_TEST_HOST_DENIED'}
    $admit={throw 'STOP_PORTS_TEST_NATIVE_MUST_NOT_REACH'}
    for ($i=1;$i -le 8;$i++) {
        $state=New-P09XrefNativeCaseState $i $lease $deny $admit
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath $state.run) -and -not $state.slot_created -and
            $null -eq $state.owner -and $null -eq $state.document -and $state.trace.sessions.Count -eq 0 -and
            $state.next_step_index -eq 0 -and -not $state.failed -and
            -not $state.trace.producer_binding_qualified -and -not $state.trace.native_host_guard_qualified -and
            -not $state.trace.p09_complete) 'TEST_PORTS_CONSTRUCTOR_NO_EFFECT'
    }
    $passed++

    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit
    Assert-P09XrefPortsReject {Invoke-P09XrefNativeCaseStep 'prepare_slot' $state} 'STOP_PORTS_TEST_HOST_DENIED'
    Assert-P09XrefBinding ($state.failed -and $state.next_step_index -eq 0 -and -not (Test-Path -LiteralPath $state.run)) 'TEST_PORTS_HOST_FAILURE_LATCHED'
    Assert-P09XrefPortsReject {Invoke-P09XrefNativeCaseStep 'prepare_slot' $state} 'P09_XREF_BIND_PORTS_ORDER_OR_RETRY'
    $passed++

    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit;$record=[ordered]@{}
    Invoke-P09XrefNativeCaseWorkflow $state $record
    Assert-P09XrefBinding ($record.error_code -ceq 'STOP_PORTS_TEST_HOST_DENIED' -and $record.steps.Count -eq 1 -and
        $record.phase -ceq 'prepare_slot' -and $record.cleanup_callback_returned -and
        $null -eq $record.cleanup_error_code -and -not $record.native_execution_attested -and
        -not $record.native_cleanup_attested -and $record.accepted_count_delta -eq 0 -and
        -not $state.trace_written -and -not (Test-Path -LiteralPath $state.run)) 'TEST_PORTS_WORKFLOW_HOST_DENIAL_CLEAN'
    $passed++

    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit
    Assert-P09XrefPortsReject {Invoke-P09XrefNativeCaseStep 'sdk_insert' $state} 'P09_XREF_BIND_PORTS_ORDER_OR_RETRY'
    Assert-P09XrefBinding (-not $state.failed -and $state.trace.sessions.Count -eq 0) 'TEST_PORTS_ORDER_REJECT_BEFORE_HOST'
    $passed++

    # Pure trace models: no owner object, COM, filesystem output or replacement native helper.
    $state=New-P09XrefNativeCaseState 1 $lease $deny $admit
    Assert-P09XrefNativeSessionsClean $state
    [void]$state.trace.sessions.Add([ordered]@{process=$null;cleanup_error='P58_OWNER_UNVERIFIED_NO_BLANKET_QUIT';
        quit_invoked=$false;close_without_dirty_prompt_returned=$false;remaining_owned_process_count=-1})
    Assert-P09XrefPortsReject {Complete-P09XrefNativeCasePorts $state} 'P09_XREF_BIND_PORTS_COMPLETION_FAILED'
    Assert-P09XrefBinding ($state.trace.completion.cleanup_error_code -ceq 'P09_XREF_BIND_PORTS_SESSION_CLEANUP_UNCONFIRMED' -and
        $null -eq $state.trace.completion.trace_write_error_code -and -not $state.trace_written) 'TEST_PORTS_UNASSIGNED_OWNER_NOT_CLEAN'
    $passed++

    $portsText=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'crossref-native-case-ports.ps1'))
    $ast=[Management.Automation.Language.Parser]::ParseInput($portsText,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'TEST_PORTS_PARSE'
    $stepFn=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $n.Name -ceq 'Invoke-P09XrefNativeCaseStep'},$false))[0]
    $switches=@($stepFn.FindAll({param($n) $n -is [Management.Automation.Language.SwitchStatementAst]},$true))
    $clauses=$switches[0].Clauses
    Assert-P09XrefBinding ($switches.Count -eq 1 -and $clauses.Count -eq 16 -and
        (($clauses | ForEach-Object {$_.Item1.Value}) -join ',') -ceq ((Get-P09XrefCaseFlowSteps) -join ',')) 'TEST_PORTS_ALL_FIXED_BRANCHES'
    $mapping=[ordered]@{create_save_session='New-P58Owner';source_open='Open-P58Document';source_bind='Observe-P09XrefOwnedActiveSource';
        opened_save='Save-P09XrefOpenedArtifact';opened_probe='Invoke-P09XrefStageProbe';sdk_insert='Invoke-P09XrefSdkInsertion';
        saved_save='Save-P09XrefPostInsertArtifact';saved_probe='Invoke-P09XrefStageProbe';save_session_close='Close-P09XrefNativeCaseOwner';
        create_reopen_session='New-P58Owner';fresh_saved_open='Open-P09XrefSavedInFreshSession';reopened_save='Save-P09XrefReopenedArtifact';
        reopened_probe='Invoke-P09XrefStageProbe';reopen_session_close='Close-P09XrefNativeCaseOwner';final_source_check='Assert-P58File';prepare_slot='Assert-P58File'}
    foreach ($clause in $clauses) {
        $commands=@($clause.Item2.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst]},$true) | ForEach-Object {$_.GetCommandName()})
        Assert-P09XrefBinding ($commands -ccontains $mapping[$clause.Item1.Value]) 'TEST_PORTS_FIXED_REAL_FUNCTION_BINDING'
    }
    $passed++

    Assert-P09XrefOriginalIoFunctions
    for ($i=1;$i -le 8;$i++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $i 'opened')))) 'TEST_PORTS_NATIVE_DIR_STILL_ABSENT'
    }
    Assert-P09XrefBinding ($null -eq ('P58OwnedWindowProcess' -as [type])) 'TEST_PORTS_NO_BRIDGE_ACTIVATED'
    $passed++
    [ordered]@{state='native_ports_eight_contracts_pass_native_not_run';passed=$passed;failed=0;
        native_session_started=$false;native_host_guard_qualified=$false;native_execution_authorized=$false;
        native_case_or_document_created=$false;accepted_count_delta=0;p09_complete=$false} | ConvertTo-Json -Depth 5 -Compress
} catch {
    [ordered]@{state='native_ports_contract_failed';passed=$passed;failed=1;error_type=$_.Exception.GetType().Name;
        source_line=$_.InvocationInfo.ScriptLineNumber;error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|STOP_[A-Z_]+)$') {
            $_.Exception.Message
        } else {'PORTS_TEST_FAILED_NO_RAW_VALUES'};native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Depth 4 -Compress
    exit 2
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
