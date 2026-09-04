using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

internal sealed class AgentWorkerSupervisor
{
    private readonly ISupervisedAgentJobExecutor executor;
    private readonly WorkerSupervisorPolicyPin policy;

    internal AgentWorkerSupervisor(
        ISupervisedAgentJobExecutor executor,
        WorkerSupervisorPolicyPin policy)
    {
        this.executor = executor ?? throw new ArgumentNullException(nameof(executor));
        AgentValidation.ValidateWorkerSupervisorPolicy(policy);
        this.policy = policy;
    }

    internal async Task RecoverStartupAsync(CancellationToken cancellationToken)
    {
        Task<WorkerStartupRecoveryReceipt>? recoveryTask = null;
        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(policy.RecycleTimeoutSeconds));
            recoveryTask = executor.RecoverStartupAsync(timeout.Token);
            var recovery = await recoveryTask
                .WaitAsync(timeout.Token)
                .ConfigureAwait(false);
            AgentValidation.ValidateStartupRecoveryReceipt(recovery);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            ObserveFault(recoveryTask);
            throw new AgentProtocolException(AgentProtocolError.CleanupResidue);
        }
        catch (Exception error) when (error is not AgentProtocolException)
        {
            ObserveFault(recoveryTask);
            throw new AgentProtocolException(AgentProtocolError.CleanupResidue);
        }
    }

    internal async Task<AgentJobResult> ExecuteAsync(
        AgentJobContext context,
        Action markExecutorInvoked,
        CancellationToken jobCancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(markExecutorInvoked);
        jobCancellationToken.ThrowIfCancellationRequested();

        using var commandTimeout = new CancellationTokenSource(
            TimeSpan.FromSeconds(context.Assignment.ResourceLimits.CommandTimeoutSeconds));
        using var executionCancellation = CancellationTokenSource.CreateLinkedTokenSource(
            jobCancellationToken,
            commandTimeout.Token);
        markExecutorInvoked();
        Task<AgentJobResult> execution;
        try
        {
            execution = executor.ExecuteAsync(context, executionCancellation.Token)
                ?? Task.FromException<AgentJobResult>(
                    new InvalidOperationException("The supervised executor returned no task."));
        }
        catch (Exception error)
        {
            execution = Task.FromException<AgentJobResult>(error);
        }

        try
        {
            var result = await execution
                .WaitAsync(executionCancellation.Token)
                .ConfigureAwait(false);
            AgentValidation.ValidateJobResult(result);
            var observation = await TryReconcileAsync(context.Assignment).ConfigureAwait(false);
            if (!IsValidCompletedObservation(observation, result))
            {
                var recycled = await TryRecycleAsync(
                    context.Assignment,
                    WorkerRecycleReason.CleanupFailure).ConfigureAwait(false);
                throw Failure(
                    BridgeErrorCode.CleanupFailed,
                    recycled
                        ? "supervisor-reconciliation-incomplete"
                        : "supervisor-reconciliation-recycle-failed",
                    effectUnknown: true);
            }

            var recycleReason = RequiredRecycleReason(observation!, result, context.Assignment);
            if (recycleReason is not null
                && !await TryRecycleAsync(context.Assignment, recycleReason.Value).ConfigureAwait(false))
            {
                throw Failure(
                    BridgeErrorCode.CleanupFailed,
                    "supervisor-terminal-recycle-failed",
                    effectUnknown: true);
            }

            return result;
        }
        catch (OperationCanceledException) when (executionCancellation.IsCancellationRequested)
        {
            var commandExpired = commandTimeout.IsCancellationRequested
                && !jobCancellationToken.IsCancellationRequested;
            return await ContainInterruptedExecutionAsync(
                context.Assignment,
                commandExpired ? WorkerRecycleReason.CommandTimeout : WorkerRecycleReason.Cancellation,
                commandExpired ? BridgeErrorCode.Timeout : BridgeErrorCode.Cancelled,
                commandExpired ? "supervisor-command-timeout" : "supervisor-job-cancelled",
                execution).ConfigureAwait(false);
        }
        catch (WorkerSupervisionException)
        {
            throw;
        }
        catch (AgentProtocolException error)
        {
            return await ContainInterruptedExecutionAsync(
                context.Assignment,
                WorkerRecycleReason.WorkerFailure,
                ToBridgeError(error.Error),
                $"supervisor-agent-protocol-{error.Error}",
                execution).ConfigureAwait(false);
        }
        catch (Exception)
        {
            return await ContainInterruptedExecutionAsync(
                context.Assignment,
                WorkerRecycleReason.WorkerFailure,
                BridgeErrorCode.UnknownOutcome,
                "supervisor-worker-failure",
                execution).ConfigureAwait(false);
        }
    }

    internal async Task<UnfinishedExecutionReconciliation> ReconcileUnfinishedAsync(
        LeaseAssignment assignment,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(assignment);
        var observation = await TryReconcileAsync(assignment, cancellationToken).ConfigureAwait(false);
        var noEffect = ProvesNoEffect(observation);
        var recycled = await TryRecycleAsync(
            assignment,
            WorkerRecycleReason.AbandonedExecution).ConfigureAwait(false);
        if (!recycled)
        {
            return new UnfinishedExecutionReconciliation(
                ExecutionState.UnknownOutcome,
                BridgeErrorCode.CleanupFailed,
                "unfinished-recycle-failed",
                EffectUnknown: true);
        }

        return noEffect
            ? new UnfinishedExecutionReconciliation(
                ExecutionState.Failed,
                BridgeErrorCode.Timeout,
                "unfinished-reconciled-no-effect",
                EffectUnknown: false)
            : new UnfinishedExecutionReconciliation(
                ExecutionState.UnknownOutcome,
                BridgeErrorCode.UnknownOutcome,
                "unfinished-effect-unknown",
                EffectUnknown: true);
    }

    private async Task<AgentJobResult> ContainInterruptedExecutionAsync(
        LeaseAssignment assignment,
        WorkerRecycleReason reason,
        BridgeErrorCode errorCode,
        string safeCategory,
        Task execution)
    {
        await TryRequestCancellationAsync(assignment.ExecutionId).ConfigureAwait(false);
        var observation = await TryReconcileAsync(assignment).ConfigureAwait(false);
        var noEffect = ProvesNoEffect(observation);
        var recycled = await TryRecycleAsync(assignment, reason).ConfigureAwait(false);
        ObserveFault(execution);
        if (!recycled)
        {
            throw Failure(
                BridgeErrorCode.CleanupFailed,
                $"{safeCategory}-recycle-failed",
                effectUnknown: true);
        }

        throw Failure(
            errorCode,
            noEffect ? $"{safeCategory}-no-effect" : $"{safeCategory}-effect-unknown",
            effectUnknown: !noEffect);
    }

    private async Task TryRequestCancellationAsync(string executionId)
    {
        Task? cancellationTask = null;
        try
        {
            using var timeout = new CancellationTokenSource(
                TimeSpan.FromSeconds(policy.CooperativeStopTimeoutSeconds));
            cancellationTask = executor.RequestCancellationAsync(executionId, timeout.Token);
            await cancellationTask
                .WaitAsync(timeout.Token)
                .ConfigureAwait(false);
        }
        catch
        {
            ObserveFault(cancellationTask);
            // Reconciliation and forced recycle remain mandatory.
        }
    }

    private Task<WorkerReconciliationObservation?> TryReconcileAsync(LeaseAssignment assignment) =>
        TryReconcileAsync(assignment, CancellationToken.None);

    private async Task<WorkerReconciliationObservation?> TryReconcileAsync(
        LeaseAssignment assignment,
        CancellationToken cancellationToken)
    {
        Task<WorkerReconciliationObservation>? reconciliationTask = null;
        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(policy.ReconciliationTimeoutSeconds));
            reconciliationTask = executor.ReconcileAsync(assignment.Clone(), timeout.Token);
            var observation = await reconciliationTask
                .WaitAsync(timeout.Token)
                .ConfigureAwait(false);
            AgentValidation.ValidateReconciliationObservation(observation, assignment);
            return observation;
        }
        catch
        {
            ObserveFault(reconciliationTask);
            return null;
        }
    }

    private async Task<bool> TryRecycleAsync(
        LeaseAssignment assignment,
        WorkerRecycleReason reason)
    {
        Task<WorkerRecycleReceipt>? recycleTask = null;
        try
        {
            using var timeout = new CancellationTokenSource(
                TimeSpan.FromSeconds(policy.RecycleTimeoutSeconds));
            recycleTask = executor.RecycleAsync(assignment.Clone(), reason, timeout.Token);
            var receipt = await recycleTask
                .WaitAsync(timeout.Token)
                .ConfigureAwait(false);
            AgentValidation.ValidateRecycleReceipt(receipt, assignment, reason);
            return true;
        }
        catch
        {
            ObserveFault(recycleTask);
            return false;
        }
    }

    private WorkerRecycleReason? RequiredRecycleReason(
        WorkerReconciliationObservation observation,
        AgentJobResult result,
        LeaseAssignment assignment)
    {
        if (result.TerminalState == ExecutionState.UnknownOutcome
            || result.Diagnostic?.EffectUnknown == true)
        {
            return WorkerRecycleReason.UnknownOutcome;
        }

        if (result.TerminalState == ExecutionState.Cancelled)
        {
            return WorkerRecycleReason.Cancellation;
        }

        if (result.TerminalState == ExecutionState.Failed)
        {
            return result.Diagnostic?.ErrorCode == BridgeErrorCode.CleanupFailed
                ? WorkerRecycleReason.CleanupFailure
                : WorkerRecycleReason.WorkerFailure;
        }

        if (!observation.WorkerProcessRunning)
        {
            return WorkerRecycleReason.WorkerFailure;
        }

        var memoryLimit = Math.Min(
            policy.MaximumPrivateMemoryBytes,
            assignment.ResourceLimits.MemoryLimitBytes);
        return observation.CompletedJobs >= policy.MaximumJobsPerWorker
            || observation.PrivateMemoryBytes >= memoryLimit
            ? WorkerRecycleReason.PolicyLimit
            : null;
    }

    private static bool IsValidCompletedObservation(
        WorkerReconciliationObservation? observation,
        AgentJobResult result)
    {
        if (observation is null
            || !observation.ProbeComplete
            || !observation.SourceUnchanged
            || observation.RawDocumentContentStored)
        {
            return false;
        }

        var outputsVerified = result.Artifacts.Count == 0
            ? !observation.OutputPresent && !observation.OutputDigestVerified
            : observation.OutputPresent && observation.OutputDigestVerified;
        var terminalEffectVerified = observation.EffectStarted
            && observation.ActionTracePresent
            && observation.ActionTraceTerminal
            && outputsVerified;
        return result.TerminalState switch
        {
            ExecutionState.Succeeded => terminalEffectVerified && observation.ReadbackVerified,
            ExecutionState.Failed or ExecutionState.Cancelled =>
                ProvesNoEffect(observation) || terminalEffectVerified,
            ExecutionState.UnknownOutcome => true,
            _ => false,
        };
    }

    private static bool ProvesNoEffect(WorkerReconciliationObservation? observation) =>
        observation is not null
        && observation.ProbeComplete
        && !observation.EffectStarted
        && observation.SourceUnchanged
        && !observation.OutputPresent
        && !observation.OutputDigestVerified
        && !observation.ActionTracePresent
        && !observation.ActionTraceTerminal
        && !observation.ReadbackVerified
        && !observation.RawDocumentContentStored;

    private static WorkerSupervisionException Failure(
        BridgeErrorCode errorCode,
        string safeCategory,
        bool effectUnknown) =>
        new(errorCode, safeCategory, effectUnknown);

    private static BridgeErrorCode ToBridgeError(AgentProtocolError error) => error switch
    {
        AgentProtocolError.InvalidFencing or AgentProtocolError.ExpiredLease =>
            BridgeErrorCode.StaleFencingToken,
        AgentProtocolError.ProfileMismatch => BridgeErrorCode.ProfileMismatch,
        AgentProtocolError.InvalidArtifact or AgentProtocolError.ArtifactMismatch =>
            BridgeErrorCode.ArtifactMismatch,
        AgentProtocolError.PolicyDenied or AgentProtocolError.IsolationNotReady =>
            BridgeErrorCode.PolicyDenied,
        AgentProtocolError.OutputLimit => BridgeErrorCode.OutputRejected,
        AgentProtocolError.CleanupResidue or AgentProtocolError.RecycleFailed =>
            BridgeErrorCode.CleanupFailed,
        _ => BridgeErrorCode.InvalidEnvelope,
    };

    private static void ObserveFault(Task? task)
    {
        if (task is null)
        {
            return;
        }

        _ = task.ContinueWith(
            static completed => _ = completed.Exception,
            CancellationToken.None,
            TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously,
            TaskScheduler.Default);
    }
}

internal sealed class WorkerSupervisionException : Exception
{
    internal WorkerSupervisionException(
        BridgeErrorCode errorCode,
        string safeCategory,
        bool effectUnknown)
        : base("The supervised worker did not produce a safely reusable outcome.")
    {
        ErrorCode = errorCode;
        SafeCategory = safeCategory;
        EffectUnknown = effectUnknown;
    }

    internal BridgeErrorCode ErrorCode { get; }

    internal string SafeCategory { get; }

    internal bool EffectUnknown { get; }
}
