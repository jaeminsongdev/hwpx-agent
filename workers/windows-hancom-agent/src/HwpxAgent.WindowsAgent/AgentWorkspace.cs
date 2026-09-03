using System.Buffers;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

public sealed class AgentWorkspace
{
    private const string WorkspaceMarker = "hwpx-agent-windows-agent-workspace/v1";
    private readonly string sandboxRoot;

    public AgentWorkspace(string rootPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootPath);
        AgentValidation.EnsurePlainDirectory(rootPath, nameof(rootPath));
        RootPath = Path.GetFullPath(rootPath);
        Directory.CreateDirectory(RootPath);
        EnsureMarker(RootPath, ".hwpx-agent-workspace", WorkspaceMarker);

        sandboxRoot = Path.Combine(RootPath, "sandboxes");
        Directory.CreateDirectory(sandboxRoot);
        AgentValidation.EnsurePlainDirectory(sandboxRoot, nameof(rootPath));
        Journal = new FileExecutionJournal(Path.Combine(RootPath, "journal"));
    }

    public string RootPath { get; }

    public FileExecutionJournal Journal { get; }

    internal AgentJobSandbox CreateSandbox(LeaseAssignment assignment)
    {
        AgentValidation.RequireGuid(assignment.ExecutionId, nameof(assignment));
        var path = Path.Combine(sandboxRoot, $"job-{assignment.ExecutionId}");
        if (Directory.Exists(path) || File.Exists(path))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }

        Directory.CreateDirectory(path);
        EnsureMarker(path, ".hwpx-agent-sandbox", assignment.ExecutionId);
        return new AgentJobSandbox(path, sandboxRoot, assignment.ResourceLimits.MaxOutputBytes);
    }

    private static void EnsureMarker(string directory, string name, string expected)
    {
        var marker = Path.Combine(directory, name);
        if (!File.Exists(marker))
        {
            try
            {
                using var stream = new FileStream(marker, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                using var writer = new StreamWriter(stream, new System.Text.UTF8Encoding(false));
                writer.Write(expected);
                writer.Flush();
                stream.Flush(flushToDisk: true);
            }
            catch (IOException) when (File.Exists(marker))
            {
                // Another constructor created the same immutable marker.
            }
        }

        if ((File.GetAttributes(marker) & FileAttributes.ReparsePoint) != 0
            || !string.Equals(
                File.ReadAllText(marker, System.Text.Encoding.UTF8),
                expected,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }
    }
}

public sealed class AgentJobContext
{
    private readonly AgentJobSandbox sandbox;
    private readonly LeaseAssignment hancomSecurityAssignment;
    private readonly HancomSecurityModulePin? hancomSecurityModule;
    private readonly TimeProvider timeProvider;

    internal AgentJobContext(
        LeaseAssignment assignment,
        AgentJobSandbox sandbox,
        HancomSecurityModulePin? hancomSecurityModule,
        TimeProvider timeProvider)
    {
        Assignment = assignment.Clone();
        hancomSecurityAssignment = assignment.Clone();
        this.sandbox = sandbox;
        this.hancomSecurityModule = hancomSecurityModule;
        this.timeProvider = timeProvider;
    }

    public LeaseAssignment Assignment { get; }

    public Stream OpenStagedInput(string sandboxHandle) => sandbox.OpenStagedInput(sandboxHandle);

    public Stream CreateOutput(string sandboxHandle) => sandbox.CreateOutput(sandboxHandle);

    public Task<HancomWorkerSecurityLease> PrepareHancomWorkerSecurityLeaseAsync(
        CancellationToken cancellationToken = default)
    {
        if (hancomSecurityModule is null)
        {
            throw new AgentProtocolException(AgentProtocolError.PolicyDenied);
        }

        return sandbox.PrepareHancomWorkerSecurityLeaseAsync(
            hancomSecurityAssignment,
            hancomSecurityModule,
            timeProvider,
            cancellationToken);
    }
}

internal sealed class AgentJobSandbox : IAsyncDisposable
{
    private const string SandboxMarkerName = ".hwpx-agent-sandbox";
    private const string HancomSecurityLeaseSchema = "hwpx-agent.p10-05-security-lease/v1";
    private const string HancomSecurityLeaseFileName = ".hancom-security-lease.json";
    private const string HancomApprovedInputFileName = "hancom_approved_input.hwpx";
    private const string HancomFileAccessPolicyId = "file.local_read";
    private const string HancomOpenPolicyId = "open.read_only";
    private const int MaximumHancomInputBytes = 8 * 1024 * 1024;
    private const int MaximumHancomLeaseBytes = 8 * 1024;
    private static readonly TimeSpan MaximumHancomLeaseLifetime = TimeSpan.FromMinutes(30);
    private readonly string path;
    private readonly string sandboxRoot;
    private readonly ulong maximumOutputBytes;
    private readonly object outputQuotaGate = new();
    private readonly HashSet<string> stagedHandles = new(StringComparer.Ordinal);
    private readonly HashSet<string> outputHandles = new(StringComparer.Ordinal);
    private bool disposed;
    private int hancomSecurityPrepared;
    private ulong createdOutputBytes;
    private ulong uploadedOutputBytes;

    internal AgentJobSandbox(string path, string sandboxRoot, ulong maximumOutputBytes)
    {
        this.path = path;
        this.sandboxRoot = sandboxRoot;
        this.maximumOutputBytes = maximumOutputBytes;
    }

    internal async Task StageAsync(
        StagedArtifactRef staged,
        IArtifactStore artifactStore,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        AgentValidation.ValidateStagedArtifact(staged, requireReadOnly: true);
        if (!stagedHandles.Add(staged.SandboxHandle))
        {
            throw new AgentProtocolException(AgentProtocolError.DuplicateHandle);
        }

        var destination = ResolveHandle(staged.SandboxHandle);
        var partial = Path.Combine(path, $".stage-{Guid.NewGuid():N}.partial");
        try
        {
            await using var source = await artifactStore
                .OpenReadAsync(staged.Artifact, cancellationToken)
                .ConfigureAwait(false);
            await CopyAndVerifyAsync(source, partial, staged.Artifact, cancellationToken)
                .ConfigureAwait(false);
            File.Move(partial, destination, overwrite: false);
            File.SetAttributes(destination, File.GetAttributes(destination) | FileAttributes.ReadOnly);
        }
        catch
        {
            stagedHandles.Remove(staged.SandboxHandle);
            if (File.Exists(partial))
            {
                File.Delete(partial);
            }

            throw;
        }
    }

    internal Stream OpenStagedInput(string sandboxHandle)
    {
        ThrowIfDisposed();
        AgentValidation.RequireHandle(sandboxHandle);
        if (!stagedHandles.Contains(sandboxHandle))
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
        }

        var candidate = ResolveHandle(sandboxHandle);
        RejectReparse(candidate);
        return new FileStream(candidate, FileMode.Open, FileAccess.Read, FileShare.Read);
    }

    internal Stream CreateOutput(string sandboxHandle)
    {
        ThrowIfDisposed();
        AgentValidation.RequireHandle(sandboxHandle);
        if (stagedHandles.Contains(sandboxHandle) || !outputHandles.Add(sandboxHandle))
        {
            throw new AgentProtocolException(AgentProtocolError.DuplicateHandle);
        }

        try
        {
            var output = new FileStream(
                ResolveHandle(sandboxHandle),
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                bufferSize: 65_536,
                FileOptions.WriteThrough);
            return new BoundedOutputStream(output, ReserveOutputBytes);
        }
        catch
        {
            outputHandles.Remove(sandboxHandle);
            throw;
        }
    }

    internal async Task<HancomWorkerSecurityLease> PrepareHancomWorkerSecurityLeaseAsync(
        LeaseAssignment assignment,
        HancomSecurityModulePin module,
        TimeProvider timeProvider,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        ArgumentNullException.ThrowIfNull(assignment);
        ArgumentNullException.ThrowIfNull(timeProvider);
        AgentValidation.ValidateHancomSecurityModulePin(module);
        if (Interlocked.CompareExchange(ref hancomSecurityPrepared, 1, 0) != 0)
        {
            throw new AgentProtocolException(AgentProtocolError.DuplicateHandle);
        }

        var approvedInput = Path.Combine(path, HancomApprovedInputFileName);
        var partialInput = Path.Combine(path, ".hancom-approved-input.partial");
        var leasePath = Path.Combine(path, HancomSecurityLeaseFileName);
        try
        {
            var input = assignment.Input;
            if (input is null
                || input.Artifact is null
                || !input.ReadOnly
                || !stagedHandles.Contains(input.SandboxHandle)
                || input.Artifact.SizeBytes is 0 or > MaximumHancomInputBytes
                || assignment.SecurityPolicy is null
                || assignment.SecurityPolicy.AllowExternalNetwork
                || assignment.SecurityPolicy.AllowClipboard
                || assignment.SecurityPolicy.AllowMacros
                || assignment.SecurityPolicy.AllowOleActivation
                || !string.Equals(
                    assignment.SecurityPolicy.FileAccessPolicyId,
                    HancomFileAccessPolicyId,
                    StringComparison.Ordinal))
            {
                throw new AgentProtocolException(AgentProtocolError.PolicyDenied);
            }

            var nowUnixMilliseconds = timeProvider.GetUtcNow().ToUnixTimeMilliseconds();
            if (nowUnixMilliseconds < 0
                || assignment.ExpiresAtUnixMs <= (ulong)nowUnixMilliseconds)
            {
                throw new AgentProtocolException(AgentProtocolError.ExpiredLease);
            }

            var sourcePath = ResolveHandle(input.SandboxHandle);
            RejectReparse(sourcePath);
            if ((File.GetAttributes(sourcePath) & FileAttributes.ReadOnly) == 0)
            {
                throw new AgentProtocolException(AgentProtocolError.MutableInput);
            }

            await using (var source = new FileStream(
                sourcePath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: 65_536,
                FileOptions.Asynchronous | FileOptions.SequentialScan))
            {
                await CopyAndVerifyAsync(source, partialInput, input.Artifact, cancellationToken)
                    .ConfigureAwait(false);
            }

            File.Move(partialInput, approvedInput, overwrite: false);
            File.SetAttributes(approvedInput, FileAttributes.ReadOnly);

            var maximumExpiry = timeProvider
                .GetUtcNow()
                .Add(MaximumHancomLeaseLifetime)
                .ToUnixTimeMilliseconds();
            var expiresAt = Math.Min(
                assignment.ExpiresAtUnixMs,
                checked((ulong)maximumExpiry));
            var document = new HancomSecurityLeaseDocument
            {
                SchemaVersion = HancomSecurityLeaseSchema,
                ExecutionId = assignment.ExecutionId,
                SessionId = assignment.ExecutionId,
                FencingToken = assignment.FencingToken,
                TargetProfileId = assignment.TargetProfileId,
                ExpiresAtUnixMs = checked((long)expiresAt),
                FileAccessPolicyId = HancomFileAccessPolicyId,
                OpenPolicyId = HancomOpenPolicyId,
                SandboxHandle = input.SandboxHandle,
                ArtifactId = input.Artifact.ArtifactId,
                InputSha256 = input.Artifact.Sha256,
                InputSizeBytes = input.Artifact.SizeBytes,
                SecurityModuleRegistrationName = module.RegistrationName,
                SecurityModuleSha256 = module.Sha256,
            };
            var leaseBytes = JsonSerializer.SerializeToUtf8Bytes(document);
            if (leaseBytes.Length is <= 0 or > MaximumHancomLeaseBytes)
            {
                throw new AgentProtocolException(AgentProtocolError.InvalidLimits);
            }

            using (var lease = new FileStream(
                leasePath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                bufferSize: MaximumHancomLeaseBytes,
                FileOptions.WriteThrough))
            {
                lease.Write(leaseBytes);
                lease.Flush(flushToDisk: true);
            }

            File.SetAttributes(leasePath, FileAttributes.ReadOnly);
            return new HancomWorkerSecurityLease(
                assignment.ExecutionId,
                assignment.FencingToken,
                assignment.TargetProfileId,
                leasePath);
        }
        catch
        {
            DeletePrivateFile(leasePath);
            DeletePrivateFile(approvedInput);
            DeletePrivateFile(partialInput);
            throw;
        }
    }

    internal async Task<ArtifactRef> UploadOutputAsync(
        ProducedArtifact output,
        IArtifactStore artifactStore,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        AgentValidation.RequireHandle(output.SandboxHandle);
        if (!outputHandles.Contains(output.SandboxHandle))
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
        }

        var outputPath = ResolveHandle(output.SandboxHandle);
        RejectReparse(outputPath);
        await using var stream = new FileStream(
            outputPath,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 65_536,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        if (stream.Length is <= 0 || (ulong)stream.Length > maximumOutputBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.OutputLimit);
        }

        ulong nextTotal;
        try
        {
            nextTotal = checked(uploadedOutputBytes + (ulong)stream.Length);
        }
        catch (OverflowException)
        {
            throw new AgentProtocolException(AgentProtocolError.OutputLimit);
        }

        if (nextTotal > maximumOutputBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.OutputLimit);
        }

        var digest = await SHA256.HashDataAsync(stream, cancellationToken).ConfigureAwait(false);
        stream.Position = 0;
        var artifact = new ArtifactRef
        {
            ArtifactId = output.ArtifactId,
            Sha256 = Convert.ToHexStringLower(digest),
            SizeBytes = (ulong)stream.Length,
        };
        AgentValidation.ValidateArtifact(artifact);
        await artifactStore.UploadAsync(artifact, stream, cancellationToken).ConfigureAwait(false);
        uploadedOutputBytes = nextTotal;
        return artifact;
    }

    internal void ValidateOutputs(IReadOnlyList<ProducedArtifact> outputs)
    {
        ThrowIfDisposed();
        ulong total = 0;
        foreach (var output in outputs)
        {
            AgentValidation.RequireHandle(output.SandboxHandle);
            if (!outputHandles.Contains(output.SandboxHandle))
            {
                throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
            }

            var outputPath = ResolveHandle(output.SandboxHandle);
            RejectReparse(outputPath);
            var length = new FileInfo(outputPath).Length;
            if (length <= 0)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }

            try
            {
                total = checked(total + (ulong)length);
            }
            catch (OverflowException)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }

            if (total > maximumOutputBytes)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }
        }
    }

    public ValueTask DisposeAsync()
    {
        if (disposed)
        {
            return ValueTask.CompletedTask;
        }

        disposed = true;
        var fullPath = Path.GetFullPath(path);
        var expectedParent = Path.GetFullPath(sandboxRoot).TrimEnd(Path.DirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!fullPath.StartsWith(expectedParent, StringComparison.OrdinalIgnoreCase)
            || !File.Exists(Path.Combine(fullPath, SandboxMarkerName)))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }

        DeleteTreeWithoutFollowingReparsePoints(fullPath);
        return ValueTask.CompletedTask;
    }

    private static async Task CopyAndVerifyAsync(
        Stream source,
        string destination,
        ArtifactRef expected,
        CancellationToken cancellationToken)
    {
        if (!source.CanRead)
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }

        await using var output = new FileStream(
            destination,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 65_536,
            FileOptions.Asynchronous | FileOptions.WriteThrough);
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        var buffer = ArrayPool<byte>.Shared.Rent(65_536);
        ulong total = 0;
        try
        {
            while (true)
            {
                var read = await source.ReadAsync(buffer.AsMemory(0, buffer.Length), cancellationToken)
                    .ConfigureAwait(false);
                if (read == 0)
                {
                    break;
                }

                total = checked(total + (uint)read);
                if (total > expected.SizeBytes || total > AgentValidation.MaximumArtifactBytes)
                {
                    throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
                }

                hash.AppendData(buffer, 0, read);
                await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken).ConfigureAwait(false);
            }

            await output.FlushAsync(cancellationToken).ConfigureAwait(false);
            output.Flush(flushToDisk: true);
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer, clearArray: true);
        }

        var actualDigest = Convert.ToHexStringLower(hash.GetHashAndReset());
        if (total != expected.SizeBytes || !string.Equals(actualDigest, expected.Sha256, StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }
    }

    private string ResolveHandle(string handle)
    {
        AgentValidation.RequireHandle(handle);
        var candidate = Path.GetFullPath(Path.Combine(path, handle));
        var prefix = Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!candidate.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
        }

        return candidate;
    }

    private static void RejectReparse(string candidate)
    {
        if (!File.Exists(candidate)
            || (File.GetAttributes(candidate) & FileAttributes.ReparsePoint) != 0)
        {
            throw new AgentProtocolException(AgentProtocolError.UnsafeHandle);
        }
    }

    private static void DeletePrivateFile(string file)
    {
        if (!File.Exists(file))
        {
            return;
        }

        var attributes = File.GetAttributes(file);
        if ((attributes & FileAttributes.ReadOnly) != 0)
        {
            File.SetAttributes(file, attributes & ~FileAttributes.ReadOnly);
        }

        File.Delete(file);
    }

    private static void DeleteTreeWithoutFollowingReparsePoints(string directory)
    {
        foreach (var entry in Directory.EnumerateFileSystemEntries(directory))
        {
            var attributes = File.GetAttributes(entry);
            if ((attributes & FileAttributes.ReparsePoint) != 0)
            {
                if ((attributes & FileAttributes.Directory) != 0)
                {
                    Directory.Delete(entry, recursive: false);
                }
                else
                {
                    File.Delete(entry);
                }

                continue;
            }

            if ((attributes & FileAttributes.Directory) != 0)
            {
                DeleteTreeWithoutFollowingReparsePoints(entry);
                continue;
            }

            if ((attributes & FileAttributes.ReadOnly) != 0)
            {
                File.SetAttributes(entry, attributes & ~FileAttributes.ReadOnly);
            }

            File.Delete(entry);
        }

        Directory.Delete(directory, recursive: false);
    }

    private void ThrowIfDisposed()
    {
        ObjectDisposedException.ThrowIf(disposed, this);
    }

    private void ReserveOutputBytes(int count)
    {
        if (count < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(count));
        }

        lock (outputQuotaGate)
        {
            ulong next;
            try
            {
                next = checked(createdOutputBytes + (uint)count);
            }
            catch (OverflowException)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }

            if (next > maximumOutputBytes)
            {
                throw new AgentProtocolException(AgentProtocolError.OutputLimit);
            }

            createdOutputBytes = next;
        }
    }

    private sealed class BoundedOutputStream(
        FileStream inner,
        Action<int> reserveBytes) : Stream
    {
        public override bool CanRead => false;

        public override bool CanSeek => false;

        public override bool CanWrite => inner.CanWrite;

        public override long Length => inner.Length;

        public override long Position
        {
            get => inner.Position;
            set => throw new NotSupportedException();
        }

        public override void Flush() => inner.Flush();

        public override Task FlushAsync(CancellationToken cancellationToken) =>
            inner.FlushAsync(cancellationToken);

        public override int Read(byte[] buffer, int offset, int count) => throw new NotSupportedException();

        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();

        public override void SetLength(long value) => throw new NotSupportedException();

        public override void Write(byte[] buffer, int offset, int count)
        {
            ArgumentNullException.ThrowIfNull(buffer);
            ArgumentOutOfRangeException.ThrowIfNegative(offset);
            ArgumentOutOfRangeException.ThrowIfNegative(count);
            if (offset > buffer.Length - count)
            {
                throw new ArgumentException("The buffer range is invalid.", nameof(count));
            }

            reserveBytes(count);
            inner.Write(buffer, offset, count);
        }

        public override void Write(ReadOnlySpan<byte> buffer)
        {
            reserveBytes(buffer.Length);
            inner.Write(buffer);
        }

        public override async ValueTask WriteAsync(
            ReadOnlyMemory<byte> buffer,
            CancellationToken cancellationToken = default)
        {
            reserveBytes(buffer.Length);
            await inner.WriteAsync(buffer, cancellationToken).ConfigureAwait(false);
        }

        public override Task WriteAsync(
            byte[] buffer,
            int offset,
            int count,
            CancellationToken cancellationToken)
        {
            ArgumentNullException.ThrowIfNull(buffer);
            ArgumentOutOfRangeException.ThrowIfNegative(offset);
            ArgumentOutOfRangeException.ThrowIfNegative(count);
            if (offset > buffer.Length - count)
            {
                throw new ArgumentException("The buffer range is invalid.", nameof(count));
            }

            reserveBytes(count);
            return inner.WriteAsync(buffer, offset, count, cancellationToken);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                inner.Dispose();
            }

            base.Dispose(disposing);
        }

        public override async ValueTask DisposeAsync()
        {
            await inner.DisposeAsync().ConfigureAwait(false);
            GC.SuppressFinalize(this);
        }
    }

    [JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
    private sealed class HancomSecurityLeaseDocument
    {
        [JsonPropertyName("schema_version")]
        public required string SchemaVersion { get; init; }

        [JsonPropertyName("execution_id")]
        public required string ExecutionId { get; init; }

        [JsonPropertyName("session_id")]
        public required string SessionId { get; init; }

        [JsonPropertyName("fencing_token")]
        public ulong FencingToken { get; init; }

        [JsonPropertyName("target_profile_id")]
        public required string TargetProfileId { get; init; }

        [JsonPropertyName("expires_at_unix_ms")]
        public long ExpiresAtUnixMs { get; init; }

        [JsonPropertyName("file_access_policy_id")]
        public required string FileAccessPolicyId { get; init; }

        [JsonPropertyName("open_policy_id")]
        public required string OpenPolicyId { get; init; }

        [JsonPropertyName("sandbox_handle")]
        public required string SandboxHandle { get; init; }

        [JsonPropertyName("artifact_id")]
        public required string ArtifactId { get; init; }

        [JsonPropertyName("input_sha256")]
        public required string InputSha256 { get; init; }

        [JsonPropertyName("input_size_bytes")]
        public ulong InputSizeBytes { get; init; }

        [JsonPropertyName("security_module_registration_name")]
        public required string SecurityModuleRegistrationName { get; init; }

        [JsonPropertyName("security_module_sha256")]
        public required string SecurityModuleSha256 { get; init; }
    }
}
