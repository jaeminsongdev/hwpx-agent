using System.IO.Pipes;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.LifecycleSmoke;

internal static class Program
{
    private const string SessionId = "90000000-0000-4000-8000-000000000001";
    private const string TraceId = "90000000-0000-4000-8000-000000000002";
    private const ulong Fence = 41;
    private const string ExecutableSha256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
    private static string actualStage = "component";

    [STAThread]
    public static async Task<int> Main(string[] args)
    {
        try
        {
            if (args.Length == 1
                && string.Equals(args[0], "--owned-process-exit-child", StringComparison.Ordinal))
            {
                await Task.Delay(750);
                return 0;
            }

            if (args.Length != 0)
            {
                return await RunActualAsync(args);
            }

            Volatile.Write(ref actualStage, "normal-lifecycle");
            await NormalLifecycleIsOrderedAsync();
            Volatile.Write(ref actualStage, "open-failure");
            await OpenFailurePreservesCleanupAsync();
            Volatile.Write(ref actualStage, "input-mutation");
            await InputMutationFailsBeforeOpenReceiptAsync();
            Volatile.Write(ref actualStage, "cleanup-failure");
            await CleanupFailureStillRunsEveryStepAsync();
            Volatile.Write(ref actualStage, "version-mismatch");
            await VersionMismatchCleansActivationAsync();
            Volatile.Write(ref actualStage, "repeated-sessions");
            await RepeatedSessionsLeaveNoFakeOwnerAsync();
            Volatile.Write(ref actualStage, "typed-handler");
            await LifecycleHandlerUsesTypedCommandsAsync();
            Volatile.Write(ref actualStage, "server-cancellation");
            await ServerCancellationRunsStaCleanupHookAsync();
            Volatile.Write(ref actualStage, "disconnect-cleanup");
            await DisconnectRunsStaCleanupHookAsync();
            Volatile.Write(ref actualStage, "owned-process-exit");
            await AbruptOwnedProcessExitIsAcceptedAsync();
            Console.WriteLine("Windows HancomSession P10-04 lifecycle and cleanup smoke passed (10/10)");
            return 0;
        }
        catch (Exception error)
        {
            var errorCode = error is HancomLifecycleException lifecycle
                ? lifecycle.Error.ToString()
                : "none";
            Console.Error.WriteLine(
                $"HANCOM_LIFECYCLE_SMOKE_FAILED stage={Volatile.Read(ref actualStage)} type={error.GetType().Name} code={errorCode}");
            return 2;
        }
    }

    private static async Task NormalLifecycleIsOrderedAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-04-normal");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                Require(session.State == HancomSessionState.Started && session.OwnedProcessId == 701, "start state drifted");
                session.Open(fixture.Document, context);
                Require(session.State == HancomSessionState.DocumentOpen, "open state drifted");
                session.CloseDocument(context);
                session.Shutdown(context);
                Require(session.State == HancomSessionState.Closed, "shutdown state drifted");
                return true;
            },
            CancellationToken.None);
        Require(
            factory.Events.SequenceEqual(["create", "open", "document-close", "document-dispose", "quit", "runtime-dispose", "process-stop", "process-dispose"]),
            "normal lifecycle ordering drifted");
        fixture.RequireUnchanged();
    }

    private static async Task OpenFailurePreservesCleanupAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory { FailOpen = true };
        await using var loop = new StaMessageLoop("p10-04-open-failure");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                RequireThrows(
                    () => session.Open(fixture.Document, context),
                    HancomLifecycleError.OpenFailed);
                Require(session.State == HancomSessionState.Started, "open failure corrupted session state");
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Events.Contains("process-stop") && factory.Events.Contains("quit"), "open failure skipped cleanup");
        fixture.RequireUnchanged();
    }

    private static async Task CleanupFailureStillRunsEveryStepAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory
        {
            FailDocumentClose = true,
            FailQuit = true,
            FailProcessStop = true,
        };
        await using var loop = new StaMessageLoop("p10-04-cleanup-failure");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                session.Open(fixture.Document, context);
                RequireThrows(() => session.Shutdown(context), HancomLifecycleError.CleanupFailed);
                Require(session.State == HancomSessionState.Faulted, "cleanup failure was not terminal");
                return true;
            },
            CancellationToken.None);
        foreach (var required in new[] { "document-close", "document-dispose", "quit", "runtime-dispose", "process-stop", "process-dispose" })
        {
            Require(factory.Events.Contains(required), $"cleanup skipped {required}");
        }
    }

    private static async Task InputMutationFailsBeforeOpenReceiptAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory { MutateOnOpen = true };
        await using var loop = new StaMessageLoop("p10-04-input-mutation");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                RequireThrows(
                    () => session.Open(fixture.Document, context),
                    HancomLifecycleError.InputChanged);
                Require(session.State == HancomSessionState.Faulted, "input mutation was not terminal");
                session.Shutdown(context);
                Require(session.State == HancomSessionState.Closed, "input mutation cleanup did not close");
                return true;
            },
            CancellationToken.None);
        Require(factory.Events.Contains("document-close") && factory.Events.Contains("process-stop"), "input mutation skipped cleanup");
    }

    private static async Task VersionMismatchCleansActivationAsync()
    {
        var factory = new FakeFactory { Version = "11.0.0.9999" };
        await using var loop = new StaMessageLoop("p10-04-version-mismatch");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                RequireThrows(
                    () => session.Start(Profile(), context),
                    HancomLifecycleError.AutomationVersionMismatch);
                Require(factory.Events.Contains("quit") && factory.Events.Contains("process-stop"), "version mismatch leaked ownership");
                return true;
            },
            CancellationToken.None);
    }

    private static async Task RepeatedSessionsLeaveNoFakeOwnerAsync()
    {
        await using var loop = new StaMessageLoop("p10-04-repeat");
        for (var index = 0; index < 32; index++)
        {
            var factory = new FakeFactory();
            await loop.InvokeAsync(
                context =>
                {
                    var session = new HancomSession(factory);
                    session.Start(Profile(), context);
                    session.Shutdown(context);
                    return true;
                },
                CancellationToken.None);
            Require(factory.Events.Count(value => value == "process-stop") == 1, "repeat session owner count drifted");
        }
    }

    private static async Task LifecycleHandlerUsesTypedCommandsAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            new FixedResolver(fixture.Document),
            TimeProvider.System);
        await using var loop = new StaMessageLoop("p10-04-handler");
        await loop.InvokeAsync(
            context =>
            {
                var start = handler.Execute(StartCommand("91000000-0000-4000-8000-000000000001"), context);
                var open = handler.Execute(OpenCommand("91000000-0000-4000-8000-000000000002", fixture.Document), context);
                var close = handler.Execute(CloseCommand("91000000-0000-4000-8000-000000000003"), context);
                Require(start.State == ExecutionState.Succeeded
                    && start.Events.Single().EventType == StaEventType.SessionStarted,
                    "typed start handler failed");
                Require(open.State == ExecutionState.Succeeded
                    && open.Events.Single().EventType == StaEventType.DocumentOpened,
                    "typed open handler failed");
                Require(close.State == ExecutionState.Succeeded
                    && close.Events.Single().EventType == StaEventType.CleanupCompleted,
                    "typed close handler failed");
                handler.Cleanup(context);
                return true;
            },
            CancellationToken.None);
        fixture.RequireUnchanged();
    }

    private static async Task DisconnectRunsStaCleanupHookAsync()
    {
        var factory = new FakeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            documentResolver: null,
            TimeProvider.System);
        var options = Options();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
        await using (var client = new NamedPipeClientStream(
            ".",
            options.PipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly))
        {
            await client.ConnectAsync(5_000, timeout.Token);
            await StaPipeFraming.WriteMessageAsync(
                client,
                StartCommand("92000000-0000-4000-8000-000000000001"),
                timeout.Token);
            _ = await StaPipeFraming.ReadFrameAsync(client, timeout.Token);
        }

        await RequireTransportAsync(server, StaTransportError.ConnectionClosed);
        Require(factory.Events.Contains("process-stop") && factory.Events.Contains("quit"), "disconnect skipped STA cleanup hook");
    }

    private static async Task ServerCancellationRunsStaCleanupHookAsync()
    {
        var factory = new FakeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            documentResolver: null,
            TimeProvider.System);
        var options = Options();
        using var serverCancellation = new CancellationTokenSource();
        using var operationTimeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var server = new StaWorkerServer().RunAsync(options, handler, serverCancellation.Token);
        await using var client = new NamedPipeClientStream(
            ".",
            options.PipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        await client.ConnectAsync(5_000, operationTimeout.Token);
        await StaPipeFraming.WriteMessageAsync(
            client,
            StartCommand("93000000-0000-4000-8000-000000000001"),
            operationTimeout.Token);
        _ = await StaPipeFraming.ReadFrameAsync(client, operationTimeout.Token);

        serverCancellation.Cancel();
        await server.WaitAsync(TimeSpan.FromSeconds(10));
        Require(
            factory.Events.Contains("process-stop") && factory.Events.Contains("quit"),
            "server cancellation skipped STA cleanup hook");
    }

    private static async Task AbruptOwnedProcessExitIsAcceptedAsync()
    {
        var executable = Environment.ProcessPath
            ?? throw new InvalidOperationException("Lifecycle smoke executable path is unavailable.");
        var startInfo = new System.Diagnostics.ProcessStartInfo(executable)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        if (string.Equals(
            Path.GetFileNameWithoutExtension(executable),
            "dotnet",
            StringComparison.OrdinalIgnoreCase))
        {
            startInfo.ArgumentList.Add(typeof(Program).Assembly.Location);
        }
        startInfo.ArgumentList.Add("--owned-process-exit-child");
        using var child = System.Diagnostics.Process.Start(startInfo)
            ?? throw new InvalidOperationException("Lifecycle smoke child process did not start.");
        using var owned = OwnedHancomProcess.Bind(child, executable);
        Require(child.WaitForExit(5_000), "owned-process crash child did not exit");
        Require(child.ExitCode == 0, "owned-process crash child failed");

        await using var loop = new StaMessageLoop("p10-04-owned-process-exit");
        await loop.InvokeAsync(
            context =>
            {
                owned.EnsureStopped(context);
                return true;
            },
            CancellationToken.None);
    }

    private static async Task<int> RunActualAsync(string[] args)
    {
        Volatile.Write(ref actualStage, "parse-arguments");
        var parsed = ParseActualArguments(args);
        Volatile.Write(ref actualStage, "validate-input");
        var input = new HancomApprovedDocument(
            parsed["--input"],
            parsed["--sha256"],
            long.Parse(parsed["--size"], System.Globalization.CultureInfo.InvariantCulture));
        if (Environment.Is64BitProcess || ProcessCount() != 0)
        {
            Console.Error.WriteLine("HANCOM_LIFECYCLE_PREFLIGHT_FAILED");
            return 2;
        }

        Volatile.Write(ref actualStage, "create-sta-loop");
        await using var loop = new StaMessageLoop("p10-04-actual");
        Volatile.Write(ref actualStage, "invoke-sta-loop");
        await loop.InvokeAsync(
            context =>
            {
                Volatile.Write(ref actualStage, "create-session-1");
                var session = new HancomSession();
                Volatile.Write(ref actualStage, "start-session-1");
                session.Start(Profile(), context);
                Volatile.Write(ref actualStage, "open-input");
                session.Open(input, context);
                Volatile.Write(ref actualStage, "close-input");
                session.CloseDocument(context);
                Volatile.Write(ref actualStage, "shutdown-session-1");
                session.Shutdown(context);
                for (var index = 0; index < 2; index++)
                {
                    Volatile.Write(ref actualStage, $"create-session-{index + 2}");
                    var repeated = new HancomSession();
                    Volatile.Write(ref actualStage, $"start-session-{index + 2}");
                    repeated.Start(Profile(), context);
                    Volatile.Write(ref actualStage, $"shutdown-session-{index + 2}");
                    repeated.Shutdown(context);
                }

                return true;
            },
            CancellationToken.None);
        Volatile.Write(ref actualStage, "post-run-delay");
        await Task.Delay(500);
        Volatile.Write(ref actualStage, "post-run-input-integrity");
        input.ValidateIntegrity();
        if (ProcessCount() != 0)
        {
            Console.Error.WriteLine("HANCOM_LIFECYCLE_RESIDUE");
            return 2;
        }

        Console.WriteLine("HANCOM_LIFECYCLE_PASS cycles=3 input_unchanged=true remaining=0");
        return 0;
    }

    private static Dictionary<string, string> ParseActualArguments(string[] args)
    {
        if (args.Length != 7 || !string.Equals(args[0], "--actual", StringComparison.Ordinal))
        {
            throw new ArgumentException("Actual lifecycle smoke requires an exact bounded argument set.", nameof(args));
        }

        var allowed = new HashSet<string>(StringComparer.Ordinal) { "--input", "--sha256", "--size" };
        var parsed = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var index = 1; index < args.Length; index += 2)
        {
            if (!allowed.Contains(args[index])
                || string.IsNullOrWhiteSpace(args[index + 1])
                || !parsed.TryAdd(args[index], args[index + 1]))
            {
                throw new ArgumentException("Actual lifecycle smoke arguments are invalid.", nameof(args));
            }
        }

        return parsed;
    }

    private static int ProcessCount()
    {
        var processes = System.Diagnostics.Process.GetProcessesByName("Hwp");
        try
        {
            return processes.Length;
        }
        finally
        {
            foreach (var process in processes)
            {
                process.Dispose();
            }
        }
    }

    private static HancomTargetProfile Profile() =>
        new(
            HancomTargetProfile.CurrentProfileId,
            HancomTargetProfile.CurrentProgId,
            "11.0.0.9136",
            "ko-KR",
            "x86",
            ExecutableSha256);

    private static StaWorkerOptions Options() =>
        new(
            StaWorkerOptions.CreatePrivatePipeName(),
            SessionId,
            Fence,
            TraceId,
            HancomTargetProfile.CurrentProfileId,
            ConnectTimeoutSeconds: 5);

    private static StaCommandEnvelope StartCommand(string commandId)
    {
        var command = BaseCommand(commandId);
        command.StartSession = new StaStartSessionCommand
        {
            TargetProfile = new TargetProfileIdentity
            {
                ProfileId = HancomTargetProfile.CurrentProfileId,
                ProductBuild = "11.0.0.9136",
                Locale = "ko-KR",
                ProcessArchitecture = "x86",
                ExecutableSha256 = ExecutableSha256,
                EnvironmentDigest = Digest('e'),
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

    private static StaCommandEnvelope OpenCommand(string commandId, HancomApprovedDocument input)
    {
        var command = BaseCommand(commandId);
        command.OpenDocument = new StaOpenDocumentCommand
        {
            Input = new StagedArtifactRef
            {
                Artifact = new ArtifactRef
                {
                    ArtifactId = "p10-04-lifecycle-fixture",
                    Sha256 = input.Sha256,
                    SizeBytes = (ulong)input.SizeBytes,
                },
                SandboxHandle = "lifecycle_input",
                ReadOnly = true,
            },
            OpenPolicyId = "open.read_only",
        };
        return command;
    }

    private static StaCommandEnvelope CloseCommand(string commandId)
    {
        var command = BaseCommand(commandId);
        command.CloseSession = new StaCloseSessionCommand { DiscardUnsavedChanges = true };
        return command;
    }

    private static StaCommandEnvelope BaseCommand(string commandId) =>
        new()
        {
            ProtocolMajor = 1,
            ProtocolMinor = 0,
            SessionId = SessionId,
            CommandId = commandId,
            FencingToken = Fence,
            DeadlineUnixMs = (ulong)DateTimeOffset.UtcNow.AddSeconds(10).ToUnixTimeMilliseconds(),
            TraceId = TraceId,
        };

    private static string Digest(char value) => new(value, 64);

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void RequireThrows(Action action, HancomLifecycleError expected)
    {
        try
        {
            action();
        }
        catch (HancomLifecycleException error) when (error.Error == expected)
        {
            return;
        }

        throw new InvalidOperationException($"Expected {expected}.");
    }

    private static async Task RequireTransportAsync(Task task, StaTransportError expected)
    {
        try
        {
            await task;
        }
        catch (StaTransportException error) when (error.Error == expected)
        {
            return;
        }

        throw new InvalidOperationException($"Expected transport error {expected}.");
    }

    private sealed class FixedResolver(HancomApprovedDocument document) : IHancomApprovedDocumentResolver
    {
        public HancomApprovedDocument Resolve(
            StaOpenDocumentCommand command,
            StaExecutionContext context)
        {
            Require(context.ApartmentState == ApartmentState.STA, "resolver left STA");
            Require(
                string.Equals(
                    command.Input.Artifact.Sha256,
                    document.Sha256,
                    StringComparison.Ordinal),
                "resolver digest drifted");
            return document;
        }
    }

    private sealed class FakeFactory : IHancomRuntimeFactory
    {
        internal List<string> Events { get; } = [];

        internal string Version { get; init; } = "11, 0, 0, 9136";

        internal bool FailOpen { get; init; }

        internal bool MutateOnOpen { get; init; }

        internal bool FailDocumentClose { get; init; }

        internal bool FailQuit { get; init; }

        internal bool FailProcessStop { get; init; }

        public HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context)
        {
            Events.Add("create");
            return new HancomRuntimeLease(
                new FakeRuntime(this),
                new FakeProcess(this));
        }

        private sealed class FakeRuntime(FakeFactory owner) : IHancomAutomationRuntime
        {
            public string Version => owner.Version;

            public bool RegisterFilePathSecurityModule(string registrationName)
            {
                owner.Events.Add("register-security");
                return true;
            }

            public IHancomAutomationDocument Open(HancomApprovedDocument input)
            {
                owner.Events.Add("open");
                if (owner.FailOpen)
                {
                    throw new HancomLifecycleException(HancomLifecycleError.OpenFailed);
                }

                if (owner.MutateOnOpen)
                {
                    using var stream = new FileStream(input.Path, FileMode.Append, FileAccess.Write, FileShare.None);
                    stream.WriteByte(0x01);
                }

                return new FakeDocument(owner);
            }

            public bool ExecuteAction(HancomBoundAction invocation) => true;

            public void Quit()
            {
                owner.Events.Add("quit");
                if (owner.FailQuit)
                {
                    throw new InvalidOperationException("synthetic quit failure");
                }
            }

            public void Dispose() => owner.Events.Add("runtime-dispose");
        }

        private sealed class FakeDocument(FakeFactory owner) : IHancomAutomationDocument
        {
            public void CloseWithoutSaving()
            {
                owner.Events.Add("document-close");
                if (owner.FailDocumentClose)
                {
                    throw new InvalidOperationException("synthetic close failure");
                }
            }

            public void Dispose() => owner.Events.Add("document-dispose");
        }

        private sealed class FakeProcess(FakeFactory owner) : IHancomOwnedProcess
        {
            public int ProcessId => 701;

            public void EnsureStopped(StaExecutionContext context)
            {
                owner.Events.Add("process-stop");
                if (owner.FailProcessStop)
                {
                    throw new InvalidOperationException("synthetic process failure");
                }
            }

            public void Dispose() => owner.Events.Add("process-dispose");
        }
    }

    private sealed class Fixture : IDisposable
    {
        private readonly string directory;

        private Fixture(string directory, HancomApprovedDocument document)
        {
            this.directory = directory;
            Document = document;
        }

        internal HancomApprovedDocument Document { get; }

        internal static Fixture Create()
        {
            var directory = Path.Combine(Path.GetTempPath(), $"hwpx-agent-p10-04-{Guid.NewGuid():N}");
            Directory.CreateDirectory(directory);
            var path = Path.Combine(directory, "fixture.hwpx");
            File.WriteAllBytes(path, [0x50, 0x4b, 0x03, 0x04, 0x01]);
            var digest = HancomApprovedDocument.HashFile(path);
            return new Fixture(directory, new HancomApprovedDocument(path, digest, 5));
        }

        internal void RequireUnchanged() => Document.ValidateIntegrity();

        public void Dispose()
        {
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }
}
