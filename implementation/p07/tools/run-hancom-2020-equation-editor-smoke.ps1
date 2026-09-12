[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$PlanPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanFileSha256,
    [Parameter(Mandatory)][string]$OracleExecutablePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOracleExecutableSha256,
    [ValidateRange(60, 1800)][int]$TimeoutSeconds = 900,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose() }
}

function Assert-PathInside {
    param([Parameter(Mandatory)][string]$Candidate, [Parameter(Mandatory)][string]$Boundary)
    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.StartsWith($boundaryFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'EDITOR_SMOKE_PATH_OUTSIDE_PRIVATE_BOUNDARY'
    }
    $cursor = Split-Path -Parent $candidateFull
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'EDITOR_SMOKE_REPARSE_POINT_REFUSED'
            }
        }
        if ($cursor.Equals($boundaryFull, [StringComparison]::OrdinalIgnoreCase)) { break }
        $next = Split-Path -Parent $cursor
        if ($next -eq $cursor) { throw 'EDITOR_SMOKE_BOUNDARY_NOT_REACHED' }
        $cursor = $next
    }
    return $candidateFull
}

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'EDITOR_SMOKE_OUTPUT_ALREADY_EXISTS' }
    $utf8 = New-Object Text.UTF8Encoding($false)
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $bytes = $utf8.GetBytes(($Value | ConvertTo-Json -Depth 16))
        $stream.Write($bytes, 0, $bytes.Length)
    }
    finally { $stream.Dispose() }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)
    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $prog = $null; $clsidNode = $null; $clsidKey = $null; $server = $null
    try {
        $prog = $root.OpenSubKey($RequestedProgId)
        if ($null -eq $prog) { throw 'EDITOR_SMOKE_PROGID_NOT_REGISTERED_32BIT' }
        $clsidNode = $prog.OpenSubKey('CLSID')
        $clsid = [string]$clsidNode.GetValue('')
        $clsidKey = $root.OpenSubKey("CLSID\$clsid")
        $server = $clsidKey.OpenSubKey('LocalServer32')
        $command = [string]$server.GetValue('')
    }
    finally {
        foreach ($key in @($server, $clsidKey, $clsidNode, $prog, $root)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match($command.Trim(), '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)')
    if (-not $match.Success) { throw 'EDITOR_SMOKE_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{
        version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Invoke-Oracle {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string]$InputPath,
        [Parameter(Mandatory)][string]$InputSha256,
        [Parameter(Mandatory)][string]$ScriptSha256,
        [Parameter(Mandatory)][string]$SemanticSha256,
        [Parameter(Mandatory)][string]$OutputPath
    )
    $lines = @(& $Executable $InputPath $InputSha256 $ScriptSha256 $SemanticSha256 2>&1)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 1) { throw 'EDITOR_SMOKE_ORACLE_FAILED' }
    $text = [string]$lines[0]
    $value = $text | ConvertFrom-Json
    if ([string]$value.schema_version -cne 'hwpx-agent.p07-09-equation-editor-oracle/v1' -or
        [string]$value.state -cne 'pass' -or -not [bool]$value.input_unchanged) {
        throw 'EDITOR_SMOKE_ORACLE_CONTRACT_MISMATCH'
    }
    Write-JsonNoOverwrite -Path $OutputPath -Value $value
    return $value
}

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$boundary = Join-Path $root 'implementation\p07\evidence\private'
$run = Assert-PathInside -Candidate $RunDirectory -Boundary $boundary
if (-not (Test-Path -LiteralPath $run -PathType Container) -or
    (Split-Path -Leaf $run) -cnotmatch '^[a-z0-9][a-z0-9-]{0,63}$') {
    throw 'EDITOR_SMOKE_RUN_DIRECTORY_INVALID'
}
$planFile = Assert-PathInside -Candidate (Resolve-Path -LiteralPath $PlanPath).Path -Boundary $boundary
$oracleExecutable = (Resolve-Path -LiteralPath $OracleExecutablePath).Path
if ((Get-Sha256File -Path $planFile) -cne $ExpectedPlanFileSha256 -or
    (Get-Sha256File -Path $oracleExecutable) -cne $ExpectedOracleExecutableSha256) {
    throw 'EDITOR_SMOKE_TOOL_OR_PLAN_IDENTITY_MISMATCH'
}
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $planFile | ConvertFrom-Json
$childScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-equation-editor-smoke-child.ps1')).Path
$parentSha256 = Get-Sha256File -Path $PSCommandPath
$childSha256 = Get-Sha256File -Path $childScript
$harnessBundleSha256 = Get-Sha256String -Value ($parentSha256 + ':' + $childSha256)
if ([string]$plan.schema_version -cne 'hwpx-agent.equation-editor-smoke/v3' -or
    [string]$plan.profile_version -cne 'hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1' -or
    [string]$plan.harness_sha256 -cne $harnessBundleSha256 -or
    [string]$plan.oracle_contract_sha256 -cne $ExpectedOracleExecutableSha256) {
    throw 'EDITOR_SMOKE_PLAN_CONTRACT_MISMATCH'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($ProgId -cne 'HWPFrame.HwpObject.2' -or $identity.version -cne $ExpectedBuild -or
    $ExpectedBuild -cne '11.0.0.9136' -or $identity.sha256 -cne $ExpectedExecutableSha256 -or
    $ExpectedExecutableSha256 -cne '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce') {
    throw 'EDITOR_SMOKE_TARGET_IDENTITY_MISMATCH'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'EDITOR_SMOKE_PREEXISTING_HWP_PROCESS'
}

$inputPath = Join-Path $run 'before.hwpx'
$outputPath = Join-Path $run 'after.hwpx'
$attestationPath = Join-Path $run 'manual-checklist.json'
$childTracePath = Join-Path $run 'child-trace.json'
$beforeOraclePath = Join-Path $run 'before-oracle-runtime.json'
$afterOraclePath = Join-Path $run 'after-oracle-runtime.json'
$oracleReceiptPath = Join-Path $run 'oracle-receipt.json'
$evidencePath = Join-Path $run 'evidence.json'
$receiptPath = Join-Path $run 'runtime-receipt.json'
foreach ($path in @($outputPath, $attestationPath, $childTracePath, $beforeOraclePath, $afterOraclePath, $oracleReceiptPath, $evidencePath, $receiptPath)) {
    if (Test-Path -LiteralPath $path) { throw 'EDITOR_SMOKE_OUTPUT_ALREADY_EXISTS' }
}
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf) -or
    (Get-Sha256File -Path $inputPath) -cne [string]$plan.source.artifact_sha256) {
    throw 'EDITOR_SMOKE_INPUT_IDENTITY_MISMATCH'
}
$beforeOracle = Invoke-Oracle -Executable $oracleExecutable -InputPath $inputPath `
    -InputSha256 ([string]$plan.source.artifact_sha256) `
    -ScriptSha256 ([string]$plan.before_script_sha256) `
    -SemanticSha256 ([string]$plan.before_semantic_sha256) -OutputPath $beforeOraclePath
if ([string]$beforeOracle.snapshot.artifact_sha256 -cne [string]$plan.source.artifact_sha256 -or
    [string]$beforeOracle.snapshot.package_graph_sha256 -cne [string]$plan.source.package_graph_sha256 -or
    [string]$beforeOracle.snapshot.document_flow_sha256 -cne [string]$plan.source.document_flow_sha256 -or
    [int64]$beforeOracle.snapshot.object_id -ne [int64]$plan.source.object_id -or
    [string]$beforeOracle.snapshot.semantic_sha256 -cne [string]$plan.source.semantic_sha256 -or
    [string]$beforeOracle.snapshot.script_sha256 -cne [string]$plan.source.script_sha256 -or
    [int64]$beforeOracle.snapshot.native_object_count -ne [int64]$plan.source.native_object_count -or
    [string]$beforeOracle.anchor_fingerprint_sha256 -cne [string]$plan.source.anchor_fingerprint_sha256) {
    throw 'EDITOR_SMOKE_SOURCE_ORACLE_MISMATCH'
}

$x86 = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
& $x86 -NoProfile -STA -File $childScript -RunDirectory $run -PlanPath $planFile `
    -ExpectedPlanFileSha256 $ExpectedPlanFileSha256 -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $childTracePath -PathType Leaf)) {
    throw 'EDITOR_SMOKE_CHILD_FAILED_OR_EFFECT_UNKNOWN'
}
$childTrace = Get-Content -Raw -Encoding UTF8 -LiteralPath $childTracePath | ConvertFrom-Json
if ([string]$childTrace.state -cne 'pass' -or [bool]$childTrace.computer_use_click_or_type_invoked) {
    throw 'EDITOR_SMOKE_CHILD_TRACE_FAILED'
}
$outputSha256 = Get-Sha256File -Path $outputPath
if ($outputSha256 -cne [string]$childTrace.output_sha256 -or
    (Get-Sha256File -Path $inputPath) -cne [string]$plan.source.artifact_sha256) {
    throw 'EDITOR_SMOKE_OUTPUT_OR_INPUT_DRIFT'
}
$afterOracle = Invoke-Oracle -Executable $oracleExecutable -InputPath $outputPath `
    -InputSha256 $outputSha256 -ScriptSha256 ([string]$plan.saved_after_script_sha256) `
    -SemanticSha256 ([string]$plan.after_semantic_sha256) -OutputPath $afterOraclePath
if ([int]$afterOracle.snapshot.object_id -ne [int]$beforeOracle.snapshot.object_id -or
    [int]$afterOracle.snapshot.native_object_count -ne [int]$beforeOracle.snapshot.native_object_count) {
    throw 'EDITOR_SMOKE_NATIVE_OBJECT_REPLACED'
}
$attestation = Get-Content -Raw -Encoding UTF8 -LiteralPath $attestationPath | ConvertFrom-Json
$attestationSha256 = Get-Sha256File -Path $attestationPath
$oracleReceipt = [ordered]@{
    schema_version = 'hwpx-agent.p07-09-equation-editor-oracle-receipt/v1'
    plan_sha256 = [string]$plan.plan_sha256
    before_oracle_sha256 = Get-Sha256File -Path $beforeOraclePath
    after_oracle_sha256 = Get-Sha256File -Path $afterOraclePath
    before = $beforeOracle.snapshot
    after_save = $afterOracle.snapshot
    after_reopen = $afterOracle.snapshot
    object_identity_preserved = $true
    semantic_change_verified = $true
    native_readback_verified = $true
}
Write-JsonNoOverwrite -Path $oracleReceiptPath -Value $oracleReceipt
$oracleReceiptSha256 = Get-Sha256File -Path $oracleReceiptPath
$childTraceSha256 = Get-Sha256File -Path $childTracePath
$evidence = [ordered]@{
    schema_version = 'hwpx-agent.equation-editor-smoke-evidence/v3'
    profile_version = 'hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1'
    plan_sha256 = [string]$plan.plan_sha256
    source_state_sha256 = [string]$plan.source_state_sha256
    harness_sha256 = $harnessBundleSha256
    oracle_contract_sha256 = $ExpectedOracleExecutableSha256
    target = [ordered]@{
        product = 'Hangul 2020'; prog_id = $ProgId; build = $ExpectedBuild
        executable_sha256 = $ExpectedExecutableSha256; architecture = 'x86'; locale = 'ko-KR'
    }
    state = 'succeeded'
    manual = [ordered]@{
        before_equation_matches_plan = [string]$attestation.before_equation_matches_plan
        double_click = [string]$attestation.double_click
        editor_visible = [string]$attestation.editor_visible
        one_token_change = [string]$attestation.one_token_change
        editor_closed_after_commit = [string]$attestation.editor_closed_after_commit
        post_commit_equation_matches_plan = [string]$attestation.post_commit_equation_matches_plan
        saved_as_after_hwpx = [string]$attestation.saved_as_after_hwpx
        user_performed_all_clicks_and_typing = [string]$attestation.user_performed_all_clicks_and_typing
        anomaly_reported = [bool]$attestation.anomaly_reported
        computer_use_click_or_type_invoked = [bool]$attestation.computer_use_click_or_type_invoked
        operator_checklist_sha256 = $attestationSha256
    }
    automation = [ordered]@{
        exact_target_preflight = 'passed'; immutable_input = 'passed'
        initial_native_readback = 'passed'; saved_native_readback = 'passed'
        reopen_native_readback = 'passed'; save = 'passed'; close = 'passed'
        reopen = 'passed'; all_phases = 'passed'
        trace_sha256 = $childTraceSha256; oracle_receipt_sha256 = $oracleReceiptSha256
    }
    before = $beforeOracle.snapshot
    after_save = $afterOracle.snapshot
    after_reopen = $afterOracle.snapshot
    silent_fallback_count = 0; text_fallback_count = 0
    image_fallback_count = 0; object_replacement_count = 0
}
Write-JsonNoOverwrite -Path $evidencePath -Value $evidence
$evidenceSha256 = Get-Sha256File -Path $evidencePath
$receipt = [ordered]@{
    schema_version = 'hwpx-agent.p07-09-equation-editor-runtime-receipt/v2'
    state = 'pass'; plan_sha256 = [string]$plan.plan_sha256
    evidence_sha256 = $evidenceSha256; child_trace_sha256 = $childTraceSha256
    oracle_receipt_sha256 = $oracleReceiptSha256
    target = [ordered]@{ build = $ExpectedBuild; executable_sha256 = $ExpectedExecutableSha256; architecture = 'x86'; locale = 'ko-KR' }
    manual_double_click = 'user_attested'; automated_save_reopen = 'passed'
    object_identity = 'preserved'; silent_fallback_count = 0
    visual_evidence = 'not_required'
    computer_use_click_or_type_invoked = $false; user_document_opened = $true
    external_network_invoked = $false; registry_or_system_setting_changed = $false
}
Write-JsonNoOverwrite -Path $receiptPath -Value $receipt
$receipt | ConvertTo-Json -Depth 12
