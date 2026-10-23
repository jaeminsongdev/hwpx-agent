# Explicit private successor, not a redefinition of the original native ports.
# All document/source/probe/producer/trace operations remain original bytes.
Set-StrictMode -Version Latest

function Get-P09XrefPreassignedPortDefinitions {
    $source=Read-P09XrefPreassignedFixedSource 'crossref-native-case-ports.ps1'
    $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'PREASSIGNED_ORIGINAL_PORT_PARSE'
    $rules=[ordered]@{
        'Invoke-P09XrefNativeCaseStep'=@(
            @('Invoke-P09XrefNativeCaseStep','Invoke-P09XrefPreassignedCaseStep',1),
            @('$State.owner=New-P58Owner ''save'' $State.trace;$State.close_attempted=$false',
                '$State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State ''save'')',1),
            @('$State.owner=New-P58Owner ''reopen'' $State.trace;$State.close_attempted=$false',
                '$State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State ''reopen'')',1),
            @('Close-P09XrefNativeCaseOwner','Close-P09XrefPreassignedCaseOwner',2));
        'Close-P09XrefNativeCaseOwner'=@(
            @('Close-P09XrefNativeCaseOwner','Close-P09XrefPreassignedCaseOwner',1),
            @('Close-P58Owner $owner','Close-P09XrefPreassignedOwner $owner',1),
            @('finally {$State.owner=$null}','finally {if ($owner.preassigned_closed) {$State.owner=$null}}',1));
        'Complete-P09XrefNativeCasePorts'=@(
            @('Complete-P09XrefNativeCasePorts','Complete-P09XrefPreassignedCasePorts',1),
            @('Close-P09XrefNativeCaseOwner','Close-P09XrefPreassignedCaseOwner',1));
        'Invoke-P09XrefNativeCaseWorkflow'=@(
            @('Invoke-P09XrefNativeCaseWorkflow','Invoke-P09XrefPreassignedCaseWorkflow',1),
            @('Invoke-P09XrefNativeCaseStep','Invoke-P09XrefPreassignedCaseStep',1),
            @('Complete-P09XrefNativeCasePorts','Complete-P09XrefPreassignedCasePorts',1))}
    foreach ($name in $rules.Keys) {
        $nodes=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$false))
        Assert-P09XrefBinding ($nodes.Count -eq 1) 'PREASSIGNED_ORIGINAL_PORT_INVENTORY'
        $original=$nodes[0].Extent.Text;$changed=$original
        foreach ($rule in $rules[$name]) {
            Assert-P09XrefBinding ([regex]::Matches($changed,[regex]::Escape($rule[0])).Count -eq $rule[2]) 'PREASSIGNED_EXACT_PORT_REWRITE_COUNT'
            $changed=$changed.Replace($rule[0],$rule[1])
        }
        $newTokens=$null;$newErrors=$null;$newAst=[Management.Automation.Language.Parser]::ParseInput($changed,[ref]$newTokens,[ref]$newErrors)
        $newNodes=@($newAst.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
        Assert-P09XrefBinding (@($newErrors).Count -eq 0 -and $newNodes.Count -eq 1) 'PREASSIGNED_SUCCESSOR_PORT_PARSE'
        $body=$newNodes[0].Body.Extent.Text
        $inner=$body.Substring(1,$body.Length-2)
        # Function f($State) has parameters on the function AST, not in Body.
        # Preserve them explicitly when installing a body-only ScriptBlock.
        if ($null -ne $newNodes[0].Parameters -and $newNodes[0].Parameters.Count -gt 0) {
            $parameters=@($newNodes[0].Parameters | ForEach-Object {$_.Extent.Text})
            $inner='param('+($parameters -join ',')+")`n"+$inner
        }
        [pscustomobject]@{name=$newNodes[0].Name;original_name=$name;original=$original;changed=$changed;
            inner=$inner;rewrites=$rules[$name]}
    }
}

function Initialize-P09XrefPreassignedCasePorts {
    foreach ($definition in (Get-P09XrefPreassignedPortDefinitions)) {
        $existing=Get-Command $definition.name -CommandType Function -ErrorAction SilentlyContinue
        if ($null -ne $existing) {
            Assert-P09XrefBinding ($existing.ScriptBlock.ToString() -ceq $definition.inner) 'PREASSIGNED_SUCCESSOR_FUNCTION_REPLACED'
        } else {Set-Item -Path ('Function:global:'+$definition.name) -Value ([scriptblock]::Create($definition.inner))}
    }
}

function New-P09XrefPreassignedCaseState {
    param([Parameter(Mandatory)][int]$CaseIndex,[Parameter(Mandatory)]$ProbeLease,[Parameter(Mandatory)]$Channel)
    Assert-P09XrefExistingOwnerAdapterReady
    Initialize-P09XrefPreassignedCasePorts
    Initialize-P09XrefFrozenWindowBridge
    $checkpoint={param($step,$state)
        $d=Invoke-P09XrefPreassignedHostMessage $state.preassigned_channel $state.case_index 'checkpoint' -Step $step
        if ($step -cin @('create_save_session','create_reopen_session')) {
            Assert-P09XrefBinding ($null -eq $state.current_descriptor -and $null -ne $d) 'PREASSIGNED_NEW_CURRENT_DESCRIPTOR'
            $state.current_descriptor=$d
        } else {Assert-P09XrefBinding ($null -eq $d) 'PREASSIGNED_NO_OTHER_DESCRIPTOR'}
    }
    $admit={param($owner,$state) Admit-P09XrefPreassignedOwner $owner $state}
    $state=New-P09XrefNativeCaseState $CaseIndex $ProbeLease $checkpoint $admit
    $state['preassigned_channel']=$Channel;$state['current_descriptor']=$null
    $state['dual_identity_evidence']=[Collections.Generic.List[object]]::new()
    $state.trace['preassigned_host_protocol']='hwpx-agent.private.crossref-preassigned-host-request/v2'
    $state.trace['dual_identity_evidence']=$state.dual_identity_evidence
    return $state
}
