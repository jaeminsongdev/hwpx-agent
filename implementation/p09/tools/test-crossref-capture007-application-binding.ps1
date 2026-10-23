[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_SEVEN_MODELS_ONLY'}
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-capture007-application-binding')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function Assert-ApplicationModel007([bool]$Condition) {if (-not $Condition) {throw 'P09_XREF_BIND_CAPTURE_SEVEN_APPLICATION_MODEL_FAILED'}}
function New-ApplicationGraph007 {
    return [pscustomobject]@{returned_application_is_com=$true;collection_bound=$true;document_bound=$true;
        windows_bound=$true;window_bound=$true;window_handle_matches=$true;window_pid_matches=$true;
        single_document=$true;version_matches=$true}
}
Assert-ApplicationModel007 (Test-P09XrefCapture007ApplicationGraph (New-ApplicationGraph007))
[Console]::WriteLine('test capture007_application::all_nine_independent_bindings_required ... ok')
foreach ($name in @('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
    'window_handle_matches','window_pid_matches','single_document','version_matches')) {
    $row=New-ApplicationGraph007;$row.$name=$false
    Assert-ApplicationModel007 (-not (Test-P09XrefCapture007ApplicationGraph $row))
    [Console]::WriteLine(('test capture007_application::reject_false_'+$name+' ... ok'))
}
foreach ($value in @($null,0,1,'True')) {
    $row=New-ApplicationGraph007;$row.window_pid_matches=$value
    Assert-ApplicationModel007 (-not (Test-P09XrefCapture007ApplicationGraph $row))
}
[Console]::WriteLine('test capture007_application::reject_non_boolean_evidence ... ok')
$row=New-ApplicationGraph007;$row|Add-Member NoteProperty unexpected $true
Assert-ApplicationModel007 (-not (Test-P09XrefCapture007ApplicationGraph $row))
$row=New-ApplicationGraph007;$row.PSObject.Properties.Remove('window_bound')
Assert-ApplicationModel007 (-not (Test-P09XrefCapture007ApplicationGraph $row))
Assert-ApplicationModel007 (-not (Test-P09XrefCapture007ApplicationGraph ([object]::new())))
[Console]::WriteLine('test capture007_application::reject_extra_missing_and_plain_schema ... ok')
$pointers=[Collections.Generic.List[IntPtr]]::new();$failed=$false
try {[void](Test-P09XrefCapture007ReturnedApplication ([object]::new()) $null $pointers ([IntPtr]1) ([IntPtr]2))}
catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_SEVEN_RETURNED_APPLICATION_REAL_COM'}
Assert-ApplicationModel007 ($failed -and $pointers.Count -eq 0)
[Console]::WriteLine('test capture007_application::plain_application_rejected_before_getters_or_addref ... ok')
$definition=Get-P09XrefCapture007ApplicationDefinition
Assert-ApplicationModel007 ($definition.changed.Replace($definition.after,$definition.before) -ceq $definition.original)
Assert-ApplicationModel007 ($definition.changed.Contains('document_application_bound=(Test-P09XrefCapture007ReturnedApplication'))
[Console]::WriteLine('test capture007_application::entire_original_observation_preserved_except_binding_predicate ... ok')
Initialize-P09XrefCapture007ApplicationBinding
$actual=Get-Command Read-P09XrefActiveSourceObservation
Assert-ApplicationModel007 ($actual.ScriptBlock.Ast.Extent.Text -ceq $definition.changed)
$failed=$false;try {Initialize-P09XrefCapture007ApplicationBinding} catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_SEVEN_APPLICATION_NO_REINSTALL'}
Assert-ApplicationModel007 $failed
[Console]::WriteLine('test capture007_application::exact_process_local_install_and_no_reinstall ... ok')
$text=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'crossref-capture007-application-binding.ps1'))
Assert-ApplicationModel007 ($text -cnotmatch '(?i)GetActiveObject|GetTypeFromProgID|CreateInstance|-ComObject|\.SaveAs\(|\.Execute\(|\.Quit\(|FinalReleaseComObject|FileAccess\]::Write|FileMode\]::Create')
[Console]::WriteLine('test capture007_application::no_activation_write_action_or_alias_final_release ... ok')
