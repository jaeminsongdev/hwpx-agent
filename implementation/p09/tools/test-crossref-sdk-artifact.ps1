# Source/model/rejection tests only. No native COM object is created or accepted as a mock.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-owned-artifact.ps1')
. (Join-Path $PSScriptRoot 'crossref-discovery-preflight-library.ps1')
. (Join-Path $PSScriptRoot 'crossref-sdk-insertion.ps1')
$script:passed=0
function New-P09XrefArtifactSample {
    return [pscustomobject]@{owner_verified=$true;application_bound=$true;collection_bound=$true;document_bound=$true;
        document_application_bound=$true;document_count=[int]1;full_name_matches=$true;modified=[int]0;
        version_matches=$true;source_digest_matches=$true}
}
function Assert-P09XrefTestReject([scriptblock]$Body) {
    $rejected=$false;try {& $Body} catch {$rejected=$true}
    Assert-P09XrefBinding $rejected 'TEST_EXPECTED_REJECTION'
}
function Invoke-P09XrefArtifactTest([scriptblock]$Body) {& $Body;$script:passed++}
function New-P09XrefOpenedProbe {
    return [pscustomobject]@{schema_version='hwpx-agent.private.crossref-worker-source-probe/v1';
        state='source_probe_completed_not_native_attestation';candidate_count=8;
        prepared_batch_sha256='1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1';
        observed_output_sha256=('a'*64);selected_case=[pscustomobject]@{case_id='P09-XREF-BOOK-C01';phase='opened';
            source_target_observation=[pscustomobject]@{observation='unique_exact_name_observed'}};
        native_execution_attested=$false;native_target_resolution_qualified=$false;parameter_key_semantics_qualified=$false;
        causal_insertion_or_preservation_proved=$false;complete_reference_validation_qualified=$false;
        native_execution_authorized=$false;raw_document_values_or_sdk_commands_present=$false;p09_complete=$false}
}
try {
    Invoke-P09XrefArtifactTest {
        for ($i=1;$i -le 8;$i++) {foreach ($point in @('opened_clean','opened_after_insert','saved_clean','reopened_clean')) {
            $scope=Get-P09XrefArtifactScope $i $point ('a'*64)
            Assert-P09XrefBinding ($scope.case_id -ceq ('P09-XREF-BOOK-C'+$i.ToString('00')) -and
                $scope.path.EndsWith(('c'+$i.ToString('00')+'-attempt01\'+$scope.stage+'.hwpx').Replace('\',[IO.Path]::DirectorySeparatorChar))) 'TEST_FIXED_MATRIX'
        }}
        Assert-P09XrefTestReject {Get-P09XrefArtifactScope 0 'saved_clean' ('a'*64)}
        Assert-P09XrefTestReject {Get-P09XrefArtifactScope 9 'saved_clean' ('a'*64)}
        Assert-P09XrefTestReject {Get-P09XrefArtifactScope 1 '../saved' ('a'*64)}
        Assert-P09XrefTestReject {Get-P09XrefArtifactScope 1 'saved_clean' ('A'*64)}
    }
    Invoke-P09XrefArtifactTest {
        foreach ($point in @('opened_clean','saved_clean','reopened_clean')) {
            $scope=Get-P09XrefArtifactScope 1 $point ('a'*64)
            [void](Assert-P09XrefArtifactObservations (New-P09XrefArtifactSample) (New-P09XrefArtifactSample) $scope)
            foreach ($value in @(1,-1,$false,'0',[long]0)) {
                $sample=New-P09XrefArtifactSample;$sample.modified=$value
                Assert-P09XrefTestReject {Assert-P09XrefArtifactObservations $sample (New-P09XrefArtifactSample) $scope}
            }
        }
    }
    Invoke-P09XrefArtifactTest {
        $scope=Get-P09XrefArtifactScope 1 'opened_after_insert' ('a'*64)
        foreach ($value in @([int]-1,[int]0,[int]1)) {
            $sample=New-P09XrefArtifactSample;$sample.modified=$value
            $receipt=Assert-P09XrefArtifactObservations $sample $sample $scope
            Assert-P09XrefBinding (-not $receipt.runtime_com_observed -and -not $receipt.reusable_execution_permit -and
                -not $receipt.native_target_resolution_qualified -and -not $receipt.causal_insertion_or_preservation_proved) 'TEST_POST_INSERT_NOT_ACCEPTANCE'
        }
        $sample=New-P09XrefArtifactSample;$sample.modified=$true
        Assert-P09XrefTestReject {Assert-P09XrefArtifactObservations $sample $sample $scope}
    }
    Invoke-P09XrefArtifactTest {
        $scope=Get-P09XrefArtifactScope 1 'saved_clean' ('a'*64)
        foreach ($name in @('owner_verified','application_bound','collection_bound','document_bound','document_application_bound',
                'full_name_matches','version_matches','source_digest_matches')) {
            $after=New-P09XrefArtifactSample;$after.$name=$false
            Assert-P09XrefTestReject {Assert-P09XrefArtifactObservations (New-P09XrefArtifactSample) $after $scope}
        }
        $sample=New-P09XrefArtifactSample;$sample.document_count=2
        Assert-P09XrefTestReject {Assert-P09XrefArtifactObservations $sample $sample $scope}
    }
    Invoke-P09XrefArtifactTest {
        for ($i=1;$i -le 8;$i++) {
            $case=Get-P09XrefFixedSdkCase $i
            $expected='?p09_crossref_discovery_anchor;6;'+[int][Math]::Floor(($i-1)/2)+';'+(($i-1)%2)+';0'
            Assert-P09XrefBinding ($case.case_id -ceq ('P09-XREF-BOOK-C'+$i.ToString('00')) -and $case.sdk_command -ceq $expected) 'TEST_FROZEN_PACKET_CASE'
        }
        Assert-P09XrefTestReject {Get-P09XrefFixedSdkCase 0}
    }
    Invoke-P09XrefArtifactTest {
        Assert-P09XrefOpenedProbe (New-P09XrefOpenedProbe) 1 ('a'*64)
        $probe=New-P09XrefOpenedProbe;$probe.selected_case.phase='saved'
        Assert-P09XrefTestReject {Assert-P09XrefOpenedProbe $probe 1 ('a'*64)}
        $probe=New-P09XrefOpenedProbe;$probe.native_execution_attested=$true
        Assert-P09XrefTestReject {Assert-P09XrefOpenedProbe $probe 1 ('a'*64)}
        Assert-P09XrefTestReject {Assert-P09XrefOpenedProbe (New-P09XrefOpenedProbe) 2 ('a'*64)}
        Assert-P09XrefTestReject {Assert-P09XrefOpenedProbe (New-P09XrefOpenedProbe) 1 ('b'*64)}
    }
    Invoke-P09XrefArtifactTest {
        $record=[ordered]@{};$owner=[pscustomobject]@{hwp=[object]::new();documents=[object]::new()}
        Assert-P09XrefTestReject {Invoke-P09XrefSdkInsertion $owner ([object]::new()) 1 ('a'*64) (New-P09XrefOpenedProbe) $record}
        Assert-P09XrefBinding ($record.phase -ceq 'input_binding' -and -not $record.execute_invoked -and
            -not $record.effect_unknown -and $record.error_code -ceq 'P09_XREF_BIND_ARTIFACT_REAL_COM_REQUIRED') 'TEST_NO_MOCK_RUNTIME_FALLBACK'
    }
    Invoke-P09XrefArtifactTest {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-sdk-insertion.ps1'),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'TEST_SDK_SYNTAX'
        $text=$ast.Extent.Text
        Assert-P09XrefBinding ($text.Contains(".GetDefault('InsertCrossReference',`$set)") -and
            $text.Contains(".Execute('InsertCrossReference',`$set)") -and $text.Contains('$parameters.HActionCrossRef') -and
            $text.Contains('$crossref.Command=$case.sdk_command')) 'TEST_DECLARED_SDK_CALL_SURFACE'
        $intent=$text.IndexOf('$Record.execute_invoked=$true',[StringComparison]::Ordinal)
        $execute=$text.IndexOf(".Execute('InsertCrossReference'",[StringComparison]::Ordinal)
        Assert-P09XrefBinding ($intent -ge 0 -and $intent -lt $execute -and
            $text -cnotmatch '(?i)New-Object|-ComObject|GetActiveObject|\.SaveAs\(|\.Quit\(') 'TEST_INTENT_BEFORE_EXECUTE_NO_ACTIVATION'
        $tokens=$null;$errors=$null
        $artifact=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-owned-artifact.ps1'),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0 -and $artifact.Extent.Text -cnotmatch '(?i)FileAccess\]::Write|FileMode\]::Create|\.Modified\s*=|SetActive_XHwpDocument') 'TEST_READ_ONLY_ARTIFACT_BRIDGE'
    }
    Assert-P09XrefBinding ($script:passed -eq 8) 'TEST_EXACT_EIGHT_SDK_ARTIFACT'
    [ordered]@{state='eight_sdk_artifact_source_model_contracts_pass_native_not_run';passed=$script:passed;failed=0;
        actual_com_sdk_execute_invoked=$false;native_session_started=$false;native_target_qualified=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_TEST_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='sdk_artifact_contract_failed';passed=$script:passed;failed=1;error_code=$code;
        actual_com_sdk_execute_invoked=$false;native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
