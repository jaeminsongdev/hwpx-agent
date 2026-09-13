[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\validate-hancom-2020-table-chart-product.ps1'
)).Path
$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-chart-product.ps1'
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

function Test-PreflightRejectsWrongInputDigest {
    $temporaryRoot = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::GetTempPath()
    ).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-chart-product-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $input = Join-Path $directory 'input.hwpx'
    $output = Join-Path $directory 'output.hwpx'
    $pdf = Join-Path $directory 'render.pdf'
    $trace = Join-Path $directory 'trace.json'
    [System.IO.File]::WriteAllBytes($input, [byte[]](1, 2, 3, 4))
    $observed = $null
    try {
        & $wrapperPath -InputPath $input -ExpectedInputSha256 ('0' * 64) `
            -OutputPath $output -PdfPath $pdf -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $pdf, $output, $input)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        $resolved = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($resolved) -and
            $resolved.StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-chart-product-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($resolved, $false)
        }
    }
    return $observed -ceq 'TABLE_CHART_PRODUCT_INPUT_INVALID'
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
        'hwpx-agent-p06-chart-product-progress-' +
            [guid]::NewGuid().ToString('N') + '.jsonl'
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
        'hwpx-agent\.p06-09-hancom-2020-table-chart-product/v1' -and
        $worker -match
            'hwpx-agent\.p06-09-hancom-2020-table-chart-product-progress/v1' -and
        $wrapper -match
            'hwpx-agent\.p06-09-hancom-2020-table-chart-product-watchdog/v1'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    immutable_hash_bound_input = $all -match 'ExpectedInputSha256' -and
        $all -match 'INPUT_DIGEST_MISMATCH' -and
        $wrapper -match 'TABLE_CHART_PRODUCT_INPUT_INVALID'
    separate_create_new_outputs = $worker -match
        '\[System\.IO\.FileMode\]::CreateNew' -and
        $all -match 'OUTPUT_ALREADY_EXISTS|OUTPUT_ALREADY_EXISTS' -and
        $worker -match '\$document\.SaveAs\(\$output' -and
        $worker -match '\$document\.SaveAs\(\$pdf'
    actual_open_save_reopen = $worker -match
        '\$document\.Open\(\$input, ''HWPX''' -and
        $worker -match '\$document\.Open\(\$output, ''HWPX''' -and
        $worker -match '\$trace\.actual_hwpx_save_reopen = \$true'
    source_text_preservation = $worker -match 'Assert-VisibleSourceText' -and
        $worker -match '\$trace\.source_text_preserved' -and
        $worker -match 'SAVED_VISIBLE_TEXT_DRIFT'
    pdf_is_export_only_until_reviewed = $worker -match
        '\$trace\.actual_pdf_export = \$true' -and
        $worker -match 'render_visual_verified = \$false' -and
        $worker -match 'user_attested_visual = \$false'
    differential_not_promoted = $worker -match
        'automation_differential = ''not_run''' -and
        $wrapper -match
            '\[string\]\$trace\.automation_differential -ceq ''not_run'''
    redacted_receipt = $all -match 'raw_document_text_present = \$false' -and
        $all -match 'raw_chart_payload_present = \$false' -and
        $worker -match 'exception_message_sha256'
    bounded_watchdog = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $wrapper -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $wrapper -match 'Stop-OwnedHancomProcess' -and
        $wrapper -match
            '\[int\]\$candidate\.ProcessId -eq \[int\]\$ExpectedProcessId' -and
        $wrapper -match '\$progress\.worker_process_id -eq \[long\]\$child\.Id'
    exact_owned_process_binding = $worker -match
        'HWP_PROCESS_OWNERSHIP_MISMATCH' -and
        $worker -match '\$processCreatedAt -lt \$comStartedAt\.AddSeconds\(-2\)' -and
        $worker -match '\[int\]\$process\.SessionId -ne \$sessionId' -and
        $wrapper -match '\[bool\]\$trace\.hwp_process_identity_bound'
    progress_journal = $wrapper -match 'Read-ProgressJournal' -and
        $wrapper -match 'progress_last_phase = \$progress\.last_phase' -and
        $wrapper -match 'inner_trace_preserved = Test-Path'
    progress_null_roundtrip = Test-ProgressNullRoundTrip
    wrong_digest_fails_before_com = Test-PreflightRejectsWrongInputDigest
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
    schema_version = 'hwpx-agent.p06-09-table-chart-product-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
