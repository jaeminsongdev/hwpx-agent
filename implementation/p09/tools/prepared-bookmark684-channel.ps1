# Child-process-local projection of the original exact channel. No Native calls.
Set-StrictMode -Version Latest
function Get-P09Prepared684Steps {
    return @('prepare_slot','create_save_session','candidate_open','candidate_bind','initial_identity','initial_snapshot',
        'initial_image','saved_save','saved_bind','save_session_close','create_reopen_session','fresh_saved_open',
        'reopened_save','reopened_image','reopen_session_close','final_source_check')
}
function Initialize-P09Prepared684Channel {
    $path=Join-Path $PSScriptRoot 'crossref-preassigned-host-channel.ps1'
    $bytes=[IO.File]::ReadAllBytes($path)
    Assert-P09XrefBinding ((Get-P09XrefFreshDigest $bytes) -ceq '4ce9ea5625f35c97bfd1d3c5b45bb69e1780b0aa5ffec45a0c665a7cb9205e86') 'PREPARED_CHANNEL_ORIGINAL_SHA'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput([Text.UTF8Encoding]::new($false,$true).GetString($bytes),$path,[ref]$tokens,[ref]$errors)
    $nodes=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-P09XrefPreassignedHostMessage'},$false))
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $nodes.Count -eq 1) 'PREPARED_CHANNEL_ORIGINAL_AST'
    $original=$nodes[0].Extent.Text
    $live=Get-Command Invoke-P09XrefPreassignedHostMessage -CommandType Function
    Assert-P09XrefBinding ($live.ScriptBlock.Ast.Extent.Text -ceq $original) 'PREPARED_CHANNEL_NO_REINSTALL'
    $rules=@(@('hwpx-agent.private.crossref-preassigned-host-request/v2','hwpx-agent.private.prepared-bookmark684-request/v1'),
        @('hwpx-agent.private.crossref-preassigned-host-response/v2','hwpx-agent.private.prepared-bookmark684-response/v1'),
        @('Get-P09XrefCaseFlowSteps','Get-P09Prepared684Steps'))
    $changed=$original
    foreach ($rule in $rules) {
        Assert-P09XrefBinding ([regex]::Matches($changed,[regex]::Escape($rule[0])).Count -eq 1) 'PREPARED_CHANNEL_EXACT_REWRITE'
        $changed=$changed.Replace($rule[0],$rule[1])
    }
    $inverse=$changed
    for ($i=$rules.Count-1;$i -ge 0;$i--) {$inverse=$inverse.Replace($rules[$i][1],$rules[$i][0])}
    Assert-P09XrefBinding ($inverse -ceq $original) 'PREPARED_CHANNEL_WHOLE_BODY_INVERSE'
    $tokens=$null;$errors=$null
    $projected=[Management.Automation.Language.Parser]::ParseInput($changed,$path,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'PREPARED_CHANNEL_PROJECTED_AST'
    . ($projected.GetScriptBlock())
    $loaded=Get-Command Invoke-P09XrefPreassignedHostMessage -CommandType Function
    Assert-P09XrefBinding ($loaded.ScriptBlock.Ast.Extent.Text -ceq $changed) 'PREPARED_CHANNEL_COMPILED_IDENTITY'
    Set-Item Function:script:Invoke-P09XrefPreassignedHostMessage -Value $loaded.ScriptBlock
}

