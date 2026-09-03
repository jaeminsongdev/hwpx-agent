using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

public interface IStaCommandHandlerCleanup
{
    void Cleanup(StaExecutionContext context);
}

internal interface IHancomApprovedDocumentResolver
{
    HancomApprovedDocument Resolve(StagedArtifactRef input);
}

public sealed class HancomLifecycleCommandHandler : IStaCommandHandler, IStaCommandHandlerCleanup
{
    private readonly Func<HancomSession> sessionFactory;
    private readonly IHancomApprovedDocumentResolver? documentResolver;
    private readonly TimeProvider timeProvider;
    private HancomSession? session;

    public HancomLifecycleCommandHandler()
        : this(() => new HancomSession(), documentResolver: null, TimeProvider.System)
    {
    }

    internal HancomLifecycleCommandHandler(
        Func<HancomSession> sessionFactory,
        IHancomApprovedDocumentResolver? documentResolver,
        TimeProvider timeProvider)
    {
        this.sessionFactory = sessionFactory ?? throw new ArgumentNullException(nameof(sessionFactory));
        this.documentResolver = documentResolver;
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
            return Success(command, StaEventType.SessionStarted, "hancom-session-started");
        }
        catch (HancomLifecycleException error)
        {
            return Failure(
                command,
                error.Error,
                cleanupRequired: created.State == HancomSessionState.Faulted);
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

        try
        {
            var approved = documentResolver.Resolve(command.OpenDocument.Input);
            session.Open(approved, context);
            return Success(command, StaEventType.DocumentOpened, "hancom-document-opened");
        }
        catch (HancomLifecycleException error)
        {
            return Failure(
                command,
                error.Error,
                cleanupRequired: session.State == HancomSessionState.Faulted);
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
            return Success(command, StaEventType.CleanupCompleted, "hancom-session-closed");
        }
        catch (HancomLifecycleException error)
        {
            return Failure(command, error.Error, cleanupRequired: true);
        }
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
