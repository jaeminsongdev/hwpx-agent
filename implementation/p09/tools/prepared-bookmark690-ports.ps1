# Fixed prepared-file IO. No SDK insert, REF-036 refresh, arbitrary action/path or retry.
Set-StrictMode -Version Latest
function Get-P09Prepared690SafeCode($Failure) {
    $code=$Failure.Exception.GetBaseException().Message
    if ($code -cmatch '^(P09_XREF_(BIND|ROT)_|P58_|STOP_)[A-Z0-9_]{1,120}$') {return $code}
    return 'P09_XREF_BIND_PREPARED_FAILED_NO_RAW_VALUES'
}
function Get-P09Prepared690Pin([string]$Path,[int]$Maximum,[string]$Expected) {
    $item=Get-Item -LiteralPath $Path -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le $Maximum) 'PREPARED_FILE_LIMIT'
    $ancestor=$item
    while ($null -ne $ancestor) {
        Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREPARED_FILE_LINK'
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    Start-Sleep -Milliseconds 50
    $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $hash=[Security.Cryptography.SHA256]::Create();$watch=[Diagnostics.Stopwatch]::StartNew()
    try {
        $buffer=[byte[]]::new(65536);$count=0L
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -gt 0) {
            $count+=$n;Assert-P09XrefBinding ($count -le $Maximum) 'PREPARED_FILE_READ_LIMIT'
            [void]$hash.TransformBlock($buffer,0,$n,$buffer,0)
            $delay=[int][Math]::Ceiling(($count/2097152.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        [void]$hash.TransformFinalBlock([byte[]]::new(0),0,0)
        $sha=([BitConverter]::ToString($hash.Hash)).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($count -eq $item.Length -and ($Expected -ceq '' -or $sha -ceq $Expected)) 'PREPARED_FILE_DIGEST'
        return [ordered]@{bytes=$count;sha256=$sha}
    } finally {$hash.Dispose();$watch.Stop();$stream.Dispose()}
}
function Open-P09Prepared690Lease($State,[string]$Path,[string]$Sha) {
    [void](Get-P09Prepared690Pin $Path 4194304 $Sha)
    $lease=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    [void]$State.leases.Add($lease)
    [void](Get-P09Prepared690Pin $Path 4194304 $Sha)
}
function Observe-P09Prepared690Document($State,[string]$Path,[string]$Sha) {
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    $pointers=[Collections.Generic.List[IntPtr]]::new()
    try {
        Open-P09Prepared690Lease $State $Path $Sha
        $app=Get-P09XrefHeldComIdentity $State.owner.hwp $pointers
        $collection=Get-P09XrefHeldComIdentity $State.owner.documents $pointers
        $document=Get-P09XrefHeldComIdentity $State.document $pointers
        $before=Read-P09XrefActiveSourceObservation $State.owner $State.document $pointers $app $collection $document $Path
        $after=Read-P09XrefActiveSourceObservation $State.owner $State.document $pointers $app $collection $document $Path
        Assert-P09XrefBinding ((Test-P58Owner $State.owner) -eq $true) 'PREPARED_DOCUMENT_FINAL_OWNER'
        [void](Assert-P09XrefActiveSourceObservations $before $after)
    } finally {foreach ($pointer in $pointers) {[void][Runtime.InteropServices.Marshal]::Release($pointer)}}
}
function Close-P09Prepared690Owner($State) {
    if ($null -eq $State.owner) {return}
    Assert-P09XrefBinding (-not $State.close_attempted) 'PREPARED_NO_CLOSE_RETRY'
    $State.close_attempted=$true;$owner=$State.owner
    try {
        if ($null -ne $State.document) {try {Release-P58Com $State.document} finally {$State.document=$null}}
    } finally {
        try {Close-P09XrefPreassignedOwner $owner}
        finally {if ($owner.preassigned_closed) {$State.owner=$null}}
    }
}
function Save-P09Prepared690Artifact($State,[string]$Name,[string]$Format) {
    Assert-P09XrefBinding (($Name -cin @('initial.hwpx','saved.hwpx','reopened.hwpx') -and $Format -ceq 'HWPX')) 'PREPARED_EXACT_OUTPUT_FORMAT'
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    Assert-P09XrefBinding ((Test-P58Owner $State.owner) -eq $true) 'PREPARED_SAVE_OWNER'
    $path=Join-Path $State.run $Name
    Assert-P09XrefExclusiveDestination $path
    # Bound to the exact admitted COM document. Never save over a candidate/source.
    $returned=$State.document.SaveAs($path,$Format,'')
    Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'PREPARED_SAVE_FAILED_EFFECT_UNKNOWN'
    $maximum=4194304
    $pin=Get-P09Prepared690Pin $path $maximum ''
    $State.trace.artifacts[$Name]=[ordered]@{pin=$pin;owner=$State.owner.identity;effect_semantics_qualified=$false}
    return $pin
}
function Assert-P09Prepared690Bitmap([byte[]]$Head,[long]$Bytes) {
    Assert-P09XrefBinding ($Head.Length -eq 54 -and $Head[0] -eq 66 -and $Head[1] -eq 77 -and
        [BitConverter]::ToUInt32($Head,2) -eq $Bytes -and [BitConverter]::ToUInt32($Head,14) -ge 40) 'PREPARED_BMP_HEADER'
    $width=[BitConverter]::ToInt32($Head,18);$height=[BitConverter]::ToInt32($Head,22)
    $offset=[BitConverter]::ToUInt32($Head,10)
    Assert-P09XrefBinding ($width -gt 0 -and $width -le 4096 -and $height -ne 0 -and
        [Math]::Abs([long]$height) -le 4096 -and [BitConverter]::ToUInt16($Head,26) -eq 1 -and
        [BitConverter]::ToUInt16($Head,28) -eq 24 -and [BitConverter]::ToUInt32($Head,30) -eq 0 -and
        $offset -ge 54 -and $offset -lt $Bytes) 'PREPARED_BMP_LAYOUT'
    $stride=([long][Math]::Floor(($width*24+31)/32))*4
    Assert-P09XrefBinding ($offset+$stride*[Math]::Abs([long]$height) -eq $Bytes) 'PREPARED_BMP_PIXELS'
    return [ordered]@{width=$width;height=$height;depth=24;resolution=96;format='BMP';visual_semantics_qualified=$false}
}
function Export-P09Prepared690Pages($State,[string]$Label) {
    Assert-P09XrefBinding ($Label -cin @('initial','reopened')) 'PREPARED_FIXED_IMAGE_LABEL'
    Assert-P09XrefPreassignedOwnerAnchor $State.owner
    Assert-P09XrefBinding ((Test-P58Owner $State.owner) -eq $true) 'PREPARED_IMAGE_OWNER'
    $count=$State.owner.hwp.PageCount
    Assert-P09XrefBinding ($count -is [int] -and $count -gt 0 -and $count -le 8) 'PREPARED_IMAGE_PAGE_LIMIT'
    for ($page=0;$page -lt $count;$page++) {
        Assert-P09XrefPreassignedOwnerAnchor $State.owner
        $name=$Label+'-page-'+($page+1).ToString('000')+'.bmp';$path=Join-Path $State.run $name
        Assert-P09XrefExclusiveDestination $path
        # Desktop Automation (installed IHwpObject), not WebHwp/CreatePageImageEx.
        # No printer, PrintToImage action, source edit, page selection or PDF SaveAs.
        $returned=$State.owner.hwp.CreatePageImage($path,$page,96,24,'BMP')
        Assert-P09XrefBinding ($returned -is [bool] -and $returned) 'PREPARED_IMAGE_FAILED_EFFECT_UNKNOWN'
        $pin=Get-P09Prepared690Pin $path 16777216 ''
        $stream=[IO.File]::OpenRead($path);$head=[byte[]]::new(54)
        try {Assert-P09XrefBinding ($stream.Read($head,0,54) -eq 54) 'PREPARED_BMP_SHORT'} finally {$stream.Dispose()}
        $bitmap=Assert-P09Prepared690Bitmap $head $pin.bytes
        $State.trace.artifacts[$name]=[ordered]@{pin=$pin;owner=$State.owner.identity;page_number=$page;
            page_count=$count;bitmap=$bitmap;effect_semantics_qualified=$false}
    }
    Assert-P09XrefBinding ($State.owner.hwp.PageCount -eq $count -and (Test-P58Owner $State.owner) -eq $true) 'PREPARED_IMAGE_STABLE_PAGE_COUNT'
}
function Invoke-P09Prepared690Step($State,[string]$Step) {
    $steps=Get-P09Prepared690Steps
    Assert-P09XrefBinding (-not $State.failed -and $State.cursor -lt $steps.Count -and $Step -ceq $steps[$State.cursor]) 'PREPARED_STEP_NO_RETRY'
    $State.trace.phase=$Step
    try {
        $d=Invoke-P09XrefPreassignedHostMessage $State.preassigned_channel $State.case_index checkpoint -Step $Step
        if ($Step -cin @('create_save_session','create_reopen_session')) {
            Assert-P09XrefBinding ($null -ne $d -and $null -eq $State.current_descriptor) 'PREPARED_NEW_OWNER_DESCRIPTOR'
            $State.current_descriptor=$d
        } else {Assert-P09XrefBinding ($null -eq $d) 'PREPARED_NO_UNEXPECTED_DESCRIPTOR'}
        switch -CaseSensitive ($Step) {
            'prepare_slot' {
                Assert-P09XrefBinding (-not (Test-Path -LiteralPath $State.run)) 'PREPARED_ATTEMPT_EXISTS'
                $parent=Get-Item -LiteralPath (Split-Path -Parent $State.run) -Force
                while ($null -ne $parent) {
                    Assert-P09XrefBinding ($parent -is [IO.DirectoryInfo] -and ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREPARED_OUTPUT_PARENT'
                    $parent=$parent.Parent
                }
                [void](New-Item -ItemType Directory -Path $State.run);$State.slot_created=$true
                [void](Get-P09Prepared690Pin $State.original 4194304 'f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')
            }
            'create_save_session' {
                $State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State save)
                Admit-P09XrefPreassignedOwner $State.owner $State
            }
            'candidate_open' {
                Open-P09Prepared690Lease $State $State.candidate $State.candidate_sha
                $State.document=Open-P58Document $State.owner $State.candidate $State.candidate_sha
            }
            'candidate_bind' {Observe-P09Prepared690Document $State $State.candidate $State.candidate_sha}
            'initial_identity' {
                Observe-P09Prepared690Document $State $State.candidate $State.candidate_sha
                $State.trace.initial_open_observed=$true
            }
            'initial_snapshot' {$State.initial=Save-P09Prepared690Artifact $State 'initial.hwpx' HWPX}
            'initial_image' {
                Observe-P09Prepared690Document $State (Join-Path $State.run 'initial.hwpx') $State.initial.sha256
                Export-P09Prepared690Pages $State initial
            }
            'saved_save' {$State.saved=Save-P09Prepared690Artifact $State 'saved.hwpx' HWPX}
            'saved_bind' {
                Observe-P09Prepared690Document $State (Join-Path $State.run 'saved.hwpx') $State.saved.sha256
                Open-P09Prepared690Lease $State (Join-Path $State.run 'saved.hwpx') $State.saved.sha256
            }
            'save_session_close' {$State.previous_identity=$State.owner.identity;Close-P09Prepared690Owner $State}
            'create_reopen_session' {
                $State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State reopen)
                Admit-P09XrefPreassignedOwner $State.owner $State
                Assert-P09XrefFreshSessionIdentity $State.previous_identity $State.owner.identity
            }
            'fresh_saved_open' {
                $State.document=Open-P58Document $State.owner (Join-Path $State.run 'saved.hwpx') $State.saved.sha256
                Observe-P09Prepared690Document $State (Join-Path $State.run 'saved.hwpx') $State.saved.sha256
            }
            'reopened_save' {$State.reopened=Save-P09Prepared690Artifact $State 'reopened.hwpx' HWPX}
            'reopened_image' {
                Observe-P09Prepared690Document $State (Join-Path $State.run 'reopened.hwpx') $State.reopened.sha256
                Export-P09Prepared690Pages $State reopened
            }
            'reopen_session_close' {Close-P09Prepared690Owner $State}
            'final_source_check' {
                [void](Get-P09Prepared690Pin $State.original 4194304 'f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')
                [void](Get-P09Prepared690Pin $State.candidate 4194304 $State.candidate_sha)
                foreach ($name in $State.trace.artifacts.Keys) {
                    [void](Get-P09Prepared690Pin (Join-Path $State.run $name) 33554432 $State.trace.artifacts[$name].pin.sha256)
                }
                $State.trace.source_identity_preserved=$true;$State.trace.state='capture_returned_semantics_unqualified'
            }
            default {throw 'P09_XREF_BIND_PREPARED_UNKNOWN_STEP'}
        }
        $State.cursor++
    } catch {$State.failed=$true;throw}
}
function Complete-P09Prepared690Case($State) {
    if ($null -ne $State.owner -and -not $State.close_attempted) {
        try {Close-P09Prepared690Owner $State} catch {$State.trace.cleanup_error=Get-P09Prepared690SafeCode $_}
    }
    if ($null -eq $State.owner) {
        foreach ($lease in $State.leases) {$lease.Dispose()}
        $State.leases.Clear();$State.trace.input_leases_closed=$true
    }
    if ($State.slot_created) {
        $path=Join-Path $State.run 'case-trace.json'
        $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($State.trace | ConvertTo-Json -Depth 20 -Compress))
        Assert-P09XrefBinding ($bytes.Length -le 262144) 'PREPARED_TRACE_BUDGET'
        $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
    }
}

