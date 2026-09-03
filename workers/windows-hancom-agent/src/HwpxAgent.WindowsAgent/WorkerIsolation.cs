using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32;

namespace HwpxAgent.WindowsAgent;

internal sealed class WorkerIsolationGuard
{
    private readonly WindowsAgentConfiguration configuration;
    private readonly AgentWorkspace workspace;
    private readonly IWorkerIsolationAttestor attestor;

    internal WorkerIsolationGuard(
        WindowsAgentConfiguration configuration,
        AgentWorkspace workspace,
        IWorkerIsolationAttestor attestor)
    {
        this.configuration = configuration;
        this.workspace = workspace;
        this.attestor = attestor ?? throw new ArgumentNullException(nameof(attestor));

        workspace.VerifyNoJobSandboxResidue();
        _ = CaptureAndValidate();
    }

    internal WorkerIsolationObservation VerifyBeforeLease()
    {
        workspace.VerifyNoJobSandboxResidue();
        return CaptureAndValidate();
    }

    internal void VerifyAfterJob(WorkerIsolationObservation before)
    {
        ArgumentNullException.ThrowIfNull(before);
        workspace.VerifyNoJobSandboxResidue();
        var after = CaptureAndValidate();
        if (before.SessionId != after.SessionId
            || !string.Equals(before.IdentitySha256, after.IdentitySha256, StringComparison.Ordinal)
            || !string.Equals(before.WindowStationSha256, after.WindowStationSha256, StringComparison.Ordinal)
            || !string.Equals(before.DesktopSha256, after.DesktopSha256, StringComparison.Ordinal)
            || !string.Equals(before.ProfileRootSha256, after.ProfileRootSha256, StringComparison.Ordinal)
            || !string.Equals(before.TempRootSha256, after.TempRootSha256, StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.IsolationNotReady);
        }
    }

    private WorkerIsolationObservation CaptureAndValidate()
    {
        WorkerIsolationObservation observation;
        try
        {
            observation = attestor.Observe(workspace.RootPath);
        }
        catch (Exception error) when (error is not AgentProtocolException)
        {
            throw new AgentProtocolException(AgentProtocolError.IsolationNotReady);
        }

        ArgumentNullException.ThrowIfNull(observation);
        var policy = configuration.WorkerIsolation;
        if (!observation.ProbeComplete
            || !observation.WindowsHost
            || !observation.InteractiveSession
            || observation.SessionId == 0
            || observation.RawIdentityStored
            || observation.TargetProcessCount != 0
            || !observation.PrivateJobWorkspace
            || !string.Equals(observation.PolicyId, policy.PolicyId, StringComparison.Ordinal)
            || !string.Equals(
                observation.TargetProfileId,
                configuration.TargetProfile.ProfileId,
                StringComparison.Ordinal)
            || !string.Equals(
                observation.HostBaselineSha256,
                policy.HostBaselineSha256,
                StringComparison.Ordinal)
            || !string.Equals(
                observation.HostIsolationIdentitySha256,
                policy.HostIsolationIdentitySha256,
                StringComparison.Ordinal)
            || !string.Equals(
                observation.WorkerImageManifestSha256,
                policy.WorkerImageManifestSha256,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.IsolationNotReady);
        }

        foreach (var digest in new[]
        {
            observation.IdentitySha256,
            observation.WindowStationSha256,
            observation.DesktopSha256,
            observation.ProfileRootSha256,
            observation.TempRootSha256,
            observation.HostIsolationIdentitySha256,
        })
        {
            AgentValidation.RequireDigest(digest);
        }

        if (policy.Scope == WorkerIsolationScope.DedicatedWorkerImage
            && (!observation.DedicatedIdentityAndProfile
                || !observation.PrivateWindowStation
                || !observation.OsNetworkDefaultDeny
                || !observation.ClipboardIsolated
                || !observation.ProfileResidueClean
                || !observation.RecoveryResidueClean
                || !observation.PrinterResidueClean))
        {
            throw new AgentProtocolException(AgentProtocolError.IsolationNotReady);
        }

        return observation;
    }
}

/// <summary>
/// Observes only privacy-preserving current-host facts. It deliberately cannot attest a dedicated
/// user/profile, private window station, firewall deny, clipboard isolation or profile-wide cleanup.
/// A sealed dedicated-worker deployment must provide its own independently verified attestor.
/// </summary>
public sealed class CurrentPcWorkerIsolationAttestor : IWorkerIsolationAttestor
{
    private const int UoiName = 2;
    private readonly WorkerIsolationPolicyPin policy;

    public CurrentPcWorkerIsolationAttestor(WorkerIsolationPolicyPin policy)
    {
        this.policy = policy ?? throw new ArgumentNullException(nameof(policy));
        if (policy.Scope != WorkerIsolationScope.CurrentPcInteractiveDevelopment)
        {
            throw new ArgumentException(
                "The current-PC attestor cannot qualify a dedicated worker image.",
                nameof(policy));
        }
    }

    public WorkerIsolationObservation Observe(string workspaceRoot)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(workspaceRoot);
        if (!OperatingSystem.IsWindows())
        {
            return IncompleteObservation();
        }

        try
        {
            using var identity = WindowsIdentity.GetCurrent(TokenAccessLevels.Query);
            using var process = Process.GetCurrentProcess();
            var identityValue = identity.User?.Value;
            var profileRoot = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            var tempRoot = Path.GetTempPath();
            var windowStation = ReadUserObjectName(GetProcessWindowStation());
            var desktop = ReadUserObjectName(GetThreadDesktop(GetCurrentThreadId()));
            var machineBindingSha256 = ReadMachineBindingSha256();
            var targetProcessCount = checked((uint)Process.GetProcessesByName("Hwp").Length);
            var workspaceIsPrivate = IsPrivateWorkspace(workspaceRoot);
            var complete = !string.IsNullOrWhiteSpace(identityValue)
                && !string.IsNullOrWhiteSpace(profileRoot)
                && !string.IsNullOrWhiteSpace(tempRoot)
                && !string.IsNullOrWhiteSpace(windowStation)
                && !string.IsNullOrWhiteSpace(desktop)
                && !string.IsNullOrWhiteSpace(machineBindingSha256)
                && process.SessionId > 0;
            var identitySha256 = HashSafeIdentity("identity", identityValue);
            var windowStationSha256 = HashSafeIdentity("window-station", windowStation);
            var desktopSha256 = HashSafeIdentity("desktop", desktop);
            var profileRootSha256 = HashSafeIdentity("profile-root", NormalizePath(profileRoot));
            var tempRootSha256 = HashSafeIdentity("temp-root", NormalizePath(tempRoot));
            var hostIsolationIdentitySha256 = HashSafeIdentity(
                "host-isolation-identity",
                string.Join(
                    '\n',
                    machineBindingSha256,
                    identitySha256,
                    windowStationSha256,
                    desktopSha256,
                    profileRootSha256,
                    tempRootSha256));

            return new WorkerIsolationObservation(
                policy.PolicyId,
                policy.TargetProfileId,
                policy.HostBaselineSha256,
                policy.WorkerImageManifestSha256,
                ProbeComplete: complete,
                WindowsHost: true,
                InteractiveSession: Environment.UserInteractive && process.SessionId > 0,
                SessionId: checked((uint)Math.Max(process.SessionId, 0)),
                IdentitySha256: identitySha256,
                WindowStationSha256: windowStationSha256,
                DesktopSha256: desktopSha256,
                ProfileRootSha256: profileRootSha256,
                TempRootSha256: tempRootSha256,
                HostIsolationIdentitySha256: hostIsolationIdentitySha256,
                PrivateJobWorkspace: workspaceIsPrivate,
                DedicatedIdentityAndProfile: false,
                PrivateWindowStation: false,
                OsNetworkDefaultDeny: false,
                ClipboardIsolated: false,
                ProfileResidueClean: false,
                RecoveryResidueClean: false,
                PrinterResidueClean: false,
                TargetProcessCount: targetProcessCount,
                RawIdentityStored: false);
        }
        catch
        {
            return IncompleteObservation();
        }
    }

    private WorkerIsolationObservation IncompleteObservation() =>
        new(
            policy.PolicyId,
            policy.TargetProfileId,
            policy.HostBaselineSha256,
            policy.WorkerImageManifestSha256,
            ProbeComplete: false,
            WindowsHost: OperatingSystem.IsWindows(),
            InteractiveSession: false,
            SessionId: 0,
            IdentitySha256: HashSafeIdentity("identity", string.Empty),
            WindowStationSha256: HashSafeIdentity("window-station", string.Empty),
            DesktopSha256: HashSafeIdentity("desktop", string.Empty),
            ProfileRootSha256: HashSafeIdentity("profile-root", string.Empty),
            TempRootSha256: HashSafeIdentity("temp-root", string.Empty),
            HostIsolationIdentitySha256: HashSafeIdentity("host-isolation-identity", string.Empty),
            PrivateJobWorkspace: false,
            DedicatedIdentityAndProfile: false,
            PrivateWindowStation: false,
            OsNetworkDefaultDeny: false,
            ClipboardIsolated: false,
            ProfileResidueClean: false,
            RecoveryResidueClean: false,
            PrinterResidueClean: false,
            TargetProcessCount: 0,
            RawIdentityStored: false);

    private static bool IsPrivateWorkspace(string workspaceRoot)
    {
        var fullPath = Path.GetFullPath(workspaceRoot);
        var root = Path.GetPathRoot(fullPath);
        if (string.Equals(
                fullPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                root?.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase)
            || !Directory.Exists(fullPath)
            || (File.GetAttributes(fullPath) & FileAttributes.ReparsePoint) != 0)
        {
            return false;
        }

        var marker = Path.Combine(fullPath, ".hwpx-agent-workspace");
        return File.Exists(marker)
            && (File.GetAttributes(marker) & FileAttributes.ReparsePoint) == 0;
    }

    private static string NormalizePath(string path) =>
        Path.GetFullPath(path)
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            .ToUpperInvariant();

    [SupportedOSPlatform("windows")]
    private static string? ReadMachineBindingSha256()
    {
        using var localMachine = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
        using var cryptography = localMachine.OpenSubKey(@"SOFTWARE\Microsoft\Cryptography", writable: false);
        var machineGuid = cryptography?.GetValue("MachineGuid", null, RegistryValueOptions.DoNotExpandEnvironmentNames)
            as string;
        if (string.IsNullOrWhiteSpace(machineGuid))
        {
            return null;
        }

        var bytes = Encoding.UTF8.GetBytes($"hwpx-agent/current-host/v1\n{machineGuid}");
        try
        {
            return Convert.ToHexStringLower(SHA256.HashData(bytes));
        }
        finally
        {
            CryptographicOperations.ZeroMemory(bytes);
        }
    }

    private static string HashSafeIdentity(string label, string? value)
    {
        var bytes = Encoding.UTF8.GetBytes($"hwpx-agent/p10-08/{label}/v1\n{value ?? string.Empty}");
        try
        {
            return Convert.ToHexStringLower(SHA256.HashData(bytes));
        }
        finally
        {
            CryptographicOperations.ZeroMemory(bytes);
        }
    }

    private static string? ReadUserObjectName(nint handle)
    {
        if (handle == 0)
        {
            return null;
        }

        _ = GetUserObjectInformation(handle, UoiName, null, 0, out var requiredBytes);
        if (requiredBytes is <= 2 or > 8_192)
        {
            return null;
        }

        var buffer = new char[requiredBytes / sizeof(char)];
        return GetUserObjectInformation(handle, UoiName, buffer, requiredBytes, out _)
            ? new string(buffer).TrimEnd('\0')
            : null;
    }

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetUserObjectInformation(
        nint handle,
        int index,
        [Out] char[]? information,
        int length,
        out int needed);

    [DllImport("user32.dll")]
    private static extern nint GetProcessWindowStation();

    [DllImport("user32.dll")]
    private static extern nint GetThreadDesktop(uint threadId);

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();
}
