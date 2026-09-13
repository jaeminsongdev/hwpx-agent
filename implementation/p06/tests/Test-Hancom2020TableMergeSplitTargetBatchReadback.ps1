[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$batchPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-merge-split-target-batch-readback.ps1'
)).Path
$singlePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-properties-target-readback.ps1'
)).Path
$boundedPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\p05\tools\invoke-hancom-2020-bounded-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\p05\tools\run-hancom-2020-tab-readback.ps1'
)).Path

$sources = [ordered]@{}
foreach ($path in @($batchPath, $singlePath, $boundedPath, $enginePath)) {
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
$batch = [string]$sources[$batchPath].content
$bounded = [string]$sources[$boundedPath].content
$engine = [string]$sources[$enginePath].content
$all = ($sources.Values | ForEach-Object { [string]$_.content }) -join "`n"

function Test-ManifestIdentityFailureBeforeCaseRun {
    $temporaryRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '..\..\..\target'
    )).Path.TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-merge-split-batch-preflight-' + [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $manifest = Join-Path $directory 'fixture-manifest.json'
    $trace = Join-Path $directory 'batch-trace.json'
    [System.IO.File]::WriteAllText(
        $manifest,
        '{"schema_version":"wrong"}',
        [System.Text.UTF8Encoding]::new($false)
    )
    $observed = $null
    try {
        & $batchPath `
            -FixtureManifestPath $manifest `
            -ExpectedFixtureManifestSha256 ('0' * 64) `
            -TracePath $trace | Out-Null
    }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        foreach ($candidate in @($trace, $manifest)) {
            if ([System.IO.File]::Exists($candidate)) {
                [System.IO.File]::Delete($candidate)
            }
        }
        if ([System.IO.Directory]::Exists($directory) -and
            [System.IO.Path]::GetFullPath($directory).StartsWith(
                $temporaryRoot + '\hwpx-agent-p06-merge-split-batch-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq 'TABLE_MERGE_SPLIT_TARGET_BATCH_MANIFEST_IDENTITY_MISMATCH'
}

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_batch_schema = $batch -match
        'hwpx-agent\.p06-09-table-merge-split-target-batch-readback/v1'
    exact_fixture_schema = $batch -match
        'hwpx-agent\.p06-09-table-merge-split-target-fixture/v1'
    exact_manifest_digest = $batch -match
        '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
    exact_two_case_bindings = $batch -match 'TABLE-016' -and
        $batch -match 'TABLE-017' -and $batch -match 'table\.split_cell' -and
        $batch -match 'table\.merge_cells'
    all_outputs_preflighted = $batch -match '\$probeProgressPath' -and
        $batch -match '\$caseProgressPath' -and $batch -match 'OUTPUT_ALREADY_EXISTS'
    text_probe_bound_to_input = $batch -match
        'TABLE_PROPERTIES_TARGET_READBACK_INPUT_TEXT_MISMATCH' -and
        $batch -match '\$expectedTextSha256 = \[string\]\$probeTrace\.input_text_sha256'
    independent_failures_continue = $batch -match '\$failures \+= \[ordered\]@\{' -and
        $batch -match 'attempted_case_count = \$prepared\.Count' -and
        $batch -match '(?m)^\s+continue\s*$'
    timeout_trace_without_target_supported = $batch -match
        "PSObject\.Properties\['target'\]"
    create_new_trace = $batch -match '\[System\.IO\.FileMode\]::CreateNew'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    bounded_watchdog = $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    exact_lifecycle = $engine -match "phase = 'open_input'" -and
        $engine -match "phase = 'save_as_hwpx'" -and
        $engine -match "phase = 'reopen_output'" -and
        $engine -match "phase = 'export_pdf'"
    process_cleanup = $bounded -match 'Stop-OwnedHancomProcesses' -and
        $batch -match 'remaining_hwp_process_count'
    manifest_failure_before_case_run = Test-ManifestIdentityFailureBeforeCaseRun
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch
        '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch
        '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version =
        'hwpx-agent.p06-09-table-merge-split-target-batch-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
