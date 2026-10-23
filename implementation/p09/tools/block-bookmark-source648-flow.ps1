# Fixed new source IO, not a general authoring API or execution permit.
Set-StrictMode -Version Latest
function Get-P09Block648SafeCode($Failure) {
    $code=$Failure.Exception.GetBaseException().Message
    if ($code -cmatch '^(P09_XREF_(BIND|ROT)_|P58_|STOP_)[A-Z0-9_]{1,120}$') {return $code}
    if ($code -cmatch '^P09_BLOCK(645|646)_(?<suffix>[A-Z0-9_]{1,95})$') {return ('P09_XREF_BIND_BLOCK648_PORT_'+$Matches.suffix)}
    return 'P09_XREF_BIND_BLOCK648_FAILURE_NO_RAW_VALUES'
}
function Save-P09Block648Artifact($State,[string]$Name) {
    Assert-P09Block645 ($Name -cin @('created.hwpx','reopened.hwpx')) 'FIXED_SOURCE_OUTPUT'
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    Assert-P09Block645 ((Test-P58Owner $State.owner) -eq $true) 'SOURCE_SAVE_OWNER'
    $path=Join-Path $State.run $Name;Assert-P09XrefExclusiveDestination $path
    $returned=$State.document.SaveAs($path,'HWPX','')
    Assert-P09Block645 ($returned -is [bool] -and $returned) 'SOURCE_SAVE_EFFECT_UNKNOWN'
    $pin=Get-P09Prepared631Pin $path 4194304 ''
    $State.trace.artifacts[$Name]=[ordered]@{pin=$pin;owner=$State.owner.identity;effect_semantics_qualified=$false}
    return $pin
}
function Export-P09Block648Image($State,[string]$Label) {
    Assert-P09Block645 ($Label -cin @('created','reopened')) 'FIXED_SOURCE_IMAGE_LABEL'
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    Assert-P09Block645 ((Test-P58Owner $State.owner) -eq $true -and $State.owner.hwp.PageCount -is [int] -and $State.owner.hwp.PageCount -eq 1) 'SOURCE_IMAGE_SINGLE_PAGE'
    $name=$Label+'-page-001.bmp';$path=Join-Path $State.run $name;Assert-P09XrefExclusiveDestination $path
    $returned=$State.owner.hwp.CreatePageImage($path,0,96,24,'BMP')
    Assert-P09Block645 ($returned -is [bool] -and $returned) 'SOURCE_IMAGE_EFFECT_UNKNOWN'
    $pin=Get-P09Prepared631Pin $path 16777216 ''
    $stream=[IO.File]::OpenRead($path);$head=[byte[]]::new(54)
    try {Assert-P09Block645 ($stream.Read($head,0,54) -eq 54) 'SOURCE_IMAGE_SHORT'} finally {$stream.Dispose()}
    $bitmap=Assert-P09Prepared631Bitmap $head $pin.bytes
    $State.trace.artifacts[$name]=[ordered]@{pin=$pin;owner=$State.owner.identity;bitmap=$bitmap;effect_semantics_qualified=$false}
}
function Invoke-P09Block648Step($State,[string]$Step) {
    $steps=Get-P09Block648Steps
    Assert-P09Block645 (-not $State.failed -and $State.cursor -lt $steps.Count -and $Step -ceq $steps[$State.cursor]) 'STEP_NO_RETRY'
    $State.trace.phase=$Step
    try {
        $d=Invoke-P09Block648Message $State.preassigned_channel checkpoint -Step $Step
        if ($Step -cin @('create_save_session','create_reopen_session')) {
            Assert-P09Block645 ($null -ne $d -and $null -eq $State.current_descriptor) 'SOURCE_DESCRIPTOR'
            $State.current_descriptor=$d
        } else {Assert-P09Block645 ($null -eq $d) 'SOURCE_NO_DESCRIPTOR'}
        switch -CaseSensitive ($Step) {
            'prepare_slot' {
                Assert-P09Block645 (-not(Test-Path -LiteralPath $State.run)) 'SOURCE_ATTEMPT_EXISTS'
                $parent=Get-Item -LiteralPath (Split-Path -Parent $State.run) -Force
                while ($null -ne $parent) {
                    Assert-P09Block645 ($parent -is [IO.DirectoryInfo] -and ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'SOURCE_PARENT'
                    $parent=$parent.Parent
                }
                [void](New-Item -ItemType Directory -Path $State.run);$State.slot_created=$true
            }
            'create_save_session' {$State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State save);Admit-P09XrefPreassignedOwner $State.owner $State}
            'bind_blank_document' {$State.document=$State.owner.documents.Active_XHwpDocument;Assert-P09Block646CurrentDocument $State}
            'seed_document' {Invoke-P09Block645Seed $State}
            'create_bookmarks' {Invoke-P09Block645Ranges $State;Assert-P09Block645 ($State.completed_ranges -eq 8) 'EIGHT_RANGES_REQUIRED'}
            'created_save' {$State.created=Save-P09Block648Artifact $State 'created.hwpx'}
            'created_image' {Observe-P09Prepared631Document $State (Join-Path $State.run 'created.hwpx') $State.created.sha256;Export-P09Block648Image $State created}
            'created_bind' {Observe-P09Prepared631Document $State (Join-Path $State.run 'created.hwpx') $State.created.sha256;Open-P09Prepared631Lease $State (Join-Path $State.run 'created.hwpx') $State.created.sha256}
            'save_ready_close' {Assert-P09Block645 ($State.completed_ranges -eq 8 -and $null -eq $State.cleanup_error_code) 'SOURCE_READY_TO_CLOSE'}
            'save_session_close' {$State.previous_identity=$State.owner.identity;Close-P09Prepared631Owner $State}
            'create_reopen_session' {
                $State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State reopen);Admit-P09XrefPreassignedOwner $State.owner $State
                Assert-P09XrefFreshSessionIdentity $State.previous_identity $State.owner.identity
            }
            'fresh_created_open' {$State.document=Open-P58Document $State.owner (Join-Path $State.run 'created.hwpx') $State.created.sha256;Observe-P09Prepared631Document $State (Join-Path $State.run 'created.hwpx') $State.created.sha256}
            'reopened_save' {$State.reopened=Save-P09Block648Artifact $State 'reopened.hwpx'}
            'reopened_image' {Observe-P09Prepared631Document $State (Join-Path $State.run 'reopened.hwpx') $State.reopened.sha256;Export-P09Block648Image $State reopened}
            'reopen_session_close' {Close-P09Prepared631Owner $State}
            'final_source_check' {
                foreach ($name in $State.trace.artifacts.Keys) {[void](Get-P09Prepared631Pin (Join-Path $State.run $name) 16777216 $State.trace.artifacts[$name].pin.sha256)}
                $State.trace.source_identity_preserved=$true;$State.trace.state='source_capture_returned_semantics_unqualified'
            }
            default {throw 'P09_XREF_BIND_BLOCK648_UNKNOWN_STEP'}
        }
        $State.cursor++
    } catch {$State.failed=$true;throw}
}
