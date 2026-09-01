using System.Text.RegularExpressions;
using HwpxAgent.Protocol.Foundation.V1;

namespace HwpxAgent.WindowsWorker;

/// <summary>
/// P01 semantic boundary. COM/HAction 실행기는 의도적으로 존재하지 않는다.
/// </summary>
public static partial class WorkerBoundary
{
    private const int Sha256HexLength = 64;
    private const ulong MaxArtifactBytes = 1_073_741_824;

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

    private static void RequireGuid(string value, string parameterName)
    {
        if (!Guid.TryParseExact(value, "D", out _))
        {
            throw new ArgumentException("A canonical UUID is required.", parameterName);
        }
    }

    [GeneratedRegex("^[a-z][a-z0-9]*(?:\\.[a-z0-9_-]+)+$", RegexOptions.CultureInvariant)]
    private static partial Regex CapabilityIdPattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();

    [GeneratedRegex("^[a-z0-9][a-z0-9._-]{2,127}$", RegexOptions.CultureInvariant)]
    private static partial Regex ArtifactIdPattern();
}
