[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 900)][int]$TimeoutSecondsPerCase = 600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$exactManifestSha256 = '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf'
$expectedTextSha256 = 'e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91'
$singleRunner = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-properties-target-readback.ps1'
)).Path

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function Read-BoundedJson {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$MaximumBytes,
        [Parameter(Mandatory)][string]$ErrorPrefix
    )

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt $MaximumBytes) {
        throw ($ErrorPrefix + '_NOT_BOUNDED_REGULAR_FILE')
    }
    try {
        if ($PSVersionTable.PSVersion.Major -ge 7) {
            return Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 |
                ConvertFrom-Json -DateKind String
        }
        return Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch { throw ($ErrorPrefix + '_JSON_INVALID') }
}

function Assert-ExactCases {
    param([Parameter(Mandatory)][object]$Manifest)

    $expected = @(
        @('table-018-equal-row-height-4x3', 'TABLE-018', 'table.equal_row_height', 'table-018-equal-row-height-4x3.hwpx'),
        @('table-019-equal-column-width-4x3', 'TABLE-019', 'table.equal_column_width', 'table-019-equal-column-width-4x3.hwpx'),
        @('table-050-row-min-height-4x3', 'TABLE-050', 'table.row_min_height', 'table-050-row-min-height-4x3.hwpx'),
        @('table-051-column-fixed-width-4x3', 'TABLE-051', 'table.column_fixed_width', 'table-051-column-fixed-width-4x3.hwpx'),
        @('table-052-autofit-content-4x3', 'TABLE-052', 'table.autofit_content', 'table-052-autofit-content-4x3.hwpx'),
        @('table-053-autofit-page-4x3', 'TABLE-053', 'table.autofit_page', 'table-053-autofit-page-4x3.hwpx'),
        @('table-034-position-4x3', 'TABLE-034', 'table.position', 'table-034-position-4x3.hwpx'),
        @('table-036-inline-floating-4x3', 'TABLE-036', 'table.inline_floating', 'table-036-inline-floating-4x3.hwpx'),
        @('table-037-wrap-4x3', 'TABLE-037', 'table.wrap', 'table-037-wrap-4x3.hwpx'),
        @('table-038-outer-margin-4x3', 'TABLE-038', 'table.outer_margin', 'table-038-outer-margin-4x3.hwpx')
    )
    $cases = @($Manifest.cases)
    if ($cases.Count -ne $expected.Count) {
        throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_SET_INVALID'
    }
    for ($index = 0; $index -lt $expected.Count; $index += 1) {
        $case = $cases[$index]
        $binding = $expected[$index]
        if ([string]$case.case_id -cne $binding[0] -or
            [string]$case.feature_id -cne $binding[1] -or
            [string]$case.capability_id -cne $binding[2] -or
            [string]$case.file -cne $binding[3] -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$' -or
            [long]$case.formula_count -ne 0 -or
            [string]$case.page_split -cne 'cell') {
            throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_BINDING_INVALID'
        }
    }
    return $cases
}

$manifestItem = Get-Item -LiteralPath $FixtureManifestPath -Force
$fixtureManifestFullPath = $manifestItem.FullName
$traceFullPath = [System.IO.Path]::GetFullPath($TracePath)
if ($ExpectedFixtureManifestSha256 -cne $exactManifestSha256) {
    throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_MANIFEST_IDENTITY_MISMATCH'
}
if ((Get-Sha256File -Path $fixtureManifestFullPath) -cne $ExpectedFixtureManifestSha256) {
    throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_MANIFEST_SHA256_MISMATCH'
}
if ([System.IO.File]::Exists($traceFullPath)) {
    throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_TRACE_ALREADY_EXISTS'
}
$traceParent = Split-Path -Parent $traceFullPath
if (-not [System.IO.Directory]::Exists($traceParent)) {
    throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_TRACE_PARENT_MISSING'
}
$manifest = Read-BoundedJson -Path $fixtureManifestFullPath -MaximumBytes 262144 `
    -ErrorPrefix 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_MANIFEST'
if ([string]$manifest.schema_version -cne
        'hwpx-agent.p06-09-table-layout-placement-target-fixture/v1' -or
    [string]$manifest.source_ancestor_sha256 -cne
        '0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252' -or
    -not ($manifest.actual_hangul_2020 -is [bool]) -or
    [bool]$manifest.actual_hangul_2020 -or
    [string]$manifest.render -cne 'not_run' -or
    [string]$manifest.automation -cne 'not_run' -or
    [string]$manifest.differential -cne 'not_run' -or
    -not [bool]$manifest.all_cases_content_preserved) {
    throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_MANIFEST_STATE_INVALID'
}
$cases = @(Assert-ExactCases -Manifest $manifest)
$fixtureDirectory = Split-Path -Parent $fixtureManifestFullPath

$prepared = @()
foreach ($case in $cases) {
    $inputPath = Join-Path $fixtureDirectory ([string]$case.file)
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension([string]$case.file)
    $outputPath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-readback.hwpx')
    $pdfPath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-render.pdf')
    $caseTracePath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-trace.json')
    if (-not [System.IO.File]::Exists($inputPath) -or
        (Get-Sha256File -Path $inputPath) -cne [string]$case.sha256) {
        throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_INPUT_IDENTITY_MISMATCH'
    }
    foreach ($output in @($outputPath, $pdfPath, $caseTracePath)) {
        if ([System.IO.File]::Exists($output)) {
            throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_OUTPUT_ALREADY_EXISTS'
        }
    }
    $prepared += [ordered]@{
        case = $case
        input_path = $inputPath
        output_path = $outputPath
        pdf_path = $pdfPath
        trace_path = $caseTracePath
    }
}

$results = @()
$target = $null
try {
    foreach ($entry in $prepared) {
        & $singleRunner `
            -InputPath ([string]$entry.input_path) `
            -ExpectedInputSha256 ([string]$entry.case.sha256) `
            -OutputPath ([string]$entry.output_path) `
            -TracePath ([string]$entry.trace_path) `
            -ExpectedTextSha256 $expectedTextSha256 `
            -RenderPdfPath ([string]$entry.pdf_path) `
            -ProgId $ProgId `
            -ExpectedBuild $ExpectedBuild `
            -ExpectedExecutableSha256 $ExpectedExecutableSha256 `
            -TimeoutSeconds $TimeoutSecondsPerCase | Out-Null
        if ($LASTEXITCODE -ne 0) {
            if ([System.IO.File]::Exists([string]$entry.trace_path)) {
                $failedCaseTrace = Read-BoundedJson `
                    -Path ([string]$entry.trace_path) `
                    -MaximumBytes 262144 `
                    -ErrorPrefix 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_TRACE'
                if ([string]$failedCaseTrace.error_code -match
                    '^TABLE_PROPERTIES_TARGET_READBACK_[A-Z0-9_]+$') {
                    throw ([string]$failedCaseTrace.error_code)
                }
            }
            throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_FAILED'
        }
        $caseTrace = Read-BoundedJson -Path ([string]$entry.trace_path) -MaximumBytes 262144 `
            -ErrorPrefix 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_TRACE'
        if ([string]$caseTrace.state -cne 'pass' -or
            [string]$caseTrace.input_sha256 -cne [string]$entry.case.sha256 -or
            -not [bool]$caseTrace.input_unchanged -or
            [string]$caseTrace.input_text_sha256 -cne $expectedTextSha256 -or
            [string]$caseTrace.output_text_sha256 -cne $expectedTextSha256 -or
            -not [bool]$caseTrace.render_pdf_signature_valid -or
            [long]$caseTrace.watchdog.remaining_hwp_process_count -ne 0) {
            throw 'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_CASE_TRACE_INVALID'
        }
        if ($null -eq $target) {
            $target = [ordered]@{
                prog_id = [string]$caseTrace.target.prog_id
                file_version = [string]$caseTrace.target.file_version
                executable_sha256 = [string]$caseTrace.target.executable_sha256
            }
        }
        $results += [ordered]@{
            case_id = [string]$entry.case.case_id
            feature_id = [string]$entry.case.feature_id
            input_path = [System.IO.Path]::GetFileName([string]$entry.input_path)
            input_sha256 = [string]$entry.case.sha256
            output_hwpx_path = [System.IO.Path]::GetFileName([string]$entry.output_path)
            output_hwpx_sha256 = Get-Sha256File -Path ([string]$entry.output_path)
            output_pdf_path = [System.IO.Path]::GetFileName([string]$entry.pdf_path)
            output_pdf_sha256 = Get-Sha256File -Path ([string]$entry.pdf_path)
            output_pdf_bytes = [long](Get-Item -LiteralPath ([string]$entry.pdf_path)).Length
            trace_path = [System.IO.Path]::GetFileName([string]$entry.trace_path)
            trace_sha256 = Get-Sha256File -Path ([string]$entry.trace_path)
            input_unchanged = $true
        }
    }
}
catch {
    $failure = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-layout-placement-target-batch-readback-failure/v1'
        state = 'failed'
        fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
        completed_case_count = $results.Count
        error_code = [string]$_.Exception.Message
        actual_hangul_2020 = $true
    }
    Write-NewUtf8File -Path $traceFullPath -Content ($failure | ConvertTo-Json -Depth 5)
    throw
}

$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-layout-placement-target-batch-readback/v1'
    state = 'pass'
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    target = $target
    cases = $results
    remaining_hwp_process_count = 0
    actual_hangul_2020 = $true
}
Write-NewUtf8File -Path $traceFullPath -Content ($receipt | ConvertTo-Json -Depth 8)
$receipt | ConvertTo-Json -Depth 8
