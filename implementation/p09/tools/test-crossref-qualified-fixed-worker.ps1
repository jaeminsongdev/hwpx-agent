# New ready-release/source contracts only. Never executes worker/native paths.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_FULL_WORKER_MODELS_ONLY'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-host-channel.ps1')
. (Join-Path $PSScriptRoot 'crossref-preassigned-host-channel.ps1')
$path=Join-Path $PSScriptRoot 'run-crossref-qualified-fixed-worker.ps1'
$source=[IO.File]::ReadAllText($path);$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
$begin=$source.IndexOf("`$phase='current_live_release';",[StringComparison]::Ordinal)
$end=$source.IndexOf("`$phase='fixed_eight';",[StringComparison]::Ordinal)
Assert-P09XrefBinding (@($errors).Count -eq 0 -and $begin -gt 0 -and $end -gt $begin) 'FULL_MODEL_RELEASE_SOURCE_BOUNDARY'
$release=[scriptblock]::Create($source.Substring($begin,$end-$begin))
function New-FullModelRelease {
    return [ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-release/v1';acknowledged=$true;error_code=$null;
        native_execution_authorized=$false;p09_complete=$false}
}
function Invoke-FullModelRelease([string]$Raw) {
    $reader=[IO.StringReader]::new($Raw+"`n");$writer=[IO.StringWriter]::new()
    try {$channel=New-P09XrefPreassignedHostChannel $reader $writer;[void](& $release);return $channel.sequence}
    finally {$reader.Dispose();$writer.Dispose()}
}
function Assert-FullModelRejected([string]$Raw) {
    $caught=$false;try {[void](Invoke-FullModelRelease $Raw)} catch {$caught=$true}
    Assert-P09XrefBinding $caught 'FULL_MODEL_EXPECTED_RELEASE_REJECTION'
}
try {
    $good=New-FullModelRelease;$raw=$good|ConvertTo-Json -Depth 5 -Compress
    Assert-P09XrefBinding ((Invoke-FullModelRelease $raw) -eq 0) 'FULL_MODEL_RELEASE_NOT_CASE_SEQUENCE'
    [Console]::WriteLine('test qualified_fixed_worker::release_does_not_consume_case_sequence ... ok')
    $bad=New-FullModelRelease;$bad.acknowledged=$false;$bad.error_code='XREF_HOST_NOT_CURRENT'
    Assert-FullModelRejected ($bad|ConvertTo-Json -Depth 5 -Compress)
    [Console]::WriteLine('test qualified_fixed_worker::denial_never_enters_cases ... ok')
    Assert-FullModelRejected ($raw.Replace('"native_execution_authorized":false','"native_execution_authorized":true'))
    [Console]::WriteLine('test qualified_fixed_worker::authority_flag_cannot_release ... ok')
    Assert-FullModelRejected ($raw.Replace('"acknowledged":true','"acknowledged":1'))
    [Console]::WriteLine('test qualified_fixed_worker::numeric_boolean_rejected ... ok')
    Assert-FullModelRejected ($raw.Replace('"acknowledged":true','"acknowledged":true,"acknowl\u0065dged":true'))
    [Console]::WriteLine('test qualified_fixed_worker::escaped_duplicate_rejected ... ok')
    $bad=New-FullModelRelease;$bad['subset']=@(1)
    Assert-FullModelRejected ($bad|ConvertTo-Json -Depth 5 -Compress)
    [Console]::WriteLine('test qualified_fixed_worker::subset_or_extra_field_rejected ... ok')
    Assert-FullModelRejected ($raw.Replace('fixed-worker-release/v1','other-release/v1'))
    [Console]::WriteLine('test qualified_fixed_worker::other_protocol_rejected ... ok')
    Assert-P09XrefBinding ($ast.ParamBlock.Parameters.Count -eq 1 -and
        $ast.ParamBlock.Parameters[0].Name.VariablePath.UserPath -ceq 'FixedEightAfterSession') 'FULL_MODEL_FIXED_ONE_MODE'
    [Console]::WriteLine('test qualified_fixed_worker::closed_fixed_eight_parameter ... ok')
    $commands=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst]},$true)|ForEach-Object {$_.GetCommandName()})
    Assert-P09XrefBinding (@($commands|Where-Object {$_ -ceq 'Invoke-P09XrefPreassignedFixedHostBatch'}).Count -eq 1 -and
        @($commands|Where-Object {$_ -cin @('New-P58Owner','Stop-Process','Invoke-Expression')}).Count -eq 0) 'FULL_MODEL_ONLY_FIXED_CONTROLLER_NO_FALLBACK'
    [Console]::WriteLine('test qualified_fixed_worker::only_fixed_controller_no_activation_or_force_kill ... ok')
    $retained=$source.IndexOf('if ($retained -gt 0)',[StringComparison]::Ordinal)
    Assert-P09XrefBinding ($retained -gt $end -and $source.Substring($retained).Contains('[Console]::In.Read()')) 'FULL_MODEL_RETAIN_UNCERTAIN_OWNERS_UNTIL_HOST_EOF'
    [Console]::WriteLine('test qualified_fixed_worker::uncertain_owners_retained_until_host_eof ... ok')
    [Console]::WriteLine('test result: ok. 10 passed; 0 failed; 0 ignored; release_source_models_not_native')
} catch {
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_FULL_WORKER_MODELS_FAILED_NO_RAW_VALUES'}
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
