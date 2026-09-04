using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using HwpxAgent.Protocol.WindowsBridge.V1;
using Microsoft.Win32.SafeHandles;

namespace HwpxAgent.WindowsAgent;

internal sealed class WindowsOwnedWorkerProcess : IAsyncDisposable
{
    private const uint JobObjectLimitKillOnJobClose = 0x00002000;
    private const uint CreateSuspended = 0x00000004;
    private const uint CreateUnicodeEnvironment = 0x00000400;
    private const uint CreateNoWindow = 0x08000000;
    private const int JobObjectBasicAccountingInformationClass = 1;
    private const int JobObjectExtendedLimitInformationClass = 9;
    private readonly SafeJobHandle job;
    private readonly Process process;
    private readonly SemaphoreSlim lifecycle = new(1, 1);
    private bool terminated;
    private bool disposed;

    private WindowsOwnedWorkerProcess(SafeJobHandle job, Process process)
    {
        this.job = job;
        this.process = process;
        InitialProcessId = process.Id;
    }

    internal int InitialProcessId { get; }

    internal Task WaitForExitAsync(CancellationToken cancellationToken) =>
        process.WaitForExitAsync(cancellationToken);

    internal static WindowsOwnedWorkerProcess Start(
        ProcessStartInfo startInfo,
        string expectedExecutableSha256)
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("Owned worker process jobs require Windows.");
        }

        ArgumentNullException.ThrowIfNull(startInfo);
        AgentValidation.RequireDigest(expectedExecutableSha256);
        if (startInfo.UseShellExecute
            || startInfo.RedirectStandardInput
            || startInfo.RedirectStandardOutput
            || startInfo.RedirectStandardError
            || !string.IsNullOrEmpty(startInfo.Arguments)
            || string.IsNullOrWhiteSpace(startInfo.FileName)
            || !Path.IsPathFullyQualified(startInfo.FileName))
        {
            throw new ArgumentException(
                "The worker executable must be an absolute non-shell path.",
                nameof(startInfo));
        }

        var executablePath = Path.GetFullPath(startInfo.FileName);
        var executable = new FileInfo(executablePath);
        if (!executable.Exists
            || (executable.Attributes & FileAttributes.ReparsePoint) != 0
            || !string.Equals(
                HashFile(executablePath),
                expectedExecutableSha256,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidDigest);
        }

        var workingDirectory = string.IsNullOrWhiteSpace(startInfo.WorkingDirectory)
            ? Path.GetDirectoryName(executablePath)!
            : Path.GetFullPath(startInfo.WorkingDirectory);
        var workingDirectoryInfo = new DirectoryInfo(workingDirectory);
        if (!workingDirectoryInfo.Exists
            || (workingDirectoryInfo.Attributes & FileAttributes.ReparsePoint) != 0)
        {
            throw new ArgumentException(
                "The worker working directory must be an existing plain directory.",
                nameof(startInfo));
        }

        var commandLine = BuildCommandLine(executablePath, startInfo.ArgumentList);
        var environmentBlock = BuildEnvironmentBlock(startInfo);
        var environmentPointer = Marshal.StringToHGlobalUni(environmentBlock);

        var job = NativeMethods.CreateJobObject(IntPtr.Zero, null);
        if (job.IsInvalid)
        {
            Marshal.ZeroFreeGlobalAllocUnicode(environmentPointer);
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }

        Process? process = null;
        SafeProcessHandle? createdProcess = null;
        IntPtr createdThread = IntPtr.Zero;
        var assigned = false;
        try
        {
            var limits = new JobObjectExtendedLimitInformation
            {
                BasicLimitInformation = new JobObjectBasicLimitInformation
                {
                    LimitFlags = JobObjectLimitKillOnJobClose,
                },
            };
            if (!NativeMethods.SetInformationJobObject(
                    job,
                    JobObjectExtendedLimitInformationClass,
                    ref limits,
                    (uint)Marshal.SizeOf<JobObjectExtendedLimitInformation>()))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            var startupInfo = new StartupInfo
            {
                Size = (uint)Marshal.SizeOf<StartupInfo>(),
            };
            var creationFlags = CreateSuspended | CreateUnicodeEnvironment;
            if (startInfo.CreateNoWindow)
            {
                creationFlags |= CreateNoWindow;
            }

            if (!NativeMethods.CreateProcess(
                    executablePath,
                    commandLine,
                    IntPtr.Zero,
                    IntPtr.Zero,
                    inheritHandles: false,
                    creationFlags,
                    environmentPointer,
                    workingDirectory,
                    ref startupInfo,
                    out var processInformation))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            createdProcess = new SafeProcessHandle(processInformation.ProcessHandle, ownsHandle: true);
            createdThread = processInformation.ThreadHandle;
            if (!NativeMethods.AssignProcessToJobObject(job, createdProcess))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            assigned = true;
            var launchedPath = QueryProcessImagePath(createdProcess);
            if (!string.Equals(
                    Path.GetFullPath(launchedPath),
                    executablePath,
                    StringComparison.OrdinalIgnoreCase)
                || !string.Equals(
                    HashFile(launchedPath),
                    expectedExecutableSha256,
                    StringComparison.Ordinal))
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidDigest);
            }

            process = Process.GetProcessById(processInformation.ProcessId);
            if (NativeMethods.ResumeThread(createdThread) == uint.MaxValue)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            NativeMethods.CloseHandle(createdThread);
            createdThread = IntPtr.Zero;
            createdProcess.Dispose();
            createdProcess = null;

            return new WindowsOwnedWorkerProcess(job, process);
        }
        catch
        {
            if (assigned)
            {
                try
                {
                    NativeMethods.TerminateJobObject(job, 0x80000001);
                }
                catch
                {
                    // Closing the kill-on-close job remains the final containment attempt.
                }
            }
            else if (createdProcess is not null && !createdProcess.IsInvalid)
            {
                try
                {
                    NativeMethods.TerminateProcess(createdProcess, 0x80000001);
                }
                catch
                {
                    // Closing the process handle follows; the process is still suspended.
                }
            }

            process?.Dispose();
            createdProcess?.Dispose();
            if (createdThread != IntPtr.Zero)
            {
                NativeMethods.CloseHandle(createdThread);
            }

            job.Dispose();
            throw;
        }
        finally
        {
            Marshal.ZeroFreeGlobalAllocUnicode(environmentPointer);
        }
    }

    internal async Task<WorkerRecycleReceipt> RecycleAsync(
        LeaseAssignment assignment,
        WorkerRecycleReason reason,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(assignment);
        AgentValidation.RequireGuid(assignment.ExecutionId, nameof(assignment));
        var assignmentSha256 = AgentValidation.ComputeSha256(assignment);
        await lifecycle.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            if (!terminated)
            {
                TerminateOwnedTree();
                await WaitForEmptyJobAsync(cancellationToken).ConfigureAwait(false);
                terminated = true;
            }

            return new WorkerRecycleReceipt(
                assignment.ExecutionId,
                assignmentSha256,
                reason,
                ProcessTreeTerminated: true,
                FreshWorkerRequired: true,
                RawProcessCommandLineStored: false,
                SafeDetailSha256: SafeReceiptDigest(
                    assignment.ExecutionId,
                    assignmentSha256,
                    reason,
                    InitialProcessId));
        }
        finally
        {
            lifecycle.Release();
        }
    }

    public async ValueTask DisposeAsync()
    {
        await lifecycle.WaitAsync().ConfigureAwait(false);
        try
        {
            if (disposed)
            {
                return;
            }

            disposed = true;
            if (!terminated)
            {
                TerminateOwnedTree();
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(5));
                await WaitForEmptyJobAsync(timeout.Token).ConfigureAwait(false);
                terminated = true;
            }
        }
        finally
        {
            process.Dispose();
            job.Dispose();
            lifecycle.Release();
        }
    }

    private static string HashFile(string path)
    {
        using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 65_536,
            FileOptions.SequentialScan);
        return Convert.ToHexStringLower(SHA256.HashData(stream));
    }

    private static StringBuilder BuildCommandLine(
        string executablePath,
        ICollection<string> arguments)
    {
        var commandLine = new StringBuilder(QuoteWindowsArgument(executablePath));
        foreach (var argument in arguments)
        {
            commandLine.Append(' ');
            commandLine.Append(QuoteWindowsArgument(argument));
        }

        if (commandLine.Length > 32_767)
        {
            throw new ArgumentException("The worker command line is too long.", nameof(arguments));
        }

        return commandLine;
    }

    private static string BuildEnvironmentBlock(ProcessStartInfo startInfo)
    {
        var block = new StringBuilder();
        foreach (var entry in startInfo.Environment.OrderBy(
                     static entry => entry.Key,
                     StringComparer.OrdinalIgnoreCase))
        {
            if (string.IsNullOrEmpty(entry.Key)
                || entry.Key.IndexOf('=') >= 0
                || entry.Key.IndexOf('\0') >= 0
                || (entry.Value?.IndexOf('\0') ?? -1) >= 0)
            {
                throw new ArgumentException(
                    "The worker environment contains an invalid entry.",
                    nameof(startInfo));
            }

            block.Append(entry.Key);
            block.Append('=');
            block.Append(entry.Value);
            block.Append('\0');
        }

        block.Append('\0');
        if (block.Length > 32_767)
        {
            throw new ArgumentException("The worker environment block is too large.", nameof(startInfo));
        }

        return block.ToString();
    }

    private static string QuoteWindowsArgument(string argument)
    {
        ArgumentNullException.ThrowIfNull(argument);
        if (argument.IndexOf('\0') >= 0)
        {
            throw new ArgumentException("A worker argument contains a null character.", nameof(argument));
        }

        if (argument.Length != 0
            && argument.IndexOfAny([' ', '\t', '\n', '\v', '"']) < 0)
        {
            return argument;
        }

        var quoted = new StringBuilder(argument.Length + 2);
        quoted.Append('"');
        var backslashes = 0;
        foreach (var character in argument)
        {
            if (character == '\\')
            {
                backslashes++;
                continue;
            }

            if (character == '"')
            {
                quoted.Append('\\', (backslashes * 2) + 1);
                quoted.Append('"');
                backslashes = 0;
                continue;
            }

            quoted.Append('\\', backslashes);
            backslashes = 0;
            quoted.Append(character);
        }

        quoted.Append('\\', backslashes * 2);
        quoted.Append('"');
        return quoted.ToString();
    }

    private static string QueryProcessImagePath(SafeProcessHandle process)
    {
        var capacity = 32_768;
        var path = new StringBuilder(capacity);
        if (!NativeMethods.QueryFullProcessImageName(process, 0, path, ref capacity))
        {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }

        return path.ToString();
    }

    private static string SafeReceiptDigest(
        string executionId,
        string assignmentSha256,
        WorkerRecycleReason reason,
        int processId)
    {
        var bytes = Encoding.ASCII.GetBytes(
            $"{executionId}\n{assignmentSha256}\n{(int)reason}\n{processId}\n");
        return Convert.ToHexStringLower(SHA256.HashData(bytes));
    }

    private void TerminateOwnedTree()
    {
        if (!NativeMethods.TerminateJobObject(job, 0x80000001))
        {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }

    private async Task WaitForEmptyJobAsync(CancellationToken cancellationToken)
    {
        while (true)
        {
            if (!NativeMethods.QueryInformationJobObject(
                    job,
                    JobObjectBasicAccountingInformationClass,
                    out var accounting,
                    (uint)Marshal.SizeOf<JobObjectBasicAccountingInformation>(),
                    IntPtr.Zero))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            if (accounting.ActiveProcesses == 0)
            {
                return;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(25), cancellationToken).ConfigureAwait(false);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JobObjectBasicAccountingInformation
    {
        internal long TotalUserTime;
        internal long TotalKernelTime;
        internal long ThisPeriodTotalUserTime;
        internal long ThisPeriodTotalKernelTime;
        internal uint TotalPageFaultCount;
        internal uint TotalProcesses;
        internal uint ActiveProcesses;
        internal uint TotalTerminatedProcesses;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JobObjectBasicLimitInformation
    {
        internal long PerProcessUserTimeLimit;
        internal long PerJobUserTimeLimit;
        internal uint LimitFlags;
        internal nuint MinimumWorkingSetSize;
        internal nuint MaximumWorkingSetSize;
        internal uint ActiveProcessLimit;
        internal nuint Affinity;
        internal uint PriorityClass;
        internal uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters
    {
        internal ulong ReadOperationCount;
        internal ulong WriteOperationCount;
        internal ulong OtherOperationCount;
        internal ulong ReadTransferCount;
        internal ulong WriteTransferCount;
        internal ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JobObjectExtendedLimitInformation
    {
        internal JobObjectBasicLimitInformation BasicLimitInformation;
        internal IoCounters IoInfo;
        internal nuint ProcessMemoryLimit;
        internal nuint JobMemoryLimit;
        internal nuint PeakProcessMemoryUsed;
        internal nuint PeakJobMemoryUsed;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct StartupInfo
    {
        internal uint Size;
        internal string? Reserved;
        internal string? Desktop;
        internal string? Title;
        internal uint X;
        internal uint Y;
        internal uint XSize;
        internal uint YSize;
        internal uint XCountChars;
        internal uint YCountChars;
        internal uint FillAttribute;
        internal uint Flags;
        internal ushort ShowWindow;
        internal ushort Reserved2Size;
        internal IntPtr Reserved2;
        internal IntPtr StandardInput;
        internal IntPtr StandardOutput;
        internal IntPtr StandardError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessInformation
    {
        internal IntPtr ProcessHandle;
        internal IntPtr ThreadHandle;
        internal int ProcessId;
        internal int ThreadId;
    }

    private sealed class SafeJobHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        private SafeJobHandle()
            : base(ownsHandle: true)
        {
        }

        protected override bool ReleaseHandle() => NativeMethods.CloseHandle(handle);
    }

    private static class NativeMethods
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool CreateProcess(
            string applicationName,
            StringBuilder commandLine,
            IntPtr processAttributes,
            IntPtr threadAttributes,
            [MarshalAs(UnmanagedType.Bool)] bool inheritHandles,
            uint creationFlags,
            IntPtr environment,
            string currentDirectory,
            ref StartupInfo startupInfo,
            out ProcessInformation processInformation);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        internal static extern SafeJobHandle CreateJobObject(IntPtr jobAttributes, string? name);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool SetInformationJobObject(
            SafeJobHandle job,
            int informationClass,
            ref JobObjectExtendedLimitInformation information,
            uint informationLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool AssignProcessToJobObject(
            SafeJobHandle job,
            SafeProcessHandle process);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool QueryFullProcessImageName(
            SafeProcessHandle process,
            uint flags,
            StringBuilder executablePath,
            ref int size);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern uint ResumeThread(IntPtr thread);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool TerminateProcess(SafeProcessHandle process, uint exitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool TerminateJobObject(SafeJobHandle job, uint exitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool QueryInformationJobObject(
            SafeJobHandle job,
            int informationClass,
            out JobObjectBasicAccountingInformation information,
            uint informationLength,
            IntPtr returnLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool CloseHandle(IntPtr handle);
    }
}
