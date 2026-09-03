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
    bounded_terminal_trace = $bounded -match 'innerItem\.Length -gt 0 -and \$innerItem\.Length -le 131072'
    progress_exact_properties = $bounded -match 'allowedProperties -cnotcontains \$property'
    progress_exact_types = $bounded -match 'sequenceIsInteger' -and $bounded -match 'privacyIsBoolean'
    progress_pid_correlation = $bounded -match 'workerProcessId -ne \[long\]\$event\.worker_process_id' -and $bounded -match 'hwpProcessId -ne \[long\]\$event\.hwp_process_id'
    progress_terminal_required = $bounded -match "progress\.last_phase -cne 'terminal'" -and $bounded -match "progress\.last_state -cne 'pass'"
    inner_trace_correlated = $bounded -match "trace\.schema_version -ceq 'hwpx-agent\.p05-04-hancom-2020-tab-readback/v1'" -and $bounded -match 'trace\.input_sha256 -ceq \$ExpectedInputSha256'
    create_new_terminal_trace = $bounded -match 'FileMode\]::CreateNew'
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
