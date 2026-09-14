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

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Invoke-Run {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)][string]$Action)
    if ($Hwp.HAction.Run($Action) -eq $false) {
        throw ('P06_V2_SURFACE_FIXTURE_ACTION_FAILED_' + $Action.ToUpperInvariant())
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
            throw 'P06_V2_SURFACE_INSERT_DEFAULT_FAILED'
        }
        $insert.Text = $Text
        if ($Hwp.HAction.Execute('InsertText', $hset) -eq $false) {
            throw 'P06_V2_SURFACE_INSERT_FAILED'
        }
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $insert
    }
}

function New-Table {
    param([Parameter(Mandatory)]$Hwp)
    $creation = $null
    $hset = $null
    try {
        $creation = $Hwp.HParameterSet.HTableCreation
        $hset = $creation.HSet
        if ($Hwp.HAction.GetDefault('TableCreate', $hset) -eq $false) {
            throw 'P06_V2_SURFACE_TABLE_DEFAULT_FAILED'
        }
        $creation.Rows = 4
        $creation.Cols = 4
        if ($Hwp.HAction.Execute('TableCreate', $hset) -eq $false) {
            throw 'P06_V2_SURFACE_TABLE_CREATE_FAILED'
        }
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $creation
    }
}

function New-NumericTable {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)]$Controls)
    New-Table -Hwp $Hwp
    foreach ($index in 1..16) {
        Write-Text -Hwp $Hwp -Text ([string]$index)
        if ($index -lt 16) {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        }
    }
    1..15 | ForEach-Object {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_left_cell)
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
    New-NumericTable -Hwp $Hwp -Controls $Controls
    if ($FeatureId -ceq 'TABLE-010') {
        1..4 | ForEach-Object {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        }
        return 'current_row_boundary'
    }
    if ($FeatureId -in @('TABLE-012', 'TABLE-014')) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block_row)
        return 'current_row_block'
    }
    if ($FeatureId -in @('TABLE-013', 'TABLE-015')) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block_column)
        return 'current_column_block'
    }
    if ($FeatureId -in @(
        'TABLE-006', 'TABLE-008', 'TABLE-009', 'TABLE-017', 'TABLE-018',
        'TABLE-019', 'TABLE-020', 'TABLE-022', 'TABLE-023', 'TABLE-024',
        'TABLE-056', 'TABLE-057', 'TABLE-058'
    )) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        1..2 | ForEach-Object {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block_extend)
        }
        return 'rectangular_cell_block'
    }
    if ($FeatureId -in @('TABLE-025', 'TABLE-026', 'TABLE-027', 'TABLE-028', 'TABLE-029', 'TABLE-030')) {
        1..15 | ForEach-Object {
            Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_right_cell)
        }
        return 'formula_destination_cell'
    }
    if ($FeatureId -in @(
        'TABLE-002', 'TABLE-003', 'TABLE-016', 'TABLE-031', 'TABLE-032',
        'TABLE-033', 'TABLE-039', 'TABLE-040', 'TABLE-041', 'TABLE-045',
        'TABLE-046', 'TABLE-047', 'TABLE-048', 'TABLE-049', 'TABLE-059',
        'TABLE-060', 'TABLE-061'
    )) {
        Invoke-Run -Hwp $Hwp -Action ([string]$Controls.table_cell_block)
        return 'single_cell_block'
    }
    return 'current_table'
}

if (-not [Environment]::Is64BitOperatingSystem -or [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'P06_V2_SURFACE_REQUIRES_X86_STA'
}
if ($StartIndex -gt $EndIndex) { throw 'P06_V2_SURFACE_RANGE_INVALID' }
foreach ($pair in @(
    @($OverlayPath, $ExpectedOverlaySha256),
    @($FixtureControlsPath, $ExpectedFixtureControlsSha256)
)) {
    if ((Get-Sha256File -Path ([string]$pair[0])) -cne [string]$pair[1]) {
        throw 'P06_V2_SURFACE_INPUT_IDENTITY_MISMATCH'
    }
}
if (Test-Path -LiteralPath $TracePath) { throw 'P06_V2_SURFACE_TRACE_ALREADY_EXISTS' }
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'P06_V2_SURFACE_PREEXISTING_HWP_PROCESS'
}

$overlay = Get-Content -LiteralPath $OverlayPath -Raw -Encoding UTF8 | ConvertFrom-Json
$controls = Get-Content -LiteralPath $FixtureControlsPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$overlay.schema_version -cne 'hwpx-agent.p06-table-automation-binding-overlay/v1' -or
    @($overlay.bindings).Count -ne 61 -or
    @($overlay.bindings | Where-Object { $_.status -cne 'candidate_unverified' }).Count -ne 0) {
    throw 'P06_V2_SURFACE_OVERLAY_CONTRACT_MISMATCH'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-v2-surface-private/v1'
    state = 'failed'
    overlay_sha256 = $ExpectedOverlaySha256
    fixture_controls_sha256 = $ExpectedFixtureControlsSha256
    target_build = $null
    start_index = $StartIndex
    end_index = $EndIndex
    case_count = $EndIndex - $StartIndex + 1
    completed_case_count = 0
    enabled_case_count = 0
    default_read_passed_count = 0
    cases = @()
    user_document_opened = $false
    file_open_or_save_invoked = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    quit_invoked = $false
    failed_feature_id = $null
    error_code = $null
}
$hwp = $null
$documents = $null
$document = $null
$action = $null
$set = $null
try {
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $trace.target_build = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($trace.target_build -cne '11.0.0.9136') { throw 'P06_V2_SURFACE_TARGET_MISMATCH' }
    $documents = $hwp.XHwpDocuments
    $orderedBindings = @($overlay.bindings | Sort-Object feature_id)
    foreach ($binding in @($orderedBindings[($StartIndex - 1)..($EndIndex - 1)])) {
        $featureId = [string]$binding.feature_id
        $result = [ordered]@{
            feature_id = $featureId
            capability_id = [string]$binding.capability_id
            action_id = [string]$binding.invocation.action_id
            parameter_set_id = $binding.invocation.parameter_set_id
            context = $null
            is_action_enable = $false
            action_created = $false
            set_created = $false
            get_default_state = 'not_applicable'
            state = 'failed'
            error_code = $null
        }
        $trace.failed_feature_id = $featureId
        try {
            $document = $documents.Add($false)
            if ($null -eq $document) { throw 'P06_V2_SURFACE_DOCUMENT_ADD_FAILED' }
            [void]$document.SetActive_XHwpDocument()
            $result.context = Prepare-Context -Hwp $hwp -Controls $controls -FeatureId $featureId
            $result.is_action_enable = [bool]$hwp.IsActionEnable([string]$result.action_id)
            if ($result.is_action_enable) { $trace.enabled_case_count += 1 }
            $action = $hwp.CreateAction([string]$result.action_id)
            if ($null -eq $action) { throw 'P06_V2_SURFACE_ACTION_CREATE_FAILED' }
            $result.action_created = $true
            if ($null -ne $result.parameter_set_id) {
                $set = $action.CreateSet()
                if ($null -eq $set) { throw 'P06_V2_SURFACE_SET_CREATE_FAILED' }
                $result.set_created = $true
                if ($action.GetDefault($set) -eq $false) {
                    throw 'P06_V2_SURFACE_GET_DEFAULT_FAILED'
                }
                $result.get_default_state = 'pass'
                $trace.default_read_passed_count += 1
            }
            $result.state = if ($result.is_action_enable) {
                'surface_present_enabled'
            }
            else { 'surface_present_disabled_in_context' }
        }
        catch {
            $result.error_code = [string]$_.Exception.Message
        }
        finally {
            Clear-ComObject -Value $set
            Clear-ComObject -Value $action
            $set = $null
            $action = $null
            if ($null -ne $document) {
                try { [void]$document.Close($false) } catch { }
                Clear-ComObject -Value $document
                $document = $null
            }
        }
        $trace.cases += $result
        $trace.completed_case_count += 1
        if ($result.state -eq 'failed') { throw ([string]$result.error_code) }
    }
    $trace.failed_feature_id = $null
    $hwp.Quit()
    $trace.quit_invoked = $true
    $trace.state = 'pass'
}
catch {
    $trace.error_code = [string]$_.Exception.Message
}
finally {
    Clear-ComObject -Value $set
    Clear-ComObject -Value $action
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    Clear-ComObject -Value $document
    Clear-ComObject -Value $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { $hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$json = $trace | ConvertTo-Json -Depth 8
$bytes = [Text.UTF8Encoding]::new($false).GetBytes($json)
$stream = [IO.File]::Open($TracePath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
finally { $stream.Dispose() }
$json
if ($trace.state -cne 'pass') { exit 2 }
