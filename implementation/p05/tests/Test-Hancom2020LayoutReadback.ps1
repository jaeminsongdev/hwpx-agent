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
$caseDefinitions = @(
    [ordered]@{
        name = 'section_columns'
        path = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-section-columns-readback.ps1')).Path
        schema = 'hwpx-agent\.p05-07-hancom-2020-section-columns-readback/v1'
        prefix = 'SECTION_COLUMNS_READBACK'
    },
    [ordered]@{
        name = 'header_footer'
        path = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-header-footer-readback.ps1')).Path
        schema = 'hwpx-agent\.p05-08-hancom-2020-header-footer-readback/v1'
        prefix = 'HEADER_FOOTER_READBACK'
    },
    [ordered]@{
        name = 'vs1_layout'
        path = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-vs1-layout-readback.ps1')).Path
        schema = 'hwpx-agent\.p05-09-hancom-2020-vs1-layout-readback/v1'
        prefix = 'VS1_LAYOUT_READBACK'
    }
)
$bounded = [System.IO.File]::ReadAllText($boundedPath)
$engine = [System.IO.File]::ReadAllText($enginePath)
$cases = @()
foreach ($definition in $caseDefinitions) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        [string]$definition.path, [ref]$tokens, [ref]$errors
    )
    $wrapper = [System.IO.File]::ReadAllText([string]$definition.path)
    $checks = [ordered]@{
        parses = $errors.Count -eq 0
        typed_schema = $wrapper -match [string]$definition.schema
        error_prefix = $wrapper -match [string]$definition.prefix
        bounded_delegate = $wrapper -match 'invoke-hancom-2020-bounded-readback\.ps1'
        exact_identity = $wrapper -match '11\.0\.0\.9136' -and $wrapper -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
        timeout = $wrapper -match 'TimeoutSeconds' -and $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
        progress = $engine -match 'hwpx-agent\.p05-hancom-readback-progress/v1'
        no_ui_input = ($wrapper + $bounded + $engine) -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
        no_network = ($wrapper + $bounded + $engine) -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
        no_registry_write = ($wrapper + $bounded + $engine) -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
    }
    foreach ($check in $checks.GetEnumerator()) {
        $cases += [ordered]@{
            case = ([string]$definition.name + '.' + [string]$check.Key)
            passed = [bool]$check.Value
        }
    }
}
$failed = @($cases | Where-Object { -not $_.passed })
[ordered]@{
    schema_version = 'hwpx-agent.p05-layout-readback-static-tests/v1'
    total = $cases.Count
    passed = $cases.Count - $failed.Count
    failed = $failed.Count
    cases = $cases
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
