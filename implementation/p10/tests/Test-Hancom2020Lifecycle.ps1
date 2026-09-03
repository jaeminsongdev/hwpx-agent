[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$session = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomSession.cs'
) -Raw
$handler = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomLifecycleCommandHandler.cs'
) -Raw
$server = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\StaWorkerServer.cs'
) -Raw
$hostProgram = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker.Host\Program.cs'
) -Raw
$hostProject = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker.Host\HwpxAgent.WindowsWorker.Host.csproj'
) -Raw
$protocol = Get-Content -LiteralPath (
    Join-Path $root 'protocol\proto\hwpx_agent\windows_bridge\v1\windows_bridge.proto'
) -Raw
$smoke = Get-Content -LiteralPath (
    Join-Path $root 'workers\windows-hancom-worker\tests\HwpxAgent.WindowsWorker.LifecycleSmoke\Program.cs'
) -Raw
$harnessPath = Join-Path $root 'implementation\p10\tools\invoke-hancom-2020-lifecycle.ps1'
$harness = Get-Content -LiteralPath $harnessPath -Raw

$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $harnessPath,
    [ref]$tokens,
    [ref]$parseErrors
)

$checks = [ordered]@{
    harness_parses = $parseErrors.Count -eq 0
    exact_current_profile = $session -match 'hancom-hangul-2020-secondary' -and
        $session -match 'HWPFrame\.HwpObject\.2'
    registry32_only = $session -match 'RegistryView\.Registry32'
    x86_process_required = $session -match 'Environment\.Is64BitProcess' -and
        $session -match 'PeMachineI386'
    exact_executable_identity = $session -match 'ExecutableSha256' -and
        $session -match 'FileVersionInfo' -and $session -match 'ReadPeMachine'
    no_preexisting_hwp = $session -match 'PreexistingProcess' -and
        $session -match 'GetProcessesByName\("Hwp"\)'
    bounded_owned_process = $session -match 'startTimeUtcTicks' -and
        $session -match 'SessionId' -and $session -match 'MainModule\?\.FileName'
    bounded_owned_kill = $session -match 'VerifyIdentity\(owned\)' -and
        $session -match 'Kill\(entireProcessTree: false\)'
    real_com_activation = $session -match 'Type\.GetTypeFromProgID' -and
        $session -match 'Activator\.CreateInstance'
    typed_lifecycle_only = $session -match 'XHwpDocuments' -and
        $session -match '\.Open\(input\.Path, "HWPX"' -and
        $session -match '\.Close\(false\)' -and $session -match 'automation\.Quit\(\)'
    no_public_raw_action_surface = $protocol -notmatch '(?m)^\s*string\s+(action_id|parameter_set_id|item_name)\s*=' -and
        $session -notmatch 'RegisterModule\((?!"FilePathCheckDLL", registrationName\))'
    source_rehashed = $session -match 'InputChanged' -and
        $session -match 'ValidateIntegrity\(HancomLifecycleError\.InputChanged\)'
    handler_typed_commands = $handler -match 'StartSession' -and
        $handler -match 'OpenDocument' -and $handler -match 'ExecutePlan' -and
        $handler -match 'CloseSession'
    open_requires_resolver = $handler -match 'p10-05-path-approval-required'
    server_finally_cleanup = $server -match 'IStaCommandHandlerCleanup cleanup' -and
        $server -match 'WaitAsync\(TimeSpan\.FromSeconds\(10\)\)'
    production_host_x86 = $hostProject -match '<PlatformTarget>x86</PlatformTarget>' -and
        $hostProgram -match 'new HancomLifecycleCommandHandler\(securityAdapter\)'
    fake_failure_and_repeat_tests = $smoke -match 'InputMutationFailsBeforeOpenReceiptAsync' -and
        $smoke -match 'CleanupFailureStillRunsEveryStepAsync' -and
        $smoke -match 'index < 32'
    actual_safe_output = $smoke -match 'HANCOM_LIFECYCLE_PASS cycles=3 input_unchanged=true remaining=0' -and
        $smoke -match 'HANCOM_LIFECYCLE_SMOKE_FAILED'
    harness_stages_copy = $harness -match 'FileMode\]::CreateNew' -and
        $harness -match 'FileAttributes\]::ReadOnly'
    harness_is_bounded = $harness -match 'ValidateRange\(30, 600\)' -and
        $harness -match '\$child\.WaitForExit\(\$TimeoutSeconds \* 1000\)'
    harness_cleanup_is_identity_checked = $harness -match 'CreationDate' -and
        $harness -match 'SessionId' -and $harness -match 'ExecutableSha256' -and
        $harness -match '-Automation\\s\+\-Embedding'
    harness_source_preserved = $harness -match 'sourceUnchanged' -and
        $harness -match 'staged_input_removed'
    no_computer_use_input = $harness -match 'computer_use_click_or_type_invoked = \$false'
    no_external_or_registry_mutation = $harness -match 'external_network_invoked = \$false' -and
        $harness -match 'registry_or_system_setting_changed = \$false'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
$result = [ordered]@{
    schema_version = 'hwpx-agent.p10-04-lifecycle-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
}
$result | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 2 }
