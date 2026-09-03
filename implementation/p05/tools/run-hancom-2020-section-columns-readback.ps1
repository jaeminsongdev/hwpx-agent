[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedTextSha256,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 900)][int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$runner = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'invoke-hancom-2020-bounded-readback.ps1'
)).Path
& $runner `
    -InputPath $InputPath `
    -ExpectedInputSha256 $ExpectedInputSha256 `
    -OutputPath $OutputPath `
    -TracePath $TracePath `
    -ExpectedTextSha256 $ExpectedTextSha256 `
    -TraceSchema 'hwpx-agent.p05-07-hancom-2020-section-columns-readback/v1' `
    -ErrorPrefix 'SECTION_COLUMNS_READBACK' `
    -ProgId $ProgId `
    -ExpectedBuild $ExpectedBuild `
    -ExpectedExecutableSha256 $ExpectedExecutableSha256 `
    -TimeoutSeconds $TimeoutSeconds
exit $LASTEXITCODE
