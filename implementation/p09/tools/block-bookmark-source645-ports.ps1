# Fixed source authoring functions only. No launcher, activation, file IO or permit.
# The future owned worker must supply the live host checkpoint. This library is
# NOT an independently executable Native entry or proof that Native succeeded.
Set-StrictMode -Version Latest

function Assert-P09Block645([bool]$Condition,[string]$Code) {
    if (-not $Condition) {throw ('P09_BLOCK645_'+$Code)}
}

function Get-P09Block645Cases {
    # ASCII source also decodes identically in Windows PowerShell 5.1/x86.
    $hangul=([string][char]0xd55c)+[char]0xae00
    $content=$hangul+[char]0xb0b4+[char]0xc6a9
    $end=[string][char]0xb05d
    $seeds=@(@('','B643_ALPHA',' right'),@('left ','two words',''),@('head ',$content,' tail'),
        @('','A&B<C>',''),@('prefix:','0123456789',':suffix'),@('before ',('Mixed_'+$hangul+'_123'),' after'),
        @('123456 ','RANGE',' 789'),@('!',$end,'?'))
    for ($i=0;$i -lt 8;$i++) {
        $prefix=[string]$seeds[$i][0];$target=[string]$seeds[$i][1];$suffix=[string]$seeds[$i][2]
        [ordered]@{case_index=$i+1;paragraph_index=$i;bookmark_name=('p09_block643_'+($i+1).ToString('00'));
            seed_text=$prefix+$target+$suffix;selected_text=$target;
            selection=[ordered]@{spara=$i;spos=$prefix.Length;epara=$i;epos=$prefix.Length+$target.Length}}
    }
}

function Assert-P09Block645CurrentDocument($State) {
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    Assert-P09Block645 ($State.owner.preassigned_admitted -is [bool] -and $State.owner.preassigned_admitted -and
        -not $State.owner.preassigned_close_attempted -and (Test-P58Owner $State.owner) -eq $true) 'CURRENT_ADMITTED_OWNER'
    $pointers=[Collections.Generic.List[IntPtr]]::new()
    try {
        $collection=$State.owner.hwp.XHwpDocuments
        $active=$collection.Active_XHwpDocument
        $heldCollection=Get-P09XrefHeldComIdentity $State.owner.documents $pointers
        $currentCollection=Get-P09XrefHeldComIdentity $collection $pointers
        $heldDocument=Get-P09XrefHeldComIdentity $State.document $pointers
        $currentDocument=Get-P09XrefHeldComIdentity $active $pointers
        $count=$collection.Count;$name=$State.document.FullName;$mode=$State.owner.hwp.EditMode
        Assert-P09Block645 ($heldCollection -eq $currentCollection -and $heldDocument -eq $currentDocument -and
            $count -is [int] -and $count -eq 1 -and $name -is [string] -and $name.Length -eq 0 -and
            $mode -is [int] -and $mode -eq 1 -and (Test-P58Owner $State.owner) -eq $true) 'SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'
    } finally {foreach ($pointer in $pointers) {[void][Runtime.InteropServices.Marshal]::Release($pointer)}}
}

function Enter-P09Block645Boundary($State,[string]$Phase,[int]$Index) {
    Assert-P09Block645 ($State.failed -is [bool] -and -not $State.failed -and $State.checkpoint -is [scriptblock]) 'STOP_LATCH_OR_MISSING_HOST_CHECKPOINT'
    # The worker/host wiring is still required. A boolean is only a callback
    # result, never a transferable Native authorization or acceptance receipt.
    $reply=& $State.checkpoint $Phase $Index
    Assert-P09Block645 ($reply -is [bool] -and $reply) 'CURRENT_HOST_BOUNDARY_DENIED'
    Assert-P09Block645CurrentDocument $State
}

function Release-P09Block645ComReference($Value) {
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Value)
    }
}

function Release-P09Block645References($State,$References) {
    foreach ($value in $References) {
        try {Release-P09Block645ComReference $value}
        catch {$State.cleanup_error_code='P09_BLOCK645_PARAMETER_REFERENCE_RELEASE_UNCONFIRMED'}
    }
    if ($null -ne $State.cleanup_error_code -and -not $State.failed) {
        $State.failed=$true;throw 'P09_BLOCK645_PARAMETER_REFERENCE_RELEASE_UNCONFIRMED'
    }
}

function Assert-P09Block645Parameters($Set,$Book,[string]$Name) {
    $nameValue=$Set.Item('Name');$typeValue=$Set.Item('Type');$commandValue=$Book.Command
    Assert-P09Block645 ($nameValue -is [string] -and $nameValue -ceq $Name -and
        ($typeValue -is [uint32] -or $typeValue -is [int]) -and [long]$typeValue -eq 1 -and
        ($commandValue -is [uint32] -or $commandValue -is [int]) -and [long]$commandValue -eq 0) 'BOOKMARK_PARAMETER_READBACK'
}

function Assert-P09Block645Selection($Hwp,$Case) {
    $mode=$Hwp.SelectionMode
    Assert-P09Block645 ($mode -is [int] -and ($mode -band 15) -ne 0) 'NONEMPTY_NATIVE_SELECTION_REQUIRED'
    [int]$sl=-1;[int]$sp=-1;[int]$so=-1;[int]$el=-1;[int]$ep=-1;[int]$eo=-1
    $returned=$Hwp.GetSelectedPos([ref]$sl,[ref]$sp,[ref]$so,[ref]$el,[ref]$ep,[ref]$eo)
    $s=$Case.selection
    Assert-P09Block645 ($returned -is [bool] -and $returned -and $sl -eq 0 -and $el -eq 0 -and
        $sp -eq $s.spara -and $so -eq $s.spos -and $ep -eq $s.epara -and $eo -eq $s.epos) 'EXACT_NATIVE_SELECTION_POSITIONS'
}

function Invoke-P09Block645Seed($State) {
    Assert-P09Block645 (-not $State.seed_attempted -and -not $State.seeded -and $State.completed_ranges -eq 0) 'SEED_NO_RETRY'
    $State.seed_attempted=$true;$refs=[Collections.ArrayList]::new()
    try {
        Enter-P09Block645Boundary $State 'seed_prepare' 0
        $hwp=$State.owner.hwp
        $modified=$State.document.Modified
        Assert-P09Block645 ($modified -is [int] -and $modified -eq 0) 'SEED_REQUIRES_FRESH_UNMODIFIED_DOCUMENT'
        $mode=$hwp.SelectionMode
        Assert-P09Block645 ($mode -is [int] -and ($mode -band 15) -eq 0) 'SEED_NO_EXISTING_SELECTION'
        $returned=$hwp.SetPos(0,0,0)
        Assert-P09Block645 ($returned -is [bool] -and $returned) 'SEED_POSITION_FAILED'
        $parameters=$hwp.HParameterSet;[void]$refs.Add($parameters)
        $insert=$parameters.HInsertText;[void]$refs.Insert(0,$insert)
        $set=$insert.HSet;[void]$refs.Insert(0,$set)
        $action=$hwp.HAction;[void]$refs.Insert(0,$action)
        $returned=$action.GetDefault('InsertText',$set)
        Assert-P09Block645 ($returned -is [bool] -and $returned) 'SEED_DEFAULT_FAILED'
        $seed=(@(Get-P09Block645Cases|ForEach-Object {$_.seed_text}) -join "`r`n")
        $insert.Text=$seed
        Assert-P09Block645 ($insert.Text -is [string] -and $insert.Text -ceq $seed) 'SEED_PARAMETER_READBACK'
        Enter-P09Block645Boundary $State 'seed_execute' 0
        $returned=$action.Execute('InsertText',$set)
        Assert-P09Block645 ($returned -is [bool] -and $returned) 'SEED_EXECUTE_EFFECT_UNKNOWN'
        Enter-P09Block645Boundary $State 'seed_returned' 0
        $State.seeded=$true
    } catch {$State.failed=$true;throw}
    finally {Release-P09Block645References $State $refs}
}

function Invoke-P09Block645Ranges($State) {
    Assert-P09Block645 ($State.seeded -is [bool] -and $State.seeded -and -not $State.ranges_attempted -and
        $State.completed_ranges -eq 0) 'RANGES_NO_RETRY_OR_UNSEEDED'
    $State.ranges_attempted=$true
    foreach ($case in (Get-P09Block645Cases)) {
        $refs=[Collections.ArrayList]::new()
        try {
            Enter-P09Block645Boundary $State 'bookmark_prepare' $case.case_index
            $hwp=$State.owner.hwp
            $parameters=$hwp.HParameterSet;[void]$refs.Add($parameters)
            $book=$parameters.HBookMark;[void]$refs.Insert(0,$book)
            $set=$book.HSet;[void]$refs.Insert(0,$set)
            $action=$hwp.HAction;[void]$refs.Insert(0,$action)
            $returned=$action.GetDefault('Bookmark',$set)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_DEFAULT_FAILED'
            # SetItem has a VOID return, not a success boolean.
            [void]$set.SetItem('Name',[string]$case.bookmark_name)
            [void]$set.SetItem('Type',[uint32]1)
            $book.Command=[uint32]0
            Assert-P09Block645Parameters $set $book $case.bookmark_name
            Enter-P09Block645Boundary $State 'bookmark_select' $case.case_index
            $s=$case.selection
            $returned=$hwp.SelectText([int]$s.spara,[int]$s.spos,[int]$s.epara,[int]$s.epos)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_SELECT_FAILED'
            Assert-P09Block645Selection $hwp $case
            Enter-P09Block645Boundary $State 'bookmark_execute' $case.case_index
            # Repeat both readbacks after the checkpoint; do not execute stale
            # parameter/selection observations following a fallible host wait.
            Assert-P09Block645Parameters $set $book $case.bookmark_name
            Assert-P09Block645Selection $hwp $case
            $returned=$action.Execute('Bookmark',$set)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_EXECUTE_EFFECT_UNKNOWN'
            Enter-P09Block645Boundary $State 'bookmark_returned' $case.case_index
            [void]$State.range_trace.Add([ordered]@{case_index=$case.case_index;selection=$case.selection;
                action_returned=$true;native_source_or_block_content_qualified=$false})
            $State.completed_ranges++
        } catch {$State.failed=$true;throw}
        finally {Release-P09Block645References $State $refs}
    }
}
