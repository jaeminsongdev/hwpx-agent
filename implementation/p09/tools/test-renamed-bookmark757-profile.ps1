[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'MODELS_ONLY_REQUIRED'}
$run=0;$failures=0
foreach ($name in @('run-prepared-bookmark755-worker.ps1','prepared-bookmark755-ports.ps1','prepared-bookmark755-channel.ps1')) {
    $run++;$tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    if (@($errors).Count -ne 0) {$failures++}
}
$worker=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'run-prepared-bookmark755-worker.ps1'))
$ports=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'prepared-bookmark755-ports.ps1'))
$run++
if (-not ($worker.Contains('PreparedRenamedEightAfterCurrentSession') -and $worker.Contains('planned_cases=8') -and
    $worker.Contains('$sourceIndex=$index') -and -not $worker.Contains('Select-Object -Skip 6'))) {$failures++}
$run++
if (-not ($ports.Contains("@('initial','saved','reopened')") -and
    $ports.Contains('Export-P09Prepared755Pages $State saved') -and
    $ports.Contains('Observe-P09Prepared755Document $State (Join-Path $State.run ''saved.hwpx'') $State.saved.sha256'))) {$failures++}
$run++
if ($worker.Contains('New-Object -ComObject') -or $worker.Contains('GetActiveObject') -or
    $ports.Contains('MoveToBookmark') -or $ports.Contains('UpdateField') -or $ports.Contains('HAction.Execute')) {$failures++}
[ordered]@{run=$run;errors=0;failures=$failures;skipped=0;actual_native_started=$false}|ConvertTo-Json -Compress
if ($failures -ne 0) {exit 2}
