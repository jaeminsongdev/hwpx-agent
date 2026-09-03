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

public sealed record WindowsAgentConfiguration(
    string AgentInstanceId,
    TargetProfileIdentity TargetProfile,
    string CapabilityRegistrySha256,
    uint AvailableJobSlots,
    TimeSpan RpcTimeout,
    WorkerIsolationPolicyPin WorkerIsolation,
    HancomSecurityModulePin? HancomSecurityModule = null,
    HancomBindingBundlePin? HancomBindingBundle = null);

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
