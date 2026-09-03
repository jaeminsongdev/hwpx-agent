using System.Collections.Concurrent;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Channels;
using Google.Protobuf;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

public sealed partial record StaWorkerOptions(
    string PipeName,
    string SessionId,
    ulong FencingToken,
    string TraceId,
    string TargetProfileId,
    uint MaximumEventCount = 1_024,
    int MaximumQueuedCommands = 16,
    int MaximumCommandCount = 1_024,
    int MaximumCommandSeconds = 900,
    int ConnectTimeoutSeconds = 30)
{
    public void Validate()
    {
        if (!PipeNamePattern().IsMatch(PipeName)
            || !Guid.TryParseExact(SessionId, "D", out var session)
            || !string.Equals(session.ToString("D"), SessionId, StringComparison.Ordinal)
            || !Guid.TryParseExact(TraceId, "D", out var trace)
            || !string.Equals(trace.ToString("D"), TraceId, StringComparison.Ordinal)
            || FencingToken == 0
            || !TargetProfilePattern().IsMatch(TargetProfileId)
            || MaximumEventCount is 0 or > 10_000
            || MaximumQueuedCommands is < 1 or > 64
            || MaximumCommandCount is < 1 or > 10_000
            || MaximumCommandSeconds is < 1 or > 900
            || ConnectTimeoutSeconds is < 1 or > 300)
        {
            throw new ArgumentException("The STA worker options are not bounded or canonical.");
        }
    }

    public static string CreatePrivatePipeName() => $"hwpx-agent-{Guid.NewGuid():N}";

    [GeneratedRegex("^hwpx-agent-[0-9a-f]{32}$", RegexOptions.CultureInvariant)]
    private static partial Regex PipeNamePattern();

    [GeneratedRegex("^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$", RegexOptions.CultureInvariant)]
    private static partial Regex TargetProfilePattern();
}

public interface IStaCommandHandler
{
    StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context);
}

public sealed class StaWorkerServer(TimeProvider? timeProvider = null)
{
    private const uint ProtocolMajor = 1;
    private const uint ProtocolMinor = 0;
    private readonly TimeProvider timeProvider = timeProvider ?? TimeProvider.System;

    public async Task RunAsync(
        StaWorkerOptions options,
        IStaCommandHandler handler,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(handler);
        options.Validate();
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("The named-pipe STA worker requires Windows.");
        }

        await using var pipe = new NamedPipeServerStream(
            options.PipeName,
            PipeDirection.InOut,
            maxNumberOfServerInstances: 1,
            PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.WriteThrough | PipeOptions.CurrentUserOnly,
            inBufferSize: StaPipeFraming.MaximumFrameBytes,
            outBufferSize: StaPipeFraming.MaximumFrameBytes);
        using var connectTimeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        connectTimeout.CancelAfter(TimeSpan.FromSeconds(options.ConnectTimeoutSeconds));
        await pipe.WaitForConnectionAsync(connectTimeout.Token).ConfigureAwait(false);
        await RunConnectedAsync(pipe, options, handler, cancellationToken).ConfigureAwait(false);
    }

    public async Task RunConnectedAsync(
        Stream duplexStream,
        StaWorkerOptions options,
        IStaCommandHandler handler,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(duplexStream);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(handler);
        options.Validate();
        if (!duplexStream.CanRead || !duplexStream.CanWrite)
        {
            throw new StaTransportException(StaTransportError.UnreadableStream);
        }

        await using var staLoop = new StaMessageLoop();
        try
        {
            using var connectionCancellation = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            using var writeGate = new SemaphoreSlim(1, 1);
            var queue = Channel.CreateBounded<QueuedCommand>(new BoundedChannelOptions(options.MaximumQueuedCommands)
            {
                FullMode = BoundedChannelFullMode.Wait,
                SingleReader = true,
                SingleWriter = true,
                AllowSynchronousContinuations = false,
            });
            var queuedCommands = new ConcurrentDictionary<string, QueuedCommand>(StringComparer.Ordinal);
            var seenCommandIds = new HashSet<string>(StringComparer.Ordinal);
            var receivedStart = false;
            var receivedClose = false;
            var receivedCommandCount = 0;
            var closed = false;
            var cleanupOnly = false;
            var processor = ProcessCommandsAsync();
            Exception? readerError = null;

            try
            {
                while (!connectionCancellation.IsCancellationRequested)
                {
                    var payload = await StaPipeFraming
                        .ReadFrameAsync(duplexStream, connectionCancellation.Token)
                        .ConfigureAwait(false);
                    if (payload is null)
                    {
                        break;
                    }

                    StaCommandEnvelope command;
                    try
                    {
                        command = WorkerBoundary.DecodeAndValidate(payload);
                    }
                    catch (ArgumentException error)
                    {
                        throw new StaTransportException(StaTransportError.InvalidEnvelope, error);
                    }

                    ValidateBinding(command, options);
                    receivedCommandCount = checked(receivedCommandCount + 1);
                    if (receivedCommandCount > options.MaximumCommandCount)
                    {
                        throw new StaTransportException(StaTransportError.FrameLimit);
                    }

                    if (!seenCommandIds.Add(command.CommandId))
                    {
                        throw new StaTransportException(StaTransportError.DuplicateCommand);
                    }

                    if (!receivedStart)
                    {
                        if (command.CommandCase != StaCommandEnvelope.CommandOneofCase.StartSession
                            || !string.Equals(
                                command.StartSession.TargetProfile.ProfileId,
                                options.TargetProfileId,
                                StringComparison.Ordinal))
                        {
                            throw new StaTransportException(StaTransportError.InvalidSequence);
                        }

                        receivedStart = true;
                    }
                    else if (command.CommandCase == StaCommandEnvelope.CommandOneofCase.StartSession || receivedClose)
                    {
                        throw new StaTransportException(StaTransportError.InvalidSequence);
                    }

                    if (command.CommandCase == StaCommandEnvelope.CommandOneofCase.Cancel)
                    {
                        var accepted = queuedCommands.TryGetValue(command.Cancel.TargetCommandId, out var target);
                        if (accepted)
                        {
                            target!.RequestCancel();
                        }

                        var cancelReceipt = accepted
                            ? CreateSuccessReceipt(command)
                            : CreateFailureReceipt(
                                command,
                                ExecutionState.Failed,
                                BridgeErrorCode.Cancelled,
                                "cancel-target-not-active",
                                effectUnknown: false,
                                cleanupRequired: false);
                        await WriteReceiptAsync(command, cancelReceipt).ConfigureAwait(false);
                        continue;
                    }

                    var queued = new QueuedCommand(command);
                    if (!queuedCommands.TryAdd(command.CommandId, queued))
                    {
                        queued.Dispose();
                        throw new StaTransportException(StaTransportError.DuplicateCommand);
                    }

                    await queue.Writer.WriteAsync(queued, connectionCancellation.Token).ConfigureAwait(false);
                    if (command.CommandCase == StaCommandEnvelope.CommandOneofCase.CloseSession)
                    {
                        receivedClose = true;
                    }
                }
            }
            catch (OperationCanceledException) when (connectionCancellation.IsCancellationRequested)
            {
                // A successful close or the caller ended this one connection.
            }
            catch (Exception error)
            {
                readerError = error;
                connectionCancellation.Cancel();
            }
            finally
            {
                queue.Writer.TryComplete();
            }

            try
            {
                await processor.ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (connectionCancellation.IsCancellationRequested)
            {
                // The reader failed, the caller cancelled, or close completed.
            }
            finally
            {
                foreach (var queued in queuedCommands.Values)
                {
                    queued.Dispose();
                }

                queuedCommands.Clear();
            }

            if (readerError is not null)
            {
                System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(readerError).Throw();
            }

            if (!closed && !cancellationToken.IsCancellationRequested)
            {
                throw new StaTransportException(StaTransportError.ConnectionClosed);
            }

            async Task ProcessCommandsAsync()
            {
                try
                {
                    await foreach (var queued in queue.Reader.ReadAllAsync(connectionCancellation.Token).ConfigureAwait(false))
                    {
                        var command = queued.Command;
                        StaCommandReceipt receipt;
                        var handlerInvoked = 0;
                        try
                        {
                            if (cleanupOnly
                                && command.CommandCase != StaCommandEnvelope.CommandOneofCase.CloseSession)
                            {
                                receipt = CreateFailureReceipt(
                                    command,
                                    ExecutionState.Failed,
                                    BridgeErrorCode.PolicyDenied,
                                    "session-cleanup-only",
                                    effectUnknown: false,
                                    cleanupRequired: true);
                            }
                            else
                            {
                                var remainingMilliseconds = checked(
                                    (long)command.DeadlineUnixMs - UtcNowMilliseconds());
                                if (remainingMilliseconds <= 0)
                                {
                                    receipt = CreateFailureReceipt(
                                        command,
                                        ExecutionState.Failed,
                                        BridgeErrorCode.Timeout,
                                        "command-deadline-expired",
                                        effectUnknown: false,
                                        cleanupRequired: false);
                                }
                                else if (remainingMilliseconds > options.MaximumCommandSeconds * 1_000L)
                                {
                                    receipt = CreateFailureReceipt(
                                        command,
                                        ExecutionState.Failed,
                                        BridgeErrorCode.InvalidEnvelope,
                                        "command-deadline-unbounded",
                                        effectUnknown: false,
                                        cleanupRequired: false);
                                }
                                else if (queued.CancelRequested)
                                {
                                    receipt = CreateFailureReceipt(
                                        command,
                                        ExecutionState.Cancelled,
                                        BridgeErrorCode.Cancelled,
                                        "command-cancelled-before-dispatch",
                                        effectUnknown: false,
                                        cleanupRequired: false);
                                }
                                else
                                {
                                    using var deadline = CancellationTokenSource.CreateLinkedTokenSource(
                                        connectionCancellation.Token,
                                        queued.CancellationToken);
                                    deadline.CancelAfter(TimeSpan.FromMilliseconds(remainingMilliseconds));
                                    try
                                    {
                                        receipt = await staLoop.InvokeAsync(
                                            context =>
                                            {
                                                Interlocked.Exchange(ref handlerInvoked, 1);
                                                return handler.Execute(command.Clone(), context);
                                            },
                                            deadline.Token).ConfigureAwait(false);
                                        WorkerBoundary.ValidateReceipt(receipt, command, options.MaximumEventCount);
                                    }
                                    catch (OperationCanceledException)
                                    {
                                        receipt = CreateFailureReceipt(
                                            command,
                                            handlerInvoked == 0 ? ExecutionState.Cancelled : ExecutionState.UnknownOutcome,
                                            queued.CancelRequested ? BridgeErrorCode.Cancelled : BridgeErrorCode.Timeout,
                                            queued.CancelRequested ? "command-cancelled" : "command-timeout",
                                            effectUnknown: handlerInvoked != 0,
                                            cleanupRequired: handlerInvoked != 0);
                                    }
                                    catch (Exception)
                                    {
                                        receipt = CreateFailureReceipt(
                                            command,
                                            handlerInvoked == 0 ? ExecutionState.Failed : ExecutionState.UnknownOutcome,
                                            BridgeErrorCode.UnknownOutcome,
                                            "handler-failure",
                                            effectUnknown: handlerInvoked != 0,
                                            cleanupRequired: handlerInvoked != 0);
                                    }
                                }
                            }

                            await WriteReceiptAsync(command, receipt).ConfigureAwait(false);
                            if (command.CommandCase == StaCommandEnvelope.CommandOneofCase.StartSession
                                && receipt.State != ExecutionState.Succeeded)
                            {
                                break;
                            }

                            cleanupOnly |= receipt.State == ExecutionState.UnknownOutcome
                                || receipt.CleanupRequired;
                            if (command.CommandCase == StaCommandEnvelope.CommandOneofCase.CloseSession)
                            {
                                closed = receipt.State == ExecutionState.Succeeded;
                                connectionCancellation.Cancel();
                                break;
                            }
                        }
                        finally
                        {
                            queuedCommands.TryRemove(command.CommandId, out _);
                            queued.Dispose();
                        }
                    }
                }
                finally
                {
                    connectionCancellation.Cancel();
                }
            }

            async Task WriteReceiptAsync(StaCommandEnvelope command, StaCommandReceipt receipt)
            {
                WorkerBoundary.ValidateReceipt(receipt, command, options.MaximumEventCount);
                await writeGate.WaitAsync(connectionCancellation.Token).ConfigureAwait(false);
                try
                {
                    await StaPipeFraming
                        .WriteMessageAsync(duplexStream, receipt, connectionCancellation.Token)
                        .ConfigureAwait(false);
                }
                finally
                {
                    writeGate.Release();
                }
            }
        }
        finally
        {
            if (handler is IStaCommandHandlerCleanup cleanup)
            {
                using var cleanupTimeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
                await staLoop
                    .InvokeAsync(
                        context =>
                        {
                            cleanup.Cleanup(context);
                            return true;
                        },
                        cleanupTimeout.Token)
                    .WaitAsync(TimeSpan.FromSeconds(10))
                    .ConfigureAwait(false);
            }
        }
    }

    internal static StaCommandReceipt CreateSuccessReceipt(
        StaCommandEnvelope command,
        IEnumerable<StaEventRecord>? events = null) =>
        new()
        {
            ProtocolMajor = ProtocolMajor,
            ProtocolMinor = ProtocolMinor,
            SessionId = command.SessionId,
            CommandId = command.CommandId,
            FencingToken = command.FencingToken,
            State = ExecutionState.Succeeded,
            ValidationState = ValidationState.Unverified,
            InputUnchanged = true,
            Events = { events ?? [] },
        };

    internal static StaCommandReceipt CreateFailureReceipt(
        StaCommandEnvelope command,
        ExecutionState state,
        BridgeErrorCode errorCode,
        string safeCategory,
        bool effectUnknown,
        bool cleanupRequired,
        IEnumerable<StaEventRecord>? events = null,
        string? safeDetailSha256 = null) =>
        new()
        {
            ProtocolMajor = ProtocolMajor,
            ProtocolMinor = ProtocolMinor,
            SessionId = command.SessionId,
            CommandId = command.CommandId,
            FencingToken = command.FencingToken,
            State = state,
            ValidationState = ValidationState.Unverified,
            InputUnchanged = true,
            CleanupRequired = cleanupRequired,
            Events = { events ?? [] },
            Diagnostic = new BridgeDiagnostic
            {
                ErrorCode = errorCode,
                SafeDetailSha256 = safeDetailSha256 ?? Sha256(safeCategory),
                Retryable = !effectUnknown && errorCode is BridgeErrorCode.Timeout or BridgeErrorCode.Cancelled,
                EffectUnknown = effectUnknown,
            },
        };

    internal static string Sha256(string value) =>
        Convert.ToHexStringLower(SHA256.HashData(Encoding.ASCII.GetBytes(value)));

    private static void ValidateBinding(StaCommandEnvelope command, StaWorkerOptions options)
    {
        if (!string.Equals(command.SessionId, options.SessionId, StringComparison.Ordinal)
            || command.FencingToken != options.FencingToken
            || !string.Equals(command.TraceId, options.TraceId, StringComparison.Ordinal))
        {
            throw new StaTransportException(StaTransportError.BindingMismatch);
        }
    }

    private long UtcNowMilliseconds() => timeProvider.GetUtcNow().ToUnixTimeMilliseconds();

    private sealed class QueuedCommand : IDisposable
    {
        private readonly CancellationTokenSource cancellation = new();
        private int cancelRequested;

        internal QueuedCommand(StaCommandEnvelope command)
        {
            Command = command.Clone();
        }

        internal StaCommandEnvelope Command { get; }

        internal CancellationToken CancellationToken => cancellation.Token;

        internal bool CancelRequested => Volatile.Read(ref cancelRequested) != 0;

        internal void RequestCancel()
        {
            Interlocked.Exchange(ref cancelRequested, 1);
            cancellation.Cancel();
        }

        public void Dispose() => cancellation.Dispose();
    }
}

public sealed class ApartmentBoundaryCommandHandler(TimeProvider? timeProvider = null) : IStaCommandHandler
{
    private readonly TimeProvider timeProvider = timeProvider ?? TimeProvider.System;

    public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(context);
        context.ThrowIfCancellationRequested();
        context.PumpPendingMessages();
        if (context.ApartmentState != ApartmentState.STA)
        {
            throw new InvalidOperationException("The command handler is not running in an STA apartment.");
        }

        var eventType = command.CommandCase switch
        {
            StaCommandEnvelope.CommandOneofCase.StartSession => StaEventType.SessionStarted,
            StaCommandEnvelope.CommandOneofCase.CloseSession => StaEventType.CleanupCompleted,
            _ => StaEventType.Unspecified,
        };
        if (eventType == StaEventType.Unspecified)
        {
            return StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.UnknownBinding,
                "p10-03-command-not-yet-implemented",
                effectUnknown: false,
                cleanupRequired: false);
        }

        return StaWorkerServer.CreateSuccessReceipt(
            command,
            [
                new StaEventRecord
                {
                    Sequence = 1,
                    EventType = eventType,
                    RecordedAtUnixMs = (ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds(),
                    SafeMetadataSha256 = StaWorkerServer.Sha256(
                        $"sta-boundary:{(Environment.Is64BitProcess ? "x64" : "x86")}"),
                },
            ]);
    }
}
