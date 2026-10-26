[CmdletBinding()]param([switch]$ModelsOnly)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
if (-not $ModelsOnly) {throw 'CURSOR769_MODELS_ONLY'}
$script:tests=0;$script:failed=[Collections.Generic.List[string]]::new();$script:outerError=$null
$noise=@()
try {$noise=@(& {
function Check($Condition) {if (-not $Condition) {throw 'CURSOR769_MODEL_ASSERT'}}
function Model([string]$CaseName,[scriptblock]$Body) {$script:tests++;try {& $Body} catch {$script:failed.Add($CaseName)}}
function Assert-P09XrefBinding($Condition,[string]$Code) {if (-not $Condition) {throw ('P09_XREF_BIND_'+$Code)}}
function Release-P58Com($Value) {}
. (Join-Path $PSScriptRoot 'prepared-bookmark768-ports.ps1')
. (Join-Path $PSScriptRoot 'bookmark-target-cursor768.ps1')
. (Join-Path $PSScriptRoot 'prepared-bookmark768-channel.ps1')
function Observe-P09Prepared768Document($State,[string]$Path,[string]$Sha) {if ($script:badOwner) {throw 'P09_XREF_BIND_MODEL_OWNER_DENIED'}}
function New-P768Set([int]$Position) {
    $v=[pscustomobject]@{SetID='ListParaPos';IsSet=$true;values=@{List=[int]0;Para=[int]0;Pos=$Position}}
    $v|Add-Member ScriptMethod ItemExist {param($Key) return $this.values.ContainsKey($Key)}
    $v|Add-Member ScriptMethod Item {param($Key) return $this.values[$Key]}
    return $v
}
function New-ModelState([string]$Stage='initial') {
    $script:badOwner=$false;$script:badDefault=$false;$script:badParameter=$false;$script:badSelected=$false
    $script:badExtent=$false;$script:badText=$false;$script:badBody=$false;$script:executed=0;$script:selectedCalls=0;$script:wholeReads=0;$script:commandValue=[uint32]0
    $book=[pscustomobject]@{name='';type=[uint32]0;HSet=[pscustomobject]@{model=$true}}
    $book|Add-Member ScriptProperty Command {[uint32]$script:commandValue} {param($Value) $script:commandValue=if ($script:badParameter) {[uint32]2} else {[uint32]$Value}}
    $action=[pscustomobject]@{}
    $action|Add-Member ScriptMethod GetDefault {param($Name,$Set) Check ($Name -ceq 'Bookmark');return (-not $script:badDefault)}
    $action|Add-Member ScriptMethod Execute {param($Name,$Set) Check ($Name -ceq 'Bookmark');$script:executed++;return $true}
    $hwp=[pscustomobject]@{SelectionMode=[int]1;HAction=$action;HParameterSet=[pscustomobject]@{HBookMark=$book}}
    $hwp|Add-Member ScriptMethod GetTextFile {param($Format,$Options)
        Check ($Format -ceq 'TEXT')
        if ($Options -ceq 'saveblock:true') {if ($script:badText) {return 'WRONG'};return 'B643_ALPHA'}
        Check ($Options -ceq 'saveblock:false');$script:wholeReads++
        if ($script:badBody -and $script:wholeReads -gt 1) {return 'CHANGED_BODY'};return 'FIXED_WHOLE_BODY'
    }
    $hwp|Add-Member ScriptMethod SetPos {param($List,$Para,$Pos) Check ($List -eq 0 -and $Para -cin @(0,8) -and $Pos -eq 0);return $true}
    $hwp|Add-Member ScriptMethod GetPosBySet {return (New-P768Set 16)}
    $hwp|Add-Member ScriptMethod CreateSet {param($Name) Check ($Name -ceq 'ListParaPos');return (New-P768Set 0)}
    $hwp|Add-Member ScriptMethod GetSelectedPosBySet {param($Start,$End)
        $script:selectedCalls++;if ($script:badSelected) {return $false}
        $Start.values.Pos=[int]19;$End.values.Pos=if ($script:badExtent) {[int]30} else {[int]29};return $true
    }
    $trace=[ordered]@{navigation=[Collections.ArrayList]::new()}
    if ($Stage -ceq 'reopened') {[void]$trace.navigation.Add([ordered]@{model_prior_query=$true})}
    return [ordered]@{failed=$false;owner=[pscustomobject]@{hwp=$hwp};trace=$trace}
}
function Expect-QueryFailure($State,[string]$Code) {
    $caught=$false
    try {Invoke-P09BookmarkCursor768 $State initial 'fixed.hwpx' ('a'*64)} catch {$caught=$_.Exception.GetBaseException().Message -cmatch $Code}
    Check $caught
}
Model 'success_initial_native_origin_not_fixed_bias' {$s=New-ModelState;Invoke-P09BookmarkCursor768 $s initial 'fixed.hwpx' ('a'*64);Check ($script:executed -eq 1 -and $script:selectedCalls -eq 2 -and $s.trace.navigation[0].complete -and $s.trace.navigation[0].selected_characters -eq 10)}
Model 'success_independent_reopened_source' {$s=New-ModelState reopened;Invoke-P09BookmarkCursor768 $s reopened 'reopened.hwpx' ('b'*64);Check ($script:executed -eq 1 -and $s.trace.navigation.Count -eq 2 -and $s.trace.navigation[1].complete)}
Model 'owner_denied_before_execute' {$s=New-ModelState;$script:badOwner=$true;Expect-QueryFailure $s 'MODEL_OWNER_DENIED';Check ($script:executed -eq 0)}
Model 'default_denied_no_execute' {$s=New-ModelState;$script:badDefault=$true;Expect-QueryFailure $s 'CURSOR768_DEFAULT_FAILED';Check ($script:executed -eq 0)}
Model 'typed_goto_parameter_denied_no_execute' {$s=New-ModelState;$script:badParameter=$true;Expect-QueryFailure $s 'CURSOR768_TYPED_GOTO_PARAMETERS';Check ($script:executed -eq 0)}
Model 'selection_api_false_no_fallback' {$s=New-ModelState;$script:badSelected=$true;Expect-QueryFailure $s 'CURSOR768_SELECTED_POSITION_FAILED';Check ($script:executed -eq 1 -and $script:selectedCalls -eq 1)}
Model 'wrong_exact_selection_extent' {$s=New-ModelState;$script:badExtent=$true;Expect-QueryFailure $s 'CURSOR768_STABLE_SELECTION_EXTENT';Check ($script:executed -eq 1)}
Model 'selected_text_identity_is_required' {$s=New-ModelState;$script:badText=$true;Expect-QueryFailure $s 'CURSOR768_EXACT_SELECTED_SOURCE_TEXT';Check ($script:executed -eq 1)}
Model 'whole_body_unchanged_after_goto' {$s=New-ModelState;$script:badBody=$true;Expect-QueryFailure $s 'CURSOR768_WHOLE_TEXT_CHANGED';Check ($script:executed -eq 1)}
Model 'no_save_or_link_activation_or_generic_fallback' {
    $text=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'bookmark-target-cursor768.ps1'))
    Check ($text.Contains("`$book.Command=[uint32]1") -and $text.Contains(".Execute('Bookmark',`$set)"))
    foreach ($forbidden in @('.SaveAs(','.PutFieldText(','.MoveToField(','.CreatePageImage(','.Run(', 'New-Object -ComObject','GetActiveObject')) {Check (-not $text.Contains($forbidden))}
}

function Invoke-P09XrefPreassignedHostMessage($Channel,$Index,$Operation,[string]$Step) {return $null}
Model 'real_junction_output_parent_denied_before_directory_creation' {
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $base=[IO.Path]::GetFullPath((Join-Path $root 'target\p09-bookmark-cursor771-junction-model-once'))
    Check ($base.StartsWith(($root+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase))
    Check (-not [IO.Directory]::Exists($base))
    $real=Join-Path $base 'real';$link=Join-Path $base 'link';$slot=Join-Path $link 'slot';$realSlot=Join-Path $real 'slot'
    try {
        [void][IO.Directory]::CreateDirectory($real)
        [void](New-Item -ItemType Junction -Path $link -Target $real -ErrorAction Stop)
        $s=[ordered]@{failed=$false;cursor=0;run=$slot;case_index=1;preassigned_channel=$null;slot_created=$false;trace=[ordered]@{phase=$null};original='unused'}
        $caught=$false
        try {Invoke-P09Prepared768Step $s prepare_slot} catch {$caught=$_.Exception.GetBaseException().Message -ceq 'P09_XREF_BIND_PREPARED_OUTPUT_PARENT'}
        Check ($caught -and -not $s.slot_created -and -not [IO.Directory]::Exists($realSlot))
    } finally {
        # Only these create-new, verified in-workspace empty paths. No recursion.
        if ([IO.Directory]::Exists($link)) {[IO.Directory]::Delete($link)}
        if ([IO.Directory]::Exists($realSlot)) {[IO.Directory]::Delete($realSlot)}
        if ([IO.Directory]::Exists($real)) {[IO.Directory]::Delete($real)}
        if ([IO.Directory]::Exists($base)) {[IO.Directory]::Delete($base)}
    }
}

})} catch {
    $script:outerError=[ordered]@{kind=$_.Exception.GetType().Name;error_id=$_.FullyQualifiedErrorId;line=$_.InvocationInfo.ScriptLineNumber}
}
$errors=if ($null -ne $script:outerError -or $noise.Count -ne 0) {1} else {0}
[ordered]@{run=$script:tests;errors=$errors;failures=$script:failed.Count;skipped=0;actual_native_started=$false;
    failed_test_ids=$script:failed.ToArray();outer_error=$script:outerError;unexpected_output_count=$noise.Count;
    unexpected_output_types=@($noise|ForEach-Object {$_.GetType().Name})}|ConvertTo-Json -Depth 6 -Compress
if ($errors -ne 0 -or $script:failed.Count -ne 0) {exit 2}
