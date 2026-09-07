[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-formula-target-readback.ps1'
)).Path
$boundedPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\p05\tools\invoke-hancom-2020-bounded-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\p05\tools\run-hancom-2020-tab-readback.ps1'
)).Path

$sources = [ordered]@{}
foreach ($path in @($wrapperPath, $boundedPath, $enginePath)) {
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

$wrapper = [string]$sources[$wrapperPath].content
$bounded = [string]$sources[$boundedPath].content
$engine = [string]$sources[$enginePath].content
$all = $wrapper + $bounded + $engine

function Test-PreflightFailure {
    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-formula-target-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $input = Join-Path $directory 'input.hwpx'
    $output = Join-Path $directory 'output.txt'
    $trace = Join-Path $directory 'trace.json'
    $pdf = Join-Path $directory 'render.pdf'
    [System.IO.File]::WriteAllBytes($input, [byte[]]@(1, 2, 3, 4))
    $observed = $null
    try {
        & $wrapperPath `
            -InputPath $input `
            -ExpectedInputSha256 ((
                Get-FileHash -LiteralPath $input -Algorithm SHA256
            ).Hash.ToLowerInvariant()) `
            -OutputPath $output `
            -TracePath $trace `
            -ExpectedTextSha256 ('0' * 64) `
            -RenderPdfPath $pdf | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($pdf, $trace, $output, $input)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        if ([System.IO.Directory]::Exists($directory) -and
            [System.IO.Path]::GetFullPath($directory).StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-formula-target-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq 'TABLE_FORMULA_TARGET_READBACK_HWPX_EXTENSION_REQUIRED'
}

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_schema = $wrapper -match 'hwpx-agent\.p06-06-hancom-2020-formula-target-readback/v1'
    exact_error_prefix = $wrapper -match "ErrorPrefix 'TABLE_FORMULA_TARGET_READBACK'"
    bounded_delegate = $wrapper -match 'invoke-hancom-2020-bounded-readback\.ps1'
    exact_target = $wrapper -match 'HWPFrame\.HwpObject\.2' -and
        $wrapper -match '11\.0\.0\.9136' -and
        $wrapper -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    finite_timeout = $wrapper -match 'ValidateRange\(30, 900\)' -and
        $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    exact_input_and_text_digests_forwarded =
        $wrapper -match '-ExpectedInputSha256 \$ExpectedInputSha256' -and
        $wrapper -match '-ExpectedTextSha256 \$ExpectedTextSha256'
    render_forwarded = $wrapper -match '-RenderPdfPath \$RenderPdfPath'
    exact_lifecycle = $engine -match "phase = 'open_input'" -and
        $engine -match "phase = 'save_as_hwpx'" -and
        $engine -match "phase = 'reopen_output'" -and
        $engine -match "phase = 'export_pdf'"
    input_immutability = $engine -match 'TAB_READBACK_INPUT_CHANGED'
    progress_journal = $engine -match 'hwpx-agent\.p05-hancom-readback-progress/v1'
    process_cleanup = $bounded -match 'Stop-OwnedHancomProcesses' -and
        $bounded -match 'remaining_hwp_process_count'
    preflight_fails_before_com = Test-PreflightFailure
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-06-formula-target-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
