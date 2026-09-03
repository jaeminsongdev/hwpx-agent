[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$boundedPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\invoke-hancom-2020-bounded-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-tab-readback.ps1'
)).Path
$sectionPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-section-columns-readback.ps1'
)).Path
$headerPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-header-footer-readback.ps1'
)).Path

$sources = [ordered]@{}
foreach ($path in @($boundedPath, $enginePath, $sectionPath, $headerPath)) {
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

$bounded = [string]$sources[$boundedPath].content
$engine = [string]$sources[$enginePath].content
$section = [string]$sources[$sectionPath].content
$header = [string]$sources[$headerPath].content
$all = $bounded + $engine + $section + $header

function Test-RenderPreflightFailure {
    param(
        [Parameter(Mandatory)][ValidateSet('bad_extension', 'outside_boundary')][string]$Case,
        [Parameter(Mandatory)][string]$ExpectedError
    )

    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    $directory = Join-Path $temporaryRoot ('hwpx-agent-render-preflight-' + [guid]::NewGuid().ToString('N'))
    [void][System.IO.Directory]::CreateDirectory($directory)
    $fixturePath = Join-Path $directory 'input.hwpx'
    $output = Join-Path $directory 'output.hwpx'
    $trace = Join-Path $directory 'trace.json'
    [System.IO.File]::WriteAllBytes($fixturePath, [byte[]]@(1, 2, 3, 4))
    $render = if ($Case -ceq 'bad_extension') {
        Join-Path $directory 'render.txt'
    }
    else { Join-Path $temporaryRoot ('outside-' + [guid]::NewGuid().ToString('N') + '.pdf') }
    $observed = $null
    try {
        & $boundedPath `
            -InputPath $fixturePath `
            -ExpectedInputSha256 ((Get-FileHash -LiteralPath $fixturePath -Algorithm SHA256).Hash.ToLowerInvariant()) `
            -OutputPath $output `
            -TracePath $trace `
            -ExpectedTextSha256 ('0' * 64) `
            -TraceSchema 'hwpx-agent.p05-render-preflight/v1' `
            -ErrorPrefix 'RENDER_PREFLIGHT' `
            -RenderPdfPath $render | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        $cleanupPaths = @(
            ($trace + '.progress.jsonl'),
            $trace,
            $output,
            $fixturePath
        )
        foreach ($cleanupPath in $cleanupPaths) {
            if ([System.IO.File]::Exists($cleanupPath)) { [System.IO.File]::Delete($cleanupPath) }
        }
        if ([System.IO.Path]::GetFullPath($directory).StartsWith(
            $temporaryRoot + '\hwpx-agent-render-preflight-',
            [System.StringComparison]::OrdinalIgnoreCase
        ) -and [System.IO.Directory]::Exists($directory)) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq $ExpectedError
}

$badExtensionFailsClosed = Test-RenderPreflightFailure `
    -Case 'bad_extension' `
    -ExpectedError 'RENDER_PREFLIGHT_PDF_EXTENSION_REQUIRED'
$outsideBoundaryFailsClosed = Test-RenderPreflightFailure `
    -Case 'outside_boundary' `
    -ExpectedError 'RENDER_PREFLIGHT_PATH_OUTSIDE_FIXTURE_BOUNDARY'

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    optional_render_parameter = $bounded -match "\[string\]\`$RenderPdfPath = ''" -and $engine -match "\[string\]\`$RenderPdfPath = ''"
    layout_wrappers_forward_render = $section -match '-RenderPdfPath \$RenderPdfPath' -and $header -match '-RenderPdfPath \$RenderPdfPath'
    render_argument_only_when_requested = $bounded -match '(?s)if \(\$null -ne \$renderPdf\).*?\$arguments \+= @\(''-RenderPdfPath'', \$renderPdf\)'
    render_path_inside_fixture_boundary = $bounded -match 'progressFile, \$renderPdf' -and $engine -match 'progressFile, \$renderPdf'
    pdf_extension_required = $bounded -match "GetExtension\(\`$renderPdf\) -cne '\.pdf'" -and $engine -match "GetExtension\(\`$renderPdf\) -cne '\.pdf'"
    render_output_no_overwrite = $bounded -match 'Test-Path -LiteralPath \$candidate' -and $engine -match 'Test-Path -LiteralPath \$renderPdf'
    official_save_as_pdf = $engine -match "SaveAs\(\`$renderPdf, 'PDF', ''\)" -and $engine -match 'IXHwpDocument\.SaveAs/PDF'
    bounded_pdf_regular_file = $engine -match 'PDF_NOT_BOUNDED_REGULAR_FILE' -and $engine -match 'Length -gt 33554432'
    pdf_reparse_refused = $engine -match 'FileAttributes\]::ReparsePoint'
    pdf_signature_checked = $engine -match "GetString\(\`$signature\) -cne '%PDF-'"
    pdf_digest_recorded = $engine -match 'render_pdf_sha256 = Get-Sha256File -Path \$renderPdf'
    pdf_length_recorded = $engine -match 'render_pdf_bytes = \[long\]\$pdfItem\.Length'
    render_phase_journaled = $engine -match "\`$phase = 'export_pdf'" -and $bounded -match "'export_pdf'"
    wrapper_requires_exact_render_fields = $bounded -match "'render_pdf_bytes', 'render_pdf_signature_valid', 'render_pdf_export_method'" -and $bounded -match 'PSObject\.Properties\.Name.*cnotcontains \$property'
    wrapper_requires_exact_render_types = $bounded -match 'render_pdf_requested -is \[bool\]' -and $bounded -match 'render_pdf_bytes -is \[long\]'
    wrapper_rechecks_pdf_regular_file = $bounded -match 'Test-BoundedPdfEvidence' -and $bounded -match 'item\.Attributes.*ReparsePoint'
    wrapper_rechecks_pdf_length = $bounded -match 'item\.Length -ne \[long\]\$Trace\.render_pdf_bytes'
    wrapper_rechecks_pdf_signature = $bounded -match "GetString\(\`$signature\) -cne '%PDF-'"
    wrapper_correlates_pdf_digest = $bounded -match 'Get-Sha256File -Path \$Path.*Trace\.render_pdf_sha256'
    timeout_trace_does_not_claim_render_pass = $bounded -match 'render_pdf_sha256 = \$null' -and $bounded -match 'render_pdf_signature_valid = \$false'
    bad_pdf_extension_fails_before_com = $badExtensionFailsClosed
    outside_pdf_path_fails_before_com = $outsideBoundaryFailsClosed
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p05-render-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
