# Extract only the pure diagnostic function. Never dot-source the actual worker.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_DIAGNOSTICS_MODELS_ONLY'}
function Assert-Diagnostic($Condition,[string]$Code) {if (-not $Condition) {throw ('P09_XREF_BIND_DIAGNOSTICS_'+$Code)}}
$source=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'run-crossref-session-qualification-worker.ps1'))
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
Assert-Diagnostic (@($errors).Count -eq 0) 'WORKER_SYNTAX'
[Console]::WriteLine('test failure_diagnostics::worker_syntax ... ok')
$functions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Get-P09XrefSessionFailure'},$true))
Assert-Diagnostic ($functions.Count -eq 1) 'ONE_PURE_FUNCTION'
. ([scriptblock]::Create($functions[0].Extent.Text))
[Console]::WriteLine('test failure_diagnostics::pure_function_extracted_not_worker ... ok')
$value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=[InvalidOperationException]::new('P09_XREF_ROT_NO_MATCH')})
Assert-Diagnostic ($value.error_code -ceq 'P09_XREF_ROT_NO_MATCH' -and $value.error_kind -ceq 'InvalidOperationException') 'ROT_PRESERVED'
[Console]::WriteLine('test failure_diagnostics::rot_code_preserved ... ok')
$value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=[InvalidOperationException]::new('P09_XREF_BIND_EXACT_OWNER')})
Assert-Diagnostic ($value.error_code -ceq 'P09_XREF_BIND_EXACT_OWNER') 'BIND_PRESERVED'
[Console]::WriteLine('test failure_diagnostics::bind_code_preserved ... ok')
$exception=[Runtime.InteropServices.COMException]::new('PRIVATE_COM_MESSAGE',-2147221021)
$value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=$exception})
Assert-Diagnostic ($value.error_hresult -ceq '0x800401E3' -and $value.error_kind -ceq 'COMException') 'COM_NUMERIC_ONLY'
Assert-Diagnostic (($value|ConvertTo-Json -Compress) -cnotmatch 'PRIVATE_COM_MESSAGE') 'COM_MESSAGE_REDACTED'
[Console]::WriteLine('test failure_diagnostics::com_hresult_without_message ... ok')
$value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=[Exception]::new('private@example.invalid')})
Assert-Diagnostic ($value.error_code -ceq 'P09_XREF_BIND_SESSION_WORKER_FAILED_NO_RAW_VALUES' -and $value.error_kind -ceq 'OtherException') 'RAW_REDACTED'
[Console]::WriteLine('test failure_diagnostics::arbitrary_values_redacted ... ok')
foreach ($message in @('P09_XREF_ROT_'+('X'*121),"P09_XREF_ROT_NO_MATCH`nPRIVATE",'P09_XREF_ROT_lowercase')) {
    $value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=[Exception]::new($message)})
    Assert-Diagnostic ($value.error_code -ceq 'P09_XREF_BIND_SESSION_WORKER_FAILED_NO_RAW_VALUES') 'MALFORMED_REDACTED'
}
[Console]::WriteLine('test failure_diagnostics::bounded_code_shape ... ok')
$wrapped=[Exception]::new('PRIVATE_WRAPPER',[InvalidOperationException]::new('P09_XREF_ROT_EXACT_OWNER'))
$value=Get-P09XrefSessionFailure ([pscustomobject]@{Exception=$wrapped})
Assert-Diagnostic ($value.error_code -ceq 'P09_XREF_ROT_EXACT_OWNER' -and ($value|ConvertTo-Json -Compress) -cnotmatch 'PRIVATE_WRAPPER') 'BASE_EXCEPTION_ONLY'
[Console]::WriteLine('test failure_diagnostics::wrapped_base_code_preserved ... ok')
$commands=@($functions[0].FindAll({param($n) $n -is [Management.Automation.Language.CommandAst]},$true))
Assert-Diagnostic ($commands.Count -eq 0) 'NO_NATIVE_COMMANDS'
[Console]::WriteLine('test failure_diagnostics::no_native_or_process_commands ... ok')
Assert-Diagnostic ($source.Contains('$result=Get-P09XrefSessionFailure $_') -and $source.Contains("`$result['native_execution_authorized']=`$false") -and
    $source.Contains("`$result['fixed_eight_executed']=`$false")) 'REAL_CATCH_AND_AUTHORITY_BOUNDARY'
[Console]::WriteLine('test failure_diagnostics::actual_catch_no_authority ... ok')
[Console]::WriteLine('10 passed; 0 failed; 0 ignored; diagnostics_models_not_native')
