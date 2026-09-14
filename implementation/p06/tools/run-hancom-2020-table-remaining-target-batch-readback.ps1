[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(30, 900)][int]$TimeoutSecondsPerInvocation = 600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$exactManifestSha256 = 'e4bb736d7182769546cefd50f2a30fd4bffba7293c589174d8aa0858f9e45c39'
$probeSentinelSha256 = '0000000000000000000000000000000000000000000000000000000000000000'
$singleRunner = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-properties-target-readback.ps1'
)).Path
$hostPowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source

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

function Invoke-SingleReadback {
    param(
        [Parameter(Mandatory)][string]$InputPath,
        [Parameter(Mandatory)][string]$ExpectedInputSha256,
        [Parameter(Mandatory)][string]$OutputPath,
        [Parameter(Mandatory)][string]$TracePath,
        [Parameter(Mandatory)][string]$ExpectedTextSha256,
        [Parameter(Mandatory)][AllowEmptyString()][string]$RenderPdfPath
    )

    $arguments = @(
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', $singleRunner,
        '-InputPath', $InputPath,
        '-ExpectedInputSha256', $ExpectedInputSha256,
        '-OutputPath', $OutputPath,
        '-TracePath', $TracePath,
        '-ExpectedTextSha256', $ExpectedTextSha256,
        '-ProgId', $ProgId,
        '-ExpectedBuild', $ExpectedBuild,
        '-ExpectedExecutableSha256', $ExpectedExecutableSha256,
        '-TimeoutSeconds', [string]$TimeoutSecondsPerInvocation
    )
    if (-not [string]::IsNullOrWhiteSpace($RenderPdfPath)) {
        $arguments += @('-RenderPdfPath', $RenderPdfPath)
    }
    & $hostPowerShell @arguments | Out-Null
    return $LASTEXITCODE
}

function Assert-ExactCases {
    param([Parameter(Mandatory)][object]$Manifest)

    $expected = @(
        @('table-020-style', 'TABLE-020', 'table.table_style', 'table_style_hwpx', 'common', 'table-020-style.hwpx', 0),
        @('table-021-transpose', 'TABLE-021', 'table.transpose', 'table_transpose_hwpx', 'common', 'table-021-transpose.hwpx', 0),
        @('table-032-thousands-add', 'TABLE-032', 'table.thousands_add', 'table_thousands_hwpx', 'thousands_removed', 'table-032-thousands-add.hwpx', 1),
        @('table-033-thousands-remove', 'TABLE-033', 'table.thousands_remove', 'table_thousands_hwpx', 'thousands_baseline', 'table-033-thousands-remove.hwpx', 1),
        @('table-049-number-format', 'TABLE-049', 'table.number_format', 'table_number_format_hwpx', 'number_baseline', 'table-049-number-format.hwpx', 6),
        @('table-054-nested-table', 'TABLE-054', 'table.nested_table', 'table_nested_table_hwpx', 'common_envelope_with_inline_nested_template', 'table-054-nested-table.hwpx', 1),
        @('table-056-sort', 'TABLE-056', 'table.sort_cells', 'table_sort_hwpx', 'common', 'table-056-sort.hwpx', 0),
        @('table-057-auto-fill', 'TABLE-057', 'table.auto_fill', 'table_auto_fill_hwpx', 'common_envelope_with_inline_auto_fill_section', 'table-057-auto-fill.hwpx', 0),
        @('table-058-auto-fill-series', 'TABLE-058', 'table.auto_fill_series', 'table_auto_fill_hwpx', 'common_envelope_with_inline_auto_fill_section', 'table-058-auto-fill-series.hwpx', 0),
        @('table-060-absolute-reference', 'TABLE-060', 'table.formula_absolute_ref', 'table_absolute_reference_hwpx', 'common_envelope_with_inline_absolute_formula_section', 'table-060-absolute-reference.hwpx', 2)
    )
    $cases = @($Manifest.cases)
    if ($cases.Count -ne $expected.Count) {
        throw 'TABLE_REMAINING_TARGET_BATCH_CASE_SET_INVALID'
    }
    for ($index = 0; $index -lt $expected.Count; $index += 1) {
        $case = $cases[$index]
        $binding = $expected[$index]
        if ([string]$case.case_id -cne $binding[0] -or
            [string]$case.feature_id -cne $binding[1] -or
            [string]$case.capability_id -cne $binding[2] -or
            [string]$case.adapter -cne $binding[3] -or
            [string]$case.source_role -cne $binding[4] -or
            [string]$case.file -cne $binding[5] -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_header_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_section_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.semantic_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [long]$case.formula_count -ne [long]$binding[6] -or
            [long]$case.table_count -lt 1 -or [long]$case.table_count -gt 2) {
            throw 'TABLE_REMAINING_TARGET_BATCH_CASE_BINDING_INVALID'
        }
    }
    return $cases
}

$manifestItem = Get-Item -LiteralPath $FixtureManifestPath -Force
$fixtureManifestFullPath = $manifestItem.FullName
$traceFullPath = [System.IO.Path]::GetFullPath($TracePath)
if ($ExpectedFixtureManifestSha256 -cne $exactManifestSha256) {
    throw 'TABLE_REMAINING_TARGET_BATCH_MANIFEST_IDENTITY_MISMATCH'
}
if ((Get-Sha256File -Path $fixtureManifestFullPath) -cne $ExpectedFixtureManifestSha256) {
    throw 'TABLE_REMAINING_TARGET_BATCH_MANIFEST_SHA256_MISMATCH'
}
if ([System.IO.File]::Exists($traceFullPath)) {
    throw 'TABLE_REMAINING_TARGET_BATCH_TRACE_ALREADY_EXISTS'
}
$traceParent = Split-Path -Parent $traceFullPath
if (-not [System.IO.Directory]::Exists($traceParent)) {
    throw 'TABLE_REMAINING_TARGET_BATCH_TRACE_PARENT_MISSING'
}
$manifest = Read-BoundedJson -Path $fixtureManifestFullPath -MaximumBytes 262144 `
    -ErrorPrefix 'TABLE_REMAINING_TARGET_BATCH_MANIFEST'
if ([string]$manifest.schema_version -cne
        'hwpx-agent.p06-09-table-remaining-target-fixture/v1' -or
    -not ($manifest.actual_hangul_2020 -is [bool]) -or
    [bool]$manifest.actual_hangul_2020 -or
    [string]$manifest.render -cne 'not_run' -or
    [string]$manifest.automation -cne 'not_run' -or
    [string]$manifest.differential -cne 'not_run' -or
    @($manifest.source_artifacts).Count -ne 7) {
    throw 'TABLE_REMAINING_TARGET_BATCH_MANIFEST_STATE_INVALID'
}
$cases = @(Assert-ExactCases -Manifest $manifest)
$fixtureDirectory = Split-Path -Parent $fixtureManifestFullPath

$prepared = @()
foreach ($case in $cases) {
    $inputPath = Join-Path $fixtureDirectory ([string]$case.file)
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension([string]$case.file)
    $probeOutputPath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-text-probe-unused.hwpx')
    $probeTracePath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-text-probe-trace.json')
    $probeProgressPath = $probeTracePath + '.progress.jsonl'
    $outputPath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-readback.hwpx')
    $pdfPath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-render.pdf')
    $caseTracePath = Join-Path $fixtureDirectory ($baseName + '.hancom-2020-trace.json')
    $caseProgressPath = $caseTracePath + '.progress.jsonl'
    if (-not [System.IO.File]::Exists($inputPath) -or
        (Get-Sha256File -Path $inputPath) -cne [string]$case.sha256) {
        throw 'TABLE_REMAINING_TARGET_BATCH_INPUT_IDENTITY_MISMATCH'
    }
    foreach ($output in @(
        $probeOutputPath, $probeTracePath, $probeProgressPath,
        $outputPath, $pdfPath, $caseTracePath, $caseProgressPath
    )) {
        if ([System.IO.File]::Exists($output)) {
            throw 'TABLE_REMAINING_TARGET_BATCH_OUTPUT_ALREADY_EXISTS'
        }
    }
    $prepared += [ordered]@{
        case = $case
        input_path = $inputPath
        probe_output_path = $probeOutputPath
        probe_trace_path = $probeTracePath
        probe_progress_path = $probeProgressPath
        output_path = $outputPath
        pdf_path = $pdfPath
        trace_path = $caseTracePath
        progress_path = $caseProgressPath
    }
}

$results = @()
$probeResults = @()
$failures = @()
$target = $null
try {
    foreach ($entry in $prepared) {
        $probeExitCode = Invoke-SingleReadback `
            -InputPath ([string]$entry.input_path) `
            -ExpectedInputSha256 ([string]$entry.case.sha256) `
            -OutputPath ([string]$entry.probe_output_path) `
            -TracePath ([string]$entry.probe_trace_path) `
            -ExpectedTextSha256 $probeSentinelSha256 `
            -RenderPdfPath ''
        $probeTrace = Read-BoundedJson -Path ([string]$entry.probe_trace_path) `
            -MaximumBytes 262144 -ErrorPrefix 'TABLE_REMAINING_TARGET_BATCH_PROBE_TRACE'
        $probeTargetProperty = $probeTrace.PSObject.Properties['target']
        if ($null -eq $target -and $null -ne $probeTargetProperty -and
            $null -ne $probeTargetProperty.Value) {
            $probeTarget = $probeTargetProperty.Value
            $target = [ordered]@{
                prog_id = [string]$probeTarget.prog_id
                file_version = [string]$probeTarget.file_version
                executable_sha256 = [string]$probeTarget.executable_sha256
            }
        }
        if ($probeExitCode -ne 2 -or
            [string]$probeTrace.state -cne 'failed' -or
            [string]$probeTrace.error_code -cne
                'TABLE_PROPERTIES_TARGET_READBACK_INPUT_TEXT_MISMATCH' -or
            [string]$probeTrace.failed_phase -cne 'read_input' -or
            [string]$probeTrace.input_sha256 -cne [string]$entry.case.sha256 -or
            [string]$probeTrace.input_text_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$probeTrace.input_text_sha256 -ceq $probeSentinelSha256 -or
            -not [bool]$probeTrace.input_unchanged -or
            [bool]$probeTrace.output_saved -or
            [bool]$probeTrace.watchdog.timed_out -or
            [long]$probeTrace.watchdog.remaining_hwp_process_count -ne 0 -or
            [System.IO.File]::Exists([string]$entry.probe_output_path)) {
            $probeErrorCode = 'TABLE_REMAINING_TARGET_BATCH_TEXT_PROBE_INVALID'
            if ([string]$probeTrace.error_code -match '^TABLE_PROPERTIES_TARGET_READBACK_[A-Z0-9_]+$') {
                $probeErrorCode = [string]$probeTrace.error_code
            }
            $failures += [ordered]@{
                case_id = [string]$entry.case.case_id
                feature_id = [string]$entry.case.feature_id
                stage = 'text_probe'
                child_exit_code = $probeExitCode
                error_code = $probeErrorCode
                failed_phase = [string]$probeTrace.failed_phase
                input_sha256 = [string]$entry.case.sha256
                input_unchanged = [bool]$probeTrace.input_unchanged
                output_absent = -not [System.IO.File]::Exists([string]$entry.probe_output_path)
                trace_path = [System.IO.Path]::GetFileName([string]$entry.probe_trace_path)
                trace_sha256 = Get-Sha256File -Path ([string]$entry.probe_trace_path)
                progress_path = [System.IO.Path]::GetFileName([string]$entry.probe_progress_path)
                progress_sha256 = Get-Sha256File -Path ([string]$entry.probe_progress_path)
                remaining_hwp_process_count = [long]$probeTrace.watchdog.remaining_hwp_process_count
            }
            continue
        }
        $expectedTextSha256 = [string]$probeTrace.input_text_sha256
        $probeResults += [ordered]@{
            case_id = [string]$entry.case.case_id
            input_sha256 = [string]$entry.case.sha256
            input_text_sha256 = $expectedTextSha256
            trace_path = [System.IO.Path]::GetFileName([string]$entry.probe_trace_path)
            trace_sha256 = Get-Sha256File -Path ([string]$entry.probe_trace_path)
            progress_path = [System.IO.Path]::GetFileName([string]$entry.probe_progress_path)
            progress_sha256 = Get-Sha256File -Path ([string]$entry.probe_progress_path)
        }

        $caseExitCode = Invoke-SingleReadback `
            -InputPath ([string]$entry.input_path) `
            -ExpectedInputSha256 ([string]$entry.case.sha256) `
            -OutputPath ([string]$entry.output_path) `
            -TracePath ([string]$entry.trace_path) `
            -ExpectedTextSha256 $expectedTextSha256 `
            -RenderPdfPath ([string]$entry.pdf_path)
        $caseTrace = Read-BoundedJson -Path ([string]$entry.trace_path) -MaximumBytes 262144 `
            -ErrorPrefix 'TABLE_REMAINING_TARGET_BATCH_CASE_TRACE'
        $caseTargetProperty = $caseTrace.PSObject.Properties['target']
        if ($null -eq $target -and $null -ne $caseTargetProperty -and
            $null -ne $caseTargetProperty.Value) {
            $caseTarget = $caseTargetProperty.Value
            $target = [ordered]@{
                prog_id = [string]$caseTarget.prog_id
                file_version = [string]$caseTarget.file_version
                executable_sha256 = [string]$caseTarget.executable_sha256
            }
        }
        if ($caseExitCode -ne 0 -or
            [string]$caseTrace.state -cne 'pass' -or
            [string]$caseTrace.input_sha256 -cne [string]$entry.case.sha256 -or
            -not [bool]$caseTrace.input_unchanged -or
            [string]$caseTrace.input_text_sha256 -cne $expectedTextSha256 -or
            [string]$caseTrace.output_text_sha256 -cne $expectedTextSha256 -or
            -not [bool]$caseTrace.render_pdf_signature_valid -or
            [long]$caseTrace.watchdog.remaining_hwp_process_count -ne 0) {
            $caseErrorCode = 'TABLE_REMAINING_TARGET_BATCH_CASE_TRACE_INVALID'
            if ([string]$caseTrace.error_code -match '^TABLE_PROPERTIES_TARGET_READBACK_[A-Z0-9_]+$') {
                $caseErrorCode = [string]$caseTrace.error_code
            }
            $failures += [ordered]@{
                case_id = [string]$entry.case.case_id
                feature_id = [string]$entry.case.feature_id
                stage = 'lifecycle'
                child_exit_code = $caseExitCode
                error_code = $caseErrorCode
                failed_phase = [string]$caseTrace.failed_phase
                input_sha256 = [string]$entry.case.sha256
                input_unchanged = [bool]$caseTrace.input_unchanged
                output_hwpx_present = [System.IO.File]::Exists([string]$entry.output_path)
                output_pdf_present = [System.IO.File]::Exists([string]$entry.pdf_path)
                trace_path = [System.IO.Path]::GetFileName([string]$entry.trace_path)
                trace_sha256 = Get-Sha256File -Path ([string]$entry.trace_path)
                progress_path = [System.IO.Path]::GetFileName([string]$entry.progress_path)
                progress_sha256 = Get-Sha256File -Path ([string]$entry.progress_path)
                remaining_hwp_process_count = [long]$caseTrace.watchdog.remaining_hwp_process_count
            }
            continue
        }
        $results += [ordered]@{
            case_id = [string]$entry.case.case_id
            feature_id = [string]$entry.case.feature_id
            input_path = [System.IO.Path]::GetFileName([string]$entry.input_path)
            input_sha256 = [string]$entry.case.sha256
            input_text_sha256 = $expectedTextSha256
            output_hwpx_path = [System.IO.Path]::GetFileName([string]$entry.output_path)
            output_hwpx_sha256 = Get-Sha256File -Path ([string]$entry.output_path)
            output_pdf_path = [System.IO.Path]::GetFileName([string]$entry.pdf_path)
            output_pdf_sha256 = Get-Sha256File -Path ([string]$entry.pdf_path)
            output_pdf_bytes = [long](Get-Item -LiteralPath ([string]$entry.pdf_path)).Length
            trace_path = [System.IO.Path]::GetFileName([string]$entry.trace_path)
            trace_sha256 = Get-Sha256File -Path ([string]$entry.trace_path)
            progress_path = [System.IO.Path]::GetFileName([string]$entry.progress_path)
            progress_sha256 = Get-Sha256File -Path ([string]$entry.progress_path)
            input_unchanged = $true
        }
    }
}
catch {
    $failure = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-remaining-target-batch-readback-failure/v1'
        state = 'failed'
        fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
        target = $target
        attempted_case_count = $probeResults.Count + $results.Count + $failures.Count
        probed_case_count = $probeResults.Count
        completed_case_count = $results.Count
        failed_case_count = $failures.Count
        error_code = [string]$_.Exception.Message
        failures = $failures
        text_probes = $probeResults
        cases = $results
        actual_hangul_2020 = $true
    }
    Write-NewUtf8File -Path $traceFullPath -Content ($failure | ConvertTo-Json -Depth 8)
    throw
}

if ($failures.Count -gt 0) {
    [long]$remainingProcessCount = 0
    foreach ($caseFailure in $failures) {
        $remainingProcessCount += [long]$caseFailure['remaining_hwp_process_count']
    }
    $failure = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-remaining-target-batch-readback-failure/v1'
        state = 'failed'
        fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
        target = $target
        attempted_case_count = $prepared.Count
        probed_case_count = $probeResults.Count
        completed_case_count = $results.Count
        failed_case_count = $failures.Count
        failures = $failures
        text_probes = $probeResults
        cases = $results
        remaining_hwp_process_count = $remainingProcessCount
        actual_hangul_2020 = $true
    }
    Write-NewUtf8File -Path $traceFullPath -Content ($failure | ConvertTo-Json -Depth 8)
    $failure | ConvertTo-Json -Depth 8
    exit 2
}

$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-remaining-target-batch-readback/v1'
    state = 'pass'
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    target = $target
    text_probes = $probeResults
    cases = $results
    remaining_hwp_process_count = 0
    actual_hangul_2020 = $true
}
Write-NewUtf8File -Path $traceFullPath -Content ($receipt | ConvertTo-Json -Depth 8)
$receipt | ConvertTo-Json -Depth 8
