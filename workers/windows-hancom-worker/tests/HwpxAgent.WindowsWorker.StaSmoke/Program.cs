using System.Diagnostics;
using System.IO.Pipes;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.StaSmoke;

internal static class Program
{
    private const string SessionId = "70000000-0000-4000-8000-000000000001";
    private const string TraceId = "80000000-0000-4000-8000-000000000001";
    private const string ProfileId = "hancom-hangul-2020-secondary";
    private const ulong FencingToken = 23;

    public static async Task<int> Main()
    {
        await StaLoopIsSerializedAndPumpedAsync();
        await ProtobufFramesAreCanonicalAndBoundedAsync();
        await ActiveCommandCancellationIsFailClosedAsync();
        await PipeBindingMismatchFailsBeforeHandlerAsync();
        await CommandSequenceAndLimitsFailClosedAsync();
        await SeparateWorkerHostRunsStaBoundaryAsync();
        Console.WriteLine("Windows STA worker P10-03 apartment, pipe, framing and cancellation smoke passed (6/6)");
        return 0;
    }

    private static async Task StaLoopIsSerializedAndPumpedAsync()
    {
        await using var loop = new StaMessageLoop("p10-03-serialization-test");
        var entered = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var active = 0;
        var maximumActive = 0;
        var threadIds = new List<int>();
        var first = loop.InvokeAsync(
            context =>
            {
                entered.TrySetResult(true);
                var current = Interlocked.Increment(ref active);
                maximumActive = Math.Max(maximumActive, current);
                threadIds.Add(context.ManagedThreadId);
                Require(context.ApartmentState == ApartmentState.STA, "message-loop handler was not STA");
                for (var index = 0; index < 25; index++)
                {
                    context.PumpPendingMessages();
                    Thread.Sleep(2);
                }

                Interlocked.Decrement(ref active);
                return 1;
            },
            CancellationToken.None);
        await entered.Task.WaitAsync(TimeSpan.FromSeconds(5));
        var second = loop.InvokeAsync(
            context =>
            {
                var current = Interlocked.Increment(ref active);
                maximumActive = Math.Max(maximumActive, current);
                threadIds.Add(context.ManagedThreadId);
                Require(context.ApartmentState == ApartmentState.STA, "queued handler was not STA");
                Interlocked.Decrement(ref active);
                return 2;
            },
            CancellationToken.None);
        Require(await first == 1 && await second == 2, "STA work results drifted");
        Require(maximumActive == 1 && threadIds.Distinct().Count() == 1, "STA work was reentrant or changed threads");
    }

    private static async Task ProtobufFramesAreCanonicalAndBoundedAsync()
    {
        var command = StartCommand("71000000-0000-4000-8000-000000000001");
        await using var stream = new MemoryStream();
        await StaPipeFraming.WriteMessageAsync(stream, command, CancellationToken.None);
        stream.Position = 0;
        var payload = await StaPipeFraming.ReadFrameAsync(stream, CancellationToken.None)
            ?? throw new InvalidOperationException("framed command was missing");
        var decoded = WorkerBoundary.DecodeAndValidate(payload);
        Require(decoded.Equals(command), "framed command did not round trip");
        Require(await StaPipeFraming.ReadFrameAsync(stream, CancellationToken.None) is null, "clean frame EOF was not preserved");

        await RequireThrowsAsync<StaTransportException>(async () =>
        {
            await using var nonCanonical = new MemoryStream([0x81, 0x00, 0x00], writable: false);
            _ = await StaPipeFraming.ReadFrameAsync(nonCanonical, CancellationToken.None);
        }, StaTransportError.NonCanonicalLengthPrefix);
        await RequireThrowsAsync<StaTransportException>(async () =>
        {
            await using var oversized = new MemoryStream([0x81, 0x80, 0x40], writable: false);
            _ = await StaPipeFraming.ReadFrameAsync(oversized, CancellationToken.None);
        }, StaTransportError.FrameLimit);
        await RequireThrowsAsync<StaTransportException>(async () =>
        {
            await using var truncated = new MemoryStream([0x02, 0x01], writable: false);
            _ = await StaPipeFraming.ReadFrameAsync(truncated, CancellationToken.None);
        }, StaTransportError.TruncatedFrame);
    }

    private static async Task ActiveCommandCancellationIsFailClosedAsync()
    {
        var options = Options();
        var handler = new CancellableHandler();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
        await using var client = CreateClient(options.PipeName);
        await client.ConnectAsync(5_000, timeout.Token);

        var start = StartCommand("72000000-0000-4000-8000-000000000001");
        await WriteAsync(client, start, timeout.Token);
        var startReceipt = await ReadReceiptAsync(client, timeout.Token);
        Require(startReceipt.State == ExecutionState.Succeeded, "start command did not succeed");

        var execute = ExecuteCommand("72000000-0000-4000-8000-000000000002");
        await WriteAsync(client, execute, timeout.Token);
        await handler.ExecuteEntered.Task.WaitAsync(TimeSpan.FromSeconds(5));
        var cancel = CancelCommand(
            "72000000-0000-4000-8000-000000000003",
            execute.CommandId);
        await WriteAsync(client, cancel, timeout.Token);
        var first = await ReadReceiptAsync(client, timeout.Token);
        var second = await ReadReceiptAsync(client, timeout.Token);
        var receipts = new[] { first, second }.ToDictionary(receipt => receipt.CommandId, StringComparer.Ordinal);
        Require(receipts[cancel.CommandId].State == ExecutionState.Succeeded, "active cancel was not acknowledged");
        Require(receipts[execute.CommandId].State == ExecutionState.UnknownOutcome
            && receipts[execute.CommandId].CleanupRequired
            && receipts[execute.CommandId].Diagnostic?.EffectUnknown == true,
            "cancelled active command was not reconciled as cleanup-required unknown outcome");

        var blocked = ExecuteCommand("72000000-0000-4000-8000-000000000004");
        await WriteAsync(client, blocked, timeout.Token);
        var blockedReceipt = await ReadReceiptAsync(client, timeout.Token);
        Require(blockedReceipt.State == ExecutionState.Failed
            && blockedReceipt.Diagnostic?.ErrorCode == BridgeErrorCode.PolicyDenied
            && blockedReceipt.CleanupRequired,
            "unknown outcome did not restrict the session to cleanup");

        var close = CloseCommand("72000000-0000-4000-8000-000000000005");
        await WriteAsync(client, close, timeout.Token);
        var closeReceipt = await ReadReceiptAsync(client, timeout.Token);
        Require(closeReceipt.State == ExecutionState.Succeeded, "close command did not succeed");
        await server.WaitAsync(TimeSpan.FromSeconds(5));
        Require(handler.MaximumActive == 1
            && handler.ThreadIds.Count == 3
            && handler.ThreadIds.Distinct().Count() == 1
            && handler.ApartmentStates.All(state => state == ApartmentState.STA),
            "pipe commands were not serialized on one STA thread");
    }

    private static async Task PipeBindingMismatchFailsBeforeHandlerAsync()
    {
        var options = Options();
        var handler = new CountingHandler();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
        await using var client = CreateClient(options.PipeName);
        await client.ConnectAsync(5_000, timeout.Token);
        var wrong = StartCommand("73000000-0000-4000-8000-000000000001");
        wrong.FencingToken += 1;
        await WriteAsync(client, wrong, timeout.Token);
        await RequireThrowsAsync<StaTransportException>(
            () => server,
            StaTransportError.BindingMismatch);
        Require(handler.Calls == 0, "binding mismatch reached the STA handler");
    }

    private static async Task SeparateWorkerHostRunsStaBoundaryAsync()
    {
        var options = Options();
        var hostPath = Path.Combine(
            AppContext.BaseDirectory,
            "sta-host",
            "HwpxAgent.WindowsWorker.Host.exe");
        Require(File.Exists(hostPath), "built STA worker host is missing");
        var startInfo = new ProcessStartInfo
        {
            FileName = hostPath,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        foreach (var argument in new[]
        {
            "--pipe", options.PipeName,
            "--session", options.SessionId,
            "--fence", options.FencingToken.ToString(System.Globalization.CultureInfo.InvariantCulture),
            "--trace", options.TraceId,
            "--profile", options.TargetProfileId,
        })
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("STA worker host did not start");
        var stdout = process.StandardOutput.ReadToEndAsync();
        var stderr = process.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        await using var client = CreateClient(options.PipeName);
        await client.ConnectAsync(5_000, timeout.Token);
        var start = StartCommand("74000000-0000-4000-8000-000000000001");
        await WriteAsync(client, start, timeout.Token);
        var startReceipt = await ReadReceiptAsync(client, timeout.Token);
        Require(startReceipt.State == ExecutionState.Succeeded
            && startReceipt.Events.Count == 1
            && startReceipt.Events[0].EventType == StaEventType.SessionStarted,
            "separate host did not execute its STA start boundary");
        var expectedArchitectureDigests = new HashSet<string>(StringComparer.Ordinal)
        {
            StaWorkerServer.Sha256("sta-boundary:x64"),
            StaWorkerServer.Sha256("sta-boundary:x86"),
        };
        Require(expectedArchitectureDigests.Contains(startReceipt.Events[0].SafeMetadataSha256),
            "separate host architecture evidence was not bounded");

        var close = CloseCommand("74000000-0000-4000-8000-000000000002");
        await WriteAsync(client, close, timeout.Token);
        var closeReceipt = await ReadReceiptAsync(client, timeout.Token);
        Require(closeReceipt.State == ExecutionState.Succeeded
            && closeReceipt.Events.Single().EventType == StaEventType.CleanupCompleted,
            "separate host did not close through the STA boundary");
        await process.WaitForExitAsync(timeout.Token);
        Require(process.ExitCode == 0, "separate STA worker host failed");
        Require(string.IsNullOrEmpty(await stdout) && string.IsNullOrEmpty(await stderr),
            "separate STA worker host emitted unexpected output");
    }

    private static async Task CommandSequenceAndLimitsFailClosedAsync()
    {
        await RunCaseAsync(
            Options(),
            StartCommand("75000000-0000-4000-8000-000000000001"),
            CloseCommand("75000000-0000-4000-8000-000000000001"),
            StaTransportError.DuplicateCommand);
        await RunCaseAsync(
            Options(),
            StartCommand("75000000-0000-4000-8000-000000000002"),
            StartCommand("75000000-0000-4000-8000-000000000003"),
            StaTransportError.InvalidSequence);
        var limited = Options() with { MaximumCommandCount = 1 };
        await RunCaseAsync(
            limited,
            StartCommand("75000000-0000-4000-8000-000000000004"),
            CloseCommand("75000000-0000-4000-8000-000000000005"),
            StaTransportError.FrameLimit);
        await FailedStartStopsPipelinedCommandsAsync();

        static async Task RunCaseAsync(
            StaWorkerOptions options,
            StaCommandEnvelope first,
            StaCommandEnvelope rejected,
            StaTransportError expected)
        {
            var handler = new CountingHandler();
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
            var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
            await using var client = CreateClient(options.PipeName);
            await client.ConnectAsync(5_000, timeout.Token);
            await WriteAsync(client, first, timeout.Token);
            _ = await ReadReceiptAsync(client, timeout.Token);
            await WriteAsync(client, rejected, timeout.Token);
            await RequireThrowsAsync<StaTransportException>(() => server, expected);
            Require(handler.Calls == 1, "rejected command reached the STA handler");
        }

        static async Task FailedStartStopsPipelinedCommandsAsync()
        {
            var options = Options();
            var handler = new FailedStartHandler();
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
            var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
            await using var client = CreateClient(options.PipeName);
            await client.ConnectAsync(5_000, timeout.Token);
            await WriteAsync(
                client,
                StartCommand("75000000-0000-4000-8000-000000000006"),
                timeout.Token);
            await WriteAsync(
                client,
                ExecuteCommand("75000000-0000-4000-8000-000000000007"),
                timeout.Token);
            var receipt = await ReadReceiptAsync(client, timeout.Token);
            Require(receipt.State == ExecutionState.Failed, "failed start receipt drifted");
            await RequireThrowsAsync<StaTransportException>(
                () => server,
                StaTransportError.ConnectionClosed);
            Require(handler.Calls == 1, "pipelined command ran after failed start");
        }
    }

    private static StaWorkerOptions Options() =>
        new(
            StaWorkerOptions.CreatePrivatePipeName(),
            SessionId,
            FencingToken,
            TraceId,
            ProfileId,
            ConnectTimeoutSeconds: 5);

    private static NamedPipeClientStream CreateClient(string pipeName) =>
        new(
            ".",
            pipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous | PipeOptions.WriteThrough | PipeOptions.CurrentUserOnly);

    private static StaCommandEnvelope StartCommand(string commandId)
    {
        var command = BaseCommand(commandId);
        command.StartSession = new StaStartSessionCommand
        {
            TargetProfile = new TargetProfileIdentity
            {
                ProfileId = ProfileId,
                ProductBuild = "11.0.0.9136",
                Locale = "ko-KR",
                ProcessArchitecture = "x86",
                ExecutableSha256 = Digest('a'),
                EnvironmentDigest = Digest('b'),
            },
            CapabilityRegistrySha256 = Digest('c'),
            SecurityPolicy = new SecurityPolicy
            {
                FileAccessPolicyId = "file.local_read",
                ModalPolicyId = "modal.fail_closed",
            },
        };
        return command;
    }

    private static StaCommandEnvelope ExecuteCommand(string commandId)
    {
        var command = BaseCommand(commandId);
        command.ExecutePlan = new StaExecutePlanCommand
        {
            OperationPlan = new StagedArtifactRef
            {
                Artifact = new ArtifactRef
                {
                    ArtifactId = "fixture-operation-plan",
                    Sha256 = Digest('d'),
                    SizeBytes = 128,
                },
                SandboxHandle = "plan_0001",
                ReadOnly = true,
            },
            BindingBundleId = "binding.bundle_v1",
            BindingBundleSha256 = Digest('e'),
        };
        return command;
    }

    private static StaCommandEnvelope CloseCommand(string commandId)
    {
        var command = BaseCommand(commandId);
        command.CloseSession = new StaCloseSessionCommand { DiscardUnsavedChanges = true };
        return command;
    }

    private static StaCommandEnvelope CancelCommand(string commandId, string targetCommandId)
    {
        var command = BaseCommand(commandId);
        command.Cancel = new StaCancelCommand { TargetCommandId = targetCommandId };
        return command;
    }

    private static StaCommandEnvelope BaseCommand(string commandId) =>
        new()
        {
            ProtocolMajor = 1,
            ProtocolMinor = 0,
            SessionId = SessionId,
            CommandId = commandId,
            FencingToken = FencingToken,
            DeadlineUnixMs = (ulong)DateTimeOffset.UtcNow.AddSeconds(10).ToUnixTimeMilliseconds(),
            TraceId = TraceId,
        };

    private static async Task WriteAsync(
        Stream stream,
        StaCommandEnvelope command,
        CancellationToken cancellationToken) =>
        await StaPipeFraming.WriteMessageAsync(stream, command, cancellationToken);

    private static async Task<StaCommandReceipt> ReadReceiptAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        var payload = await StaPipeFraming.ReadFrameAsync(stream, cancellationToken)
            ?? throw new InvalidOperationException("STA receipt stream closed early");
        try
        {
            return StaCommandReceipt.Parser.ParseFrom(payload);
        }
        catch (Google.Protobuf.InvalidProtocolBufferException error)
        {
            throw new InvalidOperationException("STA receipt protobuf was malformed", error);
        }
    }

    private static string Digest(char value) => new(value, 64);

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static async Task RequireThrowsAsync<TException>(
        Func<Task> action,
        StaTransportError expectedError)
        where TException : Exception
    {
        try
        {
            await action();
        }
        catch (TException error) when (error is StaTransportException transport && transport.Error == expectedError)
        {
            return;
        }

        throw new InvalidOperationException($"Expected {typeof(TException).Name}/{expectedError}.");
    }

    private sealed class CountingHandler : IStaCommandHandler
    {
        internal int Calls { get; private set; }

        public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
        {
            Calls += 1;
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
    }

    private sealed class CancellableHandler : IStaCommandHandler
    {
        private readonly ApartmentBoundaryCommandHandler boundary = new();
        private int active;

        internal TaskCompletionSource<bool> ExecuteEntered { get; } =
            new(TaskCreationOptions.RunContinuationsAsynchronously);

        internal int MaximumActive { get; private set; }

        internal List<int> ThreadIds { get; } = [];

        internal List<ApartmentState> ApartmentStates { get; } = [];

        public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
        {
            var current = Interlocked.Increment(ref active);
            MaximumActive = Math.Max(MaximumActive, current);
            ThreadIds.Add(context.ManagedThreadId);
            ApartmentStates.Add(context.ApartmentState);
            try
            {
                if (command.CommandCase != StaCommandEnvelope.CommandOneofCase.ExecutePlan)
                {
                    return boundary.Execute(command, context);
                }

                ExecuteEntered.TrySetResult(true);
                while (true)
                {
                    context.PumpPendingMessages();
                    Thread.Sleep(2);
                }
            }
            finally
            {
                Interlocked.Decrement(ref active);
            }
        }
    }

    private sealed class FailedStartHandler : IStaCommandHandler
    {
        internal int Calls { get; private set; }

        public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
        {
            Calls += 1;
            return StaWorkerServer.CreateFailureReceipt(
                command,
                ExecutionState.Failed,
                BridgeErrorCode.ProfileMismatch,
                "test-start-rejected",
                effectUnknown: false,
                cleanupRequired: false);
        }
    }
}
