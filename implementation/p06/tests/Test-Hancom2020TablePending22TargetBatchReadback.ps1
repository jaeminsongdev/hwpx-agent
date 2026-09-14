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
    $directory = Join-Path $targetRoot (
        'hwpx-agent-p06-pending-22-access-control-' +
        [guid]::NewGuid().ToString('N')
    )
    [void][System.IO.Directory]::CreateDirectory($directory)
    $sourceManifestPaths = @(
        Join-Path $targetRoot `
            'p06-09-table-merge-split-target-20260913-06\fixture-manifest.json'
        Join-Path $targetRoot `
            'p06-09-table-layout-placement-target-20260913-04\fixture-manifest.json'
        Join-Path $targetRoot `
            'p06-09-table-remaining-target-20260913-10\fixture-manifest.json'
    )
    $isolatedManifestPaths = @()
    for ($index = 0; $index -lt $sourceManifestPaths.Count; $index += 1) {
        $sourceManifest = [System.IO.Path]::GetFullPath(
            [string]$sourceManifestPaths[$index]
        )
        $sourceDirectory = [System.IO.Path]::GetDirectoryName($sourceManifest)
        $isolatedDirectory = Join-Path $directory ('group-' + $index)
        [void][System.IO.Directory]::CreateDirectory($isolatedDirectory)
        $isolatedManifest = Join-Path $isolatedDirectory 'fixture-manifest.json'
        [System.IO.File]::Copy($sourceManifest, $isolatedManifest, $false)
        $manifestRecord = Get-Content -Raw -LiteralPath $sourceManifest |
            ConvertFrom-Json
        foreach ($case in @($manifestRecord.cases)) {
            $relativeFile = [string]$case.file
            $sourceFile = [System.IO.Path]::GetFullPath((
                Join-Path $sourceDirectory $relativeFile
            ))
            if (-not $sourceFile.StartsWith(
                $sourceDirectory.TrimEnd('\') + '\',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
                throw 'TEST_FIXTURE_PATH_ESCAPES_MANIFEST_DIRECTORY'
            }
            $isolatedFile = [System.IO.Path]::GetFullPath((
                Join-Path $isolatedDirectory $relativeFile
            ))
            $isolatedParent = [System.IO.Path]::GetDirectoryName($isolatedFile)
            [void][System.IO.Directory]::CreateDirectory($isolatedParent)
            [System.IO.File]::Copy($sourceFile, $isolatedFile, $false)
        }
        $isolatedManifestPaths += $isolatedManifest
    }
    $trace = Join-Path $directory 'trace.json'
    $invoke = @{
        MergeSplitManifestPath = $isolatedManifestPaths[0]
        ExpectedMergeSplitManifestSha256 =
            '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
        LayoutPlacementManifestPath = $isolatedManifestPaths[1]
        ExpectedLayoutPlacementManifestSha256 =
            '053b401cbcd2a21b3e845a29ffef28b9c1f633dfa825ac3f52d520cb5f6a3430'
        RemainingManifestPath = $isolatedManifestPaths[2]
        ExpectedRemainingManifestSha256 =
            'e4bb736d7182769546cefd50f2a30fd4bffba7293c589174d8aa0858f9e45c39'
        AccessControlPath = Join-Path $targetRoot `
            'p06-09-table-structure-target-20260913-05\table-012-insert-row-3x3.hancom-2020-readback.hwpx'
        ExpectedAccessControlSha256 = ('0' * 64)
        TracePath = $trace
    }
    $observed = $null
    try { & $parentPath @invoke | Out-Null }
    catch { $observed = [string]$_.Exception.Message }
    finally {
        $fullDirectory = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($fullDirectory) -and
            $fullDirectory.StartsWith(
                $targetRoot + '\hwpx-agent-p06-pending-22-access-control-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($fullDirectory, $true)
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
$accessControlBlock = if ($accessControlPosition -ge 0 -and
    $caseLoopPosition -gt $accessControlPosition) {
    $engine.Substring(
        $accessControlPosition,
        $caseLoopPosition - $accessControlPosition
    )
}
else { '' }

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
        '053b401cbcd2a21b3e845a29ffef28b9c1f633dfa825ac3f52d520cb5f6a3430' -and
        $all -match
        'e4bb736d7182769546cefd50f2a30fd4bffba7293c589174d8aa0858f9e45c39'
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
    official_security_module = $all -match
        'official_file_path_checker_module' -and
        $all -match 'official_hancom_automation_security_module' -and
        $all -match '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6' -and
        $engine -match '\$hwp\.RegisterModule\(' -and
        $engine -match "'FilePathCheckDLL'" -and
        $engine -match "register_state = 'call_completed'" -and
        $engine -match "effective_state = 'control_open_close_pass'" -and
        $engine -notmatch 'SECURITY_MODULE_REGISTER_RETURNED_FALSE' -and
        $parent -match 'access_approval_user_owned'
    exact_access_control = $all -match
        '04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c' -and
        $all -match 'verified_hancom_saved_table_012_control' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_RETRY_RETURNED_FALSE' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_CHANGED'
    bounded_access_control_retry = $all -match
        'one_same_session_hwp_object_retry_after_first_false' -and
        $engine -match '\$phase = ''access_control_open_retry''' -and
        $engine -match 'Start-Sleep -Milliseconds 250' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_RETRY_DOCUMENT_ADD_FAILED' -and
        $engine -match 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_RETRY_DOCUMENT_COUNT_INVALID' -and
        $engine -match 'open_attempt_count = 2' -and
        $engine -match 'first_open_returned_false = \$true' -and
        [regex]::Matches($accessControlBlock, '\$document\.Open\(').Count -eq 1 -and
        [regex]::Matches($accessControlBlock, '\$hwp\.Open\(').Count -eq 1 -and
        [regex]::Matches($accessControlBlock, '\$documents\.Add\(\$false\)').Count -eq 2 -and
        $engine -notmatch '(?i)while\s*\('
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
    canonical_text_overload_safe = $engine -match
        '\$Value\.Replace\("`0", ''''\)' -and
        $engine -notmatch '\$Value\.Replace\(\[char\]0, ''''\)'
    one_window_case_reuse = [regex]::Matches(
        $engine,
        '\$documents\.Add\(\$false\)'
    ).Count -eq 2 -and
        [regex]::Matches(
            $engine,
            '\$hwp\.Open\('
        ).Count -eq 3 -and
        [regex]::Matches(
            $engine,
            '\$hwp\.Clear\(1\)'
        ).Count -eq 2 -and
        $engine -match 'TABLE_PENDING_22_BATCH_INPUT_DOCUMENT_COUNT_INVALID' -and
        $engine -match 'TABLE_PENDING_22_BATCH_OUTPUT_DOCUMENT_COUNT_INVALID'
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
    exactly_one_register_module = [regex]::Matches(
        $engine,
        '(?i)\.RegisterModule\s*\('
    ).Count -eq 1 -and
        $parent -notmatch '(?i)\.RegisterModule\s*\('
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
