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



$rows=@()
foreach ($taskFault in @('throw_put_Command','throw_get_name','throw_get_type','throw_get_Command')) {
    $s=Fake-State;$script:fault=$taskFault;$denied=$false
    try {Invoke-P09Block653Ranges $s} catch {$denied=$true}
    $rows+=@{fault=$taskFault;denied=$denied;failed=$s.failed;executions=$script:executeCount;completed=$s.completed_ranges;diagnostic=$s.parameter_call_failure}
}
@{state='OBSERVED_MODEL_ONLY_EXCEPTION_ADAPTER';rows=$rows;Native_started=$false}|ConvertTo-Json -Depth 5 -Compress

