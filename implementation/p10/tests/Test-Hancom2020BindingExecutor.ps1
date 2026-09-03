[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
function Read-RepoFile([string]$relativePath) {
    Get-Content -LiteralPath (Join-Path $root $relativePath) -Raw
}

$executor = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomBindingExecutor.cs'
$session = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomSession.cs'
$handler = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomLifecycleCommandHandler.cs'
$adapter = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomSecurityAdapter.cs'
$agentValidation = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentValidation.cs'
$agentWorkspace = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\AgentWorkspace.cs'
$agentService = Read-RepoFile 'workers\windows-hancom-agent\src\HwpxAgent.WindowsAgent\WindowsAgentService.cs'
$protocol = Read-RepoFile 'protocol\proto\hwpx_agent\windows_bridge\v1\windows_bridge.proto'
$migration = Read-RepoFile 'protocol\migrations\p02-signed-registry-to-p10-execution-bundle-v1.md'
$smoke = Read-RepoFile 'workers\windows-hancom-worker\tests\HwpxAgent.WindowsWorker.BindingSmoke\Program.cs'
$project = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HwpxAgent.WindowsWorker.csproj'
$envelopeSchemaPath = Join-Path $root 'protocol\json-schema\hancom-signed-binding-envelope-v1.schema.json'
$bundleSchemaPath = Join-Path $root 'protocol\json-schema\hancom-binding-bundle-v1.schema.json'
$envelopeSchema = Get-Content -LiteralPath $envelopeSchemaPath -Raw | ConvertFrom-Json
$bundleSchema = Get-Content -LiteralPath $bundleSchemaPath -Raw | ConvertFrom-Json

$firstPreflight = $executor.IndexOf('foreach (var operation in plan.Operations)')
$firstDispatch = $executor.IndexOf('foreach (var invocation in invocations)')
$itemExist = $session.IndexOf('typedSet.ItemExist(parameter.ItemName)')
$setItem = $session.IndexOf('typedSet.SetItem(parameter.ItemName, parameter.Value)')

$checks = [ordered]@{
    schemas_parse = $null -ne $envelopeSchema -and $null -ne $bundleSchema
    schema_draft_2020_12 = $envelopeSchema.'$schema' -ceq 'https://json-schema.org/draft/2020-12/schema' -and
        $bundleSchema.'$schema' -ceq 'https://json-schema.org/draft/2020-12/schema'
    schema_closed_objects = $envelopeSchema.additionalProperties -eq $false -and
        $bundleSchema.additionalProperties -eq $false
    schema_parameter_cross_fields = (Get-Content -LiteralPath $bundleSchemaPath -Raw) -match '"allOf"' -and
        (Get-Content -LiteralPath $bundleSchemaPath -Raw) -match 'half_away_from_zero'
    exact_envelope_versions = $executor -match 'p10-06-signed-binding-envelope/v1' -and
        $executor -match 'p10-06-binding-bundle/v1'
    ed25519_verification = $executor -match 'new Ed25519Signer\(\)' -and
        $executor -match 'VerifySignature\(signature\)'
    exact_payload_signature = $executor -match 'verifier\.BlockUpdate\(payloadBytes' -and
        $executor -match 'Hash\(payloadBytes\)'
    pinned_public_key = $executor -match 'Hash\(publicKeyBytes\)' -and
        $executor -match 'SubjectPublicKeyInfoFactory'
    exact_target_binding = $executor -match 'payload\.Target\.ProfileId' -and
        $executor -match 'payload\.Target\.ProductBuild' -and
        $executor -match 'payload\.Target\.ExecutableSha256'
    source_registry_not_routed = $executor -match 'payload\.Authorization\.SourceRegistryRoutingEnabled' -and
        $migration -match 'routing_enabled=false'
    unknown_json_rejected = $executor -match 'JsonUnmappedMemberHandling\.Disallow' -and
        $executor -match 'RejectDuplicateProperties'
    raw_public_identifier_rejected = $executor -match 'ContainsRawAutomationToken' -and
        $protocol -notmatch '(?m)^\s*string\s+(action_id|parameter_set_id|item_name)\s*='
    bounded_inputs = $executor -match 'MaximumPlanBytes = 4 \* 1024 \* 1024' -and
        $executor -match 'MaximumBindings = 4096' -and
        $executor -match 'MaximumOperations = 1024'
    full_preflight_before_dispatch = $firstPreflight -ge 0 -and $firstDispatch -gt $firstPreflight -and
        $executor -match 'new List<HancomBoundAction>'
    dependency_order_rejected = $executor -match 'operation\.DependsOn.*All\(admitted\.Contains\)' -and
        $executor -match 'OrderBy\(value => value, StringComparer\.Ordinal\)'
    canonical_value_digest = $executor -match 'SerializeCanonicalValue' -and
        $executor -match 'CryptographicOperations\.FixedTimeEquals'
    finite_typed_values = $executor -match '\("text", "string"\)' -and
        $executor -match '\("text", "int32_enum"\)' -and
        $executor -match '\("boolean", "boolean"\)' -and
        $executor -match '\("integer", "int32"\)'
    bounded_rational_scaling = $executor -match 'new BigInteger\(source\) \* numerator' -and
        $executor -match 'half_away_from_zero'
    runtime_action_identity = $session -match 'boundAction\.ActID' -and
        $session -match 'boundAction\.SetID'
    runtime_parameter_set_identity = $session -match 'typedSet\.IsSet' -and
        $session -match 'typedSet\.SetID'
    item_must_exist_before_set = $itemExist -ge 0 -and $setItem -gt $itemExist
    strict_action_results = $session -match 'runResult is bool accepted && accepted' -and
        $session -match 'defaultResult is not bool defaultAccepted' -and
        $session -match 'executeResult is bool executeAccepted && executeAccepted'
    com_objects_released = $session -match 'ReleaseComObject\(parameterSet\)' -and
        $session -match 'ReleaseComObject\(action\)' -and
        $session -match 'ReleaseComObject\(actionCollection\)'
    dispatched_failure_unknown = $session -match 'effectUnknown: true' -and
        $session -match 'State = HancomSessionState\.Faulted'
    resolver_lifecycle_typed = $handler -match 'catch \(HancomLifecycleException error\)' -and
        $smoke -match 'PlanResolverLifecycleFailureReturnsReceiptAsync'
    binding_failure_typed = $handler -match 'HancomBindingError\.UnknownBinding' -and
        $handler -match 'BridgeErrorCode\.UnknownBinding'
    v2_lease_single_use = $adapter -match 'p10-06-security-lease/v2' -and
        $adapter -match 'CompareExchange\(ref planConsumed, 1, 0\)'
    fixed_private_files = $adapter -match 'hancom_operation_plan\.json' -and
        $adapter -match 'hancom_binding_bundle\.json' -and
        $adapter -match 'hancom_binding_public_key\.pem'
    guarded_private_files = $adapter -match 'OpenGuardedBytes' -and
        $adapter -match 'FileShare\.Read'
    agent_verified_copy = $agentWorkspace -match 'CopyPinnedFileAsync' -and
        $agentWorkspace -match 'CopyAndVerifyAsync'
    agent_local_trust_paths = $agentValidation -match 'LocalDrivePathPattern' -and
        $agentWorkspace -match 'RejectReparseChain'
    agent_result_pin = $agentService -match 'result\.BindingBundleId' -and
        $agentService -match 'result\.BindingBundleSha256'
    exact_dependency = $project -match 'BouncyCastle\.Cryptography" Version="2\.7\.0"'
    negative_smoke = $smoke -match 'UnknownBindingStopsBeforeComAsync' -and
        $smoke -match 'RawPublicCapabilityStopsBeforeComAsync' -and
        $smoke -match 'SignatureTamperStopsBeforeComAsync' -and
        $smoke -match 'ComRuntimeRejectsRuntimeIdentityDrift'
    actual_private_ids_not_committed = $smoke -match 'SyntheticAction' -and
        $migration -match 'Raw Action, ParameterSet and item identifiers remain inside the signed private payload'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-06-binding-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 5

if ($failed.Count -ne 0) { exit 2 }
