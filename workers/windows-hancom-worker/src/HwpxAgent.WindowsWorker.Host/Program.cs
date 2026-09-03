using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.Host;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            return RunAsync(args).GetAwaiter().GetResult();
        }
        catch (Exception)
        {
            Console.Error.WriteLine("STA_WORKER_FAILED");
            return 2;
        }
    }

    private static async Task<int> RunAsync(string[] args)
    {
        var arguments = ParseArguments(args);
        var options = new StaWorkerOptions(
            arguments["--pipe"],
            arguments["--session"],
            ulong.Parse(arguments["--fence"], System.Globalization.CultureInfo.InvariantCulture),
            arguments["--trace"],
            arguments["--profile"]);
        options.Validate();
        using var shutdown = new CancellationTokenSource();
        ConsoleCancelEventHandler onCancel = (_, eventArgs) =>
        {
            eventArgs.Cancel = true;
            shutdown.Cancel();
        };
        Console.CancelKeyPress += onCancel;
        try
        {
            var server = new StaWorkerServer();
            await server
                .RunAsync(options, new ApartmentBoundaryCommandHandler(), shutdown.Token)
                .ConfigureAwait(false);
            return 0;
        }
        finally
        {
            Console.CancelKeyPress -= onCancel;
        }
    }

    private static Dictionary<string, string> ParseArguments(string[] args)
    {
        var allowed = new HashSet<string>(StringComparer.Ordinal)
        {
            "--pipe",
            "--session",
            "--fence",
            "--trace",
            "--profile",
        };
        if (args.Length != allowed.Count * 2)
        {
            throw new ArgumentException("The STA worker requires an exact argument set.", nameof(args));
        }

        var parsed = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var index = 0; index < args.Length; index += 2)
        {
            var key = args[index];
            var value = args[index + 1];
            if (!allowed.Contains(key) || string.IsNullOrWhiteSpace(value) || !parsed.TryAdd(key, value))
            {
                throw new ArgumentException("The STA worker argument set is invalid.", nameof(args));
            }
        }

        return parsed;
    }
}
