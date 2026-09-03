using System.Collections.Concurrent;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text.RegularExpressions;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsWorker;

internal sealed record HancomAutomationSignal(string SignalId, string SafeMetadataSha256);

internal sealed partial class HancomEventJournal
{
    private readonly int maximumEvents;
    private readonly TimeProvider timeProvider;
    private readonly List<StaEventRecord> events = [];

    internal HancomEventJournal(TimeProvider timeProvider, int maximumEvents = 1_024)
    {
        this.timeProvider = timeProvider ?? throw new ArgumentNullException(nameof(timeProvider));
        if (maximumEvents is < 1 or > 10_000)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumEvents));
        }

        this.maximumEvents = maximumEvents;
    }

    internal void Record(StaEventType eventType, string safeCategory)
    {
        if (!SafeCategoryPattern().IsMatch(safeCategory))
        {
            throw new HancomLifecycleException(HancomLifecycleError.EventInvalid);
        }

        RecordDigest(eventType, StaWorkerServer.Sha256(safeCategory));
    }

    internal void RecordDigest(StaEventType eventType, string safeMetadataSha256)
    {
        if (eventType == StaEventType.Unspecified
            || !Sha256Pattern().IsMatch(safeMetadataSha256)
            || events.Count >= maximumEvents)
        {
            throw new HancomLifecycleException(
                events.Count >= maximumEvents
                    ? HancomLifecycleError.EventOverflow
                    : HancomLifecycleError.EventInvalid);
        }

        events.Add(new StaEventRecord
        {
            Sequence = checked((uint)events.Count + 1),
            EventType = eventType,
            RecordedAtUnixMs = checked((ulong)timeProvider.GetUtcNow().ToUnixTimeMilliseconds()),
            SafeMetadataSha256 = safeMetadataSha256,
        });
    }

    internal void RecordAutomationSignals(
        IEnumerable<HancomAutomationSignal> signals,
        StaEventType carrierEventType)
    {
        ArgumentNullException.ThrowIfNull(signals);
        if (carrierEventType is not (
            StaEventType.SessionStarted
            or StaEventType.DocumentOpened
            or StaEventType.PlanExecuted
            or StaEventType.OutputSaved
            or StaEventType.RenderCompleted
            or StaEventType.CleanupCompleted))
        {
            throw new HancomLifecycleException(HancomLifecycleError.EventInvalid);
        }

        foreach (var signal in signals)
        {
            if (!SafeSignalIdPattern().IsMatch(signal.SignalId))
            {
                throw new HancomLifecycleException(HancomLifecycleError.EventInvalid);
            }

            // windows_bridge.v1 is immutable.  The COM signal digest is carried by the
            // existing semantic event for the command that observed it; raw COM data
            // and private identifiers never cross the public protocol boundary.
            RecordDigest(carrierEventType, signal.SafeMetadataSha256);
        }
    }

    internal IReadOnlyList<StaEventRecord> Snapshot() => events.Select(value => value.Clone()).ToArray();

    [GeneratedRegex("^[a-z0-9][a-z0-9:._-]{0,255}$", RegexOptions.CultureInvariant)]
    private static partial Regex SafeCategoryPattern();

    [GeneratedRegex("^[a-z][a-z0-9._-]{2,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex SafeSignalIdPattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();
}

[ComVisible(true)]
[Guid("F04A09A0-F319-40D5-88CA-CA439CC6820C")]
[InterfaceType(ComInterfaceType.InterfaceIsIDispatch)]
public interface IHancomObjectEventDispatch
{
    [DispId(1)]
    void Quit();

    [DispId(2)]
    void CreateXHwpWindow();

    [DispId(3)]
    void CloseXHwpWindow();

    [DispId(4)]
    void NewDocument(int documentId);

    [DispId(5)]
    void DocumentBeforeClose(int documentId);

    [DispId(6)]
    void DocumentBeforeOpen(int documentId);

    [DispId(7)]
    void DocumentAfterOpen(int documentId);

    [DispId(8)]
    void DocumentBeforeSave(int documentId);

    [DispId(9)]
    void DocumentAfterSave(int documentId);

    [DispId(10)]
    void DocumentAfterClose(int documentId);

    [DispId(11)]
    void DocumentChange(int documentId);

    [DispId(12)]
    void DocumentBeforePrint(int documentId);

    [DispId(13)]
    void DocumentAfterPrint(int documentId);

    [DispId(14)]
    int DocumentClickedHyperlink(int linkType, string address, string displayText);

    [DispId(15)]
    int DocumentModifiedHyperlink(int linkType, string address, string displayText);

    [DispId(16)]
    void BeforeQuit(int documentId);
}

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.None)]
public sealed class HancomObjectEventDispatch : IHancomObjectEventDispatch
{
    private const int MaximumSignals = 1_024;
    private readonly ConcurrentQueue<HancomAutomationSignal> signals = new();
    private int signalCount;
    private int overflowed;

    public void Quit() => Record("quit", null);

    public void CreateXHwpWindow() => Record("window.create", null);

    public void CloseXHwpWindow() => Record("window.close", null);

    public void NewDocument(int documentId) => Record("document.new", documentId);

    public void DocumentBeforeClose(int documentId) => Record("document.before_close", documentId);

    public void DocumentBeforeOpen(int documentId) => Record("document.before_open", documentId);

    public void DocumentAfterOpen(int documentId) => Record("document.after_open", documentId);

    public void DocumentBeforeSave(int documentId) => Record("document.before_save", documentId);

    public void DocumentAfterSave(int documentId) => Record("document.after_save", documentId);

    public void DocumentAfterClose(int documentId) => Record("document.after_close", documentId);

    public void DocumentChange(int documentId) => Record("document.change", documentId);

    public void DocumentBeforePrint(int documentId) => Record("document.before_print", documentId);

    public void DocumentAfterPrint(int documentId) => Record("document.after_print", documentId);

    public int DocumentClickedHyperlink(int linkType, string address, string displayText)
    {
        _ = address;
        _ = displayText;
        Record("hyperlink.clicked", linkType);
        return 0;
    }

    public int DocumentModifiedHyperlink(int linkType, string address, string displayText)
    {
        _ = address;
        _ = displayText;
        Record("hyperlink.modified", linkType);
        return 0;
    }

    public void BeforeQuit(int documentId) => Record("before_quit", documentId);

    internal IReadOnlyList<HancomAutomationSignal> Drain()
    {
        if (Volatile.Read(ref overflowed) != 0)
        {
            throw new HancomLifecycleException(HancomLifecycleError.EventOverflow);
        }

        var drained = new List<HancomAutomationSignal>();
        while (signals.TryDequeue(out var signal))
        {
            Interlocked.Decrement(ref signalCount);
            drained.Add(signal);
        }

        return drained;
    }

    private void Record(string signalId, int? numericValue)
    {
        var count = Interlocked.Increment(ref signalCount);
        if (count > MaximumSignals)
        {
            Interlocked.Decrement(ref signalCount);
            Interlocked.Exchange(ref overflowed, 1);
            return;
        }

        var category = numericValue.HasValue
            ? $"hancom-event:{signalId}:{numericValue.Value.ToString(System.Globalization.CultureInfo.InvariantCulture)}"
            : $"hancom-event:{signalId}";
        signals.Enqueue(new HancomAutomationSignal(signalId, StaWorkerServer.Sha256(category)));
    }
}

internal interface IHancomAutomationEventConnection : IDisposable
{
    IReadOnlyList<HancomAutomationSignal> Drain();
}

internal sealed class NoOpHancomAutomationEventConnection : IHancomAutomationEventConnection
{
    internal static NoOpHancomAutomationEventConnection Instance { get; } = new();

    public IReadOnlyList<HancomAutomationSignal> Drain() => [];

    public void Dispose()
    {
    }
}

internal sealed class HancomAutomationEventConnection : IHancomAutomationEventConnection
{
    private static readonly Guid EventInterfaceId = new("f04a09a0-f319-40d5-88ca-ca439cc6820c");
    private readonly HancomObjectEventDispatch sink;
    private IConnectionPoint? connectionPoint;
    private int cookie;

    private HancomAutomationEventConnection(
        HancomObjectEventDispatch sink,
        IConnectionPoint connectionPoint,
        int cookie)
    {
        this.sink = sink;
        this.connectionPoint = connectionPoint;
        this.cookie = cookie;
    }

    internal static HancomAutomationEventConnection Attach(object automation)
    {
        ArgumentNullException.ThrowIfNull(automation);
        IConnectionPoint? point = null;
        try
        {
            if (automation is not IConnectionPointContainer container)
            {
                throw new HancomLifecycleException(HancomLifecycleError.EventSubscriptionFailed);
            }

            var interfaceId = EventInterfaceId;
            container.FindConnectionPoint(ref interfaceId, out point);
            if (point is null)
            {
                throw new HancomLifecycleException(HancomLifecycleError.EventSubscriptionFailed);
            }

            var sink = new HancomObjectEventDispatch();
            point.Advise(sink, out var cookie);
            if (cookie == 0)
            {
                throw new HancomLifecycleException(HancomLifecycleError.EventSubscriptionFailed);
            }

            return new HancomAutomationEventConnection(sink, point, cookie);
        }
        catch (HancomLifecycleException)
        {
            ReleaseConnectionPoint(point);
            throw;
        }
        catch (Exception error) when (error is COMException or InvalidCastException)
        {
            ReleaseConnectionPoint(point);
            throw new HancomLifecycleException(HancomLifecycleError.EventSubscriptionFailed, error);
        }
    }

    public IReadOnlyList<HancomAutomationSignal> Drain() => sink.Drain();

    public void Dispose()
    {
        var point = Interlocked.Exchange(ref connectionPoint, null);
        var currentCookie = Interlocked.Exchange(ref cookie, 0);
        if (point is null)
        {
            return;
        }

        try
        {
            if (currentCookie != 0)
            {
                point.Unadvise(currentCookie);
            }
        }
        finally
        {
            ReleaseConnectionPoint(point);
        }
    }

    private static void ReleaseConnectionPoint(IConnectionPoint? point)
    {
        if (point is not null && Marshal.IsComObject(point))
        {
            _ = Marshal.FinalReleaseComObject(point);
        }
    }
}
