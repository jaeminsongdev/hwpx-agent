[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$parentPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-pending-22-target-batch-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-pending-22-target-batch-engine.ps1'
)).Path

$sources = [ordered]@{}
foreach ($path in @($parentPath, $enginePath)) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref]$tokens,
        [ref]$errors
    )
    $sources[$path] = [ordered]@{
        errors = $errors.Count
        content = [System.IO.File]::ReadAllText($path)
    }
}
$parent = [string]$sources[$parentPath].content
$engine = [string]$sources[$enginePath].content
$all = $parent + [Environment]::NewLine + $engine

function Test-ManifestIdentityFailsBeforeCom {
    $temporaryRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '..\..\..\fixtures\target-build'
    )).Path.TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-pending-22-preflight-' +
        [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $manifest = Join-Path $directory 'fixture-manifest.json'
    $trace = Join-Path $directory 'trace.json'
    [System.IO.File]::WriteAllText(
        $manifest,
        '{"schema_version":"wrong"}',
        [System.Text.UTF8Encoding]::new($false)
    )
    $observed = $null
    $invoke = @{
        MergeSplitManifestPath = $manifest
        ExpectedMergeSplitManifestSha256 = ('0' * 64)
        LayoutPlacementManifestPath = $manifest
        ExpectedLayoutPlacementManifestSha256 = ('0' * 64)
        RemainingManifestPath = $manifest
        ExpectedRemainingManifestSha256 = ('0' * 64)
        AccessControlPath = $manifest
        ExpectedAccessControlSha256 = ('0' * 64)
        TracePath = $trace
    }
    try {
        & $parentPath @invoke | Out-Null
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
                $temporaryRoot + '\hwpx-agent-p06-pending-22-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq
        'TABLE_PENDING_22_TARGET_MANIFEST_IDENTITY_MISMATCH' -and
        -not [System.IO.File]::Exists($trace)
}

function Test-AccessControlIdentityFailsBeforeCom {
    $targetRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '..\..\..\fixtures\target-build'
    )).Path.TrimEnd('\')
    $trace = Join-Path $targetRoot (
        'hwpx-agent-p06-pending-22-access-control-' +
        [guid]::NewGuid().ToString('N') + '.json'
    )
    $invoke = @{
        MergeSplitManifestPath = Join-Path $targetRoot `
            'p06-09-table-merge-split-target-20260913-06\fixture-manifest.json'
        ExpectedMergeSplitManifestSha256 =
            '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
        LayoutPlacementManifestPath = Join-Path $targetRoot `
            'p06-09-table-layout-placement-target-20260913-04\fixture-manifest.json'
        ExpectedLayoutPlacementManifestSha256 =
            '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf'
        RemainingManifestPath = Join-Path $targetRoot `
            'p06-09-table-remaining-target-20260913-10\fixture-manifest.json'
        ExpectedRemainingManifestSha256 =
            '1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e'
        AccessControlPath = Join-Path $targetRoot `
            'p06-09-table-structure-target-20260913-05\table-012-insert-row-3x3.hancom-2020-readback.hwpx'
        ExpectedAccessControlSha256 = ('0' * 64)
        TracePath = $trace
    }
    $observed = $null
    try { & $parentPath @invoke | Out-Null }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        if ([System.IO.File]::Exists($trace)) {
            [System.IO.File]::Delete($trace)
        }
    }
    return $observed -ceq
        'TABLE_PENDING_22_TARGET_ACCESS_CONTROL_IDENTITY_MISMATCH' -and
        -not [System.IO.File]::Exists($trace)
}

$expectedFeatures = @(
    'TABLE-016', 'TABLE-017',
    'TABLE-018', 'TABLE-019', 'TABLE-050', 'TABLE-051', 'TABLE-052',
    'TABLE-053', 'TABLE-034', 'TABLE-036', 'TABLE-037', 'TABLE-038',
    'TABLE-020', 'TABLE-021', 'TABLE-032', 'TABLE-033', 'TABLE-049',
    'TABLE-054', 'TABLE-056', 'TABLE-057', 'TABLE-058', 'TABLE-060'
)
$featureBindingsExact = $true
foreach ($feature in $expectedFeatures) {
    if ([regex]::Matches($engine, [regex]::Escape("'$feature'")).Count -ne 1) {
        $featureBindingsExact = $false
    }
}

$preflightPosition = $parent.IndexOf(
    '$mergeRecord = Resolve-ExactManifest',
    [System.StringComparison]::Ordinal
)
$childStartPosition = $parent.IndexOf(
    '[void]$child.Start()',
    [System.StringComparison]::Ordinal
)
$outputPreflightPosition = $parent.IndexOf(
    "throw 'TABLE_PENDING_22_TARGET_OUTPUT_ALREADY_EXISTS'",
    [System.StringComparison]::Ordinal
)
$accessControlPosition = $engine.IndexOf(
    '$phase = ''access_control_open''',
    [System.StringComparison]::Ordinal
)
$caseLoopPosition = $engine.IndexOf(
    'for ($index = 0; $index -lt $allCases.Count; $index += 1)',
    [System.StringComparison]::Ordinal
)

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values |
        Where-Object { [int]$_.errors -ne 0 }).Count -eq 0
    exact_outer_schema = $parent -match
        'hwpx-agent\.p06-09-table-pending-22-target-batch-readback/v1'
    exact_engine_schema = $engine -match
        'hwpx-agent\.p06-09-hancom-2020-table-pending-22-target-batch-engine/v1'
    exact_progress_schema = $all -match
        'hwpx-agent\.p06-09-table-pending-22-batch-progress/v1'
    exact_manifest_digests = $all -match
        '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97' -and
        $all -match
        '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf' -and
        $all -match
        '1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e'
    exact_22_feature_bindings = $featureBindingsExact -and
        $engine -match '\$allCases\.Count -ne 22' -and
        $parent -match '\$allCases\.Count -ne 22'
    one_hwp_process_session = [regex]::Matches(
        $engine,
        'New-Object -ComObject \$ProgId'
    ).Count -eq 1 -and
        [regex]::Matches(
            $parent,
            '\[void\]\$child\.Start\(\)'
        ).Count -eq 1 -and
        $engine -match 'single_hwp_process_for_22_cases'
    user_allow_all_once = $all -match
        'user_selects_allow_all_once' -and
        $parent -match 'access_approval_user_owned'
    exact_access_control = $all -match
        '04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c' -and
        $all -match 'verified_hancom_saved_table_012_control' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_OPEN_RETURNED_FALSE' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_CHANGED'
    access_control_before_cases = $accessControlPosition -ge 0 -and
        $caseLoopPosition -gt $accessControlPosition
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match
        '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    x86_sta_worker = $parent -match
        "WindowsPowerShell\\v1\.0\\powershell\.exe" -and
        $parent -match "'-STA'"
    preflight_all_outputs_before_child = $preflightPosition -ge 0 -and
        $outputPreflightPosition -ge 0 -and
        $childStartPosition -gt $preflightPosition -and
        $childStartPosition -gt $outputPreflightPosition
    input_immutability = $all -match 'input_unchanged' -and
        $all -match 'TABLE_PENDING_22_BATCH_INPUT_CHANGED'
    exact_lifecycle = $engine -match "'open_input'" -and
        $engine -match "'read_input'" -and
        $engine -match "'save_as_hwpx'" -and
        $engine -match "'reopen_output'" -and
        $engine -match "'read_output'" -and
        $engine -match "'export_pdf'" -and
        $engine -match "'close_output'"
    text_preservation = $engine -match 'input_text_sha256' -and
        $engine -match 'output_text_sha256' -and
        $engine -match 'TABLE_PENDING_22_BATCH_OUTPUT_TEXT_MISMATCH'
    layout_text_contract_bound = $engine -match
        'e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91' -and
        $engine -match 'fixture_contract'
    create_new_trace = $all -match
        '\[System\.IO\.FileMode\]::CreateNew'
    bounded_watchdog = $parent -match
        'WaitForExit\(\$TimeoutSeconds \* 1000\)' -and
        $parent -match 'ValidateRange\(300, 7200\)'
    progress_process_binding = $parent -match
        'ExpectedWorkerProcessId' -and
        $parent -match 'observedHwpProcessId'
    owned_process_cleanup = $parent -match
        'Stop-OwnedHancomProcesses' -and
        $parent -match "-Automation\\s\+\-Embedding"
    manifest_identity_fails_before_com = Test-ManifestIdentityFailsBeforeCom
    access_control_identity_fails_before_com =
        Test-AccessControlIdentityFailsBeforeCom
    no_single_case_delegate = $all -notmatch
        'run-hancom-2020-table-properties-target-readback'
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch
        '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch
        '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch
        '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() |
    Where-Object { -not [bool]$_.Value } |
    ForEach-Object { $_.Key })
[ordered]@{
    schema_version =
        'hwpx-agent.p06-09-table-pending-22-target-batch-static-tests/v1'
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
