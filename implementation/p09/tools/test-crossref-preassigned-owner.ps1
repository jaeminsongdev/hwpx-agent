# Controlled managed leases and original AST successor only. Never Attach/ROT/COM.
[CmdletBinding()]
param([switch]$ModelsOnly,[switch]$InitializeOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (($ModelsOnly -and $InitializeOnly) -or (-not $ModelsOnly -and -not $InitializeOnly)) {throw 'P09_XREF_BIND_PREASSIGNED_CLOSED_TEST_MODE'}
foreach ($name in @('crossref-owned-active-source','sdk-baseline-owned-session','crossref-case-flow','crossref-native-case-ports',
    'crossref-dual-owner-identity','crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-preassigned-case-ports')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}

function Assert-PreassignedModelReject([scriptblock]$Body,[string]$Code) {
    $rejected=$false
    try {[void](& $Body)} catch {$rejected=($_.Exception.GetBaseException().Message -ceq ('P09_XREF_BIND_'+$Code))}
    Assert-P09XrefBinding $rejected 'PREASSIGNED_MODEL_EXPECTED_CLOSED_REJECTION'
}
function New-PreassignedModelDescriptor {
    return [ordered]@{profile='hwpx-agent.private.crossref-preassigned-session-scope/v1';case_index=1;session_label='save';
        process_id=101;session_id=1;created_at_utc=[datetime]::FromFileTimeUtc(133000000000000001L).ToString('o');
        executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';source='current_exact_preassigned_process_handle';
        COM_owner_bound=$false;native_execution_authorized=$false;native_startup_qualified=$false;P09_complete=$false}
}
function New-PreassignedModelOwner([bool]$Fail) {
    $lease=[P09CrossrefExisting.PreassignedLeaseModels]::CreateLease($Fail)
    return [ordered]@{hwp=$lease.Application;windows=$lease.Windows;window=$lease.Window;documents=$null;verified=$false;identity=$null;
        trace=[ordered]@{cleanup_error=$null;close_without_dirty_prompt_returned=$false;quit_invoked=$false;remaining_owned_process_count=$null};
        preassigned_lease=$lease;preassigned_release_attempted=$false;preassigned_release_returned=$false;
        preassigned_close_attempted=$false;preassigned_closed=$false;preassigned_admitted=$false}
}
function New-PreassignedModelState {
    return [ordered]@{owner=(New-PreassignedModelOwner $false);document=$null;close_attempted=$false;completion_attempted=$false;
        slot_created=$false;trace_written=$false;trace=[ordered]@{sessions=[Collections.ArrayList]::new();cleanup_events=[Collections.ArrayList]::new()}}
}

try {
    if ($InitializeOnly) {
        Assert-PreassignedModelReject {Assert-P09XrefExistingOwnerAdapterReady} 'PREASSIGNED_ADAPTER_PREWARM_REQUIRED'
        Initialize-P09XrefExistingOwnerAdapter
        Assert-P09XrefExistingOwnerAdapterReady
        $first='P09CrossrefExisting.ExistingOwner' -as [type]
        Initialize-P09XrefExistingOwnerAdapter
        Assert-P09XrefBinding ([object]::ReferenceEquals($first,('P09CrossrefExisting.ExistingOwner' -as [type]))) 'PREASSIGNED_MODEL_SAME_COMPILED_TYPE'
        [Console]::WriteLine('test preassigned_owner::actual_adapter_initialize_idempotent ... ok')
        [Console]::WriteLine('test result: ok. 1 passed; 0 failed; 0 ignored; compile_only_not_ROT_COM_or_Native')
        exit 0
    }
    # Compile original adapter with the new controlled fake candidate in the same
    # assembly. This test-only ownership ledger never authorizes Native execution.
    $core=Read-P09XrefPreassignedFixedSource 'crossref-existing-owner.cs'
    $models=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'test-crossref-preassigned-owner.cs'))
    Add-Type -TypeDefinition ($core+"`n"+$models.Replace('using System;',''))
    Assert-PreassignedModelReject {Initialize-P09XrefExistingOwnerAdapter} 'PREASSIGNED_ADAPTER_TYPE_NOT_OWNED'
    $script:P09XrefExistingOwnerOwnedType='P09CrossrefExisting.ExistingOwner' -as [type]
    Initialize-P09XrefExistingOwnerAdapter
    [Console]::WriteLine('test preassigned_owner::unowned_type_rejected ... ok')

    $definitions=@(Get-P09XrefPreassignedPortDefinitions)
    Assert-P09XrefBinding ($definitions.Count -eq 4) 'PREASSIGNED_MODEL_EXACT_FOUR_PORTS'
    foreach ($d in $definitions) {
        $restored=$d.changed;$rules=@($d.rewrites)
        for ($i=$rules.Count-1;$i -ge 0;$i--) {$restored=$restored.Replace($rules[$i][1],$rules[$i][0])}
        Assert-P09XrefBinding ($restored -ceq $d.original) 'PREASSIGNED_MODEL_EXACT_PORT_INVERSE'
    }
    [Console]::WriteLine('test preassigned_owner::four_exact_inverse_ports ... ok')
    $before=(Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()
    Initialize-P09XrefPreassignedCasePorts;Initialize-P09XrefPreassignedCasePorts
    Assert-P09XrefBinding ($before -ceq (Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()) 'PREASSIGNED_MODEL_ORIGINAL_UNCHANGED'
    foreach ($d in $definitions) {Assert-P09XrefBinding ((Get-Command $d.name).ScriptBlock.ToString() -ceq $d.inner) 'PREASSIGNED_MODEL_EXACT_SUCCESSOR'}
    [Console]::WriteLine('test preassigned_owner::successor_install_keeps_original ... ok')
    Assert-P09XrefOriginalOwnerFunction
    [Console]::WriteLine('test preassigned_owner::original_p58_predicate_preserved ... ok')

    $d=New-PreassignedModelDescriptor;$expected=Convert-P09XrefPreassignedExpectedOwner $d 1 'save'
    Assert-P09XrefBinding ($expected.Pid -eq 101 -and $expected.Session -eq 1 -and $expected.Birth -eq 133000000000000001L) 'PREASSIGNED_MODEL_EXACT_TICK'
    [Console]::WriteLine('test preassigned_owner::descriptor_tick_not_cim_rounding ... ok')
    $d['native_execution_authorized']=$true
    Assert-PreassignedModelReject {Convert-P09XrefPreassignedExpectedOwner $d 1 'save'} 'V2_DESCRIPTOR_NO_AUTHORITY'
    [Console]::WriteLine('test preassigned_owner::descriptor_authority_rejected ... ok')
    $state=[ordered]@{owner=$null;current_descriptor=$null;preassigned_channel=[ordered]@{pending_descriptor=$null}}
    Assert-PreassignedModelReject {Connect-P09XrefPreassignedOwner $state 'save'} 'PREASSIGNED_CURRENT_PENDING_DESCRIPTOR'
    Assert-P09XrefBinding ($null -eq $state.owner) 'PREASSIGNED_MODEL_NO_ATTACH_OWNER'
    [Console]::WriteLine('test preassigned_owner::no_descriptor_rejected_before_attach ... ok')

    $owner=New-PreassignedModelOwner $false;Release-P09XrefPreassignedReferences $owner
    Assert-P09XrefBinding ([P09CrossrefExisting.PreassignedLeaseModels]::Disposals -eq 1 -and $owner.preassigned_release_returned -and
        $null -eq $owner.preassigned_lease -and $null -eq $owner.hwp -and $null -eq $owner.windows -and $null -eq $owner.window) 'PREASSIGNED_MODEL_SINGLE_LEASE_DISPOSE'
    [Console]::WriteLine('test preassigned_owner::lease_references_released_once ... ok')
    Assert-PreassignedModelReject {Release-P09XrefPreassignedReferences $owner} 'PREASSIGNED_NO_REFERENCE_RELEASE_RETRY'
    Assert-P09XrefBinding ([P09CrossrefExisting.PreassignedLeaseModels]::Disposals -eq 1) 'PREASSIGNED_MODEL_NO_DOUBLE_DISPOSE'
    [Console]::WriteLine('test preassigned_owner::second_release_rejected ... ok')
    $owner=New-PreassignedModelOwner $true;$lease=$owner.preassigned_lease
    Assert-PreassignedModelReject {Release-P09XrefPreassignedReferences $owner} 'PREASSIGNED_REFERENCE_RELEASE_FAILED'
    Assert-P09XrefBinding ([object]::ReferenceEquals($lease,$owner.preassigned_lease) -and $owner.preassigned_release_attempted -and
        -not $owner.preassigned_release_returned -and [P09CrossrefExisting.PreassignedLeaseModels]::Disposals -eq 1) 'PREASSIGNED_MODEL_FAILED_LEASE_RETAINED'
    Assert-PreassignedModelReject {Release-P09XrefPreassignedReferences $owner} 'PREASSIGNED_NO_REFERENCE_RELEASE_RETRY'
    [Console]::WriteLine('test preassigned_owner::failed_release_retained_no_retry ... ok')
    $owner=New-PreassignedModelOwner $false;$owner.documents=[object]::new()
    Assert-PreassignedModelReject {Release-P09XrefPreassignedReferences $owner} 'PREASSIGNED_REFERENCE_RELEASE_FAILED'
    Assert-P09XrefBinding ($null -ne $owner.preassigned_failed_document_reference -and
        [P09CrossrefExisting.PreassignedLeaseModels]::Disposals -eq 1 -and -not $owner.preassigned_release_returned) 'PREASSIGNED_MODEL_LEASE_CLEANUP_AFTER_DOC_ERROR'
    [Console]::WriteLine('test preassigned_owner::document_failure_still_disposes_lease ... ok')
    $owner=New-PreassignedModelOwner $false
    Assert-PreassignedModelReject {Assert-P09XrefPreassignedOwnerAnchor $owner} 'PREASSIGNED_EXACT_RETAINED_COM_LEASE'
    Release-P09XrefPreassignedReferences $owner
    [Console]::WriteLine('test preassigned_owner::managed_lease_never_com_authority ... ok')

    $d=New-PreassignedModelDescriptor;$identity=[ordered]@{process_id=101;session_id=1;created_at_utc=$d.created_at_utc;
        executable_sha256=$d.executable_sha256;window_handle_binds_exact_process=$true}
    $owner=[ordered]@{identity=[ordered]@{created_at_utc='PRESERVED_CIM_ORIGINAL'};window=[object]::new()}
    $observed=[ordered]@{compatibility_kind='original_p58_identity';kernel_creation_not_derived_from_cim=$true;
        kernel_before_after_same_handle_equal=$true;kernel_window_verified=$true;native_execution_authorized=$false;p09_complete=$false;kernel_identity=$identity}
    $proxy=New-P09XrefPreassignedAdmissionProxy $owner $observed $d
    Assert-P09XrefBinding ([object]::ReferenceEquals($proxy.identity,$identity) -and
        $owner.identity.created_at_utc -ceq 'PRESERVED_CIM_ORIGINAL') 'PREASSIGNED_MODEL_CIM_NOT_OVERWRITTEN'
    [Console]::WriteLine('test preassigned_owner::canonical_proxy_preserves_cim ... ok')
    $identity['created_at_utc']=[datetime]::FromFileTimeUtc(133000000000000002L).ToString('o')
    Assert-PreassignedModelReject {New-P09XrefPreassignedAdmissionProxy $owner $observed $d} 'PREASSIGNED_EXACT_CANONICAL_PENDING_OWNER'
    [Console]::WriteLine('test preassigned_owner::canonical_one_tick_mismatch_rejected ... ok')

    $state=New-PreassignedModelState;$owner=$state.owner
    Assert-PreassignedModelReject {Close-P09XrefPreassignedCaseOwner $state} 'PREASSIGNED_OWNED_CLEANUP_UNCONFIRMED'
    Assert-P09XrefBinding ([object]::ReferenceEquals($state.owner,$owner) -and $state.close_attempted -and -not $owner.preassigned_closed -and
        -not $owner.trace.quit_invoked -and $owner.preassigned_release_returned) 'PREASSIGNED_MODEL_UNCERTAIN_OWNER_RETAINED'
    [Console]::WriteLine('test preassigned_owner::case_cleanup_retains_unverified_owner ... ok')
    Assert-PreassignedModelReject {Close-P09XrefPreassignedCaseOwner $state} 'PORTS_NO_CLEANUP_RETRY'
    [Console]::WriteLine('test preassigned_owner::case_cleanup_no_second_quit ... ok')
    $state=New-PreassignedModelState;$owner=$state.owner
    Assert-PreassignedModelReject {Complete-P09XrefPreassignedCasePorts $state} 'PORTS_COMPLETION_FAILED'
    Assert-P09XrefBinding ([object]::ReferenceEquals($state.owner,$owner) -and $null -ne $state.trace.completion.cleanup_error_code -and
        -not $state.trace.completion.trace_write_returned -and $null -eq $state.trace.completion.trace_write_error_code) 'PREASSIGNED_MODEL_COMPLETION_RETENTION'
    [Console]::WriteLine('test preassigned_owner::completion_keeps_cleanup_failure ... ok')
    # Reopen follows a closed save owner. Reset the case cleanup latch BEFORE a
    # fallible new connection, so its retained partial owner can still be cleaned.
    $state=[ordered]@{failed=$false;next_step_index=10;close_attempted=$true;owner=$null;case_index=1;current_descriptor=$null;
        preassigned_channel=[ordered]@{pending_descriptor=$null};trace=[ordered]@{sessions=[Collections.ArrayList]::new()};
        host_checkpoint={param($step,$state)}}
    Assert-PreassignedModelReject {Invoke-P09XrefPreassignedCaseStep 'create_reopen_session' $state} 'PREASSIGNED_CURRENT_PENDING_DESCRIPTOR'
    Assert-P09XrefBinding (-not $state.close_attempted -and $state.failed -and $null -eq $state.owner) 'PREASSIGNED_MODEL_REOPEN_CLEANUP_LATCH_RESET'
    [Console]::WriteLine('test preassigned_owner::reopen_failure_does_not_inherit_closed_latch ... ok')
    [Console]::WriteLine('test result: ok. 18 passed; 0 failed; 0 ignored; managed_leases_ports_only_not_ROT_COM_or_Native')
} catch {
    $detail=[string]$_.Exception.Message
    if ($null -ne $_.ErrorDetails) {$detail+=[string]$_.ErrorDetails.Message}
    foreach ($match in [regex]::Matches($detail,'\bCS[0-9]{4}\b')) {[Console]::Error.WriteLine(('Error: '+$match.Value))}
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_PREASSIGNED_OWNER_TEST_FAILED_NO_RAW_VALUES'}
    if ($null -ne $_.InvocationInfo -and $_.InvocationInfo.ScriptLineNumber -gt 0) {
        [Console]::Error.WriteLine(('Error: P09_XREF_BIND_TEST_LINE_'+$_.InvocationInfo.ScriptLineNumber))
    }
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
