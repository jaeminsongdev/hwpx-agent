[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$adapter = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomSecurityAdapter.cs') -Raw
$session = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomSession.cs') -Raw
$handler = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomLifecycleCommandHandler.cs') -Raw
$hostProgram = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker.Host\Program.cs') -Raw
$agentWorkspace = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentWorkspace.cs') -Raw
$agentService = Get-Content -LiteralPath (Join-Path $root 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsAgentService.cs') -Raw
$moduleProbe = Get-Content -LiteralPath (Join-Path $root 'implementation\p10\tools\probe-hancom-2020-security-module.ps1') -Raw
$protocol = Get-Content -LiteralPath (Join-Path $root 'protocol\proto\hwpx_agent\windows_bridge\v1\windows_bridge.proto') -Raw

$checks = [ordered]@{
    exact_module_type = $session -match 'RegisterModule\("FilePathCheckDLL", registrationName\)'
    no_registry_write = $adapter -notmatch '(?i)CreateSubKey|SetValue\s*\('
    registry_view_32 = $adapter -match 'RegistryView\.Registry32'
    registry_current_user = $adapter -match 'RegistryHive\.CurrentUser'
    exact_registry_key = $adapter -match 'Software\\\\HNC\\\\HwpAutomation\\\\Modules'
    registry_value_string_only = $adapter -match 'RegistryValueKind\.String'
    module_hash_pinned = $adapter -match 'SHA256\.HashData\(guard\)' -and
        $adapter -match 'FileShare\.Read'
    module_x86_pinned = $adapter -match 'PeMachineI386 = 0x014c'
    module_path_absolute_before_normalize = $adapter.IndexOf('IsPathFullyQualified(configuredPath)') -ge 0 -and
        $adapter.IndexOf('IsPathFullyQualified(configuredPath)') -lt $adapter.IndexOf('GetFullPath(configuredPath)')
    module_file_not_reparse = $adapter -match 'file\.Attributes & FileAttributes\.ReparsePoint'
    immutable_lease_required = $adapter -match 'leaseFile\.Attributes & FileAttributes\.ReadOnly'
    bounded_lease = $adapter -match 'MaximumLeaseBytes = 8 \* 1024'
    unknown_json_rejected = $adapter -match 'JsonUnmappedMemberHandling\.Disallow'
    lease_expiry_bounded = $adapter -match 'MaximumLeaseLifetime = TimeSpan\.FromMinutes\(30\)'
    sandbox_marker_required = $adapter -match '\.hwpx-agent-sandbox'
    single_use = $adapter -match 'CompareExchange\(ref consumed, 1, 0\)'
    guarded_input = $session -match 'FileShare\.Read' -and $session -match 'OpenGuarded'
    read_only_input = $session -match 'FileAttributes\.ReadOnly'
    command_identity_bound = $adapter -match 'staged\.Artifact\.Sha256' -and $adapter -match 'staged\.SandboxHandle'
    production_host_requires_lease = $hostProgram -match 'arguments\["--security-lease"\]'
    public_protocol_path_free = $protocol -match 'sandbox_handle is an opaque token' -and $protocol -notmatch '(?m)^\s*string\s+(absolute_)?path\s*='
    opaque_handle_bridge = $adapter -match 'InputHandlePattern' -and
        $adapter -match '\^\[a-z\]\[a-z0-9_-\]\{2,63\}\$' -and
        $agentWorkspace -match 'HancomApprovedInputFileName = "hancom_approved_input\.hwpx"'
    agent_private_copy_verified = $agentWorkspace -match 'CopyAndVerifyAsync\(source, partialInput, input\.Artifact' -and
        $agentWorkspace -match 'FileAttributes\.ReadOnly'
    agent_lease_execution_bound = $agentWorkspace -match 'SessionId = assignment\.ExecutionId' -and
        $agentWorkspace -match 'FencingToken = assignment\.FencingToken' -and
        $agentWorkspace -match 'CompareExchange\(ref hancomSecurityPrepared, 1, 0\)'
    agent_service_supplies_trusted_pin = $agentService -match 'configuration\.HancomSecurityModule' -and
        $agentWorkspace -match 'PrepareHancomWorkerSecurityLeaseAsync'
    module_probe_read_only_registry32 = $moduleProbe -match 'RegistryView\]::Registry32' -and
        $moduleProbe -match 'OpenSubKey\(''Software\\HNC\\HwpAutomation\\Modules'', \$false\)' -and
        $moduleProbe -notmatch '(?i)CreateSubKey|SetValue\s*\('
    module_probe_redacts_path = $moduleProbe -match 'registered_path_present_in_evidence = \$false' -and
        $moduleProbe -match 'raw_registry_value_present_in_evidence = \$false'
    handler_requires_adapter = $handler -match 'p10-05-path-approval-required'
    module_failure_typed = $handler -match 'SecurityModuleRegistrationFailed => BridgeErrorCode\.PolicyDenied'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object { $_.Key })
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-05-security-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 4

if ($failed.Count -ne 0) {
    exit 1
}
