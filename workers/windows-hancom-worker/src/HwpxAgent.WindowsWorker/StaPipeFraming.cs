using Google.Protobuf;

namespace HwpxAgent.WindowsWorker;

public static class StaPipeFraming
{
    public const int MaximumFrameBytes = 1_048_576;

    public static async ValueTask<byte[]?> ReadFrameAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(stream);
        if (!stream.CanRead)
        {
            throw new StaTransportException(StaTransportError.UnreadableStream);
        }

        var singleByte = new byte[1];
        uint length = 0;
        var headerBytes = 0;
        while (headerBytes < 5)
        {
            var read = await stream.ReadAsync(singleByte, cancellationToken).ConfigureAwait(false);
            if (read == 0)
            {
                if (headerBytes == 0)
                {
                    return null;
                }

                throw new StaTransportException(StaTransportError.TruncatedFrame);
            }

            var value = singleByte[0];
            if (headerBytes == 4 && (value & 0xf0) != 0)
            {
                throw new StaTransportException(StaTransportError.InvalidLengthPrefix);
            }

            length |= (uint)(value & 0x7f) << (headerBytes * 7);
            headerBytes += 1;
            if ((value & 0x80) == 0)
            {
                if (headerBytes > 1 && length < (1u << ((headerBytes - 1) * 7)))
                {
                    throw new StaTransportException(StaTransportError.NonCanonicalLengthPrefix);
                }

                break;
            }
        }

        if ((singleByte[0] & 0x80) != 0)
        {
            throw new StaTransportException(StaTransportError.InvalidLengthPrefix);
        }

        if (length is 0 or > MaximumFrameBytes)
        {
            throw new StaTransportException(StaTransportError.FrameLimit);
        }

        var payload = new byte[checked((int)length)];
        var offset = 0;
        while (offset < payload.Length)
        {
            var read = await stream
                .ReadAsync(payload.AsMemory(offset), cancellationToken)
                .ConfigureAwait(false);
            if (read == 0)
            {
                throw new StaTransportException(StaTransportError.TruncatedFrame);
            }

            offset += read;
        }

        return payload;
    }

    public static async ValueTask WriteMessageAsync(
        Stream stream,
        IMessage message,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(message);
        var calculatedSize = message.CalculateSize();
        if (calculatedSize is 0 or > MaximumFrameBytes)
        {
            throw new StaTransportException(StaTransportError.FrameLimit);
        }

        var payload = message.ToByteArray();
        if (payload.Length != calculatedSize)
        {
            throw new StaTransportException(StaTransportError.InvalidEnvelope);
        }

        await WriteFrameAsync(stream, payload, cancellationToken).ConfigureAwait(false);
    }

    public static async ValueTask WriteFrameAsync(
        Stream stream,
        ReadOnlyMemory<byte> payload,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(stream);
        if (!stream.CanWrite)
        {
            throw new StaTransportException(StaTransportError.UnwritableStream);
        }

        if (payload.Length is 0 or > MaximumFrameBytes)
        {
            throw new StaTransportException(StaTransportError.FrameLimit);
        }

        Span<byte> header = stackalloc byte[5];
        var remaining = (uint)payload.Length;
        var headerLength = 0;
        do
        {
            var current = (byte)(remaining & 0x7f);
            remaining >>= 7;
            if (remaining != 0)
            {
                current |= 0x80;
            }

            header[headerLength++] = current;
        }
        while (remaining != 0);

        await stream.WriteAsync(header[..headerLength].ToArray(), cancellationToken).ConfigureAwait(false);
        await stream.WriteAsync(payload, cancellationToken).ConfigureAwait(false);
        await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
    }
}

public enum StaTransportError
{
    UnreadableStream,
    UnwritableStream,
    InvalidLengthPrefix,
    NonCanonicalLengthPrefix,
    FrameLimit,
    TruncatedFrame,
    MalformedProtobuf,
    InvalidEnvelope,
    BindingMismatch,
    DuplicateCommand,
    InvalidSequence,
    ConnectionClosed,
}

public sealed class StaTransportException : IOException
{
    public StaTransportException(StaTransportError error)
        : base($"STA transport rejected input: {error}.")
    {
        Error = error;
    }

    public StaTransportException(StaTransportError error, Exception innerException)
        : base($"STA transport rejected input: {error}.", innerException)
    {
        Error = error;
    }

    public StaTransportError Error { get; }
}
