using System.Diagnostics;
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

    public static async Task<int> Main(string[] args)
    {
        if (args.Length != 0)
        {
            if (args.Length == 2
                && string.Equals(args[0], "--actual-current-host-isolation", StringComparison.Ordinal))
            {
                return RunActualCurrentHostIsolation(args[1]);
            }

            if (args.Length == 2
                && string.Equals(args[0], "--p10-09-hang-tree-child", StringComparison.Ordinal))
            {
                return await RunHangTreeChildAsync(args[1]);
            }

            if (args.Length == 1
                && string.Equals(args[0], "--p10-09-hang-leaf", StringComparison.Ordinal))
            {
                await Task.Delay(Timeout.InfiniteTimeSpan);
                return 0;
            }

            return 64;
        }

        await SuccessfulLeaseReplaysWithoutDuplicateEffectAsync();
        await HancomSecurityLeaseBridgesOpaqueHandleAsync();
        await HancomBindingLeaseCopiesPinnedPlanBundleAndKeyAsync();
        await ConcurrentDuplicateLeaseIsBusyAsync();
        await StaleLeaseNeverInvokesExecutorAsync();
        await UnfinishedJournalNoEffectFailsWithoutReplayAsync();
        await UnfinishedJournalUnknownEffectNeverReplaysAsync();
        await HardCommandTimeoutRecyclesAndReplaysUnknownAsync();
        await HardCommandTimeoutProvedNoEffectIsRetryableAsync();
        await TerminalWorkerPolicyForcesRecycleAsync();
        await RecycleFailureBecomesUnknownCleanupFailureAsync();
        await StartupRecoveryQuarantinesOnlyOwnedResidueAsync();
        await StartupRecoveryRefusesMixedResidueWithoutPartialMoveAsync();
        await ActualWindowsJobKillsOwnedProcessTreeAsync();
        await FencingDriftIsRejectedWithoutCommitAsync();
        await ArtifactMismatchFailsBeforeExecutorAsync();
        await CommitDigestMismatchReplaysWithoutExecutorAsync();
        await AggregateOutputLimitFailsBeforeUploadAsync();
        await ArtifactUploadIsIdempotentButValidatesEveryStreamAsync();
        await NoWorkAndProfileMismatchFailClosedAsync();
        await IsolationDriftIsRejectedBeforeRpcAsync();
        await DedicatedIsolationRequiresEveryControlAsync();
        await DedicatedIsolationAcceptsCompleteAttestationAsync();
        await PostJobResidueBecomesUnknownOutcomeAsync();
        await StaleWorkspaceResidueIsRejectedAtStartupAsync();
        RejectsUnsafeTransportAndArtifactBoundaries();
        await RejectsUnboundedSupervisorPolicyAsync();
        Console.WriteLine("Windows Agent P10-02/P10-05/P10-06/P10-08/P10-09 staging, isolation, supervision, reconciliation, process-tree recycle, fencing, upload and auth smoke passed (28/28)");
        return 0;
    }

    private static async Task<int> RunHangTreeChildAsync(string processIdsPath)
    {
        Process? leaf = null;
        try
        {
            var startInfo = SelfStartInfo("--p10-09-hang-leaf");
            leaf = Process.Start(startInfo)
                ?? throw new InvalidOperationException("The process-tree leaf did not start.");
            var payload = JsonSerializer.SerializeToUtf8Bytes(new
            {
                schema_version = "hwpx-agent.p10-09-owned-process-tree/v1",
                root_process_id = Environment.ProcessId,
                leaf_process_id = leaf.Id,
            });
            await using (var output = new FileStream(
                processIdsPath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.Read,
                bufferSize: 4_096,
                FileOptions.WriteThrough))
            {
                await output.WriteAsync(payload);
                output.Flush(flushToDisk: true);
            }

            await Task.Delay(Timeout.InfiniteTimeSpan);
            return 0;
        }
        finally
        {
            leaf?.Dispose();
        }
    }

    private static int RunActualCurrentHostIsolation(string policyPath)
    {
        var root = Path.Combine(Path.GetTempPath(), $"hwpx-agent-p10-08-actual-{Guid.NewGuid():N}");
        try
        {
            var fullPolicyPath = Path.GetFullPath(policyPath);
            var policyFile = new FileInfo(fullPolicyPath);
            if (!policyFile.Exists
                || policyFile.Length is <= 0 or > 65_536
                || (policyFile.Attributes & FileAttributes.ReparsePoint) != 0)
            {
                return 65;
            }

            var policyBytes = File.ReadAllBytes(fullPolicyPath);
            var policySha256 = Sha256(policyBytes);
            using var document = JsonDocument.Parse(policyBytes, new JsonDocumentOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 16,
            });
            var top = document.RootElement;
            var target = top.GetProperty("target");
            if (!string.Equals(
                    top.GetProperty("schema_version").GetString(),
                    "hwpx-agent.p10-08-worker-isolation-policy/v1",
                    StringComparison.Ordinal)
                || !string.Equals(
                    top.GetProperty("scope").GetString(),
                    "current_pc_interactive_development",
                    StringComparison.Ordinal))
            {
                return 65;
            }

            var targetProfile = new TargetProfileIdentity
            {
                ProfileId = RequiredString(target, "profile_id"),
                ProductBuild = RequiredString(target, "product_build"),
                Locale = RequiredString(target, "locale"),
                ProcessArchitecture = RequiredString(target, "process_architecture"),
                ExecutableSha256 = RequiredString(target, "executable_sha256"),
                EnvironmentDigest = RequiredString(target, "host_baseline_sha256"),
            };
            var isolationPolicy = new WorkerIsolationPolicyPin(
                RequiredString(top, "policy_id"),
                WorkerIsolationScope.CurrentPcInteractiveDevelopment,
                targetProfile.ProfileId,
                targetProfile.EnvironmentDigest,
                RequiredString(target, "host_isolation_identity_sha256"),
                policySha256,
                ProductionIsolationQualified: false);
            var configuration = new WindowsAgentConfiguration(
                "30000000-0000-4000-8000-000000000080",
                targetProfile,
                RequiredString(target, "capability_registry_sha256"),
                AvailableJobSlots: 1,
                RpcTimeout: TimeSpan.FromSeconds(10),
                WorkerIsolation: isolationPolicy,
                WorkerSupervisor: CurrentSupervisorPolicy());

            Directory.CreateDirectory(root);
            var workspace = new AgentWorkspace(Path.Combine(root, "workspace"));
            var attestor = new CurrentPcWorkerIsolationAttestor(isolationPolicy);
            var preview = attestor.Observe(workspace.RootPath);
            if (!string.Equals(
                    preview.HostIsolationIdentitySha256,
                    isolationPolicy.HostIsolationIdentitySha256,
                    StringComparison.Ordinal))
            {
                Console.Error.WriteLine(
                    $"HANCOM_ISOLATION_IDENTITY_MISMATCH actual_sha256={preview.HostIsolationIdentitySha256}");
                return 2;
            }

            var guard = new WorkerIsolationGuard(configuration, workspace, attestor);
            var before = guard.VerifyBeforeLease();
            guard.VerifyAfterJob(before);

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                schema_version = "hwpx-agent.p10-08-current-host-live-observation/v1",
                state = "pass_current_pc_development_only",
                policy_id = isolationPolicy.PolicyId,
                policy_manifest_sha256 = policySha256,
                target_profile_id = targetProfile.ProfileId,
                host_baseline_sha256 = targetProfile.EnvironmentDigest,
                probe_complete = before.ProbeComplete,
                windows_host = before.WindowsHost,
                interactive_session = before.InteractiveSession,
                session_id = before.SessionId,
                identity_sha256 = before.IdentitySha256,
                window_station_sha256 = before.WindowStationSha256,
                desktop_sha256 = before.DesktopSha256,
                profile_root_sha256 = before.ProfileRootSha256,
                temp_root_sha256 = before.TempRootSha256,
                host_isolation_identity_sha256 = before.HostIsolationIdentitySha256,
                private_job_workspace = before.PrivateJobWorkspace,
                target_process_count = before.TargetProcessCount,
                raw_identity_stored = before.RawIdentityStored,
                dedicated_identity_and_profile = before.DedicatedIdentityAndProfile,
                private_window_station = before.PrivateWindowStation,
                os_network_default_deny = before.OsNetworkDefaultDeny,
                clipboard_isolated = before.ClipboardIsolated,
                profile_residue_clean = before.ProfileResidueClean,
                recovery_residue_clean = before.RecoveryResidueClean,
                printer_residue_clean = before.PrinterResidueClean,
                production_isolation_qualified = isolationPolicy.ProductionIsolationQualified,
                raw_document_text_present = false,
                user_document_scanned = false,
            }));
            return 0;
        }
        catch
        {
            Console.Error.WriteLine("HANCOM_ISOLATION_AUDIT_FAILED");
            return 2;
        }
        finally
        {
            if (Directory.Exists(root))
            {
                DeleteActualProbeRoot(root);
            }
        }
    }

    private static string RequiredString(JsonElement element, string propertyName)
    {
        var value = element.GetProperty(propertyName).GetString();
        return string.IsNullOrWhiteSpace(value)
            ? throw new InvalidDataException("Required policy value is missing.")
            : value;
    }

    private static void DeleteActualProbeRoot(string path)
    {
        var fullPath = Path.GetFullPath(path);
        var tempPrefix = Path.GetFullPath(Path.GetTempPath()).TrimEnd(
            Path.DirectorySeparatorChar,
            Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!fullPath.StartsWith(tempPrefix, StringComparison.OrdinalIgnoreCase)
            || !Path.GetFileName(fullPath).StartsWith(
                "hwpx-agent-p10-08-actual-",
                StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Actual isolation probe cleanup escaped its private root.");
        }

        DeleteTreeWithoutFollowingReparsePoints(fullPath);
    }

    private static void DeleteTreeWithoutFollowingReparsePoints(string directory)
    {
        foreach (var entry in Directory.EnumerateFileSystemEntries(directory))
        {
            var attributes = File.GetAttributes(entry);
            if ((attributes & FileAttributes.ReparsePoint) != 0)
            {
                if ((attributes & FileAttributes.Directory) != 0)
                {
                    Directory.Delete(entry, recursive: false);
                }
                else
                {
                    File.Delete(entry);
                }

                continue;
            }

            if ((attributes & FileAttributes.Directory) != 0)
            {
                DeleteTreeWithoutFollowingReparsePoints(entry);
            }
            else
            {
                if ((attributes & FileAttributes.ReadOnly) != 0)
                {
                    File.SetAttributes(entry, attributes & ~FileAttributes.ReadOnly);
                }

                File.Delete(entry);
            }
        }

        Directory.Delete(directory, recursive: false);
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
            environment.Workspace,
            environment.IsolationAttestor);
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

    private static async Task UnfinishedJournalNoEffectFailsWithoutReplayAsync()
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
            && recovered.TerminalState == ExecutionState.Failed,
            "unfinished no-effect claim was not safely classified as failed");
        Require(executorCalls == 0, "unfinished claim was re-executed");
    }

    private static async Task UnfinishedJournalUnknownEffectNeverReplaysAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("unfinished-unknown");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000021",
            "20000000-0000-4000-8000-000000000021",
            31);
        var abandoned = await environment.Workspace.Journal.ClaimAsync(assignment, CancellationToken.None);
        Require(abandoned.Disposition == JournalClaimDisposition.New, "unknown fixture claim was not new");
        await abandoned.Ownership!.DisposeAsync();

        AgentExecutionReceipt? committed = null;
        var executorCalls = 0;
        var recycleCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "CommitExecution" => CaptureCommit(
                    (AgentCommitRequest)request,
                    receipt => committed = receipt),
                _ => throw new InvalidOperationException("unfinished unknown recovery executed work"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor((_, _) =>
        {
            executorCalls++;
            throw new InvalidOperationException("unknown abandoned claim reached executor");
        })
        {
            ReconcileHandler = (candidate, _) => Task.FromResult(Observation(
                candidate,
                effectStarted: true,
                outputPresent: true,
                actionTracePresent: true,
                actionTraceTerminal: false)),
            RecycleHandler = (candidate, reason, _) =>
            {
                recycleCalls++;
                return Task.FromResult(RecycleReceipt(candidate, reason));
            },
        };

        var result = await environment.CreateService(client, executor).RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Replayed
            && result.TerminalState == ExecutionState.UnknownOutcome,
            "unfinished effectful claim was not classified unknown");
        Require(executorCalls == 0 && recycleCalls == 1, "unfinished unknown claim replayed or skipped recycle");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.UnknownOutcome
            && committed.Diagnostic.EffectUnknown
            && !committed.Diagnostic.Retryable,
            "unfinished unknown receipt lost fail-closed diagnostics");
    }

    private static async Task HardCommandTimeoutRecyclesAndReplaysUnknownAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("hard-timeout-unknown");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000022",
            "20000000-0000-4000-8000-000000000022",
            32);
        assignment.ResourceLimits.CommandTimeoutSeconds = 1;
        assignment.ResourceLimits.JobTimeoutSeconds = 5;
        var executorCalls = 0;
        var cancellationCalls = 0;
        var recycleCalls = 0;
        var committed = new List<byte[]>();
        var never = new TaskCompletionSource<AgentJobResult>(TaskCreationOptions.RunContinuationsAsynchronously);
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, committed),
                _ => throw new InvalidOperationException("unexpected timeout RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor((_, _) =>
        {
            executorCalls++;
            return never.Task;
        })
        {
            CancellationHandler = (_, _) =>
            {
                cancellationCalls++;
                return Task.CompletedTask;
            },
            ReconcileHandler = (candidate, _) => Task.FromResult(Observation(
                candidate,
                effectStarted: true,
                outputPresent: false,
                actionTracePresent: true,
                actionTraceTerminal: false)),
            RecycleHandler = (candidate, reason, _) =>
            {
                recycleCalls++;
                Require(reason == WorkerRecycleReason.CommandTimeout, "hard timeout recycle reason drifted");
                never.TrySetCanceled();
                return Task.FromResult(RecycleReceipt(candidate, reason));
            },
        };
        var service = environment.CreateService(client, executor);

        var first = await service.RunOnceAsync(CancellationToken.None);
        var second = await service.RunOnceAsync(CancellationToken.None);
        Require(first.Disposition == AgentRunDisposition.UnknownOutcome
            && first.TerminalState == ExecutionState.UnknownOutcome
            && first.ExecutorInvoked,
            "hard timeout did not become unknown outcome");
        Require(second.Disposition == AgentRunDisposition.Replayed
            && !second.ExecutorInvoked,
            "hard timeout terminal receipt was not replayed");
        Require(executorCalls == 1 && cancellationCalls == 1 && recycleCalls == 1,
            "hard timeout duplicated execution or skipped containment");
        Require(committed.Count == 2
            && committed[0].AsSpan().SequenceEqual(committed[1]),
            "hard timeout replay receipt drifted");
        var receipt = AgentExecutionReceipt.Parser.ParseFrom(committed[0]);
        Require(receipt.Diagnostic.ErrorCode == BridgeErrorCode.Timeout
            && receipt.Diagnostic.EffectUnknown
            && !receipt.Diagnostic.Retryable,
            "hard timeout receipt allowed unsafe retry");
    }

    private static async Task HardCommandTimeoutProvedNoEffectIsRetryableAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("hard-timeout-no-effect");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000023",
            "20000000-0000-4000-8000-000000000023",
            33);
        assignment.ResourceLimits.CommandTimeoutSeconds = 1;
        assignment.ResourceLimits.JobTimeoutSeconds = 5;
        AgentExecutionReceipt? committed = null;
        var never = new TaskCompletionSource<AgentJobResult>(TaskCreationOptions.RunContinuationsAsynchronously);
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CaptureCommit(
                    (AgentCommitRequest)request,
                    receipt => committed = receipt),
                _ => throw new InvalidOperationException("unexpected no-effect timeout RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor((_, _) => never.Task)
        {
            ReconcileHandler = (candidate, _) => Task.FromResult(Observation(
                candidate,
                effectStarted: false,
                outputPresent: false,
                actionTracePresent: false,
                actionTraceTerminal: false)),
            RecycleHandler = (candidate, reason, _) =>
            {
                never.TrySetCanceled();
                return Task.FromResult(RecycleReceipt(candidate, reason));
            },
        };

        var result = await environment.CreateService(client, executor).RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Failed
            && result.TerminalState == ExecutionState.Failed,
            "proved no-effect timeout was not safely retryable");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.Timeout
            && !committed.Diagnostic.EffectUnknown
            && committed.Diagnostic.Retryable,
            "proved no-effect timeout lost retryable evidence");
    }

    private static async Task TerminalWorkerPolicyForcesRecycleAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("policy-recycle");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000024",
            "20000000-0000-4000-8000-000000000024",
            34);
        var configuration = environment.Configuration with
        {
            WorkerSupervisor = environment.Configuration.WorkerSupervisor with
            {
                MaximumJobsPerWorker = 1,
            },
        };
        var recycleCalls = 0;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => Commit((AgentCommitRequest)request, []),
                _ => throw new InvalidOperationException("unexpected policy recycle RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            await using var output = context.CreateOutput("output_0024");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob("output_0024", "fixture-output-policy-recycle");
        })
        {
            RecycleHandler = (candidate, reason, _) =>
            {
                recycleCalls++;
                Require(reason == WorkerRecycleReason.PolicyLimit, "policy recycle reason drifted");
                return Task.FromResult(RecycleReceipt(candidate, reason));
            },
        };
        var service = new WindowsAgentService(
            configuration,
            client,
            environment.Store,
            executor,
            environment.Workspace,
            environment.IsolationAttestor);

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.Succeeded && recycleCalls == 1,
            "terminal job quota did not recycle the worker");
    }

    private static async Task RecycleFailureBecomesUnknownCleanupFailureAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("recycle-failure");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000025",
            "20000000-0000-4000-8000-000000000025",
            35);
        var configuration = environment.Configuration with
        {
            WorkerSupervisor = environment.Configuration.WorkerSupervisor with
            {
                MaximumJobsPerWorker = 1,
            },
        };
        AgentExecutionReceipt? committed = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CaptureCommit(
                    (AgentCommitRequest)request,
                    receipt => committed = receipt),
                _ => throw new InvalidOperationException("unexpected recycle failure RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor(async (context, cancellationToken) =>
        {
            await using var output = context.CreateOutput("output_0025");
            await output.WriteAsync(OutputBytes, cancellationToken);
            return SuccessfulJob("output_0025", "fixture-output-recycle-failure");
        })
        {
            RecycleHandler = (_, _, _) => throw new InvalidOperationException("synthetic recycle failure"),
        };
        var service = new WindowsAgentService(
            configuration,
            client,
            environment.Store,
            executor,
            environment.Workspace,
            environment.IsolationAttestor);

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.UnknownOutcome,
            "recycle failure was not fail-closed");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.CleanupFailed
            && committed.Diagnostic.EffectUnknown
            && !committed.Diagnostic.Retryable,
            "recycle failure receipt lost cleanup diagnostics");
    }

    private static async Task StartupRecoveryQuarantinesOnlyOwnedResidueAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("startup-recovery");
        var executionId = "20000000-0000-4000-8000-000000000026";
        var residue = Path.Combine(environment.Workspace.RootPath, "sandboxes", $"job-{executionId}");
        Directory.CreateDirectory(residue);
        await File.WriteAllTextAsync(
            Path.Combine(residue, ".hwpx-agent-sandbox"),
            executionId,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        var payload = Path.Combine(residue, "retained.bin");
        await File.WriteAllBytesAsync(payload, [1, 2, 3, 4]);
        var recoveryCalls = 0;
        var invoker = new ScriptedCallInvoker((method, _, headers) =>
        {
            RequireAuthorization(headers);
            return method == "AcquireLease"
                ? new AgentLeaseResponse { Disposition = LeaseDisposition.NoWork }
                : throw new InvalidOperationException("unexpected startup recovery RPC");
        });
        await using var client = AuthenticatedClient(invoker);
        var executor = new DelegatingExecutor((_, _) =>
            throw new InvalidOperationException("startup recovery reached executor"))
        {
            StartupRecoveryHandler = _ =>
            {
                recoveryCalls++;
                return Task.FromResult(StartupReceipt());
            },
        };

        var service = await WindowsAgentService.CreateRecoveredAsync(
            environment.Configuration,
            client,
            environment.Store,
            executor,
            environment.Workspace,
            environment.IsolationAttestor,
            CancellationToken.None);
        var result = await service.RunOnceAsync(CancellationToken.None);
        var quarantine = Path.Combine(environment.Workspace.RootPath, "quarantine");
        var retained = Directory.EnumerateFiles(
            quarantine,
            "retained.bin",
            SearchOption.AllDirectories).Single();
        Require(result.Disposition == AgentRunDisposition.NoWork && recoveryCalls == 1,
            "startup recovery did not complete before lease acquisition");
        Require(!Directory.Exists(residue)
            && (await File.ReadAllBytesAsync(retained)).SequenceEqual(new byte[] { 1, 2, 3, 4 }),
            "startup recovery deleted or altered owned residue instead of quarantining it");
    }

    private static async Task ActualWindowsJobKillsOwnedProcessTreeAsync()
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException(
                "P10-09 process-tree evidence requires a Windows host.");
        }

        await using var environment = await TestEnvironment.CreateAsync("actual-process-tree");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000027",
            "20000000-0000-4000-8000-000000000027",
            37);
        var processIdsPath = Path.Combine(environment.Root, "owned process ids.json");
        var executablePath = Environment.ProcessPath
            ?? throw new InvalidOperationException("The smoke executable path is unavailable.");
        var startInfo = SelfStartInfo("--p10-09-hang-tree-child", processIdsPath);
        RequireThrows<AgentProtocolException>(() =>
            WindowsOwnedWorkerProcess.Start(startInfo, Digest('0')));
        Require(!File.Exists(processIdsPath),
            "a digest-mismatched worker process was launched");
        await using var owned = WindowsOwnedWorkerProcess.Start(
            startInfo,
            Sha256File(executablePath));

        var processIds = await ReadOwnedProcessIdsAsync(processIdsPath, TimeSpan.FromSeconds(10));
        Require(processIds.RootProcessId == owned.InitialProcessId,
            "owned root process identity drifted");
        Require(ProcessIsRunning(processIds.RootProcessId)
            && ProcessIsRunning(processIds.LeafProcessId),
            "owned process tree did not become live");

        using var recycleTimeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var receipt = await owned.RecycleAsync(
            assignment,
            WorkerRecycleReason.PolicyLimit,
            recycleTimeout.Token);
        AgentValidation.ValidateRecycleReceipt(
            receipt,
            assignment,
            WorkerRecycleReason.PolicyLimit);
        await WaitForProcessesToExitAsync(
            [processIds.RootProcessId, processIds.LeafProcessId],
            TimeSpan.FromSeconds(5));
        Require(!ProcessIsRunning(processIds.RootProcessId)
            && !ProcessIsRunning(processIds.LeafProcessId),
            "Windows job recycle left an owned descendant running");
    }

    private static async Task StartupRecoveryRefusesMixedResidueWithoutPartialMoveAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("mixed-startup-residue");
        var validExecutionId = "20000000-0000-4000-8000-000000000028";
        var validResidue = Path.Combine(
            environment.Workspace.RootPath,
            "sandboxes",
            $"job-{validExecutionId}");
        Directory.CreateDirectory(validResidue);
        await File.WriteAllTextAsync(
            Path.Combine(validResidue, ".hwpx-agent-sandbox"),
            validExecutionId,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        var invalidResidue = Path.Combine(
            environment.Workspace.RootPath,
            "sandboxes",
            "job-untrusted-residue");
        Directory.CreateDirectory(invalidResidue);
        var invoker = new ScriptedCallInvoker((_, _, _) =>
            throw new InvalidOperationException("mixed residue reached the control plane"));
        await using var client = AuthenticatedClient(invoker);

        var error = await CaptureProtocolErrorAsync(() => WindowsAgentService.CreateRecoveredAsync(
            environment.Configuration,
            client,
            environment.Store,
            new DelegatingExecutor((_, _) =>
                throw new InvalidOperationException("mixed residue reached executor")),
            environment.Workspace,
            environment.IsolationAttestor,
            CancellationToken.None));
        Require(error == AgentProtocolError.CleanupResidue,
            "mixed startup residue was not rejected");
        Require(Directory.Exists(validResidue)
            && Directory.Exists(invalidResidue)
            && invoker.Methods.Count == 0,
            "mixed startup residue caused a partial move or outbound RPC");
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
            WorkerIsolation: CurrentIsolationPolicy(
                "hancom-hangul-2020-secondary",
                Digest('b')),
            WorkerSupervisor: CurrentSupervisorPolicy(),
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

    private static async Task RejectsUnboundedSupervisorPolicyAsync()
    {
        var valid = CurrentSupervisorPolicy();
        foreach (var invalid in new[]
        {
            valid with { CooperativeStopTimeoutSeconds = 0 },
            valid with { ReconciliationTimeoutSeconds = 0 },
            valid with { RecycleTimeoutSeconds = 61 },
            valid with { MaximumJobsPerWorker = 0 },
            valid with { MaximumPrivateMemoryBytes = 17_179_869_185 },
        })
        {
            RequireThrows<ArgumentException>(() =>
                AgentValidation.ValidateWorkerSupervisorPolicy(invalid));
        }

        var assignment = new LeaseAssignment
        {
            ExecutionId = "20000000-0000-4000-8000-000000000029",
        };
        foreach (var contradictory in new[]
        {
            Observation(
                assignment,
                effectStarted: false,
                outputPresent: false,
                actionTracePresent: false,
                actionTraceTerminal: false) with
            {
                OutputDigestVerified = true,
            },
            Observation(
                assignment,
                effectStarted: false,
                outputPresent: false,
                actionTracePresent: false,
                actionTraceTerminal: true),
            Observation(
                assignment,
                effectStarted: false,
                outputPresent: false,
                actionTracePresent: true,
                actionTraceTerminal: true,
                readbackVerified: true),
        })
        {
            var error = CaptureProtocolError(() =>
                AgentValidation.ValidateReconciliationObservation(contradictory, assignment));
            Require(error == AgentProtocolError.ReconciliationFailed,
                "contradictory reconciliation evidence was accepted");
        }

        await using var environment = await TestEnvironment.CreateAsync("equal-deadlines");
        var equalDeadlines = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000030",
            "20000000-0000-4000-8000-000000000030",
            39);
        equalDeadlines.ResourceLimits.CommandTimeoutSeconds = 30;
        equalDeadlines.ResourceLimits.JobTimeoutSeconds = 30;
        var limitsError = CaptureProtocolError(() => AgentValidation.ValidateAssignment(
            equalDeadlines,
            environment.Configuration,
            nowUnixMilliseconds: 1_800_000_000_000));
        Require(limitsError == AgentProtocolError.InvalidLimits,
            "equal command and job deadlines were accepted");
    }

    private static async Task IsolationDriftIsRejectedBeforeRpcAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("isolation-drift");
        var invoker = new ScriptedCallInvoker((_, _, _) =>
            throw new InvalidOperationException("isolation drift reached the control plane"));
        await using var client = AuthenticatedClient(invoker);
        var drifted = PassingIsolationObservation(environment.Configuration.WorkerIsolation) with
        {
            HostBaselineSha256 = Digest('f'),
        };

        var error = CaptureProtocolError(() => _ = new WindowsAgentService(
            environment.Configuration,
            client,
            environment.Store,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("executor invoked")),
            environment.Workspace,
            new FixedIsolationAttestor(drifted)));
        Require(error == AgentProtocolError.IsolationNotReady, "host baseline drift was not isolation failure");
        Require(invoker.Methods.Count == 0, "host baseline drift made an outbound RPC");
    }

    private static async Task DedicatedIsolationRequiresEveryControlAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("dedicated-denied");
        var policy = environment.Configuration.WorkerIsolation with
        {
            PolicyId = "isolation.dedicated_v1",
            Scope = WorkerIsolationScope.DedicatedWorkerImage,
            ProductionIsolationQualified = true,
        };
        var configuration = environment.Configuration with { WorkerIsolation = policy };
        var invoker = new ScriptedCallInvoker((_, _, _) =>
            throw new InvalidOperationException("incomplete dedicated isolation reached the control plane"));
        await using var client = AuthenticatedClient(invoker);
        var incomplete = PassingIsolationObservation(policy, dedicated: true) with
        {
            ClipboardIsolated = false,
        };

        var error = CaptureProtocolError(() => _ = new WindowsAgentService(
            configuration,
            client,
            environment.Store,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("executor invoked")),
            environment.Workspace,
            new FixedIsolationAttestor(incomplete)));
        Require(error == AgentProtocolError.IsolationNotReady, "missing clipboard isolation was accepted");
        Require(invoker.Methods.Count == 0, "incomplete dedicated isolation made an outbound RPC");

        RequireThrows<ArgumentException>(() => AgentValidation.ValidateConfiguration(
            environment.Configuration with
            {
                WorkerIsolation = environment.Configuration.WorkerIsolation with
                {
                    ProductionIsolationQualified = true,
                },
            }));
    }

    private static async Task DedicatedIsolationAcceptsCompleteAttestationAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("dedicated-pass");
        var policy = environment.Configuration.WorkerIsolation with
        {
            PolicyId = "isolation.dedicated_v1",
            Scope = WorkerIsolationScope.DedicatedWorkerImage,
            ProductionIsolationQualified = true,
        };
        var configuration = environment.Configuration with { WorkerIsolation = policy };
        var invoker = new ScriptedCallInvoker((method, _, headers) =>
        {
            RequireAuthorization(headers);
            return method == "AcquireLease"
                ? new AgentLeaseResponse { Disposition = LeaseDisposition.NoWork }
                : throw new InvalidOperationException("unexpected RPC");
        });
        await using var client = AuthenticatedClient(invoker);
        var service = new WindowsAgentService(
            configuration,
            client,
            environment.Store,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("executor invoked")),
            environment.Workspace,
            new FixedIsolationAttestor(PassingIsolationObservation(policy, dedicated: true)));

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.NoWork, "complete dedicated attestation was rejected");
        Require(invoker.Methods.SequenceEqual(["AcquireLease"]), "dedicated no-work request drifted");
    }

    private static async Task PostJobResidueBecomesUnknownOutcomeAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("post-residue");
        var assignment = environment.CreateAssignment(
            "10000000-0000-4000-8000-000000000018",
            "20000000-0000-4000-8000-000000000018",
            28);
        AgentExecutionReceipt? committed = null;
        var invoker = new ScriptedCallInvoker((method, request, headers) =>
        {
            RequireAuthorization(headers);
            return method switch
            {
                "AcquireLease" => Assigned(assignment),
                "Heartbeat" => CurrentHeartbeat(),
                "CommitExecution" => CaptureCommit(
                    (AgentCommitRequest)request,
                    receipt => committed = receipt),
                _ => throw new InvalidOperationException("unexpected RPC"),
            };
        });
        await using var client = AuthenticatedClient(invoker);
        var passing = PassingIsolationObservation(environment.Configuration.WorkerIsolation);
        var attestor = new SequenceIsolationAttestor(
            passing,
            passing,
            passing with { TargetProcessCount = 1 });
        var service = new WindowsAgentService(
            environment.Configuration,
            client,
            environment.Store,
            new DelegatingExecutor(async (context, cancellationToken) =>
            {
                await using var output = context.CreateOutput("output_0018");
                await output.WriteAsync(OutputBytes, cancellationToken);
                return SuccessfulJob("output_0018", "fixture-output-residue");
            }),
            environment.Workspace,
            attestor);

        var result = await service.RunOnceAsync(CancellationToken.None);
        Require(result.Disposition == AgentRunDisposition.UnknownOutcome
            && result.ExecutorInvoked, "post-job residue did not become unknown outcome");
        Require(committed?.Diagnostic?.ErrorCode == BridgeErrorCode.CleanupFailed
            && committed.Diagnostic.EffectUnknown, "cleanup failure receipt was not fail-closed");
        Require(environment.SandboxDirectories().Count == 0, "post-residue fixture left a sandbox");
    }

    private static async Task StaleWorkspaceResidueIsRejectedAtStartupAsync()
    {
        await using var environment = await TestEnvironment.CreateAsync("stale-residue");
        var residue = Path.Combine(environment.Workspace.RootPath, "sandboxes", "job-stale-residue");
        Directory.CreateDirectory(residue);
        var invoker = new ScriptedCallInvoker((_, _, _) =>
            throw new InvalidOperationException("stale residue reached the control plane"));
        await using var client = AuthenticatedClient(invoker);

        var error = CaptureProtocolError(() => _ = new WindowsAgentService(
            environment.Configuration,
            client,
            environment.Store,
            new DelegatingExecutor((_, _) => throw new InvalidOperationException("executor invoked")),
            environment.Workspace,
            environment.IsolationAttestor));
        Require(error == AgentProtocolError.CleanupResidue, "stale sandbox residue was accepted");
        Require(invoker.Methods.Count == 0, "stale sandbox residue made an outbound RPC");
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

    private static ProcessStartInfo SelfStartInfo(params string[] arguments)
    {
        var processPath = Environment.ProcessPath
            ?? throw new InvalidOperationException("The smoke process path is unavailable.");
        var startInfo = new ProcessStartInfo
        {
            FileName = processPath,
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = AppContext.BaseDirectory,
        };
        if (string.Equals(
                Path.GetFileNameWithoutExtension(processPath),
                "dotnet",
                StringComparison.OrdinalIgnoreCase))
        {
            startInfo.ArgumentList.Add(typeof(Program).Assembly.Location);
        }

        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        return startInfo;
    }

    private static string Sha256File(string path)
    {
        using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 65_536,
            FileOptions.SequentialScan);
        return Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(stream));
    }

    private static async Task<OwnedProcessIds> ReadOwnedProcessIdsAsync(
        string path,
        TimeSpan timeout)
    {
        var elapsed = Stopwatch.StartNew();
        while (elapsed.Elapsed < timeout)
        {
            try
            {
                if (File.Exists(path))
                {
                    var bytes = await File.ReadAllBytesAsync(path);
                    using var document = JsonDocument.Parse(bytes);
                    var root = document.RootElement;
                    if (string.Equals(
                            root.GetProperty("schema_version").GetString(),
                            "hwpx-agent.p10-09-owned-process-tree/v1",
                            StringComparison.Ordinal))
                    {
                        return new OwnedProcessIds(
                            root.GetProperty("root_process_id").GetInt32(),
                            root.GetProperty("leaf_process_id").GetInt32());
                    }
                }
            }
            catch (IOException)
            {
                // The child may still be publishing its bounded process receipt.
            }
            catch (JsonException)
            {
                // The file was observed between CreateNew and its durable flush.
            }

            await Task.Delay(TimeSpan.FromMilliseconds(25));
        }

        throw new TimeoutException("The owned process tree did not publish its process receipt.");
    }

    private static async Task WaitForProcessesToExitAsync(int[] processIds, TimeSpan timeout)
    {
        var elapsed = Stopwatch.StartNew();
        while (elapsed.Elapsed < timeout && processIds.Any(ProcessIsRunning))
        {
            await Task.Delay(TimeSpan.FromMilliseconds(25));
        }
    }

    private static bool ProcessIsRunning(int processId)
    {
        try
        {
            using var process = Process.GetProcessById(processId);
            return !process.HasExited;
        }
        catch (ArgumentException)
        {
            return false;
        }
    }

    private sealed record OwnedProcessIds(int RootProcessId, int LeafProcessId);

    private static WorkerIsolationPolicyPin CurrentIsolationPolicy(
        string targetProfileId,
        string hostBaselineSha256) =>
        new(
            "isolation.current_pc_v1",
            WorkerIsolationScope.CurrentPcInteractiveDevelopment,
            targetProfileId,
            hostBaselineSha256,
            Digest('6'),
            Digest('e'),
            ProductionIsolationQualified: false);

    private static WorkerSupervisorPolicyPin CurrentSupervisorPolicy() =>
        new(
            "supervisor.current_pc_local_v1",
            CooperativeStopTimeoutSeconds: 2,
            ReconciliationTimeoutSeconds: 2,
            RecycleTimeoutSeconds: 2,
            MaximumJobsPerWorker: 25,
            MaximumPrivateMemoryBytes: 536_870_912);

    private static WorkerStartupRecoveryReceipt StartupReceipt() =>
        new(
            ProbeComplete: true,
            OwnedProcessCountBefore: 0,
            OwnedProcessCountAfter: 0,
            ProcessTreeTerminated: true,
            FreshWorkerRequired: true,
            RawProcessCommandLineStored: false,
            SafeDetailSha256: Digest('1'));

    private static WorkerRecycleReceipt RecycleReceipt(
        LeaseAssignment assignment,
        WorkerRecycleReason reason) =>
        new(
            assignment.ExecutionId,
            AgentValidation.ComputeSha256(assignment),
            reason,
            ProcessTreeTerminated: true,
            FreshWorkerRequired: true,
            RawProcessCommandLineStored: false,
            SafeDetailSha256: Digest('2'));

    private static WorkerReconciliationObservation Observation(
        LeaseAssignment assignment,
        bool effectStarted,
        bool outputPresent,
        bool actionTracePresent,
        bool actionTraceTerminal,
        bool readbackVerified = false,
        uint completedJobs = 0,
        ulong privateMemoryBytes = 67_108_864) =>
        new(
            assignment.ExecutionId,
            AgentValidation.ComputeSha256(assignment),
            ProbeComplete: true,
            WorkerProcessRunning: true,
            EffectStarted: effectStarted,
            SourceUnchanged: true,
            OutputPresent: outputPresent,
            OutputDigestVerified: outputPresent,
            ActionTracePresent: actionTracePresent,
            ActionTraceTerminal: actionTraceTerminal,
            ReadbackVerified: readbackVerified,
            CompletedJobs: completedJobs,
            PrivateMemoryBytes: privateMemoryBytes,
            RawDocumentContentStored: false);

    private static WorkerIsolationObservation PassingIsolationObservation(
        WorkerIsolationPolicyPin policy,
        bool dedicated = false,
        uint targetProcessCount = 0) =>
        new(
            policy.PolicyId,
            policy.TargetProfileId,
            policy.HostBaselineSha256,
            policy.WorkerImageManifestSha256,
            ProbeComplete: true,
            WindowsHost: true,
            InteractiveSession: true,
            SessionId: 1,
            IdentitySha256: Digest('1'),
            WindowStationSha256: Digest('2'),
            DesktopSha256: Digest('3'),
            ProfileRootSha256: Digest('4'),
            TempRootSha256: Digest('5'),
            HostIsolationIdentitySha256: policy.HostIsolationIdentitySha256,
            PrivateJobWorkspace: true,
            DedicatedIdentityAndProfile: dedicated,
            PrivateWindowStation: dedicated,
            OsNetworkDefaultDeny: dedicated,
            ClipboardIsolated: dedicated,
            ProfileResidueClean: dedicated,
            RecoveryResidueClean: dedicated,
            PrinterResidueClean: dedicated,
            TargetProcessCount: targetProcessCount,
            RawIdentityStored: false);

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

    private static AgentProtocolError CaptureProtocolError(Action action)
    {
        try
        {
            action();
        }
        catch (AgentProtocolException error)
        {
            return error.Error;
        }

        throw new InvalidOperationException("Expected AgentProtocolException.");
    }

    private static async Task<AgentProtocolError> CaptureProtocolErrorAsync(Func<Task> action)
    {
        try
        {
            await action();
        }
        catch (AgentProtocolException error)
        {
            return error.Error;
        }

        throw new InvalidOperationException("Expected AgentProtocolException.");
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
            IWorkerIsolationAttestor isolationAttestor,
            ArtifactRef input,
            ArtifactRef plan,
            ArtifactRef validation)
        {
            Root = root;
            Store = store;
            Workspace = workspace;
            Configuration = configuration;
            IsolationAttestor = isolationAttestor;
            Input = input;
            Plan = plan;
            Validation = validation;
        }

        internal string Root { get; }

        internal ContentAddressedArtifactStore Store { get; }

        internal AgentWorkspace Workspace { get; }

        internal WindowsAgentConfiguration Configuration { get; }

        internal IWorkerIsolationAttestor IsolationAttestor { get; }

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
                WorkerIsolation: CurrentIsolationPolicy(
                    "hancom-hangul-2020-secondary",
                    Digest('b')),
                WorkerSupervisor: CurrentSupervisorPolicy(),
                HancomSecurityModule: new HancomSecurityModulePin(
                    "FilePathCheckerModuleExample",
                    Digest('d')));
            var isolationAttestor = new FixedIsolationAttestor(
                PassingIsolationObservation(configuration.WorkerIsolation));
            return new TestEnvironment(
                root,
                store,
                workspace,
                configuration,
                isolationAttestor,
                input,
                plan,
                validation);
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
            ISupervisedAgentJobExecutor executor) =>
            new(Configuration, client, Store, executor, Workspace, IsolationAttestor);

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
        Func<AgentJobContext, CancellationToken, Task<AgentJobResult>> execute)
        : ISupervisedAgentJobExecutor
    {
        private readonly object sync = new();
        private readonly Dictionary<string, AgentJobResult> completed = new(StringComparer.Ordinal);
        private readonly HashSet<string> started = new(StringComparer.Ordinal);

        internal Func<CancellationToken, Task<WorkerStartupRecoveryReceipt>>? StartupRecoveryHandler
        {
            get;
            init;
        }

        internal Func<string, CancellationToken, Task>? CancellationHandler { get; init; }

        internal Func<LeaseAssignment, CancellationToken, Task<WorkerReconciliationObservation>>?
            ReconcileHandler
        { get; init; }

        internal Func<LeaseAssignment, WorkerRecycleReason, CancellationToken, Task<WorkerRecycleReceipt>>?
            RecycleHandler
        { get; init; }

        public async Task<AgentJobResult> ExecuteAsync(
            AgentJobContext context,
            CancellationToken cancellationToken)
        {
            lock (sync)
            {
                started.Add(context.Assignment.ExecutionId);
            }

            var result = await execute(context, cancellationToken);
            lock (sync)
            {
                completed[context.Assignment.ExecutionId] = result;
            }

            return result;
        }

        public Task<WorkerStartupRecoveryReceipt> RecoverStartupAsync(
            CancellationToken cancellationToken) => StartupRecoveryHandler is null
                ? Task.FromResult(StartupReceipt())
                : StartupRecoveryHandler(cancellationToken);

        public Task RequestCancellationAsync(
            string executionId,
            CancellationToken cancellationToken) => CancellationHandler is null
                ? Task.CompletedTask
                : CancellationHandler(executionId, cancellationToken);

        public Task<WorkerReconciliationObservation> ReconcileAsync(
            LeaseAssignment assignment,
            CancellationToken cancellationToken)
        {
            if (ReconcileHandler is not null)
            {
                return ReconcileHandler(assignment, cancellationToken);
            }

            AgentJobResult? result;
            bool executionStarted;
            lock (sync)
            {
                completed.TryGetValue(assignment.ExecutionId, out result);
                executionStarted = started.Contains(assignment.ExecutionId);
            }

            var succeeded = result?.TerminalState == ExecutionState.Succeeded;
            return Task.FromResult(new WorkerReconciliationObservation(
                assignment.ExecutionId,
                AgentValidation.ComputeSha256(assignment),
                ProbeComplete: true,
                WorkerProcessRunning: true,
                EffectStarted: executionStarted,
                SourceUnchanged: true,
                OutputPresent: succeeded && result!.Artifacts.Count != 0,
                OutputDigestVerified: succeeded,
                ActionTracePresent: result is not null,
                ActionTraceTerminal: result is not null,
                ReadbackVerified: succeeded,
                CompletedJobs: result is null ? 0u : 1u,
                PrivateMemoryBytes: 67_108_864,
                RawDocumentContentStored: false));
        }

        public Task<WorkerRecycleReceipt> RecycleAsync(
            LeaseAssignment assignment,
            WorkerRecycleReason reason,
            CancellationToken cancellationToken) => RecycleHandler is null
                ? Task.FromResult(RecycleReceipt(assignment, reason))
                : RecycleHandler(assignment, reason, cancellationToken);
    }

    private sealed class FixedIsolationAttestor(WorkerIsolationObservation observation)
        : IWorkerIsolationAttestor
    {
        public WorkerIsolationObservation Observe(string workspaceRoot)
        {
            Require(Directory.Exists(workspaceRoot), "isolation attestor received a missing workspace");
            return observation;
        }
    }

    private sealed class SequenceIsolationAttestor(params WorkerIsolationObservation[] observations)
        : IWorkerIsolationAttestor
    {
        private int index;

        public WorkerIsolationObservation Observe(string workspaceRoot)
        {
            Require(Directory.Exists(workspaceRoot), "isolation attestor received a missing workspace");
            if (index >= observations.Length)
            {
                throw new InvalidOperationException("isolation observation sequence exhausted");
            }

            return observations[index++];
        }
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
