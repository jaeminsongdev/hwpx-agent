# Executes actual port function bodies on in-memory models only. No Native/file IO.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'MODEL_ONLY_REQUIRED'}
. (Join-Path $PSScriptRoot 'block-bookmark-source645-ports.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-source653-typed.ps1')

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
        if ($Name -ceq 'Bookmark') {$script:fakeHwp.SelectionMode=0;$script:book.Command=[uint32]99}
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


Model-Case 'typed_eight_no_generic_items_and_exact_order' {
    $s=Fake-State;Invoke-P09Block653Ranges $s
    Assert-Model (-not $s.failed -and $s.completed_ranges -eq 8 -and $script:executeCount -eq 8 -and $script:releases -eq 32)
    Assert-Model ($null -eq $s.parameter_call_failure)
    $events=$script:events.ToArray()
    $defaults=@(for ($i=0;$i -lt $events.Length;$i++) {if ($events[$i] -ceq 'default:Bookmark') {$i}})
    foreach ($at in $defaults) {
        # GetDefault resets Command, then explicit typed name/type/Command writes.
        Assert-Model ($events[$at+2] -ceq 'set:name' -and $events[$at+3] -ceq 'set:type' -and $events[$at+4] -ceq 'set:Command')
    }
    $calls=$script:events.Count
    try {Invoke-P09Block653Ranges $s;throw 'UNEXPECTED'} catch {
        Assert-Model ($_.Exception.GetBaseException().Message -ceq 'P09_BLOCK645_RANGES_NO_RETRY_OR_UNSEEDED')
    }
    Assert-Model ($calls -eq $script:events.Count)
}
foreach ($pair in @(@('default_false','BOOKMARK_DEFAULT_FAILED'),@('default_not_bool','BOOKMARK_DEFAULT_FAILED'),
    @('wrong_type','BOOKMARK_PARAMETER_READBACK'),@('wrong_name','BOOKMARK_PARAMETER_READBACK'),
    @('select_false','BOOKMARK_SELECT_FAILED'),@('empty_selection','NONEMPTY_NATIVE_SELECTION_REQUIRED'),
    @('wrong_position','EXACT_NATIVE_SELECTION_POSITIONS'),@('wrong_list','EXACT_NATIVE_SELECTION_POSITIONS'),
    @('position_false','EXACT_NATIVE_SELECTION_POSITIONS'),@('move_at_execute','EXACT_NATIVE_SELECTION_POSITIONS'),
    @('parameter_at_execute','BOOKMARK_PARAMETER_READBACK'),@('execute_false','BOOKMARK_EXECUTE_EFFECT_UNKNOWN'))) {
    Model-Case $pair[0] {
        $s=Fake-State;$script:fault=$pair[0]
        Expect-Denied $s $pair[1] {Invoke-P09Block653Ranges $s}
        $expected=if ($pair[0] -ceq 'execute_false') {1}else{0}
        Assert-Model ($s.completed_ranges -eq 0 -and $script:executeCount -eq $expected -and $s.parameter_call_failure.range_index -eq 1)
    }
}
foreach ($kind in @('put','get')) {foreach ($property in @('name','type','Command')) {
    Model-Case ('throw_'+$kind+'_'+$property) {
        $s=Fake-State;$script:fault='throw_'+$kind+'_'+$property
        $denied=$false;try {Invoke-P09Block653Ranges $s} catch {$denied=$true}
        $d=$s.parameter_call_failure
        Assert-Model ($denied -and $s.failed -and $script:executeCount -eq 0 -and $s.completed_ranges -eq 0)
        Assert-Model ($d.call_site -ceq ($kind+'_'+$property.ToLowerInvariant()) -and $d.exception_kind -ceq 'COMException' -and $d.hresult -ceq '0x80004005')
        Assert-Model (($d|ConvertTo-Json -Compress) -cnotmatch 'SECRET_NOT_PRINTED')
        $calls=$script:events.Count;try {Invoke-P09Block653Ranges $s} catch {}
        Assert-Model ($calls -eq $script:events.Count)
    }
}}
Model-Case 'host_stop_retains_two_and_never_retries' {
    $s=Fake-State;$script:fault='gate'
    Expect-Denied $s 'CURRENT_HOST_BOUNDARY_DENIED' {Invoke-P09Block653Ranges $s}
    Assert-Model ($s.completed_ranges -eq 2 -and $script:executeCount -eq 2 -and $s.parameter_call_failure.range_index -eq 3)
}
Model-Case 'owner_changed_before_parameter_calls' {
    $s=Fake-State;$script:fault='owner'
    Expect-Denied $s 'CURRENT_ADMITTED_OWNER' {Invoke-P09Block653Ranges $s}
    Assert-Model ($script:executeCount -eq 0 -and $s.parameter_call_failure.call_site -ceq 'bookmark_prepare')
}
Model-Case 'unseeded_no_calls' {
    $s=Fake-State;$s.seeded=$false
    try {Invoke-P09Block653Ranges $s;throw 'UNEXPECTED'} catch {
        Assert-Model ($_.Exception.GetBaseException().Message -ceq 'P09_BLOCK645_RANGES_NO_RETRY_OR_UNSEEDED')
    }
    Assert-Model ($script:events.Count -eq 0)
}
Model-Case 'release_failure_is_not_success' {
    $s=Fake-State;$script:fault='release'
    Expect-Denied $s 'PARAMETER_REFERENCE_RELEASE_UNCONFIRMED' {Invoke-P09Block653Ranges $s}
    Assert-Model ($s.parameter_call_failure.call_site -ceq 'release_references' -and $s.completed_ranges -eq 1 -and $script:executeCount -eq 1)
}
Model-Case 'primary_diagnostic_not_masked_by_release' {
    $s=Fake-State;$script:fault='default_and_release'
    Expect-Denied $s 'BOOKMARK_DEFAULT_FAILED' {Invoke-P09Block653Ranges $s}
    Assert-Model ($s.parameter_call_failure.call_site -ceq 'get_default' -and $script:executeCount -eq 0 -and $null -ne $s.cleanup_error_code)
}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    actual_native_started=$false;generic_item_calls=0}|ConvertTo-Json -Depth 6 -Compress
if ($script:failed.Count -ne 0) {exit 2}


