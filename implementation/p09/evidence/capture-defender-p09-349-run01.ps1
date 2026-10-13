# P09 diagnostic only: one 15-second capture; no workload, setting change, or upload.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$taskRoot = 'D:\devdata\Diagnostics\HwpxAgent\P09\defender-20261010-run01'
$taskTrace = Join-Path $taskRoot 'defender-scans.etl'
$taskStage = 'authority'
$taskIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$taskPrincipal = New-Object Security.Principal.WindowsPrincipal($taskIdentity)
if (-not $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 4 }
if (Test-Path -LiteralPath $taskRoot) { exit 5 }
New-Item -ItemType Directory -Path $taskRoot -ErrorAction Stop | Out-Null
function Write-TaskJson($Name, $Value) {
    $taskDestination = Join-Path $taskRoot $Name
    $taskText = $Value | ConvertTo-Json -Depth 24
    $taskStream = [IO.File]::Open($taskDestination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try {
        $taskEncoding = New-Object Text.UTF8Encoding($false)
        $taskBytes = $taskEncoding.GetBytes($taskText)
        $taskStream.Write($taskBytes, 0, $taskBytes.Length)
    } finally { $taskStream.Dispose() }
}
function Convert-TaskSafe($Value, $Key = '', $Depth = 0) {
    if ($Depth -gt 18) { return '[DEPTH_LIMIT]' }
    if ($null -eq $Value) { return $null }
    if ($Value -is [string]) {
        $taskText = [string]$Value
        if ($Key -match '(?i)extension' -and $taskText -match '^\.?[A-Za-z0-9]{1,12}$') { return $taskText }
        if ($Key -match '(?i)duration|time' -and $taskText -match '^\d{1,12}(\.\d+)?\s*(ns|us|ms|s|sec|seconds|minutes)?$') { return $taskText }
        if ($taskText -match '[\\/]') {
            $taskScope = if ($taskText -match '(?i)[\\/]hwpx-agent[\\/]') {'hwpx-agent'} elseif ($taskText -match '(?i)MapleRust|[\\/]maple-re') {'MapleRust'} elseif ($taskText -match '(?i)WindowsApps[\\/]OpenAI.Codex|[\\/]OpenAI[\\/]Codex') {'Codex-app'} elseif ($taskText -match '(?i)[\\/]Windows[\\/]') {'Windows'} else {'other'}
            $taskBase = [IO.Path]::GetFileName($taskText)
            $taskKnown = @('python.exe','python3.exe','maple-re.exe','MsMpEng.exe','ChatGPT.exe','codex.exe','node.exe','pwsh.exe','powershell.exe','git.exe','rustc.exe','cargo.exe','wpr.exe')
            $taskBaseSafe = if ($taskBase -in $taskKnown) {$taskBase} else {'[REDACTED_FILE]'}
            $taskExtension = [IO.Path]::GetExtension($taskText)
            if ($taskExtension -notmatch '^\.[A-Za-z0-9]{1,12}$') { $taskExtension = '[REDACTED]' }
            return [pscustomobject]@{scope=$taskScope;basename=$taskBaseSafe;extension=$taskExtension;full_path_redacted=$true}
        }
        if ($taskText -in @('python.exe','python3.exe','maple-re.exe','MsMpEng.exe','ChatGPT.exe','codex.exe','node.exe','pwsh.exe','powershell.exe','git.exe','rustc.exe','cargo.exe','wpr.exe')) { return $taskText }
        return '[REDACTED_STRING]'
    }
    if ($Value -is [bool] -or $Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64] -or $Value -is [uint16] -or $Value -is [uint32] -or $Value -is [uint64] -or $Value -is [single] -or $Value -is [double] -or $Value -is [decimal]) { return $Value }
    if ($Value -is [TimeSpan]) { return [pscustomobject]@{total_milliseconds=$Value.TotalMilliseconds} }
    if ($Value -is [DateTime]) { return $Value.ToUniversalTime().ToString('o') }
    if ($Value -is [Collections.IDictionary]) {
        $taskMap = [ordered]@{}
        foreach ($taskName in $Value.Keys) {
            $taskSafeName = if ([string]$taskName -match '^[A-Za-z][A-Za-z0-9_]{0,80}$') {[string]$taskName} else {'RedactedKey'}
            $taskMap[$taskSafeName] = Convert-TaskSafe $Value[$taskName] $taskSafeName ($Depth+1)
        }
        return [pscustomobject]$taskMap
    }
    if ($Value -is [Collections.IEnumerable]) {
        $taskItems = @(); $taskCount = 0
        foreach ($taskItem in $Value) {
            if ($taskCount -ge 100) { $taskItems += '[ITEM_LIMIT]'; break }
            $taskItems += ,(Convert-TaskSafe $taskItem $Key ($Depth+1)); $taskCount++
        }
        return ,$taskItems
    }
    $taskMap = [ordered]@{}
    foreach ($taskProp in $Value.PSObject.Properties) {
        if ($taskProp.Name -notmatch '^[A-Za-z][A-Za-z0-9_]{0,80}$') { continue }
        $taskMap[$taskProp.Name] = Convert-TaskSafe $taskProp.Value $taskProp.Name ($Depth+1)
    }
    return [pscustomobject]$taskMap
}
try {
    $taskOwn = [Diagnostics.Process]::GetCurrentProcess()
    $taskOwn.PriorityClass = [Diagnostics.ProcessPriorityClass]::BelowNormal
    $taskOwn.ProcessorAffinity = [IntPtr]1
    Write-TaskJson 'started.json' ([pscustomobject]@{schema='p09-defender-capture/v1';state='STARTED';pid=$PID;started_utc=[DateTime]::UtcNow.ToString('o');requested_seconds=15;elevated=$true;own_affinity=1;own_priority='BelowNormal';verification_launched=$false;settings_changed=$false})
    $taskStage = 'recording'
    New-MpPerformanceRecording -RecordTo $taskTrace -Seconds 15 -ErrorAction Stop *> $null
    if (-not (Test-Path -LiteralPath $taskTrace)) { throw 'TRACE_NOT_CREATED' }
    $taskTraceInfo = Get-Item -LiteralPath $taskTrace
    Write-TaskJson 'recording-complete.json' ([pscustomobject]@{state='RECORDED';completed_utc=[DateTime]::UtcNow.ToString('o');bytes=$taskTraceInfo.Length;trace_private_not_uploaded=$true})
    if ($taskTraceInfo.Length -le 0 -or $taskTraceInfo.Length -gt 536870912) { throw 'TRACE_SIZE_BOUND' }
    $taskStage = 'analysis'
    $taskRaw = Get-MpPerformanceReport -Path $taskTrace -TopProcesses 5 -TopExtensionsPerProcess 3 -TopExtensions 5 -TopFiles 5 -Overview -Raw -ErrorAction Stop 3>$null 4>$null 5>$null 6>$null
    if ($taskRaw -is [string]) { $taskRaw = $taskRaw | ConvertFrom-Json }
    $taskSafe = Convert-TaskSafe $taskRaw
    Write-TaskJson 'report.sanitized.json' $taskSafe
    $taskStage = 'complete'
    Write-TaskJson 'result.json' ([pscustomobject]@{schema='p09-defender-capture/v1';state='RECORDED_AND_ANALYZED';completed_utc=[DateTime]::UtcNow.ToString('o');recorded_seconds=15;trace_bytes=$taskTraceInfo.Length;private_raw_trace_preserved=$true;report_full_paths_and_unknown_strings_redacted=$true;verification_launched=$false;settings_changed=$false;exclusions_added=$false;foreign_process_terminated=$false})
    exit 0
} catch {
    Write-TaskJson 'result.json' ([pscustomobject]@{schema='p09-defender-capture/v1';state='FAILED_NOT_ACCEPTED';stage=$taskStage;error_type=$_.Exception.GetType().Name;full_error_not_recorded=$true;completed_utc=[DateTime]::UtcNow.ToString('o');verification_launched=$false;settings_changed=$false;exclusions_added=$false})
    exit 2
}

