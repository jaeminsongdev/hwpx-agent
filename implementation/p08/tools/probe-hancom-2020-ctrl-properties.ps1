[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value) } catch { }
    }
}

if ([Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'P08_CTRL_PROPERTIES_PROBE_REQUIRES_X86_STA'
}
if (@(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'P08_CTRL_PROPERTIES_PROBE_PREEXISTING_HWP'
}

$hwp = $null
$documents = $null
$document = $null
$action = $null
$set = $null
$layout = $null
$points = $null
$control = $null
$properties = $null
try {
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    [void]$document.SetActive_XHwpDocument()
    $action = $hwp.CreateAction('DrawObjCreatorRectangle')
    $set = $action.CreateSet()
    if (-not [bool]$action.GetDefault($set)) { throw 'P08_CTRL_PROPERTIES_PROBE_DEFAULT' }
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
    if (-not [bool]$action.Execute($set)) { throw 'P08_CTRL_PROPERTIES_PROBE_CREATE' }
    $control = $hwp.HeadCtrl
    while ($null -ne $control -and [string]$control.CtrlID -cne 'gso') {
        $next = $control.Next
        Clear-ComObject -Value $control
        $control = $next
    }
    if ($null -eq $control) { throw 'P08_CTRL_PROPERTIES_PROBE_CONTROL' }
    $before = [string]$hwp.GetTextFile('HWPML2X', '')
    $properties = $control.Properties
    $oldWidth = [int]$properties.Item('Width')
    $setReturn = [bool]$properties.SetItem('Width', $oldWidth + 1000)
    $control.Properties = $properties
    $after = [string]$hwp.GetTextFile('HWPML2X', '')
    [ordered]@{
        state = if ($before -cne $after) { 'pass' } else { 'no_effect' }
        width_before = $oldWidth
        set_item_return = $setReturn
        effect_observed = $before -cne $after
        before_sha256 = Get-Sha256String -Value $before
        after_sha256 = Get-Sha256String -Value $after
    } | ConvertTo-Json -Compress
}
finally {
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    if ($null -ne $hwp) { try { $hwp.Quit() } catch { } }
    foreach ($value in @($properties, $control, $points, $layout, $set, $action,
            $document, $documents, $hwp)) {
        Clear-ComObject -Value $value
    }
}
