[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\create-hancom-2020-table-thousands-source.ps1'
)).Path
$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-thousands-source.ps1'
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
        'hwpx-agent-p06-thousands-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $baseline = Join-Path $directory 'baseline.txt'
    $removed = Join-Path $directory 'removed.hwpx'
    $added = Join-Path $directory 'added.hwpx'
    $trace = Join-Path $directory 'trace.json'
    $observed = $null
    try {
        & $wrapperPath -BaselinePath $baseline -RemovedPath $removed `
            -AddedPath $added -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $added, $removed, $baseline)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        $resolved = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($resolved) -and
            $resolved.StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-thousands-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($resolved, $false)
        }
    }
    return $observed -ceq 'TABLE_THOUSANDS_OUTPUT_EXTENSION_INVALID'
}

$checks = [ordered]@{
    scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_schema = $worker -match
        'hwpx-agent\.p06-09-hancom-2020-table-thousands-source/v2' -and
        $worker -match 'hwpx-agent\.p06-09-hancom-2020-table-thousands-progress/v1' -and
        $wrapper -match
            'hwpx-agent\.p06-09-hancom-2020-table-thousands-source-watchdog/v2'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    active_new_document_only = $worker -match '\$documents\.Add\(\$false\)' -and
        $worker -match '\$document\.SetActive_XHwpDocument\(\)' -and
        $worker -notmatch '(?i)\.Open\s*\('
    exact_source_grid = $worker -match '\$creation\.Rows = 1' -and
        $worker -match '\$creation\.Cols = 3'
    exact_operands = $worker -match 'Write-ExactText -Hwp \$hwp -Text ''1200''' -and
        $worker -match 'Write-ExactText -Hwp \$hwp -Text ''3400'''
    hancom_authors_formula = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableFormulaSumHor'''
    exact_formula_cell_selection = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableCellBlock''' -and
        $worker -match '\$trace\.formula_cell_selection = ''pass''' -and
        $wrapper -match '\$trace\.formula_cell_selection -ceq ''pass'''
    exact_thousands_actions = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableDeleteComma''' -and
        $worker -match 'Invoke-ActionRun -Hwp \$hwp -Action ''TableInsertComma''' -and
        $worker -match 'Assert-ActionEnabled -Hwp \$hwp -Action ''TableDeleteComma''' -and
        $worker -match 'Assert-ActionEnabled -Hwp \$hwp -Action ''TableInsertComma'''
    ui_macro_aliases_rejected = $all -notmatch
        '(?i)DeleteThousandsSeparator|InsertThousandsSeparator'
    exact_visible_transitions = $worker -match
        'Assert-VisibleOperandsAndResult -Text \$baselineText -Mode ''grouped''' -and
        $worker -match
            'Assert-VisibleOperandsAndResult -Text \$removedText -Mode ''plain''' -and
        $worker -match
            'Assert-VisibleOperandsAndResult -Text \$addedText -Mode ''grouped'''
    no_guessed_native_format = $all -notmatch '(?i)ResultFormat|\?\?|LastResult|HFieldCtrl'
    separate_immutable_outputs = $worker -match '\$document\.SaveAs\(\$baseline' -and
        $worker -match '\$document\.SaveAs\(\$removed' -and
        $worker -match '\$document\.SaveAs\(\$added' -and
        $all -match 'OUTPUT_PATH_COLLISION' -and
        $all -match 'Split-Path -Parent \$candidate'
    output_digests_only = $worker -match 'baseline_hwpx_sha256' -and
        $worker -match 'removed_hwpx_sha256' -and
        $worker -match 'added_hwpx_sha256' -and
        $all -match 'raw_document_text_present = \$false' -and
        $all -match 'raw_formula_or_command_present = \$false'
    bounded_watchdog = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $wrapper -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $wrapper -match 'Stop-OwnedHancomProcess' -and
        $wrapper -match '\[int\]\$candidate\.ProcessId -eq \[int\]\$ExpectedProcessId' -and
        $wrapper -match '\$progress\.worker_process_id -eq \[long\]\$child\.Id'
    exact_success_receipt = $wrapper -match '\$successSemanticsValid' -and
        $wrapper -match '\[long\]\$trace\.operand_cells_written -eq 2' -and
        $wrapper -match '\$trace\.formula_cell_selection -ceq ''pass''' -and
        $wrapper -match '\$trace\.delete_thousands_action -ceq ''pass''' -and
        $wrapper -match '\$trace\.insert_thousands_action -ceq ''pass'''
    progress_journal = $wrapper -match 'Read-ProgressJournal' -and
        $wrapper -match "'baseline_save', 'formula_cell_select', 'delete_thousands'" -and
        $wrapper -match 'progress_last_phase = \$progress\.last_phase' -and
        $wrapper -match 'inner_trace_preserved = Test-Path'
    preexisting_hwp_rejected = $all -match 'PREEXISTING_HWP_PROCESS'
    preflight_fails_before_com = Test-PreflightFailure
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-thousands-source-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
