[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_EIGHT_MODELS_ONLY'}
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-capture008-application-binding')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function Assert-ApplicationModel008([bool]$Condition) {if (-not $Condition) {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_MODEL_FAILED'}}
function New-ApplicationGraph008 {
    return [pscustomobject]@{returned_application_is_com=$true;collection_bound=$true;document_bound=$true;
        windows_bound=$true;window_bound=$true;window_handle_matches=$true;window_pid_matches=$true;
        single_document=$true;version_matches=$true}
}
Assert-ApplicationModel008 (Test-P09XrefCapture008ApplicationGraph (New-ApplicationGraph008))
[Console]::WriteLine('test capture008_application::all_nine_independent_bindings_required ... ok')
foreach ($name in @('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
    'window_handle_matches','window_pid_matches','single_document','version_matches')) {
    $row=New-ApplicationGraph008;$row.$name=$false
    Assert-ApplicationModel008 (-not (Test-P09XrefCapture008ApplicationGraph $row))
    [Console]::WriteLine(('test capture008_application::reject_false_'+$name+' ... ok'))
}
foreach ($value in @($null,0,1,'True')) {
    $row=New-ApplicationGraph008;$row.window_pid_matches=$value
    Assert-ApplicationModel008 (-not (Test-P09XrefCapture008ApplicationGraph $row))
}
[Console]::WriteLine('test capture008_application::reject_non_boolean_evidence ... ok')
$row=New-ApplicationGraph008;$row|Add-Member NoteProperty unexpected $true
Assert-ApplicationModel008 (-not (Test-P09XrefCapture008ApplicationGraph $row))
$row=New-ApplicationGraph008;$row.PSObject.Properties.Remove('window_bound')
Assert-ApplicationModel008 (-not (Test-P09XrefCapture008ApplicationGraph $row))
Assert-ApplicationModel008 (-not (Test-P09XrefCapture008ApplicationGraph ([object]::new())))
[Console]::WriteLine('test capture008_application::reject_extra_missing_and_plain_schema ... ok')
$pointers=[Collections.Generic.List[IntPtr]]::new();$failed=$false
try {[void](Test-P09XrefCapture008ReturnedApplication ([object]::new()) $null $pointers ([IntPtr]1) ([IntPtr]2))}
catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_EIGHT_RETURNED_APPLICATION_REAL_COM'}
Assert-ApplicationModel008 ($failed -and $pointers.Count -eq 0)
[Console]::WriteLine('test capture008_application::plain_application_rejected_before_getters_or_addref ... ok')
$definition=Get-P09XrefCapture008ApplicationDefinition
Assert-ApplicationModel008 ($definition.changed.Replace($definition.after,$definition.before) -ceq $definition.original)
Assert-ApplicationModel008 ($definition.changed.Contains('document_application_bound=(Test-P09XrefCapture008ReturnedApplication'))
[Console]::WriteLine('test capture008_application::entire_original_observation_preserved_except_binding_predicate ... ok')
Initialize-P09XrefCapture008ApplicationBinding
$actual=Get-Command Read-P09XrefActiveSourceObservation
Assert-ApplicationModel008 ($actual.ScriptBlock.Ast.Extent.Text -ceq $definition.changed)
$failed=$false;try {Initialize-P09XrefCapture008ApplicationBinding} catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_NO_REINSTALL'}
Assert-ApplicationModel008 $failed
[Console]::WriteLine('test capture008_application::exact_process_local_install_and_no_reinstall ... ok')
$text=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'crossref-capture008-application-binding.ps1'))
Assert-ApplicationModel008 ($text -cnotmatch '(?i)GetActiveObject|GetTypeFromProgID|CreateInstance|-ComObject|\.SaveAs\(|\.Execute\(|\.Quit\(|FinalReleaseComObject|FileAccess\]::Write|FileMode\]::Create')
[Console]::WriteLine('test capture008_application::no_activation_write_action_or_alias_final_release ... ok')

Assert-ApplicationModel008 ($text.Contains('$windows=$Owner.hwp.XHwpWindows') -and
    $text.Contains('$version=$Owner.hwp.Version') -and -not $text.Contains('$windows=$Application.XHwpWindows') -and
    -not $text.Contains('$version=$Application.Version'))
[Console]::WriteLine('test capture008_application::window_and_version_getters_require_owned_root_not_returned_full_api ... ok')
Assert-ApplicationModel008 ($text.IndexOf("Assert-P09XrefBinding "+'$collectionBound') -lt $text.IndexOf('$windows=$Owner.hwp.XHwpWindows') -and
    $text.IndexOf("Assert-P09XrefBinding "+'$documentBound') -lt $text.IndexOf('$windows=$Owner.hwp.XHwpWindows'))
[Console]::WriteLine('test capture008_application::exact_collection_and_document_reject_before_root_window_reads ... ok')
Assert-ApplicationModel008 ($text.Contains('$Owner.windows $Pointers') -and $text.Contains('$Owner.window $Pointers') -and
    $text.Contains('[P58OwnedWindowProcess]::ProcessId($hwnd) -eq $Owner.identity.process_id') -and
    $text.Contains('$count -is [int] -and $count -eq 1'))
[Console]::WriteLine('test capture008_application::owner_window_pid_and_single_document_requirements_remain_mandatory ... ok')
