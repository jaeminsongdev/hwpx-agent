using Google.Protobuf;
using HwpxAgent.Protocol.Foundation.V1;
using HwpxAgent.Protocol.WindowsBridge.V1;
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

const string openCommandVector =
    "08011a2430303030303030302d303030302d343030302d383030302d303030303030303030303031222430303030303030302d303030302d343030302d383030302d30303030303030303030303228073080a0f1c2b1343a2430303030303030302d303030302d343030302d383030302d303030303030303030303033aa01770a640a540a0d666978747572652d696e70757412406363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636318d23e120a696e7075745f303030311801120f66696c652e6c6f63616c5f72656164";
var openBytes = Convert.FromHexString(openCommandVector);
var openCommand = WorkerBoundary.DecodeAndValidate(openBytes);
if (!openCommand.ToByteArray().AsSpan().SequenceEqual(openBytes))
{
    Console.Error.WriteLine("C# did not preserve the Rust bridge wire vector");
    return 1;
}

var pathCommand = openCommand.Clone();
pathCommand.OpenDocument.Input.SandboxHandle = "../user-document.hwpx";
try
{
    WorkerBoundary.Validate(pathCommand);
    Console.Error.WriteLine("path-like bridge sandbox handle was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

var uppercaseCommand = openCommand.Clone();
uppercaseCommand.SessionId = "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA";
try
{
    WorkerBoundary.Validate(uppercaseCommand);
    Console.Error.WriteLine("noncanonical uppercase UUID was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

try
{
    WorkerBoundary.DecodeAndValidate(new byte[1_048_577]);
    Console.Error.WriteLine("oversized Windows bridge frame was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

var rawActionCommand = openCommand.Clone();
rawActionCommand.ExecutePlan = new StaExecutePlanCommand
{
    OperationPlan = openCommand.OpenDocument.Input.Clone(),
    BindingBundleId = "haction.run",
    BindingBundleSha256 = new string('d', 64),
};
try
{
    WorkerBoundary.Validate(rawActionCommand);
    Console.Error.WriteLine("raw automation bridge binding was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

var unsafePolicyCommand = openCommand.Clone();
unsafePolicyCommand.StartSession = new StaStartSessionCommand
{
    TargetProfile = new TargetProfileIdentity
    {
        ProfileId = "hancom-hangul-2020-secondary",
        ProductBuild = "11.0.0.9136",
        Locale = "ko-KR",
        ProcessArchitecture = "x86",
        ExecutableSha256 = new string('a', 64),
        EnvironmentDigest = new string('b', 64),
    },
    CapabilityRegistrySha256 = new string('c', 64),
    SecurityPolicy = new SecurityPolicy
    {
        AllowMacros = true,
        FileAccessPolicyId = "file.local_read",
        ModalPolicyId = "modal.fail_closed",
    },
};
try
{
    WorkerBoundary.Validate(unsafePolicyCommand);
    Console.Error.WriteLine("unsafe STA security policy was accepted");
    return 1;
}
catch (ArgumentException)
{
    // Expected fail-closed behavior.
}

var bridgeService = WindowsBridgeReflection.Descriptor.Services[0];
var bridgeMethods = bridgeService.Methods.Select(method => method.Name).ToArray();
if (bridgeService.Name != "WindowsAgentControl"
    || !bridgeMethods.SequenceEqual(["AcquireLease", "Heartbeat", "CommitExecution", "ReportProbe"]))
{
    Console.Error.WriteLine("Windows bridge service descriptor drifted");
    return 1;
}

Console.WriteLine("windows worker semantic and P10 bridge compatibility smoke passed");
return 0;
