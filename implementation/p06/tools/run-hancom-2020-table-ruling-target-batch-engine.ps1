[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$exactFixtureManifestSha256 = '8296cf4057c1cb6b27c800c15694866008c31cfa290cd6863321179c1efda543'
if ($ExpectedFixtureManifestSha256 -cne $exactFixtureManifestSha256) {
    throw 'TABLE_RULING_BATCH_MANIFEST_IDENTITY_MISMATCH'
}

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
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

function ConvertTo-CanonicalText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC).TrimEnd([char]"`n")
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'TABLE_RULING_BATCH_VERSION_PARSE_FAILED' }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)

    $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $progIdKey = $null
    $clsidSubKey = $null
    $clsidKey = $null
    $serverKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($RequestedProgId)
        if ($null -eq $progIdKey) { throw 'TABLE_RULING_BATCH_PROGID_NOT_REGISTERED' }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) { throw 'TABLE_RULING_BATCH_CLSID_MISSING' }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $serverKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $serverKey) { throw 'TABLE_RULING_BATCH_LOCALSERVER32_MISSING' }
        $command = [string]$serverKey.GetValue('')
    }
    finally {
        foreach ($key in @($serverKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'TABLE_RULING_BATCH_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path -Force
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Assert-ExactProperties {
    param(
        [Parameter(Mandatory)][object]$Value,
        [Parameter(Mandatory)][string[]]$Expected,
        [Parameter(Mandatory)][string]$ErrorCode
    )

    $observed = @($Value.PSObject.Properties.Name)
    if ($observed.Count -ne $Expected.Count) { throw $ErrorCode }
    foreach ($name in $observed) {
        if ($Expected -cnotcontains $name) { throw $ErrorCode }
    }
}

function Read-ExactFixtureManifest {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 131072) {
        throw 'TABLE_RULING_BATCH_MANIFEST_NOT_BOUNDED_REGULAR_FILE'
    }
    if ((Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_RULING_BATCH_MANIFEST_SHA256_MISMATCH'
    }
    try {
        $manifest = if ($PSVersionTable.PSVersion.Major -ge 7) {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
        }
        else {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    }
    catch { throw 'TABLE_RULING_BATCH_MANIFEST_JSON_INVALID' }
    Assert-ExactProperties -Value $manifest -Expected @(
        'schema_version', 'source_ancestor_sha256', 'cases', 'actual_hangul_2020',
        'render', 'automation', 'differential'
    ) -ErrorCode 'TABLE_RULING_BATCH_MANIFEST_SHAPE_INVALID'
    if ([string]$manifest.schema_version -cne 'hwpx-agent.p06-09-table-ruling-target-fixture/v1' -or
        [string]$manifest.source_ancestor_sha256 -cne
            '6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5' -or
        -not ($manifest.actual_hangul_2020 -is [bool]) -or [bool]$manifest.actual_hangul_2020 -or
        [string]$manifest.render -cne 'not_run' -or
        [string]$manifest.automation -cne 'not_run' -or
        [string]$manifest.differential -cne 'not_run') {
        throw 'TABLE_RULING_BATCH_MANIFEST_STATE_INVALID'
    }
    $expectedCases = @(
        @('table-002-draw-outer', 'TABLE-002', 'table.draw', 'table-002-draw-outer.hwpx', 1, 1, 1, 0, 0, 1, 'draw-outer-table'),
        @('table-002-draw-topology', 'TABLE-002', 'table.draw', 'table-002-draw-topology.hwpx', 3, 6, 16, 8, 0, 4, 'draw-topology-table'),
        @('table-002-draw-diagonals-formula', 'TABLE-002', 'table.draw', 'table-002-draw-diagonals-formula.hwpx', 2, 4, 8, 7, 1, 2, 'draw-diagonal-table'),
        @('table-003-eraser-structural-merge', 'TABLE-003', 'table.eraser', 'table-003-eraser-structural-merge.hwpx', 2, 4, 6, 8, 0, 1, 'eraser-merge-table'),
        @('table-003-eraser-transparent-formula', 'TABLE-003', 'table.eraser', 'table-003-eraser-transparent-formula.hwpx', 2, 4, 8, 7, 1, 1, 'eraser-transparent-table')
    )
    $expectedOperationNames = @(
        @('draw_outer_rectangle'),
        @('draw_full_row', 'draw_full_column', 'draw_local_cell_split', 'draw_existing_boundary_style'),
        @('draw_slash_on_formula_cell', 'draw_back_slash_on_formula_cell'),
        @('erase_shared_column_edge'),
        @('erase_outer_edge_on_formula_cell')
    )
    $cases = @($manifest.cases)
    if ($cases.Count -ne $expectedCases.Count) {
        throw 'TABLE_RULING_BATCH_CASE_SET_INVALID'
    }
    $caseProperties = @(
        'case_id', 'feature_id', 'capability_id', 'file', 'sha256',
        'selected_table_ordinal', 'source_section_sha256', 'target_header_sha256',
        'target_section_sha256', 'target_state_sha256', 'target_grid_sha256',
        'target_rows', 'target_columns', 'target_master_cells', 'payload_block_count',
        'formula_count', 'binding', 'operations'
    )
    $bindingProperties = @(
        'table_id', 'row_boundaries_hwpunit', 'column_boundaries_hwpunit', 'cells'
    )
    $bindingCellProperties = @('master_cell_id', 'payload_block_ids')
    $operationProperties = @(
        'name', 'capability_id', 'request_sha256', 'plan_sha256',
        'source_state_sha256', 'source_grid_sha256', 'target_state_sha256',
        'target_grid_sha256', 'added_border_fill_count'
    )
    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        Assert-ExactProperties -Value $case -Expected $caseProperties `
            -ErrorCode 'TABLE_RULING_BATCH_CASE_SHAPE_INVALID'
        $expected = $expectedCases[$index]
        $integerValues = @(
            $case.selected_table_ordinal, $case.target_rows, $case.target_columns,
            $case.target_master_cells, $case.payload_block_count, $case.formula_count
        )
        if ([string]$case.case_id -cne $expected[0] -or
            [string]$case.feature_id -cne $expected[1] -or
            [string]$case.capability_id -cne $expected[2] -or
            [string]$case.file -cne $expected[3] -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.source_section_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_header_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_section_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_state_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.target_grid_sha256 -notmatch '^[0-9a-f]{64}$' -or
            @($integerValues | Where-Object { -not ($_ -is [int] -or $_ -is [long]) }).Count -ne 0 -or
            [long]$case.selected_table_ordinal -ne $(if ($index -eq 0) { 1 } else { 0 }) -or
            [long]$case.target_rows -ne [long]$expected[4] -or
            [long]$case.target_columns -ne [long]$expected[5] -or
            [long]$case.target_master_cells -ne [long]$expected[6] -or
            [long]$case.payload_block_count -ne [long]$expected[7] -or
            [long]$case.formula_count -ne [long]$expected[8]) {
            throw 'TABLE_RULING_BATCH_CASE_BINDING_INVALID'
        }
        Assert-ExactProperties -Value $case.binding -Expected $bindingProperties `
            -ErrorCode 'TABLE_RULING_BATCH_BINDING_SHAPE_INVALID'
        $expectedRowBoundaries = if ($index -eq 0) { @(0, 8000) }
        elseif ($index -eq 1) { @(0, 2000, 4000, 8000) }
        else { @(0, 4000, 8000) }
        $expectedColumnBoundaries = if ($index -eq 0) { @(0, 41952) }
        elseif ($index -eq 1) { @(0, 5244, 10488, 15732, 20976, 31464, 41952) }
        else { @(0, 10488, 20976, 31464, 41952) }
        $rowBoundaries = @($case.binding.row_boundaries_hwpunit)
        $columnBoundaries = @($case.binding.column_boundaries_hwpunit)
        $bindingCells = @($case.binding.cells)
        if ([string]$case.binding.table_id -cne [string]$expected[10] -or
            $rowBoundaries.Count -ne $expectedRowBoundaries.Count -or
            $columnBoundaries.Count -ne $expectedColumnBoundaries.Count -or
            $bindingCells.Count -ne [long]$case.target_master_cells) {
            throw 'TABLE_RULING_BATCH_BINDING_CARDINALITY_INVALID'
        }
        for ($boundaryIndex = 0; $boundaryIndex -lt $rowBoundaries.Count; $boundaryIndex += 1) {
            if (-not ($rowBoundaries[$boundaryIndex] -is [int] -or
                $rowBoundaries[$boundaryIndex] -is [long]) -or
                [long]$rowBoundaries[$boundaryIndex] -ne [long]$expectedRowBoundaries[$boundaryIndex]) {
                throw 'TABLE_RULING_BATCH_ROW_BOUNDARIES_INVALID'
            }
        }
        for ($boundaryIndex = 0; $boundaryIndex -lt $columnBoundaries.Count; $boundaryIndex += 1) {
            if (-not ($columnBoundaries[$boundaryIndex] -is [int] -or
                $columnBoundaries[$boundaryIndex] -is [long]) -or
                [long]$columnBoundaries[$boundaryIndex] -ne
                    [long]$expectedColumnBoundaries[$boundaryIndex]) {
                throw 'TABLE_RULING_BATCH_COLUMN_BOUNDARIES_INVALID'
            }
        }
        $seenLogicalIds = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::Ordinal
        )
        [void]$seenLogicalIds.Add([string]$case.binding.table_id)
        $boundPayloadCount = 0
        foreach ($bindingCell in $bindingCells) {
            Assert-ExactProperties -Value $bindingCell -Expected $bindingCellProperties `
                -ErrorCode 'TABLE_RULING_BATCH_BINDING_CELL_SHAPE_INVALID'
            if ([string]$bindingCell.master_cell_id -notmatch '^[a-z][a-z0-9-]{0,127}$' -or
                -not $seenLogicalIds.Add([string]$bindingCell.master_cell_id)) {
                throw 'TABLE_RULING_BATCH_BINDING_CELL_ID_INVALID'
            }
            foreach ($payloadId in @($bindingCell.payload_block_ids)) {
                if ([string]$payloadId -notmatch '^[a-z][a-z0-9-]{0,127}$' -or
                    -not $seenLogicalIds.Add([string]$payloadId)) {
                    throw 'TABLE_RULING_BATCH_BINDING_PAYLOAD_ID_INVALID'
                }
                $boundPayloadCount += 1
            }
        }
        if ($boundPayloadCount -ne [long]$case.payload_block_count) {
            throw 'TABLE_RULING_BATCH_BINDING_PAYLOAD_COUNT_INVALID'
        }
        $operations = @($case.operations)
        if ($operations.Count -ne [long]$expected[9]) {
            throw 'TABLE_RULING_BATCH_OPERATION_SET_INVALID'
        }
        $previousTargetState = $null
        $previousTargetGrid = $null
        for ($operationIndex = 0; $operationIndex -lt $operations.Count; $operationIndex += 1) {
            $operation = $operations[$operationIndex]
            Assert-ExactProperties -Value $operation -Expected $operationProperties `
                -ErrorCode 'TABLE_RULING_BATCH_OPERATION_SHAPE_INVALID'
            $sourceMustBeNull = $index -eq 0 -and $operationIndex -eq 0
            if ([string]$operation.name -cne $expectedOperationNames[$index][$operationIndex] -or
                [string]$operation.capability_id -cne [string]$case.capability_id -or
                [string]$operation.request_sha256 -notmatch '^[0-9a-f]{64}$' -or
                [string]$operation.plan_sha256 -notmatch '^[0-9a-f]{64}$' -or
                [string]$operation.target_state_sha256 -notmatch '^[0-9a-f]{64}$' -or
                [string]$operation.target_grid_sha256 -notmatch '^[0-9a-f]{64}$' -or
                -not ($operation.added_border_fill_count -is [int] -or
                    $operation.added_border_fill_count -is [long]) -or
                [long]$operation.added_border_fill_count -lt 0 -or
                ($sourceMustBeNull -and ($null -ne $operation.source_state_sha256 -or
                    $null -ne $operation.source_grid_sha256)) -or
                (-not $sourceMustBeNull -and (
                    [string]$operation.source_state_sha256 -notmatch '^[0-9a-f]{64}$' -or
                    [string]$operation.source_grid_sha256 -notmatch '^[0-9a-f]{64}$'))) {
                throw 'TABLE_RULING_BATCH_OPERATION_BINDING_INVALID'
            }
            if ($operationIndex -gt 0 -and (
                [string]$operation.source_state_sha256 -cne [string]$previousTargetState -or
                [string]$operation.source_grid_sha256 -cne [string]$previousTargetGrid)) {
                throw 'TABLE_RULING_BATCH_OPERATION_CHAIN_INVALID'
            }
            $previousTargetState = [string]$operation.target_state_sha256
            $previousTargetGrid = [string]$operation.target_grid_sha256
        }
        if ([string]$previousTargetState -cne [string]$case.target_state_sha256 -or
            [string]$previousTargetGrid -cne [string]$case.target_grid_sha256) {
            throw 'TABLE_RULING_BATCH_OPERATION_TARGET_INVALID'
        }
    }
    return [ordered]@{ item = $item; value = $manifest; expected_cases = $expectedCases }
}

function Get-CasePaths {
    param(
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][object]$Case
    )

    $input = [System.IO.Path]::GetFullPath((Join-Path $Boundary ([string]$Case.file)))
    $stem = [System.IO.Path]::GetFileNameWithoutExtension([string]$Case.file)
    return [ordered]@{
        input = $input
        output = [System.IO.Path]::GetFullPath((Join-Path $Boundary ($stem + '.hancom-2020-readback.hwpx')))
        pdf = [System.IO.Path]::GetFullPath((Join-Path $Boundary ($stem + '.hancom-2020-render.pdf')))
    }
}

function Assert-CaseFiles {
    param(
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][object[]]$Cases
    )

    $paths = @()
    foreach ($case in $Cases) {
        $casePaths = Get-CasePaths -Boundary $Boundary -Case $case
        foreach ($candidate in @($casePaths.input, $casePaths.output, $casePaths.pdf)) {
            if (-not $candidate.StartsWith($Boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
                throw 'TABLE_RULING_BATCH_PATH_OUTSIDE_FIXTURE_BOUNDARY'
            }
        }
        $inputItem = Get-Item -LiteralPath $casePaths.input -Force
        if ($inputItem.PSIsContainer -or
            ($inputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $inputItem.Length -le 0 -or $inputItem.Length -gt 8388608 -or
            [System.IO.Path]::GetExtension($casePaths.input) -cne '.hwpx' -or
            (Get-Sha256File -Path $casePaths.input) -cne [string]$case.sha256) {
            throw 'TABLE_RULING_BATCH_INPUT_INVALID'
        }
        foreach ($candidate in @($casePaths.output, $casePaths.pdf)) {
            if (Test-Path -LiteralPath $candidate) {
                throw 'TABLE_RULING_BATCH_OUTPUT_ALREADY_EXISTS'
            }
        }
        $paths += ,$casePaths
    }
    return $paths
}

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null,
        [ValidateRange(0, 5)][int]$CaseIndex = 0,
        [AllowNull()][string]$CaseId = $null,
        [AllowNull()][string]$FeatureId = $null
    )

    $script:progressSequence += 1
    # Windows PowerShell 5.1 coerces a null value bound to [string] into an empty string.
    # Normalize the optional case fields back to JSON null so the parent can distinguish
    # process-level events from case-bound events without weakening its exact journal schema.
    $normalizedCaseId = if ([string]::IsNullOrEmpty($CaseId)) { $null } else { [string]$CaseId }
    $normalizedFeatureId = if ([string]::IsNullOrEmpty($FeatureId)) { $null } else { [string]$FeatureId }
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-ruling-batch-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        case_index = $CaseIndex
        case_id = $normalizedCaseId
        feature_id = $normalizedFeatureId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
    }
    $line = $event | ConvertTo-Json -Compress
    if ($script:progressSequence -eq 1) {
        Write-NewUtf8File -Path $script:progressFile -Content $line
    }
    else {
        $encoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::AppendAllText($script:progressFile, "`n$line", $encoding)
    }
}

function New-CaseResult {
    param([Parameter(Mandatory)][object]$Case)

    return [ordered]@{
        case_id = [string]$Case.case_id
        feature_id = [string]$Case.feature_id
        capability_id = [string]$Case.capability_id
        input_sha256 = [string]$Case.sha256
        input_unchanged = $false
        input_text_sha256 = $null
        output_sha256 = $null
        output_text_sha256 = $null
        output_saved = $false
        render_pdf_requested = $true
        render_pdf_saved = $false
        render_pdf_sha256 = $null
        render_pdf_bytes = $null
        render_pdf_signature_valid = $false
        render_pdf_export_method = $null
        phases = [ordered]@{
            open_input = 'not_run'
            read_input = 'not_run'
            save_as_hwpx = 'not_run'
            close_input = 'not_run'
            reopen_output = 'not_run'
            read_output = 'not_run'
            export_pdf = 'not_run'
            close_output = 'not_run'
        }
        error_code = $null
        failed_phase = $null
    }
}

$manifestRecord = Read-ExactFixtureManifest `
    -Path $FixtureManifestPath `
    -ExpectedSha256 $ExpectedFixtureManifestSha256
$manifestFile = $manifestRecord.item.FullName
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $manifestFile)).Path.TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'TABLE_RULING_BATCH_FIXTURE_BOUNDARY_REPARSE_POINT'
}
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = [System.IO.Path]::GetFullPath($ProgressPath)
foreach ($candidate in @($traceFile, $script:progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'TABLE_RULING_BATCH_PATH_OUTSIDE_FIXTURE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) {
        throw 'TABLE_RULING_BATCH_OUTPUT_ALREADY_EXISTS'
    }
}
$cases = @($manifestRecord.value.cases)
$casePaths = @(Assert-CaseFiles -Boundary $boundary -Cases $cases)
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TABLE_RULING_BATCH_PREEXISTING_HWP_PROCESS'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'TABLE_RULING_BATCH_TARGET_IDENTITY_MISMATCH'
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-engine/v1'
    state = 'failed'
    target = [ordered]@{
        prog_id = $ProgId
        registry_view = 'Registry32'
        client = 'windows_powershell_x86_sta'
        file_version = $identity.file_version
        executable_sha256 = $identity.sha256
    }
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    case_count = $cases.Count
    completed_case_count = 0
    cases = @()
    failed_case_id = $null
    failed_feature_id = $null
    error_code = $null
    failed_phase = $null
    exception_type = $null
    exception_hresult = $null
    raw_document_text_present = $false
    user_document_scanned = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_user_access = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$phase = 'com_create'
$activeIndex = 0
$activeCaseId = $null
$activeFeature = $null
$activeResult = $null
$hwpProcessId = $null
$script:progressSequence = 0
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'TABLE_RULING_BATCH_CLIENT_NOT_STA'
    }
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'TABLE_RULING_BATCH_AUTOMATION_VERSION_MISMATCH'
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -eq 1) { $hwpProcessId = [int]$hwpProcesses[0].ProcessId }
    Write-ProgressEvent -Phase 'com_create' -State 'pass' -HwpProcessId $hwpProcessId

    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $result.window_visible_for_user_access = $true

    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        $paths = $casePaths[$index]
        $activeIndex = $index + 1
        $activeCaseId = [string]$case.case_id
        $activeFeature = [string]$case.feature_id
        $activeResult = New-CaseResult -Case $case
        $result.cases += ,$activeResult

        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'TABLE_RULING_BATCH_DOCUMENT_ADD_FAILED' }

        $phase = 'open_input'
        $activeResult.phases.open_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        if ($document.Open($paths.input, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'TABLE_RULING_BATCH_INPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.open_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'read_input'
        $activeResult.phases.read_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        $inputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
        $activeResult.input_text_sha256 = Get-Sha256String -Value $inputText
        $activeResult.phases.read_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'save_as_hwpx'
        $activeResult.phases.save_as_hwpx = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        [void]$document.SaveAs($paths.output, 'HWPX', '')
        if (-not (Test-Path -LiteralPath $paths.output -PathType Leaf)) {
            throw 'TABLE_RULING_BATCH_SAVE_OUTPUT_MISSING'
        }
        $activeResult.output_saved = $true
        $activeResult.output_sha256 = Get-Sha256File -Path $paths.output
        $activeResult.phases.save_as_hwpx = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'close_input'
        $activeResult.phases.close_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'reopen_output'
        $activeResult.phases.reopen_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'TABLE_RULING_BATCH_REOPEN_DOCUMENT_ADD_FAILED' }
        if ($document.Open($paths.output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'TABLE_RULING_BATCH_OUTPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.reopen_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'read_output'
        $activeResult.phases.read_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        $outputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
        $activeResult.output_text_sha256 = Get-Sha256String -Value $outputText
        if ($activeResult.output_text_sha256 -cne $activeResult.input_text_sha256) {
            throw 'TABLE_RULING_BATCH_TEXT_ROUNDTRIP_MISMATCH'
        }
        $activeResult.phases.read_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'export_pdf'
        $activeResult.phases.export_pdf = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        $activeResult.render_pdf_export_method = 'IXHwpDocument.SaveAs/PDF'
        [void]$document.SaveAs($paths.pdf, 'PDF', '')
        if (-not (Test-Path -LiteralPath $paths.pdf -PathType Leaf)) {
            throw 'TABLE_RULING_BATCH_PDF_EXPORT_OUTPUT_MISSING'
        }
        $pdfItem = Get-Item -LiteralPath $paths.pdf -Force
        if ($pdfItem.PSIsContainer -or
            ($pdfItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $pdfItem.Length -lt 5 -or $pdfItem.Length -gt 33554432) {
            throw 'TABLE_RULING_BATCH_PDF_NOT_BOUNDED_REGULAR_FILE'
        }
        $pdfStream = [System.IO.File]::OpenRead($paths.pdf)
        try {
            $signature = [byte[]]::new(5)
            if ($pdfStream.Read($signature, 0, $signature.Length) -ne $signature.Length -or
                [System.Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
                throw 'TABLE_RULING_BATCH_PDF_SIGNATURE_MISMATCH'
            }
        }
        finally { $pdfStream.Dispose() }
        $activeResult.render_pdf_saved = $true
        $activeResult.render_pdf_sha256 = Get-Sha256File -Path $paths.pdf
        $activeResult.render_pdf_bytes = [long]$pdfItem.Length
        $activeResult.render_pdf_signature_valid = $true
        $activeResult.phases.export_pdf = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $phase = 'close_output'
        $activeResult.phases.close_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature

        $activeResult.input_unchanged = (Get-Sha256File -Path $paths.input) -ceq [string]$case.sha256
        if (-not $activeResult.input_unchanged) { throw 'TABLE_RULING_BATCH_INPUT_CHANGED' }
        $result.completed_case_count += 1
    }

    $phase = 'quit'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $hwp.Quit()
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
    $result.state = 'pass'
}
catch {
    $result.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_RULING_BATCH_EXCEPTION' }
    $result.failed_case_id = $activeCaseId
    $result.failed_feature_id = $activeFeature
    $result.failed_phase = $phase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    if ($null -ne $activeResult -and $activeResult.phases.Contains($phase)) {
        $activeResult.phases[$phase] = 'failed'
        $activeResult.error_code = $result.error_code
        $activeResult.failed_phase = $phase
    }
    Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId `
        -CaseIndex $activeIndex -CaseId $activeCaseId -FeatureId $activeFeature
}
finally {
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
        Clear-ComObject -Value $document
    }
    Clear-ComObject -Value $documents
    Clear-ComObject -Value $window
    if ($null -ne $hwp -and $result.state -ne 'pass') {
        try { $hwp.Quit() } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    for ($index = 0; $index -lt $result.cases.Count; $index += 1) {
        try {
            $result.cases[$index].input_unchanged =
                (Get-Sha256File -Path $casePaths[$index].input) -ceq [string]$cases[$index].sha256
        }
        catch { $result.cases[$index].input_unchanged = $false }
    }
}

Write-ProgressEvent -Phase 'terminal' -State $(if ($result.state -eq 'pass') { 'pass' } else { 'failed' }) `
    -HwpProcessId $hwpProcessId -CaseIndex $activeIndex -CaseId $activeCaseId `
    -FeatureId $activeFeature
Write-NewUtf8File -Path $traceFile -Content ($result | ConvertTo-Json -Depth 10)
$result | ConvertTo-Json -Depth 10
if ($result.state -ne 'pass') { exit 2 }
