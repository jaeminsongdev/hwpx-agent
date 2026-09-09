[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\create-hancom-2020-table-number-format-source.ps1'
)).Path
$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-number-format-source.ps1'
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
        'hwpx-agent-p06-number-format-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $baseline = Join-Path $directory 'baseline.txt'
    $ungrouped = Join-Path $directory 'ungrouped.hwpx'
    $grouped = Join-Path $directory 'grouped.hwpx'
    $trace = Join-Path $directory 'trace.json'
    $observed = $null
    try {
        & $wrapperPath -BaselinePath $baseline -UngroupedPath $ungrouped `
            -GroupedPath $grouped -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $grouped, $ungrouped, $baseline)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        $resolved = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($resolved) -and
            $resolved.StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-number-format-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($resolved, $false)
        }
    }
    return $observed -ceq 'TABLE_NUMBER_FORMAT_OUTPUT_EXTENSION_INVALID'
}

function Test-OrderedMarkerSequence {
    param(
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][string[]]$Markers
    )
    $cursor = -1
    foreach ($marker in $Markers) {
        $cursor = $Text.IndexOf($marker, $cursor + 1, [System.StringComparison]::Ordinal)
        if ($cursor -lt 0) { return $false }
    }
    return $true
}

$checks = [ordered]@{
    scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_schema = $worker -match
        'hwpx-agent\.p06-09-hancom-2020-table-number-format-source/v1' -and
        $worker -match 'hwpx-agent\.p06-09-hancom-2020-table-number-format-progress/v1' -and
        $wrapper -match
            'hwpx-agent\.p06-09-hancom-2020-table-number-format-source-watchdog/v1'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    active_new_document_only = $worker -match '\$documents\.Add\(\$false\)' -and
        $worker -match '\$document\.SetActive_XHwpDocument\(\)' -and
        $worker -notmatch '(?i)\.Open\s*\('
    exact_source_grid = $worker -match '\$creation\.Rows = \$formatCases\.Count' -and
        $worker -match '\$creation\.Cols = 3' -and
        $worker -match 'format_case_count = \$formatCases\.Count'
    exact_format_case_order = Test-OrderedMarkerSequence -Text $worker -Markers @(
        "id = 'general'", "id = 'integer'", "id = 'decimal_1'",
        "id = 'decimal_2'", "id = 'decimal_3'", "id = 'decimal_4'"
    )
    exact_operands_and_results = $worker -match "left = '1000'; right = '100'" -and
        $worker -match "left = '1050'; right = '105'" -and
        $worker -match "ungrouped = '1122\.0'; grouped = '1,122\.0'" -and
        $worker -match "ungrouped = '1155\.0000'; grouped = '1,155\.0000'" -and
        $worker -match 'Assert-VisibleCaseRowSequence'
    hancom_authors_formula = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''TableFormulaSumHor'''
    manual_user_format_dialogs = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''ModifyCtrl''' -and
        $worker -match '\$phase = ''manual_format_''' -and
        $worker -match 'manual_ui_source_authoring_required = \$true' -and
        $worker -match 'manual_format_dialogs_passed \+= 1'
    exact_grouping_actions = $worker -match
        'Invoke-ActionRun -Hwp \$hwp -Action ''DeleteThousandsSeparator''' -and
        $worker -match 'Invoke-ActionRun -Hwp \$hwp -Action ''InsertThousandsSeparator'''
    no_guessed_native_format = $all -notmatch '(?i)ResultFormat|\?\?|LastResult|HFieldCtrl'
    separate_immutable_outputs = $worker -match '\$document\.SaveAs\(\$baseline' -and
        $worker -match '\$document\.SaveAs\(\$ungrouped' -and
        $worker -match '\$document\.SaveAs\(\$grouped' -and
        $all -match 'OUTPUT_PATH_COLLISION' -and
        $all -match 'Split-Path -Parent \$candidate'
    output_digests_only = $worker -match 'baseline_hwpx_sha256' -and
        $worker -match 'ungrouped_hwpx_sha256' -and
        $worker -match 'grouped_hwpx_sha256' -and
        $all -match 'raw_document_text_present = \$false' -and
        $all -match 'raw_formula_or_command_present = \$false'
    bounded_watchdog = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $wrapper -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $wrapper -match 'Stop-OwnedHancomProcess' -and
        $wrapper -match '\[int\]\$candidate\.ProcessId -eq \[int\]\$ExpectedProcessId' -and
        $wrapper -match '\$progress\.worker_process_id -eq \[long\]\$child\.Id'
    exact_success_receipt = $wrapper -match '\$successSemanticsValid' -and
        $wrapper -match '\[long\]\$trace\.format_case_count -eq 6' -and
        $wrapper -match '\[long\]\$trace\.operand_cells_written -eq 12' -and
        $wrapper -match '\[long\]\$trace\.formula_actions_passed -eq 6' -and
        $wrapper -match '\[long\]\$trace\.manual_format_dialogs_passed -eq 6' -and
        $wrapper -match '\[long\]\$trace\.delete_grouping_actions_passed -eq 6' -and
        $wrapper -match '\[long\]\$trace\.insert_grouping_actions_passed -eq 6'
    exact_progress_cases = $wrapper -match "'manual_format_general'" -and
        $wrapper -match "'manual_format_decimal_4'" -and
        $wrapper -match "'grouping_add_general'" -and
        $wrapper -match "'grouping_add_decimal_4'"
    progress_journal = $wrapper -match 'Read-ProgressJournal' -and
        $wrapper -match 'progress_last_phase = \$progress\.last_phase' -and
        $wrapper -match 'inner_trace_preserved = Test-Path'
    preexisting_hwp_rejected = $all -match 'PREEXISTING_HWP_PROCESS'
    preflight_fails_before_com = Test-PreflightFailure
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    user_ui_not_computer_use = $worker -match 'computer_use_click_or_type_invoked = \$false' -and
        $worker -match 'window_visible_for_user_access = \$true'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-number-format-source-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
