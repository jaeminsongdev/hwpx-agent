[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$parentScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-document-smoke.ps1')).Path
$childScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-document-smoke-child.ps1')).Path
$schemaPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\schemas\document-smoke-receipt.schema.json')).Path
$systemPowerShell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'

$results = @()
function Add-TestResult {
    param(
        [Parameter(Mandatory)][string]$Case,
        [Parameter(Mandatory)][bool]$Passed,
        [AllowNull()][string]$Detail
    )
    $script:results += [pscustomobject]@{
        case = $Case
        passed = $Passed
        detail = $Detail
    }
}

foreach ($scriptPath in @($parentScript, $childScript)) {
    $tokens = $null
    $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $scriptPath,
        [ref]$tokens,
        [ref]$parseErrors
    )
    $parseDetail = if ($parseErrors.Count -eq 0) { $null } else { [string]$parseErrors[0].Message }
    Add-TestResult -Case ('parse_' + [System.IO.Path]::GetFileName($scriptPath)) -Passed ($parseErrors.Count -eq 0) -Detail $parseDetail
}

$parentSource = [System.IO.File]::ReadAllText($parentScript)
$childSource = [System.IO.File]::ReadAllText($childScript)
$combinedSource = $parentSource + "`n" + $childSource

$requiredParentPatterns = [ordered]@{
    parent_exact_prog_id = [regex]::Escape('HWPFrame.HwpObject.2')
    parent_exact_build = [regex]::Escape('11.0.0.9136')
    parent_exact_hash = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    parent_registry32 = 'RegistryView\]::Registry32'
    parent_x86_shell = 'SysWOW64\\WindowsPowerShell'
    parent_sta_child = "'-STA'"
    parent_preexisting_process_guard = 'Refusing document smoke because an Hwp process is already running'
    parent_output_boundary = 'document-smoke-runs'
    parent_non_clean_label = 'non_clean_development_reference'
}
foreach ($entry in $requiredParentPatterns.GetEnumerator()) {
    Add-TestResult -Case $entry.Key -Passed ([regex]::IsMatch($parentSource, $entry.Value)) -Detail $entry.Value
}

$requiredChildPatterns = [ordered]@{
    child_add_document = '\.Add\(\$false\)'
    child_insert_text_allowlist = "Execute\('InsertText'"
    child_save_hwpx = 'SaveAs\(\$hwpxPath, ''HWPX'''
    child_reopen_hwpx = 'Open\(\$hwpxPath, ''HWPX'''
    child_unicode_readback = "GetTextFile\('UNICODE'"
    child_export_pdf = 'SaveAs\(\$pdfPath, ''PDF'''
    child_close_without_prompt = '\.Close\(\$false\)'
    child_quit = '\.Quit\(\)'
}
foreach ($entry in $requiredChildPatterns.GetEnumerator()) {
    Add-TestResult -Case $entry.Key -Passed ([regex]::IsMatch($childSource, $entry.Value)) -Detail $entry.Value
}

$forbiddenPatterns = [ordered]@{
    no_register_module_call = '(?i)\.RegisterModule\s*\('
    no_registry_write = '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
    no_network_cmdlet = '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_user_profile_document_scan = '(?i)(Get-ChildItem|Resolve-Path).*?(Documents|Desktop|OneDrive)'
    no_window_visibility_mutation = '(?i)\.Visible\s*='
}
foreach ($entry in $forbiddenPatterns.GetEnumerator()) {
    Add-TestResult -Case $entry.Key -Passed (-not [regex]::IsMatch($combinedSource, $entry.Value)) -Detail $entry.Value
}

try {
    $schema = Get-Content -LiteralPath $schemaPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Add-TestResult -Case 'schema_json_parse' -Passed ($schema.'$schema' -eq 'https://json-schema.org/draft/2020-12/schema') -Detail $null
}
catch {
    Add-TestResult -Case 'schema_json_parse' -Passed $false -Detail $_.Exception.GetType().FullName
}

$configOutput = & $systemPowerShell -NoProfile -NonInteractive -File $parentScript -ValidateConfigurationOnly 2>&1 | Out-String
$configExitCode = $LASTEXITCODE
$configResult = $null
try { $configResult = $configOutput | ConvertFrom-Json } catch { }
Add-TestResult -Case 'configuration_only_passes_without_com_activation' -Passed (
    $configExitCode -eq 0 -and
    $null -ne $configResult -and
    $configResult.state -eq 'pass' -and
    $configResult.document_or_com_opened -eq $false
) -Detail ("exit=$configExitCode")

$outsideRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('hwpx-agent-outside-boundary-' + [guid]::NewGuid().ToString('N'))
$savedErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    $negativeOutput = & $systemPowerShell -NoProfile -NonInteractive -File $parentScript -ValidateConfigurationOnly -OutputRoot $outsideRoot 2>&1 | Out-String
    $negativeExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $savedErrorActionPreference
}
Add-TestResult -Case 'outside_output_root_fail_closed' -Passed (
    $negativeExitCode -ne 0 -and
    $negativeOutput -match 'OUTPUT_ROOT_OUTSIDE_ALLOWED_BOUNDARY' -and
    -not (Test-Path -LiteralPath $outsideRoot)
) -Detail ("exit=$negativeExitCode")

$hwpCount = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count
Add-TestResult -Case 'static_tests_leave_no_hwp_process' -Passed ($hwpCount -eq 0) -Detail ("count=$hwpCount")

$failed = @($results | Where-Object { -not $_.passed })
[ordered]@{
    schema_version = 'hwpx-agent.hancom-document-smoke-tests/v1'
    total = $results.Count
    passed = $results.Count - $failed.Count
    failed = $failed.Count
    cases = @($results)
} | ConvertTo-Json -Depth 7

if ($failed.Count -ne 0) {
    exit 1
}
