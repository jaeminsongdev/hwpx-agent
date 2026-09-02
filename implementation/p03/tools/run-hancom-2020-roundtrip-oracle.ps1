[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$WorkspaceRoot,

    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedCorpusManifestSha256,

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$ExpectedBuild = '11.0.0.9136',

    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce',

    [ValidateRange(30, 300)]
    [int]$TimeoutSeconds = 120,

    [switch]$ValidateConfigurationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Assert-PathInsideBoundary {
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Boundary
    )

    $candidateFull = [System.IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $boundaryFull = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.Equals($boundaryFull, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $candidateFull.StartsWith($boundaryFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'ROUNDTRIP_ORACLE_PATH_OUTSIDE_WORKSPACE'
    }
    return $candidateFull
}

function Assert-NotReparsePoint {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary
    )

    $cursor = [System.IO.Path]::GetFullPath($Path)
    $boundaryFull = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    while ($true) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'ROUNDTRIP_ORACLE_REPARSE_POINT_REFUSED'
            }
        }
        if ($cursor.TrimEnd('\').Equals($boundaryFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            break
        }
        $parent = [System.IO.Directory]::GetParent($cursor)
        if ($null -eq $parent) { throw 'ROUNDTRIP_ORACLE_BOUNDARY_WALK_FAILED' }
        $cursor = $parent.FullName
    }
}

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value.Contains('"')) { throw 'ROUNDTRIP_ORACLE_PROCESS_ARGUMENT_CONTAINS_QUOTE' }
    return '"' + $Value + '"'
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $encoding = [System.Text.UTF8Encoding]::new($false)
    $bytes = $encoding.GetBytes($Content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)

    $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $progIdKey = $null
    $clsidSubKey = $null
    $clsidKey = $null
    $localServerKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($RequestedProgId)
        if ($null -eq $progIdKey) { throw 'ROUNDTRIP_ORACLE_PROGID_NOT_REGISTERED_32BIT' }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) { throw 'ROUNDTRIP_ORACLE_CLSID_MISSING' }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $localServerKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $localServerKey) { throw 'ROUNDTRIP_ORACLE_LOCALSERVER32_MISSING' }
        $serverCommand = [string]$localServerKey.GetValue('')
    }
    finally {
        foreach ($key in @($localServerKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $serverCommand.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'ROUNDTRIP_ORACLE_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Stop-OwnedHancomProcesses {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][string]$ExpectedPath,
        [Parameter(Mandatory)][int]$SessionId
    )

    $cleaned = 0
    $refused = 0
    $errors = 0
    foreach ($cimProcess in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        $runtimeProcess = Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtimeProcess) { continue }
        $processPath = [string]$cimProcess.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($processPath)) {
            try { $processPath = [string]$runtimeProcess.Path } catch { $processPath = '' }
        }
        $createdAt = if ($null -ne $cimProcess.CreationDate) {
            [datetime]$cimProcess.CreationDate
        }
        else { [datetime]::MinValue }
        $safeToClean =
            [int]$cimProcess.SessionId -eq $SessionId -and
            $createdAt -ge $StartedAt.AddSeconds(-2) -and
            $processPath.Equals($ExpectedPath, [System.StringComparison]::OrdinalIgnoreCase) -and
            $cimProcess.CommandLine -match '(?i)-Automation\s+-Embedding\s*$'
        if (-not $safeToClean) {
            $refused += 1
            continue
        }
        try {
            Stop-Process -Id $cimProcess.ProcessId -Force -ErrorAction Stop
            Wait-Process -Id $cimProcess.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            $cleaned += 1
        }
        catch {
            if ($null -eq (Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue)) {
                $cleaned += 1
            }
            else { $errors += 1 }
        }
    }
    return [ordered]@{ cleaned = $cleaned; refused = $refused; errors = $errors }
}

$resolvedWorkspaceRoot = (Resolve-Path -LiteralPath $WorkspaceRoot).Path.TrimEnd('\')
if (-not (Test-Path -LiteralPath $resolvedWorkspaceRoot -PathType Container)) {
    throw 'ROUNDTRIP_ORACLE_WORKSPACE_NOT_DIRECTORY'
}
Assert-NotReparsePoint -Path $resolvedWorkspaceRoot -Boundary $resolvedWorkspaceRoot

$caseDefinitions = @(
    [ordered]@{ fixture_ordinal = 0; mode = 'preserving'; relative_path = 'fixture-0\preserving.hwpx' },
    [ordered]@{ fixture_ordinal = 0; mode = 'normalized'; relative_path = 'fixture-0\normalized.hwpx' },
    [ordered]@{ fixture_ordinal = 1; mode = 'preserving'; relative_path = 'fixture-1\preserving.hwpx' },
    [ordered]@{ fixture_ordinal = 1; mode = 'normalized'; relative_path = 'fixture-1\normalized.hwpx' }
)

$manifestRows = @()
foreach ($case in $caseDefinitions) {
    $candidate = Join-Path $resolvedWorkspaceRoot ([string]$case.relative_path)
    $resolvedPath = (Resolve-Path -LiteralPath $candidate).Path
    $resolvedPath = Assert-PathInsideBoundary -Candidate $resolvedPath -Boundary $resolvedWorkspaceRoot
    Assert-NotReparsePoint -Path $resolvedPath -Boundary $resolvedWorkspaceRoot
    $item = Get-Item -LiteralPath $resolvedPath
    if (-not $item.PSIsContainer -and $item.Extension -ceq '.hwpx') {
        $case.full_path = $resolvedPath
        $case.input_size = [int64]$item.Length
        $case.input_sha256 = Get-Sha256File -Path $resolvedPath
        $manifestRows += ('{0}|{1}|{2}|{3}' -f
            $case.fixture_ordinal,
            $case.mode,
            $case.input_sha256,
            $case.input_size)
    }
    else { throw 'ROUNDTRIP_ORACLE_INPUT_NOT_HWPX_FILE' }
}
$manifestSeed = $manifestRows -join "`n"
$manifestSha256 = Get-Sha256String -Value $manifestSeed
if ($manifestSha256 -cne $ExpectedCorpusManifestSha256) {
    throw 'ROUNDTRIP_ORACLE_CORPUS_MANIFEST_SHA256_MISMATCH'
}

$childScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run-hancom-2020-roundtrip-oracle-child.ps1')).Path
$x86PowerShell = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $x86PowerShell -PathType Leaf)) {
    throw 'ROUNDTRIP_ORACLE_X86_POWERSHELL_MISSING'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedBuild -or $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'ROUNDTRIP_ORACLE_TARGET_IDENTITY_MISMATCH'
}

if ($ValidateConfigurationOnly) {
    [ordered]@{
        schema_version = 'hwpx-agent.hancom-2020-roundtrip-config/v1'
        state = 'pass'
        corpus_manifest_sha256 = $manifestSha256
        input_count = $caseDefinitions.Count
        target = [ordered]@{
            prog_id = $ProgId
            observed_file_version = $identity.file_version
            observed_executable_sha256 = $identity.sha256
            registry_view = 'Registry32'
            client = 'windows_powershell_x86_sta'
        }
        com_activation_performed = $false
        document_opened = $false
        input_modified = $false
    } | ConvertTo-Json -Depth 5
    exit 0
}

$receiptPath = Join-Path $resolvedWorkspaceRoot 'oracle-receipt.json'
$traceDirectory = Join-Path $resolvedWorkspaceRoot '.oracle-traces'
if ((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath $traceDirectory)) {
    throw 'ROUNDTRIP_ORACLE_OUTPUT_ALREADY_EXISTS'
}
[void][System.IO.Directory]::CreateDirectory($traceDirectory)
Assert-NotReparsePoint -Path $traceDirectory -Boundary $resolvedWorkspaceRoot

$before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($before.Count -ne 0) { throw 'ROUNDTRIP_ORACLE_PREEXISTING_HWP_PROCESS' }

$caseResults = @()
$currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$runFailed = $false
$runErrorCode = $null

foreach ($case in $caseDefinitions) {
    if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
        $runFailed = $true
        $runErrorCode = 'ROUNDTRIP_ORACLE_HWP_PROCESS_PRESENT_BETWEEN_CASES'
        break
    }

    $traceLeaf = 'fixture-{0}-{1}.json' -f $case.fixture_ordinal, $case.mode
    $tracePath = Join-Path $traceDirectory $traceLeaf
    $startedAt = Get-Date
    $arguments = @(
        '-NoProfile',
        '-NonInteractive',
        '-STA',
        '-File', $childScript,
        '-InputPath', [string]$case.full_path,
        '-ExpectedInputSha256', [string]$case.input_sha256,
        '-FixtureOrdinal', [string]$case.fixture_ordinal,
        '-Mode', [string]$case.mode,
        '-TracePath', $tracePath,
        '-ProgId', $ProgId,
        '-ExpectedBuild', $ExpectedBuild
    )
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $x86PowerShell
    $startInfo.Arguments = (($arguments | ForEach-Object {
        ConvertTo-ProcessArgument -Value ([string]$_)
    }) -join ' ')
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $child = [System.Diagnostics.Process]::new()
    $child.StartInfo = $startInfo
    [void]$child.Start()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()

    $exitedWithinTimeout = $child.WaitForExit($TimeoutSeconds * 1000)
    if (-not $exitedWithinTimeout) {
        $child.Kill()
        $child.WaitForExit()
    }
    $childExitCode = $child.ExitCode
    $outputDrained = $false
    try {
        $outputDrained = [System.Threading.Tasks.Task]::WaitAll(
            [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask),
            5000
        )
    }
    catch { $outputDrained = $false }

    Start-Sleep -Milliseconds 750
    $cleanup = Stop-OwnedHancomProcesses `
        -StartedAt $startedAt `
        -ExpectedPath $identity.path `
        -SessionId $currentSessionId
    Start-Sleep -Milliseconds 500
    $remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)

    $trace = $null
    $traceSha256 = $null
    if (Test-Path -LiteralPath $tracePath -PathType Leaf) {
        $traceSha256 = Get-Sha256File -Path $tracePath
        try { $trace = Get-Content -LiteralPath $tracePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $trace = $null }
    }
    $correlated = $null -ne $trace -and
        [int]$trace.fixture_ordinal -eq [int]$case.fixture_ordinal -and
        [string]$trace.mode -ceq [string]$case.mode -and
        [string]$trace.input_sha256 -ceq [string]$case.input_sha256 -and
        [string]$trace.automation_version_normalized -ceq $ExpectedBuild -and
        [string]$trace.apartment_state -ceq 'STA'
    $caseState = if (-not $exitedWithinTimeout) { 'failed' }
    elseif (-not $outputDrained) { 'failed' }
    elseif (-not $correlated) { 'failed' }
    elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') { 'failed' }
    elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) { 'unverified' }
    else { 'pass' }
    $caseError = if (-not $exitedWithinTimeout) { 'ROUNDTRIP_ORACLE_TIMEOUT' }
    elseif (-not $outputDrained) { 'ROUNDTRIP_ORACLE_CHILD_OUTPUT_DRAIN_TIMEOUT' }
    elseif (-not $correlated) { 'ROUNDTRIP_ORACLE_TRACE_INVALID' }
    elseif ($childExitCode -ne 0 -or [string]$trace.state -cne 'pass') {
        if ($null -ne $trace -and $null -ne $trace.error_code) {
            [string]$trace.error_code
        }
        else { 'ROUNDTRIP_ORACLE_CHILD_FAILED' }
    }
    elseif ([int]$cleanup.refused -ne 0 -or [int]$cleanup.errors -ne 0 -or $remaining.Count -ne 0) {
        'ROUNDTRIP_ORACLE_PROCESS_CLEANUP_UNVERIFIED'
    }
    else { $null }

    $caseResults += [ordered]@{
        fixture_ordinal = [int]$case.fixture_ordinal
        mode = [string]$case.mode
        state = $caseState
        error_code = $caseError
        input_sha256 = [string]$case.input_sha256
        input_size = [int64]$case.input_size
        trace_sha256 = $traceSha256
        text_sha256 = if ($null -ne $trace) { [string]$trace.text_sha256 } else { $null }
        text_utf8_length = if ($null -ne $trace) { [int]$trace.text_utf8_length } else { 0 }
        child_exit_code = $childExitCode
        timed_out = -not $exitedWithinTimeout
        cleaned_process_count = [int]$cleanup.cleaned
        cleanup_refused_count = [int]$cleanup.refused
        cleanup_error_count = [int]$cleanup.errors
        remaining_hwp_process_count = $remaining.Count
    }
    if ($caseState -cne 'pass') {
        $runFailed = $true
        $runErrorCode = $caseError
        break
    }
}

$pairResults = @()
foreach ($ordinal in 0..1) {
    $preserving = @($caseResults | Where-Object {
        [int]$_.fixture_ordinal -eq $ordinal -and [string]$_.mode -ceq 'preserving'
    })
    $normalized = @($caseResults | Where-Object {
        [int]$_.fixture_ordinal -eq $ordinal -and [string]$_.mode -ceq 'normalized'
    })
    $pairPass = $preserving.Count -eq 1 -and $normalized.Count -eq 1 -and
        [string]$preserving[0].state -ceq 'pass' -and
        [string]$normalized[0].state -ceq 'pass' -and
        [string]$preserving[0].text_sha256 -ceq [string]$normalized[0].text_sha256 -and
        [int]$preserving[0].text_utf8_length -eq [int]$normalized[0].text_utf8_length
    $pairResults += [ordered]@{
        fixture_ordinal = $ordinal
        preserving_and_normalized_text_equal = $pairPass
        text_sha256 = if ($pairPass) { [string]$preserving[0].text_sha256 } else { $null }
        text_utf8_length = if ($pairPass) { [int]$preserving[0].text_utf8_length } else { 0 }
    }
    if (-not $pairPass) {
        $runFailed = $true
        if ($null -eq $runErrorCode) { $runErrorCode = 'ROUNDTRIP_ORACLE_SEMANTIC_PAIR_MISMATCH' }
    }
}

$receipt = [ordered]@{
    schema_version = 'hwpx-agent.hancom-2020-roundtrip-receipt/v1'
    state = if ($runFailed) { 'failed' } else { 'pass' }
    error_code = $runErrorCode
    corpus_manifest_sha256 = $manifestSha256
    target = [ordered]@{
        prog_id = $ProgId
        observed_file_version = $identity.file_version
        observed_executable_sha256 = $identity.sha256
        registry_view = 'Registry32'
        client_apartment_state = 'STA'
    }
    cases = $caseResults
    pairs = $pairResults
    privacy = [ordered]@{
        restricted_output = $true
        raw_document_text_present = $false
        absolute_private_paths_present = $false
        user_document_scan_performed = $false
        input_modified = $false
        output_saved = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
    }
}
Write-NewUtf8File -Path $receiptPath -Content ($receipt | ConvertTo-Json -Depth 10)
$receipt | ConvertTo-Json -Depth 10
if ($runFailed) { exit 2 }
