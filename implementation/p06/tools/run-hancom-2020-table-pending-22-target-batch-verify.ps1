[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^p06-09-table-pending-22-target-[0-9]{8}-[0-9]{2}$')]
    [string]$AttemptName,

    [ValidateRange(300, 7200)]
    [int]$TimeoutSeconds = 3600,

    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedManifestSha256 = [ordered]@{
    merge_split = '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
    layout_placement = '053b401cbcd2a21b3e845a29ffef28b9c1f633dfa825ac3f52d520cb5f6a3430'
    remaining = 'e4bb736d7182769546cefd50f2a30fd4bffba7293c589174d8aa0858f9e45c39'
}
$expectedAccessControlSha256 =
    '04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Resolve-BoundedRegularFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][long]$MaximumBytes
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith(
        $Boundary + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'TABLE_PENDING_22_VERIFY_FILE_OUTSIDE_BOUNDARY'
    }
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt $MaximumBytes) {
        throw 'TABLE_PENDING_22_VERIFY_FILE_INVALID'
    }
    return $item.FullName
}

$repoRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\..'
)).Path.TrimEnd('\')
$targetRoot = (Resolve-Path -LiteralPath (
    Join-Path $repoRoot 'fixtures\target-build'
)).Path.TrimEnd('\')
$readback = Resolve-BoundedRegularFile -Path (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-pending-22-target-batch-readback.ps1'
) -Boundary $repoRoot -MaximumBytes 1048576
$oracleSource = Resolve-BoundedRegularFile -Path (
    Join-Path $repoRoot 'crates\hwpx-package\examples\p06_09_table_pending_22_target_oracle.rs'
) -Boundary $repoRoot -MaximumBytes 1048576
$rendererSource = Resolve-BoundedRegularFile -Path (
    Join-Path $repoRoot 'tools\p06\render_table_pending_22_target_batch.py'
) -Boundary $repoRoot -MaximumBytes 1048576
$visualReviewFinalizerSource = Resolve-BoundedRegularFile -Path (
    Join-Path $repoRoot 'tools\p06\finalize_table_pending_22_visual_review.py'
) -Boundary $repoRoot -MaximumBytes 1048576
$cargoManifest = Resolve-BoundedRegularFile -Path (
    Join-Path $repoRoot 'Cargo.toml'
) -Boundary $repoRoot -MaximumBytes 1048576

$manifestPaths = [ordered]@{
    merge_split = Resolve-BoundedRegularFile -Path (
        Join-Path $targetRoot 'p06-09-table-merge-split-target-20260913-06\fixture-manifest.json'
    ) -Boundary $targetRoot -MaximumBytes 1048576
    layout_placement = Resolve-BoundedRegularFile -Path (
        Join-Path $targetRoot 'p06-09-table-layout-placement-target-20260913-04\fixture-manifest.json'
    ) -Boundary $targetRoot -MaximumBytes 1048576
    remaining = Resolve-BoundedRegularFile -Path (
        Join-Path $targetRoot 'p06-09-table-remaining-target-20260913-10\fixture-manifest.json'
    ) -Boundary $targetRoot -MaximumBytes 1048576
}
$accessControlPath = Resolve-BoundedRegularFile -Path (
    Join-Path $targetRoot 'p06-09-table-structure-target-20260913-05\table-012-insert-row-3x3.hancom-2020-readback.hwpx'
) -Boundary $targetRoot -MaximumBytes 8388608
foreach ($group in @('merge_split', 'layout_placement', 'remaining')) {
    if ((Get-Sha256File -Path ([string]$manifestPaths[$group])) -cne
        [string]$expectedManifestSha256[$group]) {
        throw 'TABLE_PENDING_22_VERIFY_MANIFEST_IDENTITY_MISMATCH'
    }
}
if ((Get-Sha256File -Path $accessControlPath) -cne
    $expectedAccessControlSha256) {
    throw 'TABLE_PENDING_22_VERIFY_ACCESS_CONTROL_IDENTITY_MISMATCH'
}

$cargo = Get-Command 'cargo.exe' -CommandType Application -ErrorAction Stop
$python = Get-Command 'python.exe' -CommandType Application -ErrorAction Stop
$pdfinfo = Get-Command 'pdfinfo.exe' -CommandType Application -ErrorAction Stop
$pdftoppm = Get-Command 'pdftoppm.exe' -CommandType Application -ErrorAction Stop
$runDirectory = Join-Path $targetRoot $AttemptName
if ([System.IO.Directory]::Exists($runDirectory) -or
    [System.IO.File]::Exists($runDirectory)) {
    throw 'TABLE_PENDING_22_VERIFY_ATTEMPT_ALREADY_EXISTS'
}

if ($ValidateConfigurationOnly) {
    [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-pending-22-target-batch-verify-config/v1'
        state = 'pass'
        attempt_name = $AttemptName
        case_count = 22
        access_control = [ordered]@{
            source = 'verified_hancom_saved_table_012_control'
            input_file = [System.IO.Path]::GetFileName($accessControlPath)
            input_sha256 = $expectedAccessControlSha256
        }
        manifest_sha256 = $expectedManifestSha256
        readback_sha256 = Get-Sha256File -Path $readback
        oracle_source_sha256 = Get-Sha256File -Path $oracleSource
        renderer_source_sha256 = Get-Sha256File -Path $rendererSource
        visual_review_finalizer_source_sha256 =
            Get-Sha256File -Path $visualReviewFinalizerSource
        cargo_manifest_sha256 = Get-Sha256File -Path $cargoManifest
        hwp_invoked = $false
        receipt_created = $false
        render_invoked = $false
    } | ConvertTo-Json -Depth 6
    exit 0
}

[void][System.IO.Directory]::CreateDirectory($runDirectory)
$runItem = Get-Item -LiteralPath $runDirectory -Force
if (($runItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $runItem.FullName -cne [System.IO.Path]::GetFullPath($runDirectory)) {
    throw 'TABLE_PENDING_22_VERIFY_ATTEMPT_DIRECTORY_INVALID'
}
$tracePath = Join-Path $runDirectory 'pending-22-trace.json'
$receiptPath = Join-Path $runDirectory 'pending-22-oracle-receipt.json'

$readbackArguments = @{
    MergeSplitManifestPath = [string]$manifestPaths.merge_split
    ExpectedMergeSplitManifestSha256 = [string]$expectedManifestSha256.merge_split
    LayoutPlacementManifestPath = [string]$manifestPaths.layout_placement
    ExpectedLayoutPlacementManifestSha256 = [string]$expectedManifestSha256.layout_placement
    RemainingManifestPath = [string]$manifestPaths.remaining
    ExpectedRemainingManifestSha256 = [string]$expectedManifestSha256.remaining
    AccessControlPath = $accessControlPath
    ExpectedAccessControlSha256 = $expectedAccessControlSha256
    TracePath = $tracePath
    TimeoutSeconds = $TimeoutSeconds
}
& $readback @readbackArguments | Out-Host
$readbackExit = $LASTEXITCODE
if ($readbackExit -ne 0) {
    Write-Error "TABLE_PENDING_22_VERIFY_READBACK_FAILED:$readbackExit"
    exit $readbackExit
}

$resolvedTrace = Resolve-BoundedRegularFile -Path $tracePath -Boundary $targetRoot -MaximumBytes 1048576
$traceSha256 = Get-Sha256File -Path $resolvedTrace
if ([System.IO.File]::Exists($receiptPath)) {
    throw 'TABLE_PENDING_22_VERIFY_ORACLE_RECEIPT_ALREADY_EXISTS'
}

$cargoArguments = @(
    'run', '--quiet', '--manifest-path', $cargoManifest,
    '-p', 'hwpx-package', '--example', 'p06_09_table_pending_22_target_oracle', '--',
    [string]$manifestPaths.merge_split,
    [string]$expectedManifestSha256.merge_split,
    [string]$manifestPaths.layout_placement,
    [string]$expectedManifestSha256.layout_placement,
    [string]$manifestPaths.remaining,
    [string]$expectedManifestSha256.remaining,
    $resolvedTrace,
    $traceSha256,
    $receiptPath
)
& $cargo.Source @cargoArguments | Out-Host
$oracleExit = $LASTEXITCODE
if ($oracleExit -ne 0) {
    Write-Error "TABLE_PENDING_22_VERIFY_ORACLE_FAILED:$oracleExit"
    exit $oracleExit
}

$resolvedReceipt = Resolve-BoundedRegularFile -Path $receiptPath -Boundary $targetRoot -MaximumBytes 1048576
$receiptSha256 = Get-Sha256File -Path $resolvedReceipt
$renderDirectory = Join-Path $runDirectory 'rendered'
$renderManifestPath = Join-Path $runDirectory 'pending-22-render-manifest.json'
$renderArguments = @(
    $rendererSource,
    '--trace', $resolvedTrace,
    '--trace-sha256', $traceSha256,
    '--oracle-receipt', $resolvedReceipt,
    '--oracle-receipt-sha256', $receiptSha256,
    '--pdfinfo', $pdfinfo.Source,
    '--pdftoppm', $pdftoppm.Source,
    '--output-directory', $renderDirectory,
    '--output-manifest', $renderManifestPath
)
& $python.Source @renderArguments | Out-Host
$renderExit = $LASTEXITCODE
if ($renderExit -ne 0) {
    Write-Error "TABLE_PENDING_22_VERIFY_RENDER_PREPARATION_FAILED:$renderExit"
    exit $renderExit
}
$resolvedRenderManifest = Resolve-BoundedRegularFile `
    -Path $renderManifestPath `
    -Boundary $targetRoot `
    -MaximumBytes 1048576
$renderManifest = Get-Content -LiteralPath $resolvedRenderManifest -Raw |
    ConvertFrom-Json -Depth 12
if ($renderManifest.schema_version -cne
        'hwpx-agent.p06-09-table-pending-22-render-candidates/v1' -or
    $renderManifest.state -cne 'rendered_not_reviewed' -or
    [int]$renderManifest.case_count -ne 22 -or
    @($renderManifest.cases).Count -ne 22 -or
    $renderManifest.visual_review.state -cne 'not_run' -or
    @($renderManifest.cases | Where-Object {
        $_.visual_review_state -cne 'not_run'
    }).Count -ne 0) {
    throw 'TABLE_PENDING_22_VERIFY_RENDER_MANIFEST_INVALID'
}
$renderManifestSha256 = Get-Sha256File -Path $resolvedRenderManifest
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-pending-22-target-batch-verify/v1'
    state = 'pass'
    attempt_name = $AttemptName
    case_count = 22
    access_control_input_sha256 = $expectedAccessControlSha256
    trace_file = [System.IO.Path]::GetFileName($resolvedTrace)
    trace_sha256 = $traceSha256
    oracle_receipt_file = [System.IO.Path]::GetFileName($resolvedReceipt)
    oracle_receipt_sha256 = $receiptSha256
    render_manifest_file = [System.IO.Path]::GetFileName($resolvedRenderManifest)
    render_manifest_sha256 = $renderManifestSha256
    rendered_png_count = @($renderManifest.cases).Count
    visual_review_state = [string]$renderManifest.visual_review.state
    hwp_session_count = 1
    user_allow_all_decision_count = 1
} | ConvertTo-Json -Depth 5
