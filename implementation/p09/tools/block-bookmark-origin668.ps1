# Successor to consumed653: logical text offsets are not native HWP positions.
# Each paragraph origin is observed on the current owned document; no fixed +16.
# No launcher, activation, file IO, fallback API or retry.
# Exact installed2020 HBookMark metadata652 exposes lowercase name/type PUT/GET.
# Original seed, owner, selection, checkpoint, release and no-retry guards remain.
Set-StrictMode -Version Latest

function Get-P09Block668Failure($State,$Failure) {
    $allowed=@('bookmark_prepare','get_parameter_set','get_bookmark','get_hset','get_action','get_default',
        'put_name','put_type','put_command','get_name','get_type','get_command','assert_parameters',
        'bookmark_select','select_text','assert_selection','bookmark_execute','execute',
        'bookmark_returned','release_references','origin_set','origin_read','origin_map')
    $site=$State.parameter_call_site
    if ($site -isnot [string] -or $site -cnotin $allowed) {$site='unknown'}
    $exception=$Failure.Exception.GetBaseException()
    $kind=$exception.GetType().Name
    if ($kind -cnotin @('COMException','RuntimeException','MethodInvocationException','SetValueInvocationException',
        'GetValueInvocationException','InvalidOperationException','ArgumentException')) {$kind='OtherException'}
    # Never return exception messages, document values, pointers or native paths.
    return [ordered]@{schema_version='hwpx-agent.private.block-bookmark668-call-failure/v1';
        call_site=$site;range_index=[int]$State.parameter_range_index;exception_kind=$kind;
        hresult=('0x'+$exception.HResult.ToString('X8'));rerun_forbidden=$true}
}

function Assert-P09Block668Parameters($State,$Book,[string]$Name) {
    $State.parameter_call_site='get_name';$nameValue=$Book.name
    Assert-P09Block645 ($nameValue -is [string] -and $nameValue -ceq $Name) 'BOOKMARK_PARAMETER_READBACK'
    $State.parameter_call_site='get_type';$typeValue=$Book.type
    Assert-P09Block645 (($typeValue -is [uint32] -or $typeValue -is [int]) -and [long]$typeValue -eq 1) 'BOOKMARK_PARAMETER_READBACK'
    $State.parameter_call_site='get_command';$commandValue=$Book.Command
    Assert-P09Block645 (($commandValue -is [uint32] -or $commandValue -is [int]) -and [long]$commandValue -eq 0) 'BOOKMARK_PARAMETER_READBACK'
}

function Get-P09Block668NativeCase($State,$Hwp,$Case) {
    $refs=[Collections.ArrayList]::new();$primary=$false
    try {
        Assert-P09Block646CurrentDocument $State
        $s=$Case.selection
        Assert-P09Block645 ($Case.paragraph_index -is [int] -and $Case.paragraph_index -ge 0 -and
            $Case.paragraph_index -lt 8 -and $s.spara -eq $Case.paragraph_index -and $s.epara -eq $s.spara -and
            $s.spos -is [int] -and $s.epos -is [int] -and $s.spos -ge 0 -and $s.epos -gt $s.spos -and
            $Case.seed_text -is [string] -and $s.epos -le $Case.seed_text.Length -and
            $Case.selected_text -is [string] -and $Case.seed_text.Substring($s.spos,$s.epos-$s.spos) -ceq $Case.selected_text) 'LOGICAL_RANGE_IDENTITY'
        $State.parameter_call_site='origin_set'
        $returned=$Hwp.SetPos([int]0,[int]$Case.paragraph_index,[int]0)
        Assert-P09Block645 ($returned -is [bool] -and $returned) 'ORIGIN_POSITION_FAILED'
        $State.parameter_call_site='origin_read'
        $set=$Hwp.GetPosBySet();[void]$refs.Add($set)
        $origin=Read-P09Block658Position $set
        Assert-P09Block645 ($origin[0] -eq 0 -and $origin[1] -eq $Case.paragraph_index) 'ORIGIN_WRONG_LIST_OR_PARAGRAPH'
        Assert-P09Block646CurrentDocument $State
        $State.parameter_call_site='origin_map'
        $start=[long]$origin[2]+[long]$s.spos;$end=[long]$origin[2]+[long]$s.epos
        Assert-P09Block645 ($start -ge 0 -and $end -gt $start -and $end -le [int]::MaxValue) 'ORIGIN_POSITION_OVERFLOW'
        return [ordered]@{case_index=[int]$Case.case_index;paragraph_index=[int]$Case.paragraph_index;
            bookmark_name=$Case.bookmark_name;seed_text=$Case.seed_text;selected_text=$Case.selected_text;
            logical_selection=$s;observed_origin=@($origin[0],$origin[1],$origin[2]);
            selection=[ordered]@{spara=[int]$s.spara;spos=[int]$start;epara=[int]$s.epara;epos=[int]$end}}
    } catch {$primary=$true;$State.failed=$true;throw}
    finally {try {Release-P09Block645References $State $refs} catch {if (-not $primary) {throw}}}
}

function Assert-P09Block668Selection($State,$Hwp,$Case) {
    # Keep the original exact six-position and owner checks; text identity is
    # additional evidence, not a substitute for an unavailable selection API.
    Assert-P09Block658Selection $State $Hwp $Case
    $row=$State.selection_observations[$State.selection_observations.Count-1]
    $row['selected_text']=[ordered]@{exact_match=$false;character_count=$null;UTF8_bytes=$null;sha256=$null;raw_text_present=$false}
    try {
        Assert-P09Block646CurrentDocument $State
        $text=$Hwp.GetTextFile('TEXT','saveblock:true')
        Assert-P09Block645 ($text -is [string] -and $text.Length -le 4096 -and $text -ceq $Case.selected_text) 'EXACT_SELECTED_TEXT_REQUIRED'
        $bytes=[Text.UTF8Encoding]::new($false,$true).GetBytes($text)
        $sha=[Security.Cryptography.SHA256]::Create()
        try {$digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
        finally {$sha.Dispose()}
        Assert-P09Block646CurrentDocument $State
        $row.selected_text.character_count=$text.Length;$row.selected_text.UTF8_bytes=$bytes.Length
        $row.selected_text.sha256=$digest;$row.selected_text.exact_match=$true
    } catch {$State.failed=$true;throw}
}

function Invoke-P09Block668Ranges($State) {
    Assert-P09Block645 ($State.seeded -is [bool] -and $State.seeded -and -not $State.ranges_attempted -and
        $State.completed_ranges -eq 0 -and -not $State.failed) 'RANGES_NO_RETRY_OR_UNSEEDED'
    $State.ranges_attempted=$true
    foreach ($case in (Get-P09Block645Cases)) {
        $refs=[Collections.ArrayList]::new();$primary=$false
        $State.parameter_range_index=[int]$case.case_index
        try {
            $State.parameter_call_site='bookmark_prepare';Enter-P09Block645Boundary $State 'bookmark_prepare' $case.case_index
            $hwp=$State.owner.hwp
            $case=Get-P09Block668NativeCase $State $hwp $case
            $State.parameter_call_site='get_parameter_set';$parameters=$hwp.HParameterSet;[void]$refs.Add($parameters)
            $State.parameter_call_site='get_bookmark';$book=$parameters.HBookMark;[void]$refs.Insert(0,$book)
            $State.parameter_call_site='get_hset';$set=$book.HSet;[void]$refs.Insert(0,$set)
            $State.parameter_call_site='get_action';$action=$hwp.HAction;[void]$refs.Insert(0,$action)
            $State.parameter_call_site='get_default';$returned=$action.GetDefault('Bookmark',$set)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_DEFAULT_FAILED'
            # Do not guess generic item-key casing. Use observed typed properties.
            $State.parameter_call_site='put_name';$book.name=[string]$case.bookmark_name
            $State.parameter_call_site='put_type';$book.type=[uint32]1
            $State.parameter_call_site='put_command';$book.Command=[uint32]0
            Assert-P09Block668Parameters $State $book $case.bookmark_name
            $State.parameter_call_site='bookmark_select';Enter-P09Block645Boundary $State 'bookmark_select' $case.case_index
            $s=$case.selection
            $State.parameter_call_site='select_text';$returned=$hwp.SelectText([int]$s.spara,[int]$s.spos,[int]$s.epara,[int]$s.epos)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_SELECT_FAILED'
            $State.parameter_call_site='assert_selection';Assert-P09Block668Selection $State $hwp $case
            $State.parameter_call_site='bookmark_execute';Enter-P09Block645Boundary $State 'bookmark_execute' $case.case_index
            Assert-P09Block668Parameters $State $book $case.bookmark_name
            $State.parameter_call_site='assert_selection';Assert-P09Block668Selection $State $hwp $case
            $State.parameter_call_site='execute';$returned=$action.Execute('Bookmark',$set)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_EXECUTE_EFFECT_UNKNOWN'
            $State.parameter_call_site='bookmark_returned';Enter-P09Block645Boundary $State 'bookmark_returned' $case.case_index
            [void]$State.range_trace.Add([ordered]@{case_index=$case.case_index;selection=$case.selection;
                logical_selection=$case.logical_selection;observed_origin=$case.observed_origin;
                action_returned=$true;native_source_or_block_content_qualified=$false})
            $State.completed_ranges++
        } catch {
            $primary=$true;$State.failed=$true
            $State.parameter_call_failure=Get-P09Block668Failure $State $_
            throw
        } finally {
            # Preserve the first failed call if reference cleanup also fails.
            if (-not $primary) {$State.parameter_call_site='release_references'}
            try {Release-P09Block645References $State $refs}
            catch {
                if (-not $primary) {$State.parameter_call_failure=Get-P09Block668Failure $State $_}
                throw
            }
        }
    }
}
