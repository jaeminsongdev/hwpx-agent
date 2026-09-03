using Google.Protobuf;
using Grpc.Core;
using Grpc.Net.Client;
using HwpxAgent.Protocol.WindowsBridge.V1;

namespace HwpxAgent.WindowsAgent;

public sealed class GrpcWindowsAgentControlClient : IWindowsAgentControlClient, IAsyncDisposable
{
    private const string ServiceName = "hwpx_agent.windows_bridge.v1.WindowsAgentControl";
    private const int MaximumMessageBytes = 1_048_576;

    private static readonly Method<AgentLeaseRequest, AgentLeaseResponse> AcquireLeaseMethod =
        CreateMethod("AcquireLease", AgentLeaseRequest.Parser, AgentLeaseResponse.Parser);
    private static readonly Method<AgentHeartbeatRequest, AgentHeartbeatResponse> HeartbeatMethod =
        CreateMethod("Heartbeat", AgentHeartbeatRequest.Parser, AgentHeartbeatResponse.Parser);
    private static readonly Method<AgentCommitRequest, AgentCommitResponse> CommitExecutionMethod =
        CreateMethod("CommitExecution", AgentCommitRequest.Parser, AgentCommitResponse.Parser);
    private static readonly Method<AgentProbeRequest, AgentProbeResponse> ReportProbeMethod =
        CreateMethod("ReportProbe", AgentProbeRequest.Parser, AgentProbeResponse.Parser);

    private readonly CallInvoker callInvoker;
    private readonly string bearerToken;
    private readonly TimeSpan timeout;
    private readonly GrpcChannel? ownedChannel;

    public GrpcWindowsAgentControlClient(
        Uri endpoint,
        string bearerToken,
        TimeSpan timeout,
        HttpMessageHandler? httpHandler = null)
    {
        ArgumentNullException.ThrowIfNull(endpoint);
        ValidateEndpoint(endpoint);
        ValidateAuthentication(bearerToken, timeout);

        var options = new GrpcChannelOptions
        {
            MaxReceiveMessageSize = MaximumMessageBytes,
            MaxSendMessageSize = MaximumMessageBytes,
        };
        if (httpHandler is not null)
        {
            options.HttpHandler = httpHandler;
        }

        ownedChannel = GrpcChannel.ForAddress(endpoint, options);
        callInvoker = ownedChannel.CreateCallInvoker();
        this.bearerToken = bearerToken;
        this.timeout = timeout;
    }

    internal GrpcWindowsAgentControlClient(CallInvoker callInvoker, string bearerToken, TimeSpan timeout)
    {
        ArgumentNullException.ThrowIfNull(callInvoker);
        ValidateAuthentication(bearerToken, timeout);
        this.callInvoker = callInvoker;
        this.bearerToken = bearerToken;
        this.timeout = timeout;
    }

    public Task<AgentLeaseResponse> AcquireLeaseAsync(
        AgentLeaseRequest request,
        CancellationToken cancellationToken) =>
        InvokeAsync(AcquireLeaseMethod, request, cancellationToken);

    public Task<AgentHeartbeatResponse> HeartbeatAsync(
        AgentHeartbeatRequest request,
        CancellationToken cancellationToken) =>
        InvokeAsync(HeartbeatMethod, request, cancellationToken);

    public Task<AgentCommitResponse> CommitExecutionAsync(
        AgentCommitRequest request,
        CancellationToken cancellationToken) =>
        InvokeAsync(CommitExecutionMethod, request, cancellationToken);

    public Task<AgentProbeResponse> ReportProbeAsync(
        AgentProbeRequest request,
        CancellationToken cancellationToken) =>
        InvokeAsync(ReportProbeMethod, request, cancellationToken);

    public ValueTask DisposeAsync()
    {
        ownedChannel?.Dispose();
        return ValueTask.CompletedTask;
    }

    private async Task<TResponse> InvokeAsync<TRequest, TResponse>(
        Method<TRequest, TResponse> method,
        TRequest request,
        CancellationToken cancellationToken)
        where TRequest : class
        where TResponse : class
    {
        ArgumentNullException.ThrowIfNull(request);
        if (request is not IMessage requestMessage
            || requestMessage.CalculateSize() > MaximumMessageBytes)
        {
            throw new ArgumentException("The outbound gRPC message exceeds the protocol limit.", nameof(request));
        }

        var headers = new Metadata
        {
            { "authorization", $"Bearer {bearerToken}" },
        };
        var options = new CallOptions(
            headers,
            deadline: DateTime.UtcNow.Add(timeout),
            cancellationToken: cancellationToken);
        var response = await callInvoker
            .AsyncUnaryCall(method, null, options, request)
            .ResponseAsync
            .ConfigureAwait(false);
        if (response is not IMessage responseMessage
            || responseMessage.CalculateSize() > MaximumMessageBytes)
        {
            throw new AgentProtocolException(AgentProtocolError.InvalidState);
        }

        return response;
    }

    private static Method<TRequest, TResponse> CreateMethod<TRequest, TResponse>(
        string methodName,
        MessageParser<TRequest> requestParser,
        MessageParser<TResponse> responseParser)
        where TRequest : class, IMessage<TRequest>
        where TResponse : class, IMessage<TResponse> =>
        new(
            MethodType.Unary,
            ServiceName,
            methodName,
            Marshallers.Create(
                static value => value.ToByteArray(),
                payload => requestParser.ParseFrom(payload)),
            Marshallers.Create(
                static value => value.ToByteArray(),
                payload => responseParser.ParseFrom(payload)));

    private static void ValidateEndpoint(Uri endpoint)
    {
        if (!endpoint.IsAbsoluteUri
            || !string.Equals(endpoint.Scheme, Uri.UriSchemeHttps, StringComparison.Ordinal)
            || !string.IsNullOrEmpty(endpoint.UserInfo)
            || !string.IsNullOrEmpty(endpoint.Query)
            || !string.IsNullOrEmpty(endpoint.Fragment))
        {
            throw new ArgumentException("The control-plane endpoint must be a plain HTTPS authority/path.", nameof(endpoint));
        }
    }

    private static void ValidateAuthentication(string token, TimeSpan rpcTimeout)
    {
        ArgumentNullException.ThrowIfNull(token);
        if (token.Length is < 32 or > 4096
            || token.Any(character => character is < '!' or > '~')
            || rpcTimeout < TimeSpan.FromSeconds(1)
            || rpcTimeout > TimeSpan.FromMinutes(15))
        {
            throw new ArgumentException("Bounded outbound authentication and timeout are required.");
        }
    }
}
