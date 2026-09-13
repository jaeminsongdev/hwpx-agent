[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$batchPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-layout-placement-target-batch-readback.ps1'
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
$single = [string]$sources[$singlePath].content
$bounded = [string]$sources[$boundedPath].content
$engine = [string]$sources[$enginePath].content
$all = $batch + $single + $bounded + $engine

function Test-ManifestIdentityFailureBeforeCaseRun {
    $temporaryRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '..\..\..\target'
    )).Path.TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-layout-placement-batch-preflight-' + [guid]::NewGuid().ToString('N')
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
                $temporaryRoot + '\hwpx-agent-p06-layout-placement-batch-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq
        'TABLE_LAYOUT_PLACEMENT_TARGET_BATCH_MANIFEST_IDENTITY_MISMATCH'
}

$bindings = @(
    'TABLE-018', 'TABLE-019', 'TABLE-050', 'TABLE-051', 'TABLE-052', 'TABLE-053',
    'TABLE-034', 'TABLE-036', 'TABLE-037', 'TABLE-038',
    'table.equal_row_height', 'table.equal_column_width', 'table.row_min_height',
    'table.column_fixed_width', 'table.autofit_content', 'table.autofit_page',
    'table.position', 'table.inline_floating', 'table.wrap', 'table.outer_margin'
)
$bindingsPresent = @($bindings | Where-Object {
    $batch -notmatch [regex]::Escape($_)
}).Count -eq 0

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_batch_schema = $batch -match
        'hwpx-agent\.p06-09-table-layout-placement-target-batch-readback/v1'
    exact_fixture_schema = $batch -match
        'hwpx-agent\.p06-09-table-layout-placement-target-fixture/v1'
    exact_manifest_digest = $batch -match
        '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf'
    exact_ten_case_bindings = $bindingsPresent
    all_outputs_preflighted_before_first_case =
        $batch -match '\$prepared \+= \[ordered\]@\{' -and
        $batch -match 'foreach \(\$entry in \$prepared\)'
    create_new_trace = $batch -match '\[System\.IO\.FileMode\]::CreateNew'
    bounded_case_delegate = $batch -match
        'run-hancom-2020-table-properties-target-readback\.ps1'
    exact_text_digest = $batch -match
        'e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91'
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    exact_lifecycle = $engine -match "phase = 'open_input'" -and
        $engine -match "phase = 'save_as_hwpx'" -and
        $engine -match "phase = 'reopen_output'" -and
        $engine -match "phase = 'export_pdf'"
    bounded_watchdog = $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    input_immutability = $engine -match 'TAB_READBACK_INPUT_CHANGED'
    process_cleanup = $bounded -match 'Stop-OwnedHancomProcesses' -and
        $batch -match 'remaining_hwp_process_count'
    failed_trace_preserved = $batch -match
        'hwpx-agent\.p06-09-table-layout-placement-target-batch-readback-failure/v1'
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
        'hwpx-agent.p06-09-table-layout-placement-target-batch-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
