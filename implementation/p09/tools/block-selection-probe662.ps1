# Diagnostic observations only. Always stops BEFORE Bookmark Execute; no fallback
# to product/capture acceptance, no SaveAs, no selected-text publication.
Set-StrictMode -Version Latest
function Initialize-P09SelectionProbe662 {
    Add-Type -Path (Join-Path $PSScriptRoot 'block-selection-probe662-reflection.cs') -ErrorAction Stop
}
function Get-P09Selection662Mode($Hwp) {
    $v=$Hwp.SelectionMode
    return [ordered]@{is_int32=($v -is [int]);value=$(if ($v -is [int]) {$v}else{$null})}
}
function Get-P09Selection662Text($Hwp,[bool]$Selected) {
    $option=if ($Selected) {'saveblock:true'}else{''}
    $text=$Hwp.GetTextFile('TEXT',$option)
    Assert-P09Block645 ($text -is [string] -and $text.Length -le 4096) 'PROBE_TEXT_TYPE_OR_BOUND'
    $expected=if ($Selected) {[string](@(Get-P09Block645Cases)[0].selected_text)}else{
        (@(Get-P09Block645Cases|ForEach-Object {$_.seed_text}) -join "`r`n")}
    $bytes=[Text.UTF8Encoding]::new($false,$true).GetBytes($text)
    $sha=[Security.Cryptography.SHA256]::Create()
    try {$digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    return [ordered]@{character_count=$text.Length;UTF8_bytes=$bytes.Length;sha256=$digest;
        exact_fixed_text=($text -ceq $expected);exact_fixed_text_plus_CRLF=($text -ceq ($expected+"`r`n"));raw_text_present=$false}
}
function Get-P09Selection662Caret($State,$Hwp) {
    $set=$null
    try {$set=$Hwp.GetPosBySet();$p=Read-P09Block658Position $set;return [ordered]@{positions=@($p[0],$p[1],$p[2])}}
    finally {if ($null -ne $set) {Release-P09Block645References $State @($set)}}
}
function Get-P09Selection662Pointer($Hwp) {
    [int]$a=-1;[int]$b=-1;[int]$c=-1;[int]$d=-1;[int]$e=-1;[int]$f=-1
    $v=$Hwp.GetSelectedPos([ref]$a,[ref]$b,[ref]$c,[ref]$d,[ref]$e,[ref]$f)
    return [ordered]@{return_is_bool=($v -is [bool]);returned=$(if ($v -is [bool]) {$v}else{$null});positions=@($a,$b,$c,$d,$e,$f)}
}
function Get-P09Selection662SetInfo($Set) {
    if ($null -eq $Set) {return [ordered]@{present=$false}}
    $id=$Set.SetID;$valid=$Set.IsSet;$keys=[ordered]@{}
    foreach ($key in @('List','Para','Pos')) {$v=$Set.ItemExist($key);$keys[$key]=[ordered]@{is_bool=($v -is [bool]);exists=$(if ($v -is [bool]) {$v}else{$null})}}
    return [ordered]@{present=$true;expected_SetID=($id -is [string] -and $id -ceq 'ListParaPos');IsSet_is_bool=($valid -is [bool]);
        IsSet=$(if ($valid -is [bool]) {$valid}else{$null});keys=$keys}
}
function Get-P09Selection662Sets($State,$Hwp) {
    $refs=[Collections.ArrayList]::new()
    try {
        $before=Get-P09Selection662Mode $Hwp
        $a=$Hwp.CreateSet('ListParaPos');[void]$refs.Add($a)
        $b=$Hwp.CreateSet('ListParaPos');[void]$refs.Insert(0,$b)
        $info=@((Get-P09Selection662SetInfo $a),(Get-P09Selection662SetInfo $b))
        $afterCreate=Get-P09Selection662Mode $Hwp
        $v=$Hwp.GetSelectedPosBySet($a,$b)
        $result=[ordered]@{mode_before=$before;mode_after_CreateSet=$afterCreate;before=$info;return_is_bool=($v -is [bool]);
            returned=$(if ($v -is [bool]) {$v}else{$null});after=@((Get-P09Selection662SetInfo $a),(Get-P09Selection662SetInfo $b));positions=$null}
        if ($v -is [bool] -and $v) {$x=Read-P09Block658Position $a;$y=Read-P09Block658Position $b;$result.positions=@($x[0],$x[1],$x[2],$y[0],$y[1],$y[2])}
        return $result
    } finally {Release-P09Block645References $State $refs}
}
function Invoke-P09Selection662Observation($State,[string]$Label,[scriptblock]$Read) {
    Assert-P09Block645 (-not $State.failed -and $State.selection_probe.Count -lt 8 -and $State.probe_complete -is [bool] -and -not $State.probe_complete) 'PROBE_STOP_OR_BOUND'
    Assert-P09Block646CurrentDocument $State
    $row=[ordered]@{label=$Label;read_returned=$false;value=$null;error_kind=$null;hresult=$null}
    try {$row.value=& $Read;$row.read_returned=$true}
    catch {
        $e=$_.Exception.GetBaseException();$kind=$e.GetType().Name
        if ($kind -cnotin @('COMException','RuntimeException','InvalidOperationException','ArgumentException','MissingMethodException')) {$kind='OtherException'}
        $row.error_kind=$kind;$row.hresult='0x'+$e.HResult.ToString('X8')
    }
    # Owner/cleanup failures terminate the diagnostic rather than continuing.
    Assert-P09Block646CurrentDocument $State
    Assert-P09Block645 (-not $State.failed -and $null -eq $State.cleanup_error_code) 'PROBE_REFERENCE_CLEANUP'
    [void]$State.selection_probe.Add($row)
}
function Invoke-P09SelectionProbe662($State,$Hwp,$Case) {
    Assert-P09Block645 ($Case.case_index -eq 1 -and $State.completed_ranges -eq 0 -and $State.selection_probe.Count -eq 0 -and -not $State.probe_complete) 'PROBE_FIRST_RANGE_ONCE'
    Invoke-P09Selection662Observation $State 'mode_at_entry' {Get-P09Selection662Mode $Hwp}
    Invoke-P09Selection662Observation $State 'caret_before' {Get-P09Selection662Caret $State $Hwp}
    Invoke-P09Selection662Observation $State 'full_seed_text_digest' {Get-P09Selection662Text $Hwp $false}
    Invoke-P09Selection662Observation $State 'selected_text_digest' {Get-P09Selection662Text $Hwp $true}
    Invoke-P09Selection662Observation $State 'PowerShell_six_OUT' {Get-P09Selection662Pointer $Hwp}
    Invoke-P09Selection662Observation $State 'explicit_dotnet_six_OUT' {[P09Selection662Reflection]::ReadExistingCom($Hwp)}
    Invoke-P09Selection662Observation $State 'ParameterSet_selection' {Get-P09Selection662Sets $State $Hwp}
    Invoke-P09Selection662Observation $State 'caret_and_mode_after' {[ordered]@{caret=(Get-P09Selection662Caret $State $Hwp);mode=(Get-P09Selection662Mode $Hwp)}}
    Assert-P09Block645 ($State.selection_probe.Count -eq 8 -and $State.completed_ranges -eq 0) 'PROBE_COMPLETE_SET'
    $State.probe_complete=$true;$State.trace.probe_complete=$true
    # This is an expected diagnostic stop, NEVER a successful source capture.
    throw 'P09_BLOCK645_PROBE_OBSERVATIONS_COMPLETE_NOT_CAPTURE'
}
