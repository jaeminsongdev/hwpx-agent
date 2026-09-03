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
    TimeSpan RpcTimeout);

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
