using HwpxAgent.WindowsWorker;

namespace HwpxAgent.WindowsWorker.TestHost;

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
            Console.Error.WriteLine("STA_TEST_HOST_FAILED");
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
        var server = new StaWorkerServer();
        await server
            .RunAsync(options, new ApartmentBoundaryCommandHandler(), CancellationToken.None)
            .ConfigureAwait(false);
        return 0;
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
            throw new ArgumentException("The STA test host requires an exact argument set.", nameof(args));
        }

        var parsed = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var index = 0; index < args.Length; index += 2)
        {
            if (!allowed.Contains(args[index])
                || string.IsNullOrWhiteSpace(args[index + 1])
                || !parsed.TryAdd(args[index], args[index + 1]))
            {
                throw new ArgumentException("The STA test host argument set is invalid.", nameof(args));
            }
        }

        return parsed;
    }
}
