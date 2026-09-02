[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$parent = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-roundtrip-oracle.ps1')).Path
$child = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-roundtrip-oracle-child.ps1')).Path
$results = @()

function Add-Result {
    param([string]$Case, [bool]$Passed, [AllowNull()][string]$Detail)

    $script:results += [pscustomobject]@{
        case = $Case
        passed = $Passed
        detail = $Detail
    }
}

foreach ($path in @($parent, $child)) {
    $tokens = $null
    $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref]$tokens,
        [ref]$parseErrors
    )
    $parseDetail = if ($parseErrors.Count -eq 0) { $null } else { [string]$parseErrors[0].Message }
    Add-Result `
        -Case ('parse_' + [System.IO.Path]::GetFileName($path)) `
        -Passed ($parseErrors.Count -eq 0) `
        -Detail $parseDetail
}

$parentSource = [System.IO.File]::ReadAllText($parent)
$childSource = [System.IO.File]::ReadAllText($child)
$combined = $parentSource + "`n" + $childSource
$required = [ordered]@{
    exact_build = '11\.0\.0\.9136'
    exact_executable_sha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    exact_progid = 'HWPFrame\.HwpObject\.2'
    registry32 = 'RegistryView\]::Registry32'
    x86_shell = 'SysWOW64\\WindowsPowerShell'
    sta_child = "'-STA'"
    preexisting_process_refusal = 'ROUNDTRIP_ORACLE_PREEXISTING_HWP_PROCESS'
    bounded_timeout = 'ValidateRange\(30, 300\)'
    fixed_fixture_zero_preserving = 'fixture-0\\preserving\.hwpx'
    fixed_fixture_zero_normalized = 'fixture-0\\normalized\.hwpx'
    fixed_fixture_one_preserving = 'fixture-1\\preserving\.hwpx'
    fixed_fixture_one_normalized = 'fixture-1\\normalized\.hwpx'
    corpus_manifest_pin = 'ExpectedCorpusManifestSha256'
    reparse_refusal = 'ROUNDTRIP_ORACLE_REPARSE_POINT_REFUSED'
    input_hash_pin = 'ROUNDTRIP_ORACLE_INPUT_SHA256_MISMATCH'
    managed_stream_hash = 'SHA256\]::Create\(\)'
    create_new_receipt = 'FileMode\]::CreateNew'
    open_read_only_intent = "\.Open\(\`$resolvedInputPath, 'HWPX', 'lock:false;setcurdir:false'\)"
    unicode_text_read = "GetTextFile\('UNICODE', ''\)"
    semantic_pair_equality = 'preserving_and_normalized_text_equal'
    exact_owned_cleanup = 'safeToClean'
    no_overwrite = 'ROUNDTRIP_ORACLE_OUTPUT_ALREADY_EXISTS'
    privacy_no_raw_text = 'raw_document_text_present = \$false'
    computer_use_no_input = 'computer_use_click_or_type_invoked = \$false'
}
foreach ($entry in $required.GetEnumerator()) {
    Add-Result `
        -Case $entry.Key `
        -Passed ([regex]::IsMatch($combined, $entry.Value)) `
        -Detail $entry.Value
}

$forbidden = [ordered]@{
    no_register_module = '(?i)\.RegisterModule\s*\('
    no_save_or_save_as = '(?i)\.(Save|SaveAs)\s*\('
    no_registry_write = '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
    no_network_cmdlet = '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_user_document_scan = '(?i)(Get-ChildItem|Resolve-Path).*?(Documents|Desktop|OneDrive)'
    no_ui_input = '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_visible_toggle = '(?i)\.Visible\s*='
    no_recursive_enumeration = '(?i)Get-ChildItem[^\r\n]*-Recurse'
    no_module_autoload_hash = '(?i)Get-FileHash'
}
foreach ($entry in $forbidden.GetEnumerator()) {
    Add-Result `
        -Case $entry.Key `
        -Passed (-not [regex]::IsMatch($combined, $entry.Value)) `
        -Detail $entry.Value
}

$hwpCount = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count
Add-Result `
    -Case 'static_tests_leave_no_hwp_process' `
    -Passed ($hwpCount -eq 0) `
    -Detail "count=$hwpCount"

$failed = @($results | Where-Object { -not $_.passed })
[ordered]@{
    schema_version = 'hwpx-agent.hancom-2020-roundtrip-static-tests/v1'
    total = $results.Count
    passed = $results.Count - $failed.Count
    failed = $failed.Count
    cases = @($results)
} | ConvertTo-Json -Depth 6
if ($failed.Count -ne 0) { exit 1 }
