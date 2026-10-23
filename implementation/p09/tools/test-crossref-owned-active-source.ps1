# No Hangul/COM session. Models and source guards do not qualify the runtime bridge.
[CmdletBinding()]
param([switch]$OwnerContractsOnly,[switch]$IdentityContractsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1')
$script:passed=0;$script:declared=0;$script:filtered=0
function New-P09XrefObservation {
    return [pscustomobject]@{owner_verified=$true;application_bound=$true;collection_bound=$true;
        document_bound=$true;document_application_bound=$true;document_count=[int]1;
        full_name_matches=$true;modified=[int]0;version_matches=$true;source_digest_matches=$true}
}
function Assert-P09XrefPairReject($Before,$After) {
    $rejected=$false
    try {[void](Assert-P09XrefActiveSourceObservations $Before $After)} catch {$rejected=$true}
    Assert-P09XrefBinding $rejected 'TEST_PAIR_MUST_REJECT'
}
function Invoke-P09XrefBindingTest([string]$Name,[scriptblock]$Body) {
    $script:declared++
    if ($IdentityContractsOnly -and $script:declared -le 10) {$script:filtered++;return}
    if ($OwnerContractsOnly -and $script:declared -le 7) {$script:filtered++;return}
    & $Body
    $script:passed++
}
try {
    Invoke-P09XrefBindingTest 'valid_paired_observation_is_not_an_execution_permit' {
        $receipt=Assert-P09XrefActiveSourceObservations (New-P09XrefObservation) (New-P09XrefObservation)
        Assert-P09XrefBinding ($receipt.paired_observations_validated -and -not $receipt.runtime_com_observed -and
            -not $receipt.native_target_qualified -and -not $receipt.native_execution_authorized -and
            -not $receipt.reusable_execution_permit -and -not $receipt.p09_complete) 'TEST_VALID_RECEIPT'
    }
    Invoke-P09XrefBindingTest 'every_identity_and_source_flag_is_typed_and_true' {
        foreach ($name in @('owner_verified','application_bound','collection_bound','document_bound',
                'document_application_bound','full_name_matches','version_matches','source_digest_matches')) {
            foreach ($value in @($false,1,'true')) {
                $before=New-P09XrefObservation;$before.$name=$value
                Assert-P09XrefPairReject $before (New-P09XrefObservation)
            }
        }
    }
    Invoke-P09XrefBindingTest 'second_snapshot_cannot_reuse_a_stale_first_success' {
        foreach ($name in @('owner_verified','application_bound','collection_bound','document_bound',
                'document_application_bound','full_name_matches','version_matches','source_digest_matches')) {
            $after=New-P09XrefObservation;$after.$name=$false
            Assert-P09XrefPairReject (New-P09XrefObservation) $after
        }
    }
    Invoke-P09XrefBindingTest 'exact_one_i4_document_count' {
        foreach ($value in @(0,2,[long]1,'1',$true,$null)) {
            $before=New-P09XrefObservation;$before.document_count=$value
            Assert-P09XrefPairReject $before (New-P09XrefObservation)
        }
    }
    Invoke-P09XrefBindingTest 'modified_i4_zero_is_not_coerced_from_bool_string_or_i8' {
        foreach ($value in @(-1,1,$false,'0',[long]0,$null)) {
            $before=New-P09XrefObservation;$before.modified=$value
            Assert-P09XrefPairReject $before (New-P09XrefObservation)
        }
    }
    Invoke-P09XrefBindingTest 'dirty_second_sample_rejects' {
        $after=New-P09XrefObservation;$after.modified=[int]1
        Assert-P09XrefPairReject (New-P09XrefObservation) $after
    }
    Invoke-P09XrefBindingTest 'missing_or_extra_observation_fields_reject' {
        $before=New-P09XrefObservation;$before.PSObject.Properties.Remove('document_bound')
        Assert-P09XrefPairReject $before (New-P09XrefObservation)
        $before=New-P09XrefObservation;$before | Add-Member authorization $true
        Assert-P09XrefPairReject $before (New-P09XrefObservation)
    }
    Invoke-P09XrefBindingTest 'preserved_owner_function_identity_is_exact' {
        Assert-P09XrefOriginalOwnerFunction
    }
    Invoke-P09XrefBindingTest 'a_replaced_owner_checker_is_not_accepted' {
        $original=(Get-Command Test-P58Owner -CommandType Function).ScriptBlock
        try {
            Set-Item -Path Function:Test-P58Owner -Value {return $true}
            $rejected=$false
            try {Assert-P09XrefOriginalOwnerFunction} catch {$rejected=$true}
            Assert-P09XrefBinding $rejected 'TEST_REPLACED_OWNER_CHECKER_ACCEPTED'
        } finally {Set-Item -Path Function:Test-P58Owner -Value $original}
        Assert-P09XrefOriginalOwnerFunction
    }
    Invoke-P09XrefBindingTest 'runtime_bridge_has_no_non_com_fallback' {
        $rejected=$false
        try {[void](Observe-P09XrefOwnedActiveSource ([pscustomobject]@{hwp=[object]::new();documents=[object]::new()}) ([object]::new()))}
        catch {$rejected=$_.Exception.Message -ceq 'P09_XREF_BIND_REAL_OWNED_COM_REQUIRED'}
        Assert-P09XrefBinding $rejected 'TEST_RUNTIME_NON_COM_FALLBACK'
    }
    Invoke-P09XrefBindingTest 'no_iunknown_is_acquired_for_plain_objects' {
        $pointers=[Collections.Generic.List[IntPtr]]::new();$rejected=$false
        try {[void](Get-P09XrefHeldComIdentity ([object]::new()) $pointers)} catch {$rejected=$true}
        Assert-P09XrefBinding ($rejected -and $pointers.Count -eq 0) 'TEST_NON_COM_IDENTITY'
    }
    Invoke-P09XrefBindingTest 'bridge_source_has_no_activation_action_or_document_write' {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1'),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'TEST_BRIDGE_SYNTAX'
        $text=$ast.Extent.Text
        Assert-P09XrefBinding ($text -cnotmatch '(?i)GetActiveObject|GetTypeFromProgID|CreateInstance|-ComObject|\.SaveAs\(|\.Execute\(|\.Quit\(|FileAccess\]::Write|FileMode\]::Create' -and
            $text -cnotmatch '\$Document\.(Modified|FullName)\s*=') 'TEST_NO_NATIVE_ACTION_OR_WRITE'
        $receipt=Assert-P09XrefActiveSourceObservations (New-P09XrefObservation) (New-P09XrefObservation)
        $encoded=$receipt | ConvertTo-Json -Compress
        Assert-P09XrefBinding ($encoded -cnotmatch 'source-with-bookmark|p09_crossref_discovery_anchor|IntPtr|process_id|FullName') 'TEST_REDACTED_RECEIPT'
    }
    Invoke-P09XrefBindingTest 'failed_identity_retention_has_an_explicit_release_branch_not_a_runtime_oom_claim' {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1'),[ref]$tokens,[ref]$errors)
        $function=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -ceq 'Get-P09XrefHeldComIdentity'},$false))
        Assert-P09XrefBinding (@($errors).Count -eq 0 -and $function.Count -eq 1) 'TEST_IDENTITY_FUNCTION_SOURCE'
        $tries=@($function[0].Body.FindAll({param($node) $node -is [Management.Automation.Language.TryStatementAst]},$true))
        Assert-P09XrefBinding ($tries.Count -eq 1 -and $tries[0].Body.Extent.Text.Contains('$Pointers.Add($pointer)') -and
            $tries[0].CatchClauses.Count -eq 1 -and $tries[0].CatchClauses[0].Body.Extent.Text.Contains('[Runtime.InteropServices.Marshal]::Release($pointer)') -and
            $tries[0].CatchClauses[0].Body.Extent.Text.Contains('throw')) 'TEST_ADDREF_RETENTION_FAILURE_RELEASE'
    }
    Assert-P09XrefBinding (-not ($OwnerContractsOnly -and $IdentityContractsOnly)) 'TEST_EXCLUSIVE_SELECTOR'
    $expected=if ($IdentityContractsOnly) {3} elseif ($OwnerContractsOnly) {6} else {13}
    Assert-P09XrefBinding ($script:passed -eq $expected -and $script:declared -eq 13 -and
        $script:filtered -eq (13-$expected)) 'TEST_EXACT_CONTRACT_COUNT'
    $state=if ($IdentityContractsOnly) {'three_identity_source_contracts_pass_runtime_not_run'} elseif ($OwnerContractsOnly) {'six_remaining_owned_active_source_contracts_pass_runtime_not_run'} else {'thirteen_owned_active_source_contracts_pass_runtime_not_run'}
    [ordered]@{state=$state;passed=$script:passed;failed=0;filtered=$script:filtered;declared=$script:declared;
        original_owner_checker_restored=$true;native_session_started=$false;runtime_bridge_on_real_com_executed=$false;
        native_target_qualified=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_CONTRACT_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='owned_active_source_contract_failed';passed=$script:passed;failed=1;error_code=$code;
        native_session_started=$false;runtime_bridge_on_real_com_executed=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
