[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OverlayPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOverlaySha256,
    [Parameter(Mandatory)][string]$FixtureControlsPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureControlsSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [ValidateRange(1, 61)][int]$StartIndex = 1,
    [ValidateRange(1, 61)][int]$EndIndex = 61
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

function Write-ProgressRecord {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$FeatureId,
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][string]$State
    )
    $record = [ordered]@{
        feature_id = $FeatureId
        phase = $Phase
        state = $State
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
    }
    [IO.File]::AppendAllText(
        $Path,
        ($record | ConvertTo-Json -Compress) + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Invoke-Run {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)][string]$Action)
    if ($Hwp.HAction.Run($Action) -eq $false) {
        throw ('P06_V2_RUNTIME_ACTION_FAILED_' + $Action.ToUpperInvariant())
    }
}

function Write-Text {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)][string]$Text)
    $insert = $null
    $hset = $null
    try {
        $insert = $Hwp.HParameterSet.HInsertText
        $hset = $insert.HSet
        if ($Hwp.HAction.GetDefault('InsertText', $hset) -eq $false) {
            throw 'P06_V2_RUNTIME_INSERT_DEFAULT_FAILED'
        }
        $insert.Text = $Text
        if ($Hwp.HAction.Execute('InsertText', $hset) -eq $false) {
            throw 'P06_V2_RUNTIME_INSERT_FAILED'
        }
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $insert
    }
}

function New-Table {
    param(
        [Parameter(Mandatory)]$Hwp,
        [int]$Rows = 4,
        [int]$Columns = 4
    )
    $creation = $null
    $hset = $null
    try {
        $creation = $Hwp.HParameterSet.HTableCreation
        $hset = $creation.HSet
        if ($Hwp.HAction.GetDefault('TableCreate', $hset) -eq $false) {
            throw 'P06_V2_RUNTIME_TABLE_DEFAULT_FAILED'
        }
        $creation.Rows = $Rows
        $creation.Cols = $Columns
        if ($Hwp.HAction.Execute('TableCreate', $hset) -eq $false) {
            throw 'P06_V2_RUNTIME_TABLE_CREATE_FAILED'
        }
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $creation
    }
}

function New-NumericTable {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)]$Controls,
        [switch]$Reverse
    )
    New-Table -Hwp $Hwp
    foreach ($index in 1..16) {
        $value = if ($Reverse) { 17 - $index } else { $index }
        Write-Text -Hwp $Hwp -Text ([string]$value)
        if ($index -lt 16) {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        }
    }
    1..15 | ForEach-Object {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_left_cell)
    }
}

function New-ChartTable {
    param([Parameter(Mandatory)]$Hwp)
    New-Table -Hwp $Hwp -Rows 3 -Columns 3
    Invoke-Run -Hwp $Hwp -Action 'TableRightCell'
    $values = @('Series-A', 'Series-B', 'Category-A', '1', '2', 'Category-B', '3', '4')
    for ($index = 0; $index -lt $values.Count; $index++) {
        Write-Text -Hwp $Hwp -Text ([string]$values[$index])
        if ($index -lt ($values.Count - 1)) { Invoke-Run -Hwp $Hwp -Action 'TableRightCell' }
    }
    1..8 | ForEach-Object { Invoke-Run -Hwp $Hwp -Action 'TableLeftCell' }
}

function Get-ScanSnapshot {
    param([Parameter(Mandatory)]$Hwp)
    $scanInitialized = $false
    $records = New-Object System.Collections.Generic.List[string]
    $statuses = New-Object System.Collections.Generic.List[int]
    $textSeed = New-Object Text.StringBuilder
    try {
        if ($Hwp.InitScan(0x07, 0x0077, 0, 0, 0, 0) -eq $false) {
            throw 'P06_V2_RUNTIME_INIT_SCAN_FAILED'
        }
        $scanInitialized = $true
        foreach ($iteration in 1..4096) {
            $value = [string]::Empty
            $status = [int]$Hwp.GetText([ref]$value)
            if ($null -eq $value) { $value = [string]::Empty }
            $value = $value.Replace([string][char]0, '').Replace("`r`n", "`n").Replace(
                "`r", "`n"
            ).Normalize([Text.NormalizationForm]::FormC)
            $valueSha = Get-Sha256String -Value $value
            $statuses.Add($status)
            $records.Add(('{0}|{1}|{2}' -f $status, $value.Length, $valueSha))
            [void]$textSeed.Append($value)
            if ($status -in @(0, 1)) { break }
            if ($iteration -eq 4096) { throw 'P06_V2_RUNTIME_SCAN_LIMIT_EXCEEDED' }
        }
        if ($statuses.Count -eq 0 -or $statuses[-1] -notin @(0, 1)) {
            throw 'P06_V2_RUNTIME_SCAN_TERMINAL_MISSING'
        }
        return [ordered]@{
            sha256 = Get-Sha256String -Value ($records -join "`n")
            text_sha256 = Get-Sha256String -Value $textSeed.ToString()
            call_count = $statuses.Count
            control_enter_count = @($statuses | Where-Object { $_ -eq 4 }).Count
            control_exit_count = @($statuses | Where-Object { $_ -eq 5 }).Count
            paragraph_count = @($statuses | Where-Object { $_ -eq 3 }).Count
        }
    }
    finally {
        if ($scanInitialized) { try { [void]$Hwp.ReleaseScan() } catch { } }
    }
}

function Get-ItemProjection {
    param(
        [Parameter(Mandatory)]$Set,
        [Parameter(Mandatory)][string[]]$Names,
        [Parameter(Mandatory)][string]$Prefix
    )
    $items = New-Object System.Collections.Generic.List[string]
    foreach ($name in $Names) {
        try {
            $value = $Set.Item($name)
            if ($null -eq $value -or [Runtime.InteropServices.Marshal]::IsComObject($value)) {
                $valueText = '<object-or-null>'
            }
            elseif ($value -is [Array]) {
                $valueText = @($value | ForEach-Object { [string]$_ }) -join ','
            }
            else { $valueText = [string]$value }
            $items.Add(('{0}.{1}={2}' -f $Prefix, $name, $valueText))
        }
        catch { $items.Add(('{0}.{1}=<unavailable>' -f $Prefix, $name)) }
    }
    return @($items)
}

function Get-NestedSet {
    param(
        [Parameter(Mandatory)]$Parent,
        [Parameter(Mandatory)][string]$ItemId,
        [Parameter(Mandatory)][string]$SetId,
        [switch]$Create
    )
    try {
        $value = $Parent.Item($ItemId)
        if ($null -ne $value) { return $value }
    }
    catch { }
    if ($Create) { return $Parent.CreateItemSet($ItemId, $SetId) }
    return $null
}

function Get-ActionSetProjection {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)][string]$ActionId,
        [Parameter(Mandatory)][string]$SetKind
    )
    $action = $null
    $set = $null
    $nested = $null
    $records = New-Object System.Collections.Generic.List[string]
    try {
        $action = $Hwp.CreateAction($ActionId)
        if ($null -eq $action) { return '<action-unavailable>' }
        $set = $action.CreateSet()
        if ($null -eq $set -or $action.GetDefault($set) -eq $false) {
            return '<default-unavailable>'
        }
        switch ($SetKind) {
            'shape' {
                foreach ($entry in @(Get-ItemProjection -Set $set -Prefix 'shape' -Names @(
                    'TreatAsChar', 'AffectsLine', 'VertRelTo', 'VertAlign', 'VertOffset',
                    'HorzRelTo', 'HorzAlign', 'HorzOffset', 'FlowWithText', 'AllowOverlap',
                    'WidthRelTo', 'Width', 'HeightRelTo', 'Height', 'ProtectSize', 'TextWrap',
                    'TextFlow', 'OutsideMarginLeft', 'OutsideMarginRight', 'OutsideMarginTop',
                    'OutsideMarginBottom', 'Lock', 'HoldAnchorObj'
                ))) { $records.Add($entry) }
                $nested = Get-NestedSet -Parent $set -ItemId 'ShapeTableCell' -SetId 'Cell'
                if ($null -ne $nested) {
                    foreach ($entry in @(Get-ItemProjection -Set $nested -Prefix 'cell' -Names @(
                        'HasMargin', 'Protected', 'Header', 'Width', 'Height', 'Editable'
                    ))) { $records.Add($entry) }
                    Clear-ComObject -Value $nested
                    $nested = $null
                }
                $nested = Get-NestedSet -Parent $set -ItemId 'ShapeListProperties' -SetId 'ListProperties'
                if ($null -ne $nested) {
                    foreach ($entry in @(Get-ItemProjection -Set $nested -Prefix 'list' -Names @(
                        'TextDirection', 'LineWrap', 'VertAlign', 'MarginLeft', 'MarginRight',
                        'MarginTop', 'MarginBottom'
                    ))) { $records.Add($entry) }
                    Clear-ComObject -Value $nested
                    $nested = $null
                }
                $nested = Get-NestedSet -Parent $set -ItemId 'ShapeCaption' -SetId 'Caption'
                if ($null -ne $nested) {
                    foreach ($entry in @(Get-ItemProjection -Set $nested -Prefix 'caption' -Names @(
                        'Side', 'Width', 'Gap', 'CapFullSize'
                    ))) { $records.Add($entry) }
                }
            }
            'border' {
                foreach ($entry in @(Get-ItemProjection -Set $set -Prefix 'border' -Names @(
                    'ApplyTo', 'NoNeighborCell', 'BorderTypeLeft', 'BorderTypeRight',
                    'BorderTypeTop', 'BorderTypeBottom', 'BorderWidthLeft', 'BorderWidthRight',
                    'BorderWidthTop', 'BorderWidthBottom', 'BorderColorLeft', 'BorderColorRight',
                    'BorderColorTop', 'BorderColorBottom', 'SlashFlag', 'BackSlashFlag',
                    'DiagonalType', 'DiagonalWidth', 'DiagonalColor'
                ))) { $records.Add($entry) }
                $nested = Get-NestedSet -Parent $set -ItemId 'FillAttr' -SetId 'DrawFillAttr'
                if ($null -ne $nested) {
                    foreach ($entry in @(Get-ItemProjection -Set $nested -Prefix 'fill' -Names @(
                        'Type', 'WinBrushFaceStyle', 'WinBrushHatchColor',
                        'WinBrushFaceColor', 'WindowsBrush'
                    ))) { $records.Add($entry) }
                }
            }
            'table' {
                foreach ($entry in @(Get-ItemProjection -Set $set -Prefix 'table' -Names @(
                    'PageBreak', 'RepeatHeader', 'CellSpacing', 'CellMarginLeft',
                    'CellMarginRight', 'CellMarginTop', 'CellMarginBottom'
                ))) { $records.Add($entry) }
            }
            'formula' {
                foreach ($entry in @(Get-ItemProjection -Set $set -Prefix 'formula' -Names @(
                    'Command', 'Editable', 'FieldDirty', 'User'
                ))) { $records.Add($entry) }
            }
            'paragraph' {
                foreach ($entry in @(Get-ItemProjection -Set $set -Prefix 'paragraph' -Names @(
                    'AlignType', 'LineSpacingType', 'LineSpacing'
                ))) { $records.Add($entry) }
            }
            default { return '<not-applicable>' }
        }
        return Get-Sha256String -Value ($records -join "`n")
    }
    finally {
        Clear-ComObject -Value $nested
        Clear-ComObject -Value $set
        Clear-ComObject -Value $action
    }
}

function Get-CanonicalSnapshot {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)][string]$FeatureId,
        [Parameter(Mandatory)][string]$ActionId
    )
    $scan = Get-ScanSnapshot -Hwp $Hwp
    $hwpml = [string]$Hwp.GetTextFile('HWPML2X', '')
    if ([string]::IsNullOrWhiteSpace($hwpml)) {
        throw 'P06_V2_RUNTIME_HWPML_SNAPSHOT_MISSING'
    }
    $hwpml = $hwpml.Replace("`r`n", "`n").Replace("`r", "`n").Normalize(
        [Text.NormalizationForm]::FormC
    )
    $hwpmlSha256 = Get-Sha256String -Value $hwpml
    $bodyStart = $hwpml.IndexOf('<BODY', [StringComparison]::Ordinal)
    $bodyClose = $hwpml.IndexOf('</BODY>', [StringComparison]::Ordinal)
    if ($bodyStart -lt 0 -or $bodyClose -lt $bodyStart) {
        throw 'P06_V2_RUNTIME_HWPML_BODY_MISSING'
    }
    $body = $hwpml.Substring($bodyStart, $bodyClose + 7 - $bodyStart)
    $bodySha256 = Get-Sha256String -Value $body
    $shapeObjectMatch = [regex]::Match($body, '<SHAPEOBJECT\b[^>]*>')
    $shapeProjection = $null
    if ($shapeObjectMatch.Success) {
        $shapeProjection = [ordered]@{
            sha256 = Get-Sha256String -Value $shapeObjectMatch.Value
            width = [regex]::Match($shapeObjectMatch.Value, '\bWidth="([^"]*)"').Groups[1].Value
            height = [regex]::Match($shapeObjectMatch.Value, '\bHeight="([^"]*)"').Groups[1].Value
            width_rel_to = [regex]::Match($shapeObjectMatch.Value, '\bWidthRelTo="([^"]*)"').Groups[1].Value
            height_rel_to = [regex]::Match($shapeObjectMatch.Value, '\bHeightRelTo="([^"]*)"').Groups[1].Value
        }
    }
    $seed = 'scan=' + $scan.sha256 + "`nbody=" + $bodySha256
    return [ordered]@{
        sha256 = Get-Sha256String -Value $seed
        scan = $scan
        hwpml_sha256 = $hwpmlSha256
        hwpml_char_count = $hwpml.Length
        hwpml_body_sha256 = $bodySha256
        hwpml_body_char_count = $body.Length
        shape_object = $shapeProjection
    }
}

function Set-ActionItems {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)][string]$ActionId,
        [Parameter(Mandatory)][object[]]$Items
    )
    $action = $null
    $set = $null
    $nested = $null
    try {
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug = @{ stage = 'create_action' } }
        $action = $Hwp.CreateAction($ActionId)
        if ($null -eq $action) { throw 'P06_V2_RUNTIME_CREATE_ACTION_FAILED' }
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug.stage = 'create_set' }
        $set = $action.CreateSet()
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug.stage = 'get_default' }
        if ($null -eq $set -or $action.GetDefault($set) -eq $false) {
            throw 'P06_V2_RUNTIME_GET_DEFAULT_FAILED'
        }
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug.stage = 'set_items' }
        foreach ($item in $Items) {
            $target = $set
            if ($null -ne $item.path -and [string]$item.path -ne '') {
                $nested = Get-NestedSet -Parent $set -ItemId ([string]$item.path) `
                    -SetId ([string]$item.set_id) -Create
                if ($null -eq $nested) { throw 'P06_V2_RUNTIME_NESTED_SET_FAILED' }
                $target = $nested
            }
            $value = $item.value
            if ([string]$item.kind -ceq 'rgb') {
                $value = $Hwp.RGBColor([int]$item.red, [int]$item.green, [int]$item.blue)
            }
            [void]$target.SetItem([string]$item.name, $value)
            if ($target -ne $set) {
                Clear-ComObject -Value $nested
                $nested = $null
            }
        }
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug.stage = 'execute' }
        if ($action.Execute($set) -eq $false) { throw 'P06_V2_RUNTIME_EXECUTE_FAILED' }
        if ($ActionId -ceq 'Sort') { $script:p06CandidateDebug.stage = 'complete' }
    }
    finally {
        Clear-ComObject -Value $nested
        Clear-ComObject -Value $set
        Clear-ComObject -Value $action
    }
}

function Item {
    param(
        [string]$Name,
        $Value,
        [string]$Path = '',
        [string]$SetId = ''
    )
    return [pscustomobject]@{
        name = $Name
        value = $Value
        path = $Path
        set_id = $SetId
        kind = 'value'
        red = 0
        green = 0
        blue = 0
    }
}

function RgbItem {
    param(
        [string]$Name,
        [int]$Red,
        [int]$Green,
        [int]$Blue,
        [string]$Path = '',
        [string]$SetId = ''
    )
    return [pscustomobject]@{
        name = $Name
        value = 0
        path = $Path
        set_id = $SetId
        kind = 'rgb'
        red = $Red
        green = $Green
        blue = $Blue
    }
}

function Prepare-Context {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)]$Controls,
        [Parameter(Mandatory)][string]$FeatureId
    )
    if ($FeatureId -ceq 'TABLE-001') { return 'blank_document' }
    if ($FeatureId -ceq 'TABLE-004') {
        Write-Text -Hwp $Hwp -Text "1`t2`r`n3`t4"
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.move_document_begin)
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.select_all)
        return 'selected_text'
    }
    if ($FeatureId -in @('TABLE-032', 'TABLE-033', 'TABLE-049')) {
        New-Table -Hwp $Hwp -Rows 1 -Columns 3
        Write-Text -Hwp $Hwp -Text '1200'
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        Write-Text -Hwp $Hwp -Text '3400'
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        Invoke-Run -Hwp $Hwp -Action 'TableFormulaSumHor'
        if ($FeatureId -in @('TABLE-032', 'TABLE-033')) {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
            if ($FeatureId -ceq 'TABLE-032') {
                Invoke-Run -Hwp $Hwp -Action 'TableDeleteComma'
            }
            return 'large_formula_cell_block'
        }
        return 'large_formula_cell'
    }
    New-NumericTable -Hwp $Hwp -Controls $Controls
    if ($FeatureId -ceq 'TABLE-003') {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        Invoke-Run -Hwp $Hwp -Action 'TableCellBorderDiagonalDown'
        return 'single_cell_with_diagonal'
    }
    if ($FeatureId -ceq 'TABLE-010') {
        1..4 | ForEach-Object { Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell) }
        return 'current_row_boundary'
    }
    if ($FeatureId -ceq 'TABLE-011') {
        [int]$savedList = 0
        [int]$savedPara = 0
        [int]$savedPos = 0
        [void]$Hwp.GetPos([ref]$savedList, [ref]$savedPara, [ref]$savedPos)
        1..4 | ForEach-Object { Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell) }
        Invoke-Run -Hwp $Hwp -Action 'TableSplitTable'
        [void]$Hwp.SetPos($savedList, $savedPara, $savedPos)
        return 'first_of_adjacent_split_tables'
    }
    if ($FeatureId -in @('TABLE-012', 'TABLE-013', 'TABLE-014', 'TABLE-015')) {
        return 'current_cell'
    }
    if ($FeatureId -ceq 'TABLE-018') {
        Invoke-Run -Hwp $Hwp -Action 'TableResizeExDown'
    }
    if ($FeatureId -ceq 'TABLE-019') {
        Invoke-Run -Hwp $Hwp -Action 'TableResizeExRight'
    }
    if ($FeatureId -ceq 'TABLE-037') {
        Invoke-Run -Hwp $Hwp -Action 'TableTreatAsChar'
        return 'floating_table'
    }
    if ($FeatureId -in @('TABLE-009', 'TABLE-020')) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block_extend)
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        return 'two_cell_horizontal_block'
    }
    if ($FeatureId -in @('TABLE-022', 'TABLE-023', 'TABLE-024')) {
        1..15 | ForEach-Object {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        }
        return 'formula_destination_cell'
    }
    if ($FeatureId -in @(
        'TABLE-008', 'TABLE-017', 'TABLE-018',
        'TABLE-019',
        'TABLE-057', 'TABLE-058'
    )) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        1..2 | ForEach-Object {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block_extend)
        }
        return 'rectangular_cell_block'
    }
    if ($FeatureId -in @('TABLE-025', 'TABLE-026', 'TABLE-027', 'TABLE-028', 'TABLE-029', 'TABLE-030')) {
        1..15 | ForEach-Object { Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell) }
        return 'formula_destination_cell'
    }
    if ($FeatureId -in @('TABLE-031', 'TABLE-059', 'TABLE-060', 'TABLE-061')) {
        1..15 | ForEach-Object { Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell) }
        if ($FeatureId -ne 'TABLE-031') {
            Invoke-Run -Hwp $Hwp -Action 'TableFormulaSumHor'
        }
        return 'formula_cell'
    }
    if ($FeatureId -in @(
        'TABLE-002', 'TABLE-016', 'TABLE-039', 'TABLE-040', 'TABLE-041', 'TABLE-045',
        'TABLE-046', 'TABLE-047', 'TABLE-048'
    )) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        return 'single_cell_block'
    }
    return 'current_table'
}

function Invoke-Candidate {
    param(
        [Parameter(Mandatory)]$Hwp,
        [Parameter(Mandatory)][string]$FeatureId,
        [Parameter(Mandatory)][string]$ActionId
    )
    $script:p06CandidateDebug = $null
    switch ($FeatureId) {
        'TABLE-001' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Rows' 2), (Item 'Cols' 3)
            )
        }
        'TABLE-004' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'DelimiterType' 0), (Item 'AutoOrDefine' 1), (Item 'KeepSeperator' 0)
            )
        }
        'TABLE-005' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'DelimiterType' 0))
        }
        'TABLE-006' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'ChartGroup' 1), (Item 'ChartIndex' 3)
            )
        }
        'TABLE-007' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'ProtectSize' 1))
        }
        'TABLE-008' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'BorderTypeTop' 1), (Item 'BorderWidthTop' 2),
                (RgbItem 'BorderColorTop' 17 34 51)
            )
        }
        'TABLE-009' {
            $parameter = $null
            $hset = $null
            $selectedCells = $null
            try {
                $parameter = $Hwp.HParameterSet.HCellBorderFill
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_ZONE_DEFAULT_FAILED'
                }
                $selectedCells = $parameter.SelCellsBorderFill
                if ($null -eq $selectedCells) {
                    throw 'P06_V2_RUNTIME_CELL_ZONE_SELECTED_SET_MISSING'
                }
                $slashValue = [int]$Hwp.Slash('OneLine')
                $selectedCells.SlashFlag = $slashValue
                $script:p06CandidateDebug = [ordered]@{
                    slash_value = $slashValue
                    property_write = 'pass'
                }
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_ZONE_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $selectedCells
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-012' { Invoke-Run -Hwp $Hwp -Action $ActionId }
        'TABLE-013' { Invoke-Run -Hwp $Hwp -Action $ActionId }
        'TABLE-014' { Invoke-Run -Hwp $Hwp -Action $ActionId }
        'TABLE-015' { Invoke-Run -Hwp $Hwp -Action $ActionId }
        'TABLE-016' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Cols' 2), (Item 'Rows' 1), (Item 'DistributeHeight' 0),
                (Item 'Merge' 0), (Item 'Mode2' 1)
            )
        }
        'TABLE-020' {
            $parameter = $null
            $hset = $null
            $selectedCells = $null
            $fill = $null
            try {
                $parameter = $Hwp.HParameterSet.HCellBorderFill
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_ZONE_FILL_DEFAULT_FAILED'
                }
                $selectedCells = $parameter.SelCellsBorderFill
                $fill = $selectedCells.FillAttr
                $fill.Type = 1
                $fill.WinBrushFaceStyle = -1
                $fill.WinBrushHatchColor = 0
                $fill.WinBrushFaceColor = $Hwp.RGBColor(32, 64, 96)
                $fill.WindowsBrush = 1
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_ZONE_FILL_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $fill
                Clear-ComObject -Value $selectedCells
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-021' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Type' 2), (Item 'SwapMargin' 1)
            )
        }
        'TABLE-022' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Command' '=SUM(A1:B2)')
            )
        }
        'TABLE-023' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Command' '=AVG(A1:B2)')
            )
        }
        'TABLE-024' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Command' '=PRODUCT(A1:B2)')
            )
        }
        'TABLE-031' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'Command' '=SUM(LEFT)'))
        }
        'TABLE-034' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'TreatAsChar' 0), (Item 'HorzRelTo' 0), (Item 'HorzAlign' 2),
                (Item 'HorzOffset' 700)
            )
        }
        'TABLE-035' {
            Invoke-Run -Hwp $Hwp -Action $ActionId
            Invoke-Run -Hwp $Hwp -Action 'TableResizeExDown'
            $script:p06CandidateDebug = [ordered]@{
                supplemental_action = 'TableResizeExDown'
            }
        }
        'TABLE-037' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'ShapeType' 6), (Item 'TreatAsChar' 0),
                (Item 'TextWrap' 1), (Item 'TextFlow' 0)
            )
        }
        'TABLE-038' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'OutsideMarginLeft' 500), (Item 'OutsideMarginRight' 600),
                (Item 'OutsideMarginTop' 700), (Item 'OutsideMarginBottom' 800)
            )
        }
        'TABLE-039' {
            $parameter = $null
            $hset = $null
            $cellProperties = $null
            try {
                $parameter = $Hwp.HParameterSet.HShapeObject
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_PADDING_DEFAULT_FAILED'
                }
                $cellProperties = $parameter.ShapeTableCell
                $cellProperties.HasMargin = 1
                $cellProperties.MarginLeft = 400
                $cellProperties.MarginRight = 500
                $cellProperties.MarginTop = 600
                $cellProperties.MarginBottom = 700
                [void]$hset.SetItem('ShapeType', 6)
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_PADDING_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $cellProperties
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-042' {
            $parameter = $null
            $hset = $null
            $cellProperties = $null
            try {
                $parameter = $Hwp.HParameterSet.HShapeObject
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_REPEAT_HEADER_DEFAULT_FAILED'
                }
                $cellProperties = $parameter.ShapeTableCell
                $cellProperties.Header = 1
                [void]$hset.SetItem('ShapeType', 6)
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_REPEAT_HEADER_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $cellProperties
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-045' {
            $parameter = $null
            $hset = $null
            $cellProperties = $null
            try {
                $parameter = $Hwp.HParameterSet.HShapeObject
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_PROTECTION_DEFAULT_FAILED'
                }
                $cellProperties = $parameter.ShapeTableCell
                $cellProperties.Protected = 1
                [void]$hset.SetItem('ShapeType', 6)
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_PROTECTION_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $cellProperties
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-046' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'BorderTypeTop' 1), (Item 'BorderWidthTop' 4),
                (RgbItem 'BorderColorTop' 68 85 102)
            )
        }
        'TABLE-048' {
            $parameter = $null
            $hset = $null
            $fill = $null
            try {
                $parameter = $Hwp.HParameterSet.HCellBorderFill
                $hset = $parameter.HSet
                if ($Hwp.HAction.GetDefault($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_FILL_DEFAULT_FAILED'
                }
                $fill = $parameter.FillAttr
                $fill.Type = 1
                $fill.WinBrushFaceStyle = -1
                $fill.WinBrushHatchColor = 0
                $fill.WinBrushFaceColor = $Hwp.RGBColor(200, 210, 220)
                $fill.WindowsBrush = 1
                if ($Hwp.HAction.Execute($ActionId, $hset) -eq $false) {
                    throw 'P06_V2_RUNTIME_CELL_FILL_EXECUTE_FAILED'
                }
            }
            finally {
                Clear-ComObject -Value $fill
                Clear-ComObject -Value $hset
                Clear-ComObject -Value $parameter
            }
        }
        'TABLE-049' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Command' '=SUM(LEFT)??%.2f,;;42.00')
            )
        }
        'TABLE-054' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'Rows' 2), (Item 'Cols' 2)
            )
        }
        'TABLE-056' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'DelimiterType' 0)
            )
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.move_document_begin)
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.select_all)
            Invoke-Run -Hwp $Hwp -Action 'Delete'
            Write-Text -Hwp $Hwp -Text (
                "13`t14`t15`t16`r`n9`t10`t11`t12`r`n5`t6`t7`t8`r`n1`t2`t3`t4"
            )
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.move_document_begin)
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.select_all)
            Set-ActionItems -Hwp $Hwp -ActionId 'TableStringToTable' -Items @(
                (Item 'DelimiterType' 0), (Item 'AutoOrDefine' 1), (Item 'KeepSeperator' 0)
            )
            $script:p06CandidateDebug = [ordered]@{
                supplemental_action = 'TableStringToTable'
                sort_axis = 'rows'
                sort_key = 'first_column_descending'
            }
        }
        'TABLE-057' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'AutoFillSection' 0), (Item 'AutoFillItem' 0)
            )
        }
        'TABLE-058' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @(
                (Item 'AutoFillSection' 0), (Item 'AutoFillItem' 1)
            )
        }
        'TABLE-059' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'Command' '=SUM(A1:B1)'))
        }
        'TABLE-060' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'Command' '=SUM($A1:B$1)'))
        }
        'TABLE-061' {
            Set-ActionItems -Hwp $Hwp -ActionId $ActionId -Items @((Item 'Command' '=SUM(A1:C1)'))
        }
        default { Invoke-Run -Hwp $Hwp -Action $ActionId }
    }
}

if (-not [Environment]::Is64BitOperatingSystem -or [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'P06_V2_RUNTIME_REQUIRES_X86_STA'
}
if ($StartIndex -gt $EndIndex) { throw 'P06_V2_RUNTIME_RANGE_INVALID' }
foreach ($pair in @(
    @($OverlayPath, $ExpectedOverlaySha256),
    @($FixtureControlsPath, $ExpectedFixtureControlsSha256)
)) {
    if ((Get-Sha256File -Path ([string]$pair[0])) -cne [string]$pair[1]) {
        throw 'P06_V2_RUNTIME_INPUT_IDENTITY_MISMATCH'
    }
}
if (Test-Path -LiteralPath $TracePath) { throw 'P06_V2_RUNTIME_TRACE_ALREADY_EXISTS' }
$progressPath = $TracePath + '.progress.jsonl'
if (Test-Path -LiteralPath $progressPath) { throw 'P06_V2_RUNTIME_PROGRESS_ALREADY_EXISTS' }
$progressStream = [IO.File]::Open(
    $progressPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
)
$progressStream.Dispose()
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'P06_V2_RUNTIME_PREEXISTING_HWP_PROCESS'
}

$overlay = Get-Content -LiteralPath $OverlayPath -Raw -Encoding UTF8 | ConvertFrom-Json
$controls = Get-Content -LiteralPath $FixtureControlsPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$overlay.schema_version -cne 'hwpx-agent.p06-table-automation-binding-overlay/v1' -or
    @($overlay.bindings).Count -ne 61 -or
    @($overlay.bindings | Where-Object { $_.status -cne 'candidate_unverified' }).Count -ne 0) {
    throw 'P06_V2_RUNTIME_OVERLAY_CONTRACT_MISMATCH'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-v2-runtime-private/v1'
    state = 'failed'
    overlay_sha256 = $ExpectedOverlaySha256
    fixture_controls_sha256 = $ExpectedFixtureControlsSha256
    target_build = $null
    target_executable_sha256 = $null
    snapshot_transport = 'in_memory_hwpml2x'
    start_index = $StartIndex
    end_index = $EndIndex
    case_count = $EndIndex - $StartIndex + 1
    completed_case_count = 0
    passed_case_count = 0
    candidate_action_execute_count = 0
    cases = @()
    user_document_opened = $false
    file_open_or_save_invoked = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_chart = $false
    quit_invoked = $false
    failed_feature_id = $null
    error_code = $null
}
$hwp = $null
$documents = $null
$document = $null
$windows = $null
$window = $null
try {
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $trace.target_build = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($trace.target_build -cne '11.0.0.9136') { throw 'P06_V2_RUNTIME_TARGET_MISMATCH' }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'")
    if ($processes.Count -ne 1) { throw 'P06_V2_RUNTIME_PROCESS_CARDINALITY_MISMATCH' }
    $trace.target_executable_sha256 = Get-Sha256File -Path ([string]$processes[0].ExecutablePath)
    $documents = $hwp.XHwpDocuments
    $orderedBindings = @($overlay.bindings | Sort-Object feature_id)
    foreach ($binding in @($orderedBindings[($StartIndex - 1)..($EndIndex - 1)])) {
        $featureId = [string]$binding.feature_id
        $actionId = [string]$binding.invocation.action_id
        $result = [ordered]@{
            feature_id = $featureId
            capability_id = [string]$binding.capability_id
            action_id = $actionId
            context = $null
            enabled = $false
            baseline = $null
            post = $null
            undo = $null
            baseline_artifact = $null
            post_artifact = $null
            undo_artifact = $null
            candidate_executed = $false
            candidate_debug = $null
            semantic_effect_observed = $false
            undo_executed = $false
            undo_attempt_count = 0
            undo_exact = $false
            rollback_mode = 'discard_unsaved_disposable_document'
            rollback_state = 'not_run'
            state = 'failed'
            error_code = $null
        }
        $trace.failed_feature_id = $featureId
        try {
            Write-ProgressRecord -Path $progressPath -FeatureId $featureId -Phase 'case' -State 'running'
            $document = $documents.Add($false)
            if ($null -eq $document) { throw 'P06_V2_RUNTIME_DOCUMENT_ADD_FAILED' }
            [void]$document.SetActive_XHwpDocument()
            if ($featureId -ceq 'TABLE-006') {
                $windows = $hwp.XHwpWindows
                $window = $windows.Item(0)
                $window.Visible = $true
                $trace.window_visible_for_chart = $true
            }
            if ($featureId -ceq 'TABLE-006') {
                New-ChartTable -Hwp $hwp
                $result.baseline = Get-CanonicalSnapshot -Hwp $hwp -FeatureId $featureId -ActionId $actionId
                Invoke-Run -Hwp $hwp -Action ([string]$controls.table_cell_block)
                1..2 | ForEach-Object {
                    Invoke-Run -Hwp $hwp -Action ([string]$controls.table_cell_block_extend)
                }
                $result.context = 'rectangular_chart_source_block'
            }
            else {
                $result.context = Prepare-Context -Hwp $hwp -Controls $controls -FeatureId $featureId
            }
            $result.enabled = [bool]$hwp.IsActionEnable($actionId)
            if (-not $result.enabled) { throw 'P06_V2_RUNTIME_ACTION_DISABLED_IN_CONTEXT' }
            if ($null -eq $result.baseline) {
                $result.baseline = Get-CanonicalSnapshot -Hwp $hwp -FeatureId $featureId -ActionId $actionId
            }
            Write-ProgressRecord -Path $progressPath -FeatureId $featureId -Phase 'candidate' -State 'running'
            Invoke-Candidate -Hwp $hwp -FeatureId $featureId -ActionId $actionId
            $result.candidate_debug = $script:p06CandidateDebug
            Write-ProgressRecord -Path $progressPath -FeatureId $featureId -Phase 'candidate' -State 'pass'
            $result.candidate_executed = $true
            $trace.candidate_action_execute_count += 1
            $result.post = Get-CanonicalSnapshot -Hwp $hwp -FeatureId $featureId -ActionId $actionId
            $result.semantic_effect_observed =
                [string]$result.post.sha256 -cne [string]$result.baseline.sha256
            if (-not $result.semantic_effect_observed) { throw 'P06_V2_RUNTIME_SEMANTIC_EFFECT_MISSING' }
            if ($document.Close($false) -eq $false) {
                throw 'P06_V2_RUNTIME_DISCARD_CLOSE_FAILED'
            }
            Clear-ComObject -Value $document
            $document = $null
            $result.rollback_state = 'pass'
            $result.state = 'pass'
            $trace.passed_case_count += 1
            Write-ProgressRecord -Path $progressPath -FeatureId $featureId -Phase 'case' -State 'pass'
        }
        catch {
            $result.candidate_debug = $script:p06CandidateDebug
            $result.error_code = [string]$_.Exception.Message
            $trace.error_code = [string]$_.Exception.Message
            Write-ProgressRecord -Path $progressPath -FeatureId $featureId -Phase 'case' -State 'failed'
        }
        finally {
            if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
            Clear-ComObject -Value $document
            $document = $null
            Clear-ComObject -Value $window
            Clear-ComObject -Value $windows
            $window = $null
            $windows = $null
            $trace.completed_case_count += 1
            $trace.cases += $result
        }
        if ([string]$result.state -cne 'pass') { break }
    }
    [void]$hwp.Quit()
    $trace.quit_invoked = $true
    if ($trace.completed_case_count -eq $trace.case_count -and
        $trace.passed_case_count -eq $trace.case_count -and
        $trace.candidate_action_execute_count -eq $trace.case_count) {
        $trace.state = 'pass'
        $trace.failed_feature_id = $null
        $trace.error_code = $null
    }
}
catch { $trace.error_code = [string]$_.Exception.Message }
finally {
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    Clear-ComObject -Value $document
    Clear-ComObject -Value $window
    Clear-ComObject -Value $windows
    Clear-ComObject -Value $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { [void]$hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [IO.File]::WriteAllText(
        $TracePath,
        ($trace | ConvertTo-Json -Depth 20) + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}
if ($trace.state -cne 'pass') { exit 1 }
