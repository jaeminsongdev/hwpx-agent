[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$parent = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-runtime-probe.ps1')).Path
$child = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\tools\run-hancom-2020-runtime-probe-child.ps1')).Path
$results = @()
function Add-Result {
    param([string]$Case, [bool]$Passed, [AllowNull()][string]$Detail)
    $script:results += [pscustomobject]@{ case = $Case; passed = $Passed; detail = $Detail }
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
    Add-Result -Case ('parse_' + [System.IO.Path]::GetFileName($path)) -Passed ($parseErrors.Count -eq 0) -Detail $parseDetail
}

$parentSource = [System.IO.File]::ReadAllText($parent)
$childSource = [System.IO.File]::ReadAllText($child)
$combined = $parentSource + "`n" + $childSource
$required = [ordered]@{
    exact_build = '11\.0\.0\.9136'
    exact_executable_sha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    registry32 = 'RegistryView\]::Registry32'
    x86_shell = 'SysWOW64\\WindowsPowerShell'
    sta_child = "'-STA'"
    preexisting_process_refusal = 'RUNTIME_PROBE_PREEXISTING_HWP_PROCESS'
    private_output_boundary = 'evidence\\runtime-probes'
    unexpected_window_policy = 'unexpectedWindowObserved'
    exact_cleanup_identity = 'safeToClean'
    undo_allowlist = "'edit\.undo'"
    redo_allowlist = "'edit\.redo'"
    default_read_allowlist = "'edit\.go_to'"
    powershell_com_adapter_first = 'return \$ComObject\.\$Name'
    idispatch_callbyname_fallback = 'Interaction\]::CallByName'
    bounded_parameter_alias = 'documented_plus_e'
    visible_window_check = 'IsWindowVisible'
    no_overwrite = 'RUNTIME_PROBE_OUTPUT_ALREADY_EXISTS'
    semantic_reopen = 'reopen_exact_match'
    null_document_is_empty = 'return \[string\]::Empty'
    empty_undo_direct_assignment = 'IsNullOrEmpty\(\$undoRaw\)'
    empty_byte_hash_allowed = 'AllowEmptyCollection\(\)'
}
foreach ($entry in $required.GetEnumerator()) {
    Add-Result -Case $entry.Key -Passed ([regex]::IsMatch($combined, $entry.Value)) -Detail $entry.Value
}

$forbidden = [ordered]@{
    no_register_module = '(?i)\.RegisterModule\s*\('
    no_registry_write = '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
    no_network_cmdlet = '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_user_document_scan = '(?i)(Get-ChildItem|Resolve-Path).*?(Documents|Desktop|OneDrive)'
    no_ui_input = '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_print_capability_execution = "HAction\.(Run|Execute)\([^\r\n]*file\.print"
}
foreach ($entry in $forbidden.GetEnumerator()) {
    Add-Result -Case $entry.Key -Passed (-not [regex]::IsMatch($combined, $entry.Value)) -Detail $entry.Value
}

$hwpCount = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count
Add-Result -Case 'static_tests_leave_no_hwp_process' -Passed ($hwpCount -eq 0) -Detail "count=$hwpCount"

$failed = @($results | Where-Object { -not $_.passed })
[ordered]@{
    schema_version = 'hwpx-agent.runtime-probe-static-tests/v1'
    total = $results.Count
    passed = $results.Count - $failed.Count
    failed = $failed.Count
    cases = @($results)
} | ConvertTo-Json -Depth 7
if ($failed.Count -ne 0) { exit 1 }
