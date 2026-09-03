using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsWorker;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.OpenSsl;
using Org.BouncyCastle.Security;
using Org.BouncyCastle.X509;

namespace HwpxAgent.WindowsWorker.BindingSmoke;

public static class Program
{
    private const string BundleId = "hancom.current2020.v1";
    private const string CapabilityRegistrySha256 =
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
    private const string ExecutableSha256 =
        "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
        TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
    };

    [STAThread]
    public static async Task<int> Main()
    {
        try
        {
            await ValidSignedTypedPlanExecutesAsync();
            await UnknownBindingStopsBeforeComAsync();
            await RawPublicCapabilityStopsBeforeComAsync();
            await UnknownArgumentStopsBeforeComAsync();
            await EnumAndRangeFailuresStopBeforeComAsync();
            await SignatureTamperStopsBeforeComAsync();
            await TargetMismatchStopsBeforeComAsync();
            await ArgumentDigestTamperStopsBeforeComAsync();
            await ActionFailureIsUnknownAndFaultsSessionAsync();
            ComRuntimeRejectsRuntimeIdentityDrift();
            await BundleEncodingAndParserFailuresStayTypedAsync();
            await DuplicateJsonStopsBeforeComAsync();
            await SecurityLeaseBindsHandlerAndRejectsReplayAsync();
            await PlanResolverLifecycleFailureReturnsReceiptAsync();
            Console.WriteLine(
                "Windows Hancom P10-06 signed binding and typed ParameterSet smoke passed (14/14)");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(
                $"HANCOM_BINDING_SMOKE_FAILED:{error.GetType().Name}:{error.Message}");
            return 2;
        }
    }

    private static async Task ValidSignedTypedPlanExecutesAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var plan = BuildPlan();
        var factory = new FakeFactory();
        var result = await ExecuteAsync(fixture, factory, material, plan);
        Require(result.OperationCount == 2, "operation count drifted");
        Require(factory.Invocations.Count == 2, "valid plan did not dispatch exactly twice");
        Require(factory.Invocations[0].Parameters.Count == 0, "no-parameter action was widened");
        var typed = factory.Invocations[1].Parameters.ToDictionary(
            value => value.ItemName,
            value => value.Value,
            StringComparer.Ordinal);
        Require(typed.Count == 4, "typed ParameterSet count drifted");
        Require(typed.Values.OfType<string>().Single() == "safe text", "text binding drifted");
        Require(typed.Values.OfType<bool>().Single(), "boolean binding drifted");
        Require(typed.Values.OfType<int>().Order().SequenceEqual([2, 20]), "numeric binding drifted");
        fixture.RequireUnchanged();
    }

    private static async Task UnknownBindingStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var plan = BuildPlan();
        PlanOperations(plan)[0]!["capability_id"] = "edit.unknown_synthetic";
        await RequireBindingFailureAsync(
            fixture,
            material,
            plan,
            HancomBindingError.UnknownBinding);
    }

    private static async Task RawPublicCapabilityStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var plan = BuildPlan();
        PlanOperations(plan)[0]!["capability_id"] = "haction.synthetic";
        await RequireBindingFailureAsync(
            fixture,
            material,
            plan,
            HancomBindingError.PlanInvalid);
    }

    private static async Task UnknownArgumentStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var plan = BuildPlan();
        OperationArguments(PlanOperations(plan)[1]!).Add(
            "unknown",
            Argument("integer", 1));
        await RequireBindingFailureAsync(
            fixture,
            material,
            plan,
            HancomBindingError.ArgumentInvalid);
    }

    private static async Task EnumAndRangeFailuresStopBeforeComAsync()
    {
        using var enumFixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var badEnum = BuildPlan();
        OperationArguments(PlanOperations(badEnum)[1]!)["mode"] = Argument("text", "forbidden");
        await RequireBindingFailureAsync(
            enumFixture,
            material,
            badEnum,
            HancomBindingError.ArgumentInvalid);

        using var rangeFixture = Fixture.Create();
        var badRange = BuildPlan();
        OperationArguments(PlanOperations(badRange)[1]!)["count"] = Argument("integer", 1_000);
        await RequireBindingFailureAsync(
            rangeFixture,
            material,
            badRange,
            HancomBindingError.ArgumentInvalid);
    }

    private static async Task SignatureTamperStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var envelope = JsonNode.Parse(material.Envelope)!.AsObject();
        var signature = Convert.FromBase64String(envelope["signature_base64"]!.GetValue<string>());
        signature[0] ^= 0x80;
        envelope["signature_base64"] = Convert.ToBase64String(signature);
        var tampered = JsonBytes(envelope);
        await RequireBindingFailureAsync(
            fixture,
            material with { Envelope = tampered },
            BuildPlan(),
            HancomBindingError.SignatureInvalid);
    }

    private static async Task TargetMismatchStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create(payloadMutation: payload =>
        {
            payload["target"]!.AsObject()["product_build"] = "11.0.0.9999";
        });
        await RequireBindingFailureAsync(
            fixture,
            material,
            BuildPlan(),
            HancomBindingError.TargetMismatch);
    }

    private static async Task ArgumentDigestTamperStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var plan = BuildPlan();
        var digest = OperationArguments(PlanOperations(plan)[1]!)["count"]!["value_sha256"]!.AsArray();
        digest[0] = 255;
        await RequireBindingFailureAsync(
            fixture,
            material,
            plan,
            HancomBindingError.PlanInvalid);
    }

    private static async Task ActionFailureIsUnknownAndFaultsSessionAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var factory = new FakeFactory { FailAtInvocation = 2 };
        await using var loop = new StaMessageLoop("p10-06-action-failure");
        await loop.InvokeAsync(
            context =>
            {
                var session = OpenSession(fixture, factory, context);
                using var approved = material.Approve(BuildPlan());
                try
                {
                    _ = new HancomBindingExecutor().Execute(
                        Command(material.Envelope),
                        approved,
                        session,
                        Profile(),
                        CapabilityRegistrySha256,
                        context);
                    throw new InvalidOperationException("action failure was accepted");
                }
                catch (HancomBindingException error)
                {
                    Require(error.Error == HancomBindingError.ActionFailed, "action error drifted");
                    Require(error.EffectUnknown, "dispatched COM failure was treated as known");
                    Require(session.State == HancomSessionState.Faulted, "failed action did not fault session");
                }

                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Invocations.Count == 2, "action failure dispatch count drifted");
        fixture.RequireUnchanged();
    }

    private static void ComRuntimeRejectsRuntimeIdentityDrift()
    {
        var invocation = new HancomBoundAction(
            "SyntheticAction",
            "SyntheticSet",
            [new HancomBoundParameter("Count", 5)]);

        var validSet = new DynamicParameterSet("SyntheticSet", ["Count"]);
        using (var runtime = CreateComRuntime(
            new DynamicAutomation(new DynamicActionCollection(
                new DynamicAction("SyntheticAction", "SyntheticSet", validSet)))))
        {
            Require(runtime.ExecuteAction(invocation), "valid runtime identity was rejected");
            Require(
                validSet.Values.TryGetValue("Count", out var value) && value is int count && count == 5,
                "typed runtime value was not set");
        }

        using (var runtime = CreateComRuntime(
            new DynamicAutomation(new DynamicActionCollection(
                new DynamicAction(
                    "SyntheticAction",
                    "UnexpectedSet",
                    new DynamicParameterSet("UnexpectedSet", ["Count"]))))))
        {
            Require(!runtime.ExecuteAction(invocation), "runtime SetID drift was accepted");
        }

        using (var runtime = CreateComRuntime(
            new DynamicAutomation(new DynamicActionCollection(
                new DynamicAction(
                    "SyntheticAction",
                    "SyntheticSet",
                    new DynamicParameterSet("SyntheticSet", []))))))
        {
            Require(!runtime.ExecuteAction(invocation), "unknown runtime item was created implicitly");
        }

        using (var runtime = CreateComRuntime(
            new DynamicAutomation(new DynamicActionCollection(action: null, runResult: false))))
        {
            Require(
                !runtime.ExecuteAction(new HancomBoundAction("SyntheticNoop", null, [])),
                "false Run result was accepted");
        }

        using (var runtime = CreateComRuntime(
            new DynamicAutomation(new DynamicActionCollection(
                new DynamicAction(
                    "SyntheticAction",
                    "SyntheticSet",
                    new DynamicParameterSet("SyntheticSet", ["Count"]),
                    executeResult: false)))))
        {
            Require(!runtime.ExecuteAction(invocation), "false Execute result was accepted");
        }
    }

    private static ComHancomAutomationRuntime CreateComRuntime(object automation) =>
        new(automation, NoOpHancomAutomationEventConnection.Instance);

    private static async Task DuplicateJsonStopsBeforeComAsync()
    {
        using var fixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var duplicate = Encoding.UTF8.GetBytes(
            "{\"schema_version\":\"hwpx-agent.operation-plan/v2\",\"schema_version\":\"hwpx-agent.operation-plan/v2\"}");
        await RequireBindingFailureAsync(
            fixture,
            material,
            duplicate,
            HancomBindingError.PlanInvalid);
    }

    private static async Task BundleEncodingAndParserFailuresStayTypedAsync()
    {
        using var duplicateFixture = Fixture.Create();
        var material = SignedMaterial.Create();
        var originalEnvelope = Encoding.UTF8.GetString(material.Envelope);
        var duplicateEnvelope = Encoding.UTF8.GetBytes(
            $"{{\"schema_version\":\"{HancomBindingExecutor.EnvelopeSchemaVersion}\"," +
            originalEnvelope[1..]);
        await RequireBindingFailureAsync(
            duplicateFixture,
            material with { Envelope = duplicateEnvelope },
            BuildPlan(),
            HancomBindingError.BundleInvalid);

        using var encodingFixture = Fixture.Create();
        var nonCanonical = JsonNode.Parse(material.Envelope)!.AsObject();
        var payloadBase64 = nonCanonical["payload_base64"]!.GetValue<string>();
        nonCanonical["payload_base64"] = payloadBase64.Insert(4, "\n");
        await RequireBindingFailureAsync(
            encodingFixture,
            material with { Envelope = JsonBytes(nonCanonical) },
            BuildPlan(),
            HancomBindingError.SignatureInvalid);

        using var keyFixture = Fixture.Create();
        var invalidKey = Encoding.ASCII.GetBytes("not-an-ed25519-public-key");
        var badKeyEnvelope = JsonNode.Parse(material.Envelope)!.AsObject();
        badKeyEnvelope["public_key_sha256"] = Hash(invalidKey);
        await RequireBindingFailureAsync(
            keyFixture,
            material with { Envelope = JsonBytes(badKeyEnvelope), PublicKey = invalidKey },
            BuildPlan(),
            HancomBindingError.SignatureInvalid);
    }

    private static async Task SecurityLeaseBindsHandlerAndRejectsReplayAsync()
    {
        using var fixture = BindingLeaseFixture.Create();
        var factory = new FakeFactory();
        var adapter = HancomSecurityAdapter.Load(
            fixture.LeasePath,
            fixture.ExecutionId,
            fixture.Fence,
            HancomTargetProfile.CurrentProfileId,
            new FakeSecurityRegistry(fixture.ModulePath),
            TimeProvider.System);
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            adapter,
            adapter,
            adapter,
            new HancomBindingExecutor(),
            TimeProvider.System);

        await using var loop = new StaMessageLoop("p10-06-binding-lease");
        await loop.InvokeAsync(
            context =>
            {
                var start = handler.Execute(fixture.StartCommand(), context);
                Require(start.State == ExecutionState.Succeeded, "binding handler start failed");
                var open = handler.Execute(fixture.OpenCommand(), context);
                Require(open.State == ExecutionState.Succeeded, "binding handler open failed");
                var execute = handler.Execute(fixture.ExecuteCommand(), context);
                Require(
                    execute.State == ExecutionState.Succeeded
                        && execute.Events.Count == 1
                        && execute.Events[0].EventType == StaEventType.PlanExecuted,
                    "binding handler execution failed");
                var replay = handler.Execute(fixture.ExecuteCommand(), context);
                Require(
                    replay.State == ExecutionState.Failed
                        && replay.Diagnostic?.ErrorCode == BridgeErrorCode.PolicyDenied
                        && !replay.Diagnostic.EffectUnknown,
                    "binding lease replay was not denied before COM");
                var close = handler.Execute(fixture.CloseCommand(), context);
                Require(close.State == ExecutionState.Succeeded, "binding handler close failed");
                return true;
            },
            CancellationToken.None);
        Require(factory.Invocations.Count == 2, "replay reached the automation runtime");
        fixture.RequireUnchanged();
    }

    private static async Task PlanResolverLifecycleFailureReturnsReceiptAsync()
    {
        using var fixture = Fixture.Create();
        var factory = new FakeFactory();
        var handler = new HancomLifecycleCommandHandler(
            () => new HancomSession(factory),
            new FixedDocumentResolver(fixture.Document),
            sessionSecurity: null,
            new ThrowingPlanResolver(HancomLifecycleError.SecurityLeaseExpired),
            new HancomBindingExecutor(),
            TimeProvider.System);

        await using var loop = new StaMessageLoop("p10-06-lifecycle-failure");
        await loop.InvokeAsync(
            context =>
            {
                var start = CreateEnvelope("74000000-0000-4000-8000-000000000001");
                start.StartSession = new StaStartSessionCommand
                {
                    TargetProfile = new TargetProfileIdentity
                    {
                        ProfileId = HancomTargetProfile.CurrentProfileId,
                        ProductBuild = "11.0.0.9136",
                        Locale = "ko-KR",
                        ProcessArchitecture = "x86",
                        ExecutableSha256 = ExecutableSha256,
                        EnvironmentDigest = new string('f', 64),
                    },
                    CapabilityRegistrySha256 = CapabilityRegistrySha256,
                    SecurityPolicy = new SecurityPolicy
                    {
                        FileAccessPolicyId = HancomSecurityAdapter.FileAccessPolicyId,
                        ModalPolicyId = "modal.fail_closed",
                    },
                };
                Require(handler.Execute(start, context).State == ExecutionState.Succeeded, "start failed");

                var open = CreateEnvelope("74000000-0000-4000-8000-000000000002");
                open.OpenDocument = new StaOpenDocumentCommand();
                Require(handler.Execute(open, context).State == ExecutionState.Succeeded, "open failed");

                var execute = CreateEnvelope("74000000-0000-4000-8000-000000000003");
                execute.ExecutePlan = new StaExecutePlanCommand();
                var receipt = handler.Execute(execute, context);
                Require(
                    receipt.State == ExecutionState.Failed
                        && receipt.Diagnostic?.ErrorCode == BridgeErrorCode.PolicyDenied
                        && !receipt.Diagnostic.EffectUnknown
                        && !receipt.CleanupRequired,
                    "plan resolver lifecycle failure escaped the typed receipt boundary");

                var close = CreateEnvelope("74000000-0000-4000-8000-000000000004");
                close.CloseSession = new StaCloseSessionCommand { DiscardUnsavedChanges = true };
                Require(handler.Execute(close, context).State == ExecutionState.Succeeded, "close failed");
                return true;
            },
            CancellationToken.None);
        Require(factory.Invocations.Count == 0, "failed resolver reached COM");
        fixture.RequireUnchanged();
    }

    private static StaCommandEnvelope CreateEnvelope(string commandId) => new()
    {
        ProtocolMajor = 1,
        ProtocolMinor = 0,
        SessionId = "75000000-0000-4000-8000-000000000001",
        CommandId = commandId,
        FencingToken = 75,
        DeadlineUnixMs = checked((ulong)DateTimeOffset.UtcNow.AddMinutes(1).ToUnixTimeMilliseconds()),
        TraceId = "76000000-0000-4000-8000-000000000001",
    };

    private static async Task<HancomBindingExecutionResult> ExecuteAsync(
        Fixture fixture,
        FakeFactory factory,
        SignedMaterial material,
        JsonObject plan)
    {
        HancomBindingExecutionResult? result = null;
        await using var loop = new StaMessageLoop("p10-06-valid");
        await loop.InvokeAsync(
            context =>
            {
                var session = OpenSession(fixture, factory, context);
                using var approved = material.Approve(plan);
                result = new HancomBindingExecutor().Execute(
                    Command(material.Envelope),
                    approved,
                    session,
                    Profile(),
                    CapabilityRegistrySha256,
                    context);
                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        return result ?? throw new InvalidOperationException("executor returned no result");
    }

    private static async Task RequireBindingFailureAsync(
        Fixture fixture,
        SignedMaterial material,
        JsonObject plan,
        HancomBindingError expected) =>
        await RequireBindingFailureAsync(fixture, material, JsonBytes(plan), expected);

    private static async Task RequireBindingFailureAsync(
        Fixture fixture,
        SignedMaterial material,
        byte[] plan,
        HancomBindingError expected)
    {
        var factory = new FakeFactory();
        await using var loop = new StaMessageLoop("p10-06-rejection");
        await loop.InvokeAsync(
            context =>
            {
                var session = OpenSession(fixture, factory, context);
                using var approved = material.Approve(plan);
                try
                {
                    _ = new HancomBindingExecutor().Execute(
                        Command(material.Envelope),
                        approved,
                        session,
                        Profile(),
                        CapabilityRegistrySha256,
                        context);
                    throw new InvalidOperationException("invalid binding input was accepted");
                }
                catch (HancomBindingException error)
                {
                    Require(error.Error == expected, $"binding rejection drifted: {error.Error}");
                    Require(!error.EffectUnknown, "pre-COM rejection became effect-unknown");
                }

                session.Shutdown(context);
                return true;
            },
            CancellationToken.None);
        Require(factory.Invocations.Count == 0, "rejected input reached COM");
        fixture.RequireUnchanged();
    }

    private static HancomSession OpenSession(
        Fixture fixture,
        FakeFactory factory,
        StaExecutionContext context)
    {
        var session = new HancomSession(factory);
        session.Start(Profile(), context);
        session.Open(fixture.Document, context);
        return session;
    }

    private static StaExecutePlanCommand Command(byte[] envelope) => new()
    {
        OperationPlan = new StagedArtifactRef
        {
            Artifact = new ArtifactRef
            {
                ArtifactId = "p10-06-operation-plan",
                Sha256 = new string('a', 64),
                SizeBytes = 1,
            },
            SandboxHandle = "plan_0001",
            ReadOnly = true,
        },
        BindingBundleId = BundleId,
        BindingBundleSha256 = Hash(envelope),
    };

    private static HancomTargetProfile Profile() => new(
        HancomTargetProfile.CurrentProfileId,
        HancomTargetProfile.CurrentProgId,
        "11.0.0.9136",
        "ko-KR",
        "x86",
        ExecutableSha256);

    private static JsonObject BuildPlan()
    {
        var operations = new JsonArray
        {
            Operation(
                "op-1",
                "edit.synthetic_noop",
                new JsonObject(),
                new JsonArray()),
            Operation(
                "op-2",
                "layout.synthetic_typed",
                new JsonObject
                {
                    ["count"] = Argument("integer", 10),
                    ["enabled"] = Argument("boolean", true),
                    ["label"] = Argument("text", "safe text"),
                    ["mode"] = Argument("text", "second"),
                },
                new JsonArray("op-1")),
        };
        return new JsonObject
        {
            ["schema_version"] = HancomBindingExecutor.OperationPlanSchemaVersion,
            ["plan_id"] = "plan-1",
            ["base_revision"] = "revision-1",
            ["base_graph_sha256"] = DigestArray(0x11),
            ["failure_policy"] = "atomic",
            ["operations"] = operations,
        };
    }

    private static JsonObject Operation(
        string operationId,
        string capabilityId,
        JsonObject arguments,
        JsonArray dependencies) => new()
        {
            ["operation_id"] = operationId,
            ["capability_id"] = capabilityId,
            ["target"] = new JsonObject
            {
                ["node_id"] = "node-1",
                ["node_kind"] = "paragraph",
                ["structural_path"] = new JsonObject
                {
                    ["root"] = new JsonObject { ["root"] = "section", ["index"] = 0 },
                    ["steps"] = new JsonArray
                {
                    new JsonObject
                    {
                        ["step"] = "flow_child",
                        ["index"] = 0,
                        ["expected_kind"] = "paragraph",
                    },
                },
                },
                ["text_range"] = null,
                ["node_fingerprint_sha256"] = DigestArray(0x22),
            },
            ["arguments"] = arguments,
            ["depends_on"] = dependencies,
        };

    private static JsonObject Argument(string type, object value)
    {
        var canonical = new JsonObject
        {
            ["value_type"] = type,
            ["value"] = JsonValue.Create(value),
        };
        return new JsonObject
        {
            ["source"] = "caller",
            ["value"] = canonical,
            ["conversion_receipt"] = null,
            ["value_sha256"] = DigestArray(SHA256.HashData(JsonBytes(canonical))),
        };
    }

    private static JsonArray PlanOperations(JsonObject plan) => plan["operations"]!.AsArray();

    private static JsonObject OperationArguments(JsonNode operation) =>
        operation["arguments"]!.AsObject();

    private static JsonArray DigestArray(byte value) =>
        new(Enumerable.Range(0, 32)
            .Select(_ => (JsonNode?)JsonValue.Create((int)value))
            .ToArray());

    private static JsonArray DigestArray(byte[] values) =>
        new(values.Select(value => (JsonNode?)JsonValue.Create((int)value)).ToArray());

    private static byte[] JsonBytes(JsonNode node) =>
        Encoding.UTF8.GetBytes(node.ToJsonString(JsonOptions));

    private static string Hash(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private sealed record SignedMaterial(
        byte[] Envelope,
        byte[] PublicKey)
    {
        internal static SignedMaterial Create(Action<JsonObject>? payloadMutation = null)
        {
            var privateKey = new Ed25519PrivateKeyParameters(new SecureRandom());
            var publicKey = privateKey.GeneratePublicKey();
            var payload = BuildPayload();
            payloadMutation?.Invoke(payload);
            var payloadBytes = JsonBytes(payload);
            var signer = new Ed25519Signer();
            signer.Init(forSigning: true, privateKey);
            signer.BlockUpdate(payloadBytes, 0, payloadBytes.Length);
            var signature = signer.GenerateSignature();
            var publicKeyBytes = PublicPem(publicKey);
            var keyDer = SubjectPublicKeyInfoFactory
                .CreateSubjectPublicKeyInfo(publicKey)
                .GetDerEncoded();
            var envelope = new JsonObject
            {
                ["schema_version"] = HancomBindingExecutor.EnvelopeSchemaVersion,
                ["algorithm"] = "Ed25519",
                ["key_id"] = "ed25519-sha256-" + Hash(keyDer),
                ["public_key_sha256"] = Hash(publicKeyBytes),
                ["payload_sha256"] = Hash(payloadBytes),
                ["payload_base64"] = Convert.ToBase64String(payloadBytes),
                ["signature_base64"] = Convert.ToBase64String(signature),
            };
            return new SignedMaterial(JsonBytes(envelope), publicKeyBytes);
        }

        internal HancomApprovedPlanExecution Approve(JsonObject plan) => Approve(JsonBytes(plan));

        internal HancomApprovedPlanExecution Approve(byte[] plan) =>
            new(plan, Envelope, PublicKey);

        private static JsonObject BuildPayload() => new()
        {
            ["schema_version"] = HancomBindingExecutor.PayloadSchemaVersion,
            ["bundle_id"] = BundleId,
            ["sequence"] = 1,
            ["source_registry_sha256"] = new string('b', 64),
            ["capability_registry_sha256"] = CapabilityRegistrySha256,
            ["target"] = new JsonObject
            {
                ["profile_id"] = HancomTargetProfile.CurrentProfileId,
                ["product_build"] = "11.0.0.9136",
                ["locale"] = "ko-KR",
                ["process_architecture"] = "x86",
                ["executable_sha256"] = ExecutableSha256,
            },
            ["authorization"] = new JsonObject
            {
                ["execution_enabled"] = true,
                ["source_registry_routing_enabled"] = false,
                ["scope"] = "current_pc_exact_target_only",
                ["minimum_probe_state"] = "runtime_verified_current_target",
            },
            ["bindings"] = new JsonArray
            {
                new JsonObject
                {
                    ["capability_id"] = "edit.synthetic_noop",
                    ["action_id"] = "SyntheticNoParameterAction",
                    ["parameter_set_id"] = null,
                    ["probe_evidence_sha256"] = new string('d', 64),
                    ["target_mode"] = "document_global",
                    ["parameters"] = new JsonArray(),
                },
                new JsonObject
                {
                    ["capability_id"] = "layout.synthetic_typed",
                    ["action_id"] = "SyntheticTypedAction",
                    ["parameter_set_id"] = "SyntheticParameterSet",
                    ["probe_evidence_sha256"] = new string('e', 64),
                    ["target_mode"] = "document_global",
                    ["parameters"] = new JsonArray
                    {
                        TextParameter("label", "SyntheticText"),
                        BooleanParameter("enabled", "SyntheticBoolean"),
                        IntegerParameter("count", "SyntheticCount"),
                        EnumParameter("mode", "SyntheticMode"),
                    },
                },
            },
        };

        private static JsonObject TextParameter(string argument, string item) => new()
        {
            ["argument_id"] = argument,
            ["item_name"] = item,
            ["source_value_type"] = "text",
            ["target_value_type"] = "string",
            ["required"] = true,
            ["minimum"] = null,
            ["maximum"] = null,
            ["maximum_utf8_bytes"] = 128,
            ["scale_numerator"] = null,
            ["scale_denominator"] = null,
            ["rounding"] = null,
            ["enum_values"] = null,
        };

        private static JsonObject BooleanParameter(string argument, string item) => new()
        {
            ["argument_id"] = argument,
            ["item_name"] = item,
            ["source_value_type"] = "boolean",
            ["target_value_type"] = "boolean",
            ["required"] = true,
            ["minimum"] = null,
            ["maximum"] = null,
            ["maximum_utf8_bytes"] = null,
            ["scale_numerator"] = null,
            ["scale_denominator"] = null,
            ["rounding"] = null,
            ["enum_values"] = null,
        };

        private static JsonObject IntegerParameter(string argument, string item) => new()
        {
            ["argument_id"] = argument,
            ["item_name"] = item,
            ["source_value_type"] = "integer",
            ["target_value_type"] = "int32",
            ["required"] = true,
            ["minimum"] = 0,
            ["maximum"] = 100,
            ["maximum_utf8_bytes"] = null,
            ["scale_numerator"] = 2,
            ["scale_denominator"] = 1,
            ["rounding"] = "exact",
            ["enum_values"] = null,
        };

        private static JsonObject EnumParameter(string argument, string item) => new()
        {
            ["argument_id"] = argument,
            ["item_name"] = item,
            ["source_value_type"] = "text",
            ["target_value_type"] = "int32_enum",
            ["required"] = true,
            ["minimum"] = null,
            ["maximum"] = null,
            ["maximum_utf8_bytes"] = 32,
            ["scale_numerator"] = null,
            ["scale_denominator"] = null,
            ["rounding"] = null,
            ["enum_values"] = new JsonObject { ["first"] = 1, ["second"] = 2 },
        };

        private static byte[] PublicPem(Ed25519PublicKeyParameters publicKey)
        {
            using var text = new StringWriter();
            var writer = new PemWriter(text);
            writer.WriteObject(publicKey);
            writer.Writer.Flush();
            return Encoding.ASCII.GetBytes(text.ToString());
        }
    }

    private sealed class FixedDocumentResolver(HancomApprovedDocument document)
        : IHancomApprovedDocumentResolver
    {
        public HancomApprovedDocument Resolve(
            StaOpenDocumentCommand command,
            StaExecutionContext context) => document;
    }

    private sealed class ThrowingPlanResolver(HancomLifecycleError error)
        : IHancomPlanExecutionResolver
    {
        public HancomApprovedPlanExecution Resolve(
            StaExecutePlanCommand command,
            StaExecutionContext context) => throw new HancomLifecycleException(error);
    }

    public sealed class DynamicAutomation(DynamicActionCollection actions)
    {
        public DynamicActionCollection HAction { get; } = actions;
    }

    public sealed class DynamicActionCollection(DynamicAction? action, bool runResult = true)
    {
        public bool Run(string actionId) => runResult;

        public DynamicAction? CreateAction(string actionId) => action;
    }

    public sealed class DynamicAction(
        string actionId,
        string setId,
        DynamicParameterSet parameterSet,
        bool executeResult = true)
    {
        public string ActID { get; } = actionId;

        public string SetID { get; } = setId;

        public DynamicParameterSet CreateSet() => parameterSet;

        public bool GetDefault(object value) => true;

        public bool Execute(object value) => executeResult;
    }

    public sealed class DynamicParameterSet(string setId, IEnumerable<string> items)
    {
        private readonly HashSet<string> items = items.ToHashSet(StringComparer.Ordinal);

        public bool IsSet => true;

        public string SetID { get; } = setId;

        public Dictionary<string, object> Values { get; } = new(StringComparer.Ordinal);

        public bool ItemExist(string itemId) => items.Contains(itemId);

        public void SetItem(string itemId, object value) => Values[itemId] = value;
    }

    private sealed class FakeFactory : IHancomRuntimeFactory
    {
        internal List<HancomBoundAction> Invocations { get; } = [];

        internal int? FailAtInvocation { get; init; }

        public HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context) =>
            new(new FakeRuntime(this), new FakeProcess());

        private sealed class FakeRuntime(FakeFactory owner) : IHancomAutomationRuntime
        {
            public string Version => "11.0.0.9136";

            public bool RegisterFilePathSecurityModule(string registrationName) => true;

            public IHancomAutomationDocument Open(HancomApprovedDocument input) => new FakeDocument();

            public bool ExecuteAction(HancomBoundAction invocation)
            {
                owner.Invocations.Add(invocation);
                return owner.FailAtInvocation != owner.Invocations.Count;
            }

            public void Quit()
            {
            }

            public void Dispose()
            {
            }
        }

        private sealed class FakeDocument : IHancomAutomationDocument
        {
            public void CloseWithoutSaving()
            {
            }

            public void Dispose()
            {
            }
        }

        private sealed class FakeProcess : IHancomOwnedProcess
        {
            public int ProcessId => 990;

            public void EnsureStopped(StaExecutionContext context)
            {
            }

            public void Dispose()
            {
            }
        }
    }

    private sealed class FakeSecurityRegistry(string modulePath) : IHancomSecurityModuleRegistry
    {
        public HancomSecurityModuleRegistration Resolve(
            string registrationName,
            string expectedSha256)
        {
            var bytes = File.ReadAllBytes(modulePath);
            Require(Hash(bytes) == expectedSha256, "security module pin drifted");
            var guard = new FileStream(
                modulePath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read);
            return new HancomSecurityModuleRegistration(registrationName, modulePath, guard);
        }
    }

    private sealed class BindingLeaseFixture : IDisposable
    {
        private readonly string root;
        private readonly byte[] inputBytes;
        private readonly byte[] planBytes;
        private readonly byte[] bundleBytes;

        private BindingLeaseFixture(
            string root,
            string executionId,
            ulong fence,
            byte[] inputBytes,
            byte[] planBytes,
            byte[] bundleBytes,
            string leasePath,
            string modulePath)
        {
            this.root = root;
            ExecutionId = executionId;
            Fence = fence;
            this.inputBytes = inputBytes;
            this.planBytes = planBytes;
            this.bundleBytes = bundleBytes;
            LeasePath = leasePath;
            ModulePath = modulePath;
        }

        internal string ExecutionId { get; }

        internal ulong Fence { get; }

        internal string LeasePath { get; }

        internal string ModulePath { get; }

        internal static BindingLeaseFixture Create()
        {
            var root = Path.Combine(
                Path.GetTempPath(),
                $"hwpx-agent-p10-06-lease-{Guid.NewGuid():N}");
            Directory.CreateDirectory(root);
            var executionId = "71000000-0000-4000-8000-000000000001";
            var fence = 71UL;
            File.WriteAllText(Path.Combine(root, ".hwpx-agent-sandbox"), executionId);
            var material = SignedMaterial.Create();
            var planBytes = JsonBytes(BuildPlan());
            var inputBytes = Encoding.ASCII.GetBytes("synthetic-binding-lease-input");
            var moduleBytes = Encoding.ASCII.GetBytes("synthetic-security-module");
            var inputPath = WriteReadOnly(
                root,
                HancomSecurityAdapter.ApprovedInputFileName,
                inputBytes);
            _ = WriteReadOnly(
                root,
                HancomSecurityAdapter.OperationPlanFileName,
                planBytes);
            _ = WriteReadOnly(
                root,
                HancomSecurityAdapter.BindingBundleFileName,
                material.Envelope);
            _ = WriteReadOnly(
                root,
                HancomSecurityAdapter.BindingPublicKeyFileName,
                material.PublicKey);
            var modulePath = Path.Combine(root, "synthetic-security.dll");
            File.WriteAllBytes(modulePath, moduleBytes);
            var lease = new JsonObject
            {
                ["schema_version"] = HancomSecurityAdapter.BindingSchemaVersion,
                ["execution_id"] = executionId,
                ["session_id"] = executionId,
                ["fencing_token"] = fence,
                ["target_profile_id"] = HancomTargetProfile.CurrentProfileId,
                ["expires_at_unix_ms"] = DateTimeOffset.UtcNow.AddMinutes(10).ToUnixTimeMilliseconds(),
                ["file_access_policy_id"] = HancomSecurityAdapter.FileAccessPolicyId,
                ["open_policy_id"] = HancomSecurityAdapter.OpenPolicyId,
                ["sandbox_handle"] = "input_0001",
                ["artifact_id"] = "p10-06-binding-input",
                ["input_sha256"] = Hash(inputBytes),
                ["input_size_bytes"] = inputBytes.Length,
                ["security_module_registration_name"] = "SyntheticSecurityModule",
                ["security_module_sha256"] = Hash(moduleBytes),
                ["operation_plan_sandbox_handle"] = "plan_0001",
                ["operation_plan_artifact_id"] = "p10-06-operation-plan",
                ["operation_plan_sha256"] = Hash(planBytes),
                ["operation_plan_size_bytes"] = planBytes.Length,
                ["binding_bundle_id"] = BundleId,
                ["binding_bundle_sha256"] = Hash(material.Envelope),
                ["binding_public_key_sha256"] = Hash(material.PublicKey),
                ["capability_registry_sha256"] = CapabilityRegistrySha256,
            };
            var leasePath = WriteReadOnly(
                root,
                HancomSecurityAdapter.LeaseFileName,
                JsonBytes(lease));
            Require(File.Exists(inputPath), "approved input was not created");
            return new BindingLeaseFixture(
                root,
                executionId,
                fence,
                inputBytes,
                planBytes,
                material.Envelope,
                leasePath,
                modulePath);
        }

        internal StaCommandEnvelope StartCommand()
        {
            var command = Envelope("72000000-0000-4000-8000-000000000001");
            command.StartSession = new StaStartSessionCommand
            {
                TargetProfile = new TargetProfileIdentity
                {
                    ProfileId = HancomTargetProfile.CurrentProfileId,
                    ProductBuild = "11.0.0.9136",
                    Locale = "ko-KR",
                    ProcessArchitecture = "x86",
                    ExecutableSha256 = ExecutableSha256,
                    EnvironmentDigest = new string('f', 64),
                },
                CapabilityRegistrySha256 = CapabilityRegistrySha256,
                SecurityPolicy = new SecurityPolicy
                {
                    FileAccessPolicyId = HancomSecurityAdapter.FileAccessPolicyId,
                    ModalPolicyId = "modal.fail_closed",
                },
            };
            return command;
        }

        internal StaCommandEnvelope OpenCommand()
        {
            var command = Envelope("72000000-0000-4000-8000-000000000002");
            command.OpenDocument = new StaOpenDocumentCommand
            {
                Input = new StagedArtifactRef
                {
                    Artifact = new ArtifactRef
                    {
                        ArtifactId = "p10-06-binding-input",
                        Sha256 = Hash(inputBytes),
                        SizeBytes = checked((ulong)inputBytes.Length),
                    },
                    SandboxHandle = "input_0001",
                    ReadOnly = true,
                },
                OpenPolicyId = HancomSecurityAdapter.OpenPolicyId,
            };
            return command;
        }

        internal StaCommandEnvelope ExecuteCommand()
        {
            var command = Envelope("72000000-0000-4000-8000-000000000003");
            command.ExecutePlan = new StaExecutePlanCommand
            {
                OperationPlan = new StagedArtifactRef
                {
                    Artifact = new ArtifactRef
                    {
                        ArtifactId = "p10-06-operation-plan",
                        Sha256 = Hash(planBytes),
                        SizeBytes = checked((ulong)planBytes.Length),
                    },
                    SandboxHandle = "plan_0001",
                    ReadOnly = true,
                },
                BindingBundleId = BundleId,
                BindingBundleSha256 = Hash(bundleBytes),
            };
            return command;
        }

        internal StaCommandEnvelope CloseCommand()
        {
            var command = Envelope("72000000-0000-4000-8000-000000000004");
            command.CloseSession = new StaCloseSessionCommand { DiscardUnsavedChanges = true };
            return command;
        }

        internal void RequireUnchanged()
        {
            Require(
                File.ReadAllBytes(Path.Combine(root, HancomSecurityAdapter.ApprovedInputFileName))
                    .AsSpan().SequenceEqual(inputBytes),
                "approved input changed");
            Require(
                File.ReadAllBytes(Path.Combine(root, HancomSecurityAdapter.OperationPlanFileName))
                    .AsSpan().SequenceEqual(planBytes),
                "approved plan changed");
            Require(
                File.ReadAllBytes(Path.Combine(root, HancomSecurityAdapter.BindingBundleFileName))
                    .AsSpan().SequenceEqual(bundleBytes),
                "approved bundle changed");
        }

        public void Dispose()
        {
            if (!Directory.Exists(root))
            {
                return;
            }

            foreach (var file in Directory.EnumerateFiles(root))
            {
                File.SetAttributes(file, FileAttributes.Normal);
            }

            Directory.Delete(root, recursive: true);
        }

        private StaCommandEnvelope Envelope(string commandId) => new()
        {
            ProtocolMajor = 1,
            ProtocolMinor = 0,
            SessionId = ExecutionId,
            CommandId = commandId,
            FencingToken = Fence,
            DeadlineUnixMs = checked((ulong)DateTimeOffset.UtcNow.AddMinutes(1).ToUnixTimeMilliseconds()),
            TraceId = "73000000-0000-4000-8000-000000000001",
        };

        private static string WriteReadOnly(string root, string name, byte[] bytes)
        {
            var path = Path.Combine(root, name);
            File.WriteAllBytes(path, bytes);
            File.SetAttributes(path, FileAttributes.ReadOnly);
            return path;
        }
    }

    private sealed class Fixture : IDisposable
    {
        private readonly string root;
        private readonly byte[] original;

        private Fixture(string root, string path, byte[] original)
        {
            this.root = root;
            Path = path;
            this.original = original;
            Document = new HancomApprovedDocument(path, Hash(original), original.Length);
        }

        internal string Path { get; }

        internal HancomApprovedDocument Document { get; }

        internal static Fixture Create()
        {
            var root = System.IO.Path.Combine(
                System.IO.Path.GetTempPath(),
                $"hwpx-agent-p10-06-{Guid.NewGuid():N}");
            Directory.CreateDirectory(root);
            var path = System.IO.Path.Combine(root, "synthetic.hwpx");
            var bytes = Encoding.ASCII.GetBytes("synthetic-hwpx-binding-fixture");
            File.WriteAllBytes(path, bytes);
            return new Fixture(root, path, bytes);
        }

        internal void RequireUnchanged() =>
            Require(File.ReadAllBytes(Path).AsSpan().SequenceEqual(original), "input fixture changed");

        public void Dispose()
        {
            Document.Dispose();
            Directory.Delete(root, recursive: true);
        }
    }
}
