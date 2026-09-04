using System.Buffers;
using System.Security.Cryptography;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

public sealed class WindowsAgentService
{
    private const uint ProtocolMajor = 1;
    private const uint ProtocolMinor = 0;

    private readonly WindowsAgentConfiguration configuration;
    private readonly IWindowsAgentControlClient controlClient;
    private readonly IArtifactStore artifactStore;
    private readonly AgentWorkerSupervisor supervisor;
    private readonly AgentWorkspace workspace;
    private readonly WorkerIsolationGuard isolationGuard;
    private readonly IRuntimeProbeCollector runtimeProbeCollector;
    private readonly TimeProvider timeProvider;
    private ulong routableProbeExpiresAtUnixMs;
    private int activeRun;

    public WindowsAgentService(
        WindowsAgentConfiguration configuration,
        IWindowsAgentControlClient controlClient,
        IArtifactStore artifactStore,
        ISupervisedAgentJobExecutor executor,
        AgentWorkspace workspace,
        IWorkerIsolationAttestor isolationAttestor,
        IRuntimeProbeCollector runtimeProbeCollector,
        TimeProvider? timeProvider = null)
    {
        AgentValidation.ValidateConfiguration(configuration);
        this.configuration = configuration;
        this.controlClient = controlClient ?? throw new ArgumentNullException(nameof(controlClient));
        this.artifactStore = artifactStore ?? throw new ArgumentNullException(nameof(artifactStore));
        supervisor = new AgentWorkerSupervisor(
            executor ?? throw new ArgumentNullException(nameof(executor)),
            configuration.WorkerSupervisor);
        this.workspace = workspace ?? throw new ArgumentNullException(nameof(workspace));
        isolationGuard = new WorkerIsolationGuard(configuration, workspace, isolationAttestor);
        this.runtimeProbeCollector = runtimeProbeCollector
            ?? throw new ArgumentNullException(nameof(runtimeProbeCollector));
        this.timeProvider = timeProvider ?? TimeProvider.System;
    }

    public static async Task<WindowsAgentService> CreateRecoveredAsync(
        WindowsAgentConfiguration configuration,
        IWindowsAgentControlClient controlClient,
        IArtifactStore artifactStore,
        ISupervisedAgentJobExecutor executor,
        AgentWorkspace workspace,
        IWorkerIsolationAttestor isolationAttestor,
        IRuntimeProbeCollector runtimeProbeCollector,
        CancellationToken cancellationToken,
        TimeProvider? timeProvider = null)
    {
        AgentValidation.ValidateConfiguration(configuration);
        ArgumentNullException.ThrowIfNull(workspace);
        var startupSupervisor = new AgentWorkerSupervisor(
            executor ?? throw new ArgumentNullException(nameof(executor)),
            configuration.WorkerSupervisor);
        await startupSupervisor.RecoverStartupAsync(cancellationToken).ConfigureAwait(false);
        workspace.QuarantineJobSandboxResidue();
        return new WindowsAgentService(
            configuration,
            controlClient,
            artifactStore,
            executor,
            workspace,
            isolationAttestor,
            runtimeProbeCollector,
            timeProvider);
    }

    public async Task<AgentRunResult> RunOnceAsync(CancellationToken cancellationToken)
    {
        if (Interlocked.CompareExchange(ref activeRun, 1, 0) != 0)
        {
            return new AgentRunResult(
                AgentRunDisposition.Busy,
                ExecutionState.Accepted,
                ExecutorInvoked: false,
                CommitAttempted: false);
        }

        try
        {
            return await RunOnceCoreAsync(cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            Volatile.Write(ref activeRun, 0);
        }
    }

    private async Task<AgentRunResult> RunOnceCoreAsync(CancellationToken cancellationToken)
    {
        var isolationBefore = isolationGuard.VerifyBeforeLease();
        await EnsureRoutableRuntimeProbeAsync(cancellationToken).ConfigureAwait(false);
        var leaseResponse = await controlClient
            .AcquireLeaseAsync(CreateLeaseRequest(), cancellationToken)
            .ConfigureAwait(false);
        ArgumentNullException.ThrowIfNull(leaseResponse);

        if (leaseResponse.Disposition == LeaseDisposition.NoWork)
        {
            if (leaseResponse.Assignment is not null)
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidState);
            }

            isolationGuard.VerifyAfterJob(isolationBefore);

            return new AgentRunResult(
                AgentRunDisposition.NoWork,
                ExecutionState.Unspecified,
                ExecutorInvoked: false,
                CommitAttempted: false);
        }

        if (leaseResponse.Disposition != LeaseDisposition.Assigned || leaseResponse.Assignment is null)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        var assignment = leaseResponse.Assignment;
        AgentValidation.ValidateAssignment(assignment, configuration, UtcNowMilliseconds());
        var claim = await workspace.Journal.ClaimAsync(assignment, cancellationToken).ConfigureAwait(false);
        if (claim.Disposition == JournalClaimDisposition.Busy)
        {
            return new AgentRunResult(
                AgentRunDisposition.Busy,
                ExecutionState.Accepted,
                ExecutorInvoked: false,
                CommitAttempted: false);
        }

        await using var ownership = claim.Ownership
            ?? throw new AgentProtocolException(AgentProtocolError.JournalConflict);

        if (claim.Disposition == JournalClaimDisposition.Conflict)
        {
            return new AgentRunResult(
                AgentRunDisposition.FencingMismatch,
                ExecutionState.Unspecified,
                ExecutorInvoked: false,
                CommitAttempted: false);
        }

        if (claim.Disposition == JournalClaimDisposition.Terminal)
        {
            return await CommitRecordedAsync(
                assignment,
                claim.Receipt ?? throw new AgentProtocolException(AgentProtocolError.JournalConflict),
                executorInvoked: false,
                replay: true,
                cancellationToken).ConfigureAwait(false);
        }

        if (claim.Disposition == JournalClaimDisposition.Unfinished)
        {
            var reconciliation = await supervisor
                .ReconcileUnfinishedAsync(assignment, cancellationToken)
                .ConfigureAwait(false);
            var uncertain = CreateFailureReceipt(
                assignment,
                reconciliation.TerminalState,
                reconciliation.ErrorCode,
                reconciliation.SafeCategory,
                reconciliation.EffectUnknown);
            await ownership.WriteTerminalAsync(uncertain, CancellationToken.None).ConfigureAwait(false);
            return await CommitRecordedAsync(
                assignment,
                uncertain,
                executorInvoked: false,
                replay: true,
                cancellationToken).ConfigureAwait(false);
        }

        var executorInvoked = false;
        AgentExecutionReceipt terminalReceipt;
        using var jobTimeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        jobTimeout.CancelAfter(TimeSpan.FromSeconds(assignment.ResourceLimits.JobTimeoutSeconds));
        try
        {
            terminalReceipt = await ExecuteLeaseAsync(
                assignment,
                () => executorInvoked = true,
                jobTimeout.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            var callerCancelled = cancellationToken.IsCancellationRequested;
            terminalReceipt = CreateFailureReceipt(
                assignment,
                executorInvoked ? ExecutionState.UnknownOutcome : ExecutionState.Cancelled,
                callerCancelled ? BridgeErrorCode.Cancelled : BridgeErrorCode.Timeout,
                callerCancelled ? "agent-run-cancelled" : "agent-job-timeout",
                effectUnknown: executorInvoked);
        }
        catch (WorkerSupervisionException error)
        {
            var errorCode = error.ErrorCode == BridgeErrorCode.Cancelled
                && !cancellationToken.IsCancellationRequested
                    ? BridgeErrorCode.Timeout
                    : error.ErrorCode;
            terminalReceipt = CreateFailureReceipt(
                assignment,
                error.EffectUnknown ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
                errorCode,
                error.SafeCategory,
                error.EffectUnknown);
        }
        catch (AgentProtocolException error)
        {
            terminalReceipt = CreateFailureReceipt(
                assignment,
                executorInvoked ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
                ToBridgeError(error.Error),
                $"agent-protocol-{error.Error}",
                effectUnknown: executorInvoked);
        }
        catch (Exception)
        {
            terminalReceipt = CreateFailureReceipt(
                assignment,
                executorInvoked ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
                BridgeErrorCode.UnknownOutcome,
                "agent-unclassified-failure",
                effectUnknown: executorInvoked);
        }

        try
        {
            isolationGuard.VerifyAfterJob(isolationBefore);
        }
        catch (AgentProtocolException error) when (error.Error is (
            AgentProtocolError.IsolationNotReady or AgentProtocolError.CleanupResidue))
        {
            terminalReceipt = CreateFailureReceipt(
                assignment,
                executorInvoked ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
                BridgeErrorCode.CleanupFailed,
                "worker-isolation-post-job-residue",
                effectUnknown: executorInvoked);
        }

        await ownership.WriteTerminalAsync(terminalReceipt, CancellationToken.None).ConfigureAwait(false);
        return await CommitRecordedAsync(
            assignment,
            terminalReceipt,
            executorInvoked,
            replay: false,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<bool> ReportProbeAsync(
        RuntimeProbeReceipt probe,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(probe);
        if (probe.TargetProfile is null
            || !probe.TargetProfile.Equals(configuration.TargetProfile)
            || probe.Health == ProbeHealth.Unspecified
            || !string.Equals(
                probe.CapabilityRegistrySha256,
                configuration.CapabilityRegistrySha256,
                StringComparison.Ordinal)
            || probe.ObservedAtUnixMs == 0)
        {
            throw new AgentProtocolException(AgentProtocolError.ProfileMismatch);
        }

        AgentValidation.RequireDigest(probe.CapabilityRegistrySha256);
        AgentValidation.RequireDigest(probe.CapabilitySetSha256);
        AgentValidation.ValidateArtifact(probe.Evidence);
        await VerifySourceArtifactAsync(probe.Evidence, cancellationToken).ConfigureAwait(false);
        var response = await controlClient.ReportProbeAsync(
            new AgentProbeRequest
            {
                ProtocolMajor = ProtocolMajor,
                ProtocolMinor = ProtocolMinor,
                AgentInstanceId = configuration.AgentInstanceId,
                Probe = probe.Clone(),
            },
            cancellationToken).ConfigureAwait(false);
        if (response.Routable && !response.Accepted)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        if (response.Accepted)
        {
            AgentValidation.RequireDigest(response.AcceptedProbeSha256);
            if (!string.Equals(
                response.AcceptedProbeSha256,
                AgentValidation.ComputeSha256(probe),
                StringComparison.Ordinal))
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidDigest);
            }
        }

        return response.Accepted && response.Routable;
    }

    private async Task EnsureRoutableRuntimeProbeAsync(CancellationToken cancellationToken)
    {
        var nowUnixMs = checked((ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds());
        if (nowUnixMs < routableProbeExpiresAtUnixMs)
        {
            return;
        }

        var observation = await runtimeProbeCollector
            .ObserveAsync(cancellationToken)
            .ConfigureAwait(false);
        var materialized = RuntimeProbeMaterializer.Materialize(
            configuration,
            observation,
            nowUnixMs);
        await using (var content = new MemoryStream(materialized.EvidenceBytes, writable: false))
        {
            await artifactStore.UploadAsync(
                materialized.Receipt.Evidence,
                content,
                cancellationToken).ConfigureAwait(false);
        }

        var routable = await ReportProbeAsync(materialized.Receipt, cancellationToken)
            .ConfigureAwait(false);
        if (!routable || materialized.Receipt.Health == ProbeHealth.Unroutable)
        {
            throw new AgentProtocolException(AgentProtocolError.RuntimeProbeNotRoutable);
        }

        routableProbeExpiresAtUnixMs = checked(
            materialized.Receipt.ObservedAtUnixMs
            + configuration.RuntimeProbe.MaximumProbeAgeSeconds * 1_000UL);
    }

    private async Task<AgentExecutionReceipt> ExecuteLeaseAsync(
        LeaseAssignment assignment,
        Action markExecutorInvoked,
        CancellationToken cancellationToken)
    {
        var firstHeartbeat = await HeartbeatAsync(
            assignment,
            ExecutionState.Accepted,
            "lease-accepted",
            cancellationToken).ConfigureAwait(false);
        if (!firstHeartbeat.LeaseCurrent)
        {
            return CreateFailureReceipt(
                assignment,
                ExecutionState.Failed,
                BridgeErrorCode.StaleFencingToken,
                "lease-not-current",
                effectUnknown: false);
        }

        if (firstHeartbeat.CancelRequested)
        {
            return CreateFailureReceipt(
                assignment,
                ExecutionState.Cancelled,
                BridgeErrorCode.Cancelled,
                "lease-cancelled-before-stage",
                effectUnknown: false);
        }

        await using var sandbox = workspace.CreateSandbox(assignment);
        await sandbox.StageAsync(assignment.Input, artifactStore, cancellationToken).ConfigureAwait(false);
        await sandbox.StageAsync(assignment.OperationPlan, artifactStore, cancellationToken).ConfigureAwait(false);
        await sandbox.StageAsync(assignment.ValidationContract, artifactStore, cancellationToken)
            .ConfigureAwait(false);

        var runningHeartbeat = await HeartbeatAsync(
            assignment,
            ExecutionState.Running,
            "artifacts-staged",
            cancellationToken).ConfigureAwait(false);
        if (!runningHeartbeat.LeaseCurrent)
        {
            return CreateFailureReceipt(
                assignment,
                ExecutionState.Failed,
                BridgeErrorCode.StaleFencingToken,
                "lease-stale-after-stage",
                effectUnknown: false);
        }

        if (runningHeartbeat.CancelRequested)
        {
            return CreateFailureReceipt(
                assignment,
                ExecutionState.Cancelled,
                BridgeErrorCode.Cancelled,
                "lease-cancelled-before-execute",
                effectUnknown: false);
        }

        var result = await supervisor
            .ExecuteAsync(
                new AgentJobContext(
                    assignment,
                    sandbox,
                    configuration.HancomSecurityModule,
                    configuration.HancomBindingBundle,
                    configuration.CapabilityRegistrySha256,
                    timeProvider),
                markExecutorInvoked,
                cancellationToken)
            .ConfigureAwait(false);
        AgentValidation.ValidateJobResult(result);
        if (configuration.HancomBindingBundle is not null
            && (!string.Equals(
                    result.BindingBundleId,
                    configuration.HancomBindingBundle.BundleId,
                    StringComparison.Ordinal)
                || !string.Equals(
                    result.BindingBundleSha256,
                    configuration.HancomBindingBundle.Sha256,
                    StringComparison.Ordinal)))
        {
            throw new AgentProtocolException(AgentProtocolError.PolicyDenied);
        }
        await VerifySourceArtifactAsync(assignment.Input.Artifact, cancellationToken).ConfigureAwait(false);
        sandbox.ValidateOutputs(result.Artifacts);

        var outputs = new List<ArtifactRef>();
        var evidence = new List<ArtifactRef>();
        foreach (var produced in result.Artifacts)
        {
            var uploaded = await sandbox
                .UploadOutputAsync(produced, artifactStore, cancellationToken)
                .ConfigureAwait(false);
            (produced.Evidence ? evidence : outputs).Add(uploaded);
        }

        var receipt = new AgentExecutionReceipt
        {
            TerminalState = result.TerminalState,
            BackendId = result.BackendId,
            BindingBundleId = result.BindingBundleId,
            BindingBundleSha256 = result.BindingBundleSha256,
            Input = assignment.Input.Artifact.Clone(),
            ValidationState = result.ValidationState,
            InputUnchanged = true,
            ExternalNetworkInvoked = false,
            RegistryOrSystemSettingChanged = false,
            Diagnostic = result.Diagnostic?.Clone(),
        };
        receipt.Outputs.Add(outputs);
        receipt.Evidence.Add(evidence);
        return receipt;
    }

    private async Task<AgentHeartbeatResponse> HeartbeatAsync(
        LeaseAssignment assignment,
        ExecutionState state,
        string progressState,
        CancellationToken cancellationToken)
    {
        var response = await controlClient.HeartbeatAsync(
            new AgentHeartbeatRequest
            {
                LeaseId = assignment.LeaseId,
                FencingToken = assignment.FencingToken,
                ExecutionId = assignment.ExecutionId,
                ExecutionState = state,
                ObservedAtUnixMs = (ulong)UtcNowMilliseconds(),
                ProgressDigest = AgentValidation.ComputeProgressDigest(progressState),
            },
            cancellationToken).ConfigureAwait(false);
        ArgumentNullException.ThrowIfNull(response);
        if (response.LeaseCurrent && response.ExpiresAtUnixMs <= (ulong)UtcNowMilliseconds())
        {
            return new AgentHeartbeatResponse
            {
                LeaseCurrent = false,
                CancelRequested = response.CancelRequested,
                ExpiresAtUnixMs = response.ExpiresAtUnixMs,
            };
        }

        return response;
    }

    private async Task<AgentRunResult> CommitRecordedAsync(
        LeaseAssignment assignment,
        AgentExecutionReceipt receipt,
        bool executorInvoked,
        bool replay,
        CancellationToken cancellationToken)
    {
        var expectedDigest = AgentValidation.ComputeSha256(receipt);
        AgentValidation.ValidateExecutionReceipt(receipt, assignment);
        var response = await controlClient.CommitExecutionAsync(
            new AgentCommitRequest
            {
                LeaseId = assignment.LeaseId,
                FencingToken = assignment.FencingToken,
                ExecutionId = assignment.ExecutionId,
                Receipt = receipt.Clone(),
            },
            cancellationToken).ConfigureAwait(false);
        ArgumentNullException.ThrowIfNull(response);

        if (response.Disposition is CommitDisposition.Accepted or CommitDisposition.AlreadyTerminal)
        {
            if (!string.Equals(response.ReceiptSha256, expectedDigest, StringComparison.Ordinal))
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidDigest);
            }

            var disposition = replay || response.Disposition == CommitDisposition.AlreadyTerminal
                ? AgentRunDisposition.Replayed
                : FromReceipt(receipt);
            return new AgentRunResult(disposition, receipt.TerminalState, executorInvoked, CommitAttempted: true);
        }

        if (response.Disposition == CommitDisposition.StaleLease)
        {
            return new AgentRunResult(
                AgentRunDisposition.StaleLease,
                receipt.TerminalState,
                executorInvoked,
                CommitAttempted: true);
        }

        if (response.Disposition is CommitDisposition.FencingMismatch or CommitDisposition.BindingMismatch)
        {
            return new AgentRunResult(
                AgentRunDisposition.FencingMismatch,
                receipt.TerminalState,
                executorInvoked,
                CommitAttempted: true);
        }

        throw new AgentProtocolException(AgentProtocolError.InvalidState);
    }

    private AgentLeaseRequest CreateLeaseRequest()
    {
        Span<byte> nonce = stackalloc byte[32];
        RandomNumberGenerator.Fill(nonce);
        return new AgentLeaseRequest
        {
            ProtocolMajor = ProtocolMajor,
            ProtocolMinor = ProtocolMinor,
            AgentInstanceId = configuration.AgentInstanceId,
            TargetProfile = configuration.TargetProfile.Clone(),
            CapabilityRegistrySha256 = configuration.CapabilityRegistrySha256,
            AvailableJobSlots = configuration.AvailableJobSlots,
            ObservedAtUnixMs = (ulong)UtcNowMilliseconds(),
            NonceSha256 = AgentValidation.ComputeSha256(nonce),
        };
    }

    private async Task VerifySourceArtifactAsync(
        ArtifactRef expected,
        CancellationToken cancellationToken)
    {
        await using var source = await artifactStore.OpenReadAsync(expected, cancellationToken)
            .ConfigureAwait(false);
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        var buffer = ArrayPool<byte>.Shared.Rent(65_536);
        ulong total = 0;
        try
        {
            while (true)
            {
                var read = await source.ReadAsync(buffer.AsMemory(0, buffer.Length), cancellationToken)
                    .ConfigureAwait(false);
                if (read == 0)
                {
                    break;
                }

                total = checked(total + (uint)read);
                if (total > expected.SizeBytes || total > AgentValidation.MaximumArtifactBytes)
                {
                    throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
                }

                hash.AppendData(buffer, 0, read);
            }
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer, clearArray: true);
        }

        if (total != expected.SizeBytes
            || !string.Equals(
                Convert.ToHexStringLower(hash.GetHashAndReset()),
                expected.Sha256,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }
    }

    private AgentExecutionReceipt CreateFailureReceipt(
        LeaseAssignment assignment,
        ExecutionState state,
        BridgeErrorCode errorCode,
        string safeCategory,
        bool effectUnknown) =>
        new()
        {
            TerminalState = state,
            BackendId = "windows.agent",
            BindingBundleId = "binding.unavailable",
            BindingBundleSha256 = configuration.CapabilityRegistrySha256,
            Input = assignment.Input.Artifact.Clone(),
            ValidationState = ValidationState.Unverified,
            InputUnchanged = true,
            ExternalNetworkInvoked = false,
            RegistryOrSystemSettingChanged = false,
            Diagnostic = new BridgeDiagnostic
            {
                ErrorCode = errorCode,
                SafeDetailSha256 = AgentValidation.ComputeProgressDigest(safeCategory),
                Retryable = !effectUnknown && errorCode is not BridgeErrorCode.PolicyDenied,
                EffectUnknown = effectUnknown,
            },
        };

    private static AgentRunDisposition FromReceipt(AgentExecutionReceipt receipt)
    {
        if (receipt.Diagnostic?.ErrorCode == BridgeErrorCode.StaleFencingToken)
        {
            return AgentRunDisposition.StaleLease;
        }

        return receipt.TerminalState switch
        {
            ExecutionState.Succeeded => AgentRunDisposition.Succeeded,
            ExecutionState.Failed => AgentRunDisposition.Failed,
            ExecutionState.Cancelled => AgentRunDisposition.Cancelled,
            ExecutionState.UnknownOutcome => AgentRunDisposition.UnknownOutcome,
            _ => throw new AgentProtocolException(AgentProtocolError.InvalidState),
        };
    }

    private static BridgeErrorCode ToBridgeError(AgentProtocolError error) => error switch
    {
        AgentProtocolError.InvalidFencing => BridgeErrorCode.StaleFencingToken,
        AgentProtocolError.ExpiredLease => BridgeErrorCode.StaleFencingToken,
        AgentProtocolError.ProfileMismatch => BridgeErrorCode.ProfileMismatch,
        AgentProtocolError.InvalidArtifact or AgentProtocolError.ArtifactMismatch =>
            BridgeErrorCode.ArtifactMismatch,
        AgentProtocolError.PolicyDenied => BridgeErrorCode.PolicyDenied,
        AgentProtocolError.OutputLimit => BridgeErrorCode.OutputRejected,
        AgentProtocolError.JournalConflict => BridgeErrorCode.UnknownOutcome,
        AgentProtocolError.IsolationNotReady => BridgeErrorCode.PolicyDenied,
        AgentProtocolError.CleanupResidue => BridgeErrorCode.CleanupFailed,
        AgentProtocolError.ReconciliationFailed => BridgeErrorCode.UnknownOutcome,
        AgentProtocolError.RecycleFailed => BridgeErrorCode.CleanupFailed,
        _ => BridgeErrorCode.InvalidEnvelope,
    };

    private long UtcNowMilliseconds() => timeProvider.GetUtcNow().ToUnixTimeMilliseconds();
}
