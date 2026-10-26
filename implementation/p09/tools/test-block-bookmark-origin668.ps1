# Actual successor functions on bounded in-memory models. No HWP activation.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'MODEL_ONLY_REQUIRED'}
. (Join-Path $PSScriptRoot 'block-bookmark-source645-ports.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-selection658.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-origin668.ps1')
# Reuse only named model function definitions, never execute the consumed suite.
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'test-block-bookmark-selection658.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) {throw 'FIXTURE_PARSE_FAILED'}
$names=@('Assert-Model','Model-Case','Assert-P09Block645CurrentDocument','Release-P09Block645ComReference',
    'Fake-State','Expect-Denied','Assert-P09Block646CurrentDocument','New658State')
foreach ($name in $names) {
    $found=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
    if ($found.Count -ne 1) {throw 'FIXTURE_FUNCTION_NOT_UNIQUE'}
    . ([scriptblock]::Create($found[0].Extent.Text))
}
$script:run=0;$script:failed=[Collections.Generic.List[string]]::new()
function New668State {
    $state=New658State
    $script:origins=@(16,0,0,0,0,0,0,0);$script:currentPara=0;$script:positionCalls=0;$script:textCalls=0
    $script:fakeHwp|Add-Member -Force ScriptMethod SetPos {param($List,$Para,$Pos)
        $script:positionCalls++
        Assert-Model ($List -is [int] -and $List -eq 0 -and $Para -is [int] -and $Para -ge 0 -and $Para -lt 8 -and $Pos -is [int] -and $Pos -eq 0)
        $script:currentPara=$Para;$this.SelectionMode=[int]0
        if ($script:fault -ceq 'origin_set_false') {return $false}
        return $true
    }
    $script:fakeHwp|Add-Member ScriptMethod GetPosBySet {
        $set=$this.CreateSet('ListParaPos')
        $set.Values['List']=[int]0;$set.Values['Para']=[int]$script:currentPara;$set.Values['Pos']=[int]$script:origins[$script:currentPara]
        switch -CaseSensitive ($script:fault) {
            'origin_list' {$set.Values['List']=[int]1}
            'origin_para' {$set.Values['Para']++}
            'origin_int64' {$set.Values['Pos']=[long]16}
            'origin_negative' {$set.Values['Pos']=[int]-1}
            'origin_overflow' {$set.Values['Pos']=[int]::MaxValue}
            'origin_owner' {$script:fault='owner'}
        }
        return $set
    }
    $script:fakeHwp|Add-Member ScriptMethod GetTextFile {param($Format,$Options)
        Assert-Model ($Format -ceq 'TEXT' -and $Options -ceq 'saveblock:true')
        $script:textCalls++
        $text=@(Get-P09Block645Cases)[$script:index-1].selected_text
        switch -CaseSensitive ($script:fault) {
            'text_false' {return $false}
            'text_wrong' {return 'WRONG'}
            'text_CRLF' {return ($text+"`r`n")}
            'text_after_gate' {if ($script:textCalls -eq 2) {return 'CHANGED'}}
            'text_owner' {$script:fault='owner'}
        }
        return $text
    }
    return $state
}
Model-Case 'observed16_origin_and_other_zero_origins_select_exact_text_and16_readbacks' {
    $s=New668State;Invoke-P09Block668Ranges $s
    Assert-Model ($s.completed_ranges -eq 8 -and $script:executeCount -eq 8 -and $script:positionCalls -eq 8 -and $script:textCalls -eq 16)
    Assert-Model ($s.range_trace[0].logical_selection.spos -eq 0 -and $s.range_trace[0].selection.spos -eq 16 -and $s.range_trace[0].selection.epos -eq 26)
    Assert-Model ($s.range_trace[1].selection.spos -eq 5 -and $s.range_trace[1].selection.epos -eq 14 -and $script:releases -eq 72)
    Assert-Model ($s.selection_observations.Count -eq 16 -and $script:pointerCalls -eq 0)
    foreach ($row in $s.selection_observations) {Assert-Model ($row.exact_match -and $row.selected_text.exact_match -and -not $row.selected_text.raw_text_present -and $row.selected_text.sha256.Length -eq 64)}
}
Model-Case 'arbitrary_observed_origin_not_hardcoded16_or_first_paragraph_only' {
    $s=New668State;$script:origins=@(24,8,16,0,8,24,0,16);Invoke-P09Block668Ranges $s
    Assert-Model ($s.completed_ranges -eq 8)
    for ($i=0;$i -lt 8;$i++) {
        $row=$s.range_trace[$i]
        Assert-Model ($row.observed_origin[2] -eq $script:origins[$i] -and $row.selection.spos -eq ($script:origins[$i]+$row.logical_selection.spos))
    }
}
foreach ($pair in @(@('origin_set_false','ORIGIN_POSITION_FAILED'),@('origin_list','ORIGIN_WRONG_LIST_OR_PARAGRAPH'),
    @('origin_para','ORIGIN_WRONG_LIST_OR_PARAGRAPH'),@('origin_int64','SELECTION_SET_ITEM_TYPE'),
    @('origin_negative','SELECTION_SET_ITEM_TYPE'),@('origin_overflow','ORIGIN_POSITION_OVERFLOW'),
    @('origin_owner','CURRENT_ADMITTED_OWNER'),@('api_false','SELECTION_SET_READ_FAILED'),
    @('wrong_start_pos','EXACT_NATIVE_SELECTION_POSITIONS'),@('text_false','EXACT_SELECTED_TEXT_REQUIRED'),
    @('text_wrong','EXACT_SELECTED_TEXT_REQUIRED'),@('text_CRLF','EXACT_SELECTED_TEXT_REQUIRED'),
    @('text_after_gate','EXACT_SELECTED_TEXT_REQUIRED'),@('text_owner','CURRENT_ADMITTED_OWNER'),
    @('move_at_execute','EXACT_NATIVE_SELECTION_POSITIONS'),@('parameter_at_execute','BOOKMARK_PARAMETER_READBACK'))) {
    Model-Case $pair[0] {
        $s=New668State;$script:fault=$pair[0]
        Expect-Denied $s $pair[1] {Invoke-P09Block668Ranges $s}
        Assert-Model ($script:executeCount -eq 0 -and $s.completed_ranges -eq 0)
        $calls=$script:events.Count;$positions=$script:positionCalls
        try {Invoke-P09Block668Ranges $s} catch {}
        Assert-Model ($calls -eq $script:events.Count -and $positions -eq $script:positionCalls)
    }
}
Model-Case 'origin_reference_cleanup_failure_prevents_Execute' {
    $s=New668State;$script:fault='release'
    Expect-Denied $s 'PARAMETER_REFERENCE_RELEASE_UNCONFIRMED' {Invoke-P09Block668Ranges $s}
    Assert-Model ($script:executeCount -eq 0)
}
Model-Case 'logical_target_identity_cannot_be_changed' {
    $s=New668State;$case=@(Get-P09Block645Cases)[0];$case.selected_text='different';$denied=$false
    try {Get-P09Block668NativeCase $s $script:fakeHwp $case} catch {$denied=$_.Exception.GetBaseException().Message -ceq 'P09_BLOCK645_LOGICAL_RANGE_IDENTITY'}
    Assert-Model ($denied -and $s.failed -and $script:positionCalls -eq 0)
}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    actual_native_started=$false;position_requirement_weakened=$false;source_capture_qualified=$false}|ConvertTo-Json -Depth 6 -Compress
if ($script:failed.Count -ne 0) {exit 2}
