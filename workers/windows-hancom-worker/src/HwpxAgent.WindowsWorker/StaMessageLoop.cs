using System.Collections.Concurrent;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace HwpxAgent.WindowsWorker;

public sealed class StaMessageLoop : IAsyncDisposable
{
    private const uint WmQuit = 0x0012;
    private const uint WmApp = 0x8000;
    private const uint WorkMessage = WmApp + 0x251;
    private const uint PmNoRemove = 0x0000;
    private const uint PmRemove = 0x0001;

    private readonly ConcurrentQueue<WorkItemBase> workItems = new();
    private readonly CancellationTokenSource shutdown = new();
    private readonly ManualResetEventSlim ready = new(initialState: false);
    private readonly Thread thread;
    private Exception? startupError;
    private uint nativeThreadId;
    private int disposeState;

    public StaMessageLoop(string threadName = "hwpx-agent-sta")
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("The STA worker requires Windows.");
        }

        thread = new Thread(Run)
        {
            IsBackground = true,
            Name = threadName,
        };
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        if (!ready.Wait(TimeSpan.FromSeconds(10)))
        {
            shutdown.Cancel();
            throw new InvalidOperationException("The STA message loop did not become ready.");
        }

        if (startupError is not null)
        {
            shutdown.Cancel();
            throw new InvalidOperationException("The STA message loop failed during startup.", startupError);
        }
    }

    public int ManagedThreadId => thread.ManagedThreadId;

    public Task<T> InvokeAsync<T>(
        Func<StaExecutionContext, T> operation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(operation);
        ObjectDisposedException.ThrowIf(Volatile.Read(ref disposeState) != 0, this);
        var linkedCancellation = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken,
            shutdown.Token);
        var workItem = new WorkItem<T>(operation, linkedCancellation);
        workItems.Enqueue(workItem);
        if (!PostThreadMessage(nativeThreadId, WorkMessage, UIntPtr.Zero, IntPtr.Zero))
        {
            workItem.Fail(new Win32Exception(Marshal.GetLastWin32Error()));
        }

        return workItem.Task;
    }

    public ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref disposeState, 1) != 0)
        {
            return ValueTask.CompletedTask;
        }

        shutdown.Cancel();
        if (nativeThreadId != 0)
        {
            PostThreadMessage(nativeThreadId, WmQuit, UIntPtr.Zero, IntPtr.Zero);
        }

        if (!thread.Join(TimeSpan.FromSeconds(10)))
        {
            throw new InvalidOperationException("The STA message loop did not stop at a cancellation safe point.");
        }

        shutdown.Dispose();
        ready.Dispose();
        return ValueTask.CompletedTask;
    }

    private void Run()
    {
        try
        {
            nativeThreadId = GetCurrentThreadId();
            _ = PeekMessage(out _, IntPtr.Zero, 0, 0, PmNoRemove);
            ready.Set();
            while (true)
            {
                var result = GetMessage(out var message, IntPtr.Zero, 0, 0);
                if (result == 0)
                {
                    break;
                }

                if (result < 0)
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }

                if (message.Message == WorkMessage)
                {
                    DrainWorkItems();
                    continue;
                }

                _ = TranslateMessage(ref message);
                _ = DispatchMessage(ref message);
            }
        }
        catch (Exception error)
        {
            startupError ??= error;
            FailPending(error);
        }
        finally
        {
            ready.Set();
            FailPending(new OperationCanceledException("The STA message loop stopped."));
        }
    }

    private void DrainWorkItems()
    {
        while (workItems.TryDequeue(out var workItem))
        {
            workItem.Execute(new StaExecutionContext(
                thread.ManagedThreadId,
                workItem.CancellationToken,
                PumpPendingMessages));
        }
    }

    private void FailPending(Exception error)
    {
        while (workItems.TryDequeue(out var workItem))
        {
            workItem.Fail(error);
        }
    }

    private static void PumpPendingMessages()
    {
        PumpRange(0, WorkMessage - 1);
        PumpRange(WorkMessage + 1, 0xffff);
    }

    private static void PumpRange(uint minimum, uint maximum)
    {
        while (PeekMessage(out var message, IntPtr.Zero, minimum, maximum, PmRemove))
        {
            if (message.Message == WmQuit)
            {
                _ = PostThreadMessage(GetCurrentThreadId(), WmQuit, UIntPtr.Zero, IntPtr.Zero);
                return;
            }

            _ = TranslateMessage(ref message);
            _ = DispatchMessage(ref message);
        }
    }

    private abstract class WorkItemBase(CancellationTokenSource cancellation) : IDisposable
    {
        internal CancellationToken CancellationToken => cancellation.Token;

        internal abstract void Execute(StaExecutionContext context);

        internal abstract void Fail(Exception error);

        public void Dispose() => cancellation.Dispose();
    }

    private sealed class WorkItem<T>(
        Func<StaExecutionContext, T> operation,
        CancellationTokenSource cancellation) : WorkItemBase(cancellation)
    {
        private readonly TaskCompletionSource<T> completion = new(TaskCreationOptions.RunContinuationsAsynchronously);

        internal Task<T> Task => completion.Task;

        internal override void Execute(StaExecutionContext context)
        {
            if (completion.Task.IsCompleted)
            {
                Dispose();
                return;
            }

            try
            {
                context.ThrowIfCancellationRequested();
                completion.TrySetResult(operation(context));
            }
            catch (OperationCanceledException)
            {
                completion.TrySetCanceled(context.CancellationToken);
            }
            catch (Exception error)
            {
                completion.TrySetException(error);
            }
            finally
            {
                Dispose();
            }
        }

        internal override void Fail(Exception error)
        {
            completion.TrySetException(error);
            Dispose();
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeMessage
    {
        internal IntPtr Window;
        internal uint Message;
        internal UIntPtr WParam;
        internal IntPtr LParam;
        internal uint Time;
        internal NativePoint Point;
        internal uint Private;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct NativePoint
    {
        internal int X;
        internal int Y;
    }

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int GetMessage(
        out NativeMessage message,
        IntPtr window,
        uint messageFilterMinimum,
        uint messageFilterMaximum);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PeekMessage(
        out NativeMessage message,
        IntPtr window,
        uint messageFilterMinimum,
        uint messageFilterMaximum,
        uint removeMessage);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool TranslateMessage(ref NativeMessage message);

    [DllImport("user32.dll")]
    private static extern IntPtr DispatchMessage(ref NativeMessage message);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PostThreadMessage(
        uint threadId,
        uint message,
        UIntPtr wParam,
        IntPtr lParam);
}

public sealed class StaExecutionContext
{
    private readonly int expectedManagedThreadId;
    private readonly Action pumpMessages;

    internal StaExecutionContext(
        int expectedManagedThreadId,
        CancellationToken cancellationToken,
        Action pumpMessages)
    {
        this.expectedManagedThreadId = expectedManagedThreadId;
        CancellationToken = cancellationToken;
        this.pumpMessages = pumpMessages;
    }

    public CancellationToken CancellationToken { get; }

    public int ManagedThreadId
    {
        get
        {
            VerifyThread();
            return Environment.CurrentManagedThreadId;
        }
    }

    public ApartmentState ApartmentState
    {
        get
        {
            VerifyThread();
            return Thread.CurrentThread.GetApartmentState();
        }
    }

    public void ThrowIfCancellationRequested()
    {
        VerifyThread();
        CancellationToken.ThrowIfCancellationRequested();
    }

    public void PumpPendingMessages()
    {
        VerifyThread();
        ThrowIfCancellationRequested();
        pumpMessages();
        ThrowIfCancellationRequested();
    }

    private void VerifyThread()
    {
        if (Environment.CurrentManagedThreadId != expectedManagedThreadId)
        {
            throw new InvalidOperationException("STA execution context used from another thread.");
        }
    }
}
