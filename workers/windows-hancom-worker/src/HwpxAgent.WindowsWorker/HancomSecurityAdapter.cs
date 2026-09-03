using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.WindowsBridge.V1;
using Microsoft.Win32;

namespace HwpxAgent.WindowsWorker;

internal interface IHancomSessionSecurity
{
    void Apply(
        StaStartSessionCommand command,
        HancomSession session,
        StaExecutionContext context);
}

internal interface IHancomSecurityModuleRegistry
{
    HancomSecurityModuleRegistration Resolve(string registrationName, string expectedSha256);
}

internal sealed class HancomSecurityModuleRegistration : IDisposable
{
    private FileStream? integrityGuard;

    internal HancomSecurityModuleRegistration(
        string registrationName,
        string modulePath,
        FileStream integrityGuard)
    {
        RegistrationName = registrationName;
        ModulePath = modulePath;
        this.integrityGuard = integrityGuard;
    }

    internal string RegistrationName { get; }

    internal string ModulePath { get; }

    public void Dispose()
    {
        Interlocked.Exchange(ref integrityGuard, null)?.Dispose();
    }
}

public sealed partial class HancomSecurityAdapter
    : IHancomSessionSecurity, IHancomApprovedDocumentResolver, IHancomPlanExecutionResolver
{
    public const string SchemaVersion = "hwpx-agent.p10-05-security-lease/v1";
    public const string BindingSchemaVersion = "hwpx-agent.p10-06-security-lease/v2";
    public const string FileAccessPolicyId = "file.local_read";
    public const string OpenPolicyId = "open.read_only";
    public const string LeaseFileName = ".hancom-security-lease.json";
    public const string ApprovedInputFileName = "hancom_approved_input.hwpx";
    public const string OperationPlanFileName = "hancom_operation_plan.json";
    public const string BindingBundleFileName = "hancom_binding_bundle.json";
    public const string BindingPublicKeyFileName = "hancom_binding_public_key.pem";
    private const int MaximumLeaseBytes = 8 * 1024;
    private const int MaximumOperationPlanBytes = 4 * 1024 * 1024;
    private const int MaximumBindingBundleBytes = 1024 * 1024;
    private const int MaximumBindingPublicKeyBytes = 8 * 1024;
    private static readonly TimeSpan MaximumLeaseLifetime = TimeSpan.FromMinutes(30);

    private readonly HancomSecurityLease lease;
    private readonly string sandboxRoot;
    private readonly IHancomSecurityModuleRegistry moduleRegistry;
    private readonly TimeProvider timeProvider;
    private int securityApplied;
    private int consumed;
    private int planConsumed;

    private HancomSecurityAdapter(
        HancomSecurityLease lease,
        string sandboxRoot,
        IHancomSecurityModuleRegistry moduleRegistry,
        TimeProvider timeProvider)
    {
        this.lease = lease;
        this.sandboxRoot = sandboxRoot;
        this.moduleRegistry = moduleRegistry;
        this.timeProvider = timeProvider;
    }

    public static HancomSecurityAdapter Load(
        string leasePath,
        string expectedSessionId,
        ulong expectedFencingToken,
        string expectedTargetProfileId,
        TimeProvider? timeProvider = null) =>
        Load(
            leasePath,
            expectedSessionId,
            expectedFencingToken,
            expectedTargetProfileId,
            new RegistryHancomSecurityModuleRegistry(),
            timeProvider ?? TimeProvider.System);

    internal static HancomSecurityAdapter Load(
        string leasePath,
        string expectedSessionId,
        ulong expectedFencingToken,
        string expectedTargetProfileId,
        IHancomSecurityModuleRegistry moduleRegistry,
        TimeProvider timeProvider)
    {
        ArgumentNullException.ThrowIfNull(moduleRegistry);
        ArgumentNullException.ThrowIfNull(timeProvider);
        try
        {
            var fullPath = Path.GetFullPath(leasePath);
            var leaseFile = new FileInfo(fullPath);
            if (!leaseFile.Exists
                || !string.Equals(leaseFile.Name, LeaseFileName, StringComparison.Ordinal)
                || (leaseFile.Attributes & FileAttributes.ReparsePoint) != 0
                || (leaseFile.Attributes & FileAttributes.ReadOnly) == 0
                || leaseFile.Length is <= 0 or > MaximumLeaseBytes)
            {
                throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
            }

            var root = leaseFile.Directory?.FullName
                ?? throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
            EnsurePlainSandbox(root);
            byte[] bytes;
            using (var stream = new FileStream(
                fullPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: MaximumLeaseBytes,
                FileOptions.SequentialScan))
            {
                bytes = new byte[checked((int)stream.Length)];
                stream.ReadExactly(bytes);
            }

            var lease = JsonSerializer.Deserialize<HancomSecurityLease>(
                bytes,
                new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = false,
                    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
                    MaxDepth = 4,
                }) ?? throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
            lease.Validate(
                root,
                expectedSessionId,
                expectedFencingToken,
                expectedTargetProfileId,
                timeProvider);
            return new HancomSecurityAdapter(lease, root, moduleRegistry, timeProvider);
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or ArgumentException
            or NotSupportedException
            or PathTooLongException
            or JsonException
            or OverflowException)
        {
            throw Fail(HancomLifecycleError.SecurityLeaseInvalid, error);
        }
    }

    void IHancomSessionSecurity.Apply(
        StaStartSessionCommand command,
        HancomSession session,
        StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(session);
        ArgumentNullException.ThrowIfNull(context);
        EnsureFresh();
        if (Interlocked.CompareExchange(ref securityApplied, 1, 0) != 0
            || command.SecurityPolicy is null
            || command.SecurityPolicy.AllowExternalNetwork
            || command.SecurityPolicy.AllowClipboard
            || command.SecurityPolicy.AllowMacros
            || command.SecurityPolicy.AllowOleActivation
            || !string.Equals(
                command.SecurityPolicy.FileAccessPolicyId,
                lease.FileAccessPolicyId,
                StringComparison.Ordinal)
            || command.TargetProfile is null
            || !string.Equals(
                command.TargetProfile.ProfileId,
                lease.TargetProfileId,
                StringComparison.Ordinal)
            || (string.Equals(lease.SchemaVersionValue, BindingSchemaVersion, StringComparison.Ordinal)
                && !string.Equals(
                    command.CapabilityRegistrySha256,
                    lease.CapabilityRegistrySha256,
                    StringComparison.Ordinal)))
        {
            throw Fail(HancomLifecycleError.SecurityPolicyMismatch);
        }

        using var registration = moduleRegistry.Resolve(
            lease.SecurityModuleRegistrationName!,
            lease.SecurityModuleSha256!);
        session.EnableFilePathSecurity(registration.RegistrationName, context);
    }

    HancomApprovedDocument IHancomApprovedDocumentResolver.Resolve(
        StaOpenDocumentCommand command,
        StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(context);
        EnsureFresh();
        if (Volatile.Read(ref securityApplied) != 1)
        {
            throw Fail(HancomLifecycleError.SecurityPolicyMismatch);
        }

        if (Interlocked.CompareExchange(ref consumed, 1, 0) != 0)
        {
            throw Fail(HancomLifecycleError.SecurityLeaseConsumed);
        }

        var staged = command.Input;
        if (!string.Equals(command.OpenPolicyId, lease.OpenPolicyId, StringComparison.Ordinal)
            || staged is null
            || staged.Artifact is null
            || !staged.ReadOnly
            || !string.Equals(staged.SandboxHandle, lease.SandboxHandle, StringComparison.Ordinal)
            || !string.Equals(staged.Artifact.ArtifactId, lease.ArtifactId, StringComparison.Ordinal)
            || !string.Equals(staged.Artifact.Sha256, lease.InputSha256, StringComparison.Ordinal)
            || staged.Artifact.SizeBytes != lease.InputSizeBytes)
        {
            throw Fail(HancomLifecycleError.SecurityPolicyMismatch);
        }

        EnsurePlainSandbox(sandboxRoot, lease.ExecutionId);
        var candidate = Path.GetFullPath(Path.Combine(sandboxRoot, ApprovedInputFileName));
        var prefix = sandboxRoot.TrimEnd(Path.DirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!candidate.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
        }

        return HancomApprovedDocument.OpenGuarded(
            candidate,
            lease.InputSha256!,
            checked((long)lease.InputSizeBytes));
    }

    HancomApprovedPlanExecution IHancomPlanExecutionResolver.Resolve(
        StaExecutePlanCommand command,
        StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(context);
        context.ThrowIfCancellationRequested();
        EnsureFresh();
        if (Volatile.Read(ref securityApplied) != 1)
        {
            throw new HancomBindingException(HancomBindingError.BundleInvalid);
        }

        if (Interlocked.CompareExchange(ref planConsumed, 1, 0) != 0)
        {
            throw new HancomBindingException(HancomBindingError.LeaseConsumed);
        }

        var staged = command.OperationPlan;
        if (!string.Equals(lease.SchemaVersionValue, BindingSchemaVersion, StringComparison.Ordinal)
            || staged is null
            || staged.Artifact is null
            || !staged.ReadOnly
            || !string.Equals(
                staged.SandboxHandle,
                lease.OperationPlanSandboxHandle,
                StringComparison.Ordinal)
            || !string.Equals(
                staged.Artifact.ArtifactId,
                lease.OperationPlanArtifactId,
                StringComparison.Ordinal)
            || !string.Equals(
                staged.Artifact.Sha256,
                lease.OperationPlanSha256,
                StringComparison.Ordinal)
            || staged.Artifact.SizeBytes != lease.OperationPlanSizeBytes
            || !string.Equals(command.BindingBundleId, lease.BindingBundleId, StringComparison.Ordinal)
            || !string.Equals(
                command.BindingBundleSha256,
                lease.BindingBundleSha256,
                StringComparison.Ordinal))
        {
            throw new HancomBindingException(HancomBindingError.BundleInvalid);
        }

        EnsurePlainSandbox(sandboxRoot, lease.ExecutionId);
        var guards = new List<FileStream>(3);
        try
        {
            var operationPlan = OpenGuardedBytes(
                OperationPlanFileName,
                lease.OperationPlanSha256!,
                checked((long)lease.OperationPlanSizeBytes),
                MaximumOperationPlanBytes,
                guards);
            var bindingBundle = OpenGuardedBytes(
                BindingBundleFileName,
                lease.BindingBundleSha256!,
                expectedSize: null,
                MaximumBindingBundleBytes,
                guards);
            var publicKey = OpenGuardedBytes(
                BindingPublicKeyFileName,
                lease.BindingPublicKeySha256!,
                expectedSize: null,
                MaximumBindingPublicKeyBytes,
                guards);
            var approved = new HancomApprovedPlanExecution(
                operationPlan,
                bindingBundle,
                publicKey,
                guards);
            guards = [];
            return approved;
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or ArgumentException
            or NotSupportedException
            or PathTooLongException
            or OverflowException)
        {
            throw new HancomBindingException(HancomBindingError.BundleInvalid, error);
        }
        finally
        {
            foreach (var guard in guards)
            {
                guard.Dispose();
            }
        }
    }

    private byte[] OpenGuardedBytes(
        string fileName,
        string expectedSha256,
        long? expectedSize,
        int maximumSize,
        ICollection<FileStream> guards)
    {
        var candidate = Path.GetFullPath(Path.Combine(sandboxRoot, fileName));
        var prefix = sandboxRoot.TrimEnd(Path.DirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!candidate.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw new HancomBindingException(HancomBindingError.BundleInvalid);
        }

        var file = new FileInfo(candidate);
        if (!file.Exists
            || !string.Equals(file.Name, fileName, StringComparison.Ordinal)
            || (file.Attributes & FileAttributes.ReparsePoint) != 0
            || (file.Attributes & FileAttributes.ReadOnly) == 0
            || file.Length is <= 0
            || file.Length > maximumSize
            || expectedSize is not null && file.Length != expectedSize)
        {
            throw new HancomBindingException(HancomBindingError.BundleInvalid);
        }

        var guard = new FileStream(
            candidate,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 64 * 1024,
            FileOptions.SequentialScan);
        try
        {
            if (guard.Length != file.Length)
            {
                throw new HancomBindingException(HancomBindingError.BundleInvalid);
            }

            var bytes = new byte[checked((int)guard.Length)];
            guard.ReadExactly(bytes);
            if (!string.Equals(
                Convert.ToHexStringLower(SHA256.HashData(bytes)),
                expectedSha256,
                StringComparison.Ordinal))
            {
                throw new HancomBindingException(HancomBindingError.BundleInvalid);
            }

            guard.Position = 0;
            guards.Add(guard);
            return bytes;
        }
        catch
        {
            guard.Dispose();
            throw;
        }
    }

    private void EnsureFresh()
    {
        var now = timeProvider.GetUtcNow().ToUnixTimeMilliseconds();
        if (lease.ExpiresAtUnixMs <= 0 || lease.ExpiresAtUnixMs <= now)
        {
            throw Fail(HancomLifecycleError.SecurityLeaseExpired);
        }
    }

    private static void EnsurePlainSandbox(string root, string? expectedExecutionId = null)
    {
        var directory = new DirectoryInfo(root);
        if (!directory.Exists || (directory.Attributes & FileAttributes.ReparsePoint) != 0)
        {
            throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
        }

        var marker = new FileInfo(Path.Combine(root, ".hwpx-agent-sandbox"));
        if (!marker.Exists
            || (marker.Attributes & FileAttributes.ReparsePoint) != 0
            || marker.Length is <= 0 or > 128
            || (expectedExecutionId is not null
                && !string.Equals(
                    File.ReadAllText(marker.FullName),
                    expectedExecutionId,
                    StringComparison.Ordinal)))
        {
            throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
        }
    }

    private static HancomLifecycleException Fail(
        HancomLifecycleError error,
        Exception? inner = null) =>
        inner is null
            ? new HancomLifecycleException(error)
            : new HancomLifecycleException(error, inner);

    [GeneratedRegex("^[a-z][a-z0-9._-]{2,127}$", RegexOptions.CultureInvariant)]
    private static partial Regex ArtifactIdPattern();

    [GeneratedRegex("^[a-z][a-z0-9_-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex InputHandlePattern();

    [GeneratedRegex("^[A-Za-z][A-Za-z0-9._-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex ModuleNamePattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class HancomSecurityLease
    {
        [JsonPropertyName("schema_version")]
        public string? SchemaVersionValue { get; init; }

        [JsonPropertyName("execution_id")]
        public string? ExecutionId { get; init; }

        [JsonPropertyName("session_id")]
        public string? SessionId { get; init; }

        [JsonPropertyName("fencing_token")]
        public ulong FencingToken { get; init; }

        [JsonPropertyName("target_profile_id")]
        public string? TargetProfileId { get; init; }

        [JsonPropertyName("expires_at_unix_ms")]
        public long ExpiresAtUnixMs { get; init; }

        [JsonPropertyName("file_access_policy_id")]
        public string? FileAccessPolicyId { get; init; }

        [JsonPropertyName("open_policy_id")]
        public string? OpenPolicyId { get; init; }

        [JsonPropertyName("sandbox_handle")]
        public string? SandboxHandle { get; init; }

        [JsonPropertyName("artifact_id")]
        public string? ArtifactId { get; init; }

        [JsonPropertyName("input_sha256")]
        public string? InputSha256 { get; init; }

        [JsonPropertyName("input_size_bytes")]
        public ulong InputSizeBytes { get; init; }

        [JsonPropertyName("security_module_registration_name")]
        public string? SecurityModuleRegistrationName { get; init; }

        [JsonPropertyName("security_module_sha256")]
        public string? SecurityModuleSha256 { get; init; }

        [JsonPropertyName("operation_plan_sandbox_handle")]
        public string? OperationPlanSandboxHandle { get; init; }

        [JsonPropertyName("operation_plan_artifact_id")]
        public string? OperationPlanArtifactId { get; init; }

        [JsonPropertyName("operation_plan_sha256")]
        public string? OperationPlanSha256 { get; init; }

        [JsonPropertyName("operation_plan_size_bytes")]
        public ulong OperationPlanSizeBytes { get; init; }

        [JsonPropertyName("binding_bundle_id")]
        public string? BindingBundleId { get; init; }

        [JsonPropertyName("binding_bundle_sha256")]
        public string? BindingBundleSha256 { get; init; }

        [JsonPropertyName("binding_public_key_sha256")]
        public string? BindingPublicKeySha256 { get; init; }

        [JsonPropertyName("capability_registry_sha256")]
        public string? CapabilityRegistrySha256 { get; init; }

        internal void Validate(
            string root,
            string expectedSessionId,
            ulong expectedFencingToken,
            string expectedTargetProfileId,
            TimeProvider timeProvider)
        {
            var now = timeProvider.GetUtcNow().ToUnixTimeMilliseconds();
            var maximumExpiry = timeProvider.GetUtcNow().Add(MaximumLeaseLifetime).ToUnixTimeMilliseconds();
            var marker = File.ReadAllText(Path.Combine(root, ".hwpx-agent-sandbox"));
            if (ExpiresAtUnixMs <= now)
            {
                throw Fail(HancomLifecycleError.SecurityLeaseExpired);
            }

            var baseLease = string.Equals(SchemaVersionValue, SchemaVersion, StringComparison.Ordinal);
            var bindingLease = string.Equals(
                SchemaVersionValue,
                BindingSchemaVersion,
                StringComparison.Ordinal);
            if ((!baseLease && !bindingLease)
                || !Guid.TryParseExact(ExecutionId, "D", out var executionId)
                || !string.Equals(executionId.ToString("D"), ExecutionId, StringComparison.Ordinal)
                || !string.Equals(marker, ExecutionId, StringComparison.Ordinal)
                || !Guid.TryParseExact(SessionId, "D", out var sessionId)
                || !string.Equals(sessionId.ToString("D"), SessionId, StringComparison.Ordinal)
                || !string.Equals(SessionId, expectedSessionId, StringComparison.Ordinal)
                || FencingToken == 0
                || FencingToken != expectedFencingToken
                || !string.Equals(TargetProfileId, expectedTargetProfileId, StringComparison.Ordinal)
                || ExpiresAtUnixMs > maximumExpiry
                || !string.Equals(FileAccessPolicyId, HancomSecurityAdapter.FileAccessPolicyId, StringComparison.Ordinal)
                || !string.Equals(OpenPolicyId, HancomSecurityAdapter.OpenPolicyId, StringComparison.Ordinal)
                || !InputHandlePattern().IsMatch(SandboxHandle ?? string.Empty)
                || !ArtifactIdPattern().IsMatch(ArtifactId ?? string.Empty)
                || !Sha256Pattern().IsMatch(InputSha256 ?? string.Empty)
                || InputSizeBytes is 0 or > 8 * 1024 * 1024
                || !ModuleNamePattern().IsMatch(SecurityModuleRegistrationName ?? string.Empty)
                || !Sha256Pattern().IsMatch(SecurityModuleSha256 ?? string.Empty))
            {
                throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
            }

            if (baseLease)
            {
                if (OperationPlanSandboxHandle is not null
                    || OperationPlanArtifactId is not null
                    || OperationPlanSha256 is not null
                    || OperationPlanSizeBytes != 0
                    || BindingBundleId is not null
                    || BindingBundleSha256 is not null
                    || BindingPublicKeySha256 is not null
                    || CapabilityRegistrySha256 is not null)
                {
                    throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
                }

                return;
            }

            if (!InputHandlePattern().IsMatch(OperationPlanSandboxHandle ?? string.Empty)
                || !ArtifactIdPattern().IsMatch(OperationPlanArtifactId ?? string.Empty)
                || !Sha256Pattern().IsMatch(OperationPlanSha256 ?? string.Empty)
                || OperationPlanSizeBytes is 0 or > MaximumOperationPlanBytes
                || !ArtifactIdPattern().IsMatch(BindingBundleId ?? string.Empty)
                || !Sha256Pattern().IsMatch(BindingBundleSha256 ?? string.Empty)
                || !Sha256Pattern().IsMatch(BindingPublicKeySha256 ?? string.Empty)
                || !Sha256Pattern().IsMatch(CapabilityRegistrySha256 ?? string.Empty))
            {
                throw Fail(HancomLifecycleError.SecurityLeaseInvalid);
            }
        }
    }
}

internal sealed class RegistryHancomSecurityModuleRegistry : IHancomSecurityModuleRegistry
{
    private const int PeMachineI386 = 0x014c;
    private const long MaximumModuleBytes = 16 * 1024 * 1024;

    public HancomSecurityModuleRegistration Resolve(string registrationName, string expectedSha256)
    {
        try
        {
            using var currentUser = RegistryKey.OpenBaseKey(RegistryHive.CurrentUser, RegistryView.Registry32);
            using var modules = currentUser.OpenSubKey(
                "Software\\HNC\\HwpAutomation\\Modules",
                writable: false);
            if (modules is null
                || modules.GetValueKind(registrationName) != RegistryValueKind.String
                || modules.GetValue(
                    registrationName,
                    defaultValue: null,
                    RegistryValueOptions.DoNotExpandEnvironmentNames) is not string configuredPath
                || configuredPath.Length is <= 0 or > 1_024)
            {
                throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid);
            }

            return ValidateModuleFile(registrationName, configuredPath, expectedSha256);
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or System.Security.SecurityException
            or ArgumentException
            or NotSupportedException)
        {
            throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid, error);
        }
    }

    internal static HancomSecurityModuleRegistration ValidateModuleFile(
        string registrationName,
        string configuredPath,
        string expectedSha256)
    {
        FileStream? guard = null;
        try
        {
            if (!Path.IsPathFullyQualified(configuredPath))
            {
                throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid);
            }

            var path = Path.GetFullPath(configuredPath);
            var file = new FileInfo(path);
            if (!file.Exists
                || (file.Attributes & FileAttributes.ReparsePoint) != 0
                || !string.Equals(file.Extension, ".dll", StringComparison.OrdinalIgnoreCase)
                || file.Length is <= 0 or > MaximumModuleBytes)
            {
                throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid);
            }

            guard = new FileStream(
                path,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: 64 * 1024,
                FileOptions.SequentialScan);
            if (guard.Length != file.Length
                || !string.Equals(
                    Convert.ToHexStringLower(SHA256.HashData(guard)),
                    expectedSha256,
                    StringComparison.Ordinal))
            {
                throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid);
            }

            guard.Position = 0;
            if (ReadPeMachine(guard) != PeMachineI386)
            {
                throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid);
            }

            guard.Position = 0;
            var registration = new HancomSecurityModuleRegistration(registrationName, path, guard);
            guard = null;
            return registration;
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or ArgumentException
            or NotSupportedException)
        {
            throw new HancomLifecycleException(HancomLifecycleError.SecurityModuleInvalid, error);
        }
        finally
        {
            guard?.Dispose();
        }
    }

    internal static int ReadPeMachine(Stream stream)
    {
        using var reader = new BinaryReader(stream, System.Text.Encoding.UTF8, leaveOpen: true);
        stream.Position = 0;
        if (stream.Length < 64 || reader.ReadUInt16() != 0x5a4d)
        {
            return -1;
        }

        stream.Position = 0x3c;
        var offset = reader.ReadUInt32();
        if (offset > stream.Length - 6)
        {
            return -1;
        }

        stream.Position = offset;
        return reader.ReadUInt32() == 0x00004550 ? reader.ReadUInt16() : -1;
    }
}
