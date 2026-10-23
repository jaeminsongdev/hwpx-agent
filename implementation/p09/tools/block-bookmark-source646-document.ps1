# Private successor guard, loaded after unchanged645 by the future fixed worker.
# No activation, launcher, saved permit or Native authority.
Set-StrictMode -Version Latest

function Assert-P09Block646CurrentDocument($State) {
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    $verified=Test-P58Owner $State.owner
    Assert-P09Block645 ($State.owner.preassigned_admitted -is [bool] -and $State.owner.preassigned_admitted -and
        $State.owner.preassigned_close_attempted -is [bool] -and -not $State.owner.preassigned_close_attempted -and
        $verified -is [bool] -and $verified) 'CURRENT_ADMITTED_OWNER'
    $pointers=[Collections.Generic.List[IntPtr]]::new()
    $references=[Collections.ArrayList]::new()
    try {
        $collection=$State.owner.hwp.XHwpDocuments;[void]$references.Add($collection)
        $active=$collection.Active_XHwpDocument;[void]$references.Insert(0,$active)
        $heldCollection=Get-P09XrefHeldComIdentity $State.owner.documents $pointers
        $currentCollection=Get-P09XrefHeldComIdentity $collection $pointers
        $heldDocument=Get-P09XrefHeldComIdentity $State.document $pointers
        $currentDocument=Get-P09XrefHeldComIdentity $active $pointers
        $count=$collection.Count;$name=$State.document.FullName;$mode=$State.owner.hwp.EditMode
        $verified=Test-P58Owner $State.owner
        Assert-P09Block645 ($heldCollection -eq $currentCollection -and $heldDocument -eq $currentDocument -and
            $count -is [int] -and $count -eq 1 -and $name -is [string] -and $name.Length -eq 0 -and
            $mode -is [int] -and $mode -eq 1 -and $verified -is [bool] -and $verified) 'SAME_SINGLE_UNSAVED_EDITABLE_DOCUMENT'
    } catch {$State.failed=$true;throw}
    finally {
        foreach ($pointer in $pointers) {
            try {[void][Runtime.InteropServices.Marshal]::Release($pointer)}
            catch {$State.cleanup_error_code='P09_BLOCK646_IUNKNOWN_RELEASE_UNCONFIRMED'}
        }
        # Release getter RCW acquisitions as well as GetIUnknown AddRefs. Never
        # FinalRelease aliases of the owner's retained collection/document.
        foreach ($reference in $references) {
            try {Release-P09Block645ComReference $reference}
            catch {$State.cleanup_error_code='P09_BLOCK646_GETTER_RELEASE_UNCONFIRMED'}
        }
        if ($null -ne $State.cleanup_error_code -and -not $State.failed) {
            $State.failed=$true;throw 'P09_BLOCK646_DOCUMENT_REFERENCES_UNCONFIRMED'
        }
    }
}

function Assert-P09Block645CurrentDocument($State) {
    # Only the successor fixed worker imports this explicit override. The
    # unchanged645 source/22 original model records remain historical evidence.
    Assert-P09Block646CurrentDocument $State
}
