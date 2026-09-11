[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$PlanPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanFileSha256,
    [ValidateRange(60, 1800)][int]$TimeoutSeconds = 900
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'EDITOR_CHILD_OUTPUT_ALREADY_EXISTS' }
    $utf8 = New-Object Text.UTF8Encoding($false)
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $bytes = $utf8.GetBytes(($Value | ConvertTo-Json -Depth 12))
        $stream.Write($bytes, 0, $bytes.Length)
    }
    finally { $stream.Dispose() }
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Assert-Digest {
    param([Parameter(Mandatory)][string]$Value, [Parameter(Mandatory)][string]$Code)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw $Code }
}

function Wait-StableFile {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][datetime]$Deadline)
    $prior = $null
    $stable = 0
    while ((Get-Date) -lt $Deadline) {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            $item = Get-Item -LiteralPath $Path
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.Length -le 0) {
                throw 'EDITOR_CHILD_OUTPUT_NOT_REGULAR'
            }
            $current = "{0}:{1}" -f $item.Length, (Get-Sha256File -Path $Path)
            if ($current -ceq $prior) { $stable += 1 } else { $stable = 0; $prior = $current }
            if ($stable -ge 3) { return $current.Split(':')[1] }
        }
        Start-Sleep -Milliseconds 500
    }
    throw 'EDITOR_CHILD_MANUAL_TIMEOUT'
}

$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
$planFile = [IO.Path]::GetFullPath($PlanPath)
if (-not $planFile.StartsWith($run + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $planFile) -cne 'plan.json' -or
    (Get-Sha256File -Path $planFile) -cne $ExpectedPlanFileSha256) {
    throw 'EDITOR_CHILD_PLAN_IDENTITY_MISMATCH'
}
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $planFile | ConvertFrom-Json
if ([string]$plan.schema_version -cne 'hwpx-agent.equation-editor-smoke/v1' -or
    [string]$plan.profile_version -cne 'hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1' -or
    [string]$plan.plan_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
    [int]$plan.changed_token_index -lt 0 -or
    [string]$plan.before_script -ceq [string]$plan.after_script) {
    throw 'EDITOR_CHILD_PLAN_CONTRACT_MISMATCH'
}
foreach ($value in @(
    [string]$plan.harness_sha256, [string]$plan.oracle_contract_sha256,
    [string]$plan.before_semantic_sha256, [string]$plan.before_script_sha256,
    [string]$plan.after_semantic_sha256, [string]$plan.after_script_sha256,
    [string]$plan.source.artifact_sha256
)) { Assert-Digest -Value $value -Code 'EDITOR_CHILD_PLAN_DIGEST_INVALID' }

$inputPath = Join-Path $run 'before.hwpx'
$outputPath = Join-Path $run 'after.hwpx'
$attestationPath = Join-Path $run 'manual-attestation.json'
$instructionPath = Join-Path $run 'manual-instructions.json'
$tracePath = Join-Path $run 'child-trace.json'
foreach ($path in @($outputPath, $attestationPath, $instructionPath, $tracePath)) {
    if (Test-Path -LiteralPath $path) { throw 'EDITOR_CHILD_OUTPUT_ALREADY_EXISTS' }
}
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf) -or
    (Get-Sha256File -Path $inputPath) -cne [string]$plan.source.artifact_sha256) {
    throw 'EDITOR_CHILD_INPUT_IDENTITY_MISMATCH'
}
$instruction = [ordered]@{
    schema_version = 'hwpx-agent.p07-09-equation-editor-manual-instructions/v1'
    plan_sha256 = [string]$plan.plan_sha256
    before_script = [string]$plan.before_script
    after_script = [string]$plan.after_script
    changed_token_index = [int]$plan.changed_token_index
    required_output_filename = 'after.hwpx'
    required_attestation_filename = 'manual-attestation.json'
    instruction = 'User double-clicks the only native equation, changes exactly the planned token, closes the editor, saves as after.hwpx, supplies four screenshots, and confirms all clicks and typing were manual.'
    computer_use_policy = 'screenshot_only'
}
Write-JsonNoOverwrite -Path $instructionPath -Value $instruction

$trace = [ordered]@{
    schema_version = 'hwpx-agent.p07-09-equation-editor-child-trace/v1'
    plan_sha256 = [string]$plan.plan_sha256
    state = 'effect_unknown'
    phases = [ordered]@{
        com_create = 'not_run'; version_check = 'not_run'; open_input = 'not_run'
        window_visible = 'not_run'; manual_attestation = 'not_run'; output_stable = 'not_run'
        input_immutable = 'not_run'; close_after_save = 'not_run'; reopen = 'not_run'
        reopen_close = 'not_run'; quit = 'not_run'
    }
    output_sha256 = $null
    manual_attestation_sha256 = $null
    failed_phase = $null
    error_code = $null
    computer_use_click_or_type_invoked = $false
    user_document_opened = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
}
$hwp = $null; $documents = $null; $document = $null; $window = $null
$safeToQuit = $false; $phase = 'initialization'
try {
    $phase = 'com_create'; $trace.phases.com_create = 'running'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $trace.phases.com_create = 'pass'

    $phase = 'version_check'; $trace.phases.version_check = 'running'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne '11.0.0.9136') { throw 'EDITOR_CHILD_VERSION_MISMATCH' }
    $trace.phases.version_check = 'pass'

    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'EDITOR_CHILD_DOCUMENT_ADD_FAILED' }
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    [void]$document.SetActive_XHwpDocument()
    $trace.phases.window_visible = 'pass'
    Write-Output 'P07_EDITOR_SMOKE_ACCESS_OR_MANUAL_ACTION_REQUIRED'
    Write-Output ('P07_EDITOR_SMOKE_INSTRUCTIONS ' + $instructionPath)

    $phase = 'open_input'; $trace.phases.open_input = 'running'
    $opened = $document.Open($inputPath, 'HWPX', 'lock:false;setcurdir:false')
    if ($opened -eq $false) { throw 'EDITOR_CHILD_OPEN_FAILED' }
    [void]$document.SetActive_XHwpDocument()
    $trace.phases.open_input = 'pass'

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $phase = 'manual_attestation'; $trace.phases.manual_attestation = 'running'
    while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $attestationPath -PathType Leaf)) {
        Start-Sleep -Milliseconds 500
    }
    if (-not (Test-Path -LiteralPath $attestationPath -PathType Leaf)) {
        throw 'EDITOR_CHILD_MANUAL_TIMEOUT'
    }
    $attestationBytes = [IO.File]::ReadAllBytes($attestationPath)
    if ($attestationBytes.Length -le 0 -or $attestationBytes.Length -gt 1048576) {
        throw 'EDITOR_CHILD_ATTESTATION_LIMIT'
    }
    $attestation = [Text.Encoding]::UTF8.GetString($attestationBytes) | ConvertFrom-Json
    if ([string]$attestation.schema_version -cne 'hwpx-agent.p07-09-equation-editor-manual-attestation/v1' -or
        [string]$attestation.plan_sha256 -cne [string]$plan.plan_sha256 -or
        [string]$attestation.double_click -cne 'passed' -or
        [string]$attestation.editor_visible -cne 'passed' -or
        [string]$attestation.one_token_change -cne 'passed' -or
        [string]$attestation.editor_closed_after_commit -cne 'passed' -or
        [string]$attestation.user_performed_all_clicks_and_typing -cne 'passed' -or
        [bool]$attestation.computer_use_click_or_type_invoked) {
        throw 'EDITOR_CHILD_ATTESTATION_MISMATCH'
    }
    $screenshots = @(
        [string]$attestation.before_screenshot_sha256,
        [string]$attestation.editor_open_screenshot_sha256,
        [string]$attestation.changed_editor_screenshot_sha256,
        [string]$attestation.saved_document_screenshot_sha256
    )
    foreach ($digest in $screenshots) { Assert-Digest -Value $digest -Code 'EDITOR_CHILD_SCREENSHOT_DIGEST_INVALID' }
    if (@($screenshots | Select-Object -Unique).Count -ne 4) { throw 'EDITOR_CHILD_SCREENSHOT_EVIDENCE_REUSED' }
    $trace.manual_attestation_sha256 = Get-Sha256File -Path $attestationPath
    $trace.phases.manual_attestation = 'pass'

    $phase = 'output_stable'; $trace.phases.output_stable = 'running'
    $trace.output_sha256 = Wait-StableFile -Path $outputPath -Deadline $deadline
    if ($trace.output_sha256 -ceq [string]$plan.source.artifact_sha256) {
        throw 'EDITOR_CHILD_OUTPUT_DID_NOT_CHANGE'
    }
    $trace.phases.output_stable = 'pass'

    $phase = 'input_immutable'; $trace.phases.input_immutable = 'running'
    if ((Get-Sha256File -Path $inputPath) -cne [string]$plan.source.artifact_sha256) {
        throw 'EDITOR_CHILD_INPUT_MUTATED'
    }
    $trace.phases.input_immutable = 'pass'
    $safeToQuit = $true

    $phase = 'close_after_save'; $trace.phases.close_after_save = 'running'
    [void]$document.Close($false)
    Clear-ComObject -Value $document; $document = $null
    $trace.phases.close_after_save = 'pass'

    $phase = 'reopen'; $trace.phases.reopen = 'running'
    $document = $documents.Add($false)
    if ($null -eq $document -or $document.Open($outputPath, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'EDITOR_CHILD_REOPEN_FAILED'
    }
    [void]$document.SetActive_XHwpDocument()
    if ((Get-Sha256File -Path $outputPath) -cne [string]$trace.output_sha256) {
        throw 'EDITOR_CHILD_REOPEN_ARTIFACT_DRIFT'
    }
    $trace.phases.reopen = 'pass'

    $phase = 'reopen_close'; $trace.phases.reopen_close = 'running'
    [void]$document.Close($false)
    Clear-ComObject -Value $document; $document = $null
    $trace.phases.reopen_close = 'pass'

    $phase = 'quit'; $trace.phases.quit = 'running'
    $hwp.Quit(); $trace.phases.quit = 'pass'
    $trace.state = 'pass'
}
catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'EDITOR_CHILD_EXCEPTION' }
    if ($trace.phases.Contains($phase)) { $trace.phases[$phase] = 'failed' }
}
finally {
    if ($safeToQuit) {
        if ($null -ne $document) { try { [void]$document.Close($false) } catch { }; Clear-ComObject $document }
        if ($null -ne $hwp -and $trace.phases.quit -ne 'pass') { try { $hwp.Quit(); $trace.phases.quit = 'pass' } catch { } }
    }
    Clear-ComObject $window; Clear-ComObject $documents; Clear-ComObject $hwp
    [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Write-JsonNoOverwrite -Path $tracePath -Value $trace
if ($trace.state -ne 'pass') { exit 2 }
