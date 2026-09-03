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
    private readonly TimeProvider timeProvider;
    private HancomSession? session;
    private HancomTargetProfile? targetProfile;
    private string? capabilityRegistrySha256;

    public HancomLifecycleCommandHandler()
        : this(
            () => new HancomSession(),
            documentResolver: null,
            sessionSecurity: null,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            TimeProvider.System)
    {
    }

    public HancomLifecycleCommandHandler(HancomSecurityAdapter securityAdapter)
        : this(
            () => new HancomSession(),
            securityAdapter,
            securityAdapter,
            securityAdapter,
            new HancomBindingExecutor(),
            TimeProvider.System)
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
            timeProvider)
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
            timeProvider)
    {
    }

    internal HancomLifecycleCommandHandler(
        Func<HancomSession> sessionFactory,
        IHancomApprovedDocumentResolver? documentResolver,
        IHancomSessionSecurity? sessionSecurity,
        IHancomPlanExecutionResolver? planExecutionResolver,
        HancomBindingExecutor bindingExecutor,
        TimeProvider timeProvider)
    {
        this.sessionFactory = sessionFactory ?? throw new ArgumentNullException(nameof(sessionFactory));
        this.documentResolver = documentResolver;
        this.sessionSecurity = sessionSecurity;
        this.planExecutionResolver = planExecutionResolver;
        this.bindingExecutor = bindingExecutor ?? throw new ArgumentNullException(nameof(bindingExecutor));
        this.timeProvider = timeProvider ?? throw new ArgumentNullException(nameof(timeProvider));
    }

    public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(context);
        return command.CommandCase switch
        {
            StaCommandEnvelope.CommandOneofCase.StartSession => Start(command, context),
            StaCommandEnvelope.CommandOneofCase.OpenDocument => Open(command, context),
            StaCommandEnvelope.CommandOneofCase.ExecutePlan => ExecutePlan(command, context),
            StaCommandEnvelope.CommandOneofCase.CloseSession => Close(command, context),
            _ => StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.UnknownBinding,
                "p10-04-command-not-yet-implemented",
                effectUnknown: false,
                cleanupRequired: false),
        };
    }

    public void Cleanup(StaExecutionContext context)
    {
        var current = session;
        if (current is null)
        {
            return;
        }

        try
        {
            current.Shutdown(context);
            session = null;
            targetProfile = null;
            capabilityRegistrySha256 = null;
        }
        catch
        {
            session = current;
            throw;
        }
    }

    private StaCommandReceipt Start(StaCommandEnvelope command, StaExecutionContext context)
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
            return Success(command, StaEventType.SessionStarted, "hancom-session-started");
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

    private StaCommandReceipt ExecutePlan(StaCommandEnvelope command, StaExecutionContext context)
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
            return StaWorkerServer.CreateSuccessReceipt(
                command,
                [
                    new StaEventRecord
                    {
                        Sequence = 1,
                        EventType = StaEventType.PlanExecuted,
                        RecordedAtUnixMs = (ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds(),
                        SafeMetadataSha256 = StaWorkerServer.Sha256(
                            $"hancom-plan-executed:{result.OperationCount}:{result.PlanSha256}:{result.BundleSha256}"),
                    },
                ]);
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

    private StaCommandReceipt Open(StaCommandEnvelope command, StaExecutionContext context)
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
            return Success(command, StaEventType.DocumentOpened, "hancom-document-opened");
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

    private StaCommandReceipt Close(StaCommandEnvelope command, StaExecutionContext context)
    {
        if (session is null)
        {
            return Failure(command, HancomLifecycleError.InvalidState, cleanupRequired: false);
        }

        try
        {
            session.Shutdown(context);
            session = null;
            targetProfile = null;
            capabilityRegistrySha256 = null;
            return Success(command, StaEventType.CleanupCompleted, "hancom-session-closed");
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

    private StaCommandReceipt Success(
        StaCommandEnvelope command,
        StaEventType eventType,
        string category) =>
        StaWorkerServer.CreateSuccessReceipt(
            command,
            [
                new StaEventRecord
                {
                    Sequence = 1,
                    EventType = eventType,
                    RecordedAtUnixMs = (ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds(),
                    SafeMetadataSha256 = StaWorkerServer.Sha256(category),
                },
            ]);

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
