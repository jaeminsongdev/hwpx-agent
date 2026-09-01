using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.WindowsWorker;

var valid = new WorkerRequestContext
{
    RequestId = Guid.Empty.ToString("D"),
    JobId = Guid.Empty.ToString("D"),
    TraceId = Guid.Empty.ToString("D"),
    CapabilityId = "document.create",
    Input = new ArtifactRef
    {
        ArtifactId = "fixture-empty",
        Sha256 = new string('a', 64),
        SizeBytes = 0,
    },
};
WorkerBoundary.Validate(valid);

var forbidden = valid.Clone();
forbidden.CapabilityId = "haction.run";
try
{
    WorkerBoundary.Validate(forbidden);
    Console.Error.WriteLine("raw HAction capability was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

var pathLikeArtifact = valid.Clone();
pathLikeArtifact.Input = pathLikeArtifact.Input.Clone();
pathLikeArtifact.Input.ArtifactId = "../user-document.hwpx";
try
{
    WorkerBoundary.Validate(pathLikeArtifact);
    Console.Error.WriteLine("path-like artifact ID was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

Console.WriteLine("windows worker semantic boundary smoke passed");
return 0;
