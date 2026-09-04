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
$probe = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\RuntimeProbe.cs'
$service = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsAgentService.cs'
$smoke = Read-RepoFile 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\Program.cs'
$policy = Read-RepoFile 'implementation\p10\probe\p10-current-pc-runtime-probe-policy.json'
$validator = Read-RepoFile 'tools\p10\validate_runtime_probe.py'
$audit = Read-RepoFile 'implementation\p10\tools\audit-current-runtime-probe.ps1'
$ci = Read-RepoFile 'tools\p01\run_ci.py'

$probeIndex = $service.IndexOf('EnsureRoutableRuntimeProbeAsync(cancellationToken)', [StringComparison]::Ordinal)
$leaseIndex = $service.IndexOf('.AcquireLeaseAsync(CreateLeaseRequest()', [StringComparison]::Ordinal)
$uploadIndex = $service.IndexOf('artifactStore.UploadAsync(', [StringComparison]::Ordinal)
$reportIndex = $service.IndexOf('ReportProbeAsync(materialized.Receipt', [StringComparison]::Ordinal)

$checks = [ordered]@{
    mandatory_probe_policy_and_collector = $contracts -match 'RuntimeProbePolicyPin RuntimeProbe' -and
        $contracts -match 'interface IRuntimeProbeCollector'
    bounded_probe_policy = $validation -match 'MaximumProbeAgeSeconds is < 30 or > 86_400' -and
        $validation -match 'MaximumEvidenceBytes is < 1_024 or > 1_048_576'
    probe_precedes_lease = $probeIndex -ge 0 -and $leaseIndex -gt $probeIndex
    evidence_upload_precedes_report = $uploadIndex -ge 0 -and $reportIndex -gt $uploadIndex
    report_acceptance_and_routability_required = $service -match '!routable' -and
        $service -match 'RuntimeProbeNotRoutable'
    bounded_probe_cache = $service -match 'routableProbeExpiresAtUnixMs' -and
        $service -match 'MaximumProbeAgeSeconds'
    exact_profile_match_required_locally = $probe -match '!observation\.TargetProfile\.Equals\(configuration\.TargetProfile\)' -and
        $probe -match 'AgentProtocolError\.ProfileMismatch'
    stale_or_future_probe_rejected = $probe -match 'ObservedAtUnixMs > checked\(nowUnixMs \+ 300_000UL\)' -and
        $probe -match 'MaximumProbeAgeSeconds'
    privacy_flags_fail_closed = $probe -match 'observation\.RawPathStored' -and
        $probe -match 'observation\.UserDocumentScanned' -and
        $probe -match 'observation\.HancomProcessStarted'
    health_contradictions_rejected = $probe -match 'hasRequiredFailure' -and
        $probe -match 'healthConsistent'
    deterministic_capability_set = $probe -match 'OrderBy\(item => item\.CapabilityId, StringComparer\.Ordinal\)' -and
        $probe -match 'capabilitySetSha256'
    evidence_is_content_addressed = $probe -match 'Evidence = new ArtifactRef' -and
        $probe -match 'Sha256 = evidenceSha256'
    exact_executable_hash_and_version = $probe -match 'FileVersionInfo\.GetVersionInfo' -and
        $probe -match 'TryHashPlainFile\(pin\.TargetExecutablePath'
    executable_architecture_read_from_pe = $probe -match 'TryReadPeMachine' -and
        $probe -match '0x014c => "x86"'
    com_registration_is_registry32 = $probe -match 'RegistryHive\.ClassesRoot, RegistryView\.Registry32' -and
        $probe -match 'LocalServer32'
    capability_registry_digest_checked = $probe -match 'pin\.CapabilityRegistryPath' -and
        $probe -match 'pin\.CapabilityRegistrySha256'
    pinned_evidence_digests_checked = $probe -match 'foreach \(var evidence in pin\.EvidencePins\)' -and
        $probe -match 'evidence\.Sha256'
    security_module_registry_is_read_only = $probe -match 'RegistryHive\.CurrentUser, RegistryView\.Registry32' -and
        $probe -match 'HwpAutomation\\\\Modules' -and
        $probe -match 'writable: false'
    missing_security_module_is_unroutable = $probe -match 'agent\.security_file_path_module' -and
        $probe -match 'RuntimeCapabilityState\.Unavailable' -and
        $probe -match 'required: true'
    existing_hancom_process_blocks_route = $probe -match 'Process\.GetProcessesByName\("Hwp"\)' -and
        $probe -match 'agent\.zero_hancom_processes'
    current_probe_does_not_start_hancom = $probe -notmatch 'Process\.Start|CreateProcess|New-Object -ComObject' -and
        $probe -match 'HancomProcessStarted: false'
    profile_mismatch_no_rpc_test = $smoke -match 'RuntimeProbeProfileMismatchMakesNoRpcAsync' -and
        $smoke -match 'profile-mismatched runtime probe made a report or lease RPC'
    unroutable_no_lease_test = $smoke -match 'UnroutableRuntimeProbeReportsButNeverAcquiresLeaseAsync' -and
        $smoke -match 'SequenceEqual\(\["ReportProbe"\]\)'
    cache_and_privacy_tests = $smoke -match 'RuntimeProbeReportsBeforeLeaseAndCachesAdmissionAsync' -and
        $smoke -match 'RuntimeProbeRejectsPrivacyAndHealthContradictionsAsync'
    actual_current_host_probe_mode = $smoke -match '--p10-10-current-host-runtime-probe' -and
        $smoke -match 'CurrentPcRuntimeProbeCollector' -and
        $smoke -match 'AcquireLeaseCalls != 0'
    policy_is_current_pc_only = $policy -match '"current_pc_local_development_only": true' -and
        $policy -match '"production_or_provider_qualified": false' -and
        $policy -match '"another_host_requires_independent_evidence": true'
    schema_and_validator_exist = (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\runtime-probe-policy-v1.schema.json')) -and
        (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\runtime-probe-audit-v1.schema.json')) -and
        $validator -match 'Draft202012Validator'
    audit_is_bounded_no_overwrite = $audit -match 'TimeoutSeconds = 120' -and
        $audit -match 'output already exists' -and
        $audit -match 'source tree' -and
        $audit -match '\[System\.IO\.File\]::Move\(\$partialPath, \$outputFull\)'
    ci_runs_runtime_probe_checks = $ci -match 'Test-Hancom2020RuntimeProbe\.ps1' -and
        $ci -match 'validate_runtime_probe\.py'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-10-runtime-probe-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 5

if ($failed.Count -ne 0) { exit 2 }
