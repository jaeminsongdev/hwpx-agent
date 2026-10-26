# Parse fixed files only. Never dot-source a candidate or activate Native.
[CmdletBinding()]param([switch]$SyntaxOnly)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
if (-not $SyntaxOnly) {throw 'CURSOR772_SYNTAX_ONLY'}
$names=@('run-prepared-bookmark768-worker','prepared-bookmark768-channel','prepared-bookmark768-ports','bookmark-target-cursor768','test-bookmark-cursor769')
$failed=[Collections.Generic.List[object]]::new()
foreach ($name in $names) {
    $tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot ($name+'.ps1')),[ref]$tokens,[ref]$errors)
    foreach ($item in $errors) {$failed.Add([ordered]@{file=$name;line=$item.Extent.StartLineNumber;error_id=$item.ErrorId})}
}
[ordered]@{run=$names.Count;errors=$failed.Count;failures=0;skipped=0;actual_native_started=$false;syntax_only=$true;parse_errors=$failed.ToArray()}|ConvertTo-Json -Depth 5 -Compress
if ($failed.Count -ne 0) {exit 2}
