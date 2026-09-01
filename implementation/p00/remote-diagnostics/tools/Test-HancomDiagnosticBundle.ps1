[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BundlePath,

    [switch]$RequireQualified
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$maximumEntries = 50
$maximumEntryBytes = 5MB
$maximumTotalBytes = 10MB
$requiredPaths = @('events.json', 'inventory.json', 'manifest.json', 'request.json', 'session.json')

function Get-BytesSha256Lower {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($Bytes)) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

function Get-FileSha256Lower {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-ZipEntryBytes {
    param(
        [Parameter(Mandatory)]$Entry,
        [Parameter(Mandatory)][int64]$MaximumBytes
    )
    if ([int64]$Entry.Length -gt $MaximumBytes) {
        throw "ZIP entry exceeds the allowed size: $($Entry.FullName)"
    }
    $source = $Entry.Open()
    $target = New-Object System.IO.MemoryStream
    try {
        $buffer = New-Object byte[] 65536
        $total = 0L
        while (($read = $source.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $total += $read
            if ($total -gt $MaximumBytes) {
                throw "ZIP entry expanded beyond the allowed size: $($Entry.FullName)"
            }
            $target.Write($buffer, 0, $read)
        }
        return $target.ToArray()
    }
    finally {
        $target.Dispose()
        $source.Dispose()
    }
}

function ConvertFrom-StrictUtf8Json {
    param(
        [Parameter(Mandatory)][byte[]]$Bytes,
        [Parameter(Mandatory)][string]$Name
    )
    $encoding = New-Object System.Text.UTF8Encoding($false, $true)
    try {
        $text = $encoding.GetString($Bytes)
        return $text | ConvertFrom-Json
    }
    catch {
        throw "Invalid UTF-8 JSON in $Name"
    }
}

function Assert-Condition {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Code
    )
    if (-not $Condition) {
        throw $Code
    }
}

function Test-FalseValue {
    param($Value)
    return $null -ne $Value -and $Value -is [bool] -and -not [bool]$Value
}

$archive = $null
$archiveStream = $null
$bundleFile = $null
$bundleSha256 = $null
$requestId = $null
$runId = $null
$bundleState = 'invalid'
$qualificationState = 'not_evaluated'
$qualificationError = $null
$fatalCode = $null

try {
    $bundleFile = (Resolve-Path -LiteralPath $BundlePath).Path
    Assert-Condition -Condition (Test-Path -LiteralPath $bundleFile -PathType Leaf) -Code 'BUNDLE_NOT_FOUND'
    $bundleSha256 = Get-FileSha256Lower -Path $bundleFile

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archiveStream = [System.IO.File]::Open($bundleFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    $archive = New-Object System.IO.Compression.ZipArchive($archiveStream, [System.IO.Compression.ZipArchiveMode]::Read, $false)
    $entries = @($archive.Entries)
    Assert-Condition -Condition ($entries.Count -le $maximumEntries) -Code 'ZIP_ENTRY_LIMIT_EXCEEDED'

    $entryMap = @{}
    $totalBytes = 0L
    foreach ($entry in $entries) {
        $name = [string]$entry.FullName
        Assert-Condition -Condition (-not [string]::IsNullOrWhiteSpace($name)) -Code 'ZIP_EMPTY_PATH'
        Assert-Condition -Condition (-not $name.EndsWith('/') -and -not $name.EndsWith('\')) -Code 'ZIP_DIRECTORY_ENTRY_FORBIDDEN'
        Assert-Condition -Condition ($name -notmatch '(^[\\/])|(^[A-Za-z]:)|(^|[\\/])\.\.([\\/]|$)|[\\:]') -Code 'ZIP_UNSAFE_PATH'
        Assert-Condition -Condition ($name -notmatch '[\\/]') -Code 'ZIP_NESTED_PATH_FORBIDDEN'
        $key = $name.ToLowerInvariant()
        Assert-Condition -Condition (-not $entryMap.ContainsKey($key)) -Code 'ZIP_DUPLICATE_PATH'
        Assert-Condition -Condition ([int64]$entry.Length -le $maximumEntryBytes) -Code 'ZIP_ENTRY_LIMIT_EXCEEDED'
        $totalBytes += [int64]$entry.Length
        Assert-Condition -Condition ($totalBytes -le $maximumTotalBytes) -Code 'ZIP_TOTAL_LIMIT_EXCEEDED'
        $entryMap[$key] = $entry
    }

    $actualPaths = @($entryMap.Keys | Sort-Object)
    $expectedPaths = @($requiredPaths | ForEach-Object { $_.ToLowerInvariant() } | Sort-Object)
    Assert-Condition -Condition (($actualPaths -join '|') -ceq ($expectedPaths -join '|')) -Code 'BUNDLE_FILE_SET_MISMATCH'

    $bytesByName = @{}
    foreach ($path in $requiredPaths) {
        $bytesByName[$path] = Read-ZipEntryBytes -Entry $entryMap[$path] -MaximumBytes $maximumEntryBytes
    }
    $request = ConvertFrom-StrictUtf8Json -Bytes $bytesByName['request.json'] -Name 'request.json'
    $inventory = ConvertFrom-StrictUtf8Json -Bytes $bytesByName['inventory.json'] -Name 'inventory.json'
    $events = ConvertFrom-StrictUtf8Json -Bytes $bytesByName['events.json'] -Name 'events.json'
    $session = ConvertFrom-StrictUtf8Json -Bytes $bytesByName['session.json'] -Name 'session.json'
    $manifest = ConvertFrom-StrictUtf8Json -Bytes $bytesByName['manifest.json'] -Name 'manifest.json'

    Assert-Condition -Condition ($request.schema_version -eq 'hwpx-agent.hancom-diagnostic-request/v1') -Code 'REQUEST_SCHEMA_VERSION_INVALID'
    Assert-Condition -Condition ($inventory.schema_version -eq 'hwpx-agent.hancom-diagnostic-inventory/v1') -Code 'INVENTORY_SCHEMA_VERSION_INVALID'
    Assert-Condition -Condition ($events.schema_version -eq 'hwpx-agent.hancom-diagnostic-events/v1') -Code 'EVENTS_SCHEMA_VERSION_INVALID'
    Assert-Condition -Condition ($session.schema_version -eq 'hwpx-agent.hancom-diagnostic-session/v1') -Code 'SESSION_SCHEMA_VERSION_INVALID'
    Assert-Condition -Condition ($manifest.schema_version -eq 'hwpx-agent.hancom-diagnostic-bundle-manifest/v1') -Code 'MANIFEST_SCHEMA_VERSION_INVALID'

    $parsedRequestId = [guid]::Empty
    $parsedRunId = [guid]::Empty
    Assert-Condition -Condition ([guid]::TryParse([string]$request.request_id, [ref]$parsedRequestId)) -Code 'REQUEST_ID_INVALID'
    Assert-Condition -Condition ([guid]::TryParse([string]$session.run_id, [ref]$parsedRunId)) -Code 'RUN_ID_INVALID'
    $requestId = [string]$request.request_id
    $runId = [string]$session.run_id
    Assert-Condition -Condition ([string]$request.challenge_nonce -match '^[0-9a-f]{64}$') -Code 'CHALLENGE_INVALID'
    Assert-Condition -Condition ([string]$request.collector_sha256 -match '^[0-9a-f]{64}$') -Code 'COLLECTOR_HASH_INVALID'
    Assert-Condition -Condition ([string]$session.request_sha256 -match '^[0-9a-f]{64}$') -Code 'REQUEST_HASH_INVALID'

    foreach ($document in @($inventory, $events, $session, $manifest)) {
        Assert-Condition -Condition ([string]$document.request_id -ceq $requestId) -Code 'REQUEST_CORRELATION_MISMATCH'
    }
    foreach ($document in @($inventory, $events, $manifest)) {
        Assert-Condition -Condition ([string]$document.run_id -ceq $runId) -Code 'RUN_CORRELATION_MISMATCH'
    }
    Assert-Condition -Condition ([string]$session.challenge_nonce -ceq [string]$request.challenge_nonce) -Code 'CHALLENGE_MISMATCH'
    Assert-Condition -Condition ([string]$session.collector_sha256 -ceq [string]$request.collector_sha256) -Code 'COLLECTOR_HASH_MISMATCH'
    Assert-Condition -Condition ([string]$session.request_sha256 -ceq (Get-BytesSha256Lower -Bytes $bytesByName['request.json'])) -Code 'REQUEST_HASH_MISMATCH'
    Assert-Condition -Condition ([string]$session.target_profile_id -ceq [string]$request.target.profile_id) -Code 'TARGET_PROFILE_CORRELATION_MISMATCH'
    Assert-Condition -Condition ([string]$session.mode -ceq [string]$request.mode) -Code 'MODE_CORRELATION_MISMATCH'

    Assert-Condition -Condition (Test-FalseValue $request.policy.network_allowed) -Code 'NETWORK_POLICY_VIOLATION'
    Assert-Condition -Condition (Test-FalseValue $request.policy.ui_automation_allowed) -Code 'UI_AUTOMATION_POLICY_VIOLATION'
    Assert-Condition -Condition (Test-FalseValue $request.policy.user_documents_allowed) -Code 'DOCUMENT_POLICY_VIOLATION'
    Assert-Condition -Condition ([string]$request.policy.computer_use_mode -ceq 'screenshot_only') -Code 'COMPUTER_USE_POLICY_VIOLATION'
    Assert-Condition -Condition ([string]$request.policy.event_log_mode -ceq 'metadata_allowlist') -Code 'EVENT_POLICY_VIOLATION'
    Assert-Condition -Condition ([string]$request.policy.crash_dump_mode -ceq 'metadata_only') -Code 'DUMP_POLICY_VIOLATION'
    foreach ($propertyName in @('document_content_collected', 'user_document_opened', 'raw_event_messages_collected', 'dump_content_collected', 'ui_automation_performed', 'network_transmission_performed')) {
        Assert-Condition -Condition (Test-FalseValue $session.privacy.$propertyName) -Code "PRIVACY_INVARIANT_VIOLATION_$propertyName"
    }
    Assert-Condition -Condition (Test-FalseValue $inventory.crash_dump_content_collected) -Code 'DUMP_CONTENT_INVENTORY_VIOLATION'
    Assert-Condition -Condition (Test-FalseValue $events.raw_messages_collected) -Code 'RAW_EVENT_MESSAGE_VIOLATION'
    if ($session.runtime_probe.PSObject.Properties.Name -contains 'raw_stream_content_collected') {
        Assert-Condition -Condition (Test-FalseValue $session.runtime_probe.raw_stream_content_collected) -Code 'RAW_PROBE_STREAM_VIOLATION'
    }

    $manifestPaths = @{}
    foreach ($item in @($manifest.entries)) {
        $path = [string]$item.path
        Assert-Condition -Condition ($path -in @('events.json', 'inventory.json', 'request.json', 'session.json')) -Code 'MANIFEST_PATH_INVALID'
        $key = $path.ToLowerInvariant()
        Assert-Condition -Condition (-not $manifestPaths.ContainsKey($key)) -Code 'MANIFEST_DUPLICATE_PATH'
        Assert-Condition -Condition ([int64]$item.bytes -eq [int64]$bytesByName[$path].Length) -Code 'MANIFEST_SIZE_MISMATCH'
        Assert-Condition -Condition ([string]$item.sha256 -ceq (Get-BytesSha256Lower -Bytes $bytesByName[$path])) -Code 'MANIFEST_HASH_MISMATCH'
        $manifestPaths[$key] = $true
    }
    $expectedManifestPaths = @('events.json', 'inventory.json', 'request.json', 'session.json')
    Assert-Condition -Condition ((@($manifestPaths.Keys | Sort-Object) -join '|') -ceq ((@($expectedManifestPaths | Sort-Object)) -join '|')) -Code 'MANIFEST_FILE_SET_MISMATCH'

    $bundleState = 'valid'
    if ($request.mode -eq 'discover') {
        Assert-Condition -Condition ($session.state -eq 'discovered_unqualified') -Code 'DISCOVERY_STATE_INVALID'
        Assert-Condition -Condition (-not [bool]$session.runtime_probe.attempted) -Code 'DISCOVERY_PROBE_FORBIDDEN'
        $qualificationState = 'discovered_unqualified'
    }
    elseif ($request.mode -eq 'probe') {
        $observation = $session.target_observation
        $probe = $session.runtime_probe
        $probeQualified =
            $session.state -eq 'pass' -and
            $null -eq $session.error_code -and
            $null -ne $observation -and
            [string]$observation.expected_major_release -ceq [string]$request.target.expected_major_release -and
            [string]$observation.observed_major_release -ceq [string]$request.target.expected_major_release -and
            [string]$observation.expected_file_version -ceq [string]$request.target.expected_file_version -and
            [string]$observation.observed_file_version -ceq [string]$request.target.expected_file_version -and
            [string]$observation.expected_executable_sha256 -ceq [string]$request.target.expected_executable_sha256 -and
            [string]$observation.observed_executable_sha256 -ceq [string]$request.target.expected_executable_sha256 -and
            [bool]$probe.attempted -and
            $probe.state -eq 'pass' -and
            -not [bool]$probe.timed_out -and
            [bool]$probe.output_drained -and
            [int]$probe.child_exit_code -eq 0 -and
            [bool]$probe.automation_version_matches_expected -and
            [bool]$probe.quit_invoked -and
            [int]$probe.preexisting_hwp_processes -eq 0 -and
            @($probe.cleanup_refused_process_ids).Count -eq 0 -and
            @($probe.cleanup_errors).Count -eq 0 -and
            [int]$probe.remaining_probe_processes -eq 0 -and
            -not [bool]$probe.document_opened -and
            -not [bool]$probe.file_opened -and
            -not [bool]$probe.register_module_invoked
        if ($probeQualified) {
            $qualificationState = 'pass'
        }
        else {
            $qualificationState = 'failed'
            $qualificationError = if ($session.error_code) { [string]$session.error_code } else { 'RUNTIME_QUALIFICATION_INVARIANT_FAILED' }
        }
    }
    else {
        throw 'REQUEST_MODE_INVALID'
    }
}
catch {
    $fatalCode = if ($_.Exception.Message -match '^[A-Z0-9_]+$') { $_.Exception.Message } else { 'BUNDLE_VERIFICATION_EXCEPTION' }
    $bundleState = 'invalid'
    $qualificationState = 'not_evaluated'
}
finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
    if ($null -ne $archiveStream) {
        $archiveStream.Dispose()
    }
}

[ordered]@{
    verifier_schema_version = 'hwpx-agent.hancom-diagnostic-bundle-verification/v1'
    bundle_state = $bundleState
    qualification_state = $qualificationState
    qualification_error_code = $qualificationError
    verification_error_code = $fatalCode
    request_id = $requestId
    run_id = $runId
    bundle_sha256 = $bundleSha256
    require_qualified = [bool]$RequireQualified
} | ConvertTo-Json -Depth 5

if ($bundleState -ne 'valid') {
    exit 1
}
if ($RequireQualified -and $qualificationState -ne 'pass') {
    exit 2
}
