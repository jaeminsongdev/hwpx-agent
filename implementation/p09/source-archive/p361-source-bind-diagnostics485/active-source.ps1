# Internal read-only observation, not an execution permit or native target qualifier.
# Caller pins this file and the original P58 ownership source before importing functions.
Set-StrictMode -Version Latest

function Assert-P09XrefBinding([bool]$Condition,[string]$Code) {
    if (-not $Condition) {throw ('P09_XREF_BIND_'+$Code)}
}

function Assert-P09XrefOriginalOwnerFunction {
    $source=Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1'
    $item=Get-Item -LiteralPath $source -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -le 32768 -and
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'OWNER_SOURCE_BOUNDARY'
    $bytes=[IO.File]::ReadAllBytes($source)
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try {$sha=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$algorithm.Dispose()}
    Assert-P09XrefBinding ($sha -ceq 'bd908d7d8f57513df7992e75f3e7faddaa81ce71d6dc0ad8c0b65963124a6338') 'OWNER_SOURCE_IDENTITY'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput([Text.UTF8Encoding]::new($false,$true).GetString($bytes),[ref]$tokens,[ref]$errors)
    $functions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -ceq 'Test-P58Owner'},$false))
    $actual=Get-Command -Name Test-P58Owner -CommandType Function -ErrorAction Stop
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $functions.Count -eq 1 -and
        $actual.ScriptBlock.Ast -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $actual.ScriptBlock.Ast.Extent.Text -ceq $functions[0].Extent.Text) 'OWNER_FUNCTION_REPLACED'
}

function Assert-P09XrefActiveSourceObservations($Before,$After) {
    # These objects are observations, never caller-authorized native capabilities.
    $names=@('owner_verified','application_bound','collection_bound','document_bound','document_application_bound',
        'document_count','full_name_matches','modified','version_matches','source_digest_matches')
    foreach ($observation in @($Before,$After)) {
        Assert-P09XrefBinding ($observation -is [pscustomobject] -and
            @($observation.PSObject.Properties).Count -eq $names.Count) 'OBSERVATION_SCHEMA'
        foreach ($name in $names) {Assert-P09XrefBinding ($name -cin @($observation.PSObject.Properties.Name)) 'OBSERVATION_SCHEMA'}
        foreach ($name in @('owner_verified','application_bound','collection_bound','document_bound','document_application_bound',
                'full_name_matches','version_matches','source_digest_matches')) {
            Assert-P09XrefBinding ($observation.$name -is [bool] -and $observation.$name) 'OBSERVATION_MISMATCH'
        }
        Assert-P09XrefBinding ($observation.document_count -is [int] -and $observation.document_count -eq 1) 'SINGLE_DOCUMENT_REQUIRED'
        # Actual installed declaration is VT_I4, not VARIANT_BOOL. Zero is the conservative
        # admission value; behavior on an actually opened source is still NOT_RUN.
        Assert-P09XrefBinding ($observation.modified -is [int] -and $observation.modified -eq 0) 'CLEAN_LONG_REQUIRED'
    }
    return [ordered]@{state='paired_owned_active_source_observations_not_target_qualification';
        paired_observations_validated=$true;runtime_com_observed=$false;native_target_qualified=$false;
        insertion_or_preservation_proved=$false;native_execution_authorized=$false;reusable_execution_permit=$false;
        raw_document_values_or_identities_present=$false;p09_complete=$false}
}

function Get-P09XrefHeldComIdentity($Value,$Pointers) {
    Assert-P09XrefBinding ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) 'REAL_COM_REQUIRED'
    Assert-P09XrefBinding ($Pointers.Count -lt 64) 'IDENTITY_BUDGET'
    $pointer=[Runtime.InteropServices.Marshal]::GetIUnknownForObject($Value)
    Assert-P09XrefBinding ($pointer -ne [IntPtr]::Zero) 'NULL_IDENTITY'
    try {[void]$Pointers.Add($pointer)}
    catch {
        # If retaining the newly acquired AddRef fails, it never enters the outer
        # cleanup ledger. Release that one reference here; keep earlier entries.
        [void][Runtime.InteropServices.Marshal]::Release($pointer)
        throw
    }
    return $pointer
}

function Read-P09XrefActiveSourceObservation($Owner,$Document,$Pointers,$ApplicationId,$CollectionId,$DocumentId,[string]$ExpectedPath) {
    Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'OWNER_CHANGED'
    $collection=$Owner.hwp.XHwpDocuments
    $active=$collection.Active_XHwpDocument
    $application=$Owner.hwp.Application
    $documentApplication=$Document.Application
    $count=$collection.Count;$modified=$Document.Modified;$name=$Document.FullName;$activeName=$active.FullName
    $version=$Owner.hwp.Version
    return [pscustomobject]@{
        owner_verified=$true
        application_bound=((Get-P09XrefHeldComIdentity $application $Pointers) -eq $ApplicationId)
        collection_bound=((Get-P09XrefHeldComIdentity $collection $Pointers) -eq $CollectionId)
        document_bound=((Get-P09XrefHeldComIdentity $active $Pointers) -eq $DocumentId)
        document_application_bound=((Get-P09XrefHeldComIdentity $documentApplication $Pointers) -eq $ApplicationId)
        document_count=$count
        full_name_matches=($name -is [string] -and $activeName -is [string] -and
            [string]::Equals($name,$ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -and
            [string]::Equals($activeName,$ExpectedPath,[StringComparison]::OrdinalIgnoreCase))
        modified=$modified
        version_matches=($version -is [string] -and $version.Replace(',','.').Replace(' ','') -ceq '11.0.0.9136')
        source_digest_matches=$true # Only reached with the exact source stream held by the outer function.
    }
    # Getter RCW aliases belong to the owning session. Do not FinalRelease them:
    # aliases can be the caller's document/application. Only our IUnknown AddRefs are released.
}

function Observe-P09XrefOwnedActiveSource {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document)
    $pointers=[Collections.Generic.List[IntPtr]]::new();$stream=$null;$algorithm=$null
    try {
        # No activation, fallback to mocks, alternate target, supplied path or source digest.
        Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
            [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'X86_STA_REQUIRED'
        Assert-P09XrefBinding ($null -ne $Owner.hwp -and $null -ne $Owner.documents -and
            [Runtime.InteropServices.Marshal]::IsComObject($Owner.hwp) -and
            [Runtime.InteropServices.Marshal]::IsComObject($Owner.documents) -and
            [Runtime.InteropServices.Marshal]::IsComObject($Document)) 'REAL_OWNED_COM_REQUIRED'
        Assert-P09XrefOriginalOwnerFunction
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'INITIAL_OWNER_MISMATCH'
        $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
        $path=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx'
        $item=Get-Item -LiteralPath $path -Force
        Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq 14425) 'FIXED_SOURCE_SIZE'
        $ancestor=$item
        while ($null -ne $ancestor) {
            Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'SOURCE_LINKED'
            if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
        }
        Start-Sleep -Milliseconds 50
        $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        Assert-P09XrefBinding ($stream.Length -eq 14425) 'OPENED_SOURCE_SIZE'
        $algorithm=[Security.Cryptography.SHA256]::Create()
        $sourceSha=([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($sourceSha -ceq '64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184') 'FIXED_SOURCE_DIGEST'
        # Keep source bytes and all acquired IUnknown identities alive across both samples.
        $applicationId=Get-P09XrefHeldComIdentity $Owner.hwp $pointers
        $collectionId=Get-P09XrefHeldComIdentity $Owner.documents $pointers
        $documentId=Get-P09XrefHeldComIdentity $Document $pointers
        $before=Read-P09XrefActiveSourceObservation $Owner $Document $pointers $applicationId $collectionId $documentId $path
        $after=Read-P09XrefActiveSourceObservation $Owner $Document $pointers $applicationId $collectionId $documentId $path
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'FINAL_OWNER_MISMATCH'
        $receipt=Assert-P09XrefActiveSourceObservations $before $after
        $receipt.runtime_com_observed=$true
        return $receipt
    } catch {
        $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_OBSERVATION_FAILED_NO_RAW_VALUES'}
        throw $code
    } finally {
        # One Release per successful GetIUnknownForObject, including any failing snapshot.
        foreach ($pointer in $pointers) {[void][Runtime.InteropServices.Marshal]::Release($pointer)}
        $pointers.Clear()
        if ($null -ne $algorithm) {$algorithm.Dispose()}
        if ($null -ne $stream) {$stream.Dispose()}
    }
}
