[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$boundedPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\invoke-hancom-2020-bounded-readback.ps1'
)).Path
$enginePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\run-hancom-2020-tab-readback.ps1'
)).Path
$boundedTokens = $null
$boundedErrors = $null
$engineTokens = $null
$engineErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $boundedPath, [ref]$boundedTokens, [ref]$boundedErrors
)
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $enginePath, [ref]$engineTokens, [ref]$engineErrors
)
$bounded = [System.IO.File]::ReadAllText($boundedPath)
$engine = [System.IO.File]::ReadAllText($enginePath)

function Test-ProgressObservation {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('preflight_terminal', 'open_running', 'skipped_open')]
        [string]$Case
    )

    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $boundedPath, [ref]$null, [ref]$null
    )
    $definition = @($ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -ceq 'Read-ProgressJournal'
    }, $true))
    if ($definition.Count -ne 1) { return $false }
    . ([scriptblock]::Create($definition[0].Extent.Text))

    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    $directory = Join-Path $temporaryRoot (
        'hwpx-agent-p05-progress-observation-' + [guid]::NewGuid().ToString('N')
    )
    $path = Join-Path $directory 'progress.jsonl'
    [void][System.IO.Directory]::CreateDirectory($directory)
    $event = {
        param($Sequence, $Phase, $State, $HwpProcessId)
        [ordered]@{
            schema_version = 'hwpx-agent.p05-hancom-readback-progress/v1'
            sequence = $Sequence
            recorded_at_utc = '2026-09-07T00:00:00.0000000Z'
            worker_process_id = 123
            hwp_process_id = $HwpProcessId
            phase = $Phase
            state = $State
            raw_document_text_present = $false
        } | ConvertTo-Json -Compress
    }
    try {
        $lines = if ($Case -ceq 'preflight_terminal') {
            @(
                (& $event 1 'preflight' 'pass' $null),
                (& $event 2 'terminal' 'failed' $null)
            )
        }
        elseif ($Case -ceq 'skipped_open') {
            @(
                (& $event 1 'preflight' 'pass' $null),
                (& $event 2 'read_input' 'running' 456)
            )
        }
        else {
            @(
                (& $event 1 'preflight' 'pass' $null),
                (& $event 2 'com_create' 'pass' 456),
                (& $event 3 'open_input' 'running' 456)
            )
        }
        [System.IO.File]::WriteAllText(
            $path, ($lines -join "`n"), [System.Text.UTF8Encoding]::new($false)
        )
        $summary = Read-ProgressJournal -Path $path
        if ($Case -ceq 'preflight_terminal') {
            return [bool]$summary.valid -and
                -not [bool]$summary.window_visible_for_user_access -and
                [string]$summary.observed_phase -ceq 'preflight'
        }
        if ($Case -ceq 'skipped_open') {
            return [bool]$summary.valid -and
                -not [bool]$summary.window_visible_for_user_access -and
                [string]$summary.observed_phase -ceq 'read_input'
        }
        return [bool]$summary.valid -and
            [bool]$summary.window_visible_for_user_access -and
            [string]$summary.observed_phase -ceq 'open_input'
    }
    finally {
        if ([System.IO.File]::Exists($path)) { [System.IO.File]::Delete($path) }
        if ([System.IO.Directory]::Exists($directory) -and
            [System.IO.Path]::GetFullPath($directory).StartsWith(
                $temporaryRoot + '\hwpx-agent-p05-progress-observation-',
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            [System.IO.Directory]::Delete($directory, $false)
        }
    }
}

$checks = [ordered]@{
    bounded_parses = $boundedErrors.Count -eq 0
    engine_parses = $engineErrors.Count -eq 0
    x86_child_runtime = $bounded -match 'SpecialFolder\]::SystemX86' -and $bounded -match 'WindowsPowerShell\\v1\.0\\powershell\.exe'
    x86_child_runtime_bounded = $bounded -match 'powerShellItem\.Length -gt 16777216' -and $bounded -match 'powerShellItem\.Attributes.*ReparsePoint'
    no_pshome_runtime_guess = $bounded -notmatch 'Join-Path \$PSHOME'
    timeout_range = $bounded -match 'ValidateRange\(30, 900\).*TimeoutSeconds = 300'
    child_timeout = $bounded -match 'WaitForExit\(\$TimeoutSeconds \* 1000\)'
    timed_out_child_killed = $bounded -match 'if \(-not \$exitedWithinTimeout\)' -and $bounded -match '\$child\.Kill\(\)'
    cleanup_same_session = $bounded -match 'candidate\.SessionId -eq \$SessionId'
    cleanup_creation_bound = $bounded -match 'createdAt -ge \$StartedAt\.AddSeconds\(-2\)'
    cleanup_exact_binary_hash = $bounded -match 'Get-Sha256File -Path \$processPath.*ExpectedSha256'
    cleanup_automation_command = $bounded -match '-Automation\\s\+\-Embedding\\s\*\$'
    bounded_input = $bounded -match 'Length -gt 8388608' -and $engine -match 'Length -gt 8388608'
    reparse_refused = $bounded -match 'FIXTURE_BOUNDARY_REPARSE_POINT' -and $engine -match 'FIXTURE_BOUNDARY_REPARSE_POINT'
    bounded_progress = $bounded -match 'Length -gt 65536' -and $bounded -match 'expectedSequence -gt 32'
    progress_preserves_iso_time = $bounded -match 'PSVersionTable\.PSVersion\.Major -ge 7' -and $bounded -match 'ConvertFrom-Json -DateKind String'
    progress_windows_powershell_compatible = $bounded -match 'else\s*\{\s*# Windows PowerShell 5\.1 has no -DateKind parameter[\s\S]*?\$line \| ConvertFrom-Json\s*\}'
    bounded_terminal_trace = $bounded -match 'innerItem\.Length -gt 0 -and \$innerItem\.Length -le 131072'
    progress_exact_properties = $bounded -match 'allowedProperties -cnotcontains \$property'
    progress_exact_types = $bounded -match 'sequenceIsInteger' -and $bounded -match 'privacyIsBoolean'
    progress_pid_correlation = $bounded -match 'workerProcessId -ne \[long\]\$event\.worker_process_id' -and $bounded -match 'hwpProcessId -ne \[long\]\$event\.hwp_process_id'
    progress_terminal_required = $bounded -match "progress\.last_phase -cne 'terminal'" -and $bounded -match "progress\.last_state -cne 'pass'"
    progress_observed_phase_preserved = $bounded -match 'summary\.observed_phase = \[string\]\$event\.phase' -and $bounded -match 'failed_phase = \$observedFailurePhase'
    progress_window_visibility_inferred = $bounded -match 'exact prefix only after setting XHwpWindows\.Visible' -and $bounded -match 'window_visible_for_user_access = \$windowVisibleForUserAccess'
    terminal_without_open_is_not_visible = Test-ProgressObservation -Case 'preflight_terminal'
    open_running_is_visible = Test-ProgressObservation -Case 'open_running'
    skipped_open_is_not_visible = Test-ProgressObservation -Case 'skipped_open'
    inner_trace_correlated = $bounded -match "trace\.schema_version -ceq 'hwpx-agent\.p05-04-hancom-2020-tab-readback/v1'" -and $bounded -match 'trace\.input_sha256 -ceq \$ExpectedInputSha256'
    wrapper_rechecks_input_after_child = $bounded -match 'trace\.input_unchanged = \(Get-Sha256File -Path \$input\)'
    inner_failure_phase_preserved = $bounded -match 'childReportedFailure = \$childExitCode -ne 0' -and $bounded -match 'if \(-not \$childReportedFailure\)'
    create_new_terminal_trace = $bounded -match 'FileMode\]::CreateNew'
    explicit_success_exit = $bounded -match "trace\.state -cne 'pass'\) \{ exit 2 \}\s+exit 0"
    progress_privacy_constant = $engine -match 'raw_document_text_present = \$false'
    no_register_module = ($bounded + $engine) -notmatch '(?i)\.RegisterModule\s*\('
    no_ui_input = ($bounded + $engine) -notmatch '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
    no_network = ($bounded + $engine) -notmatch '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)'
    no_registry_write = ($bounded + $engine) -notmatch '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty)'
}
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p05-bounded-readback-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
