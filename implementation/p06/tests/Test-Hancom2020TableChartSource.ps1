[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\create-hancom-2020-table-chart-source.ps1'
)).Path
$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-chart-source.ps1'
)).Path
$sources = [ordered]@{}
foreach ($path in @($workerPath, $wrapperPath)) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $path, [ref]$tokens, [ref]$errors
    )
    $sources[$path] = [ordered]@{
        errors = $errors.Count
        content = [System.IO.File]::ReadAllText($path)
    }
}
$worker = [string]$sources[$workerPath].content
$wrapper = [string]$sources[$wrapperPath].content
$all = $worker + $wrapper

function Test-PreflightFailure {
    $temporaryRoot = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::GetTempPath()
    ).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-chart-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $baseline = Join-Path $directory 'baseline.txt'
    $chart = Join-Path $directory 'chart.hwpx'
    $trace = Join-Path $directory 'trace.json'
    $observed = $null
    try {
        & $wrapperPath -BaselinePath $baseline -ChartPath $chart -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $chart, $baseline)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        $resolved = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($resolved) -and
            $resolved.StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-chart-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($resolved, $false)
        }
    }
    return $observed -ceq 'TABLE_CHART_OUTPUT_EXTENSION_INVALID'
}

function Test-ProgressNullRoundTrip {
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $workerPath, [ref]$tokens, [ref]$errors
    )
    if ($errors.Count -ne 0) { return $false }
    $definition = $ast.Find(
        {
            param($node)
            $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                $node.Name -ceq 'Write-ProgressEvent'
        },
        $true
    )
    if ($null -eq $definition) { return $false }
    $path = Join-Path ([System.IO.Path]::GetTempPath()) (
        'hwpx-agent-p06-chart-progress-' + [guid]::NewGuid().ToString('N') + '.jsonl'
    )
    try {
        Invoke-Expression ([string]$definition.Extent.Text)
        $script:progressFile = $path
        $script:progressSequence = 0
        Write-ProgressEvent -Phase 'preflight' -State 'pass'
        $record = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
        return $null -eq $record.hwp_process_id -and
            [string]$record.phase -ceq 'preflight' -and
            [string]$record.state -ceq 'pass' -and
            [long]$record.sequence -eq 1
    }
    catch { return $false }
    finally {
        if ([System.IO.File]::Exists($path)) { [System.IO.File]::Delete($path) }
    }
}

$checks = [ordered]@{
    scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_schema = $worker -match
        'hwpx-agent\.p06-09-hancom-2020-table-chart-source/v1' -and
        $worker -match 'hwpx-agent\.p06-09-hancom-2020-table-chart-progress/v1' -and
        $wrapper -match
            'hwpx-agent\.p06-09-hancom-2020-table-chart-source-watchdog/v1'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    active_new_document_only = $worker -match '\$documents\.Add\(\$false\)' -and
        $worker -match '\$document\.SetActive_XHwpDocument\(\)' -and
        $worker -notmatch '(?i)\.Open\s*\('
    exact_source_grid = $worker -match '\$creation\.Rows = 3' -and
        $worker -match '\$creation\.Cols = 3'
    exact_source_values = $worker -match
        '\$values = @\(''Series-A'', ''Series-B'', ''Category-A'', ''1'', ''2'', ''Category-B'', ''3'', ''4''\)' -and
        $worker -match '\$trace\.source_cells_written \+= 1'
    blank_corner_and_row_major_write = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableRightCell''\s+foreach \(\$value in \$values\)'
    exact_full_cell_block = [regex]::Matches(
        $worker,
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableCellBlock'''
    ).Count -eq 1 -and $worker -match '1\.\.3 \| ForEach-Object' -and
        $worker -match '\$trace\.cell_block_action_count \+= 1'
    documented_chart_action = $worker -match
        '\$chartCreation = \$hwp\.HParameterSet\.HOleCreation' -and
        $worker -match '\.GetDefault\(''InsertChart'', \$chartCreationHSet\)' -and
        $worker -match '\.Execute\(''InsertChart'', \$chartCreationHSet\)'
    no_guessed_native_chart_xml = $all -notmatch
        '(?i)chartIDRef|chartSpace|content\.hpf|Contents[\\/]chart|OOXMLChartContents'
    source_text_preservation = $worker -match
        '\$trace\.source_text_preserved' -and
        $worker -match 'CHART_SOURCE_TEXT_DRIFT'
    separate_immutable_outputs = $worker -match
        '\$document\.SaveAs\(\$baseline' -and
        $worker -match '\$document\.SaveAs\(\$chart' -and
        $all -match 'OUTPUT_PATH_COLLISION' -and
        $all -match 'Split-Path -Parent \$candidate'
    output_digests_only = $worker -match 'baseline_hwpx_sha256' -and
        $worker -match 'chart_hwpx_sha256' -and
        $all -match 'raw_document_text_present = \$false' -and
        $all -match 'raw_chart_payload_present = \$false'
    bounded_watchdog = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $wrapper -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $wrapper -match 'Stop-OwnedHancomProcess' -and
        $wrapper -match '\[int\]\$candidate\.ProcessId -eq \[int\]\$ExpectedProcessId' -and
        $wrapper -match '\$progress\.worker_process_id -eq \[long\]\$child\.Id'
    exact_success_receipt = $wrapper -match '\$successSemanticsValid' -and
        $wrapper -match '\[long\]\$trace\.source_cells_written -eq 8' -and
        $wrapper -match '\[long\]\$trace\.cell_block_action_count -eq 3' -and
        $wrapper -match '\$trace\.chart_action -ceq ''pass'''
    progress_journal = $wrapper -match 'Read-ProgressJournal' -and
        $wrapper -match 'progress_last_phase = \$progress\.last_phase' -and
        $wrapper -match 'inner_trace_preserved = Test-Path'
    progress_null_roundtrip = Test-ProgressNullRoundTrip
    preexisting_hwp_rejected = $all -match 'PREEXISTING_HWP_PROCESS'
    exact_owned_process_binding = $worker -match 'HWP_PROCESS_OWNERSHIP_MISMATCH' -and
        $worker -match '\$processCreatedAt -lt \$comStartedAt\.AddSeconds\(-2\)' -and
        $worker -match '\[int\]\$process\.SessionId -ne \$sessionId' -and
        $worker -match '\$trace\.hwp_process_identity_bound = \$true' -and
        $wrapper -match '\[bool\]\$trace\.hwp_process_identity_bound'
    preflight_fails_before_com = Test-PreflightFailure
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch
        '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch
        '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-chart-source-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
