using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

public interface IWindowsAgentControlClient
{
    Task<AgentLeaseResponse> AcquireLeaseAsync(AgentLeaseRequest request, CancellationToken cancellationToken);

    Task<AgentHeartbeatResponse> HeartbeatAsync(AgentHeartbeatRequest request, CancellationToken cancellationToken);

    Task<AgentCommitResponse> CommitExecutionAsync(AgentCommitRequest request, CancellationToken cancellationToken);

    Task<AgentProbeResponse> ReportProbeAsync(AgentProbeRequest request, CancellationToken cancellationToken);
}

public interface IArtifactStore
{
    ValueTask<Stream> OpenReadAsync(ArtifactRef artifact, CancellationToken cancellationToken);

    Task UploadAsync(ArtifactRef artifact, Stream content, CancellationToken cancellationToken);
}

public interface IAgentJobExecutor
{
    Task<AgentJobResult> ExecuteAsync(AgentJobContext context, CancellationToken cancellationToken);
}

public interface ISupervisedAgentJobExecutor : IAgentJobExecutor
{
    Task<WorkerStartupRecoveryReceipt> RecoverStartupAsync(CancellationToken cancellationToken);

    Task RequestCancellationAsync(string executionId, CancellationToken cancellationToken);

    Task<WorkerReconciliationObservation> ReconcileAsync(
        LeaseAssignment assignment,
        CancellationToken cancellationToken);

    Task<WorkerRecycleReceipt> RecycleAsync(
        LeaseAssignment assignment,
        WorkerRecycleReason reason,
        CancellationToken cancellationToken);
}

public interface IRuntimeProbeCollector
{
    Task<RuntimeProbeObservation> ObserveAsync(CancellationToken cancellationToken);
}

public sealed record WindowsAgentConfiguration(
    string AgentInstanceId,
    TargetProfileIdentity TargetProfile,
    string CapabilityRegistrySha256,
    uint AvailableJobSlots,
    TimeSpan RpcTimeout,
    WorkerIsolationPolicyPin WorkerIsolation,
    WorkerSupervisorPolicyPin WorkerSupervisor,
    RuntimeProbePolicyPin RuntimeProbe,
    HancomSecurityModulePin? HancomSecurityModule = null,
    HancomBindingBundlePin? HancomBindingBundle = null);

public sealed record RuntimeProbePolicyPin(
    string PolicyId,
    string EvidenceArtifactId,
    uint MaximumProbeAgeSeconds,
    uint MaximumEvidenceBytes);

public enum RuntimeCapabilityState
{
    Verified = 1,
    Unavailable = 2,
    Unverified = 3,
    Drifted = 4,
}

public sealed record RuntimeCapabilityObservation(
    string CapabilityId,
    RuntimeCapabilityState State,
    bool RequiredForLease,
    string SafeCode,
    string ObservationSha256);

public sealed record RuntimeProbeObservation(
    string PolicyId,
    TargetProfileIdentity TargetProfile,
    string CapabilityRegistrySha256,
    ProbeHealth Health,
    IReadOnlyList<RuntimeCapabilityObservation> Capabilities,
    ulong ObservedAtUnixMs,
    bool RawPathStored,
    bool RawDocumentContentStored,
    bool UserDocumentScanned,
    bool ExternalNetworkInvoked,
    bool SystemSettingChanged,
    bool HancomProcessStarted);

public sealed record WorkerSupervisorPolicyPin(
    string PolicyId,
    uint CooperativeStopTimeoutSeconds,
    uint ReconciliationTimeoutSeconds,
    uint RecycleTimeoutSeconds,
    uint MaximumJobsPerWorker,
    ulong MaximumPrivateMemoryBytes);

public enum WorkerRecycleReason
{
    StartupRecovery = 1,
    CommandTimeout = 2,
    Cancellation = 3,
    WorkerFailure = 4,
    UnknownOutcome = 5,
    PolicyLimit = 6,
    CleanupFailure = 7,
    AbandonedExecution = 8,
}

public sealed record WorkerStartupRecoveryReceipt(
    bool ProbeComplete,
    uint OwnedProcessCountBefore,
    uint OwnedProcessCountAfter,
    bool ProcessTreeTerminated,
    bool FreshWorkerRequired,
    bool RawProcessCommandLineStored,
    string SafeDetailSha256);

public sealed record WorkerReconciliationObservation(
    string ExecutionId,
    string AssignmentSha256,
    bool ProbeComplete,
    bool WorkerProcessRunning,
    bool EffectStarted,
    bool SourceUnchanged,
    bool OutputPresent,
    bool OutputDigestVerified,
    bool ActionTracePresent,
    bool ActionTraceTerminal,
    bool ReadbackVerified,
    uint CompletedJobs,
    ulong PrivateMemoryBytes,
    bool RawDocumentContentStored);

public sealed record WorkerRecycleReceipt(
    string ExecutionId,
    string AssignmentSha256,
    WorkerRecycleReason Reason,
    bool ProcessTreeTerminated,
    bool FreshWorkerRequired,
    bool RawProcessCommandLineStored,
    string SafeDetailSha256);

public sealed record UnfinishedExecutionReconciliation(
    ExecutionState TerminalState,
    BridgeErrorCode ErrorCode,
    string SafeCategory,
    bool EffectUnknown);

public enum WorkerIsolationScope
{
    CurrentPcInteractiveDevelopment = 1,
    DedicatedWorkerImage = 2,
}

public sealed record WorkerIsolationPolicyPin(
    string PolicyId,
    WorkerIsolationScope Scope,
    string TargetProfileId,
    string HostBaselineSha256,
    string HostIsolationIdentitySha256,
    string WorkerImageManifestSha256,
    bool ProductionIsolationQualified);

public sealed record WorkerIsolationObservation(
    string PolicyId,
    string TargetProfileId,
    string HostBaselineSha256,
    string WorkerImageManifestSha256,
    bool ProbeComplete,
    bool WindowsHost,
    bool InteractiveSession,
    uint SessionId,
    string IdentitySha256,
    string WindowStationSha256,
    string DesktopSha256,
    string ProfileRootSha256,
    string TempRootSha256,
    string HostIsolationIdentitySha256,
    bool PrivateJobWorkspace,
    bool DedicatedIdentityAndProfile,
    bool PrivateWindowStation,
    bool OsNetworkDefaultDeny,
    bool ClipboardIsolated,
    bool ProfileResidueClean,
    bool RecoveryResidueClean,
    bool PrinterResidueClean,
    uint TargetProcessCount,
    bool RawIdentityStored);

public interface IWorkerIsolationAttestor
{
    WorkerIsolationObservation Observe(string workspaceRoot);
}

public sealed record HancomSecurityModulePin(string RegistrationName, string Sha256);

public sealed record HancomBindingBundlePin(
    string BundleId,
    string BundlePath,
    string Sha256,
    string TrustedPublicKeyPath,
    string TrustedPublicKeySha256);

public sealed record HancomWorkerSecurityLease(
    string SessionId,
    ulong FencingToken,
    string TargetProfileId,
    string SecurityLeasePath);

public sealed record ProducedArtifact(string SandboxHandle, string ArtifactId, bool Evidence = false);

public sealed record AgentJobResult(
    ExecutionState TerminalState,
    string BackendId,
    string BindingBundleId,
    string BindingBundleSha256,
    ValidationState ValidationState,
    IReadOnlyList<ProducedArtifact> Artifacts,
    BridgeDiagnostic? Diagnostic = null);

public enum AgentRunDisposition
{
    NoWork,
    Succeeded,
    Failed,
    Cancelled,
    UnknownOutcome,
    StaleLease,
    FencingMismatch,
    Busy,
    Replayed,
}

public sealed record AgentRunResult(
    AgentRunDisposition Disposition,
    ExecutionState TerminalState,
    bool ExecutorInvoked,
    bool CommitAttempted);
