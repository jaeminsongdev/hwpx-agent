# Only predicate/getter-failure models. No real COM or Hwp session.
[CmdletBinding()]
param([switch]$ModelsOnly,[switch]$GetterFaultsAfter485)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_SOURCE_DIAGNOSTIC_MODELS_ONLY'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1')
function New-SourceModel {
    return [pscustomobject]@{owner_verified=$true;application_bound=$true;collection_bound=$true;document_bound=$true;
        document_application_bound=$true;document_count=[int]1;full_name_matches=$true;modified=[int]0;version_matches=$true;source_digest_matches=$true}
}
function Test-ModelPair([bool]$Old,$Before,$After) {
    try {if ($Old) {[void](Assert-ModelLegacyPair $Before $After)} else {[void](Assert-P09XrefActiveSourceObservations $Before $After)};return $true}
    catch {return $false}
}
function Get-ModelPairCode($Before,$After) {
    try {[void](Assert-P09XrefActiveSourceObservations $Before $After);return $null} catch {return $_.Exception.Message}
}
try {
    if (-not $GetterFaultsAfter485) {
    $archive=Join-Path $PSScriptRoot '..\source-archive\p361-source-bind-diagnostics485\active-source.ps1'
    $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($archive,[ref]$tokens,[ref]$errors)
    $found=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-P09XrefActiveSourceObservations'},$false))
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $found.Count -eq 1) 'MODEL_EXACT_LEGACY_PREDICATE'
    . ([scriptblock]::Create($found[0].Extent.Text.Replace('function Assert-P09XrefActiveSourceObservations','function Assert-ModelLegacyPair')))
    $pairs=[Collections.Generic.List[object]]::new();[void]$pairs.Add([pscustomobject]@{before=(New-SourceModel);after=(New-SourceModel);expected=$true})
    $flags=@('owner_verified','application_bound','collection_bound','document_bound','document_application_bound','full_name_matches','version_matches','source_digest_matches')
    for ($side=0;$side -lt 2;$side++) {
        foreach ($name in $flags) {foreach ($value in @($false,1,'true')) {
            $a=New-SourceModel;$b=New-SourceModel;if ($side -eq 0) {$a.$name=$value} else {$b.$name=$value}
            [void]$pairs.Add([pscustomobject]@{before=$a;after=$b;expected=$false})
        }}
        foreach ($name in @('document_count','modified')) {
            # Assign arrays directly: pipeline output from an if-expression drops null.
            if ($name -ceq 'document_count') {$values=@(0,2,[long]1,'1',$true,$null)} else {$values=@(-1,1,$false,'0',[long]0,$null)}
            foreach ($value in $values) {
                $a=New-SourceModel;$b=New-SourceModel;if ($side -eq 0) {$a.$name=$value} else {$b.$name=$value}
                [void]$pairs.Add([pscustomobject]@{before=$a;after=$b;expected=$false})
            }
        }
        foreach ($extra in @($false,$true)) {
            $a=New-SourceModel;$b=New-SourceModel;$target=if ($side -eq 0) {$a} else {$b}
            if ($extra) {$target|Add-Member private_extra 'PRIVATE-VALUE'} else {$target.PSObject.Properties.Remove('document_bound')}
            [void]$pairs.Add([pscustomobject]@{before=$a;after=$b;expected=$false})
        }
    }
    Assert-P09XrefBinding ($pairs.Count -eq 77) 'MODEL_PAIR_COUNT'
    foreach ($pair in $pairs) {Assert-P09XrefBinding ((Test-ModelPair $true $pair.before $pair.after) -eq $pair.expected -and
        (Test-ModelPair $false $pair.before $pair.after) -eq $pair.expected) 'MODEL_ACCEPTANCE_EQUIVALENCE'}
    $old=Assert-ModelLegacyPair (New-SourceModel) (New-SourceModel);$new=Assert-P09XrefActiveSourceObservations (New-SourceModel) (New-SourceModel)
    Assert-P09XrefBinding (($old|ConvertTo-Json -Compress) -ceq ($new|ConvertTo-Json -Compress)) 'MODEL_SAME_NON_AUTHORITY_RESULT'
    [Console]::WriteLine('test source_bind_diagnostic::all77_original_and_current_admission_outcomes_identical ... ok')

    $codes=@{owner_verified='SOURCE_OWNER_MISMATCH';application_bound='SOURCE_APPLICATION_IDENTITY_MISMATCH';
        collection_bound='SOURCE_COLLECTION_IDENTITY_MISMATCH';document_bound='SOURCE_ACTIVE_DOCUMENT_IDENTITY_MISMATCH';
        document_application_bound='SOURCE_DOCUMENT_APPLICATION_IDENTITY_MISMATCH';full_name_matches='SOURCE_ACTIVE_PATH_MISMATCH';
        version_matches='SOURCE_VERSION_MISMATCH';source_digest_matches='SOURCE_DIGEST_MISMATCH'}
    foreach ($name in $flags) {foreach ($side in @(0,1)) {
        $a=New-SourceModel;$b=New-SourceModel;if ($side -eq 0) {$a.$name=$false} else {$b.$name=$false}
        Assert-P09XrefBinding ((Get-ModelPairCode $a $b) -ceq ('P09_XREF_BIND_'+$codes[$name])) 'MODEL_CLOSED_PRECISE_FLAG_CODE'
    }}
    [Console]::WriteLine('test source_bind_diagnostic::each_eight_failed_checks_has_a_closed_specific_code ... ok')
    }

    # ScriptProperty getters can suppress their exception under PowerShell's
    # Extended Type System. CLR property accessors model a throwing COM getter
    # without activating COM; no native identity getter is reached in these tests.
    Add-Type -TypeDefinition @'
public sealed class P09SourceBindGetterFaultModel {
    public string Fault;
    public object CollectionValue, ActiveValue, ApplicationValue;
    public int VersionReads;
    void Check(string name) { if (Fault == name) throw new System.InvalidOperationException("PRIVATE-GETTER-EXCEPTION"); }
    public object XHwpDocuments { get { Check("COLLECTION"); return CollectionValue; } }
    public object Active_XHwpDocument { get { Check("ACTIVE_DOCUMENT"); return ActiveValue; } }
    public object Application { get { Check("APPLICATION"); Check("DOCUMENT_APPLICATION"); return ApplicationValue; } }
    public object Count { get { Check("COUNT"); return (int)1; } }
    public object Modified { get { Check("MODIFIED"); return (int)0; } }
    public string FullName { get { Check("DOCUMENT_NAME"); Check("ACTIVE_NAME"); return "PRIVATE-PATH"; } }
    public string Version { get { VersionReads++; Check("VERSION"); return "11.0.0.9136"; } }
}
'@

    $original=(Get-Command Test-P58Owner -CommandType Function).ScriptBlock
    try {
        Set-Item -Path Function:Test-P58Owner -Value {return $true}
        $getters=@(@('hwp','XHwpDocuments','COLLECTION'),@('collection','Active_XHwpDocument','ACTIVE_DOCUMENT'),
            @('hwp','Application','APPLICATION'),@('document','Application','DOCUMENT_APPLICATION'),@('collection','Count','COUNT'),
            @('document','Modified','MODIFIED'),@('document','FullName','DOCUMENT_NAME'),@('active','FullName','ACTIVE_NAME'),@('hwp','Version','VERSION'))
        foreach ($getter in $getters) {
            $active=[P09SourceBindGetterFaultModel]::new();$document=[P09SourceBindGetterFaultModel]::new();$document.ApplicationValue=[object]::new()
            $collection=[P09SourceBindGetterFaultModel]::new();$collection.ActiveValue=$active
            $hwp=[P09SourceBindGetterFaultModel]::new();$hwp.CollectionValue=$collection;$hwp.ApplicationValue=[object]::new()
            $targets=@{hwp=$hwp;collection=$collection;document=$document;active=$active}
            $targets[$getter[0]].Fault=$getter[2]
            $pointers=[Collections.Generic.List[IntPtr]]::new();$code=$null
            try {[void](Read-P09XrefActiveSourceObservation ([pscustomobject]@{hwp=$hwp}) $document $pointers ([IntPtr]1) ([IntPtr]2) ([IntPtr]3) 'PRIVATE-PATH')}
            catch {$code=$_.Exception.Message}
            Assert-P09XrefBinding ($code -ceq ('P09_XREF_BIND_SOURCE_READ_'+$getter[2]+'_FAILED') -and $pointers.Count -eq 0 -and
                -not $code.Contains('PRIVATE')) 'MODEL_NINE_GETTER_FAILURES_NO_RAW_OR_COM'
        }
        [Console]::WriteLine('test source_bind_diagnostic::nine_getter_failures_precede_identity_and_hide_values ... ok')
        $hwp=[P09SourceBindGetterFaultModel]::new();$hwp.Fault='COLLECTION'
        try {[void](Read-P09XrefActiveSourceObservation ([pscustomobject]@{hwp=$hwp}) ([object]::new()) ([Collections.Generic.List[IntPtr]]::new()) ([IntPtr]1) ([IntPtr]2) ([IntPtr]3) 'PRIVATE-PATH')}
        catch {Assert-P09XrefBinding ($_.Exception.Message -ceq 'P09_XREF_BIND_SOURCE_READ_COLLECTION_FAILED') 'MODEL_FIRST_GETTER_CODE'}
        Assert-P09XrefBinding ($hwp.VersionReads -eq 0) 'MODEL_NO_LATER_READ_OR_RETRY'
        [Console]::WriteLine('test source_bind_diagnostic::first_failure_does_not_read_later_properties_or_retry ... ok')
    } finally {Set-Item -Path Function:Test-P58Owner -Value $original}
    Assert-P09XrefOriginalOwnerFunction
    $rejected=$false
    try {[void](Observe-P09XrefOwnedActiveSource ([pscustomobject]@{hwp=[object]::new();documents=[object]::new()}) ([object]::new()))}
    catch {$rejected=$_.Exception.Message -ceq 'P09_XREF_BIND_REAL_OWNED_COM_REQUIRED'}
    Assert-P09XrefBinding $rejected 'MODEL_ORIGINAL_REAL_COM_ADMISSION_RESTORED'
    [Console]::WriteLine('test source_bind_diagnostic::model_checker_restored_and_no_real_bridge_mock_fallback ... ok')
    if ($GetterFaultsAfter485) {
        [Console]::WriteLine('P09_SOURCE_BIND_RETAINED_PAIRS=77;GETTER_FAULTS=9')
        [Console]::WriteLine('test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out')
    } else {
        [Console]::WriteLine('P09_SOURCE_BIND_PAIRS=77;GETTER_FAULTS=9')
        [Console]::WriteLine('test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out')
    }
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_SOURCE_DIAGNOSTIC_MODEL_FAILED_NO_RAW_VALUES'}
    [Console]::WriteLine('Error: '+$code);exit 1
}
