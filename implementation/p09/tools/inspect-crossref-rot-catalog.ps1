# Fixed read-only ROT-name inventory. Does not get any running object or touch Hancom/documents.
[CmdletBinding()]
param([switch]$ModelsAndCatalogOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if(-not $ModelsAndCatalogOnly -or [IntPtr]::Size -ne 4 -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA'){throw 'P09_XREF_ROT_INSPECTION_CLOSED_MODE'}
$phase='compile'
try{
    Add-Type -Path @((Join-Path $PSScriptRoot 'crossref-existing-owner.cs'),(Join-Path $PSScriptRoot 'crossref-rot-catalog-inspection.cs'))
    $phase='models';$names=@('empty','names_only','exact_limit','overflow','incomplete','invalid_name','null_name','release_failure')
    foreach($name in $names){[P09CrossrefExisting.CatalogReadbackModels]::Run($name);[Console]::WriteLine(('test rot_catalog::{0} ... ok' -f $name))}
    $phase='catalog_names';$row=[P09CrossrefExisting.CatalogReadback]::InspectCurrentCatalogOnly()
    [ordered]@{schema_version='hwpx-agent.crossref-rot-name-observation/v1';state='OBSERVED_CURRENT_ROT_NAMES_NOT_OWNER_OR_SESSION';
        entries=[int]$row.Entries;candidate_names=[int]$row.CandidateNames;other_names=[int]$row.OtherNames;
        enumeration_complete=[bool]$row.EnumerationComplete;catalog_released=[bool]$row.CatalogReleased;
        names_or_document_values_exported=$false;GetObject_or_activation_invoked=$false;Hancom_started_or_closed=$false;
        document_or_permission_action_invoked=$false;native_startup_qualified=$false} | ConvertTo-Json -Compress
}catch{
    $exception=$_.Exception.GetBaseException();$code=[string]$exception.Message
    if($code -cnotmatch '^P09_XREF_ROT_[A-Z_]{1,120}$'){$code='P09_XREF_ROT_INSPECTION_FAILURE_NO_RAW_VALUES'}
    $hr=[BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$exception.HResult),0).ToString('X8')
    [ordered]@{state='FAILED_CURRENT_ROT_NAME_OBSERVATION';phase=$phase;error_code=$code;HRESULT=$hr;
        GetObject_or_activation_invoked=$false;Hancom_started_or_closed=$false;document_or_permission_action_invoked=$false} | ConvertTo-Json -Compress
    exit 2
}
