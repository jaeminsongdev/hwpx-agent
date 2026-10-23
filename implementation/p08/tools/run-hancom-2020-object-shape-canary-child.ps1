[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OverlayPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOverlaySha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'P08_OBJECT_SHAPE_CANARY'
$featureOrder = @('OBJ-026', 'OBJ-033', 'OBJ-038', 'OBJ-045', 'OBJ-013')

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object {
            $_.ToString('x2')
        }) -join '')
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

function Add-Progress {
    param([Parameter(Mandatory)][object]$Value)
    $line = ($Value | ConvertTo-Json -Compress -Depth 5) + "`n"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($line)
    $stream = [IO.File]::Open(
        $ProgressPath, [IO.FileMode]::Append, [IO.FileAccess]::Write, [IO.FileShare]::Read
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
    $rawNormalized = $value.Replace("`0", '').Replace("`r`n", "`n").Replace("`r", "`n")
    # HWP 2020 can materialize an omitted DRAWTEXT Name attribute as Name=""
    # after a shape action and keep that serializer-default form after Undo.
    # Treat only this empty optional attribute as semantically equivalent; all
    # geometry, styling, text, and non-empty Name values remain hash-significant.
    $emptyNamePattern = '(<DRAWTEXT\b[^<>]*?)\sName=""(?=[^<>]*>)'
    $normalizationCount = [regex]::Matches(
        $rawNormalized, $emptyNamePattern,
        [Text.RegularExpressions.RegexOptions]::CultureInvariant
    ).Count
    $semanticNormalized = [regex]::Replace(
        $rawNormalized, $emptyNamePattern, '$1',
        [Text.RegularExpressions.RegexOptions]::CultureInvariant
    )
    return [ordered]@{
        sha256 = Get-Sha256String -Value $semanticNormalized
        length = $semanticNormalized.Length
        raw_sha256 = Get-Sha256String -Value $rawNormalized
        raw_length = $rawNormalized.Length
        normalization_id = 'hwpml2x-drawtext-empty-name-default/v1'
        normalization_count = $normalizationCount
        text = $rawNormalized
    }
}

function New-Rectangle {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][int]$HorizontalOffset,
        [Parameter(Mandatory)][int]$VerticalOffset
    )
    $action = $null
    $set = $null
    $layout = $null
    $points = $null
    try {
        $action = $Hwp.CreateAction('DrawObjCreatorRectangle')
        if ($null -eq $action) { throw ($errorPrefix + '_SETUP_ACTION_MISSING') }
        $set = $action.CreateSet()
        if ($null -eq $set -or -not [bool]$action.GetDefault($set)) {
            throw ($errorPrefix + '_SETUP_DEFAULT_FAILED')
        }
        [void]$set.SetItem('TreatAsChar', 0)
        [void]$set.SetItem('TextWrap', 3)
        [void]$set.SetItem('VertOffset', $VerticalOffset)
        [void]$set.SetItem('VertAlign', 0)
        [void]$set.SetItem('VertRelTo', 0)
        [void]$set.SetItem('HorzOffset', $HorizontalOffset)
        [void]$set.SetItem('HorzAlign', 0)
        [void]$set.SetItem('HorzRelTo', 0)
        [void]$set.SetItem('HeightRelTo', 2)
        [void]$set.SetItem('Height', 4200)
        [void]$set.SetItem('WidthRelTo', 4)
        [void]$set.SetItem('Width', 6800)
        [void]$set.SetItem('AdjustTextbox', 1)
        [void]$set.SetItem('ShapeCreationMode', 0)
        [void]$set.SetItem('ShapeCreationType', 1)
        $layout = $set.CreateItemSet('ShapeDrawLayOut', 'DrawLayOut')
        if ($null -eq $layout) { throw ($errorPrefix + '_SETUP_LAYOUT_FAILED') }
        [void]$layout.SetItem('CreateNumPt', 4)
        $points = $layout.CreateItemArray('CreatePt', 8)
        if ($null -eq $points) { throw ($errorPrefix + '_SETUP_POINTS_FAILED') }
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

function Invoke-Candidate {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][string]$ActionId,
        [Parameter(Mandatory)][bool]$SetExpected
    )
    $action = $null
    $set = $null
    try {
        $action = $Hwp.CreateAction($ActionId)
        if ($null -eq $action) { throw ($errorPrefix + '_CANDIDATE_ACTION_MISSING') }
        if ($SetExpected) {
            $set = $action.CreateSet()
            if ($null -ne $set -and [bool]$action.GetDefault($set)) {
                return [bool]$action.Execute($set)
            }
        }
        return [bool]$Hwp.HAction.Run($ActionId)
    }
    finally {
        Clear-ComObject -Value $set
        Clear-ComObject -Value $action
    }
}

if (-not [Environment]::Is64BitOperatingSystem -or [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw ($errorPrefix + '_REQUIRES_X86_STA')
}
if ((Test-Path -LiteralPath $TracePath -PathType Leaf) -or
    (Test-Path -LiteralPath $ProgressPath -PathType Leaf)) {
    throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS')
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
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
$routeByFeature = @{}
foreach ($route in @($overlay.routes)) { $routeByFeature[[string]$route.feature_id] = $route }
foreach ($featureId in $featureOrder) {
    if (-not $routeByFeature.ContainsKey($featureId) -or
        [string]$routeByFeature[$featureId].state -cne 'candidate_unverified' -or
        [string]$routeByFeature[$featureId].source_kind -cne 'action_table' -or
        [string]$routeByFeature[$featureId].modal_risk -cne 'none_expected') {
        throw ($errorPrefix + '_ROUTE_CONTRACT')
    }
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p08-object-shape-canary-private/v1'
    state = 'failed'
    target_build = $null
    target_executable_sha256 = [string]$server.sha256
    hwp_process_identity_verified = $false
    overlay_sha256 = $ExpectedOverlaySha256
    feature_order = $featureOrder
    setup_rectangle_count = 0
    completed_case_count = 0
    candidate_execute_count = 0
    effect_observed_count = 0
    undo_verified_count = 0
    hwp_file_open_count = 0
    document_save_count = 0
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    cases = @()
    quit_invoked = $false
    error_code = $null
}
$hwp = $null
$documents = $null
$document = $null
$window = $null
try {
    Add-Progress -Value ([ordered]@{
        event = 'starting'; completed = 0; total = $featureOrder.Count
    })
    $hwp = New-Object -ComObject $ProgId
    $trace.target_build = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($trace.target_build -cne $ExpectedBuild) { throw ($errorPrefix + '_TARGET_BUILD') }
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue)
    if ($processes.Count -ne 1 -or
        (Get-Sha256File -Path ([string]$processes[0].ExecutablePath)) -cne
            $ExpectedExecutableSha256) {
        throw ($errorPrefix + '_PROCESS_IDENTITY')
    }
    $trace.hwp_process_identity_verified = $true
    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $document = $documents.Add($false)
    if ($null -eq $document) { throw ($errorPrefix + '_DOCUMENT_ADD') }
    [void]$document.SetActive_XHwpDocument()
    New-Rectangle -Hwp $hwp -HorizontalOffset 2000 -VerticalOffset 2000
    New-Rectangle -Hwp $hwp -HorizontalOffset 5200 -VerticalOffset 4200
    $trace.setup_rectangle_count = 2

    foreach ($featureId in $featureOrder) {
        $route = $routeByFeature[$featureId]
        $result = [ordered]@{
            feature_id = $featureId
            capability_id = [string]$route.capability_id
            source_name = [string]$route.source_name
            context = 'two_rectangle_unsaved_blank_document_first_shape_selected'
            is_action_enable = $false
            execute_return = $false
            before_sha256 = $null
            after_sha256 = $null
            undo_sha256 = $null
            before_raw_sha256 = $null
            after_raw_sha256 = $null
            undo_raw_sha256 = $null
            before_normalization_count = 0
            after_normalization_count = 0
            undo_normalization_count = 0
            effect_observed = $false
            undo_verified = $false
            undo_raw_exact = $false
            context_setup_undo_verified = $null
            state = 'failed'
            error_code = $null
        }
        Add-Progress -Value ([ordered]@{
            event = 'case_start'; feature_id = $featureId
            completed = $trace.completed_case_count; total = $featureOrder.Count
        })
        try {
            Select-FirstShapeControl -Hwp $hwp
            $result.is_action_enable = [bool]$hwp.IsActionEnable([string]$route.source_name)
            $original = $null
            if ($featureId -ceq 'OBJ-038') {
                $original = Get-DocumentSnapshot -Hwp $hwp
                if (-not [bool]$hwp.HAction.Run('ShapeObjSendToBack')) {
                    throw ($errorPrefix + '_Z_ORDER_SETUP_FAILED')
                }
                Select-FirstShapeControl -Hwp $hwp
            }
            $before = Get-DocumentSnapshot -Hwp $hwp
            $result.before_sha256 = $before.sha256
            $result.before_raw_sha256 = $before.raw_sha256
            $result.before_normalization_count = $before.normalization_count
            $setExpected = $false
            $result.execute_return = Invoke-Candidate -Hwp $hwp `
                -ActionId ([string]$route.source_name) -SetExpected $setExpected
            $trace.candidate_execute_count += 1
            $after = Get-DocumentSnapshot -Hwp $hwp
            $result.after_sha256 = $after.sha256
            $result.after_raw_sha256 = $after.raw_sha256
            $result.after_normalization_count = $after.normalization_count
            $result.effect_observed = $after.sha256 -cne $before.sha256
            if ($result.effect_observed) {
                $trace.effect_observed_count += 1
                if (-not [bool]$hwp.HAction.Run('Undo')) {
                    throw ($errorPrefix + '_UNDO_RETURNED_FALSE')
                }
                $undo = Get-DocumentSnapshot -Hwp $hwp
                $result.undo_sha256 = $undo.sha256
                $result.undo_raw_sha256 = $undo.raw_sha256
                $result.undo_normalization_count = $undo.normalization_count
                $result.undo_verified = $undo.sha256 -ceq $before.sha256
                $result.undo_raw_exact = $undo.raw_sha256 -ceq $before.raw_sha256
                if ($result.undo_verified) { $trace.undo_verified_count += 1 }
                if ($featureId -ceq 'OBJ-026') {
                    $diagnosticRoot = Split-Path -Parent $TracePath
                    Write-NewUtf8File -Path (Join-Path $diagnosticRoot 'obj-026-before.hml') `
                        -Content $before.text
                    Write-NewUtf8File -Path (Join-Path $diagnosticRoot 'obj-026-after.hml') `
                        -Content $after.text
                    Write-NewUtf8File -Path (Join-Path $diagnosticRoot 'obj-026-undo.hml') `
                        -Content $undo.text
                }
            }
            if ($featureId -ceq 'OBJ-038' -and $null -ne $original) {
                if (-not [bool]$hwp.HAction.Run('Undo')) {
                    throw ($errorPrefix + '_Z_ORDER_SETUP_UNDO_FAILED')
                }
                $restored = Get-DocumentSnapshot -Hwp $hwp
                $result.context_setup_undo_verified =
                    $restored.sha256 -ceq $original.sha256
            }
            $result.state = if ($result.effect_observed -and $result.undo_verified -and
                ($featureId -cne 'OBJ-038' -or $result.context_setup_undo_verified)) {
                'pass'
            }
            else { 'no_qualified_effect' }
        }
        catch { $result.error_code = [string]$_.Exception.Message }
        $trace.cases += $result
        $trace.completed_case_count += 1
        Add-Progress -Value ([ordered]@{
            event = 'case_complete'; feature_id = $featureId; state = $result.state
            completed = $trace.completed_case_count; total = $featureOrder.Count
        })
    }
    [void]$document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $hwp.Quit()
    $trace.quit_invoked = $true
    if ($trace.completed_case_count -ne $featureOrder.Count -or
        @($trace.cases | Where-Object { $_.state -cne 'pass' }).Count -ne 0 -or
        $trace.candidate_execute_count -ne $featureOrder.Count -or
        $trace.effect_observed_count -ne $featureOrder.Count -or
        $trace.undo_verified_count -ne $featureOrder.Count -or
        $trace.hwp_file_open_count -ne 0 -or
        $trace.document_save_count -ne 0) {
        throw ($errorPrefix + '_CANARY_INCOMPLETE')
    }
    $trace.state = 'pass'
}
catch { $trace.error_code = [string]$_.Exception.Message }
finally {
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    Clear-ComObject -Value $document
    Clear-ComObject -Value $window
    Clear-ComObject -Value $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { $hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
$json = $trace | ConvertTo-Json -Depth 8
Write-NewUtf8File -Path $TracePath -Content $json
$json
if ($trace.state -cne 'pass') { exit 2 }
