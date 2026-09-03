using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.WindowsBridge.V1;
using Microsoft.Win32;

namespace HwpxAgent.WindowsWorker;

public enum HancomSessionState
{
    Created,
    Started,
    DocumentOpen,
    Closed,
    Faulted,
}

public enum HancomLifecycleError
{
    InvalidTarget,
    InvalidState,
    WrongApartment,
    WrongProcessArchitecture,
    RegistrationMissing,
    RegistrationInvalid,
    ExecutableMismatch,
    PreexistingProcess,
    ActivationFailed,
    ProcessOwnershipFailed,
    AutomationVersionMismatch,
    InputRejected,
    InputChanged,
    SecurityLeaseInvalid,
    SecurityLeaseExpired,
    SecurityPolicyMismatch,
    SecurityModuleInvalid,
    SecurityModuleRegistrationFailed,
    SecurityLeaseConsumed,
    OpenFailed,
    CloseFailed,
    QuitFailed,
    CleanupOwnershipMismatch,
    CleanupFailed,
}

public sealed class HancomLifecycleException : Exception
{
    public HancomLifecycleException(HancomLifecycleError error)
        : base($"Hancom lifecycle failed closed: {error}.")
    {
        Error = error;
    }

    public HancomLifecycleException(HancomLifecycleError error, Exception innerException)
        : base($"Hancom lifecycle failed closed: {error}.", innerException)
    {
        Error = error;
    }

    public HancomLifecycleError Error { get; }
}

public sealed partial record HancomTargetProfile(
    string ProfileId,
    string ProgId,
    string ProductBuild,
    string Locale,
    string ProcessArchitecture,
    string ExecutableSha256)
{
    public const string CurrentProgId = "HWPFrame.HwpObject.2";
    public const string CurrentProfileId = "hancom-hangul-2020-secondary";

    public void Validate()
    {
        if (!string.Equals(ProfileId, CurrentProfileId, StringComparison.Ordinal)
            || !string.Equals(ProgId, CurrentProgId, StringComparison.Ordinal)
            || !VersionPattern().IsMatch(ProductBuild)
            || !string.Equals(Locale, "ko-KR", StringComparison.Ordinal)
            || !string.Equals(ProcessArchitecture, "x86", StringComparison.Ordinal)
            || !Sha256Pattern().IsMatch(ExecutableSha256))
        {
            throw new HancomLifecycleException(HancomLifecycleError.InvalidTarget);
        }
    }

    public static HancomTargetProfile From(TargetProfileIdentity target)
    {
        ArgumentNullException.ThrowIfNull(target);
        var profile = new HancomTargetProfile(
            target.ProfileId,
            CurrentProgId,
            target.ProductBuild,
            target.Locale,
            target.ProcessArchitecture,
            target.ExecutableSha256);
        profile.Validate();
        return profile;
    }

    [GeneratedRegex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", RegexOptions.CultureInvariant)]
    private static partial Regex VersionPattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();
}

public sealed class HancomApprovedDocument : IDisposable
{
    private const long MaximumInputBytes = 8 * 1024 * 1024;
    private FileStream? integrityGuard;

    internal HancomApprovedDocument(string path, string sha256, long sizeBytes)
        : this(path, sha256, sizeBytes, integrityGuard: null)
    {
    }

    private HancomApprovedDocument(
        string path,
        string sha256,
        long sizeBytes,
        FileStream? integrityGuard)
    {
        try
        {
            Path = System.IO.Path.GetFullPath(path);
        }
        catch (Exception error) when (error is ArgumentException or NotSupportedException or PathTooLongException)
        {
            throw new HancomLifecycleException(HancomLifecycleError.InputRejected, error);
        }
        Sha256 = sha256;
        SizeBytes = sizeBytes;
        this.integrityGuard = integrityGuard;
        ValidateIntegrity();
    }

    internal string Path { get; }

    public string Sha256 { get; }

    public long SizeBytes { get; }

    internal void ValidateIntegrity(HancomLifecycleError errorCode = HancomLifecycleError.InputRejected)
    {
        try
        {
            var item = new FileInfo(Path);
            if (!item.Exists
                || (item.Attributes & FileAttributes.ReparsePoint) != 0
                || !string.Equals(item.Extension, ".hwpx", StringComparison.Ordinal)
                || item.Length is <= 0 or > MaximumInputBytes
                || item.Length != SizeBytes
                || !Regex.IsMatch(Sha256, "^[0-9a-f]{64}$", RegexOptions.CultureInvariant)
                || !string.Equals(HashFile(Path), Sha256, StringComparison.Ordinal))
            {
                throw new HancomLifecycleException(errorCode);
            }
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException)
        {
            throw new HancomLifecycleException(errorCode, error);
        }
    }

    internal static HancomApprovedDocument OpenGuarded(string path, string sha256, long sizeBytes)
    {
        FileStream? guard = null;
        try
        {
            var fullPath = System.IO.Path.GetFullPath(path);
            var item = new FileInfo(fullPath);
            if (!item.Exists
                || (item.Attributes & FileAttributes.ReparsePoint) != 0
                || (item.Attributes & FileAttributes.ReadOnly) == 0
                || !string.Equals(item.Extension, ".hwpx", StringComparison.Ordinal)
                || item.Length != sizeBytes)
            {
                throw new HancomLifecycleException(HancomLifecycleError.InputRejected);
            }

            guard = new FileStream(
                fullPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: 64 * 1024,
                FileOptions.SequentialScan);
            if (guard.Length != sizeBytes
                || !string.Equals(
                    Convert.ToHexStringLower(SHA256.HashData(guard)),
                    sha256,
                    StringComparison.Ordinal))
            {
                throw new HancomLifecycleException(HancomLifecycleError.InputRejected);
            }

            guard.Position = 0;
            var approved = new HancomApprovedDocument(fullPath, sha256, sizeBytes, guard);
            guard = null;
            return approved;
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or ArgumentException
            or NotSupportedException
            or PathTooLongException)
        {
            throw new HancomLifecycleException(HancomLifecycleError.InputRejected, error);
        }
        finally
        {
            guard?.Dispose();
        }
    }

    public void Dispose()
    {
        Interlocked.Exchange(ref integrityGuard, null)?.Dispose();
        GC.SuppressFinalize(this);
    }

    internal static string HashFile(string path)
    {
        using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 64 * 1024,
            FileOptions.SequentialScan);
        return Convert.ToHexStringLower(SHA256.HashData(stream));
    }
}

internal interface IHancomAutomationDocument : IDisposable
{
    void CloseWithoutSaving();
}

internal interface IHancomAutomationRuntime : IDisposable
{
    string Version { get; }

    bool RegisterFilePathSecurityModule(string registrationName);

    IHancomAutomationDocument Open(HancomApprovedDocument input);

    bool ExecuteAction(HancomBoundAction invocation);

    void Quit();
}

internal interface IHancomOwnedProcess : IDisposable
{
    int ProcessId { get; }

    void EnsureStopped(StaExecutionContext context);
}

internal interface IHancomRuntimeFactory
{
    HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context);
}

internal sealed record HancomRuntimeLease(
    IHancomAutomationRuntime Automation,
    IHancomOwnedProcess Process);

public sealed class HancomSession
{
    private readonly IHancomRuntimeFactory factory;
    private HancomRuntimeLease? lease;
    private IHancomAutomationDocument? document;
    private HancomApprovedDocument? openedInput;

    public HancomSession()
        : this(new ComHancomRuntimeFactory())
    {
    }

    internal HancomSession(IHancomRuntimeFactory factory)
    {
        this.factory = factory ?? throw new ArgumentNullException(nameof(factory));
    }

    public HancomSessionState State { get; private set; } = HancomSessionState.Created;

    public int? OwnedProcessId => lease?.Process.ProcessId;

    public bool FilePathSecurityEnabled { get; private set; }

    public void Start(HancomTargetProfile profile, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(context);
        RequireState(HancomSessionState.Created);
        VerifyContext(context);
        profile.Validate();
        try
        {
            lease = factory.Create(profile, context);
            if (!string.Equals(
                NormalizeVersion(lease.Automation.Version),
                NormalizeVersion(profile.ProductBuild),
                StringComparison.Ordinal))
            {
                throw new HancomLifecycleException(HancomLifecycleError.AutomationVersionMismatch);
            }

            context.PumpPendingMessages();
            State = HancomSessionState.Started;
        }
        catch
        {
            State = HancomSessionState.Faulted;
            TryCleanupPartial(context);
            throw;
        }
    }

    public void Open(HancomApprovedDocument input, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(input);
        ArgumentNullException.ThrowIfNull(context);
        RequireState(HancomSessionState.Started);
        VerifyContext(context);
        openedInput = input;
        try
        {
            input.ValidateIntegrity();
            var opened = RequireLease().Automation.Open(input);
            document = opened;
            State = HancomSessionState.DocumentOpen;
            context.PumpPendingMessages();
            input.ValidateIntegrity(HancomLifecycleError.InputChanged);
        }
        catch (HancomLifecycleException)
        {
            ClosePartialDocument();
            if (State != HancomSessionState.Faulted)
            {
                State = HancomSessionState.Started;
            }

            throw;
        }
        catch (OperationCanceledException)
        {
            ClosePartialDocument();
            if (State != HancomSessionState.Faulted)
            {
                State = HancomSessionState.Started;
            }

            throw;
        }
        catch (Exception error)
        {
            ClosePartialDocument();
            if (State != HancomSessionState.Faulted)
            {
                State = HancomSessionState.Started;
            }

            throw new HancomLifecycleException(HancomLifecycleError.OpenFailed, error);
        }
    }

    internal void EnableFilePathSecurity(string registrationName, StaExecutionContext context)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(registrationName);
        ArgumentNullException.ThrowIfNull(context);
        RequireState(HancomSessionState.Started);
        VerifyContext(context);
        if (FilePathSecurityEnabled)
        {
            throw new HancomLifecycleException(HancomLifecycleError.InvalidState);
        }

        try
        {
            if (!RequireLease().Automation.RegisterFilePathSecurityModule(registrationName))
            {
                throw new HancomLifecycleException(
                    HancomLifecycleError.SecurityModuleRegistrationFailed);
            }

            context.PumpPendingMessages();
            FilePathSecurityEnabled = true;
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw new HancomLifecycleException(
                HancomLifecycleError.SecurityModuleRegistrationFailed,
                error);
        }
    }

    internal void ExecuteAction(HancomBoundAction invocation, StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        ArgumentNullException.ThrowIfNull(context);
        RequireState(HancomSessionState.DocumentOpen);
        VerifyContext(context);
        context.ThrowIfCancellationRequested();
        try
        {
            if (!RequireLease().Automation.ExecuteAction(invocation))
            {
                State = HancomSessionState.Faulted;
                throw new HancomBindingException(
                    HancomBindingError.ActionFailed,
                    effectUnknown: true);
            }

            context.PumpPendingMessages();
        }
        catch (HancomBindingException)
        {
            State = HancomSessionState.Faulted;
            throw;
        }
        catch (Exception error)
        {
            State = HancomSessionState.Faulted;
            throw new HancomBindingException(
                HancomBindingError.ActionFailed,
                error,
                effectUnknown: true);
        }
    }

    public void CloseDocument(StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        RequireState(HancomSessionState.DocumentOpen);
        VerifyContext(context);
        var current = document!;
        var input = openedInput!;
        document = null;
        openedInput = null;
        Exception? closeError = null;
        try
        {
            current.CloseWithoutSaving();
        }
        catch (Exception error)
        {
            closeError = error;
        }
        try
        {
            current.Dispose();
        }
        catch (Exception error)
        {
            closeError ??= error;
        }

        HancomLifecycleException? integrityError = null;
        try
        {
            input.ValidateIntegrity(HancomLifecycleError.InputChanged);
        }
        catch (HancomLifecycleException error)
        {
            integrityError = error;
        }

        Exception? disposeError = null;
        try
        {
            input.Dispose();
        }
        catch (Exception error)
        {
            disposeError = error;
        }

        if (closeError is not null || integrityError is not null || disposeError is not null)
        {
            State = HancomSessionState.Faulted;
            if (closeError is not null)
            {
                throw new HancomLifecycleException(HancomLifecycleError.CloseFailed, closeError);
            }

            if (integrityError is not null)
            {
                throw integrityError;
            }

            throw new HancomLifecycleException(HancomLifecycleError.CleanupFailed, disposeError!);
        }

        State = HancomSessionState.Started;
        context.PumpPendingMessages();
    }

    public void Shutdown(StaExecutionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        VerifyContext(context);
        if (State == HancomSessionState.Closed)
        {
            return;
        }

        var cleanupFailed = false;
        if (document is not null || openedInput is not null)
        {
            var current = document;
            var input = openedInput;
            document = null;
            openedInput = null;
            try
            {
                current?.CloseWithoutSaving();
            }
            catch
            {
                cleanupFailed = true;
            }
            try
            {
                current?.Dispose();
            }
            catch
            {
                cleanupFailed = true;
            }
            try
            {
                input?.ValidateIntegrity(HancomLifecycleError.InputChanged);
            }
            catch
            {
                cleanupFailed = true;
            }
            try
            {
                input?.Dispose();
            }
            catch
            {
                cleanupFailed = true;
            }
        }

        if (lease is not null)
        {
            var current = lease;
            lease = null;
            try
            {
                current.Automation.Quit();
            }
            catch
            {
                cleanupFailed = true;
            }
            try
            {
                current.Automation.Dispose();
            }
            catch
            {
                cleanupFailed = true;
            }

            try
            {
                current.Process.EnsureStopped(context);
            }
            catch
            {
                cleanupFailed = true;
            }
            try
            {
                current.Process.Dispose();
            }
            catch
            {
                cleanupFailed = true;
            }
        }

        State = cleanupFailed ? HancomSessionState.Faulted : HancomSessionState.Closed;
        if (cleanupFailed)
        {
            throw new HancomLifecycleException(HancomLifecycleError.CleanupFailed);
        }
    }

    internal static string NormalizeVersion(string value)
    {
        var match = Regex.Match(
            value ?? string.Empty,
            "^\\s*(?<a>[0-9]+)\\s*[.,]\\s*(?<b>[0-9]+)\\s*[.,]\\s*(?<c>[0-9]+)\\s*[.,]\\s*(?<d>[0-9]+)\\s*$",
            RegexOptions.CultureInvariant);
        if (!match.Success)
        {
            throw new HancomLifecycleException(HancomLifecycleError.AutomationVersionMismatch);
        }

        var components = new uint[4];
        var names = new[] { "a", "b", "c", "d" };
        for (var index = 0; index < names.Length; index++)
        {
            if (!uint.TryParse(
                match.Groups[names[index]].Value,
                System.Globalization.NumberStyles.None,
                System.Globalization.CultureInfo.InvariantCulture,
                out components[index]))
            {
                throw new HancomLifecycleException(HancomLifecycleError.AutomationVersionMismatch);
            }
        }

        return string.Join('.', components);
    }

    private HancomRuntimeLease RequireLease() =>
        lease ?? throw new HancomLifecycleException(HancomLifecycleError.InvalidState);

    private void RequireState(HancomSessionState expected)
    {
        if (State != expected)
        {
            throw new HancomLifecycleException(HancomLifecycleError.InvalidState);
        }
    }

    private static void VerifyContext(StaExecutionContext context)
    {
        context.ThrowIfCancellationRequested();
        if (context.ApartmentState != ApartmentState.STA)
        {
            throw new HancomLifecycleException(HancomLifecycleError.WrongApartment);
        }
    }

    private void ClosePartialDocument()
    {
        if (document is null && openedInput is null)
        {
            return;
        }

        var current = document;
        var input = openedInput;
        document = null;
        openedInput = null;
        try
        {
            current?.CloseWithoutSaving();
        }
        catch
        {
            State = HancomSessionState.Faulted;
        }
        try
        {
            current?.Dispose();
        }
        catch
        {
            State = HancomSessionState.Faulted;
        }
        try
        {
            input?.ValidateIntegrity(HancomLifecycleError.InputChanged);
        }
        catch
        {
            State = HancomSessionState.Faulted;
        }
        try
        {
            input?.Dispose();
        }
        catch
        {
            State = HancomSessionState.Faulted;
        }
    }

    private void TryCleanupPartial(StaExecutionContext context)
    {
        if (lease is null)
        {
            return;
        }

        try
        {
            Shutdown(context);
        }
        catch
        {
            State = HancomSessionState.Faulted;
        }
    }
}

internal sealed class ComHancomRuntimeFactory : IHancomRuntimeFactory
{
    private const int PeMachineI386 = 0x014c;

    public HancomRuntimeLease Create(HancomTargetProfile profile, StaExecutionContext context)
    {
        profile.Validate();
        if (Environment.Is64BitProcess)
        {
            throw new HancomLifecycleException(HancomLifecycleError.WrongProcessArchitecture);
        }

        var preexisting = Process.GetProcessesByName("Hwp");
        try
        {
            if (preexisting.Length != 0)
            {
                throw new HancomLifecycleException(HancomLifecycleError.PreexistingProcess);
            }
        }
        finally
        {
            foreach (var process in preexisting)
            {
                process.Dispose();
            }
        }

        var executable = ResolveRegistration(profile);
        var startedAt = DateTimeOffset.UtcNow;
        ComHancomAutomationRuntime? automation = null;
        OwnedHancomProcess? ownedProcess = null;
        try
        {
            var comType = Type.GetTypeFromProgID(profile.ProgId, throwOnError: true)
                ?? throw new HancomLifecycleException(HancomLifecycleError.RegistrationMissing);
            var instance = Activator.CreateInstance(comType)
                ?? throw new HancomLifecycleException(HancomLifecycleError.ActivationFailed);
            automation = new ComHancomAutomationRuntime(instance);
            ownedProcess = BindOwnedProcess(executable, startedAt, context);
            return new HancomRuntimeLease(automation, ownedProcess);
        }
        catch (HancomLifecycleException)
        {
            CleanupFailedActivation(automation, ownedProcess, context);
            throw;
        }
        catch (Exception error)
        {
            CleanupFailedActivation(automation, ownedProcess, context);
            throw new HancomLifecycleException(HancomLifecycleError.ActivationFailed, error);
        }
    }

    private static string ResolveRegistration(HancomTargetProfile profile)
    {
        try
        {
            using var classes = RegistryKey.OpenBaseKey(RegistryHive.ClassesRoot, RegistryView.Registry32);
            using var progId = classes.OpenSubKey(profile.ProgId, writable: false);
            using var clsidKey = progId?.OpenSubKey("CLSID", writable: false);
            var clsid = clsidKey?.GetValue(null) as string;
            if (string.IsNullOrWhiteSpace(clsid) || !Guid.TryParseExact(clsid, "B", out _))
            {
                throw new HancomLifecycleException(HancomLifecycleError.RegistrationMissing);
            }

            using var server = classes.OpenSubKey($"CLSID\\{clsid}\\LocalServer32", writable: false);
            var command = server?.GetValue(null) as string;
            if (string.IsNullOrWhiteSpace(command) || command.Length > 1_024)
            {
                throw new HancomLifecycleException(HancomLifecycleError.RegistrationMissing);
            }

            var match = Regex.Match(
                command.Trim(),
                "^(?:\"(?<path>[^\"]+\\.exe)\"|(?<path>.+?\\.exe))(?:\\s|$)",
                RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (!match.Success)
            {
                throw new HancomLifecycleException(HancomLifecycleError.RegistrationInvalid);
            }

            var path = Path.GetFullPath(match.Groups["path"].Value);
            var file = new FileInfo(path);
            if (!file.Exists
                || (file.Attributes & FileAttributes.ReparsePoint) != 0
                || file.Length is <= 0 or > 64 * 1024 * 1024
                || !string.Equals(file.Name, "Hwp.exe", StringComparison.OrdinalIgnoreCase)
                || !string.Equals(
                    HancomApprovedDocument.HashFile(path),
                    profile.ExecutableSha256,
                    StringComparison.Ordinal)
                || !string.Equals(
                    HancomSession.NormalizeVersion(FileVersionInfo.GetVersionInfo(path).FileVersion ?? string.Empty),
                    HancomSession.NormalizeVersion(profile.ProductBuild),
                    StringComparison.Ordinal)
                || ReadPeMachine(path) != PeMachineI386)
            {
                throw new HancomLifecycleException(HancomLifecycleError.ExecutableMismatch);
            }

            return path;
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or System.Security.SecurityException
            or ArgumentException
            or NotSupportedException
            or OverflowException
            or FormatException)
        {
            throw new HancomLifecycleException(HancomLifecycleError.RegistrationInvalid, error);
        }
    }

    private static int ReadPeMachine(string path)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        using var reader = new BinaryReader(stream);
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

    private static OwnedHancomProcess BindOwnedProcess(
        string executable,
        DateTimeOffset startedAt,
        StaExecutionContext context)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(10);
        while (DateTimeOffset.UtcNow < deadline)
        {
            context.PumpPendingMessages();
            var candidates = Process.GetProcessesByName("Hwp")
                .Where(process => MatchesNewAutomationProcess(process, executable, startedAt))
                .ToArray();
            try
            {
                if (candidates.Length == 1)
                {
                    return OwnedHancomProcess.Bind(candidates[0], executable);
                }

                if (candidates.Length > 1)
                {
                    throw new HancomLifecycleException(HancomLifecycleError.ProcessOwnershipFailed);
                }
            }
            finally
            {
                foreach (var candidate in candidates)
                {
                    candidate.Dispose();
                }
            }

            Thread.Sleep(25);
        }

        throw new HancomLifecycleException(HancomLifecycleError.ProcessOwnershipFailed);
    }

    private static bool MatchesNewAutomationProcess(
        Process process,
        string executable,
        DateTimeOffset startedAt)
    {
        try
        {
            return process.SessionId == Process.GetCurrentProcess().SessionId
                && process.StartTime.ToUniversalTime() >= startedAt.UtcDateTime.AddSeconds(-2)
                && process.MainWindowHandle == IntPtr.Zero
                && string.Equals(process.MainModule?.FileName, executable, StringComparison.OrdinalIgnoreCase);
        }
        catch
        {
            return false;
        }
    }

    private static void CleanupFailedActivation(
        ComHancomAutomationRuntime? automation,
        OwnedHancomProcess? ownedProcess,
        StaExecutionContext context)
    {
        if (automation is not null)
        {
            try
            {
                automation.Quit();
            }
            catch
            {
                // The original typed failure remains authoritative.
            }
            try
            {
                automation.Dispose();
            }
            catch
            {
                // The caller will fail closed and its supervisor audits residue.
            }
        }

        if (ownedProcess is not null)
        {
            try
            {
                ownedProcess.EnsureStopped(context);
            }
            catch
            {
                // The caller will treat activation as failed and its supervisor audits residue.
            }
            try
            {
                ownedProcess.Dispose();
            }
            catch
            {
                // The caller will fail closed and its supervisor audits residue.
            }
        }
    }
}

internal sealed class ComHancomAutomationRuntime(object instance) : IHancomAutomationRuntime
{
    private object? instance = instance;

    public string Version
    {
        get
        {
            dynamic automation = RequireInstance();
            return (string)automation.Version;
        }
    }

    public IHancomAutomationDocument Open(HancomApprovedDocument input)
    {
        input.ValidateIntegrity();
        object? documents = null;
        object? document = null;
        try
        {
            dynamic automation = RequireInstance();
            documents = automation.XHwpDocuments;
            dynamic collection = documents;
            document = collection.Add(false);
            if (document is null)
            {
                throw new HancomLifecycleException(HancomLifecycleError.OpenFailed);
            }

            dynamic openedDocument = document;
            object? result = openedDocument.Open(input.Path, "HWPX", "lock:false;setcurdir:false");
            if (result is not bool accepted || !accepted)
            {
                throw new HancomLifecycleException(HancomLifecycleError.OpenFailed);
            }

            _ = openedDocument.SetActive_XHwpDocument();
            return new ComHancomAutomationDocument(documents, document);
        }
        catch (HancomLifecycleException)
        {
            ReleasePartialDocument(documents, document);
            throw;
        }
        catch (Exception error)
        {
            ReleasePartialDocument(documents, document);
            throw new HancomLifecycleException(HancomLifecycleError.OpenFailed, error);
        }
    }

    public bool RegisterFilePathSecurityModule(string registrationName)
    {
        dynamic automation = RequireInstance();
        object? result = automation.RegisterModule("FilePathCheckDLL", registrationName);
        return result is bool accepted && accepted;
    }

    public bool ExecuteAction(HancomBoundAction invocation)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        object? actionCollection = null;
        object? action = null;
        object? parameterSet = null;
        try
        {
            dynamic automation = RequireInstance();
            actionCollection = automation.HAction;
            dynamic actions = actionCollection;
            if (invocation.Parameters.Count == 0)
            {
                object? runResult = actions.Run(invocation.ActionId);
                return runResult is bool accepted && accepted;
            }

            action = actions.CreateAction(invocation.ActionId);
            if (action is null)
            {
                return false;
            }

            dynamic boundAction = action;
            if (boundAction.ActID is not string actualActionId
                || !string.Equals(actualActionId, invocation.ActionId, StringComparison.Ordinal)
                || boundAction.SetID is not string actualSetId
                || !string.Equals(actualSetId, invocation.ParameterSetId, StringComparison.Ordinal))
            {
                return false;
            }

            parameterSet = boundAction.CreateSet();
            if (parameterSet is null)
            {
                return false;
            }

            object? defaultResult = boundAction.GetDefault(parameterSet);
            dynamic typedSet = parameterSet;
            if (defaultResult is not bool defaultAccepted
                || !defaultAccepted
                || typedSet.IsSet is not bool isSet
                || !isSet
                || typedSet.SetID is not string parameterSetId
                || !string.Equals(parameterSetId, invocation.ParameterSetId, StringComparison.Ordinal))
            {
                return false;
            }

            foreach (var parameter in invocation.Parameters)
            {
                object? itemExists = typedSet.ItemExist(parameter.ItemName);
                if (itemExists is not bool exists || !exists)
                {
                    return false;
                }

                typedSet.SetItem(parameter.ItemName, parameter.Value);
            }

            object? executeResult = boundAction.Execute(parameterSet);
            return executeResult is bool executeAccepted && executeAccepted;
        }
        finally
        {
            ReleaseComObject(parameterSet);
            ReleaseComObject(action);
            ReleaseComObject(actionCollection);
        }
    }

    public void Quit()
    {
        dynamic automation = RequireInstance();
        automation.Quit();
    }

    public void Dispose()
    {
        var current = Interlocked.Exchange(ref instance, null);
        ReleaseComObject(current);
    }

    private object RequireInstance() =>
        instance ?? throw new HancomLifecycleException(HancomLifecycleError.InvalidState);

    private static void ReleasePartialDocument(object? documents, object? document)
    {
        if (document is not null)
        {
            try
            {
                dynamic openedDocument = document;
                _ = openedDocument.Close(false);
            }
            catch
            {
                // Best effort; the session still owns and terminates the application process.
            }
        }

        ReleaseComObject(document);
        ReleaseComObject(documents);
    }

    internal static void ReleaseComObject(object? value)
    {
        if (value is not null && Marshal.IsComObject(value))
        {
            _ = Marshal.FinalReleaseComObject(value);
        }
    }
}

internal sealed class ComHancomAutomationDocument(object documents, object document)
    : IHancomAutomationDocument
{
    private object? documents = documents;
    private object? document = document;
    private int closed;

    public void CloseWithoutSaving()
    {
        if (Interlocked.Exchange(ref closed, 1) != 0)
        {
            return;
        }

        dynamic current = document
            ?? throw new HancomLifecycleException(HancomLifecycleError.InvalidState);
        object? result = current.Close(false);
        if (result is bool accepted && !accepted)
        {
            throw new HancomLifecycleException(HancomLifecycleError.CloseFailed);
        }
    }

    public void Dispose()
    {
        ComHancomAutomationRuntime.ReleaseComObject(Interlocked.Exchange(ref document, null));
        ComHancomAutomationRuntime.ReleaseComObject(Interlocked.Exchange(ref documents, null));
    }
}

internal sealed class OwnedHancomProcess : IHancomOwnedProcess
{
    private readonly int processId;
    private readonly long startTimeUtcTicks;
    private readonly int sessionId;
    private readonly string executable;

    private OwnedHancomProcess(Process process, string executable)
    {
        processId = process.Id;
        startTimeUtcTicks = process.StartTime.ToUniversalTime().Ticks;
        sessionId = process.SessionId;
        this.executable = executable;
    }

    public int ProcessId => processId;

    internal static OwnedHancomProcess Bind(Process process, string executable) => new(process, executable);

    public void EnsureStopped(StaExecutionContext context)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(5);
        var ownedProcessExited = false;
        while (DateTimeOffset.UtcNow < deadline)
        {
            context.PumpPendingMessages();
            using var process = TryOpen();
            if (process is null || process.HasExited)
            {
                ownedProcessExited = true;
                break;
            }

            Thread.Sleep(25);
        }

        if (!ownedProcessExited)
        {
            using var owned = TryOpen();
            if (owned is not null && !owned.HasExited)
            {
                VerifyIdentity(owned);
                owned.Kill(entireProcessTree: false);
                if (!owned.WaitForExit(10_000))
                {
                    throw new HancomLifecycleException(HancomLifecycleError.CleanupFailed);
                }
            }
        }

        WaitForHancomProcessQuiescence(context);
    }

    private static void WaitForHancomProcessQuiescence(StaExecutionContext context)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(5);
        while (DateTimeOffset.UtcNow < deadline)
        {
            context.PumpPendingMessages();
            var remaining = Process.GetProcessesByName("Hwp");
            try
            {
                if (remaining.Length == 0)
                {
                    return;
                }
            }
            finally
            {
                foreach (var process in remaining)
                {
                    process.Dispose();
                }
            }

            Thread.Sleep(25);
        }

        // Never terminate an unowned process. The next session remains fail-closed.
        throw new HancomLifecycleException(HancomLifecycleError.CleanupOwnershipMismatch);
    }

    public void Dispose()
    {
    }

    private Process? TryOpen()
    {
        try
        {
            return Process.GetProcessById(processId);
        }
        catch (ArgumentException)
        {
            return null;
        }
    }

    private void VerifyIdentity(Process process)
    {
        try
        {
            if (process.StartTime.ToUniversalTime().Ticks != startTimeUtcTicks
                || process.SessionId != sessionId
                || !string.Equals(process.MainModule?.FileName, executable, StringComparison.OrdinalIgnoreCase))
            {
                throw new HancomLifecycleException(HancomLifecycleError.CleanupOwnershipMismatch);
            }
        }
        catch (HancomLifecycleException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw new HancomLifecycleException(HancomLifecycleError.CleanupOwnershipMismatch, error);
        }
    }
}
