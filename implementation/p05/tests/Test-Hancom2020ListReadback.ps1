[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-list-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-tab-readback.ps1'
)).Path
$boundedPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\invoke-hancom-2020-bounded-readback.ps1'
)).Path
$wrapperTokens = $null
$wrapperErrors = $null
$engineTokens = $null
$engineErrors = $null
$boundedTokens = $null
$boundedErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $wrapperPath,
    [ref]$wrapperTokens,
    [ref]$wrapperErrors
)
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $enginePath,
    [ref]$engineTokens,
    [ref]$engineErrors
)
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $boundedPath,
    [ref]$boundedTokens,
    [ref]$boundedErrors
)
$wrapper = [System.IO.File]::ReadAllText($wrapperPath)
$engine = [System.IO.File]::ReadAllText($enginePath)
$bounded = [System.IO.File]::ReadAllText($boundedPath)
$checks = [ordered]@{
    wrapper_parses = $wrapperErrors.Count -eq 0
    bounded_runner_parses = $boundedErrors.Count -eq 0
    delegated_engine_parses = $engineErrors.Count -eq 0
    typed_trace_schema = $wrapper -match 'hwpx-agent\.p05-05-hancom-2020-list-readback/v1'
    delegated_schema_recorded = $bounded -match 'delegated_engine_schema'
    exact_progid = $engine -match 'HWPFrame\.HwpObject\.2'
    exact_build = $engine -match '11\.0\.0\.9136'
    exact_executable = $engine -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    registry32 = $engine -match 'RegistryView\]::Registry32'
    sta_required = $engine -match 'TAB_READBACK_CLIENT_NOT_STA'
    fixed_input_hash = $engine -match 'TAB_READBACK_INPUT_SHA256_MISMATCH'
    create_new_trace = $bounded -match 'FileMode\]::CreateNew'
    output_no_overwrite = $engine -match 'TAB_READBACK_OUTPUT_ALREADY_EXISTS'
    save_as_hwpx = $engine -match "SaveAs\(\`$output, 'HWPX', ''\)"
    reopen_output = $engine -match "Open\(\`$output, 'HWPX', 'lock:false;setcurdir:false'\)"
    input_and_output_text_hash = $engine -match 'TAB_READBACK_OUTPUT_TEXT_MISMATCH'
    input_unchanged = $engine -match 'TAB_READBACK_INPUT_CHANGED'
    privacy_marker = $engine -match 'raw_document_text_present = \$false'
    visible_for_user_access = $engine -match '\$window\.Visible = \$true'
    progress_journal = $engine -match 'hwpx-agent\.p05-hancom-readback-progress/v1'
    bounded_timeout = $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    exact_owned_cleanup = $bounded -match "-Automation\\s\+\-Embedding" -and $bounded -match 'ExpectedSha256'
    no_register_module = $engine -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = ($wrapper + $bounded + $engine) -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = ($wrapper + $bounded + $engine) -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = ($wrapper + $bounded + $engine) -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
    bounded_inner_delete = $bounded -match '\[System\.IO\.File\]::Delete\(\$innerTrace\)'
}
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p05-05-list-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
