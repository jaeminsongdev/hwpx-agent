[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$parentPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-create-target-batch-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-table-create-target-batch-engine.ps1'
)).Path

$sources = [ordered]@{}
foreach ($path in @($parentPath, $enginePath)) {
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

$parent = [string]$sources[$parentPath].content
$engine = [string]$sources[$enginePath].content
$all = $parent + $engine

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-ManifestIdentityFailureBeforeCom {
    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p06-create-batch-preflight-' + [guid]::NewGuid().ToString('N')
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
    try {
        & $parentPath `
            -FixtureManifestPath $manifest `
            -ExpectedFixtureManifestSha256 (Get-Sha256File -Path $manifest) `
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
                $temporaryRoot + '\hwpx-agent-p06-create-batch-preflight-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
    return $observed -ceq 'TABLE_CREATE_TARGET_BATCH_READBACK_MANIFEST_IDENTITY_MISMATCH'
}

$featureBindings = @(
    @('arbitrary-3x4-nonuniform', 'TABLE-001', 'table.create',
        'table-001-create-3x4-nonuniform.hwpx'),
    @('boundary-1x1', 'TABLE-001', 'table.create', 'table-001-create-1x1.hwpx')
)
$bindingsPresent = $true
foreach ($binding in $featureBindings) {
    foreach ($value in $binding) {
        if ($parent -notmatch [regex]::Escape($value) -or
            $engine -notmatch [regex]::Escape($value)) {
            $bindingsPresent = $false
        }
    }
}

$checks = [ordered]@{
    all_scripts_parse = @($sources.Values | Where-Object errors -ne 0).Count -eq 0
    exact_wrapper_schema = $parent -match 'hwpx-agent\.p06-09-hancom-2020-table-create-target-batch-readback/v1'
    exact_engine_schema = $engine -match 'hwpx-agent\.p06-09-hancom-2020-table-create-target-batch-engine/v1'
    exact_progress_schema = $all -match 'hwpx-agent\.p06-09-table-create-batch-progress/v1'
    exact_fixture_schema = $all -match 'hwpx-agent\.p06-09-table-create-target-fixture/v1'
    exact_fixture_manifest_digest = ([regex]::Matches(
        $all, '6595f8fa69798459f58aea01a18c954f8c39852be5c5b310aef4f5efa3c61263'
    )).Count -eq 2
    exact_two_bindings = $bindingsPresent
    dynamic_case_cardinality = $parent -match '\$expectedCaseCount = \$cases\.Count' -and
        $parent -notmatch '(?:case_count|completed_case_count) -eq 8' -and
        $parent -notmatch '\$traceCases\.Count -eq 8' -and
        $parent -notmatch '\$index -lt 8'
    manifest_validated_twice = ([regex]::Matches(
        $all, 'function Read-ExactFixtureManifest'
    )).Count -eq 2 -and ([regex]::Matches(
        $all, 'Assert-ExactProperties -Value \$manifest'
    )).Count -eq 2
    exact_target = $all -match 'HWPFrame\.HwpObject\.2' -and
        $all -match '11\.0\.0\.9136' -and
        $all -match '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    finite_watchdog = $parent -match 'ValidateRange\(60, 1800\)' -and
        $parent -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    x86_sta_child = $parent -match "'-STA'" -and
        $parent -match 'SpecialFolder\]::SystemX86'
    one_com_session = ([regex]::Matches(
        $engine, 'New-Object -ComObject \$ProgId'
    )).Count -eq 1 -and $engine -match 'for \(\$index = 0; \$index -lt \$cases\.Count; \$index \+= 1\)'
    exact_case_lifecycle = $engine -match "phase = 'open_input'" -and
        $engine -match "phase = 'save_as_hwpx'" -and
        $engine -match "phase = 'reopen_output'" -and
        $engine -match "phase = 'read_output'" -and
        $engine -match "phase = 'export_pdf'" -and
        $engine -match "phase = 'close_output'"
    bounded_document_close_quiescence = ([regex]::Matches(
        $engine, 'Start-Sleep -Milliseconds 250'
    )).Count -eq 2
    exact_text_digests = $engine -match 'INPUT_TEXT_DIGEST_INVALID' -and
        $engine -match 'output_text_sha256 -cne \$activeResult\.input_text_sha256' -and
        $parent -match 'input_text_sha256' -and $parent -match 'output_text_sha256'
    inner_trace_tamper_checks = $parent -match 'function Test-ExactInnerTraceShape' -and
        $parent -match "target\.registry_view -ceq 'Registry32'" -and
        $parent -match 'target\.executable_sha256 -ceq \$ExpectedExecutableSha256'
    input_digest_and_immutability = $engine -match 'TABLE_CREATE_BATCH_INPUT_CHANGED' -and
        $parent -match 'input_unchanged'
    create_only_trace_and_progress = ([regex]::Matches(
        $all, '\[System\.IO\.FileMode\]::CreateNew'
    )).Count -eq 2 -and $all -match 'OUTPUT_ALREADY_EXISTS'
    deterministic_output_names = $all -match '\.hancom-2020-readback\.hwpx' -and
        $all -match '\.hancom-2020-render\.pdf'
    bounded_pdf_evidence = $engine -match "'%PDF-'" -and
        $parent -match 'Test-BoundedPdfEvidence' -and
        $all -match '33554432'
    fail_fast_preserves_outputs = $engine -notmatch '(?i)(Remove-Item|Delete\(\$paths\.(?:output|pdf))' -and
        $parent -notmatch '(?i)(Remove-Item|Delete\(\$casePaths\[.*\]\.(?:output|pdf))'
    bounded_progress_journal = $parent -match 'expectedSequence -gt 160' -and
        $parent -match '262144' -and $parent -match 'progress_observed_feature_id'
    process_event_null_normalized = $engine -match 'normalizedFeatureId' -and
        $engine -match '\[string\]::IsNullOrEmpty\(\$FeatureId\)' -and
        $engine -match 'feature_id = \$normalizedFeatureId'
    owned_process_cleanup = $parent -match 'Stop-OwnedHancomProcesses' -and
        $parent -match 'remaining_hwp_process_count'
    manifest_identity_fails_before_com = Test-ManifestIdentityFailureBeforeCom
    raw_text_redacted = $all -match 'raw_document_text_present = \$false' -and
        $all -notmatch '(?i)(input_text|output_text)\s*='
    no_register_module = $all -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = $all -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = $all -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = $all -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-create-target-batch-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
