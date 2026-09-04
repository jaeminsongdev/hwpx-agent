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
$supervisor = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentWorkerSupervisor.cs'
$ownedProcess = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsOwnedWorkerProcess.cs'
$service = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsAgentService.cs'
$workspace = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentWorkspace.cs'
$smoke = Read-RepoFile 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\Program.cs'
$policy = Read-RepoFile 'implementation\p10\supervision\p10-current-pc-worker-supervisor-policy.json'
$audit = Read-RepoFile 'implementation\p10\tools\audit-current-worker-supervisor.ps1'
$validator = Read-RepoFile 'tools\p10\validate_worker_supervision.py'
$ci = Read-RepoFile 'tools\p01\run_ci.py'

$checks = [ordered]@{
    mandatory_supervisor_policy_pin = $contracts -match 'WorkerSupervisorPolicyPin WorkerSupervisor' -and
        $validation -match 'ValidateWorkerSupervisorPolicy\(configuration\.WorkerSupervisor\)'
    bounded_supervisor_policy = $validation -match 'CooperativeStopTimeoutSeconds is 0 or > 60' -and
        $validation -match 'MaximumJobsPerWorker is 0 or > 100' -and
        $validation -match 'MaximumPrivateMemoryBytes is < 67_108_864'
    command_timeout_is_separate = $supervisor -match 'ResourceLimits\.CommandTimeoutSeconds' -and
        $service -match 'ResourceLimits\.JobTimeoutSeconds' -and
        $validation -match 'CommandTimeoutSeconds >= limits\.JobTimeoutSeconds'
    executor_invocation_is_inside_supervision = $service -match 'await supervisor' -and
        $service -notmatch 'await executor\s*\.ExecuteAsync'
    synchronous_worker_failure_is_contained = $supervisor -match 'Task\.FromException<AgentJobResult>' -and
        $supervisor -match 'ContainInterruptedExecutionAsync'
    cooperative_cancel_is_bounded = $supervisor -match 'CooperativeStopTimeoutSeconds' -and
        $supervisor -match 'RequestCancellationAsync'
    reconciliation_is_bounded = $supervisor -match 'ReconciliationTimeoutSeconds' -and
        $supervisor -match 'WaitAsync\(timeout\.Token\)'
    no_effect_requires_complete_negative_proof = $supervisor -match 'ProvesNoEffect' -and
        $supervisor -match '!observation\.EffectStarted' -and
        $supervisor -match '!observation\.OutputPresent' -and
        $supervisor -match '!observation\.ActionTracePresent'
    success_requires_trace_digest_readback = $supervisor -match 'ActionTraceTerminal' -and
        $supervisor -match 'OutputDigestVerified' -and
        $supervisor -match 'ReadbackVerified'
    unknown_outcome_for_uncertain_effect = $supervisor -match 'effectUnknown: !noEffect' -and
        $service -match 'ExecutionState\.UnknownOutcome'
    same_execution_replays_terminal_journal = $service -match 'JournalClaimDisposition\.Terminal' -and
        $service -match 'replay: true'
    abandoned_execution_is_reconciled_not_executed = $service -match 'ReconcileUnfinishedAsync' -and
        $supervisor -match 'WorkerRecycleReason\.AbandonedExecution'
    recycle_failure_is_fail_closed = $supervisor -match 'BridgeErrorCode\.CleanupFailed' -and
        $supervisor -match 'recycle-failed'
    quota_and_memory_recycle = $supervisor -match 'CompletedJobs >= policy\.MaximumJobsPerWorker' -and
        $supervisor -match 'PrivateMemoryBytes >= memoryLimit'
    windows_job_kill_on_close = $ownedProcess -match 'JobObjectLimitKillOnJobClose' -and
        $ownedProcess -match 'CreateSuspended' -and
        $ownedProcess -match 'ResumeThread' -and
        $ownedProcess -match 'SetInformationJobObject'
    windows_job_terminates_owned_tree = $ownedProcess -match 'AssignProcessToJobObject' -and
        $ownedProcess -match 'TerminateJobObject' -and
        $ownedProcess -match 'ActiveProcesses == 0'
    executable_is_digest_pinned = $ownedProcess -match 'HashFile\(executablePath\)' -and
        $ownedProcess -match 'expectedExecutableSha256'
    raw_command_line_not_persisted = $ownedProcess -match 'RawProcessCommandLineStored: false' -and
        $policy -match '"raw_process_command_line_persisted": false'
    startup_recovery_precedes_lease = $service.IndexOf('RecoverStartupAsync(cancellationToken)', [StringComparison]::Ordinal) -lt
        $service.IndexOf('return new WindowsAgentService(', [StringComparison]::Ordinal)
    quarantine_prevalidates_before_move = $workspace.IndexOf('validatedEntries.Add', [StringComparison]::Ordinal) -lt
        $workspace.IndexOf('Directory.Move(entry, destination)', [StringComparison]::Ordinal)
    quarantine_is_no_delete_and_no_reparse = $workspace -match 'FileAttributes\.ReparsePoint' -and
        $workspace -notmatch 'QuarantineJobSandboxResidue[\s\S]{0,4000}Directory\.Delete'
    hang_retry_no_duplicate_tests = $smoke -match 'HardCommandTimeoutRecyclesAndReplaysUnknownAsync' -and
        $smoke -match 'executorCalls == 1 && cancellationCalls == 1 && recycleCalls == 1' -and
        $smoke -match 'committed\[0\].*SequenceEqual\(committed\[1\]\)'
    actual_process_tree_test = $smoke -match 'ActualWindowsJobKillsOwnedProcessTreeAsync' -and
        $smoke -match 'ProcessIsRunning\(processIds\.LeafProcessId\)' -and
        $smoke -match 'Windows job recycle left an owned descendant running'
    startup_quarantine_tests = $smoke -match 'StartupRecoveryQuarantinesOnlyOwnedResidueAsync' -and
        $smoke -match 'StartupRecoveryRefusesMixedResidueWithoutPartialMoveAsync'
    policy_and_audit_schemas_exist = (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\worker-supervisor-policy-v1.schema.json')) -and
        (Test-Path -LiteralPath (Join-Path $root 'tools\p10\schemas\worker-supervisor-audit-v1.schema.json')) -and
        $validator -match 'Draft202012Validator'
    audit_is_bounded_no_overwrite_private = $audit -match 'TimeoutSeconds = 120' -and
        $audit -match "@\('build', '--configuration', 'Release', '--no-restore'" -and
        $audit -match 'audit requires a clean source tree' -and
        $audit -match 'output already exists' -and
        $audit -match 'File\]::Move\(\$partialPath, \$outputFull\)' -and
        $audit -match 'raw_document_text_present = \$false' -and
        $audit -notmatch 'Get-Clipboard|Set-Clipboard'
    current_scope_does_not_overclaim = $policy -match '"production_or_provider_qualified": false' -and
        $policy -match '"another_hancom_version_requires_independent_evidence": true' -and
        $policy -match '"user_document_scan_allowed": false'
    ci_runs_supervisor_checks = $ci -match 'Test-Hancom2020Supervisor\.ps1' -and
        $ci -match 'validate_worker_supervision\.py'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-09-supervisor-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 5

if ($failed.Count -ne 0) { exit 2 }
