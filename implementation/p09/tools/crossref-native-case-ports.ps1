# Concrete private native ports; no CLI/approval route. Host admission/resource
# callbacks and independent producer/cleanup qualification remain required.
Set-StrictMode -Version Latest

function Read-P09XrefFrozenNativeHarness {
    $path=Join-Path $PSScriptRoot 'run-hancom-2020-sdk-baseline-capture.ps1'
    $item=Get-Item -LiteralPath $path -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -le 65536 -and
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PORTS_HARNESS_BOUNDARY'
    $bytes=[IO.File]::ReadAllBytes($path)
    Assert-P09XrefBinding ((Get-P09XrefFreshDigest $bytes) -ceq
        '695a35cb982a671b8614eee3407d6e00f0ef710eab0ee46c2a81b78e2a2469fd') 'PORTS_HARNESS_SHA'
    return [Text.UTF8Encoding]::new($false,$true).GetString($bytes)
}

function Import-P09XrefFrozenIoHelpers {
    $source=Read-P09XrefFrozenNativeHarness;$tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'PORTS_HARNESS_PARSE'
    foreach ($name in @('Assert-P58File','Write-P58Trace')) {
        $found=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -ceq $name},$false))
        Assert-P09XrefBinding ($found.Count -eq 1) 'PORTS_IO_HELPER_INVENTORY'
        $inner=$found[0].Body.Extent.Text.Substring(1,$found[0].Body.Extent.Text.Length-2)
        $existing=Get-Command $name -CommandType Function -ErrorAction SilentlyContinue
        if ($null -ne $existing) {
            Assert-P09XrefBinding ($existing.ScriptBlock.ToString() -ceq $inner) 'PORTS_IO_HELPER_REPLACED'
        } else {
            # Process-local functions only; no source/registry/trust-store changes.
            Set-Item -Path ('Function:global:'+$name) -Value ([scriptblock]::Create($inner))
        }
    }
}

function Initialize-P09XrefFrozenWindowBridge {
    if ($null -ne ('P58OwnedWindowProcess' -as [type])) {return}
    $source=Read-P09XrefFrozenNativeHarness
    $begin="Add-Type -TypeDefinition @'";$end="'@"
    $at=$source.IndexOf($begin,[StringComparison]::Ordinal)
    Assert-P09XrefBinding ($at -ge 0 -and $source.IndexOf($begin,$at+$begin.Length,[StringComparison]::Ordinal) -lt 0) 'PORTS_WINDOW_TYPE_BOUNDARY'
    $finish=$source.IndexOf($end,$at+$begin.Length,[StringComparison]::Ordinal)
    Assert-P09XrefBinding ($finish -gt $at) 'PORTS_WINDOW_TYPE_END'
    # Only the frozen class declaration, never the original harness main/native branch.
    [void](& ([scriptblock]::Create($source.Substring($at,$finish+$end.Length-$at))))
}

function New-P09XrefNativeCaseState {
    param([Parameter(Mandatory)][int]$CaseIndex,[Parameter(Mandatory)]$ProbeLease,
        [Parameter(Mandatory)][scriptblock]$HostCheckpoint,[Parameter(Mandatory)][scriptblock]$AdmitOwnedProcess)
    $path=Get-P09XrefCaseArtifactPath $CaseIndex 'opened'
    Assert-P09XrefBinding (-not $ProbeLease.closed -and $ProbeLease.stream -is [IO.FileStream] -and
        $ProbeLease.stream.CanRead) 'PORTS_LIVE_PROBE_LEASE'
    Assert-P09XrefOriginalIoFunctions
    Import-P09XrefFrozenIoHelpers
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $trace=[ordered]@{schema_version='hwpx-agent.private.crossref-native-case-trace/v1';
        case_id=('P09-XREF-BOOK-C'+$CaseIndex.ToString('00'));state='unstarted_effect_unattested';
        source_sha256='64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184';
        sessions=[Collections.ArrayList]::new();artifacts=[ordered]@{};operations=[ordered]@{};
        producer_events=[Collections.Generic.List[object]]::new();cleanup_events=[Collections.Generic.List[object]]::new();
        source_identity_preserved=$false;producer_binding_qualified=$false;native_host_guard_qualified=$false;p09_complete=$false}
    return [ordered]@{case_index=$CaseIndex;root=$root;run=(Split-Path -Parent $path);
        source=(Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx');
        source_sha256=$trace.source_sha256;trace=$trace;probe_lease=$ProbeLease;
        host_checkpoint=$HostCheckpoint;admit_owned_process=$AdmitOwnedProcess;
        owner=$null;document=$null;previous_identity=$null;close_attempted=$false;
        slot_created=$false;trace_written=$false;completion_attempted=$false;failed=$false;next_step_index=0;probe_responses=[ordered]@{}}
}

function Assert-P09XrefNativeSessionsClean($State) {
    foreach ($session in $State.trace.sessions) {
        Assert-P09XrefBinding ($null -ne $session.process -and $null -eq $session.cleanup_error -and
            $session.quit_invoked -eq $true -and $session.close_without_dirty_prompt_returned -eq $true -and
            $session.remaining_owned_process_count -eq 0) 'PORTS_SESSION_CLEANUP_UNCONFIRMED'
    }
}

function Close-P09XrefNativeCaseOwner($State) {
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    if ($null -eq $State.owner) {Assert-P09XrefNativeSessionsClean $State;return}
    Assert-P09XrefBinding (-not $State.close_attempted) 'PORTS_NO_CLEANUP_RETRY'
    $State.close_attempted=$true
    $owner=$State.owner
    $cleanup=[ordered]@{session_identity=$owner.identity;close_attempted=$true;close_returned=$false;document_release_returned=$false}
    [void]$State.trace.cleanup_events.Add($cleanup)
    try {
        if ($null -ne $State.document) {
            try {Release-P58Com $State.document;$cleanup.document_release_returned=$true}
            finally {$State.document=$null}
        } else {$cleanup.document_release_returned=$true}
    } finally {
        # Even a document-release error must reach verified-owner cleanup once.
        try {Close-P58Owner $owner;$cleanup.close_returned=$true}
        finally {$State.owner=$null}
    }
    Assert-P09XrefNativeSessionsClean $State
}

function Add-P09XrefProducerEvent($State,[string]$Stage,$Pin) {
    Assert-P09XrefBinding ($Stage -cin @('opened','saved','reopened') -and $null -ne $State.owner.identity -and
        $Pin.sha256 -cmatch '^[0-9a-f]{64}$' -and $Pin.bytes -gt 0 -and $Pin.bytes -le 4194304) 'PORTS_PRODUCER_EVENT'
    [void]$State.trace.producer_events.Add([ordered]@{stage=$Stage;artifact_sha256=$Pin.sha256;artifact_bytes=$Pin.bytes;
        observed_owner_identity=$State.owner.identity;source_observation_only=$false;producer_binding_qualified=$false})
}

function Invoke-P09XrefNativeCaseStep {
    param([Parameter(Mandatory)][string]$Step,[Parameter(Mandatory)][System.Collections.IDictionary]$State)
    $steps=Get-P09XrefCaseFlowSteps
    Assert-P09XrefBinding (-not $State.failed -and $State.next_step_index -lt $steps.Count -and
        $Step -ceq $steps[$State.next_step_index]) 'PORTS_ORDER_OR_RETRY'
    # These are trusted program dependencies, not approval booleans or user data.
    # No native entry provides them until original host protection/admission is qualified.
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    $exeSha='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    $securityName='FilePathCheckerModuleExample'
    try {
        [void](& $State.host_checkpoint $Step $State)
        switch -CaseSensitive ($Step) {
            'prepare_slot' {
                [void](Assert-P58File $State.source 4194304 $State.source_sha256)
                $parent=Get-Item -LiteralPath (Split-Path -Parent $State.run) -Force
                while ($null -ne $parent) {
                    Assert-P09XrefBinding ($parent -is [IO.DirectoryInfo] -and
                        ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PORTS_OUTPUT_PARENT'
                    $parent=$parent.Parent
                }
                Assert-P09XrefBinding (-not (Test-Path -LiteralPath $State.run)) 'PORTS_ATTEMPT_ALREADY_EXISTS'
                [void](New-Item -ItemType Directory -Path $State.run -ErrorAction Stop)
                $State.slot_created=$true;$State.trace.state='started_effect_unattested'
            }
            'create_save_session' {
                Initialize-P09XrefFrozenWindowBridge
                $State.owner=New-P58Owner 'save' $State.trace;$State.close_attempted=$false
                [void](& $State.admit_owned_process $State.owner $State)
            }
            'source_open' {$State.document=Open-P58Document $State.owner $State.source $State.source_sha256}
            'source_bind' {[void](Observe-P09XrefOwnedActiveSource $State.owner $State.document)}
            'opened_save' {
                $record=[ordered]@{};$State.trace.operations.opened_save=$record
                $pin=Save-P09XrefOpenedArtifact $State.owner $State.document $State.case_index $record
                $State.trace.artifacts.opened=$pin;Add-P09XrefProducerEvent $State 'opened' $pin
            }
            'opened_probe' {
                $record=[ordered]@{};$State.trace.operations.opened_probe=$record
                $State.probe_responses.opened=Invoke-P09XrefStageProbe $State.probe_lease $State.case_index 'opened' $State.trace.artifacts.opened.sha256 $record
            }
            'sdk_insert' {
                $record=[ordered]@{};$State.trace.operations.sdk_insert=$record
                [void](Invoke-P09XrefSdkInsertion $State.owner $State.document $State.case_index $State.trace.artifacts.opened.sha256 $State.probe_responses.opened $record)
            }
            'saved_save' {
                $record=[ordered]@{};$State.trace.operations.saved_save=$record
                $pin=Save-P09XrefPostInsertArtifact $State.owner $State.document $State.case_index $State.trace.artifacts.opened.sha256 $record
                $State.trace.artifacts.saved=$pin;Add-P09XrefProducerEvent $State 'saved' $pin
            }
            'saved_probe' {
                $record=[ordered]@{};$State.trace.operations.saved_probe=$record
                $State.probe_responses.saved=Invoke-P09XrefStageProbe $State.probe_lease $State.case_index 'saved' $State.trace.artifacts.saved.sha256 $record
            }
            'save_session_close' {$State.previous_identity=$State.owner.identity;Close-P09XrefNativeCaseOwner $State}
            'create_reopen_session' {
                Assert-P09XrefNativeSessionsClean $State
                $State.owner=New-P58Owner 'reopen' $State.trace;$State.close_attempted=$false
                [void](& $State.admit_owned_process $State.owner $State)
            }
            'fresh_saved_open' {
                $record=[ordered]@{};$State.trace.operations.fresh_saved_open=$record
                $State.document=Open-P09XrefSavedInFreshSession $State.owner $State.previous_identity $State.case_index $State.trace.artifacts.saved.sha256 $record
            }
            'reopened_save' {
                $record=[ordered]@{};$State.trace.operations.reopened_save=$record
                $pin=Save-P09XrefReopenedArtifact $State.owner $State.document $State.case_index $State.trace.artifacts.saved.sha256 $record
                $State.trace.artifacts.reopened=$pin;Add-P09XrefProducerEvent $State 'reopened' $pin
            }
            'reopened_probe' {
                $record=[ordered]@{};$State.trace.operations.reopened_probe=$record
                $State.probe_responses.reopened=Invoke-P09XrefStageProbe $State.probe_lease $State.case_index 'reopened' $State.trace.artifacts.reopened.sha256 $record
            }
            'reopen_session_close' {Close-P09XrefNativeCaseOwner $State}
            'final_source_check' {
                [void](Assert-P58File $State.source 4194304 $State.source_sha256)
                foreach ($stage in @('opened','saved','reopened')) {
                    [void](Assert-P58File (Get-P09XrefCaseArtifactPath $State.case_index $stage) 4194304 $State.trace.artifacts[$stage].sha256)
                }
                $State.trace.source_identity_preserved=$true
                $State.trace.state='lifecycle_callbacks_returned_semantics_unqualified'
            }
            default {throw 'P09_XREF_BIND_PORTS_UNKNOWN_STEP'}
        }
        $State.next_step_index++
    } catch {$State.failed=$true;throw}
}

function Complete-P09XrefNativeCasePorts($State) {
    Assert-P09XrefBinding (-not $State.completion_attempted) 'PORTS_NO_COMPLETION_RETRY'
    $State.completion_attempted=$true
    $State.trace.completion=[ordered]@{cleanup_error_code=$null;trace_write_error_code=$null;trace_write_returned=$false}
    try {Close-P09XrefNativeCaseOwner $State} catch {
        $State.trace.completion.cleanup_error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {
            $_.Exception.Message
        } else {'P09_XREF_BIND_PORTS_CLEANUP_FAILED_NO_RAW_VALUES'}
    }
    try {
        if ($State.slot_created -and -not $State.trace_written) {
            $State.trace.probe_observations=$State.probe_responses
            $State.trace.trace_write_attempted=$true;$State.trace_written=$true # Never replay an uncertain write.
            Write-P58Trace (Join-Path $State.run 'target-trace.json') $State.trace
            $State.trace.completion.trace_write_returned=$true
        }
    } catch {
        # Retain both errors in caller state; a failed writer must not hide cleanup failure.
        $State.trace.completion.trace_write_error_code='P09_XREF_BIND_PORTS_TRACE_WRITE_FAILED_NO_RAW_VALUES'
    }
    if ($null -ne $State.trace.completion.cleanup_error_code -or $null -ne $State.trace.completion.trace_write_error_code) {
        throw 'P09_XREF_BIND_PORTS_COMPLETION_FAILED'
    }
}

function Invoke-P09XrefNativeCaseWorkflow {
    param([Parameter(Mandatory)][System.Collections.IDictionary]$State,
        [Parameter(Mandatory)][System.Collections.IDictionary]$FlowRecord)
    Invoke-P09XrefCaseFlow $State.case_index {param($step,$state) Invoke-P09XrefNativeCaseStep $step $state} `
        {param($state) Complete-P09XrefNativeCasePorts $state} $State $FlowRecord
}
