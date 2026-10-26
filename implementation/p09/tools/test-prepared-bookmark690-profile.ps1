[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'MODELS_ONLY_REQUIRED'}
$run=0;$failures=0
foreach ($name in @('run-prepared-bookmark690-worker.ps1','prepared-bookmark690-ports.ps1','prepared-bookmark690-channel.ps1')) {
    $run++;$tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    if (@($errors).Count -ne 0) {$failures++}
}
$run++
$worker=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'run-prepared-bookmark690-worker.ps1'))
if (-not ($worker.Contains('Select-Object -Skip 6') -and $worker.Contains('$sourceIndex=$index+6') -and
    $worker.Contains('$completed -eq 2') -and $worker.Contains('planned_cases=2') -and
    $worker.Contains('PreparedBlockRemainingTwoAfterCurrentSession'))) {$failures++}
[ordered]@{run=$run;errors=0;failures=$failures;skipped=0;actual_native_started=$false}|ConvertTo-Json -Compress
if ($failures -ne 0) {exit 2}
