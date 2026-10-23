# Function-only native IO adapters. No activation, dispatcher, retry or authority input.
Set-StrictMode -Version Latest

function Get-P09XrefCaseArtifactPath([int]$CaseIndex,[string]$Stage) {
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8 -and $Stage -cin @('opened','saved','reopened')) 'IO_SELECTOR'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    return (Join-Path $root ('implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c'+
        $CaseIndex.ToString('00')+'-attempt01/'+$Stage+'.hwpx'))
}

function Assert-P09XrefOriginalIoFunctions {
    Assert-P09XrefOriginalOwnerFunction
    $source=Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1'
    # The prior owner check already requires the exact whole source SHA. Check
    # the actual live Open/Save function definitions too; do not modify P58.
    $tokens=$null;$errors=$null
    $text=[Text.UTF8Encoding]::new($false,$true).GetString([IO.File]::ReadAllBytes($source))
    $ast=[Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'IO_ORIGINAL_PARSE'
    foreach ($name in @('Open-P58Document','Save-P58Artifact')) {
        $found=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -ceq $name},$false))
        $actual=Get-Command $name -CommandType Function -ErrorAction Stop
        Assert-P09XrefBinding ($found.Count -eq 1 -and $actual.ScriptBlock.Ast -is
            [Management.Automation.Language.FunctionDefinitionAst] -and
            $actual.ScriptBlock.Ast.Extent.Text -ceq $found[0].Extent.Text) 'IO_ORIGINAL_FUNCTION_REPLACED'
    }
}

function Assert-P09XrefRealIoObjects($Owner,$Document,[bool]$RequireDocument) {
    Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
        [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'IO_X86_STA'
    Assert-P09XrefBinding ($null -ne $Owner.hwp -and $null -ne $Owner.documents -and
        [Runtime.InteropServices.Marshal]::IsComObject($Owner.hwp) -and
        [Runtime.InteropServices.Marshal]::IsComObject($Owner.documents)) 'IO_REAL_OWNER_REQUIRED'
    if ($RequireDocument) {Assert-P09XrefBinding ([Runtime.InteropServices.Marshal]::IsComObject($Document)) 'IO_REAL_DOCUMENT_REQUIRED'}
    Assert-P09XrefOriginalIoFunctions
}

function Assert-P09XrefFreshSessionIdentity($Previous,$Current) {
    foreach ($identity in @($Previous,$Current)) {
        Assert-P09XrefBinding ($identity.process_id -is [int] -and $identity.process_id -gt 0 -and
            $identity.session_id -is [int] -and $identity.session_id -ge 0 -and
            $identity.executable_sha256 -ceq '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce' -and
            $identity.window_handle_binds_exact_process -is [bool] -and $identity.window_handle_binds_exact_process -and
            $identity.created_at_utc -is [string]) 'IO_SESSION_IDENTITY'
    }
    $old=[datetime]::MinValue;$fresh=[datetime]::MinValue
    $culture=[Globalization.CultureInfo]::InvariantCulture;$style=[Globalization.DateTimeStyles]::RoundtripKind
    Assert-P09XrefBinding ([datetime]::TryParseExact($Previous.created_at_utc,'o',$culture,$style,[ref]$old) -and
        [datetime]::TryParseExact($Current.created_at_utc,'o',$culture,$style,[ref]$fresh) -and
        $old.Kind -eq [DateTimeKind]::Utc -and $fresh.Kind -eq [DateTimeKind]::Utc -and $fresh -gt $old -and
        $Current.session_id -eq $Previous.session_id) 'IO_FRESH_SESSION_REQUIRED'
    # PID reuse with a strictly later creation identity is not confused with old ownership.
}

function Assert-P09XrefExclusiveDestination([string]$Path) {
    Assert-P09XrefBinding (-not (Test-Path -LiteralPath $Path)) 'IO_OUTPUT_EXISTS'
    $parent=Get-Item -LiteralPath (Split-Path -Parent $Path) -Force
    while ($null -ne $parent) {
        Assert-P09XrefBinding ($parent -is [IO.DirectoryInfo] -and
            ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'IO_OUTPUT_PARENT'
        $parent=$parent.Parent
    }
    # This check is not an OS create-new SaveAs guarantee; filesystem races remain unqualified.
}

function Set-P09XrefIndirectIoRecord {
    param([Parameter(Mandatory)][System.Collections.IDictionary]$Record,
        [ValidateSet('save','open')][string]$Operation,[ValidateSet('enter','returned')][string]$Transition)
    $key=$Operation+'_invoked'
    if ($Transition -ceq 'enter') {
        $Record[$key]=$null # The unchanged helper can reject before its native method call.
        $Record.effect_unknown=$true;$Record.helper_operation=$Operation
        $Record.helper_invocation_started=$true;$Record.helper_returned=$false
    } else {
        Assert-P09XrefBinding ($Record['helper_operation'] -ceq $Operation -and
            $Record['helper_invocation_started'] -eq $true -and $Record['helper_returned'] -eq $false -and
            $null -eq $Record[$key]) 'IO_HELPER_RETURN_ORDER'
        $Record[$key]=$true;$Record.helper_returned=$true
    }
}

function Save-P09XrefOpenedArtifact {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    $Record.phase='opened_source_binding';$Record.save_invoked=$false;$Record.effect_unknown=$false;$Record.error_code=$null
    try {
        $path=Get-P09XrefCaseArtifactPath $CaseIndex 'opened'
        Assert-P09XrefRealIoObjects $Owner $Document $true
        [void](Observe-P09XrefOwnedActiveSource $Owner $Document)
        Assert-P09XrefExclusiveDestination $path
        $Record.phase='opened_save';$Record.save_invoked=$true;$Record.effect_unknown=$true
        $saved=$Document.SaveAs($path,'HWPX','')
        Assert-P09XrefBinding ($saved -is [bool] -and $saved) 'IO_OPENED_SAVE_FAILED_EFFECT_UNKNOWN'
        $pin=Assert-P58File $path 4194304
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'opened_clean' $pin.sha256)
        $Record.phase='opened_artifact_observed';$Record.artifact=$pin
        return $pin
    } catch {
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_BIND|P58)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_IO_OPENED_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code;throw $code
    }
}

function Save-P09XrefPostInsertArtifact {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$OpenedSha256,[Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    $Record.phase='post_insert_binding';$Record.save_invoked=$false;$Record.effect_unknown=$false;$Record.error_code=$null
    try {
        $path=Get-P09XrefCaseArtifactPath $CaseIndex 'saved'
        Assert-P09XrefRealIoObjects $Owner $Document $true
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'opened_after_insert' $OpenedSha256)
        Assert-P09XrefExclusiveDestination $path
        $run=Split-Path -Parent $path # Dynamic caller scope required by the unchanged P58 function.
        $Record.phase='saved_save';Set-P09XrefIndirectIoRecord $Record 'save' 'enter'
        $pin=Save-P58Artifact $Owner $Document 'saved.hwpx' 'HWPX'
        Set-P09XrefIndirectIoRecord $Record 'save' 'returned'
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'saved_clean' $pin.sha256)
        $Record.phase='saved_artifact_observed';$Record.artifact=$pin
        return $pin
    } catch {
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_BIND|P58)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_IO_SAVED_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code;throw $code
    }
}

function Open-P09XrefSavedInFreshSession {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$PreviousIdentity,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$SavedSha256,[Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    $Record.phase='fresh_session_binding';$Record.open_invoked=$false;$Record.effect_unknown=$false;$Record.error_code=$null
    $document=$null;$handedOff=$false
    try {
        $scope=Get-P09XrefArtifactScope $CaseIndex 'saved_clean' $SavedSha256
        Assert-P09XrefRealIoObjects $Owner $null $false
        Assert-P09XrefFreshSessionIdentity $PreviousIdentity $Owner.identity
        $Record.phase='fresh_saved_open';Set-P09XrefIndirectIoRecord $Record 'open' 'enter'
        $document=Open-P58Document $Owner $scope.path $SavedSha256
        Set-P09XrefIndirectIoRecord $Record 'open' 'returned'
        [void](Observe-P09XrefOwnedArtifact $Owner $document $CaseIndex 'saved_clean' $SavedSha256)
        $Record.phase='fresh_saved_document_observed';$handedOff=$true
        return $document
    } catch {
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_BIND|P58)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_IO_REOPEN_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code;throw $code
    } finally {
        if (-not $handedOff -and $null -ne $document) {Release-P58Com $document}
        # Caller still owns the session and must record/perform its verified cleanup.
    }
}

function Save-P09XrefReopenedArtifact {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$SavedSha256,[Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    $Record.phase='reopened_input_binding';$Record.save_invoked=$false;$Record.effect_unknown=$false;$Record.error_code=$null
    try {
        $path=Get-P09XrefCaseArtifactPath $CaseIndex 'reopened'
        Assert-P09XrefRealIoObjects $Owner $Document $true
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'saved_clean' $SavedSha256)
        Assert-P09XrefExclusiveDestination $path
        $run=Split-Path -Parent $path
        $Record.phase='reopened_save';Set-P09XrefIndirectIoRecord $Record 'save' 'enter'
        $pin=Save-P58Artifact $Owner $Document 'reopened.hwpx' 'HWPX'
        Set-P09XrefIndirectIoRecord $Record 'save' 'returned'
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'reopened_clean' $pin.sha256)
        $Record.phase='reopened_artifact_observed';$Record.artifact=$pin
        return $pin
    } catch {
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_BIND|P58)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_IO_REOPENED_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code;throw $code
    }
}
