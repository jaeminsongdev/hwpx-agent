[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-tab-readback.ps1'
)).Path
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $scriptPath,
    [ref]$tokens,
    [ref]$parseErrors
)
$source = [System.IO.File]::ReadAllText($scriptPath)
$checks = [ordered]@{
    parses = $parseErrors.Count -eq 0
    exact_progid = $source -match 'HWPFrame\.HwpObject\.2'
    exact_build = $source -match '11\.0\.0\.9136'
    exact_executable = $source -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    registry32 = $source -match 'RegistryView\]::Registry32'
    sta_required = $source -match 'TAB_READBACK_CLIENT_NOT_STA'
    fixed_input_hash = $source -match 'TAB_READBACK_INPUT_SHA256_MISMATCH'
    create_new_trace = $source -match 'FileMode\]::CreateNew'
    output_no_overwrite = $source -match 'TAB_READBACK_OUTPUT_ALREADY_EXISTS'
    save_as_hwpx = $source -match "SaveAs\(\`$output, 'HWPX', ''\)"
    reopen_output = $source -match "Open\(\`$output, 'HWPX', 'lock:false;setcurdir:false'\)"
    input_and_output_text_hash = $source -match 'TAB_READBACK_OUTPUT_TEXT_MISMATCH'
    input_unchanged = $source -match 'TAB_READBACK_INPUT_CHANGED'
    privacy_marker = $source -match 'raw_document_text_present = \$false'
    visible_for_user_access = $source -match '\$window\.Visible = \$true'
    progress_journal = $source -match 'hwpx-agent\.p05-hancom-readback-progress/v1'
    progress_has_no_text_value = $source -match 'raw_document_text_present = \$false'
    no_register_module = $source -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $source -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $source -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $source -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p05-04-tab-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
