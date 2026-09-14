[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-automation-v2-surface-child.ps1'
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
    complete_coverage = $source -match '@\(\$overlay\.bindings\)\.Count -ne 61' -and
        $source -match '\[ValidateRange\(1, 61\)\]\[int\]\$StartIndex' -and
        $source -match '\[ValidateRange\(1, 61\)\]\[int\]\$EndIndex' -and
        $source -match '\$EndIndex - \$StartIndex \+ 1'
    surface_only = $source -match '\$hwp\.IsActionEnable' -and
        $source -match '\$hwp\.CreateAction' -and
        $source -match '\$action\.GetDefault' -and
        $source -notmatch '\$action\.Execute\('
    disposable_only = $source -match '\$documents\.Add\(\$false\)' -and
        $source -notmatch '(?i)\.Open\s*\(' -and
        $source -notmatch '(?i)\.SaveAs\s*\('
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
    schema_version = 'hwpx-agent.p06-09-table-automation-v2-surface-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
