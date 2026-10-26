# Only typed Bookmark Command=1 (goto) on existing source; no insertion/save/link click.
Set-StrictMode -Version Latest
function Get-P09Cursor768TextDigest([string]$Text) {
    Assert-P09XrefBinding ($Text.Length -le 65536) 'CURSOR768_TEXT_BOUND'
    $bytes=[Text.UTF8Encoding]::new($false,$true).GetBytes($Text);$hash=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}
}
function Read-P09Cursor768Position($Set) {
    Assert-P09XrefBinding ($null -ne $Set -and $Set.SetID -is [string] -and $Set.SetID -ceq 'ListParaPos' -and $Set.IsSet -is [bool] -and $Set.IsSet) 'CURSOR768_TYPED_POSITION_SET'
    $result=[Collections.Generic.List[int]]::new()
    foreach ($key in @('List','Para','Pos')) {
        $has=$Set.ItemExist($key);Assert-P09XrefBinding ($has -is [bool] -and $has) 'CURSOR768_POSITION_KEY'
        $value=$Set.Item($key)
        Assert-P09XrefBinding (($value -is [int] -or $value -is [uint32]) -and [long]$value -ge 0 -and [long]$value -le [int]::MaxValue) 'CURSOR768_POSITION_TYPE'
        $result.Add([int]$value)
    }
    return ,$result.ToArray()
}
function Read-P09Cursor768Selection($Hwp) {
    $start=$null;$end=$null
    try {
        $mode=$Hwp.SelectionMode;Assert-P09XrefBinding ($mode -is [int] -and ($mode -band 15) -ne 0) 'CURSOR768_NONEMPTY_SELECTION'
        $start=$Hwp.CreateSet('ListParaPos');$end=$Hwp.CreateSet('ListParaPos')
        $returned=$Hwp.GetSelectedPosBySet($start,$end)
        Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'CURSOR768_SELECTED_POSITION_FAILED'
        $a=Read-P09Cursor768Position $start;$b=Read-P09Cursor768Position $end
        return ,@($a[0],$a[1],$a[2],$b[0],$b[1],$b[2])
    } finally {Release-P58Com $end;Release-P58Com $start}
}
function Invoke-P09BookmarkCursor768($State,[string]$Stage,[string]$Path,[string]$Sha) {
    Assert-P09XrefBinding ($Stage -cin @('initial','reopened') -and -not $State.failed -and $State.trace.navigation.Count -eq $(if ($Stage -ceq 'initial') {0} else {1})) 'CURSOR768_QUERY_ONCE'
    Observe-P09Prepared768Document $State $Path $Sha
    $row=[ordered]@{stage=$Stage;source_sha256=$Sha;complete=$false;bookmark_command=1;target_name_sha256=(Get-P09Cursor768TextDigest 'p09_renamed737');
        selected_text_sha256=$null;selected_UTF8_bytes=$null;selected_characters=$null;origin=$null;selection_positions=$null;confirmation_selection_positions=$null;
        whole_text_before_sha256=$null;whole_text_after_sha256=$null;source_bytes_rewritten=$false;hyperlink_activation_invoked=$false}
    [void]$State.trace.navigation.Add($row)
    $hwp=$State.owner.hwp;$refs=[Collections.ArrayList]::new()
    try {
        $whole=$hwp.GetTextFile('TEXT','saveblock:false');Assert-P09XrefBinding ($whole -is [string] -and $whole.Length -gt 0) 'CURSOR768_WHOLE_TEXT_BEFORE'
        $row.whole_text_before_sha256=Get-P09Cursor768TextDigest $whole
        $returned=$hwp.SetPos(0,0,0);Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'CURSOR768_ORIGIN_SET'
        $position=$hwp.GetPosBySet();[void]$refs.Add($position);$origin=Read-P09Cursor768Position $position
        Assert-P09XrefBinding ($origin[0] -eq 0 -and $origin[1] -eq 0) 'CURSOR768_ORIGIN_DOCUMENT'
        $row.origin=@($origin[0],$origin[1],$origin[2])
        $returned=$hwp.SetPos(0,8,0);Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'CURSOR768_MOVE_AWAY'
        $parameters=$hwp.HParameterSet;[void]$refs.Insert(0,$parameters)
        $book=$parameters.HBookMark;[void]$refs.Insert(0,$book)
        $set=$book.HSet;[void]$refs.Insert(0,$set)
        $action=$hwp.HAction;[void]$refs.Insert(0,$action)
        $returned=$action.GetDefault('Bookmark',$set);Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'CURSOR768_DEFAULT_FAILED'
        # Exact installed typed property casing, already observed by652/670.
        $book.name='p09_renamed737';$book.type=[uint32]1;$book.Command=[uint32]1
        Assert-P09XrefBinding ($book.name -is [string] -and $book.name -ceq 'p09_renamed737' -and
            ($book.type -is [uint32] -or $book.type -is [int]) -and [long]$book.type -eq 1 -and
            ($book.Command -is [uint32] -or $book.Command -is [int]) -and [long]$book.Command -eq 1) 'CURSOR768_TYPED_GOTO_PARAMETERS'
        $returned=$action.Execute('Bookmark',$set);Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'CURSOR768_GOTO_FAILED_EFFECT_UNKNOWN'
        $a=Read-P09Cursor768Selection $hwp;$b=Read-P09Cursor768Selection $hwp
        $row.selection_positions=$a;$row.confirmation_selection_positions=$b
        Assert-P09XrefBinding (($a -join ',') -ceq ($b -join ',') -and $a[0] -eq 0 -and $a[1] -eq 0 -and $a[3] -eq 0 -and $a[4] -eq 0 -and
            $a[2] -ge $origin[2] -and $a[5]-$a[2] -eq 10) 'CURSOR768_STABLE_SELECTION_EXTENT'
        $selected=$hwp.GetTextFile('TEXT','saveblock:true');Assert-P09XrefBinding ($selected -is [string] -and $selected -ceq 'B643_ALPHA') 'CURSOR768_EXACT_SELECTED_SOURCE_TEXT'
        $row.selected_text_sha256=Get-P09Cursor768TextDigest $selected;$row.selected_characters=$selected.Length
        $row.selected_UTF8_bytes=[Text.Encoding]::UTF8.GetByteCount($selected)
        $whole=$hwp.GetTextFile('TEXT','saveblock:false');Assert-P09XrefBinding ($whole -is [string] -and $whole.Length -gt 0) 'CURSOR768_WHOLE_TEXT_AFTER'
        $row.whole_text_after_sha256=Get-P09Cursor768TextDigest $whole
        Assert-P09XrefBinding ($row.whole_text_before_sha256 -ceq $row.whole_text_after_sha256) 'CURSOR768_WHOLE_TEXT_CHANGED'
        Observe-P09Prepared768Document $State $Path $Sha;$row.complete=$true
    } finally {foreach ($reference in $refs) {Release-P58Com $reference}}
}
