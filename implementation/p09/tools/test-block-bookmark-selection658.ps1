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
Model-Case 'all8_exact_typed_ranges_and16_fresh_set_reads_no_pointer_calls' {
    $s=New658State;Invoke-P09Block653Ranges $s
    Assert-Model (-not $s.failed -and $s.completed_ranges -eq 8 -and $s.selection_observations.Count -eq 16)
    Assert-Model ($script:executeCount -eq 8 -and $script:setReads -eq 16 -and $script:pointerCalls -eq 0 -and $script:setsCreated -eq 32 -and $script:releases -eq 64)
    for ($i=0;$i -lt 16;$i++) {
        $row=$s.selection_observations[$i]
        Assert-Model ($row.exact_match -and $row.returned -and $row.api -ceq 'GetSelectedPosBySet' -and $row.range_index -eq ([int][Math]::Floor($i/2)+1) -and $row.read_index -eq $i+1)
    }
}
Model-Case 'unsigned32_positions_keep_exact_semantics' {
    $s=New658State;$script:fault='unsigned';Invoke-P09Block653Ranges $s
    Assert-Model ($s.completed_ranges -eq 8 -and $s.selection_observations.Count -eq 16 -and $script:pointerCalls -eq 0)
}
foreach ($pair in @(@('api_false','SELECTION_SET_READ_FAILED'),@('api_not_bool','SELECTION_SET_READ_FAILED'),
    @('null_set','SELECTION_SET_NULL'),@('wrong_set_id','SELECTION_SET_ID'),@('unset','SELECTION_SET_INVALID'),
    @('bool_not_bool','SELECTION_SET_INVALID'),@('missing_item','SELECTION_SET_ITEM_MISSING'),@('itemexist_not_bool','SELECTION_SET_ITEM_MISSING'),
    @('item_bool','SELECTION_SET_ITEM_TYPE'),@('item_string','SELECTION_SET_ITEM_TYPE'),@('item_double','SELECTION_SET_ITEM_TYPE'),
    @('item_int64','SELECTION_SET_ITEM_TYPE'),@('item_negative','SELECTION_SET_ITEM_TYPE'),@('item_overflow','SELECTION_SET_ITEM_TYPE'),
    @('wrong_start_list','EXACT_NATIVE_SELECTION_POSITIONS'),@('wrong_end_list','EXACT_NATIVE_SELECTION_POSITIONS'),
    @('wrong_start_para','EXACT_NATIVE_SELECTION_POSITIONS'),@('wrong_start_pos','EXACT_NATIVE_SELECTION_POSITIONS'),
    @('wrong_end_para','EXACT_NATIVE_SELECTION_POSITIONS'),@('wrong_end_pos','EXACT_NATIVE_SELECTION_POSITIONS'))) {
    Model-Case $pair[0] {
        $s=New658State;$script:fault=$pair[0]
        Expect-Denied $s $pair[1] {Invoke-P09Block653Ranges $s}
        Assert-Model ($script:executeCount -eq 0 -and $s.completed_ranges -eq 0 -and $script:pointerCalls -eq 0)
        Assert-Model ($s.parameter_call_failure.call_site -ceq 'assert_selection' -and $s.selection_observations.Count -eq 1 -and -not $s.selection_observations[0].exact_match)
        Assert-Model (($s.selection_observations|ConvertTo-Json -Depth 5 -Compress) -cnotmatch 'SECRET')
        $calls=$script:events.Count;try {Invoke-P09Block653Ranges $s} catch {}
        Assert-Model ($calls -eq $script:events.Count)
    }
}
foreach ($taskFault in @('create_set_throw','api_throw','item_throw')) {
    Model-Case $taskFault {
        $s=New658State;$script:fault=$taskFault;$denied=$false
        try {Invoke-P09Block653Ranges $s} catch {$denied=$true}
        Assert-Model ($denied -and $s.failed -and $s.parameter_call_failure.hresult -ceq '0x80004005' -and $script:executeCount -eq 0)
    }
}
Model-Case 'selection_moved_after_host_wait_is_denied_before_execute' {
    $s=New658State;$script:fault='move_at_execute'
    Expect-Denied $s 'EXACT_NATIVE_SELECTION_POSITIONS' {Invoke-P09Block653Ranges $s}
    Assert-Model ($script:executeCount -eq 0 -and $s.selection_observations.Count -eq 2 -and $s.selection_observations[0].exact_match -and -not $s.selection_observations[1].exact_match)
}
Model-Case 'owner_changed_after_set_read_is_denied' {
    $s=New658State;$script:fault='owner_after_read'
    Expect-Denied $s 'CURRENT_ADMITTED_OWNER' {Invoke-P09Block653Ranges $s}
    Assert-Model ($script:executeCount -eq 0 -and -not $s.selection_observations[0].exact_match)
}
Model-Case 'readback_trace_hard_limit' {
    $s=New658State
    for ($i=0;$i -lt 16;$i++) {[void]$s.selection_observations.Add(@{})}
    Expect-Denied $s 'SELECTION_READBACK_BOUND' {Invoke-P09Block653Ranges $s}
    Assert-Model ($script:setReads -eq 0 -and $script:executeCount -eq 0)
}
Model-Case 'empty_selection_remains_denied' {
    $s=New658State;$script:fault='empty_selection'
    Expect-Denied $s 'NONEMPTY_NATIVE_SELECTION_REQUIRED' {Invoke-P09Block653Ranges $s}
    Assert-Model ($script:setReads -eq 0 -and $script:executeCount -eq 0)
}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    actual_native_started=$false;pointer_out_api_calls=0;position_requirement_weakened=$false}|ConvertTo-Json -Depth 6 -Compress
if ($script:failed.Count -ne 0) {exit 2}

