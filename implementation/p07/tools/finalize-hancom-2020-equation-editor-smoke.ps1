[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$PlanPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanFileSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedChildTraceSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPriorFinalizerTraceSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPriorFinalizerV2TraceSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPriorFinalizerV3TraceSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedAfterSha256,
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

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'EDITOR_FINALIZER_OUTPUT_ALREADY_EXISTS' }
    $utf8 = New-Object Text.UTF8Encoding($false)
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $bytes = $utf8.GetBytes(($Value | ConvertTo-Json -Depth 12))
        $stream.Write($bytes, 0, $bytes.Length)
    }
    finally { $stream.Dispose() }
}

function Wait-Sha256File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedSha256,
        [ValidateRange(1, 30)][int]$TimeoutSeconds = 10
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $observed = $null
        try {
            $observed = Get-Sha256File -Path $Path
        }
        catch { Start-Sleep -Milliseconds 250; continue }
        if ($observed -cne $ExpectedSha256) { throw 'EDITOR_FINALIZER_ARTIFACT_DRIFT' }
        return
    }
    throw 'EDITOR_FINALIZER_FILE_LOCK_TIMEOUT'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value) } catch { }
    }
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
        if ($null -eq $prog) { throw 'EDITOR_FINALIZER_PROGID_NOT_REGISTERED_32BIT' }
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
    if (-not $match.Success) { throw 'EDITOR_FINALIZER_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{
        version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$boundary = [IO.Path]::GetFullPath((Join-Path $repo 'implementation\p07\evidence\private')).TrimEnd('\')
$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if (-not $run.StartsWith($boundary + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $run) -cnotmatch '^[a-z0-9][a-z0-9-]{0,63}$' -or
    -not (Test-Path -LiteralPath $run -PathType Container)) {
    throw 'EDITOR_FINALIZER_RUN_DIRECTORY_INVALID'
}
$planFile = [IO.Path]::GetFullPath($PlanPath)
if (-not $planFile.StartsWith($run + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $planFile) -cne 'plan.json' -or
    (Get-Sha256File -Path $planFile) -cne $ExpectedPlanFileSha256) {
    throw 'EDITOR_FINALIZER_PLAN_IDENTITY_MISMATCH'
}
$beforePath = Join-Path $run 'before.hwpx'
$afterPath = Join-Path $run 'after.hwpx'
$checklistPath = Join-Path $run 'manual-checklist.json'
$childTracePath = Join-Path $run 'child-trace.json'
$priorTracePath = Join-Path $run 'lifecycle-finalizer-trace.json'
$priorV2TracePath = Join-Path $run 'lifecycle-finalizer-trace-v2.json'
$priorV3TracePath = Join-Path $run 'lifecycle-finalizer-trace-v3.json'
$tracePath = Join-Path $run 'lifecycle-finalizer-trace-v4.json'
if (Test-Path -LiteralPath $tracePath) { throw 'EDITOR_FINALIZER_OUTPUT_ALREADY_EXISTS' }
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $planFile | ConvertFrom-Json
$child = Get-Content -Raw -Encoding UTF8 -LiteralPath $childTracePath | ConvertFrom-Json
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $priorTracePath | ConvertFrom-Json
$priorV2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $priorV2TracePath | ConvertFrom-Json
$priorV3 = Get-Content -Raw -Encoding UTF8 -LiteralPath $priorV3TracePath | ConvertFrom-Json
if ([string]$plan.schema_version -cne 'hwpx-agent.equation-editor-smoke/v3' -or
    [string]$child.schema_version -cne 'hwpx-agent.p07-09-equation-editor-child-trace/v3' -or
    (Get-Sha256File -Path $childTracePath) -cne $ExpectedChildTraceSha256 -or
    [string]$child.plan_sha256 -cne [string]$plan.plan_sha256 -or
    [string]$child.state -cne 'effect_unknown' -or
    [string]$child.failed_phase -cne 'reopen' -or
    [string]$child.phases.close_after_save -cne 'pass' -or
    [string]$child.phases.reopen -cne 'failed' -or
    [string]$child.output_sha256 -cne $ExpectedAfterSha256 -or
    [string]$child.manual_checklist_sha256 -cne (Get-Sha256File -Path $checklistPath) -or
    (Get-Sha256File -Path $priorTracePath) -cne $ExpectedPriorFinalizerTraceSha256 -or
    [string]$prior.state -cne 'effect_unknown' -or
    [string]$prior.failed_phase -cne 'first_reopen' -or
    (Get-Sha256File -Path $priorV2TracePath) -cne $ExpectedPriorFinalizerV2TraceSha256 -or
    [string]$priorV2.state -cne 'effect_unknown' -or
    [string]$priorV2.failed_phase -cne 'first_reopen' -or
    (Get-Sha256File -Path $priorV3TracePath) -cne $ExpectedPriorFinalizerV3TraceSha256 -or
    [string]$priorV3.state -cne 'effect_unknown' -or
    [string]$priorV3.failed_phase -cne 'first_reopen' -or
    (Get-Sha256File -Path $beforePath) -cne [string]$plan.source.artifact_sha256 -or
    (Get-Sha256File -Path $afterPath) -cne $ExpectedAfterSha256) {
    throw 'EDITOR_FINALIZER_PREDECESSOR_MISMATCH'
}
foreach ($phaseName in @('com_create', 'version_check', 'open_input', 'window_visible',
        'manual_checklist', 'output_stable', 'input_immutable', 'close_after_save')) {
    if ([string]$child.phases.$phaseName -cne 'pass') { throw 'EDITOR_FINALIZER_PREDECESSOR_INCOMPLETE' }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'EDITOR_FINALIZER_PREEXISTING_HWP_PROCESS'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($ProgId -cne 'HWPFrame.HwpObject.2' -or $identity.version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'EDITOR_FINALIZER_TARGET_IDENTITY_MISMATCH'
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p07-09-equation-editor-lifecycle-finalizer-trace/v4'
    plan_sha256 = [string]$plan.plan_sha256
    predecessor_child_trace_sha256 = $ExpectedChildTraceSha256
    predecessor_finalizer_trace_sha256 = $ExpectedPriorFinalizerTraceSha256
    predecessor_finalizer_v2_trace_sha256 = $ExpectedPriorFinalizerV2TraceSha256
    predecessor_finalizer_v3_trace_sha256 = $ExpectedPriorFinalizerV3TraceSha256
    state = 'effect_unknown'
    phases = [ordered]@{
        exact_target_preflight = 'pass'; immutable_input = 'pass'; saved_output_identity = 'pass'
        fresh_com_create = 'not_run'; first_reopen = 'not_run'; first_reopen_close = 'not_run'
        second_reopen = 'not_run'; second_reopen_close = 'not_run'; quit = 'not_run'
    }
    after_sha256 = $ExpectedAfterSha256
    failed_phase = $null
    error_code = $null
    failure_hresult = $null
    computer_use_click_or_type_invoked = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
}
$hwp = $null; $documents = $null; $document = $null; $window = $null; $phase = 'fresh_com_create'
try {
    $trace.phases.fresh_com_create = 'running'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne $ExpectedBuild) { throw 'EDITOR_FINALIZER_VERSION_MISMATCH' }
    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.phases.fresh_com_create = 'pass'

    foreach ($entry in @(
            [ordered]@{ open = 'first_reopen'; close = 'first_reopen_close' },
            [ordered]@{ open = 'second_reopen'; close = 'second_reopen_close' }
        )) {
        $phase = [string]$entry.open; $trace.phases[$phase] = 'running'
        Wait-Sha256File -Path $afterPath -ExpectedSha256 $ExpectedAfterSha256
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'EDITOR_FINALIZER_DOCUMENT_ADD_FAILED' }
        if ($document.Open($afterPath, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'EDITOR_FINALIZER_REOPEN_FAILED'
        }
        [void]$document.SetActive_XHwpDocument()
        $trace.phases[$phase] = 'pass'
        $phase = [string]$entry.close; $trace.phases[$phase] = 'running'
        [void]$document.Close($false)
        Clear-ComObject -Value $document; $document = $null
        Wait-Sha256File -Path $afterPath -ExpectedSha256 $ExpectedAfterSha256
        $trace.phases[$phase] = 'pass'
    }
    $phase = 'quit'; $trace.phases.quit = 'running'
    $hwp.Quit(); $trace.phases.quit = 'pass'
    $trace.state = 'pass'
}
catch {
    $trace.failed_phase = $phase
    $trace.failure_hresult = [int64]$_.Exception.HResult
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'EDITOR_FINALIZER_EXCEPTION' }
    if ($trace.phases.Contains($phase)) { $trace.phases[$phase] = 'failed' }
}
finally {
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { }; Clear-ComObject $document }
    if ($null -ne $hwp -and $trace.phases.quit -ne 'pass') {
        try { $hwp.Quit(); $trace.phases.quit = 'pass' } catch { }
    }
    Clear-ComObject $window; Clear-ComObject $documents; Clear-ComObject $hwp
    [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Write-JsonNoOverwrite -Path $tracePath -Value $trace
$trace | ConvertTo-Json -Depth 12
if ($trace.state -ne 'pass') { exit 2 }
