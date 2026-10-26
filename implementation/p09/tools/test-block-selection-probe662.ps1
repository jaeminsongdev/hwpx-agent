# Executes actual port function bodies on in-memory models only. No Native/file IO.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'MODEL_ONLY_REQUIRED'}
. (Join-Path $PSScriptRoot 'block-bookmark-source645-ports.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-source653-typed.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-selection658.ps1')
. (Join-Path $PSScriptRoot 'block-selection-probe662.ps1')
Initialize-P09SelectionProbe662

$script:run=0;$script:failed=[Collections.Generic.List[string]]::new()
function Assert-Model([bool]$Value) {if (-not $Value) {throw 'MODEL_ASSERTION'}}
function Model-Case([string]$Name,[scriptblock]$Body) {
    $script:run++
    try {[void](& $Body)} catch {[void]$script:failed.Add($Name)}
}
function Assert-P09Block645CurrentDocument($State) {
    $script:owners++
    if ($script:fault -ceq 'owner') {throw 'P09_BLOCK645_CURRENT_ADMITTED_OWNER'}
}
function Release-P09Block645ComReference($Value) {
    $script:releases++
    if ($script:fault -cin @('release','default_and_release')) {throw 'PRIVATE_RELEASE_MESSAGE_NOT_PRINTED'}
}
function Fake-State {
    $script:fault='';$script:events=[Collections.Generic.List[string]]::new();$script:items=@{}
    $script:index=0;$script:owners=0;$script:releases=0;$script:executeCount=0;$script:positions=@(0,0,0,0)
    $set=[pscustomobject]@{}
    $set|Add-Member ScriptMethod SetItem {throw 'FORBIDDEN_GENERIC_ITEM_WRITE'}
    $set|Add-Member ScriptMethod Item {throw 'FORBIDDEN_GENERIC_ITEM_READ'}
    $script:book=[pscustomobject]@{HSet=$set}
    foreach ($property in @('name','type','Command')) {
        $getter=[scriptblock]::Create(@'
            if ($script:fault -ceq 'throw_get_PROPERTY') {throw [Runtime.InteropServices.COMException]::new('SECRET_NOT_PRINTED',-2147467259)}
            if ($script:fault -ceq 'wrong_type' -and 'PROPERTY' -ceq 'type') {return [double]1}
            if ($script:fault -ceq 'wrong_name' -and 'PROPERTY' -ceq 'name') {return 'wrong'}
            return $script:items['PROPERTY']
'@.Replace('PROPERTY',$property))
        $setter=[scriptblock]::Create(@'
            param($Value)
            [void]$script:events.Add('set:PROPERTY')
            if ($script:fault -ceq 'throw_put_PROPERTY') {throw [Runtime.InteropServices.COMException]::new('SECRET_NOT_PRINTED',-2147467259)}
            if ('PROPERTY' -ceq 'name') {Assert-Model ($Value -is [string])}
            else {Assert-Model ($Value -is [uint32])}
            $script:items['PROPERTY']=$Value
'@.Replace('PROPERTY',$property))
        $script:book|Add-Member ScriptProperty $property $getter $setter
    }
    $script:insert=[pscustomobject]@{HSet=$set;Text=''}
    $action=[pscustomobject]@{}
    $action|Add-Member ScriptMethod GetDefault {param($Name,$Set)
        [void]$script:events.Add('default:'+ $Name)
        Assert-Model ($Name -cin @('InsertText','Bookmark'))
        if ($Name -ceq 'Bookmark') {$script:fakeHwp.SelectionMode=0;$script:items['Command']=[uint32]99}
        if ($script:fault -cin @('default_false','default_and_release')) {return $false}
        if ($script:fault -ceq 'default_not_bool') {return [int]1}
        return $true
    }
    $action|Add-Member ScriptMethod Execute {param($Name,$Set)
        $script:executeCount++;[void]$script:events.Add('execute:'+ $Name)
        if ($script:fault -ceq 'execute_false') {return $false}
        return $true
    }
    $script:fakeHwp=[pscustomobject]@{SelectionMode=[int]0;HParameterSet=[pscustomobject]@{HInsertText=$script:insert;HBookMark=$script:book};HAction=$action}
    $script:fakeHwp|Add-Member ScriptMethod SetPos {param($List,$Para,$Pos)
        Assert-Model ($List -eq 0 -and $Para -eq 0 -and $Pos -eq 0)
        if ($script:fault -ceq 'seed_position') {return $false};return $true
    }
    $script:fakeHwp|Add-Member ScriptMethod SelectText {param($SP,$SO,$EP,$EO)
        $script:positions=@($SP,$SO,$EP,$EO);$script:fakeHwp.SelectionMode=[int]4
        [void]$script:events.Add('select:'+ $script:index)
        if ($script:fault -ceq 'select_false') {return $false}
        if ($script:fault -ceq 'empty_selection') {$script:fakeHwp.SelectionMode=[int]0}
        return $true
    }
    $script:fakeHwp|Add-Member ScriptMethod GetSelectedPos {param($SL,$SP,$SO,$EL,$EP,$EO)
        $SL.Value=[int]0;$EL.Value=[int]0
        $SP.Value=[int]$script:positions[0];$SO.Value=[int]$script:positions[1]
        $EP.Value=[int]$script:positions[2];$EO.Value=[int]$script:positions[3]
        if ($script:fault -ceq 'wrong_position') {$SO.Value++}
        if ($script:fault -ceq 'wrong_list') {$SL.Value=[int]1}
        if ($script:fault -ceq 'position_false') {return $false}
        return $true
    }
    return [ordered]@{owner=[ordered]@{hwp=$script:fakeHwp};document=[pscustomobject]@{Modified=[int]0};
        failed=$false;seed_attempted=$true;seeded=$true;ranges_attempted=$false;completed_ranges=0;cleanup_error_code=$null;
        parameter_call_site='not_started';parameter_range_index=0;parameter_call_failure=$null;
        range_trace=[Collections.Generic.List[object]]::new();checkpoint={param($Phase,$Index)
            $script:index=$Index;[void]$script:events.Add('gate:'+ $Phase+':'+$Index)
            if ($script:fault -ceq 'gate' -and $Phase -ceq 'bookmark_execute' -and $Index -eq 3) {return $false}
            if ($script:fault -ceq 'move_at_execute' -and $Phase -ceq 'bookmark_execute') {$script:positions[1]++}
            if ($script:fault -ceq 'parameter_at_execute' -and $Phase -ceq 'bookmark_execute') {$script:items['name']='changed'}
            return $true
        }}
}
function Expect-Denied($State,[string]$Code,[scriptblock]$Body) {
    $denied=$false
    try {[void](& $Body)} catch {$denied=$_.Exception.GetBaseException().Message -ceq ('P09_BLOCK645_'+$Code)}
    Assert-Model ($denied -and $State.failed)
}



function Assert-P09Block646CurrentDocument($State) {Assert-P09Block645CurrentDocument $State}
function Assert-P09Block645Selection($Hwp,$Case) {Assert-P09Block658Selection $script:current658 $Hwp $Case}
function New658State {
    $s=Fake-State;$s['selection_observations']=[Collections.Generic.List[object]]::new()
    $script:current658=$s;$script:pointerCalls=0;$script:setReads=0;$script:setsCreated=0
    $script:fakeHwp|Add-Member -Force ScriptMethod GetSelectedPos {$script:pointerCalls++;throw 'FORBIDDEN_POINTER_OUT_API'}
    $script:fakeHwp|Add-Member ScriptMethod CreateSet {param($Name)
        Assert-Model ($Name -ceq 'ListParaPos');$script:setsCreated++
        if ($script:fault -ceq 'create_set_throw') {throw [Runtime.InteropServices.COMException]::new('SECRET',-2147467259)}
        if ($script:fault -ceq 'null_set') {return $null}
        $set=[pscustomobject]@{SetID='ListParaPos';IsSet=$true;Values=@{}}
        if ($script:fault -ceq 'wrong_set_id') {$set.SetID='Other'}
        if ($script:fault -ceq 'unset') {$set.IsSet=$false}
        if ($script:fault -ceq 'bool_not_bool') {$set.IsSet=[int]1}
        $set|Add-Member ScriptMethod ItemExist {param($Key)
            if ($script:fault -ceq 'missing_item' -and $Key -ceq 'Pos') {return $false}
            if ($script:fault -ceq 'itemexist_not_bool') {return [int]1}
            return $this.Values.ContainsKey($Key)
        }
        $set|Add-Member ScriptMethod Item {param($Key)
            $value=$this.Values[$Key]
            if ($script:fault -ceq 'unsigned') {return [uint32]$value}
            if ($Key -ceq 'Pos') {
                switch -CaseSensitive ($script:fault) {
                    'item_bool' {return $true}
                    'item_string' {return '0'}
                    'item_double' {return [double]0}
                    'item_int64' {return [long]0}
                    'item_negative' {return [int]-1}
                    'item_overflow' {return [uint32]::MaxValue}
                    'item_throw' {throw [Runtime.InteropServices.COMException]::new('SECRET',-2147467259)}
                }
            }
            return $value
        }
        return $set
    }
    $script:fakeHwp|Add-Member ScriptMethod GetSelectedPosBySet {param($Start,$End)
        $script:setReads++
        if ($script:fault -ceq 'api_false') {return $false}
        if ($script:fault -ceq 'api_not_bool') {return [int]1}
        if ($script:fault -ceq 'api_throw') {throw [Runtime.InteropServices.COMException]::new('SECRET',-2147467259)}
        foreach ($pair in @(@($Start,0),@($End,2))) {
            $set=$pair[0];$offset=[int]$pair[1]
            $set.Values['List']=[int]0;$set.Values['Para']=[int]$script:positions[$offset];$set.Values['Pos']=[int]$script:positions[$offset+1]
        }
        if ($script:fault -ceq 'wrong_start_list') {$Start.Values['List']=[int]1}
        if ($script:fault -ceq 'wrong_end_list') {$End.Values['List']=[int]1}
        if ($script:fault -ceq 'wrong_start_para') {$Start.Values['Para']++}
        if ($script:fault -ceq 'wrong_start_pos') {$Start.Values['Pos']++}
        if ($script:fault -ceq 'wrong_end_para') {$End.Values['Para']++}
        if ($script:fault -ceq 'wrong_end_pos') {$End.Values['Pos']++}
        if ($script:fault -ceq 'owner_after_read') {$script:fault='owner'}
        return $true
    }
    return $s
}

function Assert-P09Block645Selection($Hwp,$Case) {Invoke-P09SelectionProbe662 $script:current658 $Hwp $Case}
function Probe-State {
    $s=New658State;$s['selection_probe']=[Collections.Generic.List[object]]::new();$s['probe_complete']=$false
    $s['trace']=[ordered]@{probe_complete=$false};$script:pointerCalls=0
    $script:fakeHwp|Add-Member -Force ScriptMethod GetSelectedPos {param($A,$B,$C,$D,$E,$F)
        $script:pointerCalls++;$A.Value=[int]0;$B.Value=[int]0;$C.Value=[int]0;$D.Value=[int]0;$E.Value=[int]0;$F.Value=[int]10
        return ($script:fault -cne 'selection_false')
    }
    $script:fakeHwp|Add-Member ScriptMethod GetPosBySet {
        $set=$this.CreateSet('ListParaPos');$set.Values['List']=[int]0;$set.Values['Para']=[int]0;$set.Values['Pos']=[int]10;return $set
    }
    $script:fakeHwp|Add-Member ScriptMethod GetTextFile {param($Format,$Option)
        Assert-Model ($Format -ceq 'TEXT' -and $Option -cin @('','saveblock:true'))
        if ($script:fault -ceq 'text_throw') {throw [Runtime.InteropServices.COMException]::new('SECRET',-2147467259)}
        if ($script:fault -ceq 'text_bound') {return ('X'*4097)}
        if ($script:fault -ceq 'text_type') {return $true}
        if ($script:fault -ceq 'wrong_text') {return 'PRIVATE_UNEXPECTED_TEXT'}
        $text=if ($Option -ceq '') {(@(Get-P09Block645Cases|ForEach-Object {$_.seed_text}) -join "`r`n")}else{[string](@(Get-P09Block645Cases)[0].selected_text)}
        if ($script:fault -ceq 'terminal_CRLF') {return $text+"`r`n"}
        return $text
    }
    return $s
}
function Run-Probe($s) {
    $stop=$false
    try {Invoke-P09Block653Ranges $s} catch {$stop=$_.Exception.GetBaseException().Message -ceq 'P09_BLOCK645_PROBE_OBSERVATIONS_COMPLETE_NOT_CAPTURE'}
    Assert-Model ($stop -and $s.failed -and $s.probe_complete -and $s.trace.probe_complete)
    Assert-Model ($s.selection_probe.Count -eq 8 -and $script:executeCount -eq 0 -and $s.completed_ranges -eq 0 -and $s.range_trace.Count -eq 0)
    $labels=@('mode_at_entry','caret_before','full_seed_text_digest','selected_text_digest','PowerShell_six_OUT','explicit_dotnet_six_OUT','ParameterSet_selection','caret_and_mode_after')
    Assert-Model (($s.selection_probe|ForEach-Object {$_.label}) -join ',' -ceq ($labels -join ','))
}
Model-Case 'eight_observations_stop_before_any_bookmark_execute_or_save' {
    $s=Probe-State;Run-Probe $s
    Assert-Model ($s.selection_probe[2].value.exact_fixed_text -and $s.selection_probe[3].value.exact_fixed_text)
    Assert-Model ($s.selection_probe[1].value.positions.Count -eq 3 -and $s.selection_probe[4].value.positions.Count -eq 6)
    Assert-Model (-not $s.selection_probe[5].read_returned -and $s.selection_probe[5].error_kind -ceq 'InvalidOperationException')
    $raw=$s.selection_probe|ConvertTo-Json -Depth 12 -Compress
    Assert-Model ($raw -cnotmatch 'B643_ALPHA|PRIVATE|SECRET' -and $script:pointerCalls -eq 1)
}
foreach ($taskFault in @('selection_false','api_false','text_throw','text_bound','text_type','wrong_text','terminal_CRLF')) {
    Model-Case $taskFault {
        $s=Probe-State;$script:fault=$taskFault;Run-Probe $s
        if ($taskFault -ceq 'api_false') {Assert-Model ($s.selection_probe[6].value.returned -eq $false)}
        if ($taskFault -ceq 'selection_false') {Assert-Model ($s.selection_probe[4].value.returned -eq $false)}
        if ($taskFault -cin @('text_throw','text_bound','text_type')) {Assert-Model (-not $s.selection_probe[2].read_returned -and -not $s.selection_probe[3].read_returned)}
        if ($taskFault -ceq 'wrong_text') {Assert-Model (-not $s.selection_probe[2].value.exact_fixed_text)}
        if ($taskFault -ceq 'terminal_CRLF') {Assert-Model ($s.selection_probe[2].value.exact_fixed_text_plus_CRLF -and -not $s.selection_probe[2].value.exact_fixed_text)}
        Assert-Model (($s.selection_probe|ConvertTo-Json -Depth 12 -Compress) -cnotmatch 'PRIVATE_UNEXPECTED_TEXT|SECRET')
    }
}
Model-Case 'same_probe_never_replays' {
    $s=Probe-State;Run-Probe $s;$calls=$script:events.Count
    try {Invoke-P09SelectionProbe662 $s $script:fakeHwp (@(Get-P09Block645Cases)[0])} catch {}
    Assert-Model ($script:events.Count -eq $calls -and $s.selection_probe.Count -eq 8)
}
Model-Case 'owner_failure_stops_before_remaining_reads' {
    $s=Probe-State;$script:fault='owner';$denied=$false
    try {Invoke-P09SelectionProbe662 $s $script:fakeHwp (@(Get-P09Block645Cases)[0])} catch {$denied=$true}
    Assert-Model ($denied -and -not $s.probe_complete -and $s.selection_probe.Count -eq 0 -and $script:pointerCalls -eq 0)
}
foreach ($scenario in @(0,1)) {
    Model-Case ('explicit_reflection_model_'+$scenario) {
        $v=[P09Selection662Reflection]::InspectFixedModel($scenario)
        Assert-Model ($v.ReturnIsBoolean -and $v.Returned -eq ($scenario -eq 0) -and $v.CoordinatesAreInt32 -and ($v.Positions -join ',') -ceq '0,1,2,0,3,4')
    }
}
Model-Case 'reflection_hresult_not_message' {
    $denied=$false;try {[void][P09Selection662Reflection]::InspectFixedModel(2)} catch {
        $denied=$_.Exception.GetBaseException().HResult -eq -2147467259
    };Assert-Model $denied
}
Model-Case 'live_reflection_rejects_managed_objects' {
    $denied=$false;try {[void][P09Selection662Reflection]::ReadExistingCom([object]::new())} catch {$denied=$true}
    Assert-Model $denied
}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    actual_native_started=$false;probe_not_source_capture=$true}|ConvertTo-Json -Depth 5 -Compress
if ($script:failed.Count -ne 0) {exit 2}

