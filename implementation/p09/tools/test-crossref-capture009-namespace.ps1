# Read-only process-local namespace models. No COM, Native or artifact writes.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_NINE_MODELS_ONLY'}
$lease=$null;$modelPhase='imports'
try {
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
        'crossref-save-reopen','crossref-stage-probe','crossref-fixed-batch','crossref-canonical-runtime',
        'crossref-preassigned-controller','crossref-native-case-ports','crossref-capture009-namespace')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $modelPhase='definitions';$definitions=@(Get-P09XrefCapture009Definitions)
    Assert-P09XrefBinding ($definitions.Count -eq 7) 'CAPTURE_NINE_MODEL_NINE_DEFINITIONS'
    foreach ($definition in $definitions) {
        $restored=$definition.changed
        for ($i=$definition.replacements.Count-1;$i -ge 0;$i--) {$restored=$restored.Replace($definition.replacements[$i][1],$definition.replacements[$i][0])}
        Assert-P09XrefBinding ($restored -ceq $definition.original) 'CAPTURE_NINE_MODEL_EXACT_WHOLE_INVERSE'
    }
    [Console]::WriteLine('test capture009_namespace::seven_definitions_restore_entire_original_bodies ... ok')

    $unaffected=@{}
    foreach ($name in @('Test-P58Owner','Open-P58Document','Save-P58Artifact','Observe-P09XrefOwnedActiveSource',
        'Read-P09XrefActiveSourceObservation','Invoke-P09XrefFixedBatchCore','New-P09XrefNativeCaseState')) {
        $unaffected[$name]=(Get-Command $name -CommandType Function).ScriptBlock.Ast.Extent.Text
    }
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $old=Get-P09XrefCaseArtifactPath 1 'opened'
    Assert-P09XrefBinding ($old.Contains('20261017-r01-c01-attempt01')) 'CAPTURE_NINE_MODEL_ORIGINAL_DEFAULT'
    $modelPhase='initialize';Initialize-P09XrefCapture009Namespace
    $modelPhase='path_matrix'
    $paths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    for ($index=1;$index -le 8;$index++) {
        $base='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g009-c'+$index.ToString('00')+'-attempt01/'
        foreach ($stage in @('opened','saved','reopened')) {
            $path=Get-P09XrefCaseArtifactPath $index $stage
            $scope=Get-P09XrefArtifactScope $index ($stage+'_clean') ('a'*64)
            Assert-P09XrefBinding ($path -ceq (Join-Path $root ($base+$stage+'.hwpx')) -and $scope.path -ceq $path -and
                $scope.case_id -ceq ('P09-XREF-BOOK-C'+$index.ToString('00')) -and $scope.require_clean -and $paths.Add($path)) 'CAPTURE_NINE_MODEL_ALL24_IO_SCOPE_PATHS'
        }
        foreach ($kind in @('trace','sidecar')) {
            $relative=Get-P09XrefCanonicalEvidenceRelativePath $index $kind
            $file=if ($kind -ceq 'trace') {'target-trace.json'} else {'owner-identities.json'}
            Assert-P09XrefBinding ($relative -ceq ($base+$file) -and $paths.Add((Join-Path $root $relative))) 'CAPTURE_NINE_MODEL_CANONICAL16_PATHS'
        }
    }
    Assert-P09XrefBinding ($paths.Count -eq 40 -and -not $paths.Contains($old)) 'CAPTURE_NINE_MODEL_FORTY_DISJOINT_FIXED_PATHS'
    [Console]::WriteLine('test capture009_namespace::all40_io_scope_trace_sidecar_paths_are_fixed_and_disjoint ... ok')

    $modelPhase='unaffected_functions'
    foreach ($name in $unaffected.Keys) {
        Assert-P09XrefBinding ((Get-Command $name -CommandType Function).ScriptBlock.Ast.Extent.Text -ceq $unaffected[$name]) 'CAPTURE_NINE_MODEL_OWNER_IO_FLOW_AND_SOURCE_UNCHANGED'
    }
    Assert-P09XrefOriginalOwnerFunction
    [Console]::WriteLine('test capture009_namespace::original_owner_source_io_and_batch_core_remain_exact ... ok')

    $modelPhase='probe_lease';$lease=New-P09XrefProbeLease
    Assert-P09XrefBinding ($lease.binary -ceq (Join-Path $root 'target/debug/examples/p09_crossref_capture009_probe.exe') -and
        $lease.binary_sha256 -ceq '66f39ca7cbddfe075d18738e97d34f49aef77e97265e3256baf7c6883f878f55' -and
        $lease.stream.Length -eq 5152256 -and $lease.stream.CanRead -and -not $lease.stream.CanWrite) 'CAPTURE_NINE_MODEL_READONLY_EXACT_BINARY_LEASE'
    Close-P09XrefProbeLease $lease
    Assert-P09XrefBinding ($lease.closed -and -not $lease.stream.CanRead) 'CAPTURE_NINE_MODEL_LEASE_CLOSED'
    [Console]::WriteLine('test capture009_namespace::fresh_fixed009_binary_lease_is_readonly_and_closed ... ok')

    $modelPhase='selector_denials';$rejected=$false
    try {Initialize-P09XrefCapture009Namespace} catch {$rejected=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_NINE_NO_REINSTALL_OR_MODE_SWITCH'}
    Assert-P09XrefBinding $rejected 'CAPTURE_NINE_MODEL_REINSTALL_REJECTED'
    foreach ($badSelector in @(@(0,'opened'),@(9,'opened'),@(1,'../opened'))) {
        $rejected=$false;try {[void](Get-P09XrefCaseArtifactPath $badSelector[0] $badSelector[1])} catch {$rejected=$true}
        Assert-P09XrefBinding $rejected 'CAPTURE_NINE_MODEL_ORIGINAL_SELECTOR_DENIAL'
    }
    Assert-P09XrefBinding ((Get-P09XrefArtifactScope 1 'opened_after_insert' ('a'*64)).require_clean -eq $false) 'CAPTURE_NINE_MODEL_DIRTY_INSERT_BOUNDARY_NOT_CHANGED'
    [Console]::WriteLine('test capture009_namespace::no_reinstall_mode_switch_or_foreign_path_selector ... ok')
    [Console]::WriteLine('test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out')
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_CAPTURE_NINE_MODEL_FAILED_NO_RAW_VALUES'}
    [Console]::WriteLine('Error: '+$code)
    if ($modelPhase -cin @('imports','definitions','initialize','path_matrix','unaffected_functions','probe_lease','selector_denials')) {
        $kind=$_.Exception.GetType().Name
        if ($kind -cmatch '^[A-Za-z]{1,80}$') {[Console]::WriteLine('Diagnostic: '+$modelPhase+':'+$kind+':'+[int]$_.InvocationInfo.ScriptLineNumber)}
    }
    exit 1
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
