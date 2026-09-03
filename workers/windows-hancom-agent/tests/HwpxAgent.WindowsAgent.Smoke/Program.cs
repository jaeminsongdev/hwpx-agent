using System.Text;
using System.Text.Json;
using Google.Protobuf;
using Grpc.Core;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using HwpxAgent.WindowsAgent;

namespace HwpxAgent.WindowsAgent.Smoke;

internal static class Program
{
    private static readonly byte[] InputBytes = Encoding.UTF8.GetBytes("bounded input fixture");
    private static readonly byte[] PlanBytes = Encoding.UTF8.GetBytes("typed operation plan");
    private static readonly byte[] ValidationBytes = Encoding.UTF8.GetBytes("validation contract");
    private static readonly byte[] OutputBytes = Encoding.UTF8.GetBytes("deterministic output fixture");

    public static async Task<int> Main()
    {
        await SuccessfulLeaseReplaysWithoutDuplicateEffectAsync();
        await HancomSecurityLeaseBridgesOpaqueHandleAsync();
        await HancomBindingLeaseCopiesPinnedPlanBundleAndKeyAsync();
        await ConcurrentDuplicateLeaseIsBusyAsync();
        await StaleLeaseNeverInvokesExecutorAsync();
        await UnfinishedJournalBecomesUnknownWithoutReplayAsync();
        await FencingDriftIsRejectedWithoutCommitAsync();
        await ArtifactMismatchFailsBeforeExecutorAsync();
        await CommitDigestMismatchReplaysWithoutExecutorAsync();
        await AggregateOutputLimitFailsBeforeUploadAsync();
        await ArtifactUploadIsIdempotentButValidatesEveryStreamAsync();
        await NoWorkAndProfileMismatchFailClosedAsync();
        RejectsUnsafeTransportAndArtifactBoundaries();
        Console.WriteLine("Windows Agent P10-02/P10-05/P10-06 staging, security lease, fencing, upload and auth smoke passed (13/13)");
        return 0;
    }

    private static async Task SuccessfulLeaseReplaysWithoutDuplicateEffectAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("success");
        var assignment = environment.CreateAssignment(
            leaseId: "10000000-0000-4000-8000-000000000001",
            executionId: "20000000-0000-4000-8000-000000000001",
            fencingToken: 7);
        var executorCalls = 0;
        var committedReceipts = new List<byte[]>();
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, committedReceipts),
                "ReportProbe" => AcceptedProbe((AgentProbeRequest)request),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            executorCalls++;
            await AssertStagedInputAsync(context, cancellationToken);
            await using var output = context.CreateOutput("output_0001");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob();
        });
        var service = environment.CreateService(client, executor);

        var first = await service.RunOnceAsync(CancellationToken.None);
        var second = await service.RunOnceAsync(CancellationToken.None);
        Require(first.Disposition == AgentRunDisposition.Succeeded && first.ExecutorInvoked, "first run did not succeed");
        Require(second.Disposition == AgentRunDisposition.Replayed && !second.ExecutorInvoked, "terminal run was not replayed");
        Require(executorCalls == 1, "executor ran more than once");
        Require(committedReceipts.Count == 2
            && committedReceipts[0].AsSpan().SequenceEqual(committedReceipts[1]), "receipt replay drifted");

        var receipt = AgentExecutionReceipt.Parser.ParseFrom(committedReceipts[0]);
        Require(receipt.Outputs.Count == 1 && receipt.Evidence.Count == 0, "uploaded output receipt is incomplete");
        await using (var uploaded = await environment.Store.OpenReadAsync(receipt.Outputs[0], CancellationToken.None))
        {
            using var copy = new MemoryStream();
            await uploaded.CopyToAsync(copy);
            Require(copy.ToArray().AsSpan().SequenceEqual(OutputBytes), "uploaded output bytes drifted");
        }

        var probe = new RuntimeProbeReceipt
        {
            TargetProfile = environment.Configuration.TargetProfile.Clone(),
            Health = ProbeHealth.Healthy,
            CapabilityRegistrySha256 = environment.Configuration.CapabilityRegistrySha256,
            CapabilitySetSha256 = Digest('9'),
            Evidence = environment.Input.Clone(),
            ObservedAtUnixMs = 1_800_000_000_000,
        };
        Require(await service.ReportProbeAsync(probe, CancellationToken.None), "probe was not accepted and routable");
        Require(invoker.Methods.SequenceEqual(
            ["AcquireLease", "Heartbeat", "Heartbeat", "CommitExecution", "AcquireLease", "CommitExecution", "ReportProbe"]),
            "outbound RPC method sequence drifted");
        Require(environment.SandboxDirectories().Count == 0, "successful run left a sandbox directory");
    }

    private static async Task HancomSecurityLeaseBridgesOpaqueHandleAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("hancom-security");
        var assignment = environment.CreateAssignment(
            leaseId: "10000000-0000-4000-8000-000000000012",
            executionId: "20000000-0000-4000-8000-000000000012",
            fencingToken: 19);
        string? sandboxPath = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            context.Assignment.Input = context.Assignment.OperationPlan.Clone();
            var lease = await context.PrepareHancomWorkerSecurityLeaseAsync(cancellationToken);
            var leaseSandbox = Path.GetDirectoryName(lease.SecurityLeasePath)
                ?? throw new InvalidOperationException("security lease escaped its sandbox");
            sandboxPath = leaseSandbox;
            Require(
                string.Equals(Path.GetFileName(lease.SecurityLeasePath), ".hancom-security-lease.json", StringComparison.Ordinal),
                "security lease filename drifted");
            Require(
                (File.GetAttributes(lease.SecurityLeasePath) & FileAttributes.ReadOnly) != 0,
                "security lease is mutable");

            using (var document = JsonDocument.Parse(await File.ReadAllBytesAsync(lease.SecurityLeasePath, cancellationToken)))
            {
                var root = document.RootElement;
                Require(root.EnumerateObject().Count() == 14, "security lease field set drifted");
                Require(root.GetProperty("schema_version").GetString() == "hwpx-agent.p10-05-security-lease/v1", "security schema drifted");
                Require(root.GetProperty("session_id").GetString() == assignment.ExecutionId, "security session was not execution-bound");
                Require(root.GetProperty("fencing_token").GetUInt64() == assignment.FencingToken, "security fence drifted");
                Require(root.GetProperty("sandbox_handle").GetString() == "input_0001", "opaque input handle drifted");
                Require(root.GetProperty("sandbox_handle").GetString()!.IndexOfAny(['\\', '/', ':', '.']) < 0, "public handle became a path");
                Require(root.GetProperty("input_sha256").GetString() == environment.Input.Sha256, "security digest drifted");
                Require(root.GetProperty("security_module_registration_name").GetString() == "FilePathCheckerModuleExample", "module pin drifted");
            }

            var approvedInput = Path.Combine(leaseSandbox, "hancom_approved_input.hwpx");
            Require(
                (File.GetAttributes(approvedInput) & FileAttributes.ReadOnly) != 0,
                "approved input is mutable");
            Require(
                (await File.ReadAllBytesAsync(approvedInput, cancellationToken)).AsSpan().SequenceEqual(InputBytes),
                "approved input copy drifted");
            await RequireThrowsAsync<AgentProtocolException>(
                () => context.PrepareHancomWorkerSecurityLeaseAsync(cancellationToken));

            await using var output = context.CreateOutput("output_0001");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob();
        });
        var result = await environment.CreateService(client, executor).RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Succeeded, "security lease integration did not succeed");
        Require(sandboxPath is not null && !Directory.Exists(sandboxPath), "security lease sandbox was not removed");
    }

    private static async Task HancomBindingLeaseCopiesPinnedPlanBundleAndKeyAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("hancom-binding");
        var bundleBytes = Encoding.UTF8.GetBytes("{\"synthetic_bundle\":true}");
        var publicKeyBytes = Encoding.ASCII.GetBytes(
            "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n-----END PUBLIC KEY-----\n");
        var bundlePath = Path.Combine(environment.Root, "synthetic-binding.json");
        var publicKeyPath = Path.Combine(environment.Root, "synthetic-binding.pem");
        await File.WriteAllBytesAsync(bundlePath, bundleBytes);
        await File.WriteAllBytesAsync(publicKeyPath, publicKeyBytes);
        var bundleId = "binding.current2020.v1";
        var bundleSha256 = Sha256(bundleBytes);
        var configuration = environment.Configuration with
        {
            HancomBindingBundle = new HancomBindingBundlePin(
                bundleId,
                bundlePath,
                bundleSha256,
                publicKeyPath,
                Sha256(publicKeyBytes)),
        };
        var assignment = environment.CreateAssignment(
            leaseId: "10000000-0000-4000-8000-000000000013",
            executionId: "20000000-0000-4000-8000-000000000013",
            fencingToken: 23);
        string? sandboxPath = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            var lease = await context.PrepareHancomWorkerSecurityLeaseAsync(cancellationToken);
            sandboxPath = Path.GetDirectoryName(lease.SecurityLeasePath)
                ?? throw new InvalidOperationException("binding lease escaped its sandbox");
            using var document = JsonDocument.Parse(
                await File.ReadAllBytesAsync(lease.SecurityLeasePath, cancellationToken));
            var root = document.RootElement;
            Require(root.EnumerateObject().Count() == 22, "binding lease field set drifted");
            Require(
                root.GetProperty("schema_version").GetString()
                    == "hwpx-agent.p10-06-security-lease/v2",
                "binding lease schema drifted");
            Require(
                root.GetProperty("operation_plan_sandbox_handle").GetString() == "plan_0001",
                "operation-plan handle drifted");
            Require(
                root.GetProperty("operation_plan_sha256").GetString() == environment.Plan.Sha256,
                "operation-plan digest drifted");
            Require(
                root.GetProperty("binding_bundle_id").GetString() == bundleId
                    && root.GetProperty("binding_bundle_sha256").GetString() == bundleSha256,
                "binding identity drifted");
            Require(
                root.GetProperty("capability_registry_sha256").GetString()
                    == configuration.CapabilityRegistrySha256,
                "capability registry binding drifted");

            foreach (var (name, expected) in new[]
            {
                ("hancom_operation_plan.json", PlanBytes),
                ("hancom_binding_bundle.json", bundleBytes),
                ("hancom_binding_public_key.pem", publicKeyBytes),
            })
            {
                var copied = Path.Combine(sandboxPath, name);
                Require(
                    (File.GetAttributes(copied) & FileAttributes.ReadOnly) != 0,
                    $"private binding input became mutable: {name}");
                Require(
                    (await File.ReadAllBytesAsync(copied, cancellationToken)).AsSpan()
                        .SequenceEqual(expected),
                    $"private binding input drifted: {name}");
            }

            await using var output = context.CreateOutput("output_0001");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return new AgentJobResult(
                ExecutionState.Succeeded,
                "windows.agent",
                bundleId,
                bundleSha256,
                ValidationState.Passed,
                [new ProducedArtifact("output_0001", "fixture-output-binding")]);
        });
        var service = new WindowsAgentService(
            configuration,
            client,
            environment.Store,
            executor,
            environment.Workspace);
        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Succeeded, "binding lease integration failed");
        Require(sandboxPath is not null && !Directory.Exists(sandboxPath), "binding lease sandbox remained");
    }

    private static async Task ConcurrentDuplicateLeaseIsBusyAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("busy");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000002",
            "20000000-0000-4000-8000-000000000002",
            8);
        var entered = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var release = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var executorCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            executorCalls++;
            entered.SetResult(true);
            await release.Task.WaitAsync(cancellationToken);
            await using var output = context.CreateOutput("output_0002");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob("output_0002", "fixture-output-busy");
        });
        var service = environment.CreateService(client, executor);

        var active = service.RunOnceAsync(CancellationToken.None);
        await entered.Task.WaitAsync(TimeSpan.FromSeconds(10));
        var duplicate = await service.RunOnceAsync(CancellationToken.None);
        Require(duplicate.Disposition == AgentRunDisposition.Busy && !duplicate.ExecutorInvoked, "active claim was not exclusive");
        release.SetResult(true);
        var completed = await active;
        Require(completed.Disposition == AgentRunDisposition.Succeeded && executorCalls == 1, "owned execution did not finish once");
    }

    private static async Task StaleLeaseNeverInvokesExecutorAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("stale");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000003",
            "20000000-0000-4000-8000-000000000003",
            9);
        var executorCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => new AgentHeartbeatResponse { LeaseCurrent = false },
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var service = environment.CreateService(
            client,
            new DelegatingExecutor((_, _) =>
            {
                executorCalls++;
                throw new InvalidOperationException("stale lease reached executor");
            }));

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.StaleLease
            && result.TerminalState == ExecutionState.Failed, "stale heartbeat did not fail closed");
        Require(executorCalls == 0 && environment.SandboxDirectories().Count == 0, "stale lease produced an effect");
    }

    private static async Task UnfinishedJournalBecomesUnknownWithoutReplayAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("unknown");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000004",
            "20000000-0000-4000-8000-000000000004",
            10);
        var abandoned = await environment.Workspace.Journal.ClaimAsync(assignment, CancellationToken.None);
        Require(abandoned.Disposition == JournalClaimDisposition.New, "fixture claim was not new");
        await abandoned.Ownership!.DisposeAsync();

        var executorCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unfinished recovery executed work"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var service = environment.CreateService(
            client,
            new DelegatingExecutor((_, _) =>
            {
                executorCalls++;
                throw new InvalidOperationException("abandoned claim reached executor");
            }));

        var recovered = await service.RunOnceAsync(CancellationToken.None);
        Require(recovered.Disposition == AgentRunDisposition.Replayed
            && recovered.TerminalState == ExecutionState.UnknownOutcome, "unfinished claim was not reconciled as unknown");
        Require(executorCalls == 0, "unfinished claim was re-executed");
    }

    private static async Task FencingDriftIsRejectedWithoutCommitAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("fencing");
        var original = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000005",
            "20000000-0000-4000-8000-000000000005",
            11);
        var drifted = original.Clone();
        drifted.FencingToken = 12;
        var acquisition = 0;
        var commits = 0;
        var executorCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(++acquisition == 1 ? original : drifted),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CountedCommit((AgentCommitRequest)request, ref commits),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            executorCalls++;
            await using var output = context.CreateOutput("output_0005");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob("output_0005", "fixture-output-fencing");
        });
        var service = environment.CreateService(client, executor);

        var first = await service.RunOnceAsync(CancellationToken.None);
        var second = await service.RunOnceAsync(CancellationToken.None);
        Require(first.Disposition == AgentRunDisposition.Succeeded, "original fence did not complete");
        Require(second.Disposition == AgentRunDisposition.FencingMismatch
            && !second.ExecutorInvoked
            && !second.CommitAttempted, "fencing drift was not rejected before effect/commit");
        Require(executorCalls == 1 && commits == 1, "fencing drift duplicated execution or commit");
    }

    private static async Task ArtifactMismatchFailsBeforeExecutorAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("artifact-mismatch");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000006",
            "20000000-0000-4000-8000-000000000006",
            13);
        assignment.Input = assignment.Input.Clone();
        assignment.Input.Artifact = assignment.Input.Artifact.Clone();
        assignment.Input.Artifact.Sha256 = Digest('d');
        var executorCalls = 0;
        AgentExecutionReceipt? committed = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CaptureCommit((AgentCommitRequest)request, receipt => committed = receipt),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var service = environment.CreateService(
            client,
            new DelegatingExecutor((_, _) =>
            {
                executorCalls++;
                throw new InvalidOperationException("bad artifact reached executor");
            }));

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Failed && !result.ExecutorInvoked, "artifact mismatch did not fail before execution");
        Require(executorCalls == 0, "artifact mismatch invoked executor");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.ArtifactMismatch, "artifact mismatch receipt lost its typed error");
        Require(environment.SandboxDirectories().Count == 0, "artifact mismatch left a sandbox directory");
    }

    private static async Task CommitDigestMismatchReplaysWithoutExecutorAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("commit-mismatch");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000007",
            "20000000-0000-4000-8000-000000000007",
            14);
        var executorCalls = 0;
        var commits = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CommitWithFirstDigestMismatch((AgentCommitRequest)request, ++commits),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            executorCalls++;
            await using var output = context.CreateOutput("output_0007");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob("output_0007", "fixture-output-commit-mismatch");
        });
        var service = environment.CreateService(client, executor);

        await RequireThrowsAsync<AgentProtocolException>(() => service.RunOnceAsync(CancellationToken.None));
        var replay = await service.RunOnceAsync(CancellationToken.None);
        Require(replay.Disposition == AgentRunDisposition.Replayed && !replay.ExecutorInvoked, "terminal receipt was not replayed after commit mismatch");
        Require(executorCalls == 1 && commits == 2, "commit mismatch duplicated executor or skipped replay commit");
    }

    private static async Task ArtifactUploadIsIdempotentButValidatesEveryStreamAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("upload-idempotency");
        var artifact = new ArtifactRef
        {
            ArtifactId = "fixture-idempotent",
            Sha256 = Sha256(OutputBytes),
            SizeBytes = (ulong)OutputBytes.Length,
        };
        await using (var first = new MemoryStream(OutputBytes, writable: false))
        {
            await environment.Store.UploadAsync(artifact, first, CancellationToken.None);
        }

        await using (var retry = new MemoryStream(OutputBytes, writable: false))
        {
            await environment.Store.UploadAsync(artifact, retry, CancellationToken.None);
        }

        var wrong = Enumerable.Repeat((byte)'x', OutputBytes.Length).ToArray();
        await RequireThrowsAsync<AgentProtocolException>(async () =>
        {
            await using var mismatched = new MemoryStream(wrong, writable: false);
            await environment.Store.UploadAsync(artifact, mismatched, CancellationToken.None);
        });
        await using var accepted = await environment.Store.OpenReadAsync(artifact, CancellationToken.None);
        using var copy = new MemoryStream();
        await accepted.CopyToAsync(copy);
        Require(copy.ToArray().AsSpan().SequenceEqual(OutputBytes), "idempotent retry changed stored bytes");
    }

    private static async Task AggregateOutputLimitFailsBeforeUploadAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("aggregate-output-limit");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000009",
            "20000000-0000-4000-8000-000000000009",
            16);
        assignment.ResourceLimits.MaxOutputBytes = (ulong)(OutputBytes.Length * 2 - 1);
        AgentExecutionReceipt? committed = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CaptureCommit((AgentCommitRequest)request, receipt => committed = receipt),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var service = environment.CreateService(
            client,
            new DelegatingExecutor(async (context, cancellationToken) =>
            {
                await using (var first = context.CreateOutput("output_0009a"))
                {
                    await first.WriteAsync(OutputBytes, cancellationToken);
                }

                await using (var second = context.CreateOutput("output_0009b"))
                {
                    await second.WriteAsync(OutputBytes, cancellationToken);
                }

                return new AgentJobResult(
                    ExecutionState.Succeeded,
                    "windows.agent",
                    "binding.bundle_v1",
                    Digest('8'),
                    ValidationState.Passed,
                    [
                        new ProducedArtifact("output_0009a", "fixture-output-limit-a"),
                        new ProducedArtifact("output_0009b", "fixture-output-limit-b"),
                    ]);
            }));

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.UnknownOutcome && result.ExecutorInvoked,
            "aggregate output overflow was not contained after executor invocation");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.OutputRejected
            && committed.Diagnostic.EffectUnknown,
            "aggregate output overflow lost its typed unknown-outcome receipt");
        Require(environment.SandboxDirectories().Count == 0, "aggregate output overflow left a sandbox directory");
    }

    private static async Task NoWorkAndProfileMismatchFailClosedAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("no-work-profile");
        var noWorkInvoker = new ScriptedCallInvoker((method, _, headers) =>
        {
            RequireAuthorization(headers);
            return method == "AcquireLease"
                ? new AgentLeaseResponse { Disposition = LeaseDisposition.NoWork, RetryAfterMs = 50 }
                : throw new InvalidOperationException("no-work response invoked another RPC");
        });
        await using (var noWorkClient = AuthenticatedClient(noWorkInvoker))
        {
            var service = environment.CreateService(
                noWorkClient,
                new DelegatingExecutor((_, _) => throw new InvalidOperationException("no work reached executor")));
            var result = await service.RunOnceAsync(CancellationToken.None);
            Require(result.Disposition == AgentRunDisposition.NoWork && !result.CommitAttempted, "no-work lease was not side-effect free");
        }

        var mismatched = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000008",
            "20000000-0000-4000-8000-000000000008",
            15);
        mismatched.TargetProfileId = "hancom-hangul-2024-deferred";
        var mismatchInvoker = new ScriptedCallInvoker((method, _, headers) =>
        {
            RequireAuthorization(headers);
            return method == "AcquireLease"
                ? Assigned(mismatched)
                : throw new InvalidOperationException("profile mismatch invoked another RPC");
        });
        await using var mismatchClient = AuthenticatedClient(mismatchInvoker);
        var mismatchService = environment.CreateService(
            mismatchClient,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("profile mismatch reached executor")));
        await RequireThrowsAsync<AgentProtocolException>(() => mismatchService.RunOnceAsync(CancellationToken.None));
        Require(environment.SandboxDirectories().Count == 0, "profile mismatch created a sandbox");

        var missingEvidence = new RuntimeProbeReceipt
        {
            TargetProfile = environment.Configuration.TargetProfile.Clone(),
            Health = ProbeHealth.Healthy,
            CapabilityRegistrySha256 = environment.Configuration.CapabilityRegistrySha256,
            CapabilitySetSha256 = Digest('9'),
            Evidence = environment.Input.Clone(),
            ObservedAtUnixMs = 1_800_000_000_000,
        };
        missingEvidence.Evidence.Sha256 = Digest('f');
        var probeInvoker = new ScriptedCallInvoker((_, _, _) =>
            throw new InvalidOperationException("missing probe evidence reached control plane"));
        await using var probeClient = AuthenticatedClient(probeInvoker);
        var probeService = environment.CreateService(
            probeClient,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("probe invoked executor")));
        await RequireThrowsAsync<AgentProtocolException>(() =>
            probeService.ReportProbeAsync(missingEvidence, CancellationToken.None));
        Require(probeInvoker.Methods.Count == 0, "missing probe evidence triggered an outbound RPC");
    }

    private static void RejectsUnsafeTransportAndArtifactBoundaries()
    {
        RequireThrows<ArgumentException>(() =>
            new GrpcWindowsAgentControlClient(
                new Uri("http://localhost:5001"),
                new string('t', 40),
                TimeSpan.FromSeconds(10)));
        RequireThrows<ArgumentException>(() =>
            new GrpcWindowsAgentControlClient(
                new ScriptedCallInvoker((_, _, _) => throw new InvalidOperationException()),
                "short-token",
                TimeSpan.FromSeconds(10)));
        RequireThrows<ArgumentException>(() =>
            _ = new ContentAddressedArtifactStore(Path.GetPathRoot(Path.GetTempPath())!));

        var configuration = new WindowsAgentConfiguration(
            "30000000-0000-4000-8000-000000000009",
            new TargetProfileIdentity
            {
                ProfileId = "hancom-hangul-2020-secondary",
                ProductBuild = "11.0.0.9136",
                Locale = "ko-KR",
                ProcessArchitecture = "x86",
                ExecutableSha256 = Digest('a'),
                EnvironmentDigest = Digest('b'),
            },
            Digest('c'),
            AvailableJobSlots: 1,
            RpcTimeout: TimeSpan.FromSeconds(10),
            HancomSecurityModule: new HancomSecurityModulePin("SyntheticModule", Digest('d')));
        RequireThrows<ArgumentException>(() => AgentValidation.ValidateConfiguration(configuration with
        {
            HancomBindingBundle = new HancomBindingBundlePin(
                "binding.current2020.v1",
                @"\\server\share\bundle.json",
                Digest('e'),
                @"C:\trust\key.pem",
                Digest('f')),
        }));
        RequireThrows<ArgumentException>(() => AgentValidation.ValidateConfiguration(configuration with
        {
            HancomBindingBundle = new HancomBindingBundlePin(
                "binding.current2020.v1",
                @"C:\trust\same.bin",
                Digest('e'),
                @"C:\trust\same.bin",
                Digest('f')),
        }));
    }

    private static async Task AssertStagedInputAsync(AgentJobContext context, CancellationToken cancellationToken)
    {
        await using var input = context.OpenStagedInput("input_0001");
        using var copy = new MemoryStream();
        await input.CopyToAsync(copy, cancellationToken);
        Require(copy.ToArray().AsSpan().SequenceEqual(InputBytes), "staged input bytes drifted");
    }

    private static AgentJobResult SuccessfulJob(
        string handle = "output_0001",
        string artifactId = "fixture-output") =>
        new(
            ExecutionState.Succeeded,
            "windows.agent",
            "binding.bundle_v1",
            Digest('8'),
            ValidationState.Passed,
            [new ProducedArtifact(handle, artifactId)]);

    private static GrpcWindowsAgentControlClient AuthenticatedClient(CallInvoker invoker) =>
        new(invoker, new string('t', 40), TimeSpan.FromSeconds(10));

    private static AgentLeaseResponse Assigned(LeaseAssignment assignment) =>
        new()
        {
            Disposition = LeaseDisposition.Assigned,
            Assignment = assignment.Clone(),
        };

    private static AgentHeartbeatResponse CurrentHeartbeat() =>
        new()
        {
            LeaseCurrent = true,
            ExpiresAtUnixMs = 1_900_000_000_000,
        };

    private static AgentCommitResponse Commit(AgentCommitRequest request, List<byte[]> receipts)
    {
        var bytes = request.Receipt.ToByteArray();
        receipts.Add(bytes);
        return new AgentCommitResponse
        {
            Disposition = receipts.Count == 1 ? CommitDisposition.Accepted : CommitDisposition.AlreadyTerminal,
            ReceiptSha256 = Sha256(bytes),
        };
    }

    private static AgentCommitResponse CountedCommit(AgentCommitRequest request, ref int count)
    {
        count++;
        return new AgentCommitResponse
        {
            Disposition = CommitDisposition.Accepted,
            ReceiptSha256 = Sha256(request.Receipt.ToByteArray()),
        };
    }

    private static AgentCommitResponse CaptureCommit(
        AgentCommitRequest request,
        Action<AgentExecutionReceipt> capture)
    {
        capture(request.Receipt.Clone());
        return new AgentCommitResponse
        {
            Disposition = CommitDisposition.Accepted,
            ReceiptSha256 = Sha256(request.Receipt.ToByteArray()),
        };
    }

    private static AgentCommitResponse CommitWithFirstDigestMismatch(AgentCommitRequest request, int commitNumber) =>
        new()
        {
            Disposition = CommitDisposition.Accepted,
            ReceiptSha256 = commitNumber == 1 ? Digest('0') : Sha256(request.Receipt.ToByteArray()),
        };

    private static AgentProbeResponse AcceptedProbe(AgentProbeRequest request) =>
        new()
        {
            Accepted = true,
            Routable = true,
            AcceptedProbeSha256 = Sha256(request.Probe.ToByteArray()),
        };

    private static void RequireAuthorization(Metadata? headers)
    {
        var authorization = headers?.FirstOrDefault(entry => entry.Key == "authorization")?.Value;
        Require(authorization is not null
            && authorization.StartsWith("Bearer ", StringComparison.Ordinal)
            && authorization.Length == 47, "authenticated outbound metadata missing");
    }

    private static string Digest(char value) => new(value, 64);

    private static string Sha256(ReadOnlySpan<byte> bytes) =>
        Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(bytes));

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
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

    private static async Task RequireThrowsAsync<TException>(Func<Task> action)
        where TException : Exception
    {
        try
        {
            await action();
        }
        catch (TException)
        {
            return;
        }

        throw new InvalidOperationException($"Expected {typeof(TException).Name}.");
    }

    private sealed class TestEnvironment : IAsyncDisposable
    {
        private TestEnvironment(
            string root,
            ContentAddressedArtifactStore store,
            AgentWorkspace workspace,
            WindowsAgentConfiguration configuration,
            ArtifactRef input,
            ArtifactRef plan,
            ArtifactRef validation)
        {
            Root = root;
            Store = store;
            Workspace = workspace;
            Configuration = configuration;
            Input = input;
            Plan = plan;
            Validation = validation;
        }

        internal string Root { get; }

        internal ContentAddressedArtifactStore Store { get; }

        internal AgentWorkspace Workspace { get; }

        internal WindowsAgentConfiguration Configuration { get; }

        internal ArtifactRef Input { get; }

        internal ArtifactRef Plan { get; }

        internal ArtifactRef Validation { get; }

        internal static async Task<TestEnvironment> CreateAsync(string label)
        {
            var root = Path.Combine(Path.GetTempPath(), $"hwpx-agent-p10-02-{label}-{Guid.NewGuid():N}");
            Directory.CreateDirectory(root);
            var store = new ContentAddressedArtifactStore(Path.Combine(root, "store"));
            var workspace = new AgentWorkspace(Path.Combine(root, "workspace"));
            var input = await UploadAsync(store, "fixture-input", InputBytes);
            var plan = await UploadAsync(store, "fixture-operation-plan", PlanBytes);
            var validation = await UploadAsync(store, "fixture-validation-contract", ValidationBytes);
            var configuration = new WindowsAgentConfiguration(
                "30000000-0000-4000-8000-000000000001",
                new TargetProfileIdentity
                {
                    ProfileId = "hancom-hangul-2020-secondary",
                    ProductBuild = "11.0.0.9136",
                    Locale = "ko-KR",
                    ProcessArchitecture = "x86",
                    ExecutableSha256 = Digest('a'),
                    EnvironmentDigest = Digest('b'),
                },
                Digest('c'),
                AvailableJobSlots: 1,
                RpcTimeout: TimeSpan.FromSeconds(10),
                HancomSecurityModule: new HancomSecurityModulePin(
                    "FilePathCheckerModuleExample",
                    Digest('d')));
            return new TestEnvironment(root, store, workspace, configuration, input, plan, validation);
        }

        internal LeaseAssignment CreateAssignment(string leaseId, string executionId, ulong fencingToken) =>
            new()
            {
                LeaseId = leaseId,
                FencingToken = fencingToken,
                ExpiresAtUnixMs = 1_900_000_000_000,
                RequestId = "40000000-0000-4000-8000-000000000001",
                JobId = "50000000-0000-4000-8000-000000000001",
                TraceId = "60000000-0000-4000-8000-000000000001",
                ExecutionId = executionId,
                TargetProfileId = Configuration.TargetProfile.ProfileId,
                Input = Staged(Input, "input_0001"),
                OperationPlan = Staged(Plan, "plan_0001"),
                ValidationContract = Staged(Validation, "validation_0001"),
                ResourceLimits = new ResourceLimits
                {
                    CommandTimeoutSeconds = 30,
                    JobTimeoutSeconds = 120,
                    MemoryLimitBytes = 268_435_456,
                    MaxOutputBytes = 1_048_576,
                    MaxEventCount = 64,
                },
                SecurityPolicy = new SecurityPolicy
                {
                    FileAccessPolicyId = "file.local_read",
                    ModalPolicyId = "modal.fail_closed",
                },
            };

        internal WindowsAgentService CreateService(
            IWindowsAgentControlClient client,
            IAgentJobExecutor executor) =>
            new(Configuration, client, Store, executor, Workspace);

        internal List<string> SandboxDirectories()
        {
            var root = Path.Combine(Workspace.RootPath, "sandboxes");
            return Directory.EnumerateDirectories(root, "job-*", SearchOption.TopDirectoryOnly).ToList();
        }

        public ValueTask DisposeAsync()
        {
            if (Directory.Exists(Root))
            {
                Directory.Delete(Root, recursive: true);
            }

            return ValueTask.CompletedTask;
        }

        private static async Task<ArtifactRef> UploadAsync(
            ContentAddressedArtifactStore store,
            string artifactId,
            byte[] bytes)
        {
            var artifact = new ArtifactRef
            {
                ArtifactId = artifactId,
                Sha256 = Sha256(bytes),
                SizeBytes = (ulong)bytes.Length,
            };
            await using var content = new MemoryStream(bytes, writable: false);
            await store.UploadAsync(artifact, content, CancellationToken.None);
            return artifact;
        }

        private static StagedArtifactRef Staged(ArtifactRef artifact, string handle) =>
            new()
            {
                Artifact = artifact.Clone(),
                SandboxHandle = handle,
                ReadOnly = true,
            };
    }

    private sealed class DelegatingExecutor(
        Func<AgentJobContext, CancellationToken, Task<AgentJobResult>> execute) : IAgentJobExecutor
    {
        public Task<AgentJobResult> ExecuteAsync(
            AgentJobContext context,
            CancellationToken cancellationToken) => execute(context, cancellationToken);
    }

    private sealed class ScriptedCallInvoker(
        Func<string, object, Metadata?, object> handler) : CallInvoker
    {
        internal List<string> Methods { get; } = [];

        public override AsyncUnaryCall<TResponse> AsyncUnaryCall<TRequest, TResponse>(
            Method<TRequest, TResponse> method,
            string? host,
            CallOptions options,
            TRequest request)
        {
            Methods.Add(method.Name);
            var response = (TResponse)handler(method.Name, request, options.Headers);
            return new AsyncUnaryCall<TResponse>(
                Task.FromResult(response),
                Task.FromResult(new Metadata()),
                static () => Status.DefaultSuccess,
                static () => [],
                static () => { });
        }

        public override TResponse BlockingUnaryCall<TRequest, TResponse>(
            Method<TRequest, TResponse> method,
            string? host,
            CallOptions options,
            TRequest request) => throw new NotSupportedException();

        public override AsyncClientStreamingCall<TRequest, TResponse> AsyncClientStreamingCall<TRequest, TResponse>(
            Method<TRequest, TResponse> method,
            string? host,
            CallOptions options) => throw new NotSupportedException();

        public override AsyncServerStreamingCall<TResponse> AsyncServerStreamingCall<TRequest, TResponse>(
            Method<TRequest, TResponse> method,
            string? host,
            CallOptions options,
            TRequest request) => throw new NotSupportedException();

        public override AsyncDuplexStreamingCall<TRequest, TResponse> AsyncDuplexStreamingCall<TRequest, TResponse>(
            Method<TRequest, TResponse> method,
            string? host,
            CallOptions options) => throw new NotSupportedException();
    }
}
