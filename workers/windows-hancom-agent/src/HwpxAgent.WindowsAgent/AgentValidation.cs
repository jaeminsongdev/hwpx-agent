using System.Security.Cryptography;
using System.Text.RegularExpressions;
using Google.Protobuf;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

internal static partial class AgentValidation
{
    internal const ulong MaximumArtifactBytes = 1_073_741_824;

    internal static void ValidateConfiguration(WindowsAgentConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(configuration);
        RequireGuid(configuration.AgentInstanceId, nameof(configuration.AgentInstanceId));
        ValidateTarget(configuration.TargetProfile);
        RequireDigest(configuration.CapabilityRegistrySha256);
        if (configuration.AvailableJobSlots is 0 or > 16
            || configuration.RpcTimeout < TimeSpan.FromSeconds(1)
            || configuration.RpcTimeout > TimeSpan.FromMinutes(15))
        {
            throw new ArgumentException("Agent capacity and RPC timeout must be bounded.", nameof(configuration));
        }

        if (configuration.HancomSecurityModule is not null)
        {
            ValidateHancomSecurityModulePin(configuration.HancomSecurityModule);
        }

        if (configuration.HancomBindingBundle is not null)
        {
            if (configuration.HancomSecurityModule is null)
            {
                throw new ArgumentException(
                    "A Hancom binding bundle requires the file-path security module boundary.",
                    nameof(configuration));
            }

            ValidateHancomBindingBundlePin(configuration.HancomBindingBundle);
        }
    }

    internal static void ValidateHancomSecurityModulePin(HancomSecurityModulePin module)
    {
        ArgumentNullException.ThrowIfNull(module);
        if (!ModuleRegistrationNamePattern().IsMatch(module.RegistrationName ?? string.Empty))
        {
            throw new ArgumentException("A bounded Hancom security module registration name is required.", nameof(module));
        }

        RequireDigest(module.Sha256);
    }

    internal static void ValidateHancomBindingBundlePin(HancomBindingBundlePin bundle)
    {
        ArgumentNullException.ThrowIfNull(bundle);
        RequireSemanticId(bundle.BundleId);
        RequireDigest(bundle.Sha256);
        RequireDigest(bundle.TrustedPublicKeySha256);
        var normalizedPaths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var path in new[] { bundle.BundlePath, bundle.TrustedPublicKeyPath })
        {
            if (string.IsNullOrWhiteSpace(path)
                || !Path.IsPathFullyQualified(path)
                || !LocalDrivePathPattern().IsMatch(path)
                || path.Length > 1_024)
            {
                throw new ArgumentException(
                    "Hancom binding trust files require bounded absolute local paths.",
                    nameof(bundle));
            }

            if (!normalizedPaths.Add(Path.GetFullPath(path)))
            {
                throw new ArgumentException(
                    "The binding envelope and trust key must be distinct files.",
                    nameof(bundle));
            }
        }
    }

    internal static void ValidateAssignment(
        LeaseAssignment assignment,
        WindowsAgentConfiguration configuration,
        long nowUnixMilliseconds)
    {
        ArgumentNullException.ThrowIfNull(assignment);
        foreach (var value in new[]
        {
            assignment.LeaseId,
            assignment.RequestId,
            assignment.JobId,
            assignment.TraceId,
            assignment.ExecutionId,
        })
        {
            RequireGuid(value, nameof(assignment));
        }

        if (assignment.FencingToken == 0)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidFencing);
        }

        if (assignment.ExpiresAtUnixMs <= (ulong)nowUnixMilliseconds)
        {
            throw new AgentProtocolException(AgentProtocolError.ExpiredLease);
        }

        if (!string.Equals(
                assignment.TargetProfileId,
                configuration.TargetProfile.ProfileId,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ProfileMismatch);
        }

        var artifacts = new[]
        {
            assignment.Input,
            assignment.OperationPlan,
            assignment.ValidationContract,
        };
        foreach (var artifact in artifacts)
        {
            ValidateStagedArtifact(artifact, requireReadOnly: true);
        }

        if (artifacts.Select(artifact => artifact.SandboxHandle).Distinct(StringComparer.Ordinal).Count()
            != artifacts.Length)
        {
            throw new AgentProtocolException(AgentProtocolError.DuplicateHandle);
        }

        ValidateLimits(assignment.ResourceLimits);
        ValidateSecurityPolicy(assignment.SecurityPolicy);
    }

    internal static void ValidateStagedArtifact(StagedArtifactRef staged, bool requireReadOnly)
    {
        if (staged is null || staged.Artifact is null)
        {
            throw new AgentProtocolException(AgentProtocolError.MissingField);
        }

        ValidateArtifact(staged.Artifact);
        RequireHandle(staged.SandboxHandle);
        if (requireReadOnly && !staged.ReadOnly)
        {
            throw new AgentProtocolException(AgentProtocolError.MutableInput);
        }
    }

    internal static void ValidateArtifact(ArtifactRef artifact)
    {
        ArgumentNullException.ThrowIfNull(artifact);
        if (!ArtifactIdPattern().IsMatch(artifact.ArtifactId)
            || artifact.SizeBytes is 0 or > MaximumArtifactBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidArtifact);
        }

        RequireDigest(artifact.Sha256);
    }

    internal static void ValidateJobResult(AgentJobResult result)
    {
        ArgumentNullException.ThrowIfNull(result);
        if (result.TerminalState is not (
                ExecutionState.Succeeded
                or ExecutionState.Failed
                or ExecutionState.Cancelled
                or ExecutionState.UnknownOutcome))
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        RequireSemanticId(result.BackendId);
        RequireSemanticId(result.BindingBundleId);
        RequireDigest(result.BindingBundleSha256);
        if (result.ValidationState == ValidationState.Unspecified
            || result.Artifacts is null
            || result.Artifacts.Count > 64
            || (result.TerminalState == ExecutionState.Succeeded
                && result.ValidationState != ValidationState.Passed))
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        var handles = new HashSet<string>(StringComparer.Ordinal);
        var artifactIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var artifact in result.Artifacts)
        {
            RequireHandle(artifact.SandboxHandle);
            if (artifact.ArtifactId is null
                || !ArtifactIdPattern().IsMatch(artifact.ArtifactId)
                || !handles.Add(artifact.SandboxHandle)
                || !artifactIds.Add(artifact.ArtifactId))
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidArtifact);
            }
        }

        if (result.TerminalState == ExecutionState.Succeeded && result.Diagnostic is not null)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        if (result.TerminalState != ExecutionState.Succeeded && result.Diagnostic is null)
        {
            throw new AgentProtocolException(AgentProtocolError.MissingField);
        }

        if (result.Diagnostic is not null)
        {
            if (result.Diagnostic.ErrorCode == BridgeErrorCode.Unspecified)
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidState);
            }

            RequireDigest(result.Diagnostic.SafeDetailSha256);
        }
    }

    internal static void ValidateExecutionReceipt(
        AgentExecutionReceipt receipt,
        LeaseAssignment assignment)
    {
        ArgumentNullException.ThrowIfNull(receipt);
        ArgumentNullException.ThrowIfNull(assignment);
        if (receipt.TerminalState is not (
                ExecutionState.Succeeded
                or ExecutionState.Failed
                or ExecutionState.Cancelled
                or ExecutionState.UnknownOutcome)
            || receipt.ValidationState == ValidationState.Unspecified
            || receipt.Outputs.Count + receipt.Evidence.Count > 64
            || !receipt.InputUnchanged
            || receipt.ExternalNetworkInvoked
            || receipt.RegistryOrSystemSettingChanged
            || receipt.Input is null
            || !receipt.Input.Equals(assignment.Input.Artifact))
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        RequireSemanticId(receipt.BackendId);
        RequireSemanticId(receipt.BindingBundleId);
        RequireDigest(receipt.BindingBundleSha256);
        var artifactIds = new HashSet<string>(StringComparer.Ordinal);
        ulong totalOutputBytes = 0;
        foreach (var artifact in receipt.Outputs.Concat(receipt.Evidence))
        {
            ValidateArtifact(artifact);
            if (!artifactIds.Add(artifact.ArtifactId))
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidArtifact);
            }

            try
            {
                totalOutputBytes = checked(totalOutputBytes + artifact.SizeBytes);
            }
            catch (OverflowException)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }

            if (totalOutputBytes > assignment.ResourceLimits.MaxOutputBytes)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }
        }

        if (receipt.TerminalState == ExecutionState.Succeeded)
        {
            if (receipt.ValidationState != ValidationState.Passed || receipt.Diagnostic is not null)
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidState);
            }

            return;
        }

        if (receipt.Diagnostic is null || receipt.Diagnostic.ErrorCode == BridgeErrorCode.Unspecified)
        {
            throw new AgentProtocolException(AgentProtocolError.MissingField);
        }

        RequireDigest(receipt.Diagnostic.SafeDetailSha256);
        if (receipt.TerminalState == ExecutionState.UnknownOutcome && !receipt.Diagnostic.EffectUnknown)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }
    }

    internal static string ComputeSha256(ReadOnlySpan<byte> bytes) =>
        Convert.ToHexStringLower(SHA256.HashData(bytes));

    internal static string ComputeSha256(IMessage message) => ComputeSha256(message.ToByteArray());

    internal static string ComputeProgressDigest(string state) =>
        ComputeSha256(System.Text.Encoding.ASCII.GetBytes(state));

    internal static void RequireDigest(string value)
    {
        if (value is null || !Sha256Pattern().IsMatch(value))
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidDigest);
        }
    }

    internal static void RequireGuid(string value, string parameterName)
    {
        if (!Guid.TryParseExact(value, "D", out var parsed)
            || !StringComparer.Ordinal.Equals(parsed.ToString("D"), value))
        {
            throw new ArgumentException("A lowercase canonical UUID is required.", parameterName);
        }
    }

    internal static void RequireHandle(string value)
    {
        if (value is null || !SandboxHandlePattern().IsMatch(value))
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
        }
    }

    internal static void RequireSemanticId(string value)
    {
        if (value is null
            || value.Contains("haction", StringComparison.OrdinalIgnoreCase)
            || value.Contains("parameterset", StringComparison.OrdinalIgnoreCase)
            || !SemanticIdPattern().IsMatch(value))
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeIdentifier);
        }
    }

    internal static void EnsurePlainDirectory(string path, string parameterName)
    {
        var fullPath = Path.GetFullPath(path);
        var root = Path.GetPathRoot(fullPath);
        if (string.Equals(
                fullPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                root?.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("A filesystem root cannot be used as an Agent workspace.", parameterName);
        }

        if (Directory.Exists(fullPath)
            && (File.GetAttributes(fullPath) & FileAttributes.ReparsePoint) != 0)
        {
            throw new ArgumentException("Reparse-point roots are not accepted.", parameterName);
        }
    }

    private static void ValidateTarget(TargetProfileIdentity target)
    {
        ArgumentNullException.ThrowIfNull(target);
        foreach (var value in new[]
        {
            target.ProfileId,
            target.ProductBuild,
            target.Locale,
            target.ProcessArchitecture,
        })
        {
            if (!TokenPattern().IsMatch(value))
            {
                throw new AgentProtocolException(AgentProtocolError.ProfileMismatch);
            }
        }

        RequireDigest(target.ExecutableSha256);
        RequireDigest(target.EnvironmentDigest);
    }

    private static void ValidateLimits(ResourceLimits limits)
    {
        if (limits is null
            || limits.CommandTimeoutSeconds is 0 or > 900
            || limits.JobTimeoutSeconds is 0 or > 3600
            || limits.CommandTimeoutSeconds > limits.JobTimeoutSeconds
            || limits.MemoryLimitBytes < 67_108_864
            || limits.MemoryLimitBytes > 17_179_869_184
            || limits.MaxOutputBytes is 0 or > MaximumArtifactBytes
            || limits.MaxEventCount is 0 or > 10_000)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidLimits);
        }
    }

    private static void ValidateSecurityPolicy(SecurityPolicy policy)
    {
        if (policy is null
            || policy.AllowExternalNetwork
            || policy.AllowClipboard
            || policy.AllowMacros
            || policy.AllowOleActivation)
        {
            throw new AgentProtocolException(AgentProtocolError.PolicyDenied);
        }

        RequireSemanticId(policy.FileAccessPolicyId);
        RequireSemanticId(policy.ModalPolicyId);
    }

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();

    [GeneratedRegex("^[a-z0-9][a-z0-9._-]{2,127}$", RegexOptions.CultureInvariant)]
    private static partial Regex ArtifactIdPattern();

    [GeneratedRegex("^[a-z][a-z0-9_-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex SandboxHandlePattern();

    [GeneratedRegex("^[a-z][a-z0-9]*(?:\\.[a-z0-9_-]+)+$", RegexOptions.CultureInvariant)]
    private static partial Regex SemanticIdPattern();

    [GeneratedRegex("^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$", RegexOptions.CultureInvariant)]
    private static partial Regex TokenPattern();

    [GeneratedRegex("^[A-Za-z][A-Za-z0-9._-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex ModuleRegistrationNamePattern();

    [GeneratedRegex("^[A-Za-z]:[\\\\/]", RegexOptions.CultureInvariant)]
    private static partial Regex LocalDrivePathPattern();
}

public enum AgentProtocolError
{
    MissingField,
    InvalidFencing,
    ExpiredLease,
    ProfileMismatch,
    InvalidArtifact,
    DuplicateHandle,
    MutableInput,
    InvalidLimits,
    PolicyDenied,
    InvalidState,
    InvalidDigest,
    UnsafeHandle,
    UnsafeIdentifier,
    JournalConflict,
    ArtifactMismatch,
    OutputLimit,
}

public sealed class AgentProtocolException : Exception
{
    public AgentProtocolException(AgentProtocolError error)
        : base($"Windows Agent rejected input: {error}.")
    {
        Error = error;
    }

    public AgentProtocolError Error { get; }
}
