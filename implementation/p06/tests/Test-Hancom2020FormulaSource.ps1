[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\create-hancom-2020-formula-source.ps1'
)).Path
$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-formula-source.ps1'
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
    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-formula-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $output = Join-Path $directory 'source.txt'
    $pdf = Join-Path $directory 'source.pdf'
    $trace = Join-Path $directory 'trace.json'
    $observed = $null
    try {
        & $wrapperPath -OutputPath $output -PdfPath $pdf -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $pdf, $output)) {
            if ([System.IO.File]::Exists($candidate)) { [System.IO.File]::Delete($candidate) }
        }
        if ([System.IO.Directory]::Exists($directory) -and
            [System.IO.Path]::GetFullPath($directory).StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-formula-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq 'FORMULA_SOURCE_OUTPUT_EXTENSION_INVALID'
}

$checks = [ordered]@{
    scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_schema = $worker -match 'hwpx-agent\.p06-06-hancom-2020-formula-source/v1' -and
        $wrapper -match 'hwpx-agent\.p06-06-hancom-2020-formula-source-watchdog/v1'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    active_document_bound = $worker -match '\$document\.SetActive_XHwpDocument\(\)' -and
        $worker -match 'active_document_bound = \$true'
    exact_source_grid = $worker -match '\$creation\.Rows = 1' -and
        $worker -match '\$creation\.Cols = 3'
    exact_operands = $worker -match 'Write-ExactText -Hwp \$hwp -Text ''17''' -and
        $worker -match 'Write-ExactText -Hwp \$hwp -Text ''25'''
    hancom_authors_formula = $worker -match 'Invoke-ActionRun -Hwp \$hwp -Action ''TableFormulaSumHor'''
    no_guessed_formula_command = $all -notmatch '(?i)HFieldCtrl|\.Command\s*=|\?\?|LastResult|ResultFormat'
    pre_save_semantic = $worker -match '\$phase = ''pre_save_semantic''' -and
        $worker -match 'Assert-FormulaVisibleText -Text \$preSaveText' -and
        $worker -match 'pre_save_visible_formula = \$true'
    save_reopen_semantic = $worker -match '\$phase = ''reopen_hwpx''' -and
        $worker -match 'Assert-FormulaVisibleText -Text \$reopenText' -and
        $worker -match 'reopen_visible_formula = \$true'
    output_digests_only = $worker -match 'output_hwpx_sha256' -and
        $worker -match 'output_pdf_sha256' -and
        $all -match 'raw_formula_or_command_present = \$false'
    bounded_watchdog = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $wrapper -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $wrapper -match 'Stop-OwnedHancomProcess'
    exact_success_receipt = $wrapper -match '\$successSemanticsValid' -and
        $wrapper -match '\[long\]\$trace\.operand_cells_written -eq 2' -and
        $wrapper -match '\$trace\.reopen_text_sha256 -ceq \[string\]\$trace\.pre_save_text_sha256'
    progress_journal = $worker -match 'hwpx-agent\.p06-06-hancom-2020-formula-progress/v1' -and
        $wrapper -match 'Read-ProgressJournal' -and
        $wrapper -match 'progress_last_phase = \$progress\.last_phase'
    pdf_signature = $all -match "'%PDF-'"
    preexisting_hwp_rejected = $all -match 'PREEXISTING_HWP_PROCESS'
    preflight_fails_before_com = Test-PreflightFailure
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-06-formula-source-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
