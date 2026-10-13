# Authorized, timed diagnostic only. No Defender preferences, exclusions, scans, or foreign trace cancellation.
[CmdletBinding()]
param([ValidatePattern('^run[0-9]{2}$')][string]$Run = 'run01')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$directory = Join-Path $root "target/private/p09-149-defender-diagnostic/$Run"
$trace = Join-Path $directory 'defender.etl'
$final = Join-Path $directory 'summary.v1.json'
$watch = [Diagnostics.Stopwatch]::StartNew()
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'P149_ADMIN_REQUIRED' }
$expectedRoot = 'D:\' + [char]0xAC1C + [char]0xBC1C + '\hwpx-agent'
if ($root -ne $expectedRoot) { throw 'P149_WRONG_ROOT' }
# Validate every existing ancestor; never follow a reparse directory into another location.
$ancestor = $directory
while ($ancestor -and $ancestor.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
    if (Test-Path -LiteralPath $ancestor) {
        if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'P149_REPARSE_SCOPE' }
    }
    if ($ancestor -eq $root) { break }
    $ancestor = [IO.Path]::GetDirectoryName($ancestor)
}
if (Test-Path -LiteralPath $directory) { throw 'P149_FRESH_DIRECTORY_REQUIRED' }
New-Item -ItemType Directory -Path $directory | Out-Null
function Write-FreshJson([string]$Path, $Value) {
    $raw = [Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 16))
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $stream.Write($raw, 0, $raw.Length) } finally { $stream.Dispose() }
}
function Safe-Path([string]$Value, [string]$Field) {
    if ($Field -match 'Process') {
        $name = [IO.Path]::GetFileName($Value)
        if ($name -in @('rustc.exe','cargo.exe','python.exe','powershell.exe','pwsh.exe','wpr.exe','MsMpEng.exe','ChatGPT.exe','codex.exe','Everything.exe','RadeonSoftware.exe')) { return $name }
        return 'other-process-redacted'
    }
    $prefix = $root + [IO.Path]::DirectorySeparatorChar
    if ($Value.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        $relative = $Value.Substring($prefix.Length).Replace('\','/')
        if ($relative.StartsWith('target/') -and -not $relative.StartsWith('target/private/')) { return $relative }
        if ($relative.StartsWith('crates/') -and $relative.EndsWith('.rs')) { return $relative }
        return 'repo-private-or-other-redacted'
    }
    return 'outside-repository-redacted'
}
function Safe-Value($Value, [string]$Field = '', [int]$Depth = 0) {
    if ($Depth -gt 8) { return 'depth-bounded' }
    if ($null -eq $Value) { return $null }
    if ($Value -is [bool] -or $Value -is [byte] -or $Value -is [int] -or $Value -is [long] -or $Value -is [uint32] -or $Value -is [uint64] -or $Value -is [decimal]) { return $Value }
    if ($Value -is [double] -or $Value -is [single]) {
        if ([double]::IsNaN($Value) -or [double]::IsInfinity($Value)) { return 'invalid-number' }
        return $Value
    }
    if ($Value -is [TimeSpan]) { return [ordered]@{total_milliseconds=$Value.TotalMilliseconds} }
    if ($Value -is [datetime]) { return $Value.ToUniversalTime().ToString('o') }
    if ($Value -is [string]) {
        if ($Field -match 'Path|File|Process') { return Safe-Path $Value $Field }
        if ($Field -match 'Extension' -and $Value -match '^\.[a-zA-Z0-9]{1,12}$') { return $Value }
        return 'string-redacted'
    }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [System.Collections.IDictionary]) {
        $items = @(); $count = 0
        foreach ($item in $Value) {
            if ($count++ -ge 48) { $items += 'item-bound'; break }
            $items += ,(Safe-Value $item $Field ($Depth+1))
        }
        return ,$items
    }
    $safe = [ordered]@{}
    foreach ($property in $Value.PSObject.Properties) {
        if ($property.Name -match '^[a-zA-Z][a-zA-Z0-9_]{0,63}$' -and $property.MemberType -in @('NoteProperty','Property')) {
            $safe[$property.Name] = Safe-Value $property.Value $property.Name ($Depth+1)
        }
    }
    return $safe
}
$process = [Diagnostics.Process]::GetCurrentProcess()
$process.PriorityClass = 'BelowNormal'
$allowed = $process.ProcessorAffinity.ToInt64()
$process.ProcessorAffinity = [IntPtr]($allowed -band (-$allowed))
$start = [ordered]@{schema_version='hwpx-agent.p09-defender-diagnostic/v1';run=$Run;state='ADMIN_TIMED_RECORDING_REQUESTED';
    started_utc=[datetime]::UtcNow.ToString('o');pid=$process.Id;elevated=$true;record_seconds=30;
    source_pin=@{path='tools/p09/record_defender_diagnostic.ps1';bytes=(Get-Item -LiteralPath $PSCommandPath).Length;
        sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()};
    priority='BelowNormal';logical_cpu_limit=1;heavy_verification_started=$false;Defender_settings_changed=$false;
    foreign_processes_modified=$false;raw_trace_private=$true;native_or_SQL_run=$false;P09_gate='OPEN';product_complete=$false}
Write-FreshJson (Join-Path $directory 'started.v1.json') $start
$result = [ordered]@{schema_version=$start.schema_version;run=$Run;state='NOT_ACCEPTED';phase='recording';
    stop_reason=$null;elapsed_seconds=0;heavy_verification_started=$false;Defender_settings_changed=$false;
    foreign_processes_modified=$false;native_or_SQL_run=$false;P09_gate='OPEN';product_complete=$false}
try {
    # Discard console text; retain the authorized private ETL only. Never cancel another recording.
    New-MpPerformanceRecording -RecordTo $trace -Seconds 30 -ErrorAction Stop *> $null
    if (-not (Test-Path -LiteralPath $trace) -or (Get-Item -LiteralPath $trace).Length -le 0) { throw 'P149_TRACE_MISSING' }
    $result.phase = 'analysis'
    Write-FreshJson (Join-Path $directory 'recorded.v1.json') @{state='TRACE_RECORDED_NOT_ANALYZED';ended_utc=[datetime]::UtcNow.ToString('o');bytes=(Get-Item -LiteralPath $trace).Length}
    $report = Get-MpPerformanceReport -Path $trace -Overview -TopFiles 8 -TopProcesses 8 -TopExtensions 8 -Raw -ErrorAction Stop 3>$null 4>$null 5>$null 6>$null
    $result.report_shape = @($report.PSObject.Properties.Name)
    $result.safe_report = Safe-Value $report
    $result.state = 'PASS_RECORDED_ANALYZED_BASELINE_NOT_CAUSE_OR_PRODUCT_PROOF'
    $result.phase = 'complete'
    $result.trace = @{path="target/private/p09-149-defender-diagnostic/$Run/defender.etl";bytes=(Get-Item -LiteralPath $trace).Length}
} catch {
    # Do not print/store tool exception text, filenames, identities, or raw report rows.
    $result.stop_reason = 'RECORDING_OR_ANALYSIS_FAILED_PRIVATE_TRACE_PRESERVED'
    $result.exception_type = $_.Exception.GetType().Name
} finally {
    $watch.Stop()
    $result.elapsed_seconds = [math]::Round($watch.Elapsed.TotalSeconds,2)
    Write-FreshJson $final $result
}
