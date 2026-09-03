[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
function Read-RepoFile([string]$relativePath) {
    Get-Content -LiteralPath (Join-Path $root $relativePath) -Raw
}

$contracts = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentContracts.cs'
$validation = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentValidation.cs'
$isolation = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WorkerIsolation.cs'
$service = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsAgentService.cs'
$workspace = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentWorkspace.cs'
$smoke = Read-RepoFile 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\Program.cs'
$audit = Read-RepoFile 'implementation\p10\tools\audit-current-worker-isolation.ps1'
$policy = Read-RepoFile 'implementation\p10\isolation\p10-current-pc-local-worker-policy.json'
$ci = Read-RepoFile 'tools\p01\run_ci.py'

$checks = [ordered]@{
    configuration_requires_isolation_pin = $contracts -match 'WorkerIsolationPolicyPin WorkerIsolation' -and
        $contracts -match 'interface IWorkerIsolationAttestor'
    exact_target_and_baseline_binding = $validation -match 'policy\.TargetProfileId, target\.ProfileId' -and
        $validation -match 'policy\.HostBaselineSha256, target\.EnvironmentDigest' -and
        $isolation -match 'policy\.HostIsolationIdentitySha256'
    single_active_job_enforced = $validation -match 'configuration\.AvailableJobSlots != 1' -and
        $service -match 'Interlocked\.CompareExchange\(ref activeRun, 1, 0\)'
    prelease_attestation_before_rpc = $service.IndexOf('isolationGuard.VerifyBeforeLease()', [StringComparison]::Ordinal) -lt
        $service.IndexOf('.AcquireLeaseAsync(', [StringComparison]::Ordinal)
    post_job_audit_before_terminal_journal = $service.IndexOf('isolationGuard.VerifyAfterJob(isolationBefore)', [StringComparison]::Ordinal) -lt
        $service.LastIndexOf('ownership.WriteTerminalAsync', [StringComparison]::Ordinal)
    residue_downgrades_unknown = $service -match 'BridgeErrorCode\.CleanupFailed' -and
        $service -match 'executorInvoked \? ExecutionState\.UnknownOutcome : ExecutionState\.Failed'
    marked_workspace_must_be_empty = $workspace -match 'VerifyNoJobSandboxResidue' -and
        $workspace -match 'Directory\.EnumerateFileSystemEntries\(sandboxRoot\)\.Any\(\)'
    current_attestor_is_development_only = $isolation -match 'CurrentPcWorkerIsolationAttestor' -and
        $isolation -match 'policy\.Scope != WorkerIsolationScope\.CurrentPcInteractiveDevelopment'
    privacy_preserving_identity_hashes = $isolation -match 'HashSafeIdentity\("identity"' -and
        $isolation -match 'ReadMachineBindingSha256' -and
        $isolation -match 'HashSafeIdentity\("host-isolation-identity"' -and
        $isolation -match 'CryptographicOperations\.ZeroMemory\(bytes\)' -and
        $isolation -notmatch 'Console\.WriteLine\(.*identityValue'
    live_session_and_desktop_observed = $isolation -match 'WindowsIdentity\.GetCurrent' -and
        $isolation -match 'GetProcessWindowStation' -and
        $isolation -match 'GetThreadDesktop' -and
        $isolation -match 'process\.SessionId > 0'
    current_attestor_does_not_claim_dedicated_controls = $isolation -match 'DedicatedIdentityAndProfile: false' -and
        $isolation -match 'OsNetworkDefaultDeny: false' -and
        $isolation -match 'ClipboardIsolated: false' -and
        $isolation -match 'PrinterResidueClean: false'
    dedicated_mode_requires_all_controls = $isolation -match '!observation\.DedicatedIdentityAndProfile' -and
        $isolation -match '!observation\.PrivateWindowStation' -and
        $isolation -match '!observation\.OsNetworkDefaultDeny' -and
        $isolation -match '!observation\.ClipboardIsolated' -and
        $isolation -match '!observation\.ProfileResidueClean' -and
        $isolation -match '!observation\.RecoveryResidueClean' -and
        $isolation -match '!observation\.PrinterResidueClean'
    current_policy_forbids_overclaim = $policy -match '"production_isolation_qualified": false' -and
        $policy -match '"release_routable": false' -and
        $policy -match '"current_policy_must_not_be_promoted": true'
    current_policy_denies_high_risk_inputs = $policy -match '"external_network_request_denied": true' -and
        $policy -match '"clipboard_request_denied": true' -and
        $policy -match '"macro_execution_denied": true' -and
        $policy -match '"ole_activation_denied": true'
    host_drift_rejected_before_rpc_test = $smoke -match 'IsolationDriftIsRejectedBeforeRpcAsync' -and
        $smoke -match 'host baseline drift made an outbound RPC'
    dedicated_negative_and_positive_tests = $smoke -match 'DedicatedIsolationRequiresEveryControlAsync' -and
        $smoke -match 'DedicatedIsolationAcceptsCompleteAttestationAsync'
    post_job_residue_test = $smoke -match 'PostJobResidueBecomesUnknownOutcomeAsync' -and
        $smoke -match 'BridgeErrorCode\.CleanupFailed'
    stale_workspace_test = $smoke -match 'StaleWorkspaceResidueIsRejectedAtStartupAsync' -and
        $smoke -match 'AgentProtocolError\.CleanupResidue'
    actual_probe_reads_no_user_document = $smoke -match 'user_document_scanned = false' -and
        $smoke -match 'raw_document_text_present = false'
    actual_probe_cleanup_is_bounded = $smoke -match 'DeleteActualProbeRoot' -and
        $smoke -match 'StartsWith\(tempPrefix' -and
        $smoke -match 'DeleteTreeWithoutFollowingReparsePoints' -and
        $smoke -match 'FileAttributes\.ReparsePoint'
    actual_audit_is_read_only_and_private = $audit -match 'profile_wide_residue_scan_performed = \$false' -and
        $audit -match 'clipboard_content_read = \$false' -and
        $audit -match 'system_setting_changed = \$false' -and
        $audit -match 'Get-NetFirewallProfile -PolicyStore ActiveStore' -and
        $audit -match 'firewall profile observation did not complete' -and
        $audit -notmatch 'Get-Clipboard|Set-Clipboard'
    audit_output_is_bounded_no_overwrite = $audit -match 'implementation/p10/evidence' -and
        $audit -match 'output already exists' -and
        $audit -match '\[System\.IO\.File\]::Move\(\$partialPath, \$outputFull\)'
    policy_and_audit_schemas_exist = (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\worker-isolation-policy-v1.schema.json')) -and
        (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\worker-isolation-audit-v1.schema.json'))
    ci_runs_isolation_checks = $ci -match 'Test-Hancom2020Isolation\.ps1' -and
        $ci -match 'validate_worker_isolation\.py'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-08-isolation-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 5

if ($failed.Count -ne 0) { exit 2 }
