# Light AST/redaction fixtures only. Never execute the recorder, elevate, or modify Defender.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = 'BelowNormal'
$mask = $self.ProcessorAffinity.ToInt64()
$self.ProcessorAffinity = [IntPtr]($mask -band (-$mask))
$source = Join-Path $PSScriptRoot '../record_defender_diagnostic.ps1'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'P149_DIAGNOSTIC_PARSE_FAILED' }
$functions = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]}, $true))
foreach ($name in @('Safe-Path','Safe-Value')) {
    $matches = @($functions | Where-Object Name -eq $name)
    if ($matches.Count -ne 1) { throw 'P149_REDACTION_FUNCTION_SCOPE' }
    # Import only these pure functions; never dot-source the recorder's top-level code.
    Invoke-Expression $matches[0].Extent.Text
}
$commands = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst]}, $true) | ForEach-Object GetCommandName)
foreach ($forbidden in @('Set-MpPreference','Add-MpPreference','Remove-MpPreference','Start-MpScan','Stop-Process','Remove-Item','Move-Item','Start-Process')) {
    if ($commands -contains $forbidden) { throw 'P149_DIAGNOSTIC_FORBIDDEN_COMMAND' }
}
$recordings = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -eq 'New-MpPerformanceRecording'}, $true))
if ($recordings.Count -ne 1 -or $recordings[0].Extent.Text -notmatch '-Seconds 30' -or $recordings[0].Extent.Text -match '-Cancel') { throw 'P149_DIAGNOSTIC_RECORDING_BOUNDARY' }
if ($ast.Extent.Text -notmatch '\[IO.FileMode\]::CreateNew' -or $ast.Extent.Text -notmatch 'P149_FRESH_DIRECTORY_REQUIRED' -or $ast.Extent.Text -notmatch 'P149_REPARSE_SCOPE') { throw 'P149_DIAGNOSTIC_FRESH_SCOPE' }
$root = 'D:\fixture-repo'
if ((Safe-Path 'C:\fixture-user\outside.exe' 'Path') -ne 'outside-repository-redacted') { throw 'P149_OUTSIDE_PATH_LEAK' }
if ((Safe-Path 'D:\fixture-repo-sibling\target\sample.exe' 'Path') -ne 'outside-repository-redacted') { throw 'P149_SIBLING_PATH_LEAK' }
if ((Safe-Path 'D:\fixture-repo\target\private\sample.exe' 'Path') -ne 'repo-private-or-other-redacted') { throw 'P149_PRIVATE_PATH_LEAK' }
if ((Safe-Path 'D:\fixture-repo\target\debug\sample.exe' 'Path') -ne 'target/debug/sample.exe') { throw 'P149_PUBLIC_PATH_REDACTION' }
if ((Safe-Path 'C:\fixture-user\cargo.exe' 'ProcessPath') -ne 'cargo.exe') { throw 'P149_PROCESS_ROLE_REDACTION' }
if ((Safe-Path 'C:\fixture-user\unknown.exe' 'ProcessPath') -ne 'other-process-redacted') { throw 'P149_UNKNOWN_PROCESS_LEAK' }
if ((Safe-Value 'fixture-sensitive-text' 'Message') -ne 'string-redacted') { throw 'P149_ARBITRARY_STRING_LEAK' }
if ((Safe-Value '.exe' 'Extension') -ne '.exe' -or (Safe-Value '.invalid/extension' 'Extension') -ne 'string-redacted') { throw 'P149_EXTENSION_SCOPE' }
if ((Safe-Value ([double]::NaN)) -ne 'invalid-number' -or (Safe-Value ([double]::PositiveInfinity)) -ne 'invalid-number') { throw 'P149_INVALID_NUMBER' }
if ((Safe-Value 1 '' 9) -ne 'depth-bounded') { throw 'P149_DEPTH_BOUND' }
$array = Safe-Value (1..100)
if ($array.Count -ne 49 -or $array[-1] -ne 'item-bound') { throw 'P149_ITEM_BOUND' }
$object = Safe-Value ([pscustomobject]@{Path='C:\fixture-user\outside.exe';ProcessPath='C:\fixture-user\cargo.exe';Count=7;Message='fixture-sensitive-text'})
if ($object['Path'] -ne 'outside-repository-redacted' -or $object['ProcessPath'] -ne 'cargo.exe' -or $object['Count'] -ne 7 -or $object['Message'] -ne 'string-redacted') { throw 'P149_OBJECT_REDACTION' }
if ((Safe-Value ([timespan]::FromTicks(8212150))).total_milliseconds -ne 821.215) { throw 'P149_TICK_CONVERSION' }
[ordered]@{state='PASS_AST_AND_REDACTION_FIXTURES_NOT_RECORDING_OR_PRODUCT_PROOF';parse_errors=0;
    recording_started=$false;elevated=$false;Defender_settings_changed=$false;raw_output_printed=$false;
    fixture_groups=14;P09_gate='OPEN';product_complete=$false} | ConvertTo-Json -Compress
