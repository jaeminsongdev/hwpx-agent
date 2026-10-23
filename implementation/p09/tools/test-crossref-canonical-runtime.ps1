# Fixed readonly denial + in-memory sidecar contracts. No native attempt/fixtures.
[CmdletBinding()]
param([switch]$InspectOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $InspectOnly) {throw 'P09_XREF_CANONICAL_INSPECT_ONLY'}
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
    'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch',
    'crossref-dual-owner-identity','crossref-canonical-runtime')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
$lease=$null;$passed=0;$script:factoryCalls=0
function Assert-P09CanonicalReject([scriptblock]$Body,[string]$Expected) {
    $actual=$null;try {& $Body} catch {$actual=$_.Exception.Message}
    Assert-P09XrefBinding ($actual -ceq $Expected) 'CANONICAL_TEST_EXPECTED_REJECTION'
}
try {
    $empty=[Collections.Generic.List[object]]::new()
    $pin=[ordered]@{path=(Get-P09XrefCanonicalEvidenceRelativePath 1 'trace');bytes=100;sha256=('a'*64)}
    $model=New-P09XrefCanonicalSidecar 1 $pin $empty
    Assert-P09XrefBinding ($model.case_id -ceq 'P09-XREF-BOOK-C01' -and $model.admissions.Count -eq 0 -and
        -not $model.native_provenance_qualified -and -not $model.native_execution_authorized) 'CANONICAL_TEST_PARTIAL_MODEL_NOT_NATIVE'
    $passed++

    Assert-P09CanonicalReject {Invoke-P09XrefCanonicalFixedHostBatch $null $null ([ordered]@{}) $null} 'P09_XREF_BIND_CANONICAL_FRESH_CHANNEL_AND_FACTORY'
    $passed++

    $state=[ordered]@{canonical_sidecar_attempted=$false;slot_created=$false}
    Write-P09XrefCanonicalSidecar $state $empty
    Assert-P09CanonicalReject {Write-P09XrefCanonicalSidecar $state $empty} 'P09_XREF_BIND_CANONICAL_NO_SIDECAR_RETRY'
    $completed=[ordered]@{canonical_completion_attempted=$true}
    $oldError=[ordered]@{original_completion_error_code='P58_PRESERVED_MODEL_ERROR'}
    Assert-P09CanonicalReject {Complete-P09XrefCanonicalCase $completed $empty $oldError} 'P09_XREF_BIND_CANONICAL_NO_COMPLETION_RETRY'
    Assert-P09XrefBinding ($oldError.original_completion_error_code -ceq 'P58_PRESERVED_MODEL_ERROR') 'CANONICAL_TEST_ORIGINAL_ERROR_NOT_RESET'
    $passed++

    $lease=New-P09XrefProbeLease
    $deny='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":1,"case_index":1,"acknowledged":false,"error_code":"STOP_CANONICAL_TEST_NO_NATIVE_STARTUP","native_execution_authorized":false,"p09_complete":false}'
    $finish='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":2,"case_index":1,"acknowledged":true,"error_code":null,"native_execution_authorized":false,"p09_complete":false}'
    $inputReader=[IO.StringReader]::new($deny+"`n"+$finish+"`n");$outputWriter=[IO.StringWriter]::new()
    try {
        $channel=New-P09XrefHostChannel $inputReader $outputWriter;$batch=[ordered]@{}
        $factory={param($label,$trace,$s) $script:factoryCalls++;throw 'STOP_CANONICAL_TEST_NO_QUALIFIED_FACTORY'}
        Invoke-P09XrefCanonicalFixedHostBatch $channel $lease $batch $factory
        Assert-P09XrefBinding ($batch.planned_cases -eq 8 -and $batch.cases.Count -eq 1 -and
            $batch.completed_callback_cases -eq 0 -and $batch.stopped_case_index -eq 1 -and
            $batch.cases[0].phase -ceq 'prepare_slot' -and $channel.sequence -eq 2 -and
            $null -eq $batch.cases[0].host_finish_error_code -and $script:factoryCalls -eq 0 -and
            $null -eq ('P58OwnedWindowProcess' -as [type])) 'CANONICAL_TEST_DENIAL_BEFORE_NATIVE_SLOT_FACTORY_OR_COM'
        for ($index=1;$index -le 8;$index++) {
            Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'CANONICAL_TEST_NO_NATIVE_DIRECTORY'
        }
    } finally {$inputReader.Dispose();$outputWriter.Dispose()}
    $passed++
    [ordered]@{state='four_canonical_runtime_denial_and_sidecar_contracts_pass_not_native';passed=$passed;failed=0;
        factory_calls=$script:factoryCalls;batch=$batch;native_directories_created=$false;source_trace_rewritten=$false;
        actual_Hangul_or_COM=$false;native_provenance_qualified=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Depth 10 -Compress
} catch {
    [ordered]@{state='canonical_runtime_contract_failed';passed=$passed;failed=1;line=$_.InvocationInfo.ScriptLineNumber;
        error_code=if ($_.Exception.Message -cmatch '^(P09_XREF_|P58_|STOP_)[A-Z_]{1,120}$') {$_.Exception.Message}
            else {'P09_XREF_CANONICAL_TEST_FAILED_NO_RAW_VALUES'};actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
