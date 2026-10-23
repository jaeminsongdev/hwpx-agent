# Only the eleven not-yet-run lease/cleanup tests, plus one new name-collision
# diagnostic. Original eight successful400 tests are preserved, not replayed.
[CmdletBinding()]
param([switch]$RemainingModelsOnly,[switch]$PostParameterFixOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (($RemainingModelsOnly -and $PostParameterFixOnly) -or (-not $RemainingModelsOnly -and -not $PostParameterFixOnly)) {throw 'P09_XREF_BIND_PREASSIGNED_REMAINING_MODELS_ONLY'}
foreach ($name in @('crossref-owned-active-source','sdk-baseline-owned-session','crossref-case-flow','crossref-native-case-ports',
    'crossref-dual-owner-identity','crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-preassigned-case-ports')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
try {
    $core=Read-P09XrefPreassignedFixedSource 'crossref-existing-owner.cs'
    $models=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'test-crossref-preassigned-owner.cs'))
    $collision='public static class P09PreassignedModelNewCollision { public static int New(bool value) { return 1; } }'
    Add-Type -TypeDefinition ($core+"`n"+$models.Replace('using System;','')+"`n"+$collision)
    $source=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'test-crossref-preassigned-owner.ps1'))
    $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'PREASSIGNED_REMAINING_SOURCE_PARSE'
    foreach ($name in @('Assert-PreassignedModelReject','New-PreassignedModelDescriptor','New-PreassignedModelOwner','New-PreassignedModelState')) {
        $nodes=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$false))
        Assert-P09XrefBinding ($nodes.Count -eq 1) 'PREASSIGNED_REMAINING_HELPER_INVENTORY'
        $body=$nodes[0].Body.Extent.Text
        $inner=$body.Substring(1,$body.Length-2)
        if ($null -ne $nodes[0].Parameters -and $nodes[0].Parameters.Count -gt 0) {
            $parameters=@($nodes[0].Parameters | ForEach-Object {$_.Extent.Text})
            $inner='param('+($parameters -join ',')+")`n"+$inner
        }
        Set-Item -Path ('Function:global:'+$name) -Value ([scriptblock]::Create($inner))
    }
    $script:P09XrefExistingOwnerOwnedType='P09CrossrefExisting.ExistingOwner' -as [type]
    Initialize-P09XrefExistingOwnerAdapter
    Initialize-P09XrefPreassignedCasePorts
    if ($PostParameterFixOnly) {
        # Recheck only the affected installation assertion from the old prefix.
        $before=(Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()
        Initialize-P09XrefPreassignedCasePorts
        $definitions=@(Get-P09XrefPreassignedPortDefinitions)
        foreach ($d in $definitions) {Assert-P09XrefBinding ((Get-Command $d.name).ScriptBlock.ToString() -ceq $d.inner) 'PREASSIGNED_MODEL_EXACT_SUCCESSOR'}
        Assert-P09XrefBinding ($before -ceq (Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()) 'PREASSIGNED_MODEL_ORIGINAL_UNCHANGED'
        [Console]::WriteLine('test preassigned_owner::successor_install_keeps_original ... ok')
        foreach ($name in @('Close-P09XrefPreassignedCaseOwner','Complete-P09XrefPreassignedCasePorts','New-PreassignedModelOwner')) {
            $block=(Get-Command $name).ScriptBlock
            Assert-P09XrefBinding ($null -ne $block.Ast.ParamBlock -and $block.Ast.ParamBlock.Parameters.Count -eq 1) 'PREASSIGNED_BODY_ONLY_PARAMETER_PRESERVED'
        }
        [Console]::WriteLine('test preassigned_owner::body_only_external_parameters_preserved ... ok')
    } else {
    # Reproduce PowerShell's special ::new constructor binding without calling
    # the old failed test method or any lease/native operation.
    $method=[P09PreassignedModelNewCollision].GetMethod('New')
    Assert-P09XrefBinding ($null -ne $method -and $method.Invoke($null,@($false)) -eq 1) 'PREASSIGNED_DIAGNOSTIC_REAL_STATIC_NEW_METHOD'
    $errorType=$null
    try {[void][P09PreassignedModelNewCollision]::New($false)} catch {$errorType=$_.Exception.GetType().FullName}
    Assert-P09XrefBinding ($errorType -ceq 'System.Management.Automation.MethodException') 'PREASSIGNED_DIAGNOSTIC_NEW_BINDS_CONSTRUCTOR'
    [Console]::WriteLine('test preassigned_owner::powershell_new_factory_name_collision ... ok')
    }
    $begin='$owner=New-PreassignedModelOwner $false;Release-P09XrefPreassignedReferences $owner'
    $end="[Console]::WriteLine('test result: ok. 18 passed; 0 failed; 0 ignored; managed_leases_ports_only_not_ROT_COM_or_Native')"
    $start=$source.IndexOf($begin,[StringComparison]::Ordinal);$finish=$source.IndexOf($end,[StringComparison]::Ordinal)
    Assert-P09XrefBinding ($start -gt 0 -and $finish -gt $start -and
        $source.IndexOf($begin,$start+$begin.Length,[StringComparison]::Ordinal) -lt 0 -and
        $source.IndexOf($end,$finish+$end.Length,[StringComparison]::Ordinal) -lt 0) 'PREASSIGNED_EXACT_REMAINING_TEST_BOUNDARIES'
    [void](& ([scriptblock]::Create($source.Substring($start,$finish-$start))))
    if ($PostParameterFixOnly) {[Console]::WriteLine('test result: ok. 13 passed; 0 failed; 0 ignored; remaining11_affected1_parameters1_not_ROT_COM_or_Native')}
    else {[Console]::WriteLine('test result: ok. 12 passed; 0 failed; 0 ignored; remaining_models_and_diagnostic_not_ROT_COM_or_Native')}
} catch {
    $detail=[string]$_.Exception.Message
    if ($null -ne $_.ErrorDetails) {$detail+=[string]$_.ErrorDetails.Message}
    foreach ($match in [regex]::Matches($detail,'\bCS[0-9]{4}\b')) {[Console]::Error.WriteLine(('Error: '+$match.Value))}
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_PREASSIGNED_RECOVERY_FAILED_NO_RAW_VALUES'}
    if ($null -ne $_.InvocationInfo -and $_.InvocationInfo.ScriptLineNumber -gt 0) {
        [Console]::Error.WriteLine(('Error: P09_XREF_BIND_TEST_LINE_'+$_.InvocationInfo.ScriptLineNumber))
    }
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
