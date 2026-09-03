using System.IO.Pipes;
using System.Security.Cryptography;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.ModalWatchdogSmoke;

internal static class Program
{
    private const string SessionId = "b0000000-0000-4000-8000-000000000001";
    private const string TraceId = "b0000000-0000-4000-8000-000000000002";
    private const string ExecutableSha256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
    private const ulong Fence = 47;
    private static string actualStage = "component";

    [STAThread]
    private static async Task<int> Main(string[] args)
    {
        try
        {
            if (args.Length == 1 && string.Equals(args[0], "--actual-event-delivery", StringComparison.Ordinal))
            {
                return await ActualEventDeliveryAsync();
            }

            if (args.Length == 2 && string.Equals(args[0], "--actual-modal-probe", StringComparison.Ordinal))
            {
                return ActualModalProbe(args[1]);
            }

            if (args.Length != 0)
            {
                throw new ArgumentException("Unknown modal watchdog smoke arguments.", nameof(args));
            }

            EventJournalIsFiniteAndRedacted();
            EventDispatchDoesNotRetainRawHyperlinkText();
            InvalidPolicyFailsClosed();
            UnknownModalFailsClosed();
            ExactExpectedFingerprintIsDistinguished();
            FingerprintDriftBecomesUnknown();
            ProbeFailureBecomesUnknown();
            NullProbeCollectionBecomesUnknown();
            await BackgroundPollDetectsModalAsync();
            await HandlerRejectsDetectedModalAsync();
            await HandlerConvertsWatchdogFailureToReceiptAsync();
            await CleanupRequiredReceiptStopsFurtherDispatchAsync();
            NativeProbeRejectsInvalidProcess();
            Console.WriteLine("Windows Hancom P10-07 event and modal watchdog smoke passed (13/13)");
            return 0;
        }
        catch (Exception error)
        {
            var inner = error.InnerException;
            Console.Error.WriteLine(
                $"HANCOM_MODAL_WATCHDOG_SMOKE_FAILED:{error.GetType().Name}:"
                + $"stage={Volatile.Read(ref actualStage)}:"
                + $"category={SafeFailureCategory(error)}:"
                + $"code={(error is HancomLifecycleException lifecycle ? lifecycle.Error : "untyped")}:"
                + $"inner_type={inner?.GetType().Name ?? "none"}:"
                + $"inner_hresult=0x{(inner?.HResult ?? 0):x8}");
            return 2;
        }
    }

    private static void EventJournalIsFiniteAndRedacted()
    {
        var journal = new HancomEventJournal(TimeProvider.System, maximumEvents: 2);
        journal.Record(StaEventType.SessionStarted, "event.session_started");
        journal.RecordAutomationSignals(
            [new HancomAutomationSignal("document.after_open", Digest('a'))],
            StaEventType.DocumentOpened);
        var events = journal.Snapshot();
        Require(events.Count == 2 && events[0].Sequence == 1 && events[1].Sequence == 2, "event order drifted");
        Require(events[1].EventType == StaEventType.DocumentOpened, "COM signal escaped the v1 carrier event");
        Require(events.All(value => IsDigest(value.SafeMetadataSha256)), "event metadata was not hashed");
        RequireLifecycle(
            () => journal.Record(StaEventType.PlanExecuted, "event.overflow"),
            HancomLifecycleError.EventOverflow);

        var invalidCarrierJournal = new HancomEventJournal(TimeProvider.System);
        RequireLifecycle(
            () => invalidCarrierJournal.RecordAutomationSignals(
                [new HancomAutomationSignal("document.after_open", Digest('a'))],
                StaEventType.UnknownModal),
            HancomLifecycleError.EventInvalid);

        var unsafeJournal = new HancomEventJournal(TimeProvider.System);
        RequireLifecycle(
            () => unsafeJournal.Record(StaEventType.PlanExecuted, "D:/private/document.hwpx"),
            HancomLifecycleError.EventInvalid);
    }

    private static void EventDispatchDoesNotRetainRawHyperlinkText()
    {
        var dispatch = new HancomObjectEventDispatch();
        dispatch.DocumentAfterOpen(17);
        _ = dispatch.DocumentClickedHyperlink(3, "https://private.invalid/secret", "private display text");
        var signals = dispatch.Drain();
        Require(signals.Count == 2, "event dispatch count drifted");
        Require(
            signals.All(value => IsDigest(value.SafeMetadataSha256))
                && signals.All(value => !value.ToString().Contains("private", StringComparison.OrdinalIgnoreCase)),
            "raw event payload escaped into a signal");
    }

    private static void InvalidPolicyFailsClosed()
    {
        var factory = new HancomModalWatchdogFactory(
            new FixedProbe([]),
            new NullPolicyResolver(),
            TimeProvider.System);
        RequireLifecycle(
            () => factory.Start(101, Profile(), FailClosedHancomModalPolicyResolver.PolicyId),
            HancomLifecycleError.ModalPolicyInvalid);

        var mismatched = Policy([]) with { ProductBuild = "11.0.0.0" };
        factory = new HancomModalWatchdogFactory(
            new FixedProbe([]),
            new FixedPolicyResolver(mismatched),
            TimeProvider.System);
        RequireLifecycle(
            () => factory.Start(101, Profile(), FailClosedHancomModalPolicyResolver.PolicyId),
            HancomLifecycleError.ModalPolicyInvalid);
    }

    private static void UnknownModalFailsClosed()
    {
        var observation = Observation('a', 'b', 'c', captured: true);
        using var session = CreateWatchdog(
            new FixedProbe([observation]),
            new FixedPolicyResolver(Policy([])));
        var incidents = session.DrainIncidents();
        Require(incidents.Count == 1, "unknown modal was not detected");
        var incident = incidents[0];
        Require(
            incident.Disposition == HancomModalDisposition.UnknownBlocked
                && incident.ErrorCode == BridgeErrorCode.UnknownModal
                && incident.EventType == StaEventType.UnknownModal
                && incident.ScreenshotCaptured
                && !incident.AutoResponseAttempted
                && !incident.RawDialogTextLogged
                && incident.RequiresRecycle
                && IsDigest(incident.SafeMetadataSha256),
            "unknown modal did not fail closed");
    }

    private static void ExactExpectedFingerprintIsDistinguished()
    {
        var observation = Observation('d', 'e', 'f', captured: false);
        var fingerprint = new HancomExpectedDialogFingerprint(
            "fixture.expected",
            observation.WindowClassSha256,
            observation.WindowTitleSha256,
            observation.ControlStructureSha256,
            100,
            1_000,
            100,
            1_000);
        using var session = CreateWatchdog(
            new FixedProbe([observation]),
            new FixedPolicyResolver(Policy([fingerprint])));
        var incident = session.DrainIncidents().Single();
        Require(
            incident.Disposition == HancomModalDisposition.ExpectedBlocked
                && incident.ErrorCode == BridgeErrorCode.PolicyDenied
                && incident.EventType == StaEventType.ExpectedModal
                && !incident.AutoResponseAttempted,
            "expected report-and-stop modal classification drifted");
    }

    private static void FingerprintDriftBecomesUnknown()
    {
        var observation = Observation('1', '2', '3', captured: true);
        var fingerprint = new HancomExpectedDialogFingerprint(
            "fixture.expected",
            observation.WindowClassSha256,
            observation.WindowTitleSha256,
            Digest('4'),
            100,
            1_000,
            100,
            1_000);
        using var session = CreateWatchdog(
            new FixedProbe([observation]),
            new FixedPolicyResolver(Policy([fingerprint])));
        Require(
            session.DrainIncidents().Single().Disposition == HancomModalDisposition.UnknownBlocked,
            "fingerprint drift was treated as expected");
    }

    private static void ProbeFailureBecomesUnknown()
    {
        using var session = CreateWatchdog(
            new ThrowingProbe(),
            new FixedPolicyResolver(Policy([])));
        var incident = session.DrainIncidents().Single();
        Require(
            incident.Disposition == HancomModalDisposition.UnknownBlocked
                && !incident.ScreenshotCaptured,
            "probe failure did not become a redacted unknown-modal incident");
    }

    private static void NullProbeCollectionBecomesUnknown()
    {
        using var session = CreateWatchdog(
            new NullProbe(),
            new FixedPolicyResolver(Policy([])));
        var incident = session.DrainIncidents().Single();
        Require(
            incident.Disposition == HancomModalDisposition.UnknownBlocked
                && incident.ErrorCode == BridgeErrorCode.UnknownModal,
            "null probe collection did not fail closed");
    }

    private static async Task BackgroundPollDetectsModalAsync()
    {
        var probe = new SwitchProbe();
        using var session = new HancomModalWatchdogSession(
            processId: 101,
            Policy([]),
            probe,
            TimeProvider.System,
            TimeSpan.FromMilliseconds(10),
            maximumIncidents: 4);
        Require(session.DrainIncidents().Count == 0, "background probe started dirty");
        probe.Enabled = true;
        await Task.Delay(100);
        Require(session.DrainIncidents().Any(), "background poll did not detect a modal");
    }

    private static async Task HandlerRejectsDetectedModalAsync()
    {
        var incident = UnknownIncident();
        var factory = new FakeRuntimeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            documentResolver: null,
            sessionSecurity: null,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            TimeProvider.System,
            new FixedWatchdogFactory(incident));
        await using var loop = new StaMessageLoop("p10-07-handler-modal");
        await loop.InvokeAsync(
            context =>
            {
                var receipt = handler.Execute(StartCommand("b1000000-0000-4000-8000-000000000001"), context);
                Require(
                    receipt.State == ExecutionState.Failed
                        && receipt.Diagnostic?.ErrorCode == BridgeErrorCode.UnknownModal
                        && !receipt.Diagnostic.EffectUnknown
                        && receipt.CleanupRequired
                        && receipt.Events.Any(value => value.EventType == StaEventType.UnknownModal),
                    "handler did not reject the detected modal");
                handler.Cleanup(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Events.Contains("process-stop"), "modal cleanup skipped the owned process");
    }

    private static async Task HandlerConvertsWatchdogFailureToReceiptAsync()
    {
        var factory = new FakeRuntimeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            documentResolver: null,
            sessionSecurity: null,
            planExecutionResolver: null,
            new HancomBindingExecutor(),
            TimeProvider.System,
            new ThrowingWatchdogFactory());
        await using var loop = new StaMessageLoop("p10-07-handler-watchdog-failure");
        await loop.InvokeAsync(
            context =>
            {
                var receipt = handler.Execute(StartCommand("b1000000-0000-4000-8000-000000000002"), context);
                Require(
                    receipt.State == ExecutionState.UnknownOutcome
                        && receipt.Diagnostic?.ErrorCode == BridgeErrorCode.UnknownModal
                        && receipt.Diagnostic.EffectUnknown
                        && receipt.CleanupRequired,
                    "watchdog failure escaped the typed receipt boundary");
                handler.Cleanup(context);
                return true;
            },
            CancellationToken.None);
    }

    private static async Task CleanupRequiredReceiptStopsFurtherDispatchAsync()
    {
        var handler = new CleanupOnlyHandler();
        var options = Options();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var server = new StaWorkerServer().RunAsync(options, handler, timeout.Token);
        await using var client = new NamedPipeClientStream(
            ".",
            options.PipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        await client.ConnectAsync(5_000, timeout.Token);

        var start = StartCommand("b2000000-0000-4000-8000-000000000001");
        var open = BaseCommand("b2000000-0000-4000-8000-000000000002");
        open.OpenDocument = new StaOpenDocumentCommand
        {
            Input = Staged("cleanup-input"),
            OpenPolicyId = "open.read_only",
        };
        var execute = BaseCommand("b2000000-0000-4000-8000-000000000003");
        execute.ExecutePlan = new StaExecutePlanCommand
        {
            OperationPlan = Staged("cleanup-plan"),
            BindingBundleId = "bundle.current",
            BindingBundleSha256 = Digest('b'),
        };
        var close = BaseCommand("b2000000-0000-4000-8000-000000000004");
        close.CloseSession = new StaCloseSessionCommand { DiscardUnsavedChanges = true };

        await SendAsync(client, start, timeout.Token);
        Require((await ReceiveAsync(client, timeout.Token)).State == ExecutionState.Succeeded, "start failed");
        await SendAsync(client, open, timeout.Token);
        var blocked = await ReceiveAsync(client, timeout.Token);
        Require(blocked.CleanupRequired && blocked.State == ExecutionState.Failed, "cleanup-required setup failed");
        await SendAsync(client, execute, timeout.Token);
        var denied = await ReceiveAsync(client, timeout.Token);
        Require(
            denied.State == ExecutionState.Failed
                && denied.Diagnostic?.ErrorCode == BridgeErrorCode.PolicyDenied
                && denied.CleanupRequired
                && handler.ExecuteCalls == 0,
            "cleanup-only session dispatched another effectful command");
        await SendAsync(client, close, timeout.Token);
        Require((await ReceiveAsync(client, timeout.Token)).State == ExecutionState.Succeeded, "cleanup close failed");
        await server.WaitAsync(TimeSpan.FromSeconds(5));
    }

    private static void NativeProbeRejectsInvalidProcess()
    {
        var probe = new NativeHancomModalProbe();
        try
        {
            _ = probe.Capture(0);
        }
        catch (ArgumentOutOfRangeException)
        {
            return;
        }

        throw new InvalidOperationException("native probe accepted an invalid process id");
    }

    private static async Task<int> ActualEventDeliveryAsync()
    {
        if (Environment.Is64BitProcess || ProcessCount() != 0)
        {
            Console.Error.WriteLine("HANCOM_EVENT_ATTACH_PREFLIGHT_FAILED");
            return 2;
        }

        await using var loop = new StaMessageLoop("p10-07-actual-event-delivery");
        var signalCount = await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession();
                IHancomAutomationDocument? blank = null;
                var count = 0;
                try
                {
                    session.Start(Profile(), context);
                    blank = CreateActualBlankDocument(session);
                    PumpForActualEvent(context);
                    count += session.DrainAutomationSignals(context).Count;
                    blank.CloseWithoutSaving();
                    blank.Dispose();
                    blank = null;
                    PumpForActualEvent(context);
                    count += session.DrainAutomationSignals(context).Count;
                }
                finally
                {
                    if (blank is not null)
                    {
                        try
                        {
                            blank.CloseWithoutSaving();
                        }
                        catch
                        {
                            // The session-owned process is still terminated below.
                        }

                        blank.Dispose();
                    }

                    session.Shutdown(context);
                    count += session.DrainAutomationSignals(context).Count;
                }

                return count;
            },
            CancellationToken.None);
        await Task.Delay(500);
        Require(signalCount > 0, "actual event sink received no automation signals");
        Require(ProcessCount() == 0, "actual event attach left an Hwp process");
        Console.WriteLine(
            "HANCOM_EVENT_DELIVERY_PASS target=2020 "
            + "interface=f04a09a0-f319-40d5-88ca-ca439cc6820c "
            + $"signals={signalCount} remaining=0");
        return 0;
    }

    private static IHancomAutomationDocument CreateActualBlankDocument(HancomSession session)
    {
        var leaseField = typeof(HancomSession).GetField(
            "lease",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
            ?? throw new InvalidOperationException("HancomSession lease field was unavailable.");
        var runtime = (leaseField.GetValue(session) as HancomRuntimeLease)?.Automation
            as ComHancomAutomationRuntime
            ?? throw new InvalidOperationException("Actual COM runtime was unavailable.");
        var instanceField = typeof(ComHancomAutomationRuntime).GetField(
            "instance",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
            ?? throw new InvalidOperationException("COM runtime instance field was unavailable.");
        dynamic automation = instanceField.GetValue(runtime)
            ?? throw new InvalidOperationException("Actual COM instance was unavailable.");
        object? documents = null;
        object? document = null;
        try
        {
            documents = automation.XHwpDocuments;
            dynamic collection = documents;
            document = collection.Add(false);
            return new ComHancomAutomationDocument(documents, document);
        }
        catch
        {
            ComHancomAutomationRuntime.ReleaseComObject(document);
            ComHancomAutomationRuntime.ReleaseComObject(documents);
            throw;
        }
    }

    private static void PumpForActualEvent(StaExecutionContext context)
    {
        for (var attempt = 0; attempt < 50; attempt++)
        {
            context.PumpPendingMessages();
            Thread.Sleep(10);
        }
    }

    private static int ActualModalProbe(string rawProcessId)
    {
        Volatile.Write(ref actualStage, "parse-process-id");
        if (Environment.Is64BitProcess
            || !int.TryParse(rawProcessId, System.Globalization.NumberStyles.None,
                System.Globalization.CultureInfo.InvariantCulture, out var processId)
            || processId <= 0)
        {
            Console.Error.WriteLine("HANCOM_MODAL_PROBE_PREFLIGHT_FAILED");
            return 2;
        }

        Volatile.Write(ref actualStage, "verify-process-identity");
        using var process = System.Diagnostics.Process.GetProcessById(processId);
        using var current = System.Diagnostics.Process.GetCurrentProcess();
        var executable = process.MainModule?.FileName
            ?? throw new InvalidOperationException("Actual modal process executable was unavailable.");
        using var executableStream = new FileStream(
            executable,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read);
        var executableSha256 = Convert.ToHexStringLower(SHA256.HashData(executableStream));
        Require(
            string.Equals(process.ProcessName, "Hwp", StringComparison.OrdinalIgnoreCase)
                && process.SessionId == current.SessionId
                && string.Equals(executableSha256, ExecutableSha256, StringComparison.Ordinal),
            "actual modal process identity mismatch");

        Volatile.Write(ref actualStage, "capture-observations");
        var probe = new NativeHancomModalProbe();
        var observations = probe.Capture(processId);
        if (observations.Count == 0)
        {
            foreach (var item in probe.CaptureSafeWindowInventory(processId))
            {
                Console.WriteLine(
                    "HANCOM_WINDOW_INVENTORY "
                    + $"class={item.WindowClass} title_sha256={item.WindowTitleSha256} "
                    + $"title_length={item.WindowTitleLength} width={item.Width} height={item.Height} "
                    + $"top_level={item.IsTopLevel.ToString().ToLowerInvariant()} "
                    + $"visible={item.IsVisible.ToString().ToLowerInvariant()} "
                    + $"enabled={item.IsEnabled.ToString().ToLowerInvariant()} "
                    + $"parent_depth={item.ParentDepth} style=0x{item.Style:x} ex_style=0x{item.ExtendedStyle:x}");
            }
        }

        Require(observations.Count is >= 1 and <= 64, "actual modal was not detected");
        Volatile.Write(ref actualStage, "classify-observations");
        using var watchdog = new HancomModalWatchdogSession(
            processId,
            Policy([]),
            probe,
            TimeProvider.System,
            TimeSpan.FromSeconds(5),
            maximumIncidents: 64);
        var incidents = watchdog.DrainIncidents();
        Require(
            incidents.Count == observations.Count
                && incidents.All(value =>
                    value.Disposition == HancomModalDisposition.UnknownBlocked
                    && value.ErrorCode == BridgeErrorCode.UnknownModal
                    && value.EventType == StaEventType.UnknownModal
                    && value.RequiresRecycle
                    && !value.AutoResponseAttempted
                    && !value.RawDialogTextLogged),
            "actual modal was not classified fail-closed");

        Volatile.Write(ref actualStage, "emit-safe-evidence");
        foreach (var observation in observations)
        {
            Console.WriteLine(
                "HANCOM_MODAL_FINGERPRINT "
                + $"class_sha256={observation.WindowClassSha256} "
                + $"title_sha256={observation.WindowTitleSha256} "
                + $"controls_sha256={observation.ControlStructureSha256} "
                + $"width={observation.Width} height={observation.Height} "
                + $"screenshot_state={observation.Screenshot.State.ToString().ToLowerInvariant()} "
                + $"pixel_sha256={observation.Screenshot.PixelSha256}");
        }

        Console.WriteLine(
            $"HANCOM_MODAL_PROBE_PASS target=2020 count={observations.Count} "
            + "classification=unknown_fail_closed auto_response=false raw_dialog_text=false screenshot_persisted=false");
        return 0;
    }

    private static IHancomModalWatchdogSession CreateWatchdog(
        IHancomModalProbe probe,
        IHancomModalPolicyResolver resolver) =>
        new HancomModalWatchdogFactory(probe, resolver, TimeProvider.System).Start(
            101,
            Profile(),
            FailClosedHancomModalPolicyResolver.PolicyId);

    private static HancomModalPolicy Policy(IReadOnlyList<HancomExpectedDialogFingerprint> expected) =>
        new(
            FailClosedHancomModalPolicyResolver.PolicyId,
            HancomTargetProfile.CurrentProfileId,
            "11.0.0.9136",
            expected);

    private static HancomDialogObservation Observation(char classHash, char titleHash, char controlHash, bool captured) =>
        new(
            101,
            Digest(classHash),
            Digest(titleHash),
            Digest(controlHash),
            640,
            320,
            captured
                ? HancomScreenshotMetadata.Captured(640, 320, Digest('9'))
                : HancomScreenshotMetadata.Unavailable(640, 320, "fixture-capture-unavailable"));

    private static HancomModalIncident UnknownIncident() =>
        new(
            HancomModalDisposition.UnknownBlocked,
            BridgeErrorCode.UnknownModal,
            StaEventType.UnknownModal,
            Digest('7'),
            ScreenshotCaptured: true,
            AutoResponseAttempted: false,
            RawDialogTextLogged: false,
            RequiresRecycle: true);

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
                ModalPolicyId = FailClosedHancomModalPolicyResolver.PolicyId,
            },
        };
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
            DeadlineUnixMs = checked((ulong)DateTimeOffset.UtcNow.AddSeconds(10).ToUnixTimeMilliseconds()),
            TraceId = TraceId,
        };

    private static StagedArtifactRef Staged(string handle) =>
        new()
        {
            Artifact = new ArtifactRef
            {
                ArtifactId = $"p10-07-{handle}",
                Sha256 = Digest('a'),
                SizeBytes = 5,
            },
            SandboxHandle = handle,
            ReadOnly = true,
        };

    private static async Task SendAsync(
        Stream stream,
        StaCommandEnvelope command,
        CancellationToken cancellationToken) =>
        await StaPipeFraming.WriteMessageAsync(stream, command, cancellationToken);

    private static async Task<StaCommandReceipt> ReceiveAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        var frame = await StaPipeFraming.ReadFrameAsync(stream, cancellationToken)
            ?? throw new InvalidOperationException("worker closed before a receipt");
        return StaCommandReceipt.Parser.ParseFrom(frame);
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

    private static bool IsDigest(string value) =>
        value.Length == 64 && value.All(character => character is >= '0' and <= '9' or >= 'a' and <= 'f');

    private static string SafeFailureCategory(Exception error) => error.Message switch
    {
        "Modal bounds were outside the capture policy." => "modal_bounds_outside_policy",
        "Modal bounds were unavailable." => "modal_bounds_unavailable",
        "Modal control enumeration failed." => "modal_control_enumeration_failed",
        "Modal control structure was unbounded." => "modal_control_structure_unbounded",
        "Process top-level window set was unbounded." => "top_level_window_set_unbounded",
        "Process window inventory was unbounded." => "window_inventory_unbounded",
        "Top-level window enumeration failed." => "top_level_window_enumeration_failed",
        "Window class was unavailable or unbounded." => "window_class_unavailable",
        "Window inventory bounds were unavailable." => "inventory_bounds_unavailable",
        "Window inventory parent chain was unbounded." => "inventory_parent_chain_unbounded",
        "Window inventory title length was unbounded." => "inventory_title_length_unbounded",
        "Window title changed while being read." => "window_title_changed",
        "Window title was unbounded." => "window_title_unbounded",
        _ => "unclassified",
    };

    private static string Digest(char value) => new(value, 64);

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void RequireLifecycle(Action action, HancomLifecycleError expected)
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

    private sealed class FixedProbe(IReadOnlyList<HancomDialogObservation> observations) : IHancomModalProbe
    {
        public IReadOnlyList<HancomDialogObservation> Capture(int processId)
        {
            _ = processId;
            return observations;
        }
    }

    private sealed class SwitchProbe : IHancomModalProbe
    {
        internal bool Enabled { get; set; }

        public IReadOnlyList<HancomDialogObservation> Capture(int processId)
        {
            _ = processId;
            return Enabled ? [Observation('a', 'b', 'c', captured: true)] : [];
        }
    }

    private sealed class ThrowingProbe : IHancomModalProbe
    {
        public IReadOnlyList<HancomDialogObservation> Capture(int processId)
        {
            _ = processId;
            throw new InvalidOperationException("synthetic probe failure");
        }
    }

    private sealed class NullProbe : IHancomModalProbe
    {
        public IReadOnlyList<HancomDialogObservation> Capture(int processId)
        {
            _ = processId;
            return null!;
        }
    }

    private sealed class FixedPolicyResolver(HancomModalPolicy policy) : IHancomModalPolicyResolver
    {
        public HancomModalPolicy Resolve(HancomTargetProfile profile, string modalPolicyId)
        {
            _ = profile;
            _ = modalPolicyId;
            return policy;
        }
    }

    private sealed class NullPolicyResolver : IHancomModalPolicyResolver
    {
        public HancomModalPolicy Resolve(HancomTargetProfile profile, string modalPolicyId)
        {
            _ = profile;
            _ = modalPolicyId;
            return null!;
        }
    }

    private sealed class FixedWatchdogFactory(HancomModalIncident incident) : IHancomModalWatchdogFactory
    {
        public IHancomModalWatchdogSession Start(
            int processId,
            HancomTargetProfile profile,
            string modalPolicyId)
        {
            _ = processId;
            _ = profile;
            _ = modalPolicyId;
            return new FixedWatchdogSession(incident);
        }
    }

    private sealed class FixedWatchdogSession(HancomModalIncident incident) : IHancomModalWatchdogSession
    {
        private HancomModalIncident? current = incident;

        public void ScanNow()
        {
        }

        public IReadOnlyList<HancomModalIncident> DrainIncidents()
        {
            var value = Interlocked.Exchange(ref current, null);
            return value is null ? [] : [value];
        }

        public void Dispose()
        {
        }
    }

    private sealed class ThrowingWatchdogFactory : IHancomModalWatchdogFactory
    {
        public IHancomModalWatchdogSession Start(
            int processId,
            HancomTargetProfile profile,
            string modalPolicyId)
        {
            _ = processId;
            _ = profile;
            _ = modalPolicyId;
            return new ThrowingWatchdogSession();
        }

        private sealed class ThrowingWatchdogSession : IHancomModalWatchdogSession
        {
            public void ScanNow() =>
                throw new HancomLifecycleException(HancomLifecycleError.ModalWatchdogOverflow);

            public IReadOnlyList<HancomModalIncident> DrainIncidents() => [];

            public void Dispose()
            {
            }
        }
    }

    private sealed class FakeRuntimeFactory : IHancomRuntimeFactory
    {
        internal List<string> Events { get; } = [];

        public HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context)
        {
            _ = profile;
            _ = context;
            Events.Add("create");
            return new HancomRuntimeLease(new FakeRuntime(Events), new FakeProcess(Events));
        }

        private sealed class FakeRuntime(List<string> events) : IHancomAutomationRuntime
        {
            public string Version => "11, 0, 0, 9136";

            public bool RegisterFilePathSecurityModule(string registrationName)
            {
                _ = registrationName;
                return true;
            }

            public IHancomAutomationDocument Open(HancomApprovedDocument input)
            {
                _ = input;
                throw new InvalidOperationException("open must not be called");
            }

            public bool ExecuteAction(HancomBoundAction invocation)
            {
                _ = invocation;
                throw new InvalidOperationException("action must not be called");
            }

            public void Quit() => events.Add("quit");

            public void Dispose()
            {
            }
        }

        private sealed class FakeProcess(List<string> events) : IHancomOwnedProcess
        {
            public int ProcessId => 901;

            public void EnsureStopped(StaExecutionContext context)
            {
                _ = context;
                events.Add("process-stop");
            }

            public void Dispose()
            {
            }
        }
    }

    private sealed class CleanupOnlyHandler : IStaCommandHandler, IStaCommandHandlerCleanup
    {
        internal int ExecuteCalls { get; private set; }

        public StaCommandReceipt Execute(StaCommandEnvelope command, StaExecutionContext context)
        {
            _ = context;
            return command.CommandCase switch
            {
                StaCommandEnvelope.CommandOneofCase.StartSession =>
                    StaWorkerServer.CreateSuccessReceipt(command),
                StaCommandEnvelope.CommandOneofCase.OpenDocument =>
                    StaWorkerServer.CreateFailureReceipt(
                        command,
                        ExecutionState.Failed,
                        BridgeErrorCode.UnknownModal,
                        "fixture-modal",
                        effectUnknown: false,
                        cleanupRequired: true),
                StaCommandEnvelope.CommandOneofCase.ExecutePlan => ExecuteUnexpected(command),
                StaCommandEnvelope.CommandOneofCase.CloseSession =>
                    StaWorkerServer.CreateSuccessReceipt(command),
                _ => throw new InvalidOperationException("unexpected command"),
            };
        }

        public void Cleanup(StaExecutionContext context)
        {
            _ = context;
        }

        private StaCommandReceipt ExecuteUnexpected(StaCommandEnvelope command)
        {
            ExecuteCalls++;
            return StaWorkerServer.CreateSuccessReceipt(command);
        }
    }
}
