using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

public interface IStaCommandHandlerCleanup
{
    void Cleanup(StaExecutionContext context);
}

internal interface IHancomApprovedDocumentResolver
{
    HancomApprovedDocument Resolve(StaOpenDocumentCommand command, StaExecutionContext context);
}

public sealed class HancomLifecycleCommandHandler : IStaCommandHandler, IStaCommandHandlerCleanup
{
    private readonly Func<HancomSession> sessionFactory;
    private readonly IHancomApprovedDocumentResolver? documentResolver;
    private readonly IHancomSessionSecurity? sessionSecurity;
    private readonly IHancomPlanExecutionResolver? planExecutionResolver;
    private readonly HancomBindingExecutor bindingExecutor;
    private readonly IHancomModalWatchdogFactory modalWatchdogFactory;
    private readonly TimeProvider timeProvider;
    private HancomSession? session;
    private HancomTargetProfile? targetProfile;
    private string? capabilityRegistrySha256;
    private string? modalPolicyId;
    private IHancomModalWatchdogSession? modalWatchdog;

    public HancomLifecycleCommandHandler()
        : this(
            () => new HancomSession(),
            documentResolver: null,
            sessionSecurity: null,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            TimeProvider.System,
            new HancomModalWatchdogFactory(timeProvider: TimeProvider.System))
    {
    }

    public HancomLifecycleCommandHandler(HancomSecurityAdapter securityAdapter)
        : this(
            () => new HancomSession(),
            securityAdapter,
            securityAdapter,
            securityAdapter,
            new HancomBindingExecutor(),
            TimeProvider.System,
            new HancomModalWatchdogFactory(timeProvider: TimeProvider.System))
    {
        ArgumentNullException.ThrowIfNull(securityAdapter);
    }

    internal HancomLifecycleCommandHandler(
        Func<HancomSession> sessionFactory,
        IHancomApprovedDocumentResolver? documentResolver,
        TimeProvider timeProvider)
        : this(
            sessionFactory,
            documentResolver,
            sessionSecurity: null,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            timeProvider,
            NoOpHancomModalWatchdogFactory.Instance)
    {
    }

    internal HancomLifecycleCommandHandler(
        Func<HancomSession> sessionFactory,
        IHancomApprovedDocumentResolver? documentResolver,
        IHancomSessionSecurity? sessionSecurity,
        TimeProvider timeProvider)
        : this(
            sessionFactory,
            documentResolver,
            sessionSecurity,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            timeProvider,
            NoOpHancomModalWatchdogFactory.Instance)
    {
    }

    internal HancomLifecycleCommandHandler(
        Func<HancomSession> sessionFactory,
        IHancomApprovedDocumentResolver? documentResolver,
        IHancomSessionSecurity? sessionSecurity,
        IHancomPlanExecutionResolver? planExecutionResolver,
        HancomBindingExecutor bindingExecutor,
        TimeProvider timeProvider,
        IHancomModalWatchdogFactory? modalWatchdogFactory = null)
    {
        this.sessionFactory = sessionFactory ?? throw new ArgumentNullException(nameof(sessionFactory));
        this.documentResolver = documentResolver;
        this.sessionSecurity = sessionSecurity;
        this.planExecutionResolver = planExecutionResolver;
        this.bindingExecutor = bindingExecutor ?? throw new ArgumentNullException(nameof(bindingExecutor));
        this.timeProvider = timeProvider ?? throw new ArgumentNullException(nameof(timeProvider));
        this.modalWatchdogFactory = modalWatchdogFactory ?? NoOpHancomModalWatchdogFactory.Instance;
    }

    public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(context);
        try
        {
            return ExecuteCore(command, context);
        }
        catch (HancomLifecycleException error)
        {
            return Failure(
                command,
                error.Error,
                cleanupRequired: session is not null || modalWatchdog is not null);
        }
    }

    private StaCommandReceipt ExecuteCore(StaCommandEnvelope command, StaExecutionContext context)
    {
        var journal = new HancomEventJournal(timeProvider);
        var before = InspectModal(journal);
        if (before is not null
            && command.CommandCase is not (
                StaCommandEnvelope.CommandOneofCase.StartSession
                or StaCommandEnvelope.CommandOneofCase.CloseSession))
        {
            return ModalFailure(command, before, journal, effectUnknown: false, cleanupCompleted: false);
        }

        var receipt = command.CommandCase switch
        {
            StaCommandEnvelope.CommandOneofCase.StartSession => Start(command, context, journal),
            StaCommandEnvelope.CommandOneofCase.OpenDocument => Open(command, context, journal),
            StaCommandEnvelope.CommandOneofCase.ExecutePlan => ExecutePlan(command, context, journal),
            StaCommandEnvelope.CommandOneofCase.CloseSession => Close(command, context, journal),
            _ => StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.UnknownBinding,
                "p10-04-command-not-yet-implemented",
                effectUnknown: false,
                cleanupRequired: false),
        };

        RecordAutomationSignals(journal, context, command.CommandCase);
        var after = InspectModal(journal);
        var incident = before ?? after;
        if (incident is not null)
        {
            var cleanupCompleted = command.CommandCase == StaCommandEnvelope.CommandOneofCase.CloseSession
                && session is null
                && receipt.State == ExecutionState.Succeeded;
            var effectUnknown = receipt.State == ExecutionState.UnknownOutcome
                || (receipt.State == ExecutionState.Succeeded
                    && command.CommandCase is StaCommandEnvelope.CommandOneofCase.ExecutePlan
                        or StaCommandEnvelope.CommandOneofCase.SaveDocument
                        or StaCommandEnvelope.CommandOneofCase.RenderDocument);
            return ModalFailure(command, incident, journal, effectUnknown, cleanupCompleted);
        }

        receipt.Events.Clear();
        receipt.Events.Add(journal.Snapshot());
        return receipt;
    }

    public void Cleanup(StaExecutionContext context)
    {
        var current = session;
        var watcher = Interlocked.Exchange(ref modalWatchdog, null);
        Exception? watcherError = null;
        try
        {
            watcher?.Dispose();
        }
        catch (Exception error)
        {
            watcherError = error;
        }

        if (current is null)
        {
            if (watcherError is not null)
            {
                throw new HancomLifecycleException(
                    HancomLifecycleError.ModalWatchdogStopFailed,
                    watcherError);
            }

            return;
        }

        try
        {
            current.Shutdown(context);
        }
        catch
        {
            session = current;
            throw;
        }

        session = null;
        targetProfile = null;
        capabilityRegistrySha256 = null;
        modalPolicyId = null;
        if (watcherError is not null)
        {
            throw new HancomLifecycleException(
                HancomLifecycleError.ModalWatchdogStopFailed,
                watcherError);
        }
    }

    private StaCommandReceipt Start(
        StaCommandEnvelope command,
        StaExecutionContext context,
        HancomEventJournal journal)
    {
        if (session is not null)
        {
            return Failure(command, HancomLifecycleError.InvalidState, cleanupRequired: true);
        }

        var created = sessionFactory();
        session = created;
        try
        {
            var profile = HancomTargetProfile.From(command.StartSession.TargetProfile);
            created.Start(profile, context);
            sessionSecurity?.Apply(command.StartSession, created, context);
            targetProfile = profile;
            capabilityRegistrySha256 = command.StartSession.CapabilityRegistrySha256;
            modalPolicyId = command.StartSession.SecurityPolicy.ModalPolicyId;
            modalWatchdog = modalWatchdogFactory.Start(
                created.OwnedProcessId
                    ?? throw new HancomLifecycleException(HancomLifecycleError.ProcessOwnershipFailed),
                profile,
                modalPolicyId);
            journal.Record(StaEventType.SessionStarted, "hancom-session-started");
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
        catch (HancomLifecycleException error)
        {
            var cleanupRequired = created.State == HancomSessionState.Faulted;
            try
            {
                if (created.State != HancomSessionState.Closed)
                {
                    created.Shutdown(context);
                }

                session = null;
                targetProfile = null;
                capabilityRegistrySha256 = null;
                modalPolicyId = null;
                var watcher = Interlocked.Exchange(ref modalWatchdog, null);
                watcher?.Dispose();
            }
            catch
            {
                cleanupRequired = true;
            }

            return Failure(
                command,
                error.Error,
                cleanupRequired);
        }
    }

    private StaCommandReceipt ExecutePlan(
        StaCommandEnvelope command,
        StaExecutionContext context,
        HancomEventJournal journal)
    {
        if (session is null || targetProfile is null || capabilityRegistrySha256 is null)
        {
            return Failure(command, HancomLifecycleError.InvalidState, cleanupRequired: false);
        }

        if (planExecutionResolver is null)
        {
            return StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.PolicyDenied,
                "p10-06-binding-approval-required",
                effectUnknown: false,
                cleanupRequired: false);
        }

        try
        {
            using var approved = planExecutionResolver.Resolve(command.ExecutePlan, context);
            var result = bindingExecutor.Execute(
                command.ExecutePlan,
                approved,
                session,
                targetProfile,
                capabilityRegistrySha256,
                context);
            journal.Record(
                StaEventType.PlanExecuted,
                $"hancom-plan-executed:{result.OperationCount}:{result.PlanSha256}:{result.BundleSha256}");
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
        catch (HancomBindingException error)
        {
            return BindingFailure(
                command,
                error,
                cleanupRequired: error.EffectUnknown || session.State == HancomSessionState.Faulted);
        }
        catch (HancomLifecycleException error)
        {
            return Failure(command, error.Error, cleanupRequired: false);
        }
    }

    private StaCommandReceipt Open(
        StaCommandEnvelope command,
        StaExecutionContext context,
        HancomEventJournal journal)
    {
        if (session is null)
        {
            return Failure(command, HancomLifecycleError.InvalidState, cleanupRequired: false);
        }

        if (documentResolver is null)
        {
            return StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.PolicyDenied,
                "p10-05-path-approval-required",
                effectUnknown: false,
                cleanupRequired: false);
        }

        HancomApprovedDocument? approved = null;
        try
        {
            approved = documentResolver.Resolve(command.OpenDocument, context);
            session.Open(approved, context);
            approved = null;
            journal.Record(StaEventType.DocumentOpened, "hancom-document-opened");
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
        catch (HancomLifecycleException error)
        {
            return Failure(
                command,
                error.Error,
                cleanupRequired: session.State == HancomSessionState.Faulted);
        }
        finally
        {
            approved?.Dispose();
        }
    }

    private StaCommandReceipt Close(
        StaCommandEnvelope command,
        StaExecutionContext context,
        HancomEventJournal journal)
    {
        if (session is null)
        {
            return Failure(command, HancomLifecycleError.InvalidState, cleanupRequired: false);
        }

        try
        {
            var current = session;
            current.Shutdown(context);
            journal.RecordAutomationSignals(
                current.DrainAutomationSignals(context),
                StaEventType.CleanupCompleted);
            var watcher = Interlocked.Exchange(ref modalWatchdog, null);
            watcher?.Dispose();
            session = null;
            targetProfile = null;
            capabilityRegistrySha256 = null;
            modalPolicyId = null;
            journal.Record(StaEventType.CleanupCompleted, "hancom-session-closed");
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
        catch (HancomLifecycleException error)
        {
            return Failure(command, error.Error, cleanupRequired: true);
        }
    }

    private static StaCommandReceipt BindingFailure(
        StaCommandEnvelope command,
        HancomBindingException error,
        bool cleanupRequired)
    {
        var uncertain = error.EffectUnknown || cleanupRequired;
        var code = error.Error switch
        {
            HancomBindingError.TargetMismatch => BridgeErrorCode.ProfileMismatch,
            HancomBindingError.PlanInvalid => BridgeErrorCode.ArtifactMismatch,
            HancomBindingError.BundleInvalid or HancomBindingError.SignatureInvalid or
                HancomBindingError.LeaseConsumed => BridgeErrorCode.PolicyDenied,
            HancomBindingError.UnknownBinding or HancomBindingError.ArgumentInvalid =>
                BridgeErrorCode.UnknownBinding,
            HancomBindingError.ActionFailed => BridgeErrorCode.ComFailure,
            _ => BridgeErrorCode.UnknownOutcome,
        };
        return StaWorkerServer.CreateFailureReceipt(
            command,
            uncertain ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
            code,
            $"hancom-binding-{error.Error.ToString().ToLowerInvariant()}",
            effectUnknown: uncertain,
            cleanupRequired: uncertain);
    }

    private void RecordAutomationSignals(
        HancomEventJournal journal,
        StaExecutionContext context,
        StaCommandEnvelope.CommandOneofCase commandCase)
    {
        if (session is null)
        {
            return;
        }

        var carrierEventType = commandCase switch
        {
            StaCommandEnvelope.CommandOneofCase.StartSession => StaEventType.SessionStarted,
            StaCommandEnvelope.CommandOneofCase.OpenDocument => StaEventType.DocumentOpened,
            StaCommandEnvelope.CommandOneofCase.ExecutePlan => StaEventType.PlanExecuted,
            StaCommandEnvelope.CommandOneofCase.SaveDocument => StaEventType.OutputSaved,
            StaCommandEnvelope.CommandOneofCase.RenderDocument => StaEventType.RenderCompleted,
            _ => StaEventType.Unspecified,
        };
        if (carrierEventType == StaEventType.Unspecified)
        {
            return;
        }

        journal.RecordAutomationSignals(
            session.DrainAutomationSignals(context),
            carrierEventType);
    }

    private HancomModalIncident? InspectModal(HancomEventJournal journal)
    {
        var watcher = modalWatchdog;
        if (watcher is null)
        {
            return null;
        }

        watcher.ScanNow();
        var incidents = watcher.DrainIncidents();
        HancomModalIncident? first = null;
        foreach (var incident in incidents)
        {
            journal.RecordDigest(incident.EventType, incident.SafeMetadataSha256);
            first ??= incident;
        }

        return first;
    }

    private static StaCommandReceipt ModalFailure(
        StaCommandEnvelope command,
        HancomModalIncident incident,
        HancomEventJournal journal,
        bool effectUnknown,
        bool cleanupCompleted) =>
        StaWorkerServer.CreateFailureReceipt(
            command,
            effectUnknown ? ExecutionState.UnknownOutcome : ExecutionState.Failed,
            incident.ErrorCode,
            incident.Disposition == HancomModalDisposition.UnknownBlocked
                ? "hancom-modal-unknown"
                : "hancom-modal-expected-report-and-stop",
            effectUnknown,
            cleanupRequired: incident.RequiresRecycle && !cleanupCompleted,
            events: journal.Snapshot(),
            safeDetailSha256: incident.SafeMetadataSha256);

    private static StaCommandReceipt Failure(
        StaCommandEnvelope command,
        HancomLifecycleError error,
        bool cleanupRequired)
    {
        var cleanupFailure = error is HancomLifecycleError.CleanupFailed
            or HancomLifecycleError.CleanupOwnershipMismatch
            or HancomLifecycleError.CloseFailed
            or HancomLifecycleError.QuitFailed;
        var uncertain = cleanupRequired || cleanupFailure;
        var state = uncertain ? ExecutionState.UnknownOutcome : ExecutionState.Failed;
        var code = error switch
        {
            HancomLifecycleError.InvalidTarget
                or HancomLifecycleError.WrongProcessArchitecture
                or HancomLifecycleError.RegistrationMissing
                or HancomLifecycleError.RegistrationInvalid
                or HancomLifecycleError.ExecutableMismatch
                or HancomLifecycleError.PreexistingProcess
                or HancomLifecycleError.AutomationVersionMismatch => BridgeErrorCode.ProfileMismatch,
            HancomLifecycleError.InputRejected or HancomLifecycleError.InputChanged =>
                BridgeErrorCode.ArtifactMismatch,
            HancomLifecycleError.SecurityLeaseInvalid
                or HancomLifecycleError.SecurityLeaseExpired
                or HancomLifecycleError.SecurityPolicyMismatch
                or HancomLifecycleError.SecurityLeaseConsumed => BridgeErrorCode.PolicyDenied,
            HancomLifecycleError.SecurityModuleInvalid => BridgeErrorCode.ProfileMismatch,
            HancomLifecycleError.SecurityModuleRegistrationFailed => BridgeErrorCode.PolicyDenied,
            HancomLifecycleError.EventSubscriptionFailed => BridgeErrorCode.ProfileMismatch,
            HancomLifecycleError.ModalPolicyInvalid => BridgeErrorCode.PolicyDenied,
            HancomLifecycleError.ModalWatchdogOverflow
                or HancomLifecycleError.ModalWatchdogStopFailed => BridgeErrorCode.UnknownModal,
            HancomLifecycleError.EventInvalid or HancomLifecycleError.EventOverflow =>
                BridgeErrorCode.UnknownOutcome,
            HancomLifecycleError.CleanupFailed or HancomLifecycleError.CleanupOwnershipMismatch =>
                BridgeErrorCode.CleanupFailed,
            HancomLifecycleError.InvalidState => BridgeErrorCode.InvalidEnvelope,
            _ => BridgeErrorCode.ComFailure,
        };
        return StaWorkerServer.CreateFailureReceipt(
            command,
            state,
            code,
            $"hancom-lifecycle-{error.ToString().ToLowerInvariant()}",
            effectUnknown: uncertain,
            cleanupRequired: uncertain);
    }
}
