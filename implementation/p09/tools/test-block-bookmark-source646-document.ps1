# New guard function bodies with fake identities only. No COM/process/file IO.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'MODELS_ONLY_REQUIRED'}
. (Join-Path $PSScriptRoot 'block-bookmark-source645-ports.ps1')
. (Join-Path $PSScriptRoot 'block-bookmark-source646-document.ps1')
$script:run=0;$script:failed=[Collections.Generic.List[string]]::new()
function Assert-Model([bool]$Value) {if (-not $Value) {throw 'MODEL_ASSERTION'}}
function Model([string]$Name,[scriptblock]$Body) {
    $script:run++;try {[void](& $Body)}catch {[void]$script:failed.Add($Name)}
}
function Assert-P09XrefPreassignedOwnerAnchor($Owner) {Assert-Model $Owner.anchor}
function Test-P58Owner($Owner) {
    $script:observations++
    if ($script:observations -eq 2 -and $script:lateOwnerLoss) {return $false}
    return $Owner.live
}
function Get-P09XrefHeldComIdentity($Value,$Pointers) {
    # No fabricated native pointer is added; no real Marshal.Release runs.
    return $Value.model_identity
}
function Release-P09Block645ComReference($Value) {
    [void]$script:released.Add($Value.model_identity)
    if ($script:releaseFails) {throw 'PRIVATE_RELEASE_ERROR_NOT_PRINTED'}
}
function State {
    $script:observations=0;$script:lateOwnerLoss=$false;$script:releaseFails=$false
    $script:released=[Collections.Generic.List[int]]::new()
    $doc=[pscustomobject]@{model_identity=20;FullName=''}
    $collection=[pscustomobject]@{model_identity=10;Count=[int]1;Active_XHwpDocument=$doc}
    return [ordered]@{failed=$false;cleanup_error_code=$null;document=$doc;owner=[ordered]@{
        anchor=$true;live=$true;preassigned_admitted=$true;preassigned_close_attempted=$false;
        documents=$collection;hwp=[pscustomobject]@{XHwpDocuments=$collection;EditMode=[int]1}}}
}
function Denied($State,[string]$Code) {
    $found=$false
    try {Assert-P09Block645CurrentDocument $State} catch {$found=$_.Exception.GetBaseException().Message -ceq $Code}
    Assert-Model $found
}
Model 'exact_live_unsaved_guard_balanced_getters' {
    $s=State;Assert-P09Block645CurrentDocument $s
    Assert-Model (-not $s.failed -and $script:observations -eq 2 -and ($script:released -join ',') -ceq '20,10')
}
Model 'not_admitted' {$s=State;$s.owner.preassigned_admitted=$false;Denied $s 'P09_BLOCK645_CURRENT_ADMITTED_OWNER';Assert-Model ($script:released.Count -eq 0)}
Model 'admission_not_bool' {$s=State;$s.owner.preassigned_admitted=[int]1;Denied $s 'P09_BLOCK645_CURRENT_ADMITTED_OWNER'}
Model 'close_already_attempted' {$s=State;$s.owner.preassigned_close_attempted=$true;Denied $s 'P09_BLOCK645_CURRENT_ADMITTED_OWNER'}
Model 'owner_lost_after_properties' {$s=State;$script:lateOwnerLoss=$true;Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT';Assert-Model ($s.failed -and $script:released.Count -eq 2)}
Model 'wrong_collection_identity' {$s=State;$s.owner.documents=[pscustomobject]@{model_identity=99};Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT';Assert-Model ($script:released.Count -eq 2)}
Model 'wrong_active_document' {$s=State;$s.owner.hwp.XHwpDocuments.Active_XHwpDocument=[pscustomobject]@{model_identity=99};Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'}
Model 'multiple_documents' {$s=State;$s.owner.documents.Count=[int]2;Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'}
Model 'count_not_integer' {$s=State;$s.owner.documents.Count=$true;Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'}
Model 'not_unsaved' {$s=State;$s.document.FullName='D:\MODELED-USER-DOCUMENT';Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'}
Model 'not_edit_mode' {$s=State;$s.owner.hwp.EditMode=[int]0;Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'}
Model 'release_failure_fails_closed' {$s=State;$script:releaseFails=$true;Denied $s 'P09_BLOCK646_DOCUMENT_REFERENCES_UNCONFIRMED';Assert-Model ($s.failed -and $script:released.Count -eq 2)}
Model 'primary_failure_preserved_on_release_fault' {$s=State;$s.owner.documents.Count=[int]2;$script:releaseFails=$true;Denied $s 'P09_BLOCK645_SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT';Assert-Model ($s.failed -and $null -ne $s.cleanup_error_code -and $script:released.Count -eq 2)}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    actual_native_started=$false;real_COM_identity_or_release_qualified=$false}|ConvertTo-Json -Compress
if ($script:failed.Count -ne 0) {exit 2}
