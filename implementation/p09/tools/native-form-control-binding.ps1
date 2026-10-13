# 내부 전용 함수 라이브러리. dot-source만으로 한글 실행/문서 열기/쓰기를 하지 않는다.
# 실제 native 수용은 전체 15사례의 saved/reopened 패키지와 render로 별도 검증한다.
Set-StrictMode -Version Latest

function Test-P09FormPlanInteger {
    param([AllowNull()]$Value, [long]$Maximum)
    return (($Value -is [int] -or $Value -is [long]) -and $Value -ge 0 -and $Value -le $Maximum)
}

function Assert-P09FormPlan {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][string]$InputSha256)
    if ($Plan.schema_version -cne 'hwpx-agent.private-native-form-control-plan/v1' -or
        $Plan.source_package_sha256 -cne $InputSha256 -or
        $Plan.anchor_mapping_qualified -isnot [bool] -or $Plan.anchor_mapping_qualified -ne $false -or
        $Plan.native_runtime_qualified -isnot [bool] -or $Plan.native_runtime_qualified -ne $false -or
        $Plan.public_action_or_p09_gate -isnot [bool] -or $Plan.public_action_or_p09_gate -ne $false -or
        -not (Test-P09FormPlanInteger $Plan.source_package_bytes 4194304) -or $Plan.source_package_bytes -eq 0 -or
        $Plan.case_id -cnotmatch '^P09-35-C(0[1-9]|1[0-5])$' -or
        $Plan.controls.Count -lt 1 -or $Plan.controls.Count -gt 128) { throw 'P09_FORM_PLAN_REJECTED' }
    $keys = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $tabs = [Collections.Generic.HashSet[int]]::new()
    foreach ($intent in $Plan.controls) {
        if ($intent.native_identity_observation -cne 'missing' -or
            $intent.shape_locked -isnot [bool] -or $intent.shape_locked -ne $false -or
            $intent.native_ctrl_type -cnotin @('+edt', '+rbt') -or
            -not (Test-P09FormPlanInteger $intent.runtime_anchor_candidate.List 0) -or
            -not (Test-P09FormPlanInteger $intent.runtime_anchor_candidate.Para 2147483647) -or
            $intent.name -isnot [string] -or [Text.Encoding]::UTF8.GetByteCount($intent.name) -gt 1024 -or
            $intent.name.Length -eq 0 -or $intent.name -match '[\x00-\x1f]' -or
            -not (Test-P09FormPlanInteger $intent.tab_order 999999999) -or
            -not (Test-P09FormPlanInteger $intent.foreground_rgb 16777215) -or
            -not $keys.Add("$($intent.runtime_anchor_candidate.Para):$($intent.native_ctrl_type)") -or
            -not $names.Add($intent.name) -or -not $tabs.Add([int]$intent.tab_order)) {
            throw 'P09_FORM_PLAN_INTENT_REJECTED'
        }
    }
}

function Resolve-P09FormTargets {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Observed)
    if ($Observed.Count -ne $Plan.controls.Count) { throw 'P09_FORM_NATIVE_INVENTORY_MISMATCH' }
    $byAnchor = @{}
    foreach ($item in $Observed) {
        # Three observed scopes must agree for this root-body profile. Pos is
        # observed and compared, NEVER inferred from XML control byte length.
        foreach ($scope in @($item.local_anchor, $item.top_anchor, $item.root_anchor)) {
            if (-not (Test-P09FormPlanInteger $scope.List 0) -or
                -not (Test-P09FormPlanInteger $scope.Para 2147483647) -or
                -not (Test-P09FormPlanInteger $scope.Pos 2147483647) -or
                $scope.List -ne $item.root_anchor.List -or $scope.Para -ne $item.root_anchor.Para -or
                $scope.Pos -ne $item.root_anchor.Pos) { throw 'P09_FORM_NATIVE_ANCHOR_SCOPE_MISMATCH' }
        }
        $key = "$($item.root_anchor.Para):$($item.ctrl_type)"
        if ($byAnchor.ContainsKey($key)) { throw 'P09_FORM_NATIVE_ANCHOR_AMBIGUOUS' }
        $byAnchor[$key] = $item
    }
    $targets = [Collections.Generic.List[object]]::new()
    foreach ($intent in $Plan.controls) {
        $key = "$($intent.runtime_anchor_candidate.Para):$($intent.native_ctrl_type)"
        if (-not $byAnchor.ContainsKey($key)) { throw 'P09_FORM_SOURCE_NATIVE_BINDING_MISMATCH' }
        $targets.Add([pscustomobject]@{ intent=$intent; observed=$byAnchor[$key] })
    }
    return $targets.ToArray()
}

function Release-P09FormCom {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        # One locally acquired reference; do not invalidate unrelated RCW owners.
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Value)
    }
}

function Get-P09FormAnchor {
    param([Parameter(Mandatory)]$Control, [Parameter(Mandatory)][int]$Scope)
    $position = $null
    try {
        $position = $Control.GetAnchorPos($Scope)
        if ($null -eq $position -or -not $position.IsSet -or $position.SetID -cne 'ListParaPos') {
            throw 'P09_FORM_NATIVE_ANCHOR_SET_REJECTED'
        }
        $anchor = [ordered]@{}
        foreach ($field in @('List', 'Para', 'Pos')) {
            if (-not $position.ItemExist($field)) { throw 'P09_FORM_NATIVE_ANCHOR_ITEM_MISSING' }
            $value = $position.Item($field)
            if ($value -isnot [int] -and $value -isnot [uint32]) { throw 'P09_FORM_NATIVE_ANCHOR_TYPE_REJECTED' }
            if ([long]$value -lt 0 -or [long]$value -gt [int]::MaxValue) { throw 'P09_FORM_NATIVE_ANCHOR_BOUND' }
            $anchor[$field] = [int]$value
        }
        return [pscustomobject]$anchor
    }
    finally { Release-P09FormCom $position }
}

function Get-P09FormCommon {
    param([Parameter(Mandatory)]$Properties)
    if (-not $Properties.IsSet -or $Properties.SetID -cne 'ShapeObject' -or
        -not $Properties.ItemExist('ShapeFormCommonAttr')) { throw 'P09_FORM_NATIVE_SHAPE_SET_REJECTED' }
    $common = $null
    try {
        $common = $Properties.Item('ShapeFormCommonAttr')
        if ($null -eq $common -or -not $common.IsSet -or $common.SetID -cne 'FormCommonAttr') {
            throw 'P09_FORM_NATIVE_COMMON_SET_REJECTED'
        }
        foreach ($field in @('name', 'TabOrder', 'Color')) {
            if (-not $common.ItemExist($field)) { throw 'P09_FORM_NATIVE_COMMON_ITEM_MISSING' }
        }
        return $common
    }
    catch { Release-P09FormCom $common; throw }
}

function Get-P09FormRgb {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)][int]$Rgb)
    # Use the installed declared native conversion, not guessed RGB/COLORREF order.
    $value = $Hwp.RGBColor([byte](($Rgb -shr 16) -band 255), [byte](($Rgb -shr 8) -band 255), [byte]($Rgb -band 255))
    if ($value -isnot [int] -or $value -lt 0 -or $value -gt 16777215) { throw 'P09_FORM_NATIVE_COLOR_TYPE_REJECTED' }
    return [uint32]$value
}

function Copy-P09FormParameters {
    param([Parameter(Mandatory)]$Original)
    $copy = $null; $originalPointer = [IntPtr]::Zero; $copyPointer = [IntPtr]::Zero
    try {
        $copy = $Original.Clone()
        if (-not $copy.IsEquivalent($Original)) { throw 'P09_FORM_NATIVE_PARAMETER_CLONE_MISMATCH' }
        $originalPointer = [Runtime.InteropServices.Marshal]::GetIUnknownForObject($Original)
        $copyPointer = [Runtime.InteropServices.Marshal]::GetIUnknownForObject($copy)
        if ($copyPointer -eq $originalPointer) { throw 'P09_FORM_NATIVE_PARAMETER_CLONE_ALIAS' }
        $result = $copy; $copy = $null
        return $result
    }
    finally {
        if ($copyPointer -ne [IntPtr]::Zero) { [void][Runtime.InteropServices.Marshal]::Release($copyPointer) }
        if ($originalPointer -ne [IntPtr]::Zero) { [void][Runtime.InteropServices.Marshal]::Release($originalPointer) }
        Release-P09FormCom $copy
    }
}

function Copy-P09FormCommon {
    param([Parameter(Mandatory)]$Properties)
    $original = $null
    try {
        $original = Get-P09FormCommon $Properties
        return (Copy-P09FormParameters $original)
    }
    finally { Release-P09FormCom $original }
}

function Assert-P09FormManagedValues {
    param([Parameter(Mandatory)]$Properties, [Parameter(Mandatory)]$Intent, [Parameter(Mandatory)][uint32]$Color)
    $common = $null
    try {
        $common = Get-P09FormCommon $Properties
        $name = $common.Item('name'); $tab = $common.Item('TabOrder'); $actualColor = $common.Item('Color')
        if ($name -isnot [string] -or $name -cne $Intent.name -or
            ($tab -isnot [int] -and $tab -isnot [uint32]) -or [long]$tab -ne $Intent.tab_order -or
            ($actualColor -isnot [int] -and $actualColor -isnot [uint32]) -or [long]$actualColor -ne $Color) {
            throw 'P09_FORM_NATIVE_EXACT_VALUES_MISMATCH'
        }
    }
    finally { Release-P09FormCom $common }
}

function Assert-P09FormUnmanagedProperties {
    param([Parameter(Mandatory)]$Actual, [Parameter(Mandatory)]$Baseline)
    $restored = $null; $afterCommon = $null; $beforeCommon = $null
    try {
        $restored = Copy-P09FormParameters $Actual
        $afterCommon = Copy-P09FormCommon $restored
        $beforeCommon = Get-P09FormCommon $Baseline
        foreach ($field in @('name', 'TabOrder', 'Color')) { $afterCommon.SetItem($field, $beforeCommon.Item($field)) }
        $restored.SetItem('ShapeFormCommonAttr', $afterCommon)
        if (-not $restored.IsEquivalent($Baseline)) { throw 'P09_FORM_NATIVE_UNMANAGED_PROPERTIES_CHANGED' }
    }
    finally {
        Release-P09FormCom $beforeCommon; Release-P09FormCom $afterCommon; Release-P09FormCom $restored
    }
}

function Invoke-P09NativeFormBinding {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)]$Plan,
          [Parameter(Mandatory)][string]$InputSha256, [switch]$VerifyOnly)
    Assert-P09FormPlan $Plan $InputSha256
    $observed = [Collections.Generic.List[object]]::new()
    $identities = [Collections.Generic.HashSet[long]]::new()
    $control = $null; $next = $null; $targets = @(); $modified = [Collections.Generic.List[object]]::new()
    $rollback = 'not_needed'; $walk = 0; $typeCounts = @{}
    try {
        $control = $Hwp.HeadCtrl
        while ($null -ne $control) {
            $walk += 1
            if ($walk -gt 4096) { throw 'P09_FORM_NATIVE_CTRL_WALK_BOUND' }
            $pointer = [Runtime.InteropServices.Marshal]::GetIUnknownForObject($control)
            try { if (-not $identities.Add($pointer.ToInt64())) { throw 'P09_FORM_NATIVE_CTRL_CYCLE' } }
            finally { [void][Runtime.InteropServices.Marshal]::Release($pointer) }
            $next = $control.Next
            $kind = $control.CtrlID
            if ($kind -isnot [string] -or $kind -cnotmatch '^[A-Za-z0-9$%+ ]{1,4}$') { throw 'P09_FORM_NATIVE_CTRL_TYPE_REJECTED' }
            if (-not $typeCounts.ContainsKey($kind)) { $typeCounts[$kind] = 0 }
            $typeCounts[$kind] += 1
            if ($kind -cin @('+edt', '+rbt')) {
                $properties = $null; $baseline = $null
                try {
                    $properties = $control.Properties
                    $baseline = Copy-P09FormParameters $properties
                    $observed.Add([pscustomobject]@{ ctrl_type=$kind; control=$control; baseline=$baseline;
                        local_anchor=(Get-P09FormAnchor $control 0); top_anchor=(Get-P09FormAnchor $control 1);
                        root_anchor=(Get-P09FormAnchor $control 2) })
                    $control = $null; $baseline = $null
                }
                finally { Release-P09FormCom $properties; Release-P09FormCom $baseline }
            }
            elseif ($kind -ceq 'form' -or ($kind -is [string] -and $kind.StartsWith('+', [StringComparison]::Ordinal))) {
                throw 'P09_FORM_NATIVE_UNDECLARED_FORM_TYPE'
            }
            Release-P09FormCom $control
            $control = $next; $next = $null
        }
        # Complete matching BEFORE the first property write.
        $targets = @(Resolve-P09FormTargets $Plan $observed.ToArray())
        foreach ($target in $targets) {
            $common = $null
            try { $common = Get-P09FormCommon $target.observed.baseline }
            finally { Release-P09FormCom $common }
            $target | Add-Member -NotePropertyName color -NotePropertyValue (Get-P09FormRgb $Hwp $target.intent.foreground_rgb)
        }
        if (-not $VerifyOnly) {
            foreach ($target in $targets) {
                $copy = $null; $common = $null; $current = $null
                try {
                    $copy = Copy-P09FormParameters $target.observed.baseline
                    $common = Copy-P09FormCommon $copy
                    $common.SetItem('name', [string]$target.intent.name)
                    $common.SetItem('TabOrder', [int]$target.intent.tab_order)
                    $common.SetItem('Color', [uint32]$target.color)
                    $copy.SetItem('ShapeFormCommonAttr', $common)
                    $current = $target.observed.control.Properties
                    # Earlier TabOrder writes may adjust another DECLARED target's
                    # managed fields. Never accept unmanaged drift; the whole final
                    # check still requires every exact original intended value.
                    Assert-P09FormUnmanagedProperties $current $target.observed.baseline
                    # Include attempted writes in rollback even when a setter throws.
                    $modified.Add($target)
                    $target.observed.control.Properties = $copy
                }
                finally { Release-P09FormCom $current; Release-P09FormCom $common; Release-P09FormCom $copy }
            }
        }
        # Whole target set read AFTER all writes: detects name/tab side effects on peers.
        foreach ($target in $targets) {
            $properties = $null
            try {
                $properties = $target.observed.control.Properties
                Assert-P09FormManagedValues $properties $target.intent $target.color
                $afterAnchor = Get-P09FormAnchor $target.observed.control 2
                foreach ($field in @('List','Para','Pos')) {
                    if ($afterAnchor.$field -ne $target.observed.root_anchor.$field) { throw 'P09_FORM_NATIVE_ANCHOR_CHANGED' }
                }
                if (-not $VerifyOnly) {
                    # Restore ONLY the managed fields in a detached clone; compare the
                    # COMPLETE remaining parameter set, including nested/opaque fields.
                    Assert-P09FormUnmanagedProperties $properties $target.observed.baseline
                }
            }
            finally { Release-P09FormCom $properties }
        }
        return [ordered]@{ state='managed_property_check_pass_not_saved_package_qualification';
            matched_controls=$targets.Count; walked_controls=$walk; verify_only=[bool]$VerifyOnly;
            observed_control_type_counts=$typeCounts;
            observed_anchor_inventory=@($observed | ForEach-Object { [ordered]@{
                ctrl_type=$_.ctrl_type; local_anchor=$_.local_anchor; top_anchor=$_.top_anchor; root_anchor=$_.root_anchor } });
            binding_uses_collection_index_or_reservation_id=$false; pos_inferred_from_xml=$false;
            unmanaged_runtime_parameters_checked=(-not [bool]$VerifyOnly);
            native_save_reopen_render_qualified=$false; p09_complete=$false }
    }
    catch {
        $cause = $_.Exception
        if ($modified.Count -gt 0) {
            $rollback = 'attempted_not_yet_verified'
            try {
                # Include peers touched indirectly by native tab/name side effects.
                foreach ($target in $targets) { $target.observed.control.Properties = $target.observed.baseline }
                foreach ($target in $targets) {
                    $restored = $null
                    try {
                        $restored = $target.observed.control.Properties
                        if (-not $restored.IsEquivalent($target.observed.baseline)) { throw 'P09_FORM_NATIVE_ROLLBACK_MISMATCH' }
                    }
                    finally { Release-P09FormCom $restored }
                }
                $rollback = 'runtime_parameters_restored_not_saved_package_proof'
            }
            catch { $rollback = 'failed_preserve_evidence_and_close_without_save' }
        }
        $failure = [Exception]::new('P09_FORM_NATIVE_BINDING_FAILED', $cause)
        $failure.Data['rollback_state'] = $rollback
        $failure.Data['observed_control_type_counts'] = $typeCounts
        $failure.Data['observed_anchor_inventory'] = @($observed | ForEach-Object { [ordered]@{
            ctrl_type=$_.ctrl_type; local_anchor=$_.local_anchor; top_anchor=$_.top_anchor; root_anchor=$_.root_anchor } })
        throw $failure
    }
    finally {
        Release-P09FormCom $next; Release-P09FormCom $control
        foreach ($item in $observed) { Release-P09FormCom $item.baseline; Release-P09FormCom $item.control }
    }
}
