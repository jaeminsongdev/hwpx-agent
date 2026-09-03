using System.Security.Cryptography;
using System.Text.Json;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.SecuritySmoke;

internal static class Program
{
    private const string ExecutionId = "a0000000-0000-4000-8000-000000000001";
    private const string SessionId = "a0000000-0000-4000-8000-000000000002";
    private const string TraceId = "a0000000-0000-4000-8000-000000000003";
    private const string ProfileId = HancomTargetProfile.CurrentProfileId;
    private const string ModuleName = "FilePathCheckerModuleExample";
    private const string Handle = "approved_input";
    private const string ArtifactId = "p10-05-approved-input";
    private const ulong Fence = 53;
    private const string ExecutableSha256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
    private static readonly DateTimeOffset Now = new(2026, 9, 3, 14, 0, 0, TimeSpan.Zero);

    [STAThread]
    public static async Task<int> Main()
    {
        var stage = "allowed-lease";
        try
        {
            await AllowedLeasePinsModuleAndGuardsInputAsync();
            stage = "handler-order";
            await HandlerRegistersBeforeOpenAsync();
            stage = "command-mismatch";
            await CommandMismatchConsumesLeaseAsync();
            stage = "lease-expiry";
            ExpiredAndOverlongLeasesFailClosed();
            stage = "malformed-lease";
            MalformedUnknownAndMarkerDriftFailClosed();
            stage = "writable-input";
            await WritableInputFailsBeforeOpenAsync();
            stage = "module-pin";
            await ModuleHashAndArchitectureFailClosedAsync();
            stage = "registration-failure";
            await RegistrationFailureIsPolicyDeniedAndCleanedAsync();
            stage = "lease-replay";
            await SingleUseLeaseRejectsReplayAsync();
            stage = "close-failure";
            await CloseFailureReleasesInputGuardAsync();
            Console.WriteLine("Windows P10-05 security adapter allowed/denied smoke passed (10/10)");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(
                $"HANCOM_SECURITY_SMOKE_FAILED stage={stage} type={error.GetType().Name}");
            return 2;
        }
    }

    private static async Task AllowedLeasePinsModuleAndGuardsInputAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory
        {
            OnRegister = () => RequireThrows<IOException>(
                () =>
                {
                    using var denied = new FileStream(
                        fixture.ModulePath,
                        FileMode.Open,
                        FileAccess.Write,
                        FileShare.Read);
                }),
        };
        await using var loop = new StaMessageLoop("p10-05-allowed");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                ((IHancomSessionSecurity)adapter).Apply(StartCommand().StartSession, session, context);
                Require(session.FilePathSecurityEnabled, "security module was not enabled");
                using var approved = ((IHancomApprovedDocumentResolver)adapter).Resolve(
                    OpenCommand().OpenDocument,
                    context);
                approved.ValidateIntegrity();
                File.SetAttributes(fixture.InputPath, FileAttributes.Normal);
                RequireThrows<IOException>(
                    () =>
                    {
                        using var denied = new FileStream(
                            fixture.InputPath,
                            FileMode.Open,
                            FileAccess.Write,
                            FileShare.Read);
                    });
                File.SetAttributes(fixture.InputPath, FileAttributes.ReadOnly);
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Events.SequenceEqual(["create", "register-security", "quit", "process-stop"]), "allowed lifecycle order drifted");
        fixture.RequireInputUnchanged();
    }

    private static async Task HandlerRegistersBeforeOpenAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            adapter,
            adapter,
            new FixedTimeProvider(Now));
        await using var loop = new StaMessageLoop("p10-05-handler");
        await loop.InvokeAsync(
            context =>
            {
                var start = handler.Execute(StartCommand(), context);
                var open = handler.Execute(OpenCommand(), context);
                var close = handler.Execute(CloseCommand(), context);
                Require(start.State == ExecutionState.Succeeded, "secured start failed");
                Require(open.State == ExecutionState.Succeeded, "secured open failed");
                Require(close.State == ExecutionState.Succeeded, "secured close failed");
                return true;
            },
            CancellationToken.None);
        Require(
            factory.Events.SequenceEqual(
                ["create", "register-security", "open", "document-close", "quit", "process-stop"]),
            "security registration did not precede open");
        fixture.RequireInputUnchanged();
    }

    private static async Task CommandMismatchConsumesLeaseAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-05-mismatch");
        await loop.InvokeAsync(
            context =>
            {
                var session = StartSecuredSession(factory, adapter, context);
                var mismatched = OpenCommand();
                mismatched.OpenDocument.Input.Artifact.Sha256 = Digest('f');
                RequireLifecycle(
                    () => ((IHancomApprovedDocumentResolver)adapter).Resolve(
                        mismatched.OpenDocument,
                        context),
                    HancomLifecycleError.SecurityPolicyMismatch);
                RequireLifecycle(
                    () => ((IHancomApprovedDocumentResolver)adapter).Resolve(
                        OpenCommand().OpenDocument,
                        context),
                    HancomLifecycleError.SecurityLeaseConsumed);
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
    }

    private static void ExpiredAndOverlongLeasesFailClosed()
    {
        using (var expired = Fixture.Create(expiresAt: Now.AddMilliseconds(-1)))
        {
            RequireLifecycle(() => expired.LoadAdapter(), HancomLifecycleError.SecurityLeaseExpired);
        }

        using var overlong = Fixture.Create(expiresAt: Now.AddMinutes(31));
        RequireLifecycle(() => overlong.LoadAdapter(), HancomLifecycleError.SecurityLeaseInvalid);
    }

    private static void MalformedUnknownAndMarkerDriftFailClosed()
    {
        using (var unknown = Fixture.Create(extraLeaseProperty: true))
        {
            RequireLifecycle(() => unknown.LoadAdapter(), HancomLifecycleError.SecurityLeaseInvalid);
        }

        using var marker = Fixture.Create();
        File.WriteAllText(marker.MarkerPath, "a0000000-0000-4000-8000-000000000099");
        RequireLifecycle(() => marker.LoadAdapter(), HancomLifecycleError.SecurityLeaseInvalid);
    }

    private static async Task WritableInputFailsBeforeOpenAsync()
    {
        using var fixture = Fixture.Create(readOnlyInput: false);
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-05-writable");
        await loop.InvokeAsync(
            context =>
            {
                var session = StartSecuredSession(factory, adapter, context);
                RequireLifecycle(
                    () => ((IHancomApprovedDocumentResolver)adapter).Resolve(
                        OpenCommand().OpenDocument,
                        context),
                    HancomLifecycleError.InputRejected);
                Require(!factory.Events.Contains("open"), "writable input reached automation open");
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
    }

    private static async Task ModuleHashAndArchitectureFailClosedAsync()
    {
        using (var badHash = Fixture.Create())
        {
            var adapter = badHash.LoadAdapter(modulePathOverride: badHash.ModulePath, moduleHashOverride: Digest('b'));
            await RequireApplyFailureAsync(adapter, HancomLifecycleError.SecurityModuleInvalid);
        }

        using (var relative = Fixture.Create())
        {
            var adapter = relative.LoadAdapter(modulePathOverride: "security_module.dll");
            await RequireApplyFailureAsync(adapter, HancomLifecycleError.SecurityModuleInvalid);
        }

        using var wrongMachine = Fixture.Create(moduleMachine: 0x8664);
        var wrongAdapter = wrongMachine.LoadAdapter();
        await RequireApplyFailureAsync(wrongAdapter, HancomLifecycleError.SecurityModuleInvalid);
    }

    private static async Task RegistrationFailureIsPolicyDeniedAndCleanedAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory { RegistrationAccepted = false };
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            adapter,
            adapter,
            new FixedTimeProvider(Now));
        await using var loop = new StaMessageLoop("p10-05-register-false");
        await loop.InvokeAsync(
            context =>
            {
                var receipt = handler.Execute(StartCommand(), context);
                Require(receipt.State == ExecutionState.Failed, "registration false was not terminal");
                Require(receipt.Diagnostic?.ErrorCode == BridgeErrorCode.PolicyDenied, "registration false error drifted");
                handler.Cleanup(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Events.Contains("quit") && factory.Events.Contains("process-stop"), "registration failure leaked owner");
    }

    private static async Task SingleUseLeaseRejectsReplayAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-05-replay");
        await loop.InvokeAsync(
            context =>
            {
                var session = StartSecuredSession(factory, adapter, context);
                using var approved = ((IHancomApprovedDocumentResolver)adapter).Resolve(
                    OpenCommand().OpenDocument,
                    context);
                RequireLifecycle(
                    () => ((IHancomApprovedDocumentResolver)adapter).Resolve(
                        OpenCommand().OpenDocument,
                        context),
                    HancomLifecycleError.SecurityLeaseConsumed);
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
    }

    private static async Task CloseFailureReleasesInputGuardAsync()
    {
        using var fixture = Fixture.Create();
        var adapter = fixture.LoadAdapter();
        var factory = new FakeFactory { CloseFails = true };
        await using var loop = new StaMessageLoop("p10-05-close-failure");
        await loop.InvokeAsync(
            context =>
            {
                var session = StartSecuredSession(factory, adapter, context);
                var approved = ((IHancomApprovedDocumentResolver)adapter).Resolve(
                    OpenCommand().OpenDocument,
                    context);
                session.Open(approved, context);
                RequireLifecycle(
                    () => session.CloseDocument(context),
                    HancomLifecycleError.CloseFailed);
                File.SetAttributes(fixture.InputPath, FileAttributes.Normal);
                using (var writable = new FileStream(
                    fixture.InputPath,
                    FileMode.Open,
                    FileAccess.Write,
                    FileShare.Read))
                {
                }

                File.SetAttributes(fixture.InputPath, FileAttributes.ReadOnly);
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        fixture.RequireInputUnchanged();
    }

    private static async Task RequireApplyFailureAsync(
        HancomSecurityAdapter adapter,
        HancomLifecycleError expected)
    {
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-05-module-failure");
        await loop.InvokeAsync(
            context =>
            {
                var session = new HancomSession(factory);
                session.Start(Profile(), context);
                RequireLifecycle(
                    () => ((IHancomSessionSecurity)adapter).Apply(
                        StartCommand().StartSession,
                        session,
                        context),
                    expected);
                Require(!factory.Events.Contains("register-security"), "invalid module reached RegisterModule");
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
    }

    private static HancomSession StartSecuredSession(
        FakeFactory factory,
        HancomSecurityAdapter adapter,
        StaExecutionContext context)
    {
        var session = new HancomSession(factory);
        session.Start(Profile(), context);
        ((IHancomSessionSecurity)adapter).Apply(StartCommand().StartSession, session, context);
        return session;
    }

    private static HancomTargetProfile Profile() =>
        new(ProfileId, HancomTargetProfile.CurrentProgId, "11.0.0.9136", "ko-KR", "x86", ExecutableSha256);

    private static StaCommandEnvelope StartCommand()
    {
        var command = BaseCommand("a1000000-0000-4000-8000-000000000001");
        command.StartSession = new StaStartSessionCommand
        {
            TargetProfile = new TargetProfileIdentity
            {
                ProfileId = ProfileId,
                ProductBuild = "11.0.0.9136",
                Locale = "ko-KR",
                ProcessArchitecture = "x86",
                ExecutableSha256 = ExecutableSha256,
                EnvironmentDigest = Digest('e'),
            },
            CapabilityRegistrySha256 = Digest('c'),
            SecurityPolicy = new SecurityPolicy
            {
                FileAccessPolicyId = HancomSecurityAdapter.FileAccessPolicyId,
                ModalPolicyId = "modal.fail_closed",
            },
        };
        return command;
    }

    private static StaCommandEnvelope OpenCommand()
    {
        var command = BaseCommand("a1000000-0000-4000-8000-000000000002");
        command.OpenDocument = new StaOpenDocumentCommand
        {
            Input = new StagedArtifactRef
            {
                Artifact = new ArtifactRef
                {
                    ArtifactId = ArtifactId,
                    Sha256 = InputSha256,
                    SizeBytes = (ulong)InputBytes.Length,
                },
                SandboxHandle = Handle,
                ReadOnly = true,
            },
            OpenPolicyId = HancomSecurityAdapter.OpenPolicyId,
        };
        return command;
    }

    private static StaCommandEnvelope CloseCommand()
    {
        var command = BaseCommand("a1000000-0000-4000-8000-000000000003");
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
            DeadlineUnixMs = (ulong)Now.AddMinutes(1).ToUnixTimeMilliseconds(),
            TraceId = TraceId,
        };

    private static readonly byte[] InputBytes = "synthetic-p10-05-hwpx-input"u8.ToArray();
    private static readonly string InputSha256 = Sha256(InputBytes);

    private static string Digest(char value) => new(value, 64);

    private static string Sha256(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));

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

    private static void RequireThrows<TException>(Action action)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException)
        {
            return;
        }

        throw new InvalidOperationException($"Expected {typeof(TException).Name}.");
    }

    private sealed class FixedTimeProvider(DateTimeOffset now) : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => now;
    }

    private sealed class FakeRegistry(
        string modulePath,
        string moduleHashOverride) : IHancomSecurityModuleRegistry
    {
        public HancomSecurityModuleRegistration Resolve(
            string registrationName,
            string expectedSha256) =>
            RegistryHancomSecurityModuleRegistry.ValidateModuleFile(
                registrationName,
                modulePath,
                moduleHashOverride.Length == 0 ? expectedSha256 : moduleHashOverride);
    }

    private sealed class FakeFactory : IHancomRuntimeFactory
    {
        internal List<string> Events { get; } = [];

        internal bool RegistrationAccepted { get; init; } = true;

        internal bool CloseFails { get; init; }

        internal Action? OnRegister { get; init; }

        public HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context)
        {
            Events.Add("create");
            return new HancomRuntimeLease(new FakeRuntime(this), new FakeProcess(this));
        }

        private sealed class FakeRuntime(FakeFactory owner) : IHancomAutomationRuntime
        {
            public string Version => "11, 0, 0, 9136";

            public bool RegisterFilePathSecurityModule(string registrationName)
            {
                owner.Events.Add("register-security");
                owner.OnRegister?.Invoke();
                return owner.RegistrationAccepted;
            }

            public IHancomAutomationDocument Open(HancomApprovedDocument input)
            {
                owner.Events.Add("open");
                input.ValidateIntegrity();
                return new FakeDocument(owner);
            }

            public bool ExecuteAction(HancomBoundAction invocation) => true;

            public void Quit() => owner.Events.Add("quit");

            public void Dispose()
            {
            }
        }

        private sealed class FakeDocument(FakeFactory owner) : IHancomAutomationDocument
        {
            public void CloseWithoutSaving()
            {
                owner.Events.Add("document-close");
                if (owner.CloseFails)
                {
                    throw new InvalidOperationException("synthetic close failure");
                }
            }

            public void Dispose()
            {
            }
        }

        private sealed class FakeProcess(FakeFactory owner) : IHancomOwnedProcess
        {
            public int ProcessId => 805;

            public void EnsureStopped(StaExecutionContext context) => owner.Events.Add("process-stop");

            public void Dispose()
            {
            }
        }
    }

    private sealed class Fixture : IDisposable
    {
        private Fixture(
            string root,
            string inputPath,
            string markerPath,
            string leasePath,
            string modulePath,
            string moduleSha256)
        {
            Root = root;
            InputPath = inputPath;
            MarkerPath = markerPath;
            LeasePath = leasePath;
            ModulePath = modulePath;
            ModuleSha256 = moduleSha256;
        }

        internal string Root { get; }

        internal string InputPath { get; }

        internal string MarkerPath { get; }

        internal string LeasePath { get; }

        internal string ModulePath { get; }

        internal string ModuleSha256 { get; }

        internal static Fixture Create(
            bool readOnlyInput = true,
            ushort moduleMachine = 0x014c,
            DateTimeOffset? expiresAt = null,
            bool extraLeaseProperty = false)
        {
            var root = Path.Combine(Path.GetTempPath(), $"hwpx-agent-p10-05-{Guid.NewGuid():N}");
            Directory.CreateDirectory(root);
            var marker = Path.Combine(root, ".hwpx-agent-sandbox");
            File.WriteAllText(marker, ExecutionId);
            var input = Path.Combine(root, HancomSecurityAdapter.ApprovedInputFileName);
            File.WriteAllBytes(input, InputBytes);
            if (readOnlyInput)
            {
                File.SetAttributes(input, FileAttributes.ReadOnly);
            }

            var module = Path.Combine(root, "security_module.dll");
            var moduleBytes = MinimalPe(moduleMachine);
            File.WriteAllBytes(module, moduleBytes);
            var moduleSha = Sha256(moduleBytes);
            var lease = Path.Combine(root, HancomSecurityAdapter.LeaseFileName);
            var values = new Dictionary<string, object?>
            {
                ["schema_version"] = HancomSecurityAdapter.SchemaVersion,
                ["execution_id"] = ExecutionId,
                ["session_id"] = SessionId,
                ["fencing_token"] = Fence,
                ["target_profile_id"] = ProfileId,
                ["expires_at_unix_ms"] = (expiresAt ?? Now.AddMinutes(5)).ToUnixTimeMilliseconds(),
                ["file_access_policy_id"] = HancomSecurityAdapter.FileAccessPolicyId,
                ["open_policy_id"] = HancomSecurityAdapter.OpenPolicyId,
                ["sandbox_handle"] = Handle,
                ["artifact_id"] = ArtifactId,
                ["input_sha256"] = InputSha256,
                ["input_size_bytes"] = InputBytes.Length,
                ["security_module_registration_name"] = ModuleName,
                ["security_module_sha256"] = moduleSha,
            };
            if (extraLeaseProperty)
            {
                values["unexpected"] = true;
            }

            File.WriteAllBytes(lease, JsonSerializer.SerializeToUtf8Bytes(values));
            File.SetAttributes(lease, FileAttributes.ReadOnly);
            return new Fixture(root, input, marker, lease, module, moduleSha);
        }

        internal HancomSecurityAdapter LoadAdapter(
            string? modulePathOverride = null,
            string? moduleHashOverride = null) =>
            HancomSecurityAdapter.Load(
                LeasePath,
                SessionId,
                Fence,
                ProfileId,
                new FakeRegistry(
                    modulePathOverride ?? ModulePath,
                    moduleHashOverride ?? string.Empty),
                new FixedTimeProvider(Now));

        internal void RequireInputUnchanged()
        {
            Require(
                string.Equals(HancomApprovedDocument.HashFile(InputPath), InputSha256, StringComparison.Ordinal),
                "input digest changed");
        }

        public void Dispose()
        {
            if (!Directory.Exists(Root))
            {
                return;
            }

            foreach (var file in Directory.EnumerateFiles(Root))
            {
                File.SetAttributes(file, FileAttributes.Normal);
            }

            Directory.Delete(Root, recursive: true);
        }

        private static byte[] MinimalPe(ushort machine)
        {
            var bytes = new byte[512];
            bytes[0] = 0x4d;
            bytes[1] = 0x5a;
            BitConverter.GetBytes(0x80).CopyTo(bytes, 0x3c);
            bytes[0x80] = 0x50;
            bytes[0x81] = 0x45;
            BitConverter.GetBytes(machine).CopyTo(bytes, 0x84);
            return bytes;
        }
    }
}
