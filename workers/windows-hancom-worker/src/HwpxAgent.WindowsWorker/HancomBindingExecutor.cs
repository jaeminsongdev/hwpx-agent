using System.Globalization;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.WindowsBridge.V1;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.OpenSsl;
using Org.BouncyCastle.X509;

namespace HwpxAgent.WindowsWorker;

internal interface IHancomPlanExecutionResolver
{
    HancomApprovedPlanExecution Resolve(
        StaExecutePlanCommand command,
        StaExecutionContext context);
}

internal sealed class HancomApprovedPlanExecution : IDisposable
{
    private readonly IReadOnlyList<FileStream> integrityGuards;

    internal HancomApprovedPlanExecution(
        byte[] operationPlan,
        byte[] bindingBundle,
        byte[] trustedPublicKey,
        IReadOnlyList<FileStream>? integrityGuards = null)
    {
        OperationPlan = operationPlan ?? throw new ArgumentNullException(nameof(operationPlan));
        BindingBundle = bindingBundle ?? throw new ArgumentNullException(nameof(bindingBundle));
        TrustedPublicKey = trustedPublicKey ?? throw new ArgumentNullException(nameof(trustedPublicKey));
        this.integrityGuards = integrityGuards ?? [];
    }

    internal byte[] OperationPlan { get; }

    internal byte[] BindingBundle { get; }

    internal byte[] TrustedPublicKey { get; }

    public void Dispose()
    {
        foreach (var guard in integrityGuards)
        {
            guard.Dispose();
        }
    }
}

internal enum HancomBindingError
{
    PlanInvalid,
    BundleInvalid,
    SignatureInvalid,
    TargetMismatch,
    UnknownBinding,
    ArgumentInvalid,
    LeaseConsumed,
    ActionFailed,
}

internal sealed class HancomBindingException : Exception
{
    internal HancomBindingException(HancomBindingError error, bool effectUnknown = false)
        : base($"Hancom binding execution failed closed: {error}.")
    {
        Error = error;
        EffectUnknown = effectUnknown;
    }

    internal HancomBindingException(
        HancomBindingError error,
        Exception innerException,
        bool effectUnknown = false)
        : base($"Hancom binding execution failed closed: {error}.", innerException)
    {
        Error = error;
        EffectUnknown = effectUnknown;
    }

    internal HancomBindingError Error { get; }

    internal bool EffectUnknown { get; }
}

internal sealed record HancomBoundParameter(string ItemName, object Value);

internal sealed record HancomBoundAction(
    string ActionId,
    string? ParameterSetId,
    IReadOnlyList<HancomBoundParameter> Parameters);

internal sealed record HancomBindingExecutionResult(
    int OperationCount,
    string PlanSha256,
    string BundleSha256);

internal sealed partial class HancomBindingExecutor
{
    internal const string EnvelopeSchemaVersion =
        "hwpx-agent.p10-06-signed-binding-envelope/v1";
    internal const string PayloadSchemaVersion =
        "hwpx-agent.p10-06-binding-bundle/v1";
    internal const string OperationPlanSchemaVersion =
        "hwpx-agent.operation-plan/v2";
    private const int MaximumPlanBytes = 4 * 1024 * 1024;
    private const int MaximumEnvelopeBytes = 1024 * 1024;
    private const int MaximumPayloadBytes = 512 * 1024;
    private const int MaximumPublicKeyBytes = 8 * 1024;
    private const int MaximumOperations = 1024;
    private const int MaximumBindings = 4096;
    private const int MaximumArgumentsPerOperation = 64;
    private const int MaximumDependencies = 4096;
    private const int MaximumTextBytes = 64 * 1024;
    private static readonly JsonSerializerOptions StrictJsonOptions = new()
    {
        PropertyNameCaseInsensitive = false,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        MaxDepth = 32,
    };
    internal HancomBindingExecutionResult Execute(
        StaExecutePlanCommand command,
        HancomApprovedPlanExecution approved,
        HancomSession session,
        HancomTargetProfile targetProfile,
        string capabilityRegistrySha256,
        StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(approved);
        ArgumentNullException.ThrowIfNull(session);
        ArgumentNullException.ThrowIfNull(targetProfile);
        ArgumentNullException.ThrowIfNull(context);
        context.ThrowIfCancellationRequested();

        try
        {
            RequireLength(approved.OperationPlan, MaximumPlanBytes, HancomBindingError.PlanInvalid);
            RequireLength(approved.BindingBundle, MaximumEnvelopeBytes, HancomBindingError.BundleInvalid);
            RequireLength(approved.TrustedPublicKey, MaximumPublicKeyBytes, HancomBindingError.SignatureInvalid);

            var expectedBundleSha256 = Hash(approved.BindingBundle);
            if (!string.Equals(
                    expectedBundleSha256,
                    command.BindingBundleSha256,
                    StringComparison.Ordinal))
            {
                throw Fail(HancomBindingError.BundleInvalid);
            }

            var payload = VerifyAndParseBundle(
                approved.BindingBundle,
                approved.TrustedPublicKey,
                command.BindingBundleId,
                targetProfile,
                capabilityRegistrySha256);
            var plan = ParsePlan(approved.OperationPlan);
            var bindings = ValidateBindings(payload.Bindings!);
            var admitted = new HashSet<string>(StringComparer.Ordinal);
            var invocations = new List<HancomBoundAction>(plan.Operations!.Count);

            foreach (var operation in plan.Operations)
            {
                context.ThrowIfCancellationRequested();
                if (!operation.DependsOn!.All(admitted.Contains))
                {
                    throw Fail(HancomBindingError.PlanInvalid);
                }

                if (!bindings.TryGetValue(operation.CapabilityId!, out var binding))
                {
                    throw Fail(HancomBindingError.UnknownBinding);
                }

                var invocation = BindArguments(operation, binding);
                invocations.Add(invocation);
                if (!admitted.Add(operation.OperationId!))
                {
                    throw Fail(HancomBindingError.PlanInvalid);
                }
            }

            foreach (var invocation in invocations)
            {
                context.ThrowIfCancellationRequested();
                session.ExecuteAction(invocation, context);
            }

            return new HancomBindingExecutionResult(
                admitted.Count,
                Hash(approved.OperationPlan),
                expectedBundleSha256);
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception error) when (error is JsonException
            or FormatException
            or InvalidDataException
            or OverflowException
            or ArgumentException)
        {
            throw Fail(HancomBindingError.PlanInvalid, error);
        }
    }

    private static BindingBundlePayload VerifyAndParseBundle(
        byte[] envelopeBytes,
        byte[] publicKeyBytes,
        string expectedBundleId,
        HancomTargetProfile targetProfile,
        string capabilityRegistrySha256)
    {
        SignedBindingEnvelope envelope;
        try
        {
            using var envelopeJson = ParseUniqueJson(
                envelopeBytes,
                MaximumEnvelopeBytes,
                HancomBindingError.BundleInvalid);
            envelope = JsonSerializer.Deserialize<SignedBindingEnvelope>(
                envelopeJson.RootElement.GetRawText(),
                StrictJsonOptions) ?? throw Fail(HancomBindingError.BundleInvalid);
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (Exception error) when (error is JsonException or FormatException)
        {
            throw Fail(HancomBindingError.BundleInvalid, error);
        }

        if (!string.Equals(envelope.SchemaVersion, EnvelopeSchemaVersion, StringComparison.Ordinal)
            || !string.Equals(envelope.Algorithm, "Ed25519", StringComparison.Ordinal)
            || !Sha256Pattern().IsMatch(envelope.PayloadSha256 ?? string.Empty)
            || !Sha256Pattern().IsMatch(envelope.PublicKeySha256 ?? string.Empty)
            || !KeyIdPattern().IsMatch(envelope.KeyId ?? string.Empty))
        {
            throw Fail(HancomBindingError.BundleInvalid);
        }

        byte[] payloadBytes;
        byte[] signature;
        try
        {
            payloadBytes = Convert.FromBase64String(envelope.PayloadBase64 ?? string.Empty);
            signature = Convert.FromBase64String(envelope.SignatureBase64 ?? string.Empty);
        }
        catch (FormatException error)
        {
            throw Fail(HancomBindingError.SignatureInvalid, error);
        }

        RequireLength(payloadBytes, MaximumPayloadBytes, HancomBindingError.BundleInvalid);
        if (signature.Length != 64
            || !string.Equals(
                Convert.ToBase64String(payloadBytes),
                envelope.PayloadBase64,
                StringComparison.Ordinal)
            || !string.Equals(
                Convert.ToBase64String(signature),
                envelope.SignatureBase64,
                StringComparison.Ordinal)
            || !string.Equals(Hash(payloadBytes), envelope.PayloadSha256, StringComparison.Ordinal)
            || !string.Equals(Hash(publicKeyBytes), envelope.PublicKeySha256, StringComparison.Ordinal))
        {
            throw Fail(HancomBindingError.SignatureInvalid);
        }

        var publicKey = ParsePublicKey(publicKeyBytes);
        string keyId;
        try
        {
            var subjectPublicKeyInfo = SubjectPublicKeyInfoFactory
                .CreateSubjectPublicKeyInfo(publicKey)
                .GetDerEncoded();
            keyId = "ed25519-sha256-" + Hash(subjectPublicKeyInfo);
        }
        catch (Exception error)
        {
            throw Fail(HancomBindingError.SignatureInvalid, error);
        }
        if (!string.Equals(keyId, envelope.KeyId, StringComparison.Ordinal))
        {
            throw Fail(HancomBindingError.SignatureInvalid);
        }

        var verifier = new Ed25519Signer();
        verifier.Init(forSigning: false, publicKey);
        verifier.BlockUpdate(payloadBytes, 0, payloadBytes.Length);
        if (!verifier.VerifySignature(signature))
        {
            throw Fail(HancomBindingError.SignatureInvalid);
        }

        BindingBundlePayload payload;
        try
        {
            using var payloadJson = ParseUniqueJson(
                payloadBytes,
                MaximumPayloadBytes,
                HancomBindingError.BundleInvalid);
            payload = JsonSerializer.Deserialize<BindingBundlePayload>(
                payloadJson.RootElement.GetRawText(),
                StrictJsonOptions) ?? throw Fail(HancomBindingError.BundleInvalid);
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (JsonException error)
        {
            throw Fail(HancomBindingError.BundleInvalid, error);
        }

        ValidatePayload(payload, expectedBundleId, targetProfile, capabilityRegistrySha256);
        return payload;
    }

    private static Ed25519PublicKeyParameters ParsePublicKey(byte[] bytes)
    {
        try
        {
            var text = new UTF8Encoding(false, true).GetString(bytes);
            using var reader = new StringReader(text);
            var value = new PemReader(reader).ReadObject();
            if (value is not Ed25519PublicKeyParameters publicKey
                || reader.ReadToEnd().Any(character => !char.IsWhiteSpace(character)))
            {
                throw Fail(HancomBindingError.SignatureInvalid);
            }

            return publicKey;
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw Fail(HancomBindingError.SignatureInvalid, error);
        }
    }

    private static void ValidatePayload(
        BindingBundlePayload payload,
        string expectedBundleId,
        HancomTargetProfile targetProfile,
        string capabilityRegistrySha256)
    {
        targetProfile.Validate();
        if (!string.Equals(payload.SchemaVersion, PayloadSchemaVersion, StringComparison.Ordinal)
            || !SemanticIdPattern().IsMatch(payload.BundleId ?? string.Empty)
            || !string.Equals(payload.BundleId, expectedBundleId, StringComparison.Ordinal)
            || payload.Sequence is 0 or > 1_000_000_000
            || !Sha256Pattern().IsMatch(payload.SourceRegistrySha256 ?? string.Empty)
            || !Sha256Pattern().IsMatch(payload.CapabilityRegistrySha256 ?? string.Empty)
            || !string.Equals(
                payload.CapabilityRegistrySha256,
                capabilityRegistrySha256,
                StringComparison.Ordinal)
            || payload.Target is null
            || !string.Equals(payload.Target.ProfileId, targetProfile.ProfileId, StringComparison.Ordinal)
            || !string.Equals(payload.Target.ProductBuild, targetProfile.ProductBuild, StringComparison.Ordinal)
            || !string.Equals(payload.Target.Locale, targetProfile.Locale, StringComparison.Ordinal)
            || !string.Equals(
                payload.Target.ProcessArchitecture,
                targetProfile.ProcessArchitecture,
                StringComparison.Ordinal)
            || !string.Equals(
                payload.Target.ExecutableSha256,
                targetProfile.ExecutableSha256,
                StringComparison.Ordinal)
            || payload.Authorization is null
            || !payload.Authorization.ExecutionEnabled
            || payload.Authorization.SourceRegistryRoutingEnabled
            || !string.Equals(
                payload.Authorization.Scope,
                "current_pc_exact_target_only",
                StringComparison.Ordinal)
            || !string.Equals(
                payload.Authorization.MinimumProbeState,
                "runtime_verified_current_target",
                StringComparison.Ordinal)
            || payload.Bindings is null
            || payload.Bindings.Count is 0 or > MaximumBindings)
        {
            throw Fail(HancomBindingError.TargetMismatch);
        }
    }

    private static Dictionary<string, BindingDefinition> ValidateBindings(
        IReadOnlyList<BindingDefinition> definitions)
    {
        var bindings = new Dictionary<string, BindingDefinition>(StringComparer.Ordinal);
        foreach (var binding in definitions)
        {
            if (!SemanticIdPattern().IsMatch(binding.CapabilityId ?? string.Empty)
                || ContainsRawAutomationToken(binding.CapabilityId!)
                || !IsPrivateIdentifier(binding.ActionId)
                || !Sha256Pattern().IsMatch(binding.ProbeEvidenceSha256 ?? string.Empty)
                || !string.Equals(binding.TargetMode, "document_global", StringComparison.Ordinal)
                || binding.Parameters is null
                || binding.Parameters.Count > MaximumArgumentsPerOperation
                || !bindings.TryAdd(binding.CapabilityId!, binding))
            {
                throw Fail(HancomBindingError.BundleInvalid);
            }

            if ((binding.Parameters.Count == 0) != (binding.ParameterSetId is null)
                || (binding.ParameterSetId is not null && !IsPrivateIdentifier(binding.ParameterSetId)))
            {
                throw Fail(HancomBindingError.BundleInvalid);
            }

            var argumentIds = new HashSet<string>(StringComparer.Ordinal);
            var itemNames = new HashSet<string>(StringComparer.Ordinal);
            foreach (var parameter in binding.Parameters)
            {
                ValidateParameterDefinition(parameter);
                if (!argumentIds.Add(parameter.ArgumentId!) || !itemNames.Add(parameter.ItemName!))
                {
                    throw Fail(HancomBindingError.BundleInvalid);
                }
            }
        }

        return bindings;
    }

    private static void ValidateParameterDefinition(ParameterDefinition parameter)
    {
        if (!ArgumentIdPattern().IsMatch(parameter.ArgumentId ?? string.Empty)
            || !IsPrivateIdentifier(parameter.ItemName)
            || parameter.MaximumUtf8Bytes is < 0 or > MaximumTextBytes
            || parameter.ScaleNumerator is < -1_000_000_000 or > 1_000_000_000
            || parameter.ScaleDenominator is < 0 or > 1_000_000_000)
        {
            throw Fail(HancomBindingError.BundleInvalid);
        }

        switch ((parameter.SourceValueType, parameter.TargetValueType))
        {
            case ("text", "string"):
                if (parameter.MaximumUtf8Bytes is <= 0
                    || parameter.Minimum is not null
                    || parameter.Maximum is not null
                    || parameter.ScaleNumerator is not null
                    || parameter.ScaleDenominator is not null
                    || parameter.Rounding is not null
                    || parameter.EnumValues is not null)
                {
                    throw Fail(HancomBindingError.BundleInvalid);
                }

                break;
            case ("text", "int32_enum"):
                if (parameter.MaximumUtf8Bytes is <= 0
                    || parameter.Minimum is not null
                    || parameter.Maximum is not null
                    || parameter.ScaleNumerator is not null
                    || parameter.ScaleDenominator is not null
                    || parameter.Rounding is not null
                    || parameter.EnumValues is null
                    || parameter.EnumValues.Count is 0 or > 256
                    || parameter.EnumValues.Keys.Any(value => !IsSemanticEnum(value))
                    || parameter.EnumValues.Values.Any(value => value is < int.MinValue or > int.MaxValue))
                {
                    throw Fail(HancomBindingError.BundleInvalid);
                }

                break;
            case ("boolean", "boolean"):
                if (parameter.MaximumUtf8Bytes is not null
                    || parameter.Minimum is not null
                    || parameter.Maximum is not null
                    || parameter.ScaleNumerator is not null
                    || parameter.ScaleDenominator is not null
                    || parameter.Rounding is not null
                    || parameter.EnumValues is not null)
                {
                    throw Fail(HancomBindingError.BundleInvalid);
                }

                break;
            case ("integer", "int32"):
            case ("length_micrometers", "int32"):
            case ("point_milli", "int32"):
            case ("ratio_millionths", "int32"):
            case ("angle_microdegrees", "int32"):
                if (parameter.MaximumUtf8Bytes is not null
                    || parameter.Minimum is null
                    || parameter.Maximum is null
                    || parameter.Minimum > parameter.Maximum
                    || parameter.Minimum < int.MinValue
                    || parameter.Maximum > int.MaxValue
                    || parameter.ScaleNumerator is null or 0
                    || parameter.ScaleDenominator is null or <= 0
                    || parameter.Rounding is not ("exact" or "half_away_from_zero")
                    || parameter.EnumValues is not null)
                {
                    throw Fail(HancomBindingError.BundleInvalid);
                }

                break;
            default:
                throw Fail(HancomBindingError.BundleInvalid);
        }
    }

    private static OperationPlanDocument ParsePlan(byte[] bytes)
    {
        OperationPlanDocument plan;
        try
        {
            using var planJson = ParseUniqueJson(
                bytes,
                MaximumPlanBytes,
                HancomBindingError.PlanInvalid);
            plan = JsonSerializer.Deserialize<OperationPlanDocument>(
                planJson.RootElement.GetRawText(),
                StrictJsonOptions) ?? throw Fail(HancomBindingError.PlanInvalid);
        }
        catch (HancomBindingException)
        {
            throw;
        }
        catch (JsonException error)
        {
            throw Fail(HancomBindingError.PlanInvalid, error);
        }

        if (!string.Equals(plan.SchemaVersion, OperationPlanSchemaVersion, StringComparison.Ordinal)
            || !BoundedIdentifier(plan.PlanId)
            || !BoundedIdentifier(plan.BaseRevision)
            || !IsDigestArray(plan.BaseGraphSha256)
            || !string.Equals(plan.FailurePolicy, "atomic", StringComparison.Ordinal)
            || plan.Operations is null
            || plan.Operations.Count is 0 or > MaximumOperations)
        {
            throw Fail(HancomBindingError.PlanInvalid);
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        var totalDependencies = 0;
        foreach (var operation in plan.Operations)
        {
            if (!BoundedIdentifier(operation.OperationId)
                || !SemanticIdPattern().IsMatch(operation.CapabilityId ?? string.Empty)
                || ContainsRawAutomationToken(operation.CapabilityId!)
                || operation.Arguments is null
                || operation.Arguments.Count > MaximumArgumentsPerOperation
                || operation.DependsOn is null
                || operation.DependsOn.Count > MaximumDependencies
                || !ValidateResolvedTarget(operation.Target)
                || !ids.Add(operation.OperationId!))
            {
                throw Fail(HancomBindingError.PlanInvalid);
            }

            totalDependencies = checked(totalDependencies + operation.DependsOn.Count);
            if (totalDependencies > MaximumDependencies
                || operation.DependsOn.Distinct(StringComparer.Ordinal).Count()
                    != operation.DependsOn.Count
                || !operation.DependsOn.SequenceEqual(
                    operation.DependsOn.OrderBy(value => value, StringComparer.Ordinal))
                || operation.DependsOn.Any(dependency => !ids.Contains(dependency)))
            {
                throw Fail(HancomBindingError.PlanInvalid);
            }

            foreach (var (argumentId, argument) in operation.Arguments)
            {
                if (!ArgumentIdPattern().IsMatch(argumentId)
                    || !ValidateCompiledArgument(argument))
                {
                    throw Fail(HancomBindingError.PlanInvalid);
                }
            }
        }

        return plan;
    }

    private static bool ValidateResolvedTarget(ResolvedTargetDocument? target)
    {
        if (target is null
            || !BoundedIdentifier(target.NodeId)
            || target.NodeKind is not (
                "paragraph" or "table" or "equation" or "drawing" or "chart" or
                "field" or "form_control" or "break" or "embedded_object")
            || !IsDigestArray(target.NodeFingerprintSha256)
            || target.StructuralPath.ValueKind != JsonValueKind.Object)
        {
            return false;
        }

        if (target.TextRange is not null
            && target.TextRange.StartScalar > target.TextRange.EndScalar)
        {
            return false;
        }

        return ValidateStructuralPath(target.StructuralPath);
    }

    private static bool ValidateStructuralPath(JsonElement path)
    {
        if (!HasExactProperties(path, "root", "steps")
            || !path.TryGetProperty("root", out var root)
            || root.ValueKind != JsonValueKind.Object
            || !path.TryGetProperty("steps", out var steps)
            || steps.ValueKind != JsonValueKind.Array
            || steps.GetArrayLength() is 0 or > 256)
        {
            return false;
        }

        if (!HasExactProperties(root, "root", "index")
            || !root.TryGetProperty("root", out var rootKind)
            || rootKind.ValueKind != JsonValueKind.String
            || rootKind.GetString() is not ("section" or "note")
            || !root.TryGetProperty("index", out var rootIndex)
            || !rootIndex.TryGetUInt32(out _))
        {
            return false;
        }

        foreach (var step in steps.EnumerateArray())
        {
            if (step.ValueKind != JsonValueKind.Object
                || !step.TryGetProperty("step", out var stepKind)
                || stepKind.ValueKind != JsonValueKind.String)
            {
                return false;
            }

            switch (stepKind.GetString())
            {
                case "flow_child":
                    if (!HasExactProperties(step, "step", "index", "expected_kind")
                        || !step.GetProperty("index").TryGetUInt32(out _)
                        || step.GetProperty("expected_kind").ValueKind != JsonValueKind.String)
                    {
                        return false;
                    }

                    break;
                case "table_cell":
                    if (!HasExactProperties(step, "step", "row", "column")
                        || !step.GetProperty("row").TryGetUInt32(out _)
                        || !step.GetProperty("column").TryGetUInt32(out _))
                    {
                        return false;
                    }

                    break;
                default:
                    return false;
            }
        }

        return true;
    }

    private static bool ValidateCompiledArgument(CompiledArgumentDocument? argument)
    {
        if (argument is null
            || argument.Source is not ("caller" or "capability_default")
            || !IsDigestArray(argument.ValueSha256)
            || argument.Value.ValueKind != JsonValueKind.Object
            || !HasExactProperties(argument.Value, "value_type", "value")
            || !argument.Value.TryGetProperty("value_type", out var type)
            || type.ValueKind != JsonValueKind.String
            || !argument.Value.TryGetProperty("value", out var value)
            || !ValidateCanonicalValue(type.GetString(), value)
            || !ValidateConversionReceipt(argument.ConversionReceipt))
        {
            return false;
        }

        var canonical = SerializeCanonicalValue(type.GetString()!, value);
        return CryptographicOperations.FixedTimeEquals(
            SHA256.HashData(canonical),
            argument.ValueSha256!.Select(number => checked((byte)number)).ToArray());
    }

    private static bool ValidateCanonicalValue(string? type, JsonElement value) => type switch
    {
        "text" => value.ValueKind == JsonValueKind.String
            && Encoding.UTF8.GetByteCount(value.GetString()!) <= MaximumTextBytes
            && value.GetString()!.All(character =>
                !char.IsControl(character) || character is '\n' or '\t'),
        "boolean" => value.ValueKind is JsonValueKind.True or JsonValueKind.False,
        "integer" or "length_micrometers" or "point_milli" or
            "ratio_millionths" or "angle_microdegrees" =>
            value.ValueKind == JsonValueKind.Number && value.TryGetInt64(out _),
        _ => false,
    };

    private static bool ValidateConversionReceipt(JsonElement receipt)
    {
        if (receipt.ValueKind == JsonValueKind.Null)
        {
            return true;
        }

        if (receipt.ValueKind != JsonValueKind.Object
            || !HasExactProperties(
                receipt,
                "source_unit",
                "target_unit",
                "source_numerator",
                "source_denominator",
                "normalized_value",
                "rounding_delta_numerator",
                "rounding_delta_denominator",
                "context_dpi"))
        {
            return false;
        }

        return receipt.GetProperty("source_unit").ValueKind == JsonValueKind.String
            && receipt.GetProperty("target_unit").ValueKind == JsonValueKind.String
            && receipt.GetProperty("source_numerator").TryGetInt64(out _)
            && receipt.GetProperty("source_denominator").TryGetUInt32(out var denominator)
            && denominator > 0
            && receipt.GetProperty("normalized_value").TryGetInt64(out _)
            && receipt.GetProperty("rounding_delta_numerator").TryGetInt64(out _)
            && receipt.GetProperty("rounding_delta_denominator").TryGetUInt64(out var roundingDenominator)
            && roundingDenominator > 0
            && (receipt.GetProperty("context_dpi").ValueKind == JsonValueKind.Null
                || receipt.GetProperty("context_dpi").TryGetUInt32(out var dpi) && dpi > 0);
    }

    private static byte[] SerializeCanonicalValue(string type, JsonElement value)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions
        {
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            Indented = false,
        }))
        {
            writer.WriteStartObject();
            writer.WriteString("value_type", type);
            writer.WritePropertyName("value");
            value.WriteTo(writer);
            writer.WriteEndObject();
        }

        return stream.ToArray();
    }

    private static HancomBoundAction BindArguments(
        CompiledOperationDocument operation,
        BindingDefinition binding)
    {
        var definitions = binding.Parameters!
            .ToDictionary(parameter => parameter.ArgumentId!, StringComparer.Ordinal);
        if (operation.Arguments!.Keys.Any(argument => !definitions.ContainsKey(argument))
            || definitions.Values.Any(parameter =>
                parameter.Required && !operation.Arguments.ContainsKey(parameter.ArgumentId!)))
        {
            throw Fail(HancomBindingError.ArgumentInvalid);
        }

        var values = new List<HancomBoundParameter>(operation.Arguments.Count);
        foreach (var parameter in binding.Parameters!)
        {
            if (!operation.Arguments.TryGetValue(parameter.ArgumentId!, out var argument))
            {
                continue;
            }

            var valueType = argument.Value.GetProperty("value_type").GetString();
            if (!string.Equals(valueType, parameter.SourceValueType, StringComparison.Ordinal))
            {
                throw Fail(HancomBindingError.ArgumentInvalid);
            }

            values.Add(new HancomBoundParameter(
                parameter.ItemName!,
                ConvertArgument(argument.Value.GetProperty("value"), parameter)));
        }

        return new HancomBoundAction(binding.ActionId!, binding.ParameterSetId, values);
    }

    private static object ConvertArgument(JsonElement value, ParameterDefinition parameter)
    {
        switch ((parameter.SourceValueType, parameter.TargetValueType))
        {
            case ("text", "string"):
                {
                    var text = value.GetString()!;
                    if (Encoding.UTF8.GetByteCount(text) > parameter.MaximumUtf8Bytes)
                    {
                        throw Fail(HancomBindingError.ArgumentInvalid);
                    }

                    return text;
                }
            case ("text", "int32_enum"):
                {
                    var text = value.GetString()!;
                    if (Encoding.UTF8.GetByteCount(text) > parameter.MaximumUtf8Bytes
                        || !parameter.EnumValues!.TryGetValue(text, out var mapped)
                        || mapped is < int.MinValue or > int.MaxValue)
                    {
                        throw Fail(HancomBindingError.ArgumentInvalid);
                    }

                    return checked((int)mapped);
                }
            case ("boolean", "boolean"):
                return value.GetBoolean();
            default:
                {
                    if (!value.TryGetInt64(out var source))
                    {
                        throw Fail(HancomBindingError.ArgumentInvalid);
                    }

                    var converted = ScaleInteger(
                        source,
                        parameter.ScaleNumerator!.Value,
                        parameter.ScaleDenominator!.Value,
                        parameter.Rounding!);
                    if (converted < parameter.Minimum || converted > parameter.Maximum
                        || converted is < int.MinValue or > int.MaxValue)
                    {
                        throw Fail(HancomBindingError.ArgumentInvalid);
                    }

                    return checked((int)converted);
                }
        }
    }

    private static long ScaleInteger(long source, long numerator, long denominator, string rounding)
    {
        var product = new BigInteger(source) * numerator;
        var divisor = new BigInteger(denominator);
        var quotient = BigInteger.DivRem(product, divisor, out var remainder);
        if (remainder != 0)
        {
            if (string.Equals(rounding, "exact", StringComparison.Ordinal))
            {
                throw Fail(HancomBindingError.ArgumentInvalid);
            }

            var doubled = BigInteger.Abs(remainder) * 2;
            if (doubled >= divisor)
            {
                quotient += product.Sign;
            }
        }

        if (quotient < long.MinValue || quotient > long.MaxValue)
        {
            throw Fail(HancomBindingError.ArgumentInvalid);
        }

        return (long)quotient;
    }

    private static JsonDocument ParseUniqueJson(
        byte[] bytes,
        int maximum,
        HancomBindingError error)
    {
        RequireLength(bytes, maximum, error);
        var document = JsonDocument.Parse(bytes, new JsonDocumentOptions
        {
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow,
            MaxDepth = 32,
        });
        try
        {
            RejectDuplicateProperties(document.RootElement, error);
            return document;
        }
        catch
        {
            document.Dispose();
            throw;
        }
    }

    private static void RejectDuplicateProperties(JsonElement value, HancomBindingError error)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            var names = new HashSet<string>(StringComparer.Ordinal);
            foreach (var property in value.EnumerateObject())
            {
                if (!names.Add(property.Name))
                {
                    throw Fail(error);
                }

                RejectDuplicateProperties(property.Value, error);
            }
        }
        else if (value.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in value.EnumerateArray())
            {
                RejectDuplicateProperties(item, error);
            }
        }
    }

    private static bool HasExactProperties(JsonElement value, params string[] expected)
    {
        if (value.ValueKind != JsonValueKind.Object)
        {
            return false;
        }

        var actual = value.EnumerateObject().Select(property => property.Name).ToArray();
        return actual.Length == expected.Length
            && actual.ToHashSet(StringComparer.Ordinal).SetEquals(expected);
    }

    private static bool IsDigestArray(IReadOnlyList<int>? values) =>
        values is { Count: 32 } && values.All(value => value is >= 0 and <= byte.MaxValue);

    private static bool BoundedIdentifier(string? value) =>
        !string.IsNullOrEmpty(value)
        && Encoding.UTF8.GetByteCount(value) <= 512
        && value.All(character => !char.IsControl(character));

    private static bool IsSemanticEnum(string value) =>
        !string.IsNullOrEmpty(value)
        && Encoding.UTF8.GetByteCount(value) <= 128
        && value.All(character =>
            char.IsAsciiLetterOrDigit(character) || character is '_' or '-' or '.');

    private static bool IsPrivateIdentifier(string? value) =>
        !string.IsNullOrEmpty(value)
        && Encoding.UTF8.GetByteCount(value) <= 512
        && value.All(character =>
        {
            var category = CharUnicodeInfo.GetUnicodeCategory(character);
            return category is not (
                UnicodeCategory.Control or
                UnicodeCategory.Format or
                UnicodeCategory.Surrogate or
                UnicodeCategory.PrivateUse or
                UnicodeCategory.OtherNotAssigned);
        });

    private static bool ContainsRawAutomationToken(string value) =>
        value.Contains("haction", StringComparison.OrdinalIgnoreCase)
        || value.Contains("parameterset", StringComparison.OrdinalIgnoreCase);

    private static void RequireLength(byte[] value, int maximum, HancomBindingError error)
    {
        if (value.Length is <= 0 || value.Length > maximum)
        {
            throw Fail(error);
        }
    }

    private static string Hash(byte[] value) =>
        Convert.ToHexStringLower(SHA256.HashData(value));

    private static HancomBindingException Fail(
        HancomBindingError error,
        Exception? inner = null,
        bool effectUnknown = false) =>
        inner is null
            ? new HancomBindingException(error, effectUnknown)
            : new HancomBindingException(error, inner, effectUnknown);

    [GeneratedRegex("^[a-z][a-z0-9]*(?:\\.[a-z0-9_-]+)+$", RegexOptions.CultureInvariant)]
    private static partial Regex SemanticIdPattern();

    [GeneratedRegex("^[a-z][a-z0-9_-]{0,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex ArgumentIdPattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();

    [GeneratedRegex("^ed25519-sha256-[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex KeyIdPattern();

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class SignedBindingEnvelope
    {
        [JsonPropertyName("schema_version")]
        public string? SchemaVersion { get; init; }

        [JsonPropertyName("algorithm")]
        public string? Algorithm { get; init; }

        [JsonPropertyName("key_id")]
        public string? KeyId { get; init; }

        [JsonPropertyName("public_key_sha256")]
        public string? PublicKeySha256 { get; init; }

        [JsonPropertyName("payload_sha256")]
        public string? PayloadSha256 { get; init; }

        [JsonPropertyName("payload_base64")]
        public string? PayloadBase64 { get; init; }

        [JsonPropertyName("signature_base64")]
        public string? SignatureBase64 { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class BindingBundlePayload
    {
        [JsonPropertyName("schema_version")]
        public string? SchemaVersion { get; init; }

        [JsonPropertyName("bundle_id")]
        public string? BundleId { get; init; }

        [JsonPropertyName("sequence")]
        public ulong Sequence { get; init; }

        [JsonPropertyName("source_registry_sha256")]
        public string? SourceRegistrySha256 { get; init; }

        [JsonPropertyName("capability_registry_sha256")]
        public string? CapabilityRegistrySha256 { get; init; }

        [JsonPropertyName("target")]
        public BindingTarget? Target { get; init; }

        [JsonPropertyName("authorization")]
        public BindingAuthorization? Authorization { get; init; }

        [JsonPropertyName("bindings")]
        public List<BindingDefinition>? Bindings { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class BindingTarget
    {
        [JsonPropertyName("profile_id")]
        public string? ProfileId { get; init; }

        [JsonPropertyName("product_build")]
        public string? ProductBuild { get; init; }

        [JsonPropertyName("locale")]
        public string? Locale { get; init; }

        [JsonPropertyName("process_architecture")]
        public string? ProcessArchitecture { get; init; }

        [JsonPropertyName("executable_sha256")]
        public string? ExecutableSha256 { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class BindingAuthorization
    {
        [JsonPropertyName("execution_enabled")]
        public bool ExecutionEnabled { get; init; }

        [JsonPropertyName("source_registry_routing_enabled")]
        public bool SourceRegistryRoutingEnabled { get; init; }

        [JsonPropertyName("scope")]
        public string? Scope { get; init; }

        [JsonPropertyName("minimum_probe_state")]
        public string? MinimumProbeState { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class BindingDefinition
    {
        [JsonPropertyName("capability_id")]
        public string? CapabilityId { get; init; }

        [JsonPropertyName("action_id")]
        public string? ActionId { get; init; }

        [JsonPropertyName("parameter_set_id")]
        public string? ParameterSetId { get; init; }

        [JsonPropertyName("probe_evidence_sha256")]
        public string? ProbeEvidenceSha256 { get; init; }

        [JsonPropertyName("target_mode")]
        public string? TargetMode { get; init; }

        [JsonPropertyName("parameters")]
        public List<ParameterDefinition>? Parameters { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class ParameterDefinition
    {
        [JsonPropertyName("argument_id")]
        public string? ArgumentId { get; init; }

        [JsonPropertyName("item_name")]
        public string? ItemName { get; init; }

        [JsonPropertyName("source_value_type")]
        public string? SourceValueType { get; init; }

        [JsonPropertyName("target_value_type")]
        public string? TargetValueType { get; init; }

        [JsonPropertyName("required")]
        public bool Required { get; init; }

        [JsonPropertyName("minimum")]
        public long? Minimum { get; init; }

        [JsonPropertyName("maximum")]
        public long? Maximum { get; init; }

        [JsonPropertyName("maximum_utf8_bytes")]
        public int? MaximumUtf8Bytes { get; init; }

        [JsonPropertyName("scale_numerator")]
        public long? ScaleNumerator { get; init; }

        [JsonPropertyName("scale_denominator")]
        public long? ScaleDenominator { get; init; }

        [JsonPropertyName("rounding")]
        public string? Rounding { get; init; }

        [JsonPropertyName("enum_values")]
        public Dictionary<string, long>? EnumValues { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class OperationPlanDocument
    {
        [JsonPropertyName("schema_version")]
        public string? SchemaVersion { get; init; }

        [JsonPropertyName("plan_id")]
        public string? PlanId { get; init; }

        [JsonPropertyName("base_revision")]
        public string? BaseRevision { get; init; }

        [JsonPropertyName("base_graph_sha256")]
        public List<int>? BaseGraphSha256 { get; init; }

        [JsonPropertyName("failure_policy")]
        public string? FailurePolicy { get; init; }

        [JsonPropertyName("operations")]
        public List<CompiledOperationDocument>? Operations { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class CompiledOperationDocument
    {
        [JsonPropertyName("operation_id")]
        public string? OperationId { get; init; }

        [JsonPropertyName("capability_id")]
        public string? CapabilityId { get; init; }

        [JsonPropertyName("target")]
        public ResolvedTargetDocument? Target { get; init; }

        [JsonPropertyName("arguments")]
        public Dictionary<string, CompiledArgumentDocument>? Arguments { get; init; }

        [JsonPropertyName("depends_on")]
        public List<string>? DependsOn { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class ResolvedTargetDocument
    {
        [JsonPropertyName("node_id")]
        public string? NodeId { get; init; }

        [JsonPropertyName("node_kind")]
        public string? NodeKind { get; init; }

        [JsonPropertyName("structural_path")]
        public JsonElement StructuralPath { get; init; }

        [JsonPropertyName("text_range")]
        public TextRangeDocument? TextRange { get; init; }

        [JsonPropertyName("node_fingerprint_sha256")]
        public List<int>? NodeFingerprintSha256 { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class TextRangeDocument
    {
        [JsonPropertyName("start_scalar")]
        public ulong StartScalar { get; init; }

        [JsonPropertyName("end_scalar")]
        public ulong EndScalar { get; init; }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class CompiledArgumentDocument
    {
        [JsonPropertyName("source")]
        public string? Source { get; init; }

        [JsonPropertyName("value")]
        public JsonElement Value { get; init; }

        [JsonPropertyName("conversion_receipt")]
        public JsonElement ConversionReceipt { get; init; }

        [JsonPropertyName("value_sha256")]
        public List<int>? ValueSha256 { get; init; }
    }
}
