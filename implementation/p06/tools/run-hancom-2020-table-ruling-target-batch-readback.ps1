[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',
    [ValidateRange(60, 1800)][int]$TimeoutSeconds = 900
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'TABLE_RULING_TARGET_BATCH_READBACK'
$exactFixtureManifestSha256 = '8296cf4057c1cb6b27c800c15694866008c31cfa290cd6863321179c1efda543'
if ($ExpectedFixtureManifestSha256 -cne $exactFixtureManifestSha256) {
    throw ($errorPrefix + '_MANIFEST_IDENTITY_MISMATCH')
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

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) { throw ($errorPrefix + '_PROCESS_ARGUMENT_CONTAINS_QUOTE') }
    return '"' + $Value + '"'
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
        throw ($errorPrefix + '_MANIFEST_NOT_BOUNDED_REGULAR_FILE')
    }
    if ((Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw ($errorPrefix + '_MANIFEST_SHA256_MISMATCH')
    }
    try {
        $manifest = if ($PSVersionTable.PSVersion.Major -ge 7) {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
        }
        else {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    }
    catch { throw ($errorPrefix + '_MANIFEST_JSON_INVALID') }
    Assert-ExactProperties -Value $manifest -Expected @(
        'schema_version', 'source_ancestor_sha256', 'cases', 'actual_hangul_2020',
        'render', 'automation', 'differential'
    ) -ErrorCode ($errorPrefix + '_MANIFEST_SHAPE_INVALID')
    if ([string]$manifest.schema_version -cne 'hwpx-agent.p06-09-table-ruling-target-fixture/v1' -or
        [string]$manifest.source_ancestor_sha256 -cne
            '6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5' -or
        -not ($manifest.actual_hangul_2020 -is [bool]) -or [bool]$manifest.actual_hangul_2020 -or
        [string]$manifest.render -cne 'not_run' -or
        [string]$manifest.automation -cne 'not_run' -or
        [string]$manifest.differential -cne 'not_run') {
        throw ($errorPrefix + '_MANIFEST_STATE_INVALID')
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
        throw ($errorPrefix + '_CASE_SET_INVALID')
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
            -ErrorCode ($errorPrefix + '_CASE_SHAPE_INVALID')
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
            throw ($errorPrefix + '_CASE_BINDING_INVALID')
        }
        Assert-ExactProperties -Value $case.binding -Expected $bindingProperties `
            -ErrorCode ($errorPrefix + '_BINDING_SHAPE_INVALID')
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
            throw ($errorPrefix + '_BINDING_CARDINALITY_INVALID')
        }
        for ($boundaryIndex = 0; $boundaryIndex -lt $rowBoundaries.Count; $boundaryIndex += 1) {
            if (-not ($rowBoundaries[$boundaryIndex] -is [int] -or
                $rowBoundaries[$boundaryIndex] -is [long]) -or
                [long]$rowBoundaries[$boundaryIndex] -ne [long]$expectedRowBoundaries[$boundaryIndex]) {
                throw ($errorPrefix + '_ROW_BOUNDARIES_INVALID')
            }
        }
        for ($boundaryIndex = 0; $boundaryIndex -lt $columnBoundaries.Count; $boundaryIndex += 1) {
            if (-not ($columnBoundaries[$boundaryIndex] -is [int] -or
                $columnBoundaries[$boundaryIndex] -is [long]) -or
                [long]$columnBoundaries[$boundaryIndex] -ne
                    [long]$expectedColumnBoundaries[$boundaryIndex]) {
                throw ($errorPrefix + '_COLUMN_BOUNDARIES_INVALID')
            }
        }
        $seenLogicalIds = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::Ordinal
        )
        [void]$seenLogicalIds.Add([string]$case.binding.table_id)
        $boundPayloadCount = 0
        foreach ($bindingCell in $bindingCells) {
            Assert-ExactProperties -Value $bindingCell -Expected $bindingCellProperties `
                -ErrorCode ($errorPrefix + '_BINDING_CELL_SHAPE_INVALID')
            if ([string]$bindingCell.master_cell_id -notmatch '^[a-z][a-z0-9-]{0,127}$' -or
                -not $seenLogicalIds.Add([string]$bindingCell.master_cell_id)) {
                throw ($errorPrefix + '_BINDING_CELL_ID_INVALID')
            }
            foreach ($payloadId in @($bindingCell.payload_block_ids)) {
                if ([string]$payloadId -notmatch '^[a-z][a-z0-9-]{0,127}$' -or
                    -not $seenLogicalIds.Add([string]$payloadId)) {
                    throw ($errorPrefix + '_BINDING_PAYLOAD_ID_INVALID')
                }
                $boundPayloadCount += 1
            }
        }
        if ($boundPayloadCount -ne [long]$case.payload_block_count) {
            throw ($errorPrefix + '_BINDING_PAYLOAD_COUNT_INVALID')
        }
        $operations = @($case.operations)
        if ($operations.Count -ne [long]$expected[9]) {
            throw ($errorPrefix + '_OPERATION_SET_INVALID')
        }
        $previousTargetState = $null
        $previousTargetGrid = $null
        for ($operationIndex = 0; $operationIndex -lt $operations.Count; $operationIndex += 1) {
            $operation = $operations[$operationIndex]
            Assert-ExactProperties -Value $operation -Expected $operationProperties `
                -ErrorCode ($errorPrefix + '_OPERATION_SHAPE_INVALID')
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
                throw ($errorPrefix + '_OPERATION_BINDING_INVALID')
            }
            if ($operationIndex -gt 0 -and (
                [string]$operation.source_state_sha256 -cne [string]$previousTargetState -or
                [string]$operation.source_grid_sha256 -cne [string]$previousTargetGrid)) {
                throw ($errorPrefix + '_OPERATION_CHAIN_INVALID')
            }
            $previousTargetState = [string]$operation.target_state_sha256
            $previousTargetGrid = [string]$operation.target_grid_sha256
        }
        if ([string]$previousTargetState -cne [string]$case.target_state_sha256 -or
            [string]$previousTargetGrid -cne [string]$case.target_grid_sha256) {
            throw ($errorPrefix + '_OPERATION_TARGET_INVALID')
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
                throw ($errorPrefix + '_PATH_OUTSIDE_FIXTURE_BOUNDARY')
            }
        }
        $inputItem = Get-Item -LiteralPath $casePaths.input -Force
        if ($inputItem.PSIsContainer -or
            ($inputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $inputItem.Length -le 0 -or $inputItem.Length -gt 8388608 -or
            [System.IO.Path]::GetExtension($casePaths.input) -cne '.hwpx' -or
            (Get-Sha256File -Path $casePaths.input) -cne [string]$case.sha256) {
            throw ($errorPrefix + '_INPUT_INVALID')
        }
        foreach ($candidate in @($casePaths.output, $casePaths.pdf)) {
            if (Test-Path -LiteralPath $candidate) {
                throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS')
            }
        }
        $paths += ,$casePaths
    }
    return $paths
}

function Test-BoundedPdfEvidence {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][object]$CaseTrace
    )

    if (-not ($CaseTrace.render_pdf_requested -is [bool]) -or
        -not [bool]$CaseTrace.render_pdf_requested -or
        -not ($CaseTrace.render_pdf_saved -is [bool]) -or
        -not [bool]$CaseTrace.render_pdf_saved -or
        [string]$CaseTrace.render_pdf_sha256 -notmatch '^[0-9a-f]{64}$' -or
        -not ($CaseTrace.render_pdf_bytes -is [int] -or $CaseTrace.render_pdf_bytes -is [long]) -or
        [long]$CaseTrace.render_pdf_bytes -lt 5 -or [long]$CaseTrace.render_pdf_bytes -gt 33554432 -or
        -not ($CaseTrace.render_pdf_signature_valid -is [bool]) -or
        -not [bool]$CaseTrace.render_pdf_signature_valid -or
        [string]$CaseTrace.render_pdf_export_method -cne 'IXHwpDocument.SaveAs/PDF' -or
        -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -ne [long]$CaseTrace.render_pdf_bytes) {
        return $false
    }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $signature = [byte[]]::new(5)
        if ($stream.Read($signature, 0, $signature.Length) -ne $signature.Length -or
            [System.Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
            return $false
        }
    }
    finally { $stream.Dispose() }
    return (Get-Sha256File -Path $Path) -ceq [string]$CaseTrace.render_pdf_sha256
}

function Test-ExactInnerTraceShape {
    param([Parameter(Mandatory)][object]$Trace)

    try {
        Assert-ExactProperties -Value $Trace -Expected @(
            'schema_version', 'state', 'target', 'fixture_manifest_sha256', 'case_count',
            'completed_case_count', 'cases', 'failed_case_id', 'failed_feature_id', 'error_code',
            'failed_phase', 'exception_type', 'exception_hresult',
            'raw_document_text_present', 'user_document_scanned',
            'external_network_invoked', 'registry_or_system_setting_changed',
            'computer_use_click_or_type_invoked', 'window_visible_for_user_access'
        ) -ErrorCode 'INVALID'
        Assert-ExactProperties -Value $Trace.target -Expected @(
            'prog_id', 'registry_view', 'client', 'file_version', 'executable_sha256'
        ) -ErrorCode 'INVALID'
        $caseProperties = @(
            'case_id', 'feature_id', 'capability_id', 'input_sha256', 'input_unchanged',
            'input_text_sha256', 'output_sha256', 'output_text_sha256', 'output_saved',
            'render_pdf_requested', 'render_pdf_saved', 'render_pdf_sha256',
            'render_pdf_bytes', 'render_pdf_signature_valid', 'render_pdf_export_method',
            'phases', 'error_code', 'failed_phase'
        )
        $phaseProperties = @(
            'open_input', 'read_input', 'save_as_hwpx', 'close_input',
            'reopen_output', 'read_output', 'export_pdf', 'close_output'
        )
        foreach ($caseTrace in @($Trace.cases)) {
            Assert-ExactProperties -Value $caseTrace -Expected $caseProperties -ErrorCode 'INVALID'
            Assert-ExactProperties -Value $caseTrace.phases -Expected $phaseProperties -ErrorCode 'INVALID'
        }
        return $true
    }
    catch { return $false }
}

function Test-ExactCaseEvidence {
    param(
        [Parameter(Mandatory)][object]$CaseTrace,
        [Parameter(Mandatory)][object]$Case,
        [Parameter(Mandatory)][object]$Paths
    )

    $phaseNames = @(
        'open_input', 'read_input', 'save_as_hwpx', 'close_input',
        'reopen_output', 'read_output', 'export_pdf', 'close_output'
    )
    if ([string]$CaseTrace.case_id -cne [string]$Case.case_id -or
        [string]$CaseTrace.feature_id -cne [string]$Case.feature_id -or
        [string]$CaseTrace.capability_id -cne [string]$Case.capability_id -or
        [string]$CaseTrace.input_sha256 -cne [string]$Case.sha256 -or
        -not ($CaseTrace.input_unchanged -is [bool]) -or -not [bool]$CaseTrace.input_unchanged -or
        [string]$CaseTrace.input_text_sha256 -notmatch '^[0-9a-f]{64}$' -or
        [string]$CaseTrace.output_text_sha256 -notmatch '^[0-9a-f]{64}$' -or
        [string]$CaseTrace.output_text_sha256 -cne [string]$CaseTrace.input_text_sha256 -or
        -not ($CaseTrace.output_saved -is [bool]) -or -not [bool]$CaseTrace.output_saved -or
        [string]$CaseTrace.output_sha256 -notmatch '^[0-9a-f]{64}$' -or
        $null -ne $CaseTrace.error_code -or $null -ne $CaseTrace.failed_phase -or
        -not (Test-Path -LiteralPath $Paths.output -PathType Leaf) -or
        -not (Test-BoundedPdfEvidence -Path $Paths.pdf -CaseTrace $CaseTrace)) {
        return $false
    }
    $outputItem = Get-Item -LiteralPath $Paths.output -Force
    if ($outputItem.PSIsContainer -or
        ($outputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $outputItem.Length -le 0 -or $outputItem.Length -gt 8388608 -or
        (Get-Sha256File -Path $Paths.output) -cne [string]$CaseTrace.output_sha256) {
        return $false
    }
    $observedPhases = @($CaseTrace.phases.PSObject.Properties.Name)
    if ($observedPhases.Count -ne $phaseNames.Count) { return $false }
    foreach ($phaseName in $phaseNames) {
        if ($observedPhases -cnotcontains $phaseName -or
            [string]$CaseTrace.phases.$phaseName -cne 'pass') {
            return $false
        }
    }
    return $true
}

function Read-ProgressJournal {
    param([Parameter(Mandatory)][string]$Path)

    $summary = [ordered]@{
        present = Test-Path -LiteralPath $Path -PathType Leaf
        valid = $false
        event_count = 0
        last_phase = $null
        last_state = $null
        observed_phase = $null
        observed_case_id = $null
        observed_feature_id = $null
        window_visible_for_user_access = $false
    }
    if (-not $summary.present) { return $summary }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 262144) {
        return $summary
    }
    $allowedProperties = @(
        'schema_version', 'sequence', 'recorded_at_utc', 'worker_process_id',
        'hwp_process_id', 'case_index', 'case_id', 'feature_id', 'phase', 'state',
        'raw_document_text_present'
    )
    $allowedPhases = @(
        'preflight', 'com_create', 'open_input', 'read_input', 'save_as_hwpx',
        'close_input', 'reopen_output', 'read_output', 'export_pdf', 'close_output',
        'quit', 'terminal'
    )
    $allowedCaseIds = @(
        'table-002-draw-outer',
        'table-002-draw-topology',
        'table-002-draw-diagonals-formula',
        'table-003-eraser-structural-merge',
        'table-003-eraser-transparent-formula'
    )
    $allowedFeatures = @('TABLE-002', 'TABLE-002', 'TABLE-002', 'TABLE-003', 'TABLE-003')
    $expectedSequence = 1
    $workerProcessId = $null
    $hwpProcessId = $null
    $preflightPrefixValid = $false
    $comPrefixValid = $false
    foreach ($line in @(Get-Content -LiteralPath $Path -Encoding UTF8)) {
        if ($expectedSequence -gt 160 -or [string]::IsNullOrWhiteSpace($line)) { return $summary }
        try {
            $event = if ($PSVersionTable.PSVersion.Major -ge 7) {
                $line | ConvertFrom-Json -DateKind String
            }
            else { $line | ConvertFrom-Json }
        }
        catch { return $summary }
        $properties = @($event.PSObject.Properties.Name)
        if ($properties.Count -ne $allowedProperties.Count) { return $summary }
        foreach ($property in $properties) {
            if ($allowedProperties -cnotcontains $property) { return $summary }
        }
        $sequenceIsInteger = $event.sequence -is [int] -or $event.sequence -is [long]
        $workerIsInteger = $event.worker_process_id -is [int] -or $event.worker_process_id -is [long]
        $hwpIsValid = $null -eq $event.hwp_process_id -or
            $event.hwp_process_id -is [int] -or $event.hwp_process_id -is [long]
        $caseIsInteger = $event.case_index -is [int] -or $event.case_index -is [long]
        if (-not $sequenceIsInteger -or -not $workerIsInteger -or -not $hwpIsValid -or
            -not $caseIsInteger -or -not ($event.raw_document_text_present -is [bool]) -or
            [bool]$event.raw_document_text_present -or
            [string]$event.schema_version -cne 'hwpx-agent.p06-09-table-ruling-batch-progress/v1' -or
            [long]$event.sequence -ne $expectedSequence -or
            [string]$event.recorded_at_utc -notmatch '^\d{4}-\d{2}-\d{2}T' -or
            [long]$event.worker_process_id -le 0 -or
            ($null -ne $event.hwp_process_id -and [long]$event.hwp_process_id -le 0) -or
            [long]$event.case_index -lt 0 -or [long]$event.case_index -gt 5 -or
            ($null -ne $event.case_id -and $allowedCaseIds -cnotcontains [string]$event.case_id) -or
            ($null -ne $event.feature_id -and $allowedFeatures -cnotcontains [string]$event.feature_id) -or
            $allowedPhases -cnotcontains [string]$event.phase -or
            [string]$event.state -notin @('running', 'pass', 'failed')) {
            return $summary
        }
        if ($null -eq $workerProcessId) { $workerProcessId = [long]$event.worker_process_id }
        elseif ($workerProcessId -ne [long]$event.worker_process_id) { return $summary }
        if ($null -ne $event.hwp_process_id) {
            if ($null -eq $hwpProcessId) { $hwpProcessId = [long]$event.hwp_process_id }
            elseif ($hwpProcessId -ne [long]$event.hwp_process_id) { return $summary }
        }
        if ([long]$event.case_index -eq 0 -and
            ($null -ne $event.case_id -or $null -ne $event.feature_id)) {
            return $summary
        }
        if ([long]$event.case_index -gt 0 -and (
            [string]$event.case_id -cne $allowedCaseIds[[long]$event.case_index - 1] -or
            [string]$event.feature_id -cne $allowedFeatures[[long]$event.case_index - 1])) {
            return $summary
        }
        $summary.event_count += 1
        $summary.last_phase = [string]$event.phase
        $summary.last_state = [string]$event.state
        if ([string]$event.phase -cne 'terminal') {
            $summary.observed_phase = [string]$event.phase
            $summary.observed_case_id = $event.case_id
            $summary.observed_feature_id = $event.feature_id
        }
        if ($expectedSequence -eq 1) {
            $preflightPrefixValid = [string]$event.phase -ceq 'preflight' -and
                [string]$event.state -ceq 'pass' -and [long]$event.case_index -eq 0
        }
        elseif ($expectedSequence -eq 2) {
            $comPrefixValid = $preflightPrefixValid -and
                [string]$event.phase -ceq 'com_create' -and
                [string]$event.state -ceq 'pass' -and $null -ne $event.hwp_process_id
        }
        elseif ($comPrefixValid -and [string]$event.phase -ceq 'open_input' -and
            [string]$event.state -ceq 'running' -and [long]$event.case_index -eq 1) {
            $summary.window_visible_for_user_access = $true
        }
        $expectedSequence += 1
    }
    $summary.valid = $summary.event_count -gt 0
    return $summary
}

function Stop-OwnedHancomProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )

    $cleaned = 0
    $refused = 0
    $errors = 0
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        $runtime = Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtime) { continue }
        $processPath = [string]$candidate.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($processPath)) {
            try { $processPath = [string]$runtime.Path } catch { $processPath = '' }
        }
        $createdAt = if ($null -ne $candidate.CreationDate) {
            [datetime]$candidate.CreationDate
        }
        else { [datetime]::MinValue }
        $identityMatches = $false
        if (-not [string]::IsNullOrWhiteSpace($processPath) -and
            (Test-Path -LiteralPath $processPath -PathType Leaf)) {
            try { $identityMatches = (Get-Sha256File -Path $processPath) -ceq $ExpectedSha256 } catch { }
        }
        $safeToClean =
            [int]$candidate.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            $identityMatches -and
            [string]$candidate.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $safeToClean) {
            $refused += 1
            continue
        }
        try {
            Stop-Process -Id $candidate.ProcessId -Force -ErrorAction Stop
            Wait-Process -Id $candidate.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            $cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue)) {
                $cleaned += 1
            }
            else { $errors += 1 }
        }
    }
    return [ordered]@{ cleaned = $cleaned; refused = $refused; errors = $errors }
}

$engine = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-table-ruling-target-batch-engine.ps1'
)).Path
$manifestRecord = Read-ExactFixtureManifest `
    -Path $FixtureManifestPath `
    -ExpectedSha256 $ExpectedFixtureManifestSha256
$manifestFile = $manifestRecord.item.FullName
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $manifestFile)).Path.TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw ($errorPrefix + '_FIXTURE_BOUNDARY_REPARSE_POINT')
}
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
$progressFile = $traceFile + '.progress.jsonl'
foreach ($candidate in @($traceFile, $innerTrace, $progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw ($errorPrefix + '_PATH_OUTSIDE_FIXTURE_BOUNDARY')
    }
    if (Test-Path -LiteralPath $candidate) { throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS') }
}
$cases = @($manifestRecord.value.cases)
$casePaths = @(Assert-CaseFiles -Boundary $boundary -Cases $cases)
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}

$systemX86 = [System.Environment]::GetFolderPath(
    [System.Environment+SpecialFolder]::SystemX86
)
if ([string]::IsNullOrWhiteSpace($systemX86)) {
    throw ($errorPrefix + '_X86_POWERSHELL_UNAVAILABLE')
}
$powerShellItem = Get-Item -LiteralPath (
    Join-Path $systemX86 'WindowsPowerShell\v1.0\powershell.exe'
) -Force
if ($powerShellItem.PSIsContainer -or
    ($powerShellItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $powerShellItem.Length -le 0 -or $powerShellItem.Length -gt 16777216) {
    throw ($errorPrefix + '_X86_POWERSHELL_UNAVAILABLE')
}
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $engine,
    '-FixtureManifestPath', $manifestFile,
    '-ExpectedFixtureManifestSha256', $ExpectedFixtureManifestSha256,
    '-TracePath', $innerTrace,
    '-ProgressPath', $progressFile,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powerShellItem.FullName
$startInfo.Arguments = (($arguments | ForEach-Object {
    ConvertTo-ProcessArgument -Value ([string]$_)
}) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$child = [System.Diagnostics.Process]::new()
$child.StartInfo = $startInfo
$startedAt = Get-Date
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
[void]$child.Start()
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()

$exitedWithinTimeout = $child.WaitForExit($TimeoutSeconds * 1000)
if (-not $exitedWithinTimeout) {
    $child.Kill()
    $child.WaitForExit()
}
$childExitCode = $child.ExitCode
$outputDrained = $false
try {
    $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
        [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
        5000
    )
}
catch { $outputDrained = $false }

Start-Sleep -Milliseconds 500
$cleanup = Stop-OwnedHancomProcesses `
    -StartedAt $startedAt `
    -SessionId $currentSessionId `
    -ExpectedSha256 $ExpectedExecutableSha256
Start-Sleep -Milliseconds 250
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
$progress = Read-ProgressJournal -Path $progressFile
$observedFailurePhase = if ([bool]$progress.valid -and
    -not [string]::IsNullOrWhiteSpace([string]$progress.observed_phase)) {
    [string]$progress.observed_phase
}
else { 'watchdog' }
$windowVisibleForUserAccess = [bool]$progress.valid -and
    [bool]$progress.window_visible_for_user_access

$trace = $null
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    $innerItem = Get-Item -LiteralPath $innerTrace -Force
    if (($innerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0 -and
        $innerItem.Length -gt 0 -and $innerItem.Length -le 262144) {
        try {
            $trace = if ($PSVersionTable.PSVersion.Major -ge 7) {
                Get-Content -LiteralPath $innerTrace -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
            }
            else { Get-Content -LiteralPath $innerTrace -Raw -Encoding UTF8 | ConvertFrom-Json }
        }
        catch { $trace = $null }
    }
}
$traceValid = $null -ne $trace -and
    (Test-ExactInnerTraceShape -Trace $trace) -and
    @($trace.PSObject.Properties.Name) -ccontains 'schema_version' -and
    @($trace.PSObject.Properties.Name) -ccontains 'state' -and
    @($trace.PSObject.Properties.Name) -ccontains 'error_code' -and
    @($trace.PSObject.Properties.Name) -ccontains 'fixture_manifest_sha256' -and
    @($trace.PSObject.Properties.Name) -ccontains 'raw_document_text_present' -and
    [string]$trace.schema_version -ceq 'hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-engine/v1' -and
    [string]$trace.fixture_manifest_sha256 -ceq $ExpectedFixtureManifestSha256 -and
    [string]$trace.target.prog_id -ceq $ProgId -and
    [string]$trace.target.registry_view -ceq 'Registry32' -and
    [string]$trace.target.client -ceq 'windows_powershell_x86_sta' -and
    [string]$trace.target.file_version -ceq $ExpectedBuild -and
    [string]$trace.target.executable_sha256 -ceq $ExpectedExecutableSha256 -and
    ($trace.raw_document_text_present -is [bool]) -and -not [bool]$trace.raw_document_text_present -and
    ($trace.user_document_scanned -is [bool]) -and -not [bool]$trace.user_document_scanned -and
    ($trace.external_network_invoked -is [bool]) -and -not [bool]$trace.external_network_invoked -and
    ($trace.registry_or_system_setting_changed -is [bool]) -and
    -not [bool]$trace.registry_or_system_setting_changed -and
    ($trace.computer_use_click_or_type_invoked -is [bool]) -and
    -not [bool]$trace.computer_use_click_or_type_invoked
if (-not $traceValid) { $trace = $null }

$caseEvidenceValid = $false
if ($null -ne $trace -and [string]$trace.state -ceq 'pass' -and
    ($trace.case_count -is [int] -or $trace.case_count -is [long]) -and
    [long]$trace.case_count -eq 5 -and
    ($trace.completed_case_count -is [int] -or $trace.completed_case_count -is [long]) -and
    [long]$trace.completed_case_count -eq 5) {
    $traceCases = @($trace.cases)
    $caseEvidenceValid = $traceCases.Count -eq 5
    for ($index = 0; $caseEvidenceValid -and $index -lt 5; $index += 1) {
        $caseEvidenceValid = Test-ExactCaseEvidence `
            -CaseTrace $traceCases[$index] `
            -Case $cases[$index] `
            -Paths $casePaths[$index]
    }
}

$wrapperError = if (-not $exitedWithinTimeout) { $errorPrefix + '_TIMEOUT' }
elseif (-not $outputDrained) { $errorPrefix + '_CHILD_OUTPUT_DRAIN_TIMEOUT' }
elseif ($null -eq $trace) { $errorPrefix + '_INNER_TRACE_MISSING_OR_INVALID' }
elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
    if ($null -ne $trace.error_code) { [string]$trace.error_code }
    else { $errorPrefix + '_CHILD_FAILED' }
}
elseif (-not $caseEvidenceValid) { $errorPrefix + '_CASE_EVIDENCE_INVALID' }
elseif (-not [bool]$progress.valid -or
    [string]$progress.last_phase -cne 'terminal' -or
    [string]$progress.last_state -cne 'pass') {
    $errorPrefix + '_PROGRESS_INVALID'
}
elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) {
    $errorPrefix + '_PROCESS_CLEANUP_UNVERIFIED'
}
else { $null }

if ($null -eq $trace) {
    $stubCases = @()
    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $stubCases += ,[ordered]@{
            case_id = [string]$cases[$index].case_id
            feature_id = [string]$cases[$index].feature_id
            capability_id = [string]$cases[$index].capability_id
            input_sha256 = [string]$cases[$index].sha256
            input_unchanged = (Get-Sha256File -Path $casePaths[$index].input) -ceq [string]$cases[$index].sha256
            input_text_sha256 = $null
            output_sha256 = $null
            output_text_sha256 = $null
            output_saved = Test-Path -LiteralPath $casePaths[$index].output -PathType Leaf
            render_pdf_requested = $true
            render_pdf_saved = Test-Path -LiteralPath $casePaths[$index].pdf -PathType Leaf
            render_pdf_sha256 = $null
            render_pdf_bytes = $null
            render_pdf_signature_valid = $false
            render_pdf_export_method = $null
            phases = $null
            error_code = $wrapperError
            failed_phase = $observedFailurePhase
        }
    }
    $trace = [pscustomobject][ordered]@{
        schema_version = 'hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-readback/v1'
        state = 'failed'
        delegated_engine_schema = $null
        target = $null
        fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
        case_count = $cases.Count
        completed_case_count = 0
        cases = $stubCases
        failed_case_id = $progress.observed_case_id
        failed_feature_id = $progress.observed_feature_id
        error_code = $wrapperError
        failed_phase = $observedFailurePhase
        exception_type = $null
        exception_hresult = $null
        raw_document_text_present = $false
        user_document_scanned = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
        window_visible_for_user_access = $windowVisibleForUserAccess
    }
}
else {
    $innerSchema = [string]$trace.schema_version
    $trace.schema_version = 'hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-readback/v1'
    $trace | Add-Member -NotePropertyName delegated_engine_schema -NotePropertyValue $innerSchema -Force
    $traceCases = @($trace.cases)
    for ($index = 0; $index -lt $traceCases.Count -and $index -lt $cases.Count; $index += 1) {
        $traceCases[$index].input_unchanged =
            (Get-Sha256File -Path $casePaths[$index].input) -ceq [string]$cases[$index].sha256
    }
    if ($null -ne $wrapperError) {
        $trace.state = if ($wrapperError.EndsWith('_PROCESS_CLEANUP_UNVERIFIED')) { 'unverified' } else { 'failed' }
        $trace.error_code = $wrapperError
        if ($childExitCode -eq 0) { $trace.failed_phase = 'watchdog' }
    }
}
$trace | Add-Member -NotePropertyName watchdog -NotePropertyValue ([ordered]@{
    timeout_seconds = $TimeoutSeconds
    timed_out = -not $exitedWithinTimeout
    child_exit_code = $childExitCode
    output_drained = $outputDrained
    cleaned_process_count = [int]$cleanup.cleaned
    cleanup_refused_count = [int]$cleanup.refused
    cleanup_error_count = [int]$cleanup.errors
    remaining_hwp_process_count = $remaining.Count
    progress_present = [bool]$progress.present
    progress_valid = [bool]$progress.valid
    progress_event_count = [int]$progress.event_count
    progress_last_phase = $progress.last_phase
    progress_last_state = $progress.last_state
    progress_observed_phase = $progress.observed_phase
    progress_observed_case_id = $progress.observed_case_id
    progress_observed_feature_id = $progress.observed_feature_id
    window_visible_for_user_access = $windowVisibleForUserAccess
}) -Force

$json = $trace | ConvertTo-Json -Depth 12
Write-NewUtf8File -Path $traceFile -Content $json
if (Test-Path -LiteralPath $innerTrace -PathType Leaf) {
    [System.IO.File]::Delete($innerTrace)
}
$child.Dispose()
$json
if ($null -ne $wrapperError -or [string]$trace.state -cne 'pass') { exit 2 }
exit 0
