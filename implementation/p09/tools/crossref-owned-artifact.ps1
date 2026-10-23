# Functions only. No native activation or execution permit. The caller pins all imports.
Set-StrictMode -Version Latest

function Get-P09XrefArtifactScope {
    param([Parameter(Mandatory)][int]$CaseIndex,[Parameter(Mandatory)][string]$Point,
        [Parameter(Mandatory)][string]$ExpectedSha256)
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8 -and
        $ExpectedSha256 -cmatch '^[0-9a-f]{64}$') 'ARTIFACT_SELECTOR'
    $stage=switch -CaseSensitive ($Point) {
        'opened_clean' {'opened'}
        'opened_after_insert' {'opened'}
        'saved_clean' {'saved'}
        'reopened_clean' {'reopened'}
        default {throw 'P09_XREF_BIND_ARTIFACT_POINT'}
    }
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $relative='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c'+
        $CaseIndex.ToString('00')+'-attempt01/'+$stage+'.hwpx'
    return [pscustomobject]@{case_id=('P09-XREF-BOOK-C'+$CaseIndex.ToString('00'));point=$Point;stage=$stage;
        path=(Join-Path $root $relative);sha256=$ExpectedSha256;require_clean=($Point -cne 'opened_after_insert')}
}

function Assert-P09XrefArtifactObservations($Before,$After,$Scope) {
    # Post-insertion observations allow any actual VT_I4 value and do not interpret
    # nonzero as successful mutation. Before action and after saves still require zero.
    $names=@('owner_verified','application_bound','collection_bound','document_bound','document_application_bound',
        'document_count','full_name_matches','modified','version_matches','source_digest_matches')
    foreach ($sample in @($Before,$After)) {
        Assert-P09XrefBinding ($sample -is [pscustomobject] -and @($sample.PSObject.Properties).Count -eq $names.Count) 'ARTIFACT_SAMPLE_SCHEMA'
        foreach ($name in $names) {Assert-P09XrefBinding ($name -cin @($sample.PSObject.Properties.Name)) 'ARTIFACT_SAMPLE_SCHEMA'}
        foreach ($name in @('owner_verified','application_bound','collection_bound','document_bound','document_application_bound',
                'full_name_matches','version_matches','source_digest_matches')) {
            Assert-P09XrefBinding ($sample.$name -is [bool] -and $sample.$name) 'ARTIFACT_SAMPLE_MISMATCH'
        }
        Assert-P09XrefBinding ($sample.document_count -is [int] -and $sample.document_count -eq 1 -and
            $sample.modified -is [int]) 'ARTIFACT_SAMPLE_TYPES'
        if ($Scope.require_clean) {Assert-P09XrefBinding ($sample.modified -eq 0) 'ARTIFACT_MUST_BE_CLEAN'}
    }
    return [ordered]@{state='paired_owned_artifact_observation_not_execution_permit';case_id=$Scope.case_id;point=$Scope.point;
        runtime_com_observed=$false;native_execution_authorized=$false;reusable_execution_permit=$false;
        native_target_resolution_qualified=$false;causal_insertion_or_preservation_proved=$false;p09_complete=$false}
}

function Observe-P09XrefOwnedArtifact {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$Point,[Parameter(Mandatory)][string]$ExpectedSha256)
    $scope=Get-P09XrefArtifactScope $CaseIndex $Point $ExpectedSha256
    $pointers=[Collections.Generic.List[IntPtr]]::new();$stream=$null;$algorithm=$null
    try {
        Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
            [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'ARTIFACT_X86_STA'
        Assert-P09XrefBinding ($null -ne $Owner.hwp -and $null -ne $Owner.documents -and
            [Runtime.InteropServices.Marshal]::IsComObject($Owner.hwp) -and
            [Runtime.InteropServices.Marshal]::IsComObject($Owner.documents) -and
            [Runtime.InteropServices.Marshal]::IsComObject($Document)) 'ARTIFACT_REAL_COM_REQUIRED'
        Assert-P09XrefOriginalOwnerFunction
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'ARTIFACT_INITIAL_OWNER'
        $item=Get-Item -LiteralPath $scope.path -Force
        Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le 4194304) 'ARTIFACT_FILE_BOUNDARY'
        $ancestor=$item
        while ($null -ne $ancestor) {
            Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'ARTIFACT_LINKED'
            if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
        }
        Start-Sleep -Milliseconds 50
        $stream=[IO.File]::Open($scope.path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $algorithm=[Security.Cryptography.SHA256]::Create();$watch=[Diagnostics.Stopwatch]::StartNew()
        $buffer=[byte[]]::new(65536);$count=0L
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -ne 0) {
            $count+=$n;Assert-P09XrefBinding ($count -le 4194304) 'ARTIFACT_READ_LIMIT'
            [void]$algorithm.TransformBlock($buffer,0,$n,$buffer,0)
            $delay=[int][Math]::Ceiling(($count/2097152.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        [void]$algorithm.TransformFinalBlock([byte[]]::new(0),0,0);$watch.Stop()
        $sha=([BitConverter]::ToString($algorithm.Hash)).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($count -eq $item.Length -and $sha -ceq $scope.sha256) 'ARTIFACT_SHA'
        $applicationId=Get-P09XrefHeldComIdentity $Owner.hwp $pointers
        $collectionId=Get-P09XrefHeldComIdentity $Owner.documents $pointers
        $documentId=Get-P09XrefHeldComIdentity $Document $pointers
        $before=Read-P09XrefActiveSourceObservation $Owner $Document $pointers $applicationId $collectionId $documentId $scope.path
        $after=Read-P09XrefActiveSourceObservation $Owner $Document $pointers $applicationId $collectionId $documentId $scope.path
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'ARTIFACT_FINAL_OWNER'
        $receipt=Assert-P09XrefArtifactObservations $before $after $scope
        $receipt.runtime_com_observed=$true
        return $receipt
    } catch {
        $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_ARTIFACT_FAILED_NO_RAW_VALUES'}
        throw $code
    } finally {
        foreach ($pointer in $pointers) {[void][Runtime.InteropServices.Marshal]::Release($pointer)}
        $pointers.Clear()
        if ($null -ne $algorithm) {$algorithm.Dispose()}
        if ($null -ne $stream) {$stream.Dispose()}
    }
}
