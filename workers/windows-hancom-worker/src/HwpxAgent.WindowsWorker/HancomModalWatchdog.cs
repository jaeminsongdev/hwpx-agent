using System.Collections.Concurrent;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

internal enum HancomModalDisposition
{
    ExpectedBlocked,
    UnknownBlocked,
}

internal enum HancomScreenshotCaptureState
{
    Captured,
    Unavailable,
}

internal sealed record HancomScreenshotMetadata(
    HancomScreenshotCaptureState State,
    int Width,
    int Height,
    string PixelSha256,
    string FailureSha256)
{
    internal static HancomScreenshotMetadata Captured(int width, int height, string pixelSha256) =>
        new(HancomScreenshotCaptureState.Captured, width, height, pixelSha256, new string('0', 64));

    internal static HancomScreenshotMetadata Unavailable(int width, int height, string failureCategory) =>
        new(
            HancomScreenshotCaptureState.Unavailable,
            width,
            height,
            new string('0', 64),
            StaWorkerServer.Sha256(failureCategory));
}

internal sealed record HancomDialogObservation(
    int ProcessId,
    string WindowClassSha256,
    string WindowTitleSha256,
    string ControlStructureSha256,
    int Width,
    int Height,
    HancomScreenshotMetadata Screenshot)
{
    internal string IdentitySha256 => StaWorkerServer.Sha256(
        string.Join(
            ':',
            ProcessId.ToString(System.Globalization.CultureInfo.InvariantCulture),
            WindowClassSha256,
            WindowTitleSha256,
            ControlStructureSha256,
            Width.ToString(System.Globalization.CultureInfo.InvariantCulture),
            Height.ToString(System.Globalization.CultureInfo.InvariantCulture)));
}

internal sealed record HancomWindowInventoryItem(
    string WindowClass,
    string WindowTitleSha256,
    int WindowTitleLength,
    int Width,
    int Height,
    bool IsTopLevel,
    bool IsVisible,
    bool IsEnabled,
    int ParentDepth,
    long Style,
    long ExtendedStyle);

internal sealed record HancomExpectedDialogFingerprint(
    string FingerprintId,
    string WindowClassSha256,
    string WindowTitleSha256,
    string ControlStructureSha256,
    int MinimumWidth,
    int MaximumWidth,
    int MinimumHeight,
    int MaximumHeight)
{
    internal bool Matches(HancomDialogObservation observation) =>
        string.Equals(WindowClassSha256, observation.WindowClassSha256, StringComparison.Ordinal)
        && string.Equals(WindowTitleSha256, observation.WindowTitleSha256, StringComparison.Ordinal)
        && string.Equals(ControlStructureSha256, observation.ControlStructureSha256, StringComparison.Ordinal)
        && observation.Width >= MinimumWidth
        && observation.Width <= MaximumWidth
        && observation.Height >= MinimumHeight
        && observation.Height <= MaximumHeight;
}

internal sealed record HancomModalPolicy(
    string PolicyId,
    string TargetProfileId,
    string ProductBuild,
    IReadOnlyList<HancomExpectedDialogFingerprint> ExpectedDialogs);

internal sealed record HancomModalIncident(
    HancomModalDisposition Disposition,
    BridgeErrorCode ErrorCode,
    StaEventType EventType,
    string SafeMetadataSha256,
    bool ScreenshotCaptured,
    bool AutoResponseAttempted,
    bool RawDialogTextLogged,
    bool RequiresRecycle);

internal interface IHancomModalProbe
{
    IReadOnlyList<HancomDialogObservation> Capture(int processId);
}

internal interface IHancomModalPolicyResolver
{
    HancomModalPolicy Resolve(HancomTargetProfile profile, string modalPolicyId);
}

internal interface IHancomModalWatchdogSession : IDisposable
{
    void ScanNow();

    IReadOnlyList<HancomModalIncident> DrainIncidents();
}

internal interface IHancomModalWatchdogFactory
{
    IHancomModalWatchdogSession Start(
        int processId,
        HancomTargetProfile profile,
        string modalPolicyId);
}

internal sealed class FailClosedHancomModalPolicyResolver : IHancomModalPolicyResolver
{
    internal const string PolicyId = "modal.fail_closed";

    public HancomModalPolicy Resolve(HancomTargetProfile profile, string modalPolicyId)
    {
        ArgumentNullException.ThrowIfNull(profile);
        profile.Validate();
        if (!string.Equals(modalPolicyId, PolicyId, StringComparison.Ordinal))
        {
            throw new HancomLifecycleException(HancomLifecycleError.ModalPolicyInvalid);
        }

        return new HancomModalPolicy(
            PolicyId,
            profile.ProfileId,
            profile.ProductBuild,
            []);
    }
}

internal sealed class HancomModalWatchdogFactory(
    IHancomModalProbe? probe = null,
    IHancomModalPolicyResolver? policyResolver = null,
    TimeProvider? timeProvider = null) : IHancomModalWatchdogFactory
{
    private readonly IHancomModalProbe probe = probe ?? new NativeHancomModalProbe();
    private readonly IHancomModalPolicyResolver policyResolver =
        policyResolver ?? new FailClosedHancomModalPolicyResolver();
    private readonly TimeProvider timeProvider = timeProvider ?? TimeProvider.System;

    public IHancomModalWatchdogSession Start(
        int processId,
        HancomTargetProfile profile,
        string modalPolicyId)
    {
        if (processId <= 0)
        {
            throw new HancomLifecycleException(HancomLifecycleError.ModalPolicyInvalid);
        }

        var policy = policyResolver.Resolve(profile, modalPolicyId);
        ValidatePolicy(policy, profile, modalPolicyId);
        policy = policy with { ExpectedDialogs = policy.ExpectedDialogs.ToArray() };
        return new HancomModalWatchdogSession(
            processId,
            policy,
            probe,
            timeProvider,
            TimeSpan.FromMilliseconds(100),
            maximumIncidents: 64);
    }

    private static void ValidatePolicy(
        HancomModalPolicy? policy,
        HancomTargetProfile profile,
        string modalPolicyId)
    {
        if (policy is null
            || policy.ExpectedDialogs is null
            || !string.Equals(policy.PolicyId, modalPolicyId, StringComparison.Ordinal)
            || !string.Equals(policy.TargetProfileId, profile.ProfileId, StringComparison.Ordinal)
            || !string.Equals(policy.ProductBuild, profile.ProductBuild, StringComparison.Ordinal)
            || policy.ExpectedDialogs.Count > 64)
        {
            throw new HancomLifecycleException(HancomLifecycleError.ModalPolicyInvalid);
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var fingerprint in policy.ExpectedDialogs)
        {
            if (fingerprint is null
                || fingerprint.FingerprintId is null
                || !Regex.IsMatch(
                    fingerprint.FingerprintId,
                    "^[a-z][a-z0-9._-]{2,63}$",
                    RegexOptions.CultureInvariant)
                || !IsDigest(fingerprint.WindowClassSha256)
                || !IsDigest(fingerprint.WindowTitleSha256)
                || !IsDigest(fingerprint.ControlStructureSha256)
                || fingerprint.MinimumWidth < 1
                || fingerprint.MaximumWidth < fingerprint.MinimumWidth
                || fingerprint.MaximumWidth > 8_192
                || fingerprint.MinimumHeight < 1
                || fingerprint.MaximumHeight < fingerprint.MinimumHeight
                || fingerprint.MaximumHeight > 8_192
                || !ids.Add(fingerprint.FingerprintId))
            {
                throw new HancomLifecycleException(HancomLifecycleError.ModalPolicyInvalid);
            }
        }
    }

    private static bool IsDigest(string? value) =>
        value is not null
        && Regex.IsMatch(value, "^[0-9a-f]{64}$", RegexOptions.CultureInvariant);
}

internal sealed class NoOpHancomModalWatchdogFactory : IHancomModalWatchdogFactory
{
    internal static NoOpHancomModalWatchdogFactory Instance { get; } = new();

    public IHancomModalWatchdogSession Start(
        int processId,
        HancomTargetProfile profile,
        string modalPolicyId)
    {
        _ = processId;
        _ = profile;
        _ = modalPolicyId;
        return NoOpHancomModalWatchdogSession.Instance;
    }

    private sealed class NoOpHancomModalWatchdogSession : IHancomModalWatchdogSession
    {
        internal static NoOpHancomModalWatchdogSession Instance { get; } = new();

        public void ScanNow()
        {
        }

        public IReadOnlyList<HancomModalIncident> DrainIncidents() => [];

        public void Dispose()
        {
        }
    }
}

internal sealed class HancomModalWatchdogSession : IHancomModalWatchdogSession
{
    private readonly int processId;
    private readonly HancomModalPolicy policy;
    private readonly IHancomModalProbe probe;
    private readonly TimeProvider timeProvider;
    private readonly TimeSpan pollInterval;
    private readonly int maximumIncidents;
    private readonly ConcurrentQueue<HancomModalIncident> incidents = new();
    private readonly HashSet<string> seenObservationIds = new(StringComparer.Ordinal);
    private readonly object gate = new();
    private readonly CancellationTokenSource cancellation = new();
    private readonly Task monitor;
    private int incidentCount;
    private int overflowed;
    // 0 = active, 1 = stopping, 2 = disposed.  The monitor is allowed to finish
    // an in-flight bounded probe while state 1 is visible; public callers are not.
    private int disposeState;

    internal HancomModalWatchdogSession(
        int processId,
        HancomModalPolicy policy,
        IHancomModalProbe probe,
        TimeProvider timeProvider,
        TimeSpan pollInterval,
        int maximumIncidents)
    {
        this.processId = processId;
        this.policy = policy ?? throw new ArgumentNullException(nameof(policy));
        this.probe = probe ?? throw new ArgumentNullException(nameof(probe));
        this.timeProvider = timeProvider ?? throw new ArgumentNullException(nameof(timeProvider));
        if (pollInterval < TimeSpan.FromMilliseconds(10)
            || pollInterval > TimeSpan.FromSeconds(5)
            || maximumIncidents is < 1 or > 1_024)
        {
            throw new ArgumentOutOfRangeException(nameof(pollInterval));
        }

        this.pollInterval = pollInterval;
        this.maximumIncidents = maximumIncidents;
        ScanCore();
        monitor = Task.Run(MonitorAsync);
    }

    public void ScanNow()
    {
        ObjectDisposedException.ThrowIf(Volatile.Read(ref disposeState) != 0, this);
        ScanCore();
    }

    private void ScanCore()
    {
        IReadOnlyList<HancomDialogObservation> observations;
        try
        {
            observations = probe.Capture(processId)
                ?? throw new InvalidOperationException("Modal probe returned no collection.");
        }
        catch
        {
            EnqueueProbeFailure();
            return;
        }

        if (observations.Count > 64)
        {
            EnqueueProbeFailure();
            return;
        }

        foreach (var observation in observations.OrderBy(value => value.IdentitySha256, StringComparer.Ordinal))
        {
            if (observation.ProcessId != processId || !ValidateObservation(observation))
            {
                EnqueueProbeFailure();
                continue;
            }

            lock (gate)
            {
                if (!seenObservationIds.Add(observation.IdentitySha256))
                {
                    continue;
                }
            }

            var expected = policy.ExpectedDialogs.FirstOrDefault(value => value.Matches(observation));
            var disposition = expected is null
                ? HancomModalDisposition.UnknownBlocked
                : HancomModalDisposition.ExpectedBlocked;
            var eventType = expected is null ? StaEventType.UnknownModal : StaEventType.ExpectedModal;
            var errorCode = expected is null ? BridgeErrorCode.UnknownModal : BridgeErrorCode.PolicyDenied;
            var fingerprintId = expected?.FingerprintId ?? "unknown";
            var safeMetadata = StaWorkerServer.Sha256(
                string.Join(
                    ':',
                    "hancom-modal",
                    policy.PolicyId,
                    policy.TargetProfileId,
                    policy.ProductBuild,
                    fingerprintId,
                    observation.IdentitySha256,
                    observation.Screenshot.State.ToString().ToLowerInvariant(),
                    observation.Screenshot.PixelSha256,
                    observation.Screenshot.FailureSha256));
            Enqueue(new HancomModalIncident(
                disposition,
                errorCode,
                eventType,
                safeMetadata,
                observation.Screenshot.State == HancomScreenshotCaptureState.Captured,
                AutoResponseAttempted: false,
                RawDialogTextLogged: false,
                RequiresRecycle: true));
        }
    }

    public IReadOnlyList<HancomModalIncident> DrainIncidents()
    {
        ObjectDisposedException.ThrowIf(Volatile.Read(ref disposeState) != 0, this);
        if (Volatile.Read(ref overflowed) != 0)
        {
            throw new HancomLifecycleException(HancomLifecycleError.ModalWatchdogOverflow);
        }

        var drained = new List<HancomModalIncident>();
        while (incidents.TryDequeue(out var incident))
        {
            Interlocked.Decrement(ref incidentCount);
            drained.Add(incident);
        }

        return drained;
    }

    public void Dispose()
    {
        if (Interlocked.CompareExchange(ref disposeState, 1, 0) != 0)
        {
            return;
        }

        var monitorCompleted = false;
        AggregateException? monitorFailure = null;
        cancellation.Cancel();
        try
        {
            monitorCompleted = monitor.Wait(TimeSpan.FromSeconds(2));
        }
        catch (AggregateException error) when (error.InnerExceptions.All(value => value is OperationCanceledException))
        {
            // Expected cancellation during bounded shutdown.
            monitorCompleted = true;
        }
        catch (AggregateException error)
        {
            monitorCompleted = monitor.IsCompleted;
            monitorFailure = error;
        }
        finally
        {
            Volatile.Write(ref disposeState, 2);
            if (monitorCompleted)
            {
                cancellation.Dispose();
            }
        }

        if (!monitorCompleted || monitorFailure is not null)
        {
            throw new HancomLifecycleException(
                HancomLifecycleError.ModalWatchdogStopFailed,
                (Exception?)monitorFailure
                    ?? new TimeoutException("Modal watchdog did not stop within the bounded interval."));
        }
    }

    private async Task MonitorAsync()
    {
        try
        {
            while (true)
            {
                await Task.Delay(pollInterval, timeProvider, cancellation.Token).ConfigureAwait(false);
                if (cancellation.IsCancellationRequested)
                {
                    break;
                }

                ScanCore();
            }
        }
        catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
        {
            // Expected bounded shutdown.
        }
    }

    private void EnqueueProbeFailure()
    {
        var safeMetadata = StaWorkerServer.Sha256(
            $"hancom-modal:{policy.PolicyId}:{policy.TargetProfileId}:{policy.ProductBuild}:probe-failed");
        Enqueue(new HancomModalIncident(
            HancomModalDisposition.UnknownBlocked,
            BridgeErrorCode.UnknownModal,
            StaEventType.UnknownModal,
            safeMetadata,
            ScreenshotCaptured: false,
            AutoResponseAttempted: false,
            RawDialogTextLogged: false,
            RequiresRecycle: true));
    }

    private void Enqueue(HancomModalIncident incident)
    {
        var count = Interlocked.Increment(ref incidentCount);
        if (count > maximumIncidents)
        {
            Interlocked.Decrement(ref incidentCount);
            Interlocked.Exchange(ref overflowed, 1);
            return;
        }

        incidents.Enqueue(incident);
    }

    private static bool ValidateObservation(HancomDialogObservation observation) =>
        observation.Width is >= 1 and <= 8_192
        && observation.Height is >= 1 and <= 8_192
        && IsDigest(observation.WindowClassSha256)
        && IsDigest(observation.WindowTitleSha256)
        && IsDigest(observation.ControlStructureSha256)
        && IsDigest(observation.Screenshot.PixelSha256)
        && IsDigest(observation.Screenshot.FailureSha256)
        && (observation.Screenshot.State != HancomScreenshotCaptureState.Captured
            || (observation.Screenshot.Width == observation.Width
                && observation.Screenshot.Height == observation.Height
                && observation.Screenshot.PixelSha256 != new string('0', 64)))
        && (observation.Screenshot.State != HancomScreenshotCaptureState.Unavailable
            || observation.Screenshot.FailureSha256 != new string('0', 64));

    private static bool IsDigest(string value) =>
        Regex.IsMatch(value, "^[0-9a-f]{64}$", RegexOptions.CultureInvariant);
}

internal sealed class NativeHancomModalProbe : IHancomModalProbe
{
    private const uint GwOwner = 4;
    private const int GwlStyle = -16;
    private const int GwlExStyle = -20;
    private const long WsExDlgModalFrame = 0x00000001L;
    private const uint Srccopy = 0x00cc0020;
    private const uint DibRgbColors = 0;
    private const int BiRgb = 0;
    private const int MaximumDimension = 8_192;
    private const long MaximumPixels = 16_777_216;

    public IReadOnlyList<HancomDialogObservation> Capture(int processId)
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("Hancom modal probing requires Windows.");
        }

        if (processId <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(processId));
        }

        var processWindows = CaptureProcessTopLevelWindows(processId);

        var observations = new List<HancomDialogObservation>();
        var visited = new HashSet<IntPtr>();
        foreach (var root in processWindows)
        {
            InspectCandidate(root, processId, visited, observations);
            Exception? callbackFailure = null;
            _ = EnumChildWindows(
                root,
                (window, parameter) =>
                {
                    _ = parameter;
                    try
                    {
                        InspectCandidate(window, processId, visited, observations);
                        return true;
                    }
                    catch (Exception error)
                    {
                        callbackFailure = error;
                        return false;
                    }
                },
                IntPtr.Zero);
            if (callbackFailure is not null)
            {
                throw new InvalidOperationException("Child window inspection failed.", callbackFailure);
            }
        }

        return observations.OrderBy(value => value.IdentitySha256, StringComparer.Ordinal).ToArray();
    }

    internal IReadOnlyList<HancomWindowInventoryItem> CaptureSafeWindowInventory(int processId)
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("Hancom window inventory requires Windows.");
        }

        if (processId <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(processId));
        }

        var roots = CaptureProcessTopLevelWindows(processId);
        var rootSet = roots.ToHashSet();
        var windows = new List<IntPtr>();
        var visited = new HashSet<IntPtr>();
        foreach (var root in roots)
        {
            if (visited.Add(root))
            {
                windows.Add(root);
            }

            var inventoryOverflow = false;
            Exception? callbackFailure = null;
            _ = EnumChildWindows(
                root,
                (window, parameter) =>
                {
                    _ = parameter;
                    try
                    {
                        _ = GetWindowThreadProcessId(window, out var candidateProcessId);
                        if (candidateProcessId == processId && visited.Add(window))
                        {
                            if (windows.Count >= 512)
                            {
                                inventoryOverflow = true;
                                return false;
                            }

                            windows.Add(window);
                        }

                        return true;
                    }
                    catch (Exception error)
                    {
                        callbackFailure = error;
                        return false;
                    }
                },
                IntPtr.Zero);
            if (inventoryOverflow)
            {
                throw new InvalidOperationException("Process window inventory was unbounded.");
            }

            if (callbackFailure is not null)
            {
                throw new InvalidOperationException("Process window inventory failed.", callbackFailure);
            }
        }

        return windows.Select(window => CreateInventoryItem(window, rootSet.Contains(window))).ToArray();
    }

    private static IReadOnlyList<IntPtr> CaptureProcessTopLevelWindows(int processId)
    {
        var processWindows = new List<IntPtr>();
        var overflowed = false;
        Exception? callbackFailure = null;
        var enumerated = EnumWindows(
                (window, parameter) =>
                {
                    _ = parameter;
                    try
                    {
                        _ = GetWindowThreadProcessId(window, out var ownerProcessId);
                        if (ownerProcessId == processId)
                        {
                            if (processWindows.Count >= 64)
                            {
                                overflowed = true;
                                return false;
                            }

                            processWindows.Add(window);
                        }

                        return true;
                    }
                    catch (Exception error)
                    {
                        callbackFailure = error;
                        return false;
                    }
                },
                IntPtr.Zero);
        if (overflowed)
        {
            throw new InvalidOperationException("Process top-level window set was unbounded.");
        }

        if (callbackFailure is not null)
        {
            throw new InvalidOperationException("Top-level window inspection failed.", callbackFailure);
        }

        if (!enumerated)
        {
            throw new InvalidOperationException("Top-level window enumeration failed.");
        }

        return processWindows;
    }

    private static HancomWindowInventoryItem CreateInventoryItem(IntPtr window, bool isTopLevel)
    {
        if (!GetWindowRect(window, out var rectangle))
        {
            throw new InvalidOperationException("Window inventory bounds were unavailable.");
        }

        var titleLength = GetWindowTextLength(window);
        if (titleLength < 0 || titleLength > 4_096)
        {
            throw new InvalidOperationException("Window inventory title length was unbounded.");
        }

        var depth = 0;
        var parent = GetParent(window);
        while (parent != IntPtr.Zero)
        {
            depth++;
            if (depth > 32)
            {
                throw new InvalidOperationException("Window inventory parent chain was unbounded.");
            }

            parent = GetParent(parent);
        }

        return new HancomWindowInventoryItem(
            ReadClassName(window),
            HashUnicode(ReadWindowText(window)),
            titleLength,
            checked(rectangle.Right - rectangle.Left),
            checked(rectangle.Bottom - rectangle.Top),
            isTopLevel,
            IsWindowVisible(window),
            IsWindowEnabled(window),
            depth,
            GetWindowLongPtr(window, GwlStyle).ToInt64(),
            GetWindowLongPtr(window, GwlExStyle).ToInt64());
    }

    private static void InspectCandidate(
        IntPtr window,
        int processId,
        HashSet<IntPtr> visited,
        List<HancomDialogObservation> observations)
    {
        if (!visited.Add(window) || !IsWindowVisible(window))
        {
            return;
        }

        _ = GetWindowThreadProcessId(window, out var candidateProcessId);
        if (candidateProcessId != processId)
        {
            return;
        }

        var className = ReadClassName(window);
        var ownerWindow = GetWindow(window, GwOwner);
        _ = GetWindowThreadProcessId(ownerWindow, out var ownerWindowProcessId);
        var extendedStyle = GetWindowLongPtr(window, GwlExStyle).ToInt64();
        if (!string.Equals(className, "#32770", StringComparison.Ordinal)
            && ownerWindowProcessId != processId
            && (extendedStyle & WsExDlgModalFrame) == 0)
        {
            return;
        }

        if (!GetWindowRect(window, out var rectangle))
        {
            throw new InvalidOperationException("Modal bounds were unavailable.");
        }

        var width = checked(rectangle.Right - rectangle.Left);
        var height = checked(rectangle.Bottom - rectangle.Top);
        if (width is < 1 or > MaximumDimension
            || height is < 1 or > MaximumDimension
            || checked((long)width * height) > MaximumPixels)
        {
            throw new InvalidOperationException("Modal bounds were outside the capture policy.");
        }

        var title = ReadWindowText(window);
        var structure = ReadControlStructure(window, rectangle);
        observations.Add(new HancomDialogObservation(
            processId,
            HashUnicode(className),
            HashUnicode(title),
            HashUnicode(structure),
            width,
            height,
            CaptureScreenshotMetadata(window, width, height)));
    }

    private static string ReadClassName(IntPtr window)
    {
        var buffer = new StringBuilder(256);
        var length = GetClassName(window, buffer, buffer.Capacity);
        if (length <= 0 || length >= buffer.Capacity)
        {
            throw new InvalidOperationException("Window class was unavailable or unbounded.");
        }

        return buffer.ToString();
    }

    private static string ReadWindowText(IntPtr window)
    {
        var textLength = GetWindowTextLength(window);
        if (textLength < 0 || textLength > 4_096)
        {
            throw new InvalidOperationException("Window title was unbounded.");
        }

        var buffer = new StringBuilder(textLength + 1);
        var copied = GetWindowText(window, buffer, buffer.Capacity);
        if (copied < 0 || copied > textLength)
        {
            throw new InvalidOperationException("Window title changed while being read.");
        }

        return buffer.ToString();
    }

    private static string ReadControlStructure(IntPtr window, NativeRect parentRectangle)
    {
        var controls = new List<string>();
        Exception? callbackFailure = null;
        _ = EnumChildWindows(
            window,
            (child, parameter) =>
            {
                _ = parameter;
                try
                {
                    if (controls.Count >= 256 || !GetWindowRect(child, out var rectangle))
                    {
                        callbackFailure = new InvalidOperationException(
                            "Modal control structure was unbounded.");
                        return false;
                    }

                    var controlId = GetDlgCtrlID(child);
                    var className = ReadClassName(child);
                    controls.Add(string.Join(
                        ',',
                        controlId.ToString(System.Globalization.CultureInfo.InvariantCulture),
                        HashUnicode(className),
                        (rectangle.Left - parentRectangle.Left).ToString(System.Globalization.CultureInfo.InvariantCulture),
                        (rectangle.Top - parentRectangle.Top).ToString(System.Globalization.CultureInfo.InvariantCulture),
                        (rectangle.Right - rectangle.Left).ToString(System.Globalization.CultureInfo.InvariantCulture),
                        (rectangle.Bottom - rectangle.Top).ToString(System.Globalization.CultureInfo.InvariantCulture)));
                    return true;
                }
                catch (Exception error)
                {
                    callbackFailure = error;
                    return false;
                }
            },
            IntPtr.Zero);
        if (callbackFailure is not null)
        {
            throw new InvalidOperationException("Modal control enumeration failed.", callbackFailure);
        }

        controls.Sort(StringComparer.Ordinal);
        return string.Join(';', controls);
    }

    private static HancomScreenshotMetadata CaptureScreenshotMetadata(
        IntPtr window,
        int width,
        int height)
    {
        IntPtr windowDc = IntPtr.Zero;
        IntPtr memoryDc = IntPtr.Zero;
        IntPtr bitmap = IntPtr.Zero;
        IntPtr previous = IntPtr.Zero;
        try
        {
            windowDc = GetWindowDC(window);
            if (windowDc == IntPtr.Zero)
            {
                return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-window-dc-unavailable");
            }

            memoryDc = CreateCompatibleDC(windowDc);
            bitmap = CreateCompatibleBitmap(windowDc, width, height);
            if (memoryDc == IntPtr.Zero || bitmap == IntPtr.Zero)
            {
                return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-gdi-allocation-failed");
            }

            previous = SelectObject(memoryDc, bitmap);
            if (previous == IntPtr.Zero || previous == new IntPtr(-1))
            {
                return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-select-object-failed");
            }

            if (!BitBlt(memoryDc, 0, 0, width, height, windowDc, 0, 0, Srccopy))
            {
                return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-copy-failed");
            }

            var deselected = SelectObject(memoryDc, previous);
            if (deselected == IntPtr.Zero || deselected == new IntPtr(-1))
            {
                return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-deselect-object-failed");
            }

            previous = IntPtr.Zero;

            var information = new BitmapInfo
            {
                Header = new BitmapInfoHeader
                {
                    Size = checked((uint)Marshal.SizeOf<BitmapInfoHeader>()),
                    Width = width,
                    Height = -height,
                    Planes = 1,
                    BitCount = 32,
                    Compression = BiRgb,
                },
            };
            var bytes = new byte[checked(width * height * 4)];
            try
            {
                var rows = GetDIBits(
                    memoryDc,
                    bitmap,
                    0,
                    checked((uint)height),
                    bytes,
                    ref information,
                    DibRgbColors);
                if (rows != height)
                {
                    return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-pixel-read-failed");
                }

                return HancomScreenshotMetadata.Captured(
                    width,
                    height,
                    Convert.ToHexStringLower(SHA256.HashData(bytes)));
            }
            finally
            {
                CryptographicOperations.ZeroMemory(bytes);
            }
        }
        catch (Exception error) when (error is OverflowException or OutOfMemoryException)
        {
            return HancomScreenshotMetadata.Unavailable(width, height, "screenshot-bounds-failed");
        }
        finally
        {
            if (previous != IntPtr.Zero && previous != new IntPtr(-1) && memoryDc != IntPtr.Zero)
            {
                _ = SelectObject(memoryDc, previous);
            }

            if (bitmap != IntPtr.Zero)
            {
                _ = DeleteObject(bitmap);
            }

            if (memoryDc != IntPtr.Zero)
            {
                _ = DeleteDC(memoryDc);
            }

            if (windowDc != IntPtr.Zero)
            {
                _ = ReleaseDC(window, windowDc);
            }
        }
    }

    private static string HashUnicode(string value)
    {
        var normalized = value.Normalize(NormalizationForm.FormC);
        var bytes = Encoding.UTF8.GetBytes(normalized);
        try
        {
            return Convert.ToHexStringLower(SHA256.HashData(bytes));
        }
        finally
        {
            CryptographicOperations.ZeroMemory(bytes);
        }
    }

    private static IntPtr GetWindowLongPtr(IntPtr window, int index) =>
        IntPtr.Size == 8 ? GetWindowLongPtr64(window, index) : new IntPtr(GetWindowLong32(window, index));

    private delegate bool EnumWindowProcedure(IntPtr window, IntPtr parameter);

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        internal int Left;
        internal int Top;
        internal int Right;
        internal int Bottom;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct BitmapInfoHeader
    {
        internal uint Size;
        internal int Width;
        internal int Height;
        internal ushort Planes;
        internal ushort BitCount;
        internal int Compression;
        internal uint SizeImage;
        internal int XPelsPerMeter;
        internal int YPelsPerMeter;
        internal uint ClrUsed;
        internal uint ClrImportant;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct BitmapInfo
    {
        internal BitmapInfoHeader Header;
        internal uint Colors;
    }

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(EnumWindowProcedure callback, IntPtr parameter);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumChildWindows(
        IntPtr parent,
        EnumWindowProcedure callback,
        IntPtr parameter);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(IntPtr window);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowEnabled(IntPtr window);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr window, out int processId);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr GetWindow(IntPtr window, uint command);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr GetParent(IntPtr window);

    [DllImport("user32.dll", EntryPoint = "GetWindowLongW", SetLastError = true)]
    private static extern int GetWindowLong32(IntPtr window, int index);

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW", SetLastError = true)]
    private static extern IntPtr GetWindowLongPtr64(IntPtr window, int index);

    [DllImport("user32.dll", EntryPoint = "GetClassNameW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int GetClassName(IntPtr window, StringBuilder className, int maximumCount);

    [DllImport("user32.dll", EntryPoint = "GetWindowTextLengthW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int GetWindowTextLength(IntPtr window);

    [DllImport("user32.dll", EntryPoint = "GetWindowTextW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int GetWindowText(IntPtr window, StringBuilder text, int maximumCount);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(IntPtr window, out NativeRect rectangle);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int GetDlgCtrlID(IntPtr window);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr GetWindowDC(IntPtr window);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int ReleaseDC(IntPtr window, IntPtr deviceContext);

    [DllImport("gdi32.dll", SetLastError = true)]
    private static extern IntPtr CreateCompatibleDC(IntPtr deviceContext);

    [DllImport("gdi32.dll", SetLastError = true)]
    private static extern IntPtr CreateCompatibleBitmap(IntPtr deviceContext, int width, int height);

    [DllImport("gdi32.dll", SetLastError = true)]
    private static extern IntPtr SelectObject(IntPtr deviceContext, IntPtr value);

    [DllImport("gdi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool DeleteObject(IntPtr value);

    [DllImport("gdi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool DeleteDC(IntPtr deviceContext);

    [DllImport("gdi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool BitBlt(
        IntPtr destination,
        int destinationX,
        int destinationY,
        int width,
        int height,
        IntPtr source,
        int sourceX,
        int sourceY,
        uint operation);

    [DllImport("gdi32.dll", SetLastError = true)]
    private static extern int GetDIBits(
        IntPtr deviceContext,
        IntPtr bitmap,
        uint startScan,
        uint scanLines,
        [Out] byte[] bits,
        ref BitmapInfo information,
        uint usage);
}
