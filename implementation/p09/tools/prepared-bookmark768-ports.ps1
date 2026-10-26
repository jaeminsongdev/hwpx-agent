# Fixed prepared-file IO. No SDK insert, REF-036 refresh, arbitrary action/path or retry.
Set-StrictMode -Version Latest
function Get-P09Prepared768SafeCode($Failure) {
    $code=$Failure.Exception.GetBaseException().Message
    if ($code -cmatch '^(P09_XREF_(BIND|ROT)_|P58_|STOP_)[A-Z0-9_]{1,120}$') {return $code}
    return 'P09_XREF_BIND_PREPARED_FAILED_NO_RAW_VALUES'
}
function Get-P09Prepared768Pin([string]$Path,[int]$Maximum,[string]$Expected) {
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
function Open-P09Prepared768Lease($State,[string]$Path,[string]$Sha) {
    [void](Get-P09Prepared768Pin $Path 4194304 $Sha)
    $lease=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    [void]$State.leases.Add($lease)
    [void](Get-P09Prepared768Pin $Path 4194304 $Sha)
}
function Observe-P09Prepared768Document($State,[string]$Path,[string]$Sha) {
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    $pointers=[Collections.Generic.List[IntPtr]]::new()
    try {
        Open-P09Prepared768Lease $State $Path $Sha
        $app=Get-P09XrefHeldComIdentity $State.owner.hwp $pointers
        $collection=Get-P09XrefHeldComIdentity $State.owner.documents $pointers
        $document=Get-P09XrefHeldComIdentity $State.document $pointers
        $before=Read-P09XrefActiveSourceObservation $State.owner $State.document $pointers $app $collection $document $Path
        $after=Read-P09XrefActiveSourceObservation $State.owner $State.document $pointers $app $collection $document $Path
        Assert-P09XrefBinding ((Test-P58Owner $State.owner) -eq $true) 'PREPARED_DOCUMENT_FINAL_OWNER'
        [void](Assert-P09XrefActiveSourceObservations $before $after)
    } finally {foreach ($pointer in $pointers) {[void][Runtime.InteropServices.Marshal]::Release($pointer)}}
}
function Close-P09Prepared768Owner($State) {
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

function Invoke-P09Prepared768Step($State,[string]$Step) {
    $steps=Get-P09Prepared768Steps
    Assert-P09XrefBinding (-not $State.failed -and $State.cursor -lt $steps.Count -and $Step -ceq $steps[$State.cursor]) 'CURSOR768_STEP_NO_RETRY'
    $State.trace.phase=$Step
    try {
        $d=Invoke-P09XrefPreassignedHostMessage $State.preassigned_channel $State.case_index checkpoint -Step $Step
        if ($Step -cin @('create_save_session','create_reopen_session')) {
            Assert-P09XrefBinding ($null -ne $d -and $null -eq $State.current_descriptor) 'CURSOR768_NEW_OWNER'
            $State.current_descriptor=$d
        } else {Assert-P09XrefBinding ($null -eq $d) 'CURSOR768_NO_UNEXPECTED_DESCRIPTOR'}
        switch -CaseSensitive ($Step) {
            'prepare_slot' {
                Assert-P09XrefBinding (-not (Test-Path -LiteralPath $State.run)) 'CURSOR768_OUTPUT_EXISTS'
                $parent=Get-Item -LiteralPath (Split-Path -Parent $State.run) -Force
                while ($null -ne $parent) {
                    Assert-P09XrefBinding ($parent -is [IO.DirectoryInfo] -and ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREPARED_OUTPUT_PARENT'
                    $parent=$parent.Parent
                }
                [void](New-Item -ItemType Directory -Path $State.run);$State.slot_created=$true
                [void](Get-P09Prepared768Pin $State.original 4194304 'f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')
            }
            'create_save_session' {$State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State save);Admit-P09XrefPreassignedOwner $State.owner $State}
            'candidate_open' {
                Open-P09Prepared768Lease $State $State.candidate $State.candidate_sha
                $State.document=Open-P58Document $State.owner $State.candidate $State.candidate_sha
            }
            'candidate_bind' {Observe-P09Prepared768Document $State $State.candidate $State.candidate_sha}
            'initial_identity' {Observe-P09Prepared768Document $State $State.candidate $State.candidate_sha}
            'initial_snapshot' {Assert-P09XrefBinding ($State.trace.navigation.Count -eq 0) 'CURSOR768_QUERY_NOT_STARTED'}
            'initial_image' {Invoke-P09BookmarkCursor768 $State initial $State.candidate $State.candidate_sha}
            'saved_save' {Observe-P09Prepared768Document $State $State.candidate $State.candidate_sha}
            'saved_bind' {Assert-P09XrefBinding ($State.trace.navigation.Count -eq 1) 'CURSOR768_FIRST_QUERY_ONCE'}
            'save_session_close' {$State.previous_identity=$State.owner.identity;Close-P09Prepared768Owner $State}
            'create_reopen_session' {
                $State.close_attempted=$false;[void](Connect-P09XrefPreassignedOwner $State reopen);Admit-P09XrefPreassignedOwner $State.owner $State
                Assert-P09XrefFreshSessionIdentity $State.previous_identity $State.owner.identity
            }
            'fresh_saved_open' {
                Open-P09Prepared768Lease $State $State.second $State.second_sha
                $State.document=Open-P58Document $State.owner $State.second $State.second_sha
                Observe-P09Prepared768Document $State $State.second $State.second_sha
            }
            'reopened_save' {Invoke-P09BookmarkCursor768 $State reopened $State.second $State.second_sha}
            'reopened_image' {Assert-P09XrefBinding ($State.trace.navigation.Count -eq 2) 'CURSOR768_SECOND_QUERY_ONCE'}
            'reopen_session_close' {Close-P09Prepared768Owner $State}
            'final_source_check' {
                [void](Get-P09Prepared768Pin $State.candidate 4194304 $State.candidate_sha)
                [void](Get-P09Prepared768Pin $State.second 4194304 $State.second_sha)
                [void](Get-P09Prepared768Pin $State.original 4194304 'f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')
                Assert-P09XrefBinding ($State.trace.navigation.Count -eq 2 -and -not $State.trace.SaveAs_invoked) 'CURSOR768_WHOLE_QUERY_ONLY'
                $State.trace.source_identity_preserved=$true;$State.trace.state='capture_returned_semantics_unqualified'
            }
            default {throw 'P09_XREF_BIND_CURSOR768_UNKNOWN_STEP'}
        }
        $State.cursor++
    } catch {$State.failed=$true;throw}
}
function Complete-P09Prepared768Case($State) {
    if ($null -ne $State.owner -and -not $State.close_attempted) {
        try {Close-P09Prepared768Owner $State} catch {$State.trace.cleanup_error=Get-P09Prepared768SafeCode $_}
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

