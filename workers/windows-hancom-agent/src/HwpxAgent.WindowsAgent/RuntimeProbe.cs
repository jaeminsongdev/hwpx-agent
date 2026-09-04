using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
using Microsoft.Win32;

namespace HwpxAgent.WindowsAgent;

internal sealed record MaterializedRuntimeProbe(
    RuntimeProbeReceipt Receipt,
    byte[] EvidenceBytes);

internal static class RuntimeProbeMaterializer
{
    private const string EvidenceSchema = "hwpx-agent.runtime-probe-evidence/v1";
    private static readonly string[] RequiredCoreCapabilities =
    [
        "agent.target_identity",
        "agent.com_registration",
        "agent.capability_registry",
        "agent.security_file_path_module",
        "agent.zero_hancom_processes",
    ];

    internal static MaterializedRuntimeProbe Materialize(
        WindowsAgentConfiguration configuration,
        RuntimeProbeObservation observation,
        ulong nowUnixMs)
    {
        ArgumentNullException.ThrowIfNull(configuration);
        ArgumentNullException.ThrowIfNull(observation);
        if (!string.Equals(
                observation.PolicyId,
                configuration.RuntimeProbe.PolicyId,
                StringComparison.Ordinal)
            || observation.TargetProfile is null
            || !observation.TargetProfile.Equals(configuration.TargetProfile)
            || !string.Equals(
                observation.CapabilityRegistrySha256,
                configuration.CapabilityRegistrySha256,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ProfileMismatch);
        }

        if (observation.Health == ProbeHealth.Unspecified
            || observation.ObservedAtUnixMs == 0
            || observation.ObservedAtUnixMs > checked(nowUnixMs + 300_000UL)
            || nowUnixMs > checked(
                observation.ObservedAtUnixMs
                + configuration.RuntimeProbe.MaximumProbeAgeSeconds * 1_000UL))
        {
            throw new AgentProtocolException(AgentProtocolError.RuntimeProbeInvalid);
        }

        if (observation.RawPathStored
            || observation.RawDocumentContentStored
            || observation.UserDocumentScanned
            || observation.ExternalNetworkInvoked
            || observation.SystemSettingChanged
            || observation.HancomProcessStarted)
        {
            throw new AgentProtocolException(AgentProtocolError.PolicyDenied);
        }

        if (observation.Capabilities is null
            || observation.Capabilities.Count is 0 or > 256)
        {
            throw new AgentProtocolException(AgentProtocolError.RuntimeProbeInvalid);
        }

        var capabilities = observation.Capabilities
            .OrderBy(item => item.CapabilityId, StringComparer.Ordinal)
            .ToArray();
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var capability in capabilities)
        {
            ArgumentNullException.ThrowIfNull(capability);
            AgentValidation.RequireSemanticId(capability.CapabilityId);
            if (!IsSafeCode(capability.SafeCode))
            {
                throw new AgentProtocolException(AgentProtocolError.UnsafeIdentifier);
            }
            AgentValidation.RequireDigest(capability.ObservationSha256);
            if (!ids.Add(capability.CapabilityId)
                || capability.State is not (
                    RuntimeCapabilityState.Verified
                    or RuntimeCapabilityState.Unavailable
                    or RuntimeCapabilityState.Unverified
                    or RuntimeCapabilityState.Drifted))
            {
                throw new AgentProtocolException(AgentProtocolError.RuntimeProbeInvalid);
            }
        }

        if (RequiredCoreCapabilities.Any(id =>
            !capabilities.Any(item =>
                item.RequiredForLease
                && string.Equals(item.CapabilityId, id, StringComparison.Ordinal))))
        {
            throw new AgentProtocolException(AgentProtocolError.RuntimeProbeInvalid);
        }

        var hasRequiredFailure = capabilities.Any(
            item => item.RequiredForLease && item.State != RuntimeCapabilityState.Verified);
        var hasAnyFailure = capabilities.Any(item => item.State != RuntimeCapabilityState.Verified);
        var healthConsistent = observation.Health switch
        {
            ProbeHealth.Healthy => !hasAnyFailure,
            ProbeHealth.Degraded => hasAnyFailure && !hasRequiredFailure,
            ProbeHealth.Unroutable => hasRequiredFailure,
            _ => false,
        };
        if (!healthConsistent)
        {
            throw new AgentProtocolException(AgentProtocolError.RuntimeProbeInvalid);
        }

        var capabilitySet = new StringBuilder();
        foreach (var capability in capabilities)
        {
            capabilitySet
                .Append(capability.CapabilityId).Append('|')
                .Append((int)capability.State).Append('|')
                .Append(capability.RequiredForLease ? '1' : '0').Append('|')
                .Append(capability.ObservationSha256).Append('\n');
        }

        var capabilitySetSha256 = Sha256(Encoding.UTF8.GetBytes(capabilitySet.ToString()));
        var evidence = new
        {
            schema_version = EvidenceSchema,
            policy_id = configuration.RuntimeProbe.PolicyId,
            observed_at_unix_ms = observation.ObservedAtUnixMs,
            health = observation.Health.ToString().ToLowerInvariant(),
            target_profile = new
            {
                profile_id = observation.TargetProfile.ProfileId,
                product_build = observation.TargetProfile.ProductBuild,
                locale = observation.TargetProfile.Locale,
                process_architecture = observation.TargetProfile.ProcessArchitecture,
                executable_sha256 = observation.TargetProfile.ExecutableSha256,
                environment_digest = observation.TargetProfile.EnvironmentDigest,
            },
            capability_registry_sha256 = configuration.CapabilityRegistrySha256,
            capability_set_sha256 = capabilitySetSha256,
            capabilities = capabilities.Select(item => new
            {
                capability_id = item.CapabilityId,
                state = item.State.ToString().ToLowerInvariant(),
                required_for_lease = item.RequiredForLease,
                safe_code = item.SafeCode,
                observation_sha256 = item.ObservationSha256,
            }),
            privacy = new
            {
                raw_path_stored = false,
                raw_document_content_stored = false,
                user_document_scanned = false,
                external_network_invoked = false,
                system_setting_changed = false,
                hancom_process_started = false,
            },
        };
        var evidenceBytes = JsonSerializer.SerializeToUtf8Bytes(evidence, new JsonSerializerOptions
        {
            PropertyNamingPolicy = null,
            WriteIndented = false,
        });
        if ((uint)evidenceBytes.Length > configuration.RuntimeProbe.MaximumEvidenceBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.OutputLimit);
        }

        var evidenceSha256 = Sha256(evidenceBytes);
        return new MaterializedRuntimeProbe(
            new RuntimeProbeReceipt
            {
                TargetProfile = observation.TargetProfile.Clone(),
                Health = observation.Health,
                CapabilityRegistrySha256 = configuration.CapabilityRegistrySha256,
                CapabilitySetSha256 = capabilitySetSha256,
                Evidence = new ArtifactRef
                {
                    ArtifactId = configuration.RuntimeProbe.EvidenceArtifactId,
                    Sha256 = evidenceSha256,
                    SizeBytes = (ulong)evidenceBytes.Length,
                },
                ObservedAtUnixMs = observation.ObservedAtUnixMs,
            },
            evidenceBytes);
    }

    internal static string Sha256(byte[] bytes) =>
        Convert.ToHexStringLower(SHA256.HashData(bytes));

    private static bool IsSafeCode(string? value) =>
        value is { Length: >= 3 and <= 64 }
        && value[0] is >= 'a' and <= 'z'
        && value.All(character =>
            character is >= 'a' and <= 'z'
            or >= '0' and <= '9'
            or '.' or '_' or '-');
}

public sealed record RuntimeEvidencePin(
    string CapabilityId,
    string Path,
    string Sha256,
    bool RequiredForLease);

public sealed record CurrentPcRuntimeProbePin(
    string PolicyId,
    TargetProfileIdentity TargetProfile,
    string TargetExecutablePath,
    string ProgId,
    string Clsid,
    string CapabilityRegistryPath,
    string CapabilityRegistrySha256,
    IReadOnlyList<RuntimeEvidencePin> EvidencePins);

public sealed class CurrentPcRuntimeProbeCollector : IRuntimeProbeCollector
{
    private static readonly Regex LocalServerPattern = new(
        "^(?:\\\"(?<path>[^\\\"]+\\.exe)\\\"|(?<path>.+?\\.exe))(?:\\s|$)",
        RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);
    private readonly CurrentPcRuntimeProbePin pin;
    private readonly HancomSecurityModulePin? securityModule;
    private readonly TimeProvider timeProvider;

    public CurrentPcRuntimeProbeCollector(
        CurrentPcRuntimeProbePin pin,
        HancomSecurityModulePin? securityModule,
        TimeProvider? timeProvider = null)
    {
        ArgumentNullException.ThrowIfNull(pin);
        AgentValidation.RequireSemanticId(pin.PolicyId);
        AgentValidation.RequireDigest(pin.CapabilityRegistrySha256);
        if (pin.TargetProfile is null
            || string.IsNullOrWhiteSpace(pin.ProgId)
            || string.IsNullOrWhiteSpace(pin.Clsid)
            || pin.EvidencePins is null
            || pin.EvidencePins.Count is 0 or > 32)
        {
            throw new ArgumentException("The current-PC runtime probe pin is incomplete.", nameof(pin));
        }

        foreach (var path in new[] { pin.TargetExecutablePath, pin.CapabilityRegistryPath })
        {
            RequireBoundedAbsolutePath(path);
        }

        foreach (var evidence in pin.EvidencePins)
        {
            AgentValidation.RequireSemanticId(evidence.CapabilityId);
            AgentValidation.RequireDigest(evidence.Sha256);
            RequireBoundedAbsolutePath(evidence.Path);
        }

        if (pin.EvidencePins.Select(item => item.CapabilityId).Distinct(StringComparer.Ordinal).Count()
            != pin.EvidencePins.Count)
        {
            throw new ArgumentException("Runtime evidence capability IDs must be unique.", nameof(pin));
        }

        this.pin = pin;
        this.securityModule = securityModule;
        this.timeProvider = timeProvider ?? TimeProvider.System;
    }

    public Task<RuntimeProbeObservation> ObserveAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var capabilities = new List<RuntimeCapabilityObservation>();

        var executableDigest = TryHashPlainFile(pin.TargetExecutablePath, 64 * 1024 * 1024, out var targetHash)
            ? targetHash
            : SafeDigest("target-executable-unavailable");
        var fileVersion = File.Exists(pin.TargetExecutablePath)
            ? NormalizeVersion(FileVersionInfo.GetVersionInfo(pin.TargetExecutablePath).FileVersion)
            : null;
        var architecture = TryReadPeMachine(pin.TargetExecutablePath, out var machine)
            ? machine
            : "unknown";
        var observedTarget = pin.TargetProfile.Clone();
        observedTarget.ProductBuild = fileVersion ?? "unavailable";
        observedTarget.ProcessArchitecture = architecture;
        observedTarget.ExecutableSha256 = executableDigest;
        observedTarget.Locale = CultureInfo.CurrentCulture.Name;
        var targetMatches = observedTarget.Equals(pin.TargetProfile);
        capabilities.Add(Capability(
            "agent.target_identity",
            targetMatches ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Drifted,
            required: true,
            targetMatches ? "exact_match" : "identity_drift",
            executableDigest));

        var comMatches = TryReadComRegistration(out var registeredClsid, out var registeredServer)
            && string.Equals(registeredClsid, pin.Clsid, StringComparison.OrdinalIgnoreCase)
            && string.Equals(
                Path.GetFullPath(registeredServer),
                Path.GetFullPath(pin.TargetExecutablePath),
                StringComparison.OrdinalIgnoreCase);
        capabilities.Add(Capability(
            "agent.com_registration",
            comMatches ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Drifted,
            required: true,
            comMatches ? "registry32_exact_match" : "registry32_mismatch",
            SafeDigest(comMatches ? "com-match" : "com-mismatch")));

        var registryReadable = TryHashPlainFile(
            pin.CapabilityRegistryPath,
            64 * 1024 * 1024,
            out var registryHash);
        var registryMatches = registryReadable
            && string.Equals(registryHash, pin.CapabilityRegistrySha256, StringComparison.Ordinal);
        capabilities.Add(Capability(
            "agent.capability_registry",
            registryMatches ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Drifted,
            required: true,
            registryMatches ? "exact_match" : "digest_mismatch",
            registryReadable ? registryHash : SafeDigest("registry-unavailable")));

        foreach (var evidence in pin.EvidencePins)
        {
            var readable = TryHashPlainFile(evidence.Path, 64 * 1024 * 1024, out var observedHash);
            var matches = readable && string.Equals(observedHash, evidence.Sha256, StringComparison.Ordinal);
            capabilities.Add(Capability(
                evidence.CapabilityId,
                matches ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Drifted,
                evidence.RequiredForLease,
                matches ? "exact_match" : "digest_mismatch",
                readable ? observedHash : SafeDigest($"{evidence.CapabilityId}-unavailable")));
        }

        var securityReady = TryVerifySecurityModule(out var securityObservation);
        capabilities.Add(Capability(
            "agent.security_file_path_module",
            securityReady ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Unavailable,
            required: true,
            securityReady ? "registered_exact_match" : "not_registered",
            securityObservation));

        var hwpProcesses = Process.GetProcessesByName("Hwp");
        var hwpCount = hwpProcesses.Length;
        foreach (var process in hwpProcesses)
        {
            process.Dispose();
        }
        capabilities.Add(Capability(
            "agent.zero_hancom_processes",
            hwpCount == 0 ? RuntimeCapabilityState.Verified : RuntimeCapabilityState.Unavailable,
            required: true,
            hwpCount == 0 ? "zero_processes" : "process_present",
            SafeDigest($"hwp-process-count:{hwpCount}")));

        var requiredFailure = capabilities.Any(
            item => item.RequiredForLease && item.State != RuntimeCapabilityState.Verified);
        var optionalFailure = capabilities.Any(item => item.State != RuntimeCapabilityState.Verified);
        var health = requiredFailure
            ? ProbeHealth.Unroutable
            : optionalFailure ? ProbeHealth.Degraded : ProbeHealth.Healthy;
        var observedAt = checked((ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds());
        return Task.FromResult(new RuntimeProbeObservation(
            pin.PolicyId,
            observedTarget,
            pin.CapabilityRegistrySha256,
            health,
            capabilities,
            observedAt,
            RawPathStored: false,
            RawDocumentContentStored: false,
            UserDocumentScanned: false,
            ExternalNetworkInvoked: false,
            SystemSettingChanged: false,
            HancomProcessStarted: false));
    }

    private bool TryReadComRegistration(out string clsid, out string serverPath)
    {
        clsid = string.Empty;
        serverPath = string.Empty;
        if (!OperatingSystem.IsWindows())
        {
            return false;
        }

        try
        {
            using var classes = RegistryKey.OpenBaseKey(RegistryHive.ClassesRoot, RegistryView.Registry32);
            using var progIdKey = classes.OpenSubKey(pin.ProgId, writable: false);
            using var clsidKey = progIdKey?.OpenSubKey("CLSID", writable: false);
            clsid = clsidKey?.GetValue(null, null, RegistryValueOptions.DoNotExpandEnvironmentNames) as string
                ?? string.Empty;
            using var serverKey = classes.OpenSubKey($"CLSID\\{clsid}\\LocalServer32", writable: false);
            var command = serverKey?.GetValue(null, null, RegistryValueOptions.DoNotExpandEnvironmentNames) as string;
            var match = LocalServerPattern.Match(command?.Trim() ?? string.Empty);
            if (!match.Success)
            {
                return false;
            }

            serverPath = match.Groups["path"].Value;
            return IsLocalDrivePath(serverPath) && File.Exists(serverPath);
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or System.Security.SecurityException)
        {
            clsid = string.Empty;
            serverPath = string.Empty;
            return false;
        }
    }

    private bool TryVerifySecurityModule(out string observationSha256)
    {
        observationSha256 = SafeDigest("security-module-not-configured");
        if (!OperatingSystem.IsWindows() || securityModule is null)
        {
            return false;
        }

        using var currentUser = RegistryKey.OpenBaseKey(RegistryHive.CurrentUser, RegistryView.Registry32);
        using var modules = currentUser.OpenSubKey("Software\\HNC\\HwpAutomation\\Modules", writable: false);
        if (modules is null
            || !modules.GetValueNames().Contains(securityModule.RegistrationName, StringComparer.Ordinal)
            || modules.GetValueKind(securityModule.RegistrationName) != RegistryValueKind.String)
        {
            return false;
        }

        var path = modules.GetValue(
            securityModule.RegistrationName,
            null,
            RegistryValueOptions.DoNotExpandEnvironmentNames) as string;
        if (string.IsNullOrWhiteSpace(path)
            || !IsLocalDrivePath(path)
            || !TryHashPlainFile(path, 16 * 1024 * 1024, out var digest)
            || !string.Equals(digest, securityModule.Sha256, StringComparison.Ordinal)
            || !TryReadPeMachine(path, out var architecture)
            || !string.Equals(architecture, "x86", StringComparison.Ordinal))
        {
            observationSha256 = SafeDigest("security-module-invalid");
            return false;
        }

        observationSha256 = digest;
        return true;
    }

    private static RuntimeCapabilityObservation Capability(
        string id,
        RuntimeCapabilityState state,
        bool required,
        string safeCode,
        string observationSha256) =>
        new(id, state, required, safeCode, observationSha256);

    private static bool TryHashPlainFile(string path, long maximumBytes, out string digest)
    {
        digest = string.Empty;
        try
        {
            var info = new FileInfo(path);
            if (!info.Exists
                || info.Length is <= 0
                || info.Length > maximumBytes
                || (info.Attributes & FileAttributes.ReparsePoint) != 0)
            {
                return false;
            }

            using var stream = new FileStream(
                info.FullName,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: 65_536,
                FileOptions.SequentialScan);
            digest = Convert.ToHexStringLower(SHA256.HashData(stream));
            return true;
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
    }

    private static bool TryReadPeMachine(string path, out string architecture)
    {
        architecture = "unknown";
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            using var reader = new BinaryReader(stream, Encoding.UTF8, leaveOpen: false);
            if (stream.Length < 64 || reader.ReadUInt16() != 0x5a4d)
            {
                return false;
            }

            stream.Position = 0x3c;
            var peOffset = reader.ReadUInt32();
            if (peOffset > stream.Length - 6)
            {
                return false;
            }

            stream.Position = peOffset;
            if (reader.ReadUInt32() != 0x00004550)
            {
                return false;
            }

            architecture = reader.ReadUInt16() switch
            {
                0x014c => "x86",
                0x8664 => "x64",
                0xaa64 => "arm64",
                _ => "unknown",
            };
            return architecture != "unknown";
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
    }

    private static string? NormalizeVersion(string? value)
    {
        var components = value?
            .Split([',', '.'], StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);
        return components is { Length: 4 }
            && components.All(component => uint.TryParse(component, out _))
                ? string.Join('.', components.Select(component => uint.Parse(component, CultureInfo.InvariantCulture)))
                : null;
    }

    private static string SafeDigest(string value) =>
        RuntimeProbeMaterializer.Sha256(Encoding.UTF8.GetBytes(value));

    private static void RequireBoundedAbsolutePath(string path)
    {
        if (string.IsNullOrWhiteSpace(path)
            || path.Length > 1_024
            || !IsLocalDrivePath(path))
        {
            throw new ArgumentException("Runtime probe paths must be bounded local-drive paths.", nameof(path));
        }
    }

    private static bool IsLocalDrivePath(string path) =>
        path is { Length: >= 3 }
        && char.IsAsciiLetter(path[0])
        && path[1] == ':'
        && path[2] is '\\' or '/'
        && Path.IsPathFullyQualified(path);
}
