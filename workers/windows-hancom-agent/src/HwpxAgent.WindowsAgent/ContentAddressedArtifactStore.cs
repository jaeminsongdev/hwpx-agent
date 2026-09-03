using System.Buffers;
using System.Security.Cryptography;
using HwpxAgent.Protocol.Foundation.V1;

namespace HwpxAgent.WindowsAgent;

public sealed class ContentAddressedArtifactStore : IArtifactStore
{
    private const string StoreMarker = "hwpx-agent-local-artifact-store/v1";
    private readonly string rootPath;

    public ContentAddressedArtifactStore(string rootPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootPath);
        AgentValidation.EnsurePlainDirectory(rootPath, nameof(rootPath));
        this.rootPath = Path.GetFullPath(rootPath);
        Directory.CreateDirectory(this.rootPath);
        var marker = Path.Combine(this.rootPath, ".hwpx-agent-artifact-store");
        if (!File.Exists(marker))
        {
            try
            {
                using var stream = new FileStream(marker, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                using var writer = new StreamWriter(stream, new System.Text.UTF8Encoding(false));
                writer.Write(StoreMarker);
                writer.Flush();
                stream.Flush(flushToDisk: true);
            }
            catch (IOException) when (File.Exists(marker))
            {
                // Another constructor created the same immutable marker.
            }
        }

        if ((File.GetAttributes(marker) & FileAttributes.ReparsePoint) != 0
            || !string.Equals(File.ReadAllText(marker), StoreMarker, StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.JournalConflict);
        }
    }

    public async ValueTask<Stream> OpenReadAsync(
        ArtifactRef artifact,
        CancellationToken cancellationToken)
    {
        AgentValidation.ValidateArtifact(artifact);
        var path = ObjectPath(artifact.Sha256);
        RejectInvalidObject(path, artifact.SizeBytes);
        var verified = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 65_536,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        try
        {
            RejectInvalidObject(path, artifact.SizeBytes);
            var digest = await SHA256.HashDataAsync(verified, cancellationToken).ConfigureAwait(false);
            if (!string.Equals(Convert.ToHexStringLower(digest), artifact.Sha256, StringComparison.Ordinal))
            {
                throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
            }

            verified.Position = 0;
            return verified;
        }
        catch
        {
            await verified.DisposeAsync().ConfigureAwait(false);
            throw;
        }
    }

    public async Task UploadAsync(
        ArtifactRef artifact,
        Stream content,
        CancellationToken cancellationToken)
    {
        AgentValidation.ValidateArtifact(artifact);
        ArgumentNullException.ThrowIfNull(content);
        if (!content.CanRead)
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }

        var destination = ObjectPath(artifact.Sha256);
        var partial = Path.Combine(rootPath, $".upload-{Guid.NewGuid():N}.partial");
        try
        {
            await CopyExactAsync(content, partial, artifact, cancellationToken).ConfigureAwait(false);
            if (File.Exists(destination))
            {
                File.Delete(partial);
                await VerifyExistingAsync(destination, artifact, cancellationToken).ConfigureAwait(false);
                return;
            }

            try
            {
                File.Move(partial, destination, overwrite: false);
            }
            catch (IOException) when (File.Exists(destination))
            {
                File.Delete(partial);
                await VerifyExistingAsync(destination, artifact, cancellationToken).ConfigureAwait(false);
            }
        }
        catch
        {
            if (File.Exists(partial))
            {
                File.Delete(partial);
            }

            throw;
        }
    }

    private async Task VerifyExistingAsync(
        string path,
        ArtifactRef artifact,
        CancellationToken cancellationToken)
    {
        RejectInvalidObject(path, artifact.SizeBytes);
        await using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 65_536,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        var digest = await SHA256.HashDataAsync(stream, cancellationToken).ConfigureAwait(false);
        if (!string.Equals(Convert.ToHexStringLower(digest), artifact.Sha256, StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }
    }

    private static async Task CopyExactAsync(
        Stream source,
        string destination,
        ArtifactRef expected,
        CancellationToken cancellationToken)
    {
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

        if (total != expected.SizeBytes
            || !string.Equals(
                Convert.ToHexStringLower(hash.GetHashAndReset()),
                expected.Sha256,
                StringComparison.Ordinal))
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }
    }

    private string ObjectPath(string digest)
    {
        AgentValidation.RequireDigest(digest);
        return Path.Combine(rootPath, $"{digest}.blob");
    }

    private static void RejectInvalidObject(string path, ulong expectedBytes)
    {
        if (!File.Exists(path))
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }

        var info = new FileInfo(path);
        if ((info.Attributes & FileAttributes.ReparsePoint) != 0 || (ulong)info.Length != expectedBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.ArtifactMismatch);
        }
    }
}
