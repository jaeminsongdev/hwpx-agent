[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-automation-v2-runtime-child.ps1'
)).Path
$tokens = $null
$errors = $null
[void][Management.Automation.Language.Parser]::ParseFile(
    $scriptPath, [ref]$tokens, [ref]$errors
)
$source = [IO.File]::ReadAllText($scriptPath)
$checks = [ordered]@{
    parses = $errors.Count -eq 0
    exact_target = $source -match 'HWPFrame\.HwpObject\.2' -and
        $source -match '11\.0\.0\.9136' -and
        $source -match 'REQUIRES_X86_STA'
    complete_range = $source -match '@\(\$overlay\.bindings\)\.Count -ne 61' -and
        $source -match '\[ValidateRange\(1, 61\)\]\[int\]\$StartIndex' -and
        $source -match '\[ValidateRange\(1, 61\)\]\[int\]\$EndIndex'
    in_memory_snapshot = $source -match "GetTextFile\('HWPML2X', ''\)" -and
        $source -match "snapshot_transport = 'in_memory_hwpml2x'"
    no_file_open_or_save = $source -notmatch '(?i)\.Open\s*\(' -and
        $source -notmatch '(?i)\.SaveAs\s*\(' -and
        $source -match 'file_open_or_save_invoked = \$false'
    discard_rollback = $source -match '\$document\.Close\(\$false\)' -and
        $source -match "rollback_mode = 'discard_unsaved_disposable_document'" -and
        $source -match "rollback_state = 'pass'"
    candidate_execution = $source -match 'Invoke-Candidate' -and
        $source -match 'semantic_effect_observed' -and
        $source -match 'candidate_action_execute_count'
    no_ui_input = $source -notmatch
        '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $source -notmatch
        '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $source -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty|RegisterModule)'
    create_new_trace = $source -match '\[IO\.FileMode\]::CreateNew'
}
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-v2-runtime-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
