using System.Text.RegularExpressions;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

/// <summary>
/// P01 semantic boundary. COM/HAction 실행기는 의도적으로 존재하지 않는다.
/// </summary>
public static partial class WorkerBoundary
{
    private const int Sha256HexLength = 64;
    private const ulong MaxArtifactBytes = 1_073_741_824;
    private const int MaxWindowsBridgeFrameBytes = 1_048_576;
    private const uint WindowsBridgeProtocolMajor = 1;
    private const uint WindowsBridgeProtocolMinor = 0;

    public static void Validate(WorkerRequestContext request)
    {
        ArgumentNullException.ThrowIfNull(request);
        RequireGuid(request.RequestId, nameof(request.RequestId));
        RequireGuid(request.JobId, nameof(request.JobId));
        RequireGuid(request.TraceId, nameof(request.TraceId));

        if (!CapabilityIdPattern().IsMatch(request.CapabilityId))
        {
            throw new ArgumentException("Only semantic capability IDs are accepted.", nameof(request));
        }

        if (request.CapabilityId.Contains("haction", StringComparison.OrdinalIgnoreCase)
            || request.CapabilityId.Contains("parameterset", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Raw automation actions are forbidden.", nameof(request));
        }

        if (request.Input is null
            || !ArtifactIdPattern().IsMatch(request.Input.ArtifactId)
            || request.Input.Sha256.Length != Sha256HexLength
            || !Sha256Pattern().IsMatch(request.Input.Sha256)
            || request.Input.SizeBytes > MaxArtifactBytes)
        {
            throw new ArgumentException("Input must be a checksum-addressed artifact reference.", nameof(request));
        }
    }

    /// <summary>
    /// P10-01 local named-pipe envelope boundary. Transport and COM execution are implemented by
    /// later P10 tasks; this boundary accepts only the versioned typed command union.
    /// </summary>
    public static StaCommandEnvelope DecodeAndValidate(ReadOnlySpan<byte> bytes)
    {
        if (bytes.Length > MaxWindowsBridgeFrameBytes)
        {
            throw new ArgumentException("Windows bridge frame limit exceeded.", nameof(bytes));
        }

        StaCommandEnvelope envelope;
        try
        {
            envelope = StaCommandEnvelope.Parser.ParseFrom(bytes.ToArray());
        }
        catch (Google.Protobuf.InvalidProtocolBufferException error)
        {
            throw new ArgumentException("Windows bridge protobuf rejected.", nameof(bytes), error);
        }

        Validate(envelope);
        return envelope;
    }

    /// <summary>
    /// Validates an already decoded local named-pipe envelope.
    /// </summary>
    public static void Validate(StaCommandEnvelope envelope)
    {
        ArgumentNullException.ThrowIfNull(envelope);
        if (envelope.ProtocolMajor != WindowsBridgeProtocolMajor
            || envelope.ProtocolMinor != WindowsBridgeProtocolMinor)
        {
            throw new ArgumentException("Unsupported Windows bridge protocol version.", nameof(envelope));
        }

        RequireGuid(envelope.SessionId, nameof(envelope.SessionId));
        RequireGuid(envelope.CommandId, nameof(envelope.CommandId));
        RequireGuid(envelope.TraceId, nameof(envelope.TraceId));
        if (envelope.FencingToken == 0 || envelope.DeadlineUnixMs == 0)
        {
            throw new ArgumentException("Fencing token and deadline are required.", nameof(envelope));
        }

        switch (envelope.CommandCase)
        {
            case StaCommandEnvelope.CommandOneofCase.StartSession:
                ValidateTarget(envelope.StartSession.TargetProfile);
                ValidateDigest(envelope.StartSession.CapabilityRegistrySha256);
                ValidatePolicy(envelope.StartSession.SecurityPolicy);
                break;
            case StaCommandEnvelope.CommandOneofCase.OpenDocument:
                ValidateStagedArtifact(envelope.OpenDocument.Input, requireReadOnly: true);
                ValidateSemanticId(envelope.OpenDocument.OpenPolicyId);
                break;
            case StaCommandEnvelope.CommandOneofCase.ExecutePlan:
                ValidateStagedArtifact(envelope.ExecutePlan.OperationPlan, requireReadOnly: true);
                RejectRawAutomation(envelope.ExecutePlan.BindingBundleId);
                ValidateSemanticId(envelope.ExecutePlan.BindingBundleId);
                ValidateDigest(envelope.ExecutePlan.BindingBundleSha256);
                break;
            case StaCommandEnvelope.CommandOneofCase.SaveDocument:
                ValidateHandle(envelope.SaveDocument.OutputSlot);
                ValidateSemanticId(envelope.SaveDocument.FormatId);
                break;
            case StaCommandEnvelope.CommandOneofCase.RenderDocument:
                ValidateHandle(envelope.RenderDocument.OutputSlot);
                ValidateSemanticId(envelope.RenderDocument.RenderProfileId);
                break;
            case StaCommandEnvelope.CommandOneofCase.CloseSession:
                if (!envelope.CloseSession.DiscardUnsavedChanges)
                {
                    throw new ArgumentException("Close must discard uncommitted changes.", nameof(envelope));
                }

                break;
            case StaCommandEnvelope.CommandOneofCase.Cancel:
                RequireGuid(envelope.Cancel.TargetCommandId, nameof(envelope.Cancel.TargetCommandId));
                break;
            default:
                throw new ArgumentException("A typed STA command is required.", nameof(envelope));
        }
    }

    private static void ValidateStagedArtifact(StagedArtifactRef staged, bool requireReadOnly)
    {
        if (staged is null
            || staged.Artifact is null
            || !ArtifactIdPattern().IsMatch(staged.Artifact.ArtifactId)
            || staged.Artifact.SizeBytes == 0
            || staged.Artifact.SizeBytes > MaxArtifactBytes)
        {
            throw new ArgumentException("A bounded staged artifact is required.", nameof(staged));
        }

        ValidateDigest(staged.Artifact.Sha256);
        ValidateHandle(staged.SandboxHandle);
        if (requireReadOnly && !staged.ReadOnly)
        {
            throw new ArgumentException("The staged input must be read-only.", nameof(staged));
        }
    }

    private static void ValidateTarget(TargetProfileIdentity target)
    {
        if (target is null
            || !TokenPattern().IsMatch(target.ProfileId)
            || !TokenPattern().IsMatch(target.ProductBuild)
            || !TokenPattern().IsMatch(target.Locale)
            || !TokenPattern().IsMatch(target.ProcessArchitecture))
        {
            throw new ArgumentException("A typed target profile is required.", nameof(target));
        }

        ValidateDigest(target.ExecutableSha256);
        ValidateDigest(target.EnvironmentDigest);
    }

    private static void ValidatePolicy(SecurityPolicy policy)
    {
        if (policy is null)
        {
            throw new ArgumentException("A security policy is required.", nameof(policy));
        }

        ValidateSemanticId(policy.FileAccessPolicyId);
        ValidateSemanticId(policy.ModalPolicyId);
    }

    private static void ValidateSemanticId(string value)
    {
        RejectRawAutomation(value);
        if (!CapabilityIdPattern().IsMatch(value))
        {
            throw new ArgumentException("A semantic identifier is required.", nameof(value));
        }
    }

    private static void RejectRawAutomation(string value)
    {
        if (value.Contains("haction", StringComparison.OrdinalIgnoreCase)
            || value.Contains("parameterset", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Raw automation actions are forbidden.", nameof(value));
        }
    }

    private static void ValidateDigest(string value)
    {
        if (value.Length != Sha256HexLength || !Sha256Pattern().IsMatch(value))
        {
            throw new ArgumentException("A lowercase SHA-256 digest is required.", nameof(value));
        }
    }

    private static void ValidateHandle(string value)
    {
        if (!SandboxHandlePattern().IsMatch(value))
        {
            throw new ArgumentException("A path-free sandbox handle is required.", nameof(value));
        }
    }

    private static void RequireGuid(string value, string parameterName)
    {
        if (!Guid.TryParseExact(value, "D", out var parsed)
            || !StringComparer.Ordinal.Equals(parsed.ToString("D"), value))
        {
            throw new ArgumentException("A lowercase canonical UUID is required.", parameterName);
        }
    }

    [GeneratedRegex("^[a-z][a-z0-9]*(?:\\.[a-z0-9_-]+)+$", RegexOptions.CultureInvariant)]
    private static partial Regex CapabilityIdPattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();

    [GeneratedRegex("^[a-z0-9][a-z0-9._-]{2,127}$", RegexOptions.CultureInvariant)]
    private static partial Regex ArtifactIdPattern();

    [GeneratedRegex("^[a-z][a-z0-9_-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex SandboxHandlePattern();

    [GeneratedRegex("^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$", RegexOptions.CultureInvariant)]
    private static partial Regex TokenPattern();
}
