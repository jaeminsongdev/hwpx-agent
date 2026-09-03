using System.Text.Json;
using Google.Protobuf;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

public sealed class FileExecutionJournal
{
    private const string JournalMarker = "hwpx-agent-windows-agent-journal/v1";
    private const int MaximumClaimBytes = 16_384;
    private const int MaximumTerminalBytes = 1_048_576;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    private readonly string rootPath;

    public FileExecutionJournal(string rootPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootPath);
        AgentValidation.EnsurePlainDirectory(rootPath, nameof(rootPath));
        this.rootPath = Path.GetFullPath(rootPath);
        Directory.CreateDirectory(this.rootPath);
        EnsureMarker();
    }

    public async Task<JournalClaimResult> ClaimAsync(
        LeaseAssignment assignment,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(assignment);
        AgentValidation.RequireGuid(assignment.ExecutionId, nameof(assignment));
        var binding = JournalBinding.FromAssignment(assignment);
        var claimPath = ClaimPath(assignment.ExecutionId);
        var terminalPath = TerminalPath(assignment.ExecutionId);
        var lockPath = LockPath(assignment.ExecutionId);
        RejectReparseIfPresent(lockPath);
        FileStream ownershipStream;
        try
        {
            ownershipStream = new FileStream(
                lockPath,
                FileMode.OpenOrCreate,
                FileAccess.ReadWrite,
                FileShare.None,
                bufferSize: 1,
                FileOptions.WriteThrough);
        }
        catch (IOException)
        {
            return new JournalClaimResult(JournalClaimDisposition.Busy, null, null);
        }

        try
        {
            RejectReparseIfPresent(lockPath);
        }
        catch
        {
            ownershipStream.Dispose();
            throw;
        }

        var ownership = new JournalOwnership(this, assignment, ownershipStream);
        try
        {
            var serialized = JsonSerializer.SerializeToUtf8Bytes(binding, JsonOptions);
            var created = await TryWriteNewAsync(claimPath, serialized, cancellationToken).ConfigureAwait(false);
            if (created)
            {
                if (File.Exists(terminalPath))
                {
                    throw new AgentProtocolException(AgentProtocolError.JournalConflict);
                }

                return new JournalClaimResult(JournalClaimDisposition.New, null, ownership);
            }

            RejectReparseIfPresent(claimPath);
            var existingBytes = await ReadRegularFileAsync(
                claimPath,
                MaximumClaimBytes,
                cancellationToken).ConfigureAwait(false);
            var existing = JsonSerializer.Deserialize<JournalBinding>(existingBytes, JsonOptions)
                ?? throw new AgentProtocolException(AgentProtocolError.JournalConflict);
            if (existing != binding)
            {
                return new JournalClaimResult(JournalClaimDisposition.Conflict, null, ownership);
            }

            if (!File.Exists(terminalPath))
            {
                return new JournalClaimResult(JournalClaimDisposition.Unfinished, null, ownership);
            }

            RejectReparseIfPresent(terminalPath);
            var receiptBytes = await ReadRegularFileAsync(
                terminalPath,
                MaximumTerminalBytes,
                cancellationToken).ConfigureAwait(false);
            AgentExecutionReceipt receipt;
            try
            {
                receipt = AgentExecutionReceipt.Parser.ParseFrom(receiptBytes);
            }
            catch (InvalidProtocolBufferException)
            {
                throw new AgentProtocolException(AgentProtocolError.JournalConflict);
            }

            AgentValidation.ValidateExecutionReceipt(receipt, assignment);

            return new JournalClaimResult(JournalClaimDisposition.Terminal, receipt, ownership);
        }
        catch
        {
            await ownership.DisposeAsync().ConfigureAwait(false);
            throw;
        }
    }

    private async Task WriteTerminalAsync(
        LeaseAssignment assignment,
        AgentExecutionReceipt receipt,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(assignment);
        ArgumentNullException.ThrowIfNull(receipt);
        var claimPath = ClaimPath(assignment.ExecutionId);
        RejectReparseIfPresent(claimPath);
        var existingClaimBytes = await ReadRegularFileAsync(
            claimPath,
            MaximumClaimBytes,
            cancellationToken).ConfigureAwait(false);
        var existingBinding = JsonSerializer.Deserialize<JournalBinding>(existingClaimBytes, JsonOptions)
            ?? throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        if (existingBinding != JournalBinding.FromAssignment(assignment))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }

        var receiptBytes = receipt.ToByteArray();
        AgentValidation.ValidateExecutionReceipt(receipt, assignment);
        var path = TerminalPath(assignment.ExecutionId);
        if (File.Exists(path))
        {
            RejectReparseIfPresent(path);
            var existing = await ReadRegularFileAsync(
                path,
                MaximumTerminalBytes,
                cancellationToken).ConfigureAwait(false);
            if (!existing.AsSpan().SequenceEqual(receiptBytes))
            {
                throw new AgentProtocolException(AgentProtocolError.JournalConflict);
            }

            return;
        }

        if (!await TryWriteNewAsync(path, receiptBytes, cancellationToken).ConfigureAwait(false))
        {
            var existing = await ReadRegularFileAsync(
                path,
                MaximumTerminalBytes,
                cancellationToken).ConfigureAwait(false);
            if (!existing.AsSpan().SequenceEqual(receiptBytes))
            {
                throw new AgentProtocolException(AgentProtocolError.JournalConflict);
            }
        }
    }

    private static async Task<bool> TryWriteNewAsync(
        string destination,
        byte[] content,
        CancellationToken cancellationToken)
    {
        var partial = $"{destination}.{Guid.NewGuid():N}.partial";
        try
        {
            await using (var stream = new FileStream(
                partial,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                bufferSize: 16_384,
                FileOptions.Asynchronous | FileOptions.WriteThrough))
            {
                await stream.WriteAsync(content, cancellationToken).ConfigureAwait(false);
                await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
                stream.Flush(flushToDisk: true);
            }

            try
            {
                File.Move(partial, destination, overwrite: false);
                return true;
            }
            catch (IOException) when (File.Exists(destination))
            {
                return false;
            }
        }
        finally
        {
            if (File.Exists(partial))
            {
                File.Delete(partial);
            }
        }
    }

    private static async Task<byte[]> ReadRegularFileAsync(
        string path,
        int maximumBytes,
        CancellationToken cancellationToken)
    {
        RejectReparseIfPresent(path);
        await using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 16_384,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        RejectReparseIfPresent(path);
        if (stream.Length is <= 0 || stream.Length > maximumBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }

        var content = new byte[checked((int)stream.Length)];
        await stream.ReadExactlyAsync(content, cancellationToken).ConfigureAwait(false);
        return content;
    }

    private string ClaimPath(string executionId) => Path.Combine(rootPath, $"{executionId}.claim.json");

    private string TerminalPath(string executionId) => Path.Combine(rootPath, $"{executionId}.terminal.pb");

    private string LockPath(string executionId) => Path.Combine(rootPath, $"{executionId}.active.lock");

    private static void RejectReparseIfPresent(string path)
    {
        if ((File.Exists(path) || Directory.Exists(path))
            && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }
    }

    private void EnsureMarker()
    {
        var marker = Path.Combine(rootPath, ".hwpx-agent-journal");
        if (!File.Exists(marker))
        {
            try
            {
                using var stream = new FileStream(marker, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                using var writer = new StreamWriter(stream, new System.Text.UTF8Encoding(false));
                writer.Write(JournalMarker);
                writer.Flush();
                stream.Flush(flushToDisk: true);
            }
            catch (IOException) when (File.Exists(marker))
            {
                // Another constructor created the same immutable marker.
            }
        }

        if ((File.GetAttributes(marker) & FileAttributes.ReparsePoint) != 0
            || !string.Equals(File.ReadAllText(marker), JournalMarker, StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }
    }

    public sealed class JournalOwnership : IAsyncDisposable
    {
        private readonly FileExecutionJournal journal;
        private readonly LeaseAssignment assignment;
        private FileStream? stream;

        internal JournalOwnership(
            FileExecutionJournal journal,
            LeaseAssignment assignment,
            FileStream stream)
        {
            this.journal = journal;
            this.assignment = assignment.Clone();
            this.stream = stream;
        }

        public Task WriteTerminalAsync(
            AgentExecutionReceipt receipt,
            CancellationToken cancellationToken)
        {
            ObjectDisposedException.ThrowIf(stream is null, this);
            return journal.WriteTerminalAsync(assignment, receipt, cancellationToken);
        }

        public ValueTask DisposeAsync()
        {
            stream?.Dispose();
            stream = null;
            return ValueTask.CompletedTask;
        }
    }

    private sealed record JournalBinding(
        string LeaseId,
        ulong FencingToken,
        string ExecutionId,
        string TargetProfileId,
        string AssignmentSha256)
    {
        internal static JournalBinding FromAssignment(LeaseAssignment assignment) =>
            new(
                assignment.LeaseId,
                assignment.FencingToken,
                assignment.ExecutionId,
                assignment.TargetProfileId,
                AgentValidation.ComputeSha256(assignment));
    }
}

public enum JournalClaimDisposition
{
    New,
    Unfinished,
    Terminal,
    Conflict,
    Busy,
}

public sealed record JournalClaimResult(
    JournalClaimDisposition Disposition,
    AgentExecutionReceipt? Receipt,
    FileExecutionJournal.JournalOwnership? Ownership);
