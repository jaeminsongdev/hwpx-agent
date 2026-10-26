# Successor to the consumed645 range writer only; no launcher/activation/IO.
# Exact installed2020 HBookMark metadata652 exposes lowercase name/type PUT/GET.
# Original seed, owner, selection, checkpoint, release and no-retry guards remain.
Set-StrictMode -Version Latest

function Get-P09Block653Failure($State,$Failure) {
    $allowed=@('bookmark_prepare','get_parameter_set','get_bookmark','get_hset','get_action','get_default',
        'put_name','put_type','put_command','get_name','get_type','get_command','assert_parameters',
        'bookmark_select','select_text','assert_selection','bookmark_execute','execute',
        'bookmark_returned','release_references')
    $site=$State.parameter_call_site
    if ($site -isnot [string] -or $site -cnotin $allowed) {$site='unknown'}
    $exception=$Failure.Exception.GetBaseException()
    $kind=$exception.GetType().Name
    if ($kind -cnotin @('COMException','RuntimeException','MethodInvocationException','SetValueInvocationException',
        'GetValueInvocationException','InvalidOperationException','ArgumentException')) {$kind='OtherException'}
    # Never return exception messages, document values, pointers or native paths.
    return [ordered]@{schema_version='hwpx-agent.private.block-bookmark653-call-failure/v1';
        call_site=$site;range_index=[int]$State.parameter_range_index;exception_kind=$kind;
        hresult=('0x'+$exception.HResult.ToString('X8'));rerun_forbidden=$true}
}

function Assert-P09Block653Parameters($State,$Book,[string]$Name) {
    $State.parameter_call_site='get_name';$nameValue=$Book.name
    Assert-P09Block645 ($nameValue -is [string] -and $nameValue -ceq $Name) 'BOOKMARK_PARAMETER_READBACK'
    $State.parameter_call_site='get_type';$typeValue=$Book.type
    Assert-P09Block645 (($typeValue -is [uint32] -or $typeValue -is [int]) -and [long]$typeValue -eq 1) 'BOOKMARK_PARAMETER_READBACK'
    $State.parameter_call_site='get_command';$commandValue=$Book.Command
    Assert-P09Block645 (($commandValue -is [uint32] -or $commandValue -is [int]) -and [long]$commandValue -eq 0) 'BOOKMARK_PARAMETER_READBACK'
}

function Invoke-P09Block653Ranges($State) {
    Assert-P09Block645 ($State.seeded -is [bool] -and $State.seeded -and -not $State.ranges_attempted -and
        $State.completed_ranges -eq 0 -and -not $State.failed) 'RANGES_NO_RETRY_OR_UNSEEDED'
    $State.ranges_attempted=$true
    foreach ($case in (Get-P09Block645Cases)) {
        $refs=[Collections.ArrayList]::new();$primary=$false
        $State.parameter_range_index=[int]$case.case_index
        try {
            $State.parameter_call_site='bookmark_prepare';Enter-P09Block645Boundary $State 'bookmark_prepare' $case.case_index
            $hwp=$State.owner.hwp
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
            Assert-P09Block653Parameters $State $book $case.bookmark_name
            $State.parameter_call_site='bookmark_select';Enter-P09Block645Boundary $State 'bookmark_select' $case.case_index
            $s=$case.selection
            $State.parameter_call_site='select_text';$returned=$hwp.SelectText([int]$s.spara,[int]$s.spos,[int]$s.epara,[int]$s.epos)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_SELECT_FAILED'
            $State.parameter_call_site='assert_selection';Assert-P09Block645Selection $hwp $case
            $State.parameter_call_site='bookmark_execute';Enter-P09Block645Boundary $State 'bookmark_execute' $case.case_index
            Assert-P09Block653Parameters $State $book $case.bookmark_name
            $State.parameter_call_site='assert_selection';Assert-P09Block645Selection $hwp $case
            $State.parameter_call_site='execute';$returned=$action.Execute('Bookmark',$set)
            Assert-P09Block645 ($returned -is [bool] -and $returned) 'BOOKMARK_EXECUTE_EFFECT_UNKNOWN'
            $State.parameter_call_site='bookmark_returned';Enter-P09Block645Boundary $State 'bookmark_returned' $case.case_index
            [void]$State.range_trace.Add([ordered]@{case_index=$case.case_index;selection=$case.selection;
                action_returned=$true;native_source_or_block_content_qualified=$false})
            $State.completed_ranges++
        } catch {
            $primary=$true;$State.failed=$true
            $State.parameter_call_failure=Get-P09Block653Failure $State $_
            throw
        } finally {
            # Preserve the first failed call if reference cleanup also fails.
            if (-not $primary) {$State.parameter_call_site='release_references'}
            try {Release-P09Block645References $State $refs}
            catch {
                if (-not $primary) {$State.parameter_call_failure=Get-P09Block653Failure $State $_}
                throw
            }
        }
    }
}
