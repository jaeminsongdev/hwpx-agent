[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'MASTER_REFERENCE_VERSION_UNREADABLE' }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'MASTER_REFERENCE_CLIENT_NOT_STA'
}

$output = [IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::GetExtension($output) -cne '.hwpx') {
    throw 'MASTER_REFERENCE_HWPX_EXTENSION_REQUIRED'
}
$parent = Split-Path -Parent $output
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw 'MASTER_REFERENCE_PARENT_MISSING'
}
if (Test-Path -LiteralPath $output) {
    throw 'MASTER_REFERENCE_REFUSES_OVERWRITE'
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$masterAction = $null
$masterSet = $null
$insertAction = $null
$insertSet = $null
try {
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'MASTER_REFERENCE_AUTOMATION_VERSION_MISMATCH'
    }
    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'MASTER_REFERENCE_DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    [void]$document.SetActive_XHwpDocument()

    $masterAction = $hwp.CreateAction('MasterPage')
    $masterSet = $masterAction.CreateSet()
    [void]$masterAction.GetDefault($masterSet)
    [void]$masterSet.SetItem('Type', 0)
    [void]$masterSet.SetItem('Duplicate', 0)
    [void]$masterSet.SetItem('Front', 0)
    [void]$masterSet.SetItem('ApplyTo', 0)
    if (-not [bool]$masterAction.Execute($masterSet)) {
        throw 'MASTER_REFERENCE_MASTER_PAGE_ACTION_FAILED'
    }

    $insertAction = $hwp.CreateAction('InsertText')
    $insertSet = $insertAction.CreateSet()
    [void]$insertAction.GetDefault($insertSet)
    [void]$insertSet.SetItem('Text', 'P05-08-MASTER-REFERENCE')
    if (-not [bool]$insertAction.Execute($insertSet)) {
        throw 'MASTER_REFERENCE_INSERT_TEXT_FAILED'
    }

    [void]$document.SaveAs($output, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $output -PathType Leaf)) {
        throw 'MASTER_REFERENCE_OUTPUT_MISSING'
    }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $output).Hash.ToLowerInvariant()
    Write-Output "HANCOM_2020_MASTER_REFERENCE_PASS sha256=$hash"
}
finally {
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
    }
    if ($null -ne $hwp) {
        try { [void]$hwp.Quit() } catch { }
    }
    foreach ($value in @(
        $insertSet, $insertAction, $masterSet, $masterAction,
        $window, $document, $documents, $hwp
    )) {
        Clear-ComObject -Value $value
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
