# Trusted private successor functions only. No launcher, CLI or Native permit.
# The existing adapter owns application/windows/window RCWs; never FinalRelease
# those aliases through the original P58 cleanup as well as disposing its lease.
Set-StrictMode -Version Latest

function Read-P09XrefPreassignedFixedSource([string]$Name) {
    $pins=@{'crossref-existing-owner.cs'='92143ee252cb7c132bc819e24044e5b6dc0e9a17b9d3777575ab6b1ba8732733';
        'crossref-native-case-ports.ps1'='7b5c9d4ae25a35e505d6c34385159cbaa94d3725e49d58cc07c42c4c1e46bd0e'}
    Assert-P09XrefBinding ($Name -cin @($pins.Keys)) 'PREASSIGNED_FIXED_SOURCE_NAME'
    $item=Get-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le 32768) 'PREASSIGNED_FIXED_SOURCE_SIZE'
    $ancestor=$item
    while ($null -ne $ancestor) {
        Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREASSIGNED_FIXED_SOURCE_LINK'
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    $bytes=[IO.File]::ReadAllBytes($item.FullName);$sha=[Security.Cryptography.SHA256]::Create()
    try {$digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$sha.Dispose()}
    Assert-P09XrefBinding ($digest -ceq $pins[$Name]) 'PREASSIGNED_FIXED_SOURCE_IDENTITY'
    return [Text.UTF8Encoding]::new($false,$true).GetString($bytes)
}

function Initialize-P09XrefExistingOwnerAdapter {
    Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
        [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'PREASSIGNED_X86_STA'
    $source=Read-P09XrefPreassignedFixedSource 'crossref-existing-owner.cs'
    $type='P09CrossrefExisting.ExistingOwner' -as [type]
    $owned=Get-Variable P09XrefExistingOwnerOwnedType -Scope Script -ErrorAction SilentlyContinue
    if ($null -ne $type) {
        Assert-P09XrefBinding ($null -ne $owned -and $owned.Value -eq $type) 'PREASSIGNED_ADAPTER_TYPE_NOT_OWNED'
        return
    }
    # A future worker must do this before asking the host to start Native.
    # Compile these already pinned bytes, not an unguarded second path read.
    Add-Type -TypeDefinition $source
    $script:P09XrefExistingOwnerOwnedType='P09CrossrefExisting.ExistingOwner' -as [type]
}

function Assert-P09XrefExistingOwnerAdapterReady {
    $type='P09CrossrefExisting.ExistingOwner' -as [type]
    $owned=Get-Variable P09XrefExistingOwnerOwnedType -Scope Script -ErrorAction SilentlyContinue
    Assert-P09XrefBinding ($null -ne $type -and $null -ne $owned -and $owned.Value -eq $type -and
        -not [Environment]::Is64BitProcess -and [Threading.Thread]::CurrentThread.GetApartmentState() -eq 'STA') 'PREASSIGNED_ADAPTER_PREWARM_REQUIRED'
}

function Convert-P09XrefPreassignedExpectedOwner($Descriptor,[int]$CaseIndex,[string]$Label) {
    Assert-P09XrefExistingOwnerAdapterReady
    $d=Assert-P09XrefPreassignedDescriptor ([pscustomobject]$Descriptor) $CaseIndex $Label
    $birth=[datetime]::ParseExact($d.created_at_utc,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToFileTimeUtc()
    return [P09CrossrefExisting.ExpectedOwner]::new($d.process_id,$d.session_id,$birth)
}

function New-P09XrefPreassignedAdmissionProxy($Owner,$Observed,$Descriptor) {
    Assert-P09XrefBinding ($Observed.compatibility_kind -ceq 'original_p58_identity' -and $Observed.kernel_creation_not_derived_from_cim -and
        $Observed.kernel_before_after_same_handle_equal -and $Observed.kernel_window_verified -and
        -not $Observed.native_execution_authorized -and -not $Observed.p09_complete) 'PREASSIGNED_CANONICAL_OBSERVATION_REQUIRED'
    foreach ($key in @('process_id','session_id','created_at_utc','executable_sha256')) {
        Assert-P09XrefBinding ($Observed.kernel_identity[$key] -ceq $Descriptor[$key]) 'PREASSIGNED_EXACT_CANONICAL_PENDING_OWNER'
    }
    # Borrowed representation only. Never overwrite the original CIM identity.
    return [ordered]@{identity=$Observed.kernel_identity;window=$Owner.window}
}

function Connect-P09XrefPreassignedOwner($State,[string]$Label) {
    Assert-P09XrefExistingOwnerAdapterReady
    Assert-P09XrefOriginalOwnerFunction
    Assert-P09XrefBinding ($null -eq $State.owner -and $null -ne $State.current_descriptor -and
        [object]::ReferenceEquals($State.current_descriptor,$State.preassigned_channel.pending_descriptor)) 'PREASSIGNED_CURRENT_PENDING_DESCRIPTOR'
    $expected=Convert-P09XrefPreassignedExpectedOwner $State.current_descriptor $State.case_index $Label
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    $exeSha='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    $row=[ordered]@{label=$Label;version=$null;register_module_return=$null;process=$null;
        close_without_dirty_prompt_returned=$false;quit_invoked=$false;remaining_owned_process_count=$null;cleanup_error=$null}
    [void]$State.trace.sessions.Add($row)
    # Install the owner record before any fallible attachment/property operation.
    # Original case completion retains it if cleanup is uncertain; no attach retry.
    $owner=[ordered]@{hwp=$null;windows=$null;window=$null;documents=$null;verified=$false;identity=$null;trace=$row;
        preassigned_lease=$null;preassigned_release_attempted=$false;preassigned_release_returned=$false;
        preassigned_close_attempted=$false;preassigned_closed=$false;preassigned_admitted=$false}
    $State.owner=$owner
    $lease=[P09CrossrefExisting.ExistingOwner]::Attach($expected);$owner.preassigned_lease=$lease
    $owner.hwp=$lease.Application;$owner.windows=$lease.Windows;$owner.window=$lease.Window
    $processes=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$expected.Pid))
    Assert-P09XrefBinding ($processes.Count -eq 1) 'PREASSIGNED_CIM_ONE_OWNER'
    $process=$processes[0]
    Assert-P09XrefBinding ([string]$process.Name -ceq 'Hwp.exe' -and [string]$process.ExecutablePath -ceq $executable -and
        [int]$process.SessionId -eq $expected.Session -and $expected.Session -eq [Diagnostics.Process]::GetCurrentProcess().SessionId -and
        $null -ne $process.CreationDate) 'PREASSIGNED_ORIGINAL_CIM_PROCESS'
    [void](Assert-P58File $executable 4194304 $exeSha)
    $owner.identity=[ordered]@{process_id=[int]$expected.Pid;session_id=[int]$process.SessionId;
        created_at_utc=([datetime]$process.CreationDate).ToUniversalTime().ToString('o');executable_sha256=$exeSha;
        window_handle_binds_exact_process=$true}
    $owner.verified=$true;$row.process=$owner.identity;$row.version=$lease.Identity.Version
    Assert-P09XrefBinding ((Test-P58Owner $owner) -eq $true) 'PREASSIGNED_ORIGINAL_FRESH_OWNER'
    $owner.documents=$owner.hwp.XHwpDocuments
    Assert-P09XrefBinding ([Runtime.InteropServices.Marshal]::IsComObject($owner.documents)) 'PREASSIGNED_REAL_DOCUMENT_COLLECTION'
    # RegisterModule/Visible/document actions occur only after host admission.
}

function Admit-P09XrefPreassignedOwner($Owner,$State) {
    $observed=Observe-P09XrefDualOwnedIdentity $Owner
    $proxy=New-P09XrefPreassignedAdmissionProxy $Owner $observed $State.current_descriptor
    $entry=[ordered]@{observation=$observed;channel_message_attempted=$true;channel_message_returned=$false;error_code=$null;
        native_provenance_qualified=$false;native_execution_authorized=$false;p09_complete=$false}
    [void]$State.dual_identity_evidence.Add($entry)
    try {[void](Invoke-P09XrefPreassignedHostMessage $State.preassigned_channel $State.case_index 'admit_owner' -Owner $proxy);$entry.channel_message_returned=$true}
    catch {$entry.error_code='P09_XREF_BIND_PREASSIGNED_HOST_ADMISSION_FAILED';throw}
    $Owner.preassigned_admitted=$true;$State.current_descriptor=$null
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'PREASSIGNED_OWNER_BEFORE_SETUP'
    $Owner.trace.register_module_return=[bool]$Owner.hwp.RegisterModule('FilePathCheckDLL','FilePathCheckerModuleExample')
    $Owner.window.Visible=$true
}

function Release-P09XrefPreassignedReferences($Owner) {
    Assert-P09XrefBinding (-not $Owner.preassigned_release_attempted) 'PREASSIGNED_NO_REFERENCE_RELEASE_RETRY'
    $Owner.preassigned_release_attempted=$true;$failed=$false
    try {
        $documents=$Owner.documents;$Owner.documents=$null
        if ($null -ne $documents) {
            Assert-P09XrefBinding ([Runtime.InteropServices.Marshal]::IsComObject($documents)) 'PREASSIGNED_DOCUMENT_COLLECTION_RELEASE_TYPE'
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($documents)
        }
    } catch {$failed=$true;$Owner['preassigned_failed_document_reference']=$documents}
    finally {
        try {
            if ($null -ne $Owner.preassigned_lease) {
                Assert-P09XrefBinding ($Owner.preassigned_lease -is [P09CrossrefExisting.ExistingOwnerLease]) 'PREASSIGNED_TYPED_LEASE_RELEASE'
                $Owner.preassigned_lease.Dispose()
            }
        } catch {$failed=$true}
        finally {$Owner.hwp=$null;$Owner.windows=$null;$Owner.window=$null}
    }
    # Keep a failed lease reference and record for diagnosis, never dispose twice.
    if (-not $failed) {$Owner.preassigned_lease=$null;$Owner.preassigned_release_returned=$true}
    Assert-P09XrefBinding (-not $failed) 'PREASSIGNED_REFERENCE_RELEASE_FAILED'
}

function Assert-P09XrefPreassignedOwnerAnchor($Owner) {
    Assert-P09XrefExistingOwnerAdapterReady
    Assert-P09XrefBinding ($null -ne $Owner.preassigned_lease -and $Owner.preassigned_lease -is [P09CrossrefExisting.ExistingOwnerLease] -and
        [Runtime.InteropServices.Marshal]::IsComObject($Owner.hwp) -and [Runtime.InteropServices.Marshal]::IsComObject($Owner.window) -and
        [object]::ReferenceEquals($Owner.hwp,$Owner.preassigned_lease.Application) -and
        [object]::ReferenceEquals($Owner.windows,$Owner.preassigned_lease.Windows) -and
        [object]::ReferenceEquals($Owner.window,$Owner.preassigned_lease.Window)) 'PREASSIGNED_EXACT_RETAINED_COM_LEASE'
}

function Close-P09XrefPreassignedOwner($Owner) {
    Assert-P09XrefBinding (-not $Owner.preassigned_close_attempted) 'PREASSIGNED_NO_CLOSE_OR_QUIT_RETRY'
    $Owner.preassigned_close_attempted=$true
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    try {
        Assert-P09XrefOriginalOwnerFunction;Assert-P09XrefPreassignedOwnerAnchor $Owner
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'PREASSIGNED_OWNER_BEFORE_CLOSE'
        $Owner.documents.Close($false);$Owner.trace.close_without_dirty_prompt_returned=$true
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'PREASSIGNED_OWNER_BEFORE_QUIT'
        $Owner.hwp.Quit();$Owner.trace.quit_invoked=$true
    } catch {$Owner.trace.cleanup_error='P09_XREF_BIND_PREASSIGNED_OWNED_CLOSE_FAILED_NO_FORCE_KILL'}
    finally {
        try {Release-P09XrefPreassignedReferences $Owner}
        catch {$Owner.trace.cleanup_error='P09_XREF_BIND_PREASSIGNED_REFERENCE_CLEANUP_FAILED'}
    }
    $watch=[Diagnostics.Stopwatch]::StartNew();$remaining=-1
    try {
        if ($null -ne $Owner.identity) {
            do {
                $remaining=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$Owner.identity.process_id)).Count
                if ($remaining -eq 0 -or $watch.ElapsedMilliseconds -ge 10000) {break}
                Start-Sleep -Milliseconds 100
            } while ($true)
        }
    } finally {$watch.Stop();$Owner.trace.remaining_owned_process_count=$remaining}
    $Owner.preassigned_closed=($null -eq $Owner.trace.cleanup_error -and $Owner.trace.quit_invoked -and
        $Owner.trace.close_without_dirty_prompt_returned -and $Owner.preassigned_release_returned -and $remaining -eq 0)
    Assert-P09XrefBinding $Owner.preassigned_closed 'PREASSIGNED_OWNED_CLEANUP_UNCONFIRMED'
}
