[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$PlanPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanFileSha256,
    [Parameter(Mandatory)][string]$OracleExecutablePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOracleExecutableSha256,
    [ValidateRange(60, 1800)][int]$TimeoutSeconds = 900,
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
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Assert-Inside {
    param([Parameter(Mandatory)][string]$Candidate, [Parameter(Mandatory)][string]$Boundary)
    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.StartsWith($boundaryFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'LAYOUT_PATH_OUTSIDE_PRIVATE_BOUNDARY'
    }
    $cursor = Split-Path -Parent $candidateFull
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'LAYOUT_REPARSE_POINT_REFUSED'
            }
        }
        if ($cursor.Equals($boundaryFull, [StringComparison]::OrdinalIgnoreCase)) { break }
        $cursor = Split-Path -Parent $cursor
    }
    return $candidateFull
}

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'LAYOUT_OUTPUT_ALREADY_EXISTS' }
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($Value | ConvertTo-Json -Depth 16))
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) }
    finally { $stream.Dispose() }
}

function Get-ComServerIdentity {
    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot, [Microsoft.Win32.RegistryView]::Registry32
    )
    $prog = $null; $clsidNode = $null; $clsidKey = $null; $server = $null
    try {
        $prog = $root.OpenSubKey('HWPFrame.HwpObject.2')
        if ($null -eq $prog) { throw 'LAYOUT_PROGID_NOT_REGISTERED_32BIT' }
        $clsidNode = $prog.OpenSubKey('CLSID'); $clsid = [string]$clsidNode.GetValue('')
        $clsidKey = $root.OpenSubKey("CLSID\$clsid")
        $server = $clsidKey.OpenSubKey('LocalServer32'); $command = [string]$server.GetValue('')
    }
    finally {
        foreach ($key in @($server, $clsidKey, $clsidNode, $prog, $root)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match($command.Trim(), '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)')
    if (-not $match.Success) { throw 'LAYOUT_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{ version = [string]$item.VersionInfo.FileVersion; sha256 = Get-Sha256File $path }
}

function Invoke-Oracle {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string]$InputPath,
        [Parameter(Mandatory)][string]$InputSha256,
        [Parameter(Mandatory)][string]$Layout,
        [Parameter(Mandatory)][string]$ScriptSha256,
        [Parameter(Mandatory)][string]$SemanticSha256
    )
    $lines = @(& $Executable $InputPath $InputSha256 $Layout $ScriptSha256 $SemanticSha256 2>&1)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 1) { throw 'LAYOUT_ORACLE_FAILED' }
    $value = ([string]$lines[0]) | ConvertFrom-Json
    if ([string]$value.schema_version -cne 'hwpx-agent.p07-07-equation-layout-oracle/v1' -or
        [string]$value.state -cne 'pass' -or -not [bool]$value.input_unchanged) {
        throw 'LAYOUT_ORACLE_CONTRACT_MISMATCH'
    }
    return $value
}

function Test-MetricsEqual {
    param([Parameter(Mandatory)]$Expected, [Parameter(Mandatory)]$Actual)
    foreach ($name in @(
        'advance_units', 'above_levels', 'below_levels', 'nodes', 'depth',
        'matrix_rows', 'matrix_columns'
    )) {
        if ([int64]$Expected.$name -ne [int64]$Actual.$name) { return $false }
    }
    return $true
}

function Assert-BoundedPdf {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][long]$ExpectedBytes
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'LAYOUT_PDF_MISSING' }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -ne $ExpectedBytes -or $item.Length -lt 5 -or $item.Length -gt 33554432 -or
        (Get-Sha256File $Path) -cne $ExpectedSha256) {
        throw 'LAYOUT_PDF_IDENTITY_MISMATCH'
    }
    $stream = [IO.File]::OpenRead($Path)
    try {
        $signature = [byte[]]::new(5)
        if ($stream.Read($signature, 0, 5) -ne 5 -or
            [Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
            throw 'LAYOUT_PDF_SIGNATURE_MISMATCH'
        }
    }
    finally { $stream.Dispose() }
}

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$boundary = Join-Path $root 'implementation\p07\evidence\private'
$run = Assert-Inside $RunDirectory $boundary
if (-not (Test-Path -LiteralPath $run -PathType Container) -or
    (Split-Path -Leaf $run) -cnotmatch '^[a-z0-9][a-z0-9-]{0,63}$') { throw 'LAYOUT_RUN_INVALID' }
$planFile = Assert-Inside (Resolve-Path -LiteralPath $PlanPath).Path $boundary
$oracle = (Resolve-Path -LiteralPath $OracleExecutablePath).Path
if ((Get-Sha256File $planFile) -cne $ExpectedPlanFileSha256 -or
    (Get-Sha256File $oracle) -cne $ExpectedOracleExecutableSha256) {
    throw 'LAYOUT_PLAN_OR_ORACLE_IDENTITY_MISMATCH'
}
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $planFile | ConvertFrom-Json
$child = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-equation-layout-child.ps1')).Path
$parentSha256 = Get-Sha256File $PSCommandPath; $childSha256 = Get-Sha256File $child
$harnessSha256 = Get-Sha256String ($parentSha256 + ':' + $childSha256)
if ([string]$plan.schema_version -cne 'hwpx-agent.p07-07-equation-layout-target-plan/v1' -or
    [string]$plan.harness_sha256 -cne $harnessSha256 -or
    [string]$plan.oracle_executable_sha256 -cne $ExpectedOracleExecutableSha256 -or
    @($plan.samples).Count -ne 8) { throw 'LAYOUT_PLAN_CONTRACT_MISMATCH' }
$identity = Get-ComServerIdentity
if ($identity.version -cne '11.0.0.9136' -or $identity.sha256 -cne $ExpectedExecutableSha256 -or
    $ExpectedExecutableSha256 -cne '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce') {
    throw 'LAYOUT_TARGET_IDENTITY_MISMATCH'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'LAYOUT_PREEXISTING_HWP_PROCESS'
}
$tracePath = Join-Path $run 'child-trace.json'; $evidencePath = Join-Path $run 'target-evidence.json'
$childStdout = Join-Path $run 'child.stdout.txt'; $childStderr = Join-Path $run 'child.stderr.txt'
foreach ($path in @($tracePath, $evidencePath, $childStdout, $childStderr)) {
    if (Test-Path -LiteralPath $path) { throw 'LAYOUT_OUTPUT_ALREADY_EXISTS' }
}
$x86 = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
$childProcess = Start-Process -FilePath $x86 -ArgumentList @(
    '-NoProfile', '-STA', '-File', $child, '-RunDirectory', $run, '-PlanPath', $planFile,
    '-ExpectedPlanFileSha256', $ExpectedPlanFileSha256
) -WindowStyle Hidden -PassThru -RedirectStandardOutput $childStdout -RedirectStandardError $childStderr
if (-not $childProcess.WaitForExit($TimeoutSeconds * 1000)) {
    throw 'LAYOUT_CHILD_TIMEOUT_EFFECT_UNKNOWN'
}
if ($childProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $tracePath -PathType Leaf)) {
    throw 'LAYOUT_CHILD_FAILED_OR_EFFECT_UNKNOWN'
}
$trace = Get-Content -Raw -Encoding UTF8 -LiteralPath $tracePath | ConvertFrom-Json
if ([string]$trace.state -cne 'pass' -or @($trace.sample_results).Count -ne 8 -or
    [bool]$trace.computer_use_click_or_type_invoked) { throw 'LAYOUT_CHILD_TRACE_FAILED' }
$oracles = New-Object Collections.ArrayList
$inlineContextSha256 = Get-Sha256String 'I'
for ($index = 0; $index -lt 8; $index += 1) {
    $sample = @($plan.samples)[$index]; $runtime = @($trace.sample_results)[$index]
    $layout = [string]$sample.layout
    $contextMatches = if ($layout -ceq 'inline') {
        [string]$runtime.inline_context_sha256 -ceq $inlineContextSha256
    } else { $null -eq $runtime.inline_context_sha256 }
    if ([string]$runtime.id -cne [string]$sample.id -or [string]$runtime.layout -cne $layout -or
        [string]$runtime.state -cne 'pass' -or -not $contextMatches -or
        [string]$runtime.insert_readback_sha256 -cne [string]$sample.script_sha256 -or
        [string]$runtime.reopen_readback_sha256 -cne [string]$sample.script_sha256 -or
        [string]$runtime.save -cne 'pass' -or [string]$runtime.reopen -cne 'pass' -or
        [string]$runtime.reopen_readback -cne 'pass' -or [string]$runtime.pdf_export -cne 'pass' -or
        -not [bool]$runtime.pdf_signature_valid) { throw 'LAYOUT_SAMPLE_TRACE_MISMATCH' }
    $artifact = Join-Path $run ([string]$sample.id + '.hwpx')
    $artifactSha256 = Get-Sha256File $artifact
    if ($artifactSha256 -cne [string]$runtime.artifact_sha256) { throw 'LAYOUT_ARTIFACT_DRIFT' }
    $pdf = Join-Path $run ([string]$sample.id + '.pdf')
    Assert-BoundedPdf $pdf ([string]$runtime.pdf_sha256) ([long]$runtime.pdf_bytes)
    $oracleValue = Invoke-Oracle $oracle $artifact $artifactSha256 $layout `
        ([string]$sample.script_sha256) ([string]$sample.semantic_sha256)
    if ([string]$oracleValue.layout -cne $layout -or
        [string]$oracleValue.script_sha256 -cne [string]$sample.script_sha256 -or
        [string]$oracleValue.semantic_sha256 -cne [string]$sample.semantic_sha256 -or
        -not (Test-MetricsEqual $sample.metrics $oracleValue.metrics)) {
        throw 'LAYOUT_ORACLE_SAMPLE_MISMATCH'
    }
    $oraclePath = Join-Path $run ('oracle-' + [string]$sample.id + '.json')
    Write-JsonNoOverwrite $oraclePath $oracleValue
    [void]$oracles.Add([ordered]@{
        id = [string]$sample.id; layout = $layout
        artifact_sha256 = $artifactSha256; pdf_sha256 = [string]$runtime.pdf_sha256
        pdf_bytes = [long]$runtime.pdf_bytes; oracle_sha256 = Get-Sha256File $oraclePath
        native_readback_sha256 = [string]$oracleValue.native_readback_sha256
        width_hwpunit = [int]$oracleValue.width_hwpunit
        height_hwpunit = [int]$oracleValue.height_hwpunit
        baseline_percent = [int]$oracleValue.baseline_percent
        metrics = $oracleValue.metrics
    })
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'LAYOUT_HWP_PROCESS_REMAINED'
}
$evidence = [ordered]@{
    schema_version = 'hwpx-agent.p07-07-equation-layout-target-evidence/v1'
    profile_version = 'hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1'
    plan_sha256 = [string]$plan.plan_sha256
    sample_manifest_sha256 = [string]$plan.sample_manifest_sha256
    tier_b_plan_file_sha256 = [string]$plan.tier_b_plan_file_sha256
    tier_b_plan_sha256 = [string]$plan.tier_b_plan_sha256
    plan_file_sha256 = $ExpectedPlanFileSha256; harness_sha256 = $harnessSha256
    oracle_executable_sha256 = $ExpectedOracleExecutableSha256
    child_trace_sha256 = Get-Sha256File $tracePath; timeout_seconds = $TimeoutSeconds
    target = [ordered]@{
        product = 'Hangul 2020'; build = '11.0.0.9136'; architecture = 'x86'
        locale = 'ko-KR'; executable_sha256 = $ExpectedExecutableSha256; font_name = 'HancomEQN'
    }
    state = 'native_pass_visual_not_run'; sample_count = 8
    inline_sample_count = 4; display_sample_count = 4
    samples = $oracles; render_state = 'pdf_exported_visual_not_run'; visual_state = 'not_run'
    actual_hangul = $true; computer_use_click_or_type_invoked = $false
    user_document_opened = $false; external_network_invoked = $false
    registry_or_system_setting_changed = $false; qualification_issued = $false
    p07_07_complete = $false; p07_complete = $false; production_ready = $false; product_complete = $false
}
Write-JsonNoOverwrite $evidencePath $evidence
[ordered]@{
    schema_version = 'hwpx-agent.p07-07-equation-layout-target-runtime-receipt/v1'
    state = 'native_pass_visual_not_run'; sample_count = 8
    evidence_sha256 = Get-Sha256File $evidencePath
    actual_hangul = $true; save_reopen = $true; pdf_export = $true
    visual = $false; qualification_issued = $false; product_complete = $false
} | ConvertTo-Json -Compress
