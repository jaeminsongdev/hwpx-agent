# Installed657 supports GetSelectedPosBySet. Same exact six coordinates; no
# pointer OUT adaptation, fallback/retry, launcher, activation, or document IO.
Set-StrictMode -Version Latest

function Read-P09Block658Position($Set) {
    Assert-P09Block645 ($null -ne $Set -and $Set.SetID -is [string] -and $Set.SetID -ceq 'ListParaPos') 'SELECTION_SET_ID'
    $valid=$Set.IsSet
    Assert-P09Block645 ($valid -is [bool] -and $valid) 'SELECTION_SET_INVALID'
    $values=[Collections.Generic.List[int]]::new()
    foreach ($key in @('List','Para','Pos')) {
        $exists=$Set.ItemExist($key)
        Assert-P09Block645 ($exists -is [bool] -and $exists) 'SELECTION_SET_ITEM_MISSING'
        $value=$Set.Item($key)
        # ParameterSet.Item is VARIANT, unlike the six LONG* signature. Accept
        # only nonnegative signed/unsigned32 integers exactly representable I4.
        Assert-P09Block645 (($value -is [int] -or $value -is [uint32]) -and [long]$value -ge 0 -and [long]$value -le [int]::MaxValue) 'SELECTION_SET_ITEM_TYPE'
        $values.Add([int]$value)
    }
    return ,$values.ToArray()
}

function Assert-P09Block658Selection($State,$Hwp,$Case) {
    Assert-P09Block645 (-not $State.failed -and $State.selection_observations.Count -lt 16 -and
        $Case.case_index -is [int] -and $Case.case_index -ge 1 -and $Case.case_index -le 8) 'SELECTION_READBACK_BOUND'
    $refs=[Collections.ArrayList]::new();$primary=$false
    $row=[ordered]@{range_index=[int]$Case.case_index;read_index=[int]($State.selection_observations.Count+1);
        api='GetSelectedPosBySet';mode=$null;returned=$null;positions=$null;exact_match=$false}
    [void]$State.selection_observations.Add($row)
    try {
        Assert-P09Block646CurrentDocument $State
        $mode=$Hwp.SelectionMode
        Assert-P09Block645 ($mode -is [int] -and ($mode -band 15) -ne 0) 'NONEMPTY_NATIVE_SELECTION_REQUIRED'
        $row.mode=$mode
        $start=$Hwp.CreateSet('ListParaPos');[void]$refs.Add($start)
        $end=$Hwp.CreateSet('ListParaPos');[void]$refs.Insert(0,$end)
        Assert-P09Block645 ($null -ne $start -and $null -ne $end) 'SELECTION_SET_NULL'
        # These are two newly obtained sets, never HParameterSet aliases. A
        # successful API return is not evidence until all six typed items match.
        $returned=$Hwp.GetSelectedPosBySet($start,$end)
        if ($returned -is [bool]) {$row.returned=$returned}
        Assert-P09Block645 ($returned -is [bool] -and $returned) 'SELECTION_SET_READ_FAILED'
        $a=Read-P09Block658Position $start;$b=Read-P09Block658Position $end
        $row.positions=@($a[0],$a[1],$a[2],$b[0],$b[1],$b[2])
        Assert-P09Block646CurrentDocument $State
        $s=$Case.selection
        Assert-P09Block645 ($a[0] -eq 0 -and $b[0] -eq 0 -and $a[1] -eq $s.spara -and
            $a[2] -eq $s.spos -and $b[1] -eq $s.epara -and $b[2] -eq $s.epos) 'EXACT_NATIVE_SELECTION_POSITIONS'
        $row.exact_match=$true
    } catch {$primary=$true;$State.failed=$true;throw}
    finally {
        # Preserve the first readback failure if parameter RCW release also fails.
        try {Release-P09Block645References $State $refs} catch {if (-not $primary) {throw}}
    }
}
