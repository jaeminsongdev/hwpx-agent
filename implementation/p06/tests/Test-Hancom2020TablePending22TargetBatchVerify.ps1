[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$wrapperPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-pending-22-target-batch-verify.ps1'
)).Path
$wrapper = [System.IO.File]::ReadAllText($wrapperPath)
$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $wrapperPath,
    [ref]$tokens,
    [ref]$errors
)

$targetRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\..\fixtures\target-build'
)).Path.TrimEnd('\')
$configurationAttempt = 'p06-09-table-pending-22-target-20991231-99'
$configurationDirectory = Join-Path $targetRoot $configurationAttempt
if ([System.IO.Directory]::Exists($configurationDirectory) -or
    [System.IO.File]::Exists($configurationDirectory)) {
    throw 'TABLE_PENDING_22_VERIFY_TEST_CONFIGURATION_PATH_EXISTS'
}
$configuration = & $wrapperPath -AttemptName $configurationAttempt -ValidateConfigurationOnly |
    ConvertFrom-Json
$configurationIsSideEffectFree =
    [string]$configuration.schema_version -ceq
        'hwpx-agent.p06-09-table-pending-22-target-batch-verify-config/v1' -and
    [string]$configuration.state -ceq 'pass' -and
    [int]$configuration.case_count -eq 22 -and
    -not [bool]$configuration.hwp_invoked -and
    -not [bool]$configuration.receipt_created -and
    -not [System.IO.Directory]::Exists($configurationDirectory) -and
    -not [System.IO.File]::Exists($configurationDirectory)

$collisionError = $null
try {
    & $wrapperPath `
        -AttemptName 'p06-09-table-pending-22-target-20260913-01' `
        -ValidateConfigurationOnly | Out-Null
}
catch { $collisionError = [string]$_.Exception.Message }

$checks = [ordered]@{
    script_parses = $errors.Count -eq 0
    exact_config_schema = $wrapper -match
        'hwpx-agent\.p06-09-table-pending-22-target-batch-verify-config/v1'
    exact_result_schema = $wrapper -match
        'hwpx-agent\.p06-09-table-pending-22-target-batch-verify/v1'
    exact_attempt_name = $wrapper -match
        '\^p06-09-table-pending-22-target-\[0-9\]\{8\}-\[0-9\]\{2\}\$'
    exact_manifest_digests = $wrapper -match
        '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97' -and
        $wrapper -match
        '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf' -and
        $wrapper -match
        '1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e'
    exact_manifest_paths = $wrapper -match
        'p06-09-table-merge-split-target-20260913-06' -and
        $wrapper -match
        'p06-09-table-layout-placement-target-20260913-04' -and
        $wrapper -match
        'p06-09-table-remaining-target-20260913-10'
    bounded_files = $wrapper -match 'Resolve-BoundedRegularFile' -and
        $wrapper -match 'FileAttributes\]::ReparsePoint'
    create_new_attempt = $wrapper -match
        'TABLE_PENDING_22_VERIFY_ATTEMPT_ALREADY_EXISTS' -and
        $wrapper -match 'Directory\]::CreateDirectory\(\$runDirectory\)'
    one_readback_invocation = [regex]::Matches(
        $wrapper,
        '& \$readback @readbackArguments'
    ).Count -eq 1
    readback_failure_stops_oracle = $wrapper.IndexOf(
        'if ($readbackExit -ne 0)',
        [System.StringComparison]::Ordinal
    ) -lt $wrapper.IndexOf(
        '& $cargo.Source @cargoArguments',
        [System.StringComparison]::Ordinal
    )
    exact_oracle = $wrapper -match
        "'p06_09_table_pending_22_target_oracle'" -and
        [regex]::Matches($wrapper, '& \$cargo\.Source @cargoArguments').Count -eq 1
    trace_digest_forwarded = $wrapper -match
        '\$traceSha256 = Get-Sha256File -Path \$resolvedTrace' -and
        $wrapper -match '\$resolvedTrace,\s*\r?\n\s*\$traceSha256,\s*\r?\n\s*\$receiptPath'
    exact_output_names = $wrapper -match "'pending-22-trace\.json'" -and
        $wrapper -match "'pending-22-oracle-receipt\.json'"
    receipt_revalidated = $wrapper -match
        'Resolve-BoundedRegularFile -Path \$receiptPath' -and
        $wrapper -match 'oracle_receipt_sha256'
    bounded_watchdog = $wrapper -match 'ValidateRange\(300, 7200\)' -and
        $wrapper -match 'TimeoutSeconds = 3600'
    config_is_side_effect_free = $configurationIsSideEffectFree
    existing_attempt_fails_before_hwp = $collisionError -ceq
        'TABLE_PENDING_22_VERIFY_ATTEMPT_ALREADY_EXISTS'
    no_ui_input = $wrapper -notmatch
        '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $wrapper -notmatch
        '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $wrapper -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() |
    Where-Object { -not [bool]$_.Value } |
    ForEach-Object { $_.Key })
[ordered]@{
    schema_version =
        'hwpx-agent.p06-09-table-pending-22-target-batch-verify-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{
            case = $_.Key
            passed = [bool]$_.Value
        }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
