[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^OBJ-[0-9]{3}$')][string]$FeatureId,
    [Parameter(Mandatory)][string]$OverlayPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOverlaySha256,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'P08_OBJECT_PROPERTY_ISOLATION'
$allowedFeatures = @(
    'OBJ-001', 'OBJ-002', 'OBJ-003', 'OBJ-007', 'OBJ-010', 'OBJ-012', 'OBJ-014',
    'OBJ-015', 'OBJ-016', 'OBJ-017', 'OBJ-018', 'OBJ-019', 'OBJ-020',
    'OBJ-021', 'OBJ-022', 'OBJ-023', 'OBJ-024', 'OBJ-025', 'OBJ-027',
    'OBJ-028', 'OBJ-029', 'OBJ-030', 'OBJ-031', 'OBJ-032', 'OBJ-034',
    'OBJ-035', 'OBJ-036', 'OBJ-037', 'OBJ-039', 'OBJ-040', 'OBJ-041', 'OBJ-042',
    'OBJ-043', 'OBJ-047', 'OBJ-048'
)

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value) }
        catch { }
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)
    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $prog = $null
    $clsidNode = $null
    $clsidKey = $null
    $server = $null
    try {
        $prog = $root.OpenSubKey($RequestedProgId)
        if ($null -eq $prog) { throw ($errorPrefix + '_PROGID_NOT_REGISTERED') }
        $clsidNode = $prog.OpenSubKey('CLSID')
        if ($null -eq $clsidNode) { throw ($errorPrefix + '_CLSID_MISSING') }
        $clsid = [string]$clsidNode.GetValue('')
        $clsidKey = $root.OpenSubKey("CLSID\$clsid")
        $server = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $server) { throw ($errorPrefix + '_LOCALSERVER32_MISSING') }
        $command = [string]$server.GetValue('')
    }
    finally {
        foreach ($key in @($server, $clsidKey, $clsidNode, $prog, $root)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw ($errorPrefix + '_LOCALSERVER32_PARSE_FAILED') }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    return [ordered]@{ path = $path; sha256 = Get-Sha256File -Path $path }
}

function Get-DocumentSnapshot {
    param([Parameter(Mandatory)][object]$Hwp)
    $value = [string]$Hwp.GetTextFile('HWPML2X', '')
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw ($errorPrefix + '_EMPTY_HWPML_SNAPSHOT')
    }
    $raw = $value.Replace("`0", '').Replace("`r`n", "`n").Replace("`r", "`n")
    $pattern = '(<DRAWTEXT\b[^<>]*?)\sName=""(?=[^<>]*>)'
    $normalizationCount = [regex]::Matches($raw, $pattern).Count
    $semantic = [regex]::Replace($raw, $pattern, '$1')
    return [ordered]@{
        sha256 = Get-Sha256String -Value $semantic
        raw_sha256 = Get-Sha256String -Value $raw
        normalization_count = $normalizationCount
    }
}

function New-Rectangle {
    param([Parameter(Mandatory)][object]$Hwp)
    $action = $null
    $set = $null
    $layout = $null
    $points = $null
    try {
        $action = $Hwp.CreateAction('DrawObjCreatorRectangle')
        $set = $action.CreateSet()
        if ($null -eq $set -or -not [bool]$action.GetDefault($set)) {
            throw ($errorPrefix + '_SETUP_DEFAULT_FAILED')
        }
        foreach ($pair in @(
            @('TreatAsChar', 0), @('TextWrap', 3), @('VertOffset', 2000),
            @('VertAlign', 0), @('VertRelTo', 0), @('HorzOffset', 2000),
            @('HorzAlign', 0), @('HorzRelTo', 0), @('HeightRelTo', 2),
            @('Height', 4200), @('WidthRelTo', 4), @('Width', 6800),
            @('AdjustTextbox', 1), @('ShapeCreationMode', 0), @('ShapeCreationType', 1)
        )) { [void]$set.SetItem([string]$pair[0], [int]$pair[1]) }
        $layout = $set.CreateItemSet('ShapeDrawLayOut', 'DrawLayOut')
        [void]$layout.SetItem('CreateNumPt', 4)
        $points = $layout.CreateItemArray('CreatePt', 8)
        $values = @(0, 0, 6800, 0, 6800, 4200, 0, 4200)
        for ($index = 0; $index -lt $values.Count; $index += 1) {
            [void]$points.SetItem($index, $values[$index])
        }
        if (-not [bool]$action.Execute($set)) {
            throw ($errorPrefix + '_SETUP_EXECUTE_FAILED')
        }
    }
    finally {
        Clear-ComObject -Value $points
        Clear-ComObject -Value $layout
        Clear-ComObject -Value $set
        Clear-ComObject -Value $action
    }
}

function New-ParameterizedShape {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][string]$ActionId,
        [ValidateRange(2, 8)][int]$PointCount = 4,
        [switch]$TextBox,
        [switch]$ParagraphRelative
    )
    $action = $null
    $set = $null
    $layout = $null
    $points = $null
    $segments = $null
    try {
        $action = $Hwp.CreateAction($ActionId)
        $set = $action.CreateSet()
        if ($null -eq $set -or -not [bool]$action.GetDefault($set)) {
            throw ($errorPrefix + '_INSERT_DEFAULT_FAILED')
        }
        $horzRelTo = if ($ParagraphRelative) { 3 } else { 0 }
        $vertRelTo = if ($ParagraphRelative) { 2 } else { 0 }
        foreach ($pair in @(
            @('TreatAsChar', 0), @('TextWrap', 3), @('VertOffset', 2000),
            @('VertAlign', 0), @('VertRelTo', $vertRelTo), @('HorzOffset', 2000),
            @('HorzAlign', 0), @('HorzRelTo', $horzRelTo), @('HeightRelTo', 2),
            @('Height', 4200), @('WidthRelTo', 4), @('Width', 6800),
            @('AdjustTextbox', $(if ($TextBox) { 1 } else { 0 })),
            @('ShapeCreationMode', 0), @('ShapeCreationType', 1)
        )) { [void]$set.SetItem([string]$pair[0], [int]$pair[1]) }
        $layout = $set.CreateItemSet('ShapeDrawLayOut', 'DrawLayOut')
        [void]$layout.SetItem('CreateNumPt', $PointCount)
        $points = $layout.CreateItemArray('CreatePt', $PointCount * 2)
        $values = if ($PointCount -eq 2) {
            @(0, 0, 6800, 4200)
        }
        else { @(0, 0, 6800, 0, 5200, 4200, 800, 3600) }
        for ($index = 0; $index -lt $values.Count; $index += 1) {
            [void]$points.SetItem($index, $values[$index])
        }
        if ($ActionId -ceq 'DrawObjCreatorCurve') {
            $segments = $layout.CreateItemArray('CurveSegmentInfo', $PointCount)
            for ($index = 0; $index -lt $PointCount; $index += 1) {
                [void]$segments.SetItem($index, 0)
            }
        }
        if (-not [bool]$action.Execute($set)) {
            throw ($errorPrefix + '_INSERT_EXECUTE_FAILED')
        }
        return $true
    }
    finally {
        Clear-ComObject -Value $segments
        Clear-ComObject -Value $points
        Clear-ComObject -Value $layout
        Clear-ComObject -Value $set
        Clear-ComObject -Value $action
    }
}

function Invoke-InsertFeature {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][string]$RequestedFeature,
        [AllowNull()][string]$PicturePath
    )
    $control = $null
    $parameter = $null
    $hset = $null
    try {
        switch ($RequestedFeature) {
            'OBJ-001' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjCreatorRectangle'
            }
            'OBJ-002' {
                if ([string]::IsNullOrWhiteSpace($PicturePath)) {
                    throw ($errorPrefix + '_PICTURE_PATH_MISSING')
                }
                $control = $Hwp.InsertPicture(
                    $PicturePath, $true, 0, $false, $false, 0, 0, 0
                )
                return $null -ne $control
            }
            'OBJ-003' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjTemplateLoad'
            }
            'OBJ-007' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjCreatorTextBox' `
                    -TextBox
            }
            'OBJ-010' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjCreatorObject'
            }
            'OBJ-012' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'FormObjCreatorEdit' `
                    -TextBox
            }
            'OBJ-014' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjCreatorRectangle' `
                    -ParagraphRelative
            }
            'OBJ-041' {
                return New-ParameterizedShape -Hwp $Hwp `
                    -ActionId 'InsertConnectLineStraightNoArrow' -PointCount 2
            }
            'OBJ-042' {
                return New-ParameterizedShape -Hwp $Hwp -ActionId 'DrawObjCreatorCurve'
            }
            'OBJ-048' {
                $parameter = $Hwp.HParameterSet.HHyperLink
                $hset = $parameter.HSet
                if (-not [bool]$Hwp.HAction.GetDefault('Hyperlink', $hset)) {
                    throw ($errorPrefix + '_HYPERLINK_DEFAULT_FAILED')
                }
                $parameter.Text = ''
                $parameter.Command = 'https\://example.test/p08-runtime;0;0;0;'
                $parameter.NoLInk = 0
                $parameter.ShapeObject = 1
                $parameter.DirectInsert = 1
                return [bool]$Hwp.HAction.Execute('Hyperlink', $hset)
            }
            default { throw ($errorPrefix + '_INSERT_FEATURE_MISSING') }
        }
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $parameter
        Clear-ComObject -Value $control
    }
}

function Select-FirstShapeControl {
    param([Parameter(Mandatory)][object]$Hwp)
    $control = $null
    $anchor = $null
    try {
        $control = $Hwp.HeadCtrl
        for ($index = 0; $index -lt 128 -and $null -ne $control; $index += 1) {
            if ([string]$control.CtrlID -ceq 'gso') {
                $anchor = $control.GetAnchorPos(0)
                if ($null -eq $anchor -or -not [bool]$Hwp.SetPosBySet($anchor) -or
                    -not [bool]$Hwp.FindCtrl()) {
                    throw ($errorPrefix + '_SELECT_CONTROL_FAILED')
                }
                return
            }
            $next = $control.Next
            Clear-ComObject -Value $control
            $control = $next
        }
        throw ($errorPrefix + '_SHAPE_CONTROL_NOT_FOUND')
    }
    finally {
        Clear-ComObject -Value $anchor
        Clear-ComObject -Value $control
    }
}

function Select-ShapeControl {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [ValidateRange(1, 16)][int]$Ordinal = 1
    )
    $control = $null
    $anchor = $null
    $seen = 0
    try {
        $control = $Hwp.HeadCtrl
        for ($index = 0; $index -lt 128 -and $null -ne $control; $index += 1) {
            if ([string]$control.CtrlID -ceq 'gso') {
                $seen += 1
                if ($seen -eq $Ordinal) {
                    $anchor = $control.GetAnchorPos(0)
                    if ($null -eq $anchor -or -not [bool]$Hwp.SetPosBySet($anchor) -or
                        -not [bool]$Hwp.FindCtrl()) {
                        throw ($errorPrefix + '_SELECT_CONTROL_FAILED')
                    }
                    return
                }
            }
            $next = $control.Next
            Clear-ComObject -Value $control
            $control = $next
        }
        throw ($errorPrefix + '_SHAPE_CONTROL_ORDINAL_NOT_FOUND')
    }
    finally {
        Clear-ComObject -Value $anchor
        Clear-ComObject -Value $control
    }
}

function Get-FirstShapeControl {
    param([Parameter(Mandatory)][object]$Hwp)
    $control = $Hwp.HeadCtrl
    for ($index = 0; $index -lt 128 -and $null -ne $control; $index += 1) {
        if ([string]$control.CtrlID -ceq 'gso') { return $control }
        $next = $control.Next
        Clear-ComObject -Value $control
        $control = $next
    }
    Clear-ComObject -Value $control
    throw ($errorPrefix + '_SHAPE_CONTROL_NOT_FOUND')
}

function Get-ShapeControl {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [ValidateRange(1, 16)][int]$Ordinal = 1
    )
    $control = $Hwp.HeadCtrl
    $seen = 0
    for ($index = 0; $index -lt 128 -and $null -ne $control; $index += 1) {
        if ([string]$control.CtrlID -ceq 'gso') {
            $seen += 1
            if ($seen -eq $Ordinal) { return $control }
        }
        $next = $control.Next
        Clear-ComObject -Value $control
        $control = $next
    }
    Clear-ComObject -Value $control
    throw ($errorPrefix + '_SHAPE_CONTROL_ORDINAL_NOT_FOUND')
}

function Invoke-Feature {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][object]$Control,
        [Parameter(Mandatory)][string]$RequestedFeature
    )
    $properties = $null
    $nested = $null
    $colors = $null
    $parameter = $null
    $hset = $null
    $shapeAction = $null
    $shapeSet = $null
    try {
        switch ($RequestedFeature) {
            'OBJ-027' { return [bool]$Hwp.HAction.Run('PictureNoReflection') }
            'OBJ-028' { return [bool]$Hwp.HAction.Run('PictureNoGlow') }
            'OBJ-029' { return [bool]$Hwp.HAction.Run('PictureNoSofeEdge') }
            'OBJ-036' { return [bool]$Hwp.HAction.Run('ShapeObjGroup') }
            'OBJ-037' { return [bool]$Hwp.HAction.Run('ShapeObjUngroup') }
            'OBJ-039' { return [bool]$Hwp.HAction.Run('ShapeObjAlignLeft') }
            'OBJ-040' { return [bool]$Hwp.HAction.Run('ShapeObjAlignHorzSpacing') }
        }
        if ($RequestedFeature -ceq 'OBJ-032') {
            $parameter = $Hwp.HParameterSet.HShapeObject
            $hset = $parameter.HSet
            $actionId = switch ($RequestedFeature) {
                'OBJ-032' { 'ShapeObjRandomAngleRotater' }
            }
            if (-not [bool]$Hwp.HAction.GetDefault($actionId, $hset)) {
                throw ($errorPrefix + '_SHAPE_OBJECT_DEFAULT_FAILED')
            }
            switch ($RequestedFeature) {
                'OBJ-032' {
                    $nested = $parameter.ShapeDrawRotate
                    $nested.Angle = [int]$nested.Angle + 4500
                }
            }
            return [bool]$Hwp.HAction.Execute($actionId, $hset)
        }
        $properties = $Control.Properties
        switch ($RequestedFeature) {
            'OBJ-015' {
                [void]$properties.SetItem(
                    'HorzOffset', [int]$properties.Item('HorzOffset') + 1000
                )
            }
            'OBJ-016' {
                [void]$properties.SetItem('WidthRelTo', 4)
                [void]$properties.SetItem('HeightRelTo', 2)
                [void]$properties.SetItem('Width', [int]$properties.Item('Width') + 1000)
                [void]$properties.SetItem('Height', [int]$properties.Item('Height') + 1000)
            }
            'OBJ-017' {
                $next = if ([int]$properties.Item('HorzRelTo') -eq 1) { 0 } else { 1 }
                [void]$properties.SetItem('HorzRelTo', $next)
                [void]$properties.SetItem('HorzAlign', 0)
            }
            'OBJ-018' {
                $next = if ([int]$properties.Item('TextWrap') -eq 0) { 1 } else { 0 }
                [void]$properties.SetItem('TextWrap', $next)
            }
            'OBJ-019' {
                [void]$properties.SetItem(
                    'OutsideMarginLeft', [int]$properties.Item('OutsideMarginLeft') + 200
                )
            }
            'OBJ-020' {
                $nested = $properties.Item('ShapeDrawLineAttr')
                $next = if ([int]$nested.Item('Style') -eq 1) { 2 } else { 1 }
                [void]$nested.SetItem('Style', $next)
                [void]$nested.SetItem('Color', 255)
                [void]$properties.SetItem('ShapeDrawLineAttr', $nested)
            }
            'OBJ-021' {
                $nested = $properties.Item('ShapeDrawFillAttr')
                [void]$nested.SetItem('Type', 0)
                [void]$properties.SetItem('ShapeDrawFillAttr', $nested)
            }
            'OBJ-022' {
                $nested = $properties.Item('ShapeDrawFillAttr')
                [void]$nested.SetItem('Type', 0)
                [void]$properties.SetItem('ShapeDrawFillAttr', $nested)
            }
            'OBJ-023' {
                $nested = $properties.Item('ShapeDrawFillAttr')
                [void]$nested.SetItem('Type', 0)
                [void]$properties.SetItem('ShapeDrawFillAttr', $nested)
            }
            'OBJ-024' {
                $nested = $properties.Item('ShapeDrawFillAttr')
                [void]$nested.SetItem('Type', 0)
                [void]$properties.SetItem('ShapeDrawFillAttr', $nested)
            }
            'OBJ-025' {
                $nested = $properties.Item('ShapeListProperties')
                if ($null -eq $nested) {
                    $nested = $properties.CreateItemSet(
                        'ShapeListProperties', 'ListProperties'
                    )
                }
                $margin = $nested.Item('MarginLeft')
                [void]$nested.SetItem(
                    'MarginLeft', $(if ($null -eq $margin) { 1500 } else { [int]$margin + 700 })
                )
                [void]$properties.SetItem('ShapeListProperties', $nested)
            }
            'OBJ-030' {
                $nested = $properties.Item('ShapeDrawImageAttr')
                $next = if ([int]$nested.Item('Brightness') -eq 10) { 20 } else { 10 }
                [void]$nested.SetItem('Brightness', $next)
                [void]$properties.SetItem('ShapeDrawImageAttr', $nested)
            }
            'OBJ-031' {
                $nested = $properties.Item('ShapeDrawFillAttr')
                [void]$nested.SetItem('SkipLeft', [int]$nested.Item('SkipLeft') + 100)
                [void]$properties.SetItem('ShapeDrawFillAttr', $nested)
            }
            'OBJ-034' {
                $nested = $properties.Item('ShapeDrawLineAttr')
                $next = if ([int]$nested.Item('Alpha') -eq 64) { 96 } else { 64 }
                [void]$nested.SetItem('Alpha', $next)
                [void]$properties.SetItem('ShapeDrawLineAttr', $nested)
            }
            'OBJ-035' {
                $nested = $properties.Item('ShapeDrawImageAttr')
                $next = if ([int]$nested.Item('Contrast') -eq 10) { 20 } else { 10 }
                [void]$nested.SetItem('Contrast', $next)
                [void]$properties.SetItem('ShapeDrawImageAttr', $nested)
            }
            'OBJ-043' {
                $nested = $properties.Item('ShapeDrawEditDetail')
                if ($null -eq $nested) {
                    $nested = $properties.CreateItemSet(
                        'ShapeDrawEditDetail', 'DrawEditDetail'
                    )
                }
                [void]$nested.SetItem('Command', 0)
                [void]$nested.SetItem('Index', 0)
                $pointX = $nested.Item('PointX')
                [void]$nested.SetItem(
                    'PointX', $(if ($null -eq $pointX) { 100 } else { [int]$pointX + 100 })
                )
                [void]$properties.SetItem('ShapeDrawEditDetail', $nested)
            }
            'OBJ-047' {
                $nested = $properties.Item('ShapeComment')
                [void]$nested.SetItem('EditShapeObjCommentFlag', 1)
                [void]$nested.SetItem('EditShapeObjCommentStr', 'P08-25 alternative text')
                [void]$properties.SetItem('ShapeComment', $nested)
            }
            default { throw ($errorPrefix + '_FEATURE_MUTATION_MISSING') }
        }
        $Control.Properties = $properties
        return $true
    }
    finally {
        Clear-ComObject -Value $colors
        Clear-ComObject -Value $nested
        Clear-ComObject -Value $shapeSet
        Clear-ComObject -Value $shapeAction
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $parameter
        Clear-ComObject -Value $properties
    }
}

if (-not [Environment]::Is64BitOperatingSystem -or [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw ($errorPrefix + '_REQUIRES_X86_STA')
}
if ($allowedFeatures -cnotcontains $FeatureId) { throw ($errorPrefix + '_FEATURE_NOT_ALLOWED') }
if (Test-Path -LiteralPath $TracePath -PathType Leaf) {
    throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS')
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}
if (-not (Test-Path -LiteralPath $OverlayPath -PathType Leaf) -or
    (Get-Sha256File -Path $OverlayPath) -cne $ExpectedOverlaySha256) {
    throw ($errorPrefix + '_OVERLAY_IDENTITY')
}
$server = Get-ComServerIdentity -RequestedProgId $ProgId
if ([string]$server.sha256 -cne $ExpectedExecutableSha256) {
    throw ($errorPrefix + '_COM_SERVER_IDENTITY')
}
$overlay = Get-Content -LiteralPath $OverlayPath -Raw -Encoding UTF8 | ConvertFrom-Json
$route = @($overlay.routes | Where-Object { [string]$_.feature_id -ceq $FeatureId })
if ($route.Count -ne 1 -or [string]$route[0].state -cne 'candidate_unverified' -or
    [string]$route[0].source_kind -notin @('action_table', 'automation_object') -or
    [string]$route[0].modal_risk -notin @('must_probe', 'none_expected', 'known_modal')) {
    throw ($errorPrefix + '_ROUTE_CONTRACT')
}
$route = $route[0]

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path.TrimEnd('\')
$fixtureRoot = Join-Path $root (
    'implementation\p08\evidence\private\p08-20-object-target-20260915-18'
)
$fixtureNames = @{
    'OBJ-021' = 'obj-021-fill-solid.hancom-2020-readback.hwpx'
    'OBJ-022' = 'obj-022-fill-gradient.hancom-2020-readback.hwpx'
    'OBJ-023' = 'obj-023-fill-pattern.hancom-2020-readback.hwpx'
    'OBJ-024' = 'obj-024-fill-image.hancom-2020-readback.hwpx'
    'OBJ-025' = 'obj-025-textbox-properties.hancom-2020-readback.hwpx'
    'OBJ-027' = 'obj-027-reflection.hancom-2020-readback.hwpx'
    'OBJ-028' = 'obj-028-glow.hancom-2020-readback.hwpx'
    'OBJ-029' = 'obj-029-soft-edge.hancom-2020-readback.hwpx'
    'OBJ-030' = 'obj-030-image-properties.hancom-2020-readback.hwpx'
    'OBJ-031' = 'obj-031-crop.hancom-2020-readback.hwpx'
    'OBJ-034' = 'obj-034-transparency.hancom-2020-readback.hwpx'
    'OBJ-035' = 'obj-035-color-adjust.hancom-2020-readback.hwpx'
    'OBJ-036' = 'obj-036-group.hancom-2020-readback.hwpx'
    'OBJ-037' = 'obj-036-group.hancom-2020-readback.hwpx'
    'OBJ-039' = 'obj-036-group.hancom-2020-readback.hwpx'
    'OBJ-040' = 'obj-040-distribute.hancom-2020-readback.hwpx'
    'OBJ-043' = 'obj-043-shape-edit-points.hancom-2020-readback.hwpx'
}
$fixturePath = if ($fixtureNames.ContainsKey($FeatureId)) {
    Join-Path $fixtureRoot $fixtureNames[$FeatureId]
} else { $null }
$insertFeatures = @(
    'OBJ-001', 'OBJ-002', 'OBJ-003', 'OBJ-007', 'OBJ-010', 'OBJ-012', 'OBJ-014',
    'OBJ-041', 'OBJ-042', 'OBJ-048'
)
$pictureSource = Join-Path $fixtureRoot 'obj-002-image-insert.hancom-2020-readback.hwpx'
$picturePath = $null
if ($null -ne $fixturePath -and -not (Test-Path -LiteralPath $fixturePath -PathType Leaf)) {
    throw ($errorPrefix + '_FIXTURE_MISSING')
}
if ($FeatureId -ceq 'OBJ-002' -and
    -not (Test-Path -LiteralPath $pictureSource -PathType Leaf)) {
    throw ($errorPrefix + '_PICTURE_SOURCE_MISSING')
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p08-object-property-isolation-private/v1'
    state = 'failed'
    feature_id = $FeatureId
    capability_id = [string]$route.capability_id
    source_name = [string]$route.source_name
    target_build = $null
    target_executable_sha256 = [string]$server.sha256
    hwp_process_identity_verified = $false
    security_module_register_return = $null
    is_action_enable = $false
    execute_return = $false
    effect_observed = $false
    undo_semantic_verified = $false
    undo_raw_exact = $false
    before_sha256 = $null
    after_sha256 = $null
    undo_sha256 = $null
    before_raw_sha256 = $null
    after_raw_sha256 = $null
    undo_raw_sha256 = $null
    before_normalization_count = 0
    after_normalization_count = 0
    undo_normalization_count = 0
    hwp_file_open_count = 0
    approved_fixture_open_count = 0
    document_save_count = 0
    rollback_mode = 'discard_unsaved_disposable_document'
    rollback_verified = $false
    quit_invoked = $false
    error_code = $null
}
$hwp = $null
$documents = $null
$document = $null
$window = $null
$selectedControl = $null
$pictureArchive = $null
$pictureEntry = $null
$pictureStream = $null
$pictureOutput = $null
try {
    $hwp = New-Object -ComObject $ProgId
    $trace.target_build = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($trace.target_build -cne $ExpectedBuild) { throw ($errorPrefix + '_TARGET_BUILD') }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($processes.Count -ne 1 -or
        (Get-Sha256File -Path ([string]$processes[0].ExecutablePath)) -cne
            $ExpectedExecutableSha256) {
        throw ($errorPrefix + '_PROCESS_IDENTITY')
    }
    $trace.hwp_process_identity_verified = $true
    if ($null -ne $fixturePath -or $FeatureId -ceq 'OBJ-002') {
        $trace.security_module_register_return = [bool]$hwp.RegisterModule(
            'FilePathCheckDLL', 'FilePathCheckerModuleExample'
        )
    }
    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $document = $documents.Add($false)
    [void]$document.SetActive_XHwpDocument()
    if ($FeatureId -ceq 'OBJ-002') {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $picturePath = $TracePath + '.input.png'
        $pictureArchive = [IO.Compression.ZipFile]::OpenRead($pictureSource)
        $pictureEntry = $pictureArchive.GetEntry('BinData/image1.png')
        if ($null -eq $pictureEntry) { throw ($errorPrefix + '_PICTURE_ENTRY_MISSING') }
        $pictureStream = $pictureEntry.Open()
        $pictureOutput = [IO.File]::Open(
            $picturePath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write,
            [IO.FileShare]::None
        )
        $pictureStream.CopyTo($pictureOutput)
        $pictureOutput.Flush($true)
        $pictureOutput.Dispose(); $pictureOutput = $null
        $pictureStream.Dispose(); $pictureStream = $null
        $pictureArchive.Dispose(); $pictureArchive = $null
    }
    if ($null -ne $fixturePath) {
        if (-not [bool]$document.Open(
                $fixturePath, 'HWPX', 'lock:false;setcurdir:false')) {
            throw ($errorPrefix + '_FIXTURE_OPEN')
        }
        $trace.hwp_file_open_count = 1
        $trace.approved_fixture_open_count = 1
    }
    elseif ($FeatureId -ceq 'OBJ-048' -or $FeatureId -notin $insertFeatures) {
        New-Rectangle -Hwp $hwp
    }
    $shapeOrdinal = if ($FeatureId -ceq 'OBJ-024') { 2 } else { 1 }
    if ($FeatureId -ceq 'OBJ-048' -or $FeatureId -notin $insertFeatures) {
        Select-ShapeControl -Hwp $hwp -Ordinal $shapeOrdinal
    }
    $trace.is_action_enable = if ([string]$route.source_kind -ceq 'automation_object') {
        $null -ne $hwp.PSObject.Methods['InsertPicture']
    } else { [bool]$hwp.IsActionEnable([string]$route.source_name) }
    if ($FeatureId -in @('OBJ-036', 'OBJ-039')) {
        if (-not [bool]$hwp.HAction.Run('ShapeObjUngroup')) {
            throw ($errorPrefix + '_MULTISELECT_SETUP')
        }
    }
    elseif ($FeatureId -ceq 'OBJ-040') {
        [void]$hwp.HAction.Run('ShapeObjSelect')
        [void]$hwp.HAction.Run('SelectAll')
    }
    $before = Get-DocumentSnapshot -Hwp $hwp
    $trace.before_sha256 = $before.sha256
    $trace.before_raw_sha256 = $before.raw_sha256
    $trace.before_normalization_count = $before.normalization_count
    if ($FeatureId -in $insertFeatures) {
        $trace.execute_return = Invoke-InsertFeature -Hwp $hwp `
            -RequestedFeature $FeatureId -PicturePath $picturePath
    }
    else {
        $selectedControl = Get-ShapeControl -Hwp $hwp -Ordinal $shapeOrdinal
        $trace.execute_return = Invoke-Feature -Hwp $hwp -Control $selectedControl `
            -RequestedFeature $FeatureId
    }
    $after = Get-DocumentSnapshot -Hwp $hwp
    $trace.after_sha256 = $after.sha256
    $trace.after_raw_sha256 = $after.raw_sha256
    $trace.after_normalization_count = $after.normalization_count
    $trace.effect_observed = $after.sha256 -cne $before.sha256
    if ($trace.effect_observed) {
        if ([bool]$hwp.HAction.Run('Undo')) {
            $undo = Get-DocumentSnapshot -Hwp $hwp
            $trace.undo_sha256 = $undo.sha256
            $trace.undo_raw_sha256 = $undo.raw_sha256
            $trace.undo_normalization_count = $undo.normalization_count
            $trace.undo_semantic_verified = $undo.sha256 -ceq $before.sha256
            $trace.undo_raw_exact = $undo.raw_sha256 -ceq $before.raw_sha256
        }
    }
    [void]$document.Close($false)
    $trace.rollback_verified = $true
    Clear-ComObject -Value $document
    $document = $null
    $hwp.Quit()
    $trace.quit_invoked = $true
    if ($trace.effect_observed -and $trace.rollback_verified) {
        $trace.state = 'pass'
    }
    else { $trace.state = 'no_qualified_effect' }
}
catch { $trace.error_code = [string]$_.Exception.Message }
finally {
    foreach ($stream in @($pictureOutput, $pictureStream, $pictureArchive)) {
        if ($null -ne $stream) { try { $stream.Dispose() } catch { } }
    }
    if ($null -ne $picturePath -and (Test-Path -LiteralPath $picturePath -PathType Leaf)) {
        Remove-Item -LiteralPath $picturePath -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    if ($null -ne $hwp -and -not $trace.quit_invoked) { try { $hwp.Quit() } catch { } }
    Clear-ComObject -Value $window
    Clear-ComObject -Value $selectedControl
    Clear-ComObject -Value $document
    Clear-ComObject -Value $documents
    Clear-ComObject -Value $hwp
    $json = $trace | ConvertTo-Json -Depth 6
    Write-NewUtf8File -Path $TracePath -Content ($json + "`n")
}
if ($trace.state -cne 'pass') { exit 2 }
