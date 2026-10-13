# Functions only. The caller verifies source identity before dot-sourcing this file.
Set-StrictMode -Version Latest

function Test-P58Owner {
    param($Owner)
    if (-not $Owner.verified -or $null -eq $Owner.identity) {return $false}
    $rows=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$Owner.identity.process_id))
    if ($rows.Count -ne 1) {return $false}
    $row=$rows[0]
    return ([int]$row.SessionId -eq $Owner.identity.session_id -and
        ([datetime]$row.CreationDate).ToUniversalTime().ToString('o') -ceq $Owner.identity.created_at_utc -and
        [string]$row.ExecutablePath -ceq $executable -and
        ([P58OwnedWindowProcess]::ProcessId([int]$Owner.window.WindowHandle)) -eq $Owner.identity.process_id)
}

function Release-P58Com {
    param($Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Close-P58Owner {
    param($Owner)
    if ($null -eq $Owner) {return}
    try {
        if (Test-P58Owner $Owner) {
            $Owner.documents.Close($false)
            $Owner.trace.close_without_dirty_prompt_returned=$true
            if (-not (Test-P58Owner $Owner)) {throw 'P58_OWNER_CHANGED_BEFORE_QUIT'}
            $Owner.hwp.Quit();$Owner.trace.quit_invoked=$true
        } else {$Owner.trace.cleanup_error='P58_OWNER_UNVERIFIED_NO_BLANKET_QUIT'}
    } catch {$Owner.trace.cleanup_error='P58_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL'}
    finally {
        Release-P58Com $Owner.documents;Release-P58Com $Owner.window
        Release-P58Com $Owner.windows;Release-P58Com $Owner.hwp
        $Owner.documents=$null;$Owner.window=$null;$Owner.windows=$null;$Owner.hwp=$null
        [GC]::Collect();[GC]::WaitForPendingFinalizers();[GC]::Collect();[GC]::WaitForPendingFinalizers()
    }
    $watch=[Diagnostics.Stopwatch]::StartNew()
    do {
        $remaining=if ($null -ne $Owner.identity) {@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$Owner.identity.process_id)).Count} else {-1}
        if ($remaining -eq 0 -or $watch.ElapsedMilliseconds -ge 10000) {break}
        Start-Sleep -Milliseconds 100
    } while ($true)
    $watch.Stop();$Owner.trace.remaining_owned_process_count=$remaining
}

function New-P58Owner {
    param([string]$Label,$Trace)
    if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {throw 'P58_NEW_SESSION_REQUIRES_ZERO_HWP'}
    $started=[datetime]::UtcNow
    $row=[ordered]@{label=$Label;version=$null;register_module_return=$null;process=$null;
        close_without_dirty_prompt_returned=$false;quit_invoked=$false;remaining_owned_process_count=$null;cleanup_error=$null}
    [void]$Trace.sessions.Add($row)
    $owner=[ordered]@{hwp=$null;windows=$null;window=$null;documents=$null;verified=$false;identity=$null;trace=$row}
    try {
        $owner.hwp=New-Object -ComObject 'HWPFrame.HwpObject.2'
        $owner.windows=$owner.hwp.XHwpWindows;$owner.window=$owner.windows.Item(0)
        $handle=$owner.window.WindowHandle
        if ($handle -isnot [int] -or $handle -eq 0) {throw 'P58_NATIVE_WINDOW_HANDLE_TYPE'}
        $processId=[P58OwnedWindowProcess]::ProcessId($handle)
        $processes=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$processId))
        if ($processes.Count -ne 1) {throw 'P58_OWNED_WINDOW_PROCESS_MISSING'}
        $process=$processes[0]
        if ([string]$process.Name -cne 'Hwp.exe' -or [string]$process.ExecutablePath -cne $executable -or
            [int]$process.SessionId -ne [Diagnostics.Process]::GetCurrentProcess().SessionId -or
            $null -eq $process.CreationDate -or ([datetime]$process.CreationDate).ToUniversalTime() -lt $started.AddSeconds(-2)) {
            throw 'P58_WINDOW_PROCESS_OWNERSHIP_REJECTED'
        }
        [void](Assert-P58File $executable 4194304 $exeSha)
        $owner.identity=[ordered]@{process_id=[int]$processId;session_id=[int]$process.SessionId;
            created_at_utc=([datetime]$process.CreationDate).ToUniversalTime().ToString('o');
            executable_sha256=$exeSha;window_handle_binds_exact_process=$true}
        $owner.verified=$true;$row.process=$owner.identity;$owner.documents=$owner.hwp.XHwpDocuments
        $version=([string]$owner.hwp.Version).Replace(',','.').Replace(' ','')
        if ($version -cne '11.0.0.9136') {throw 'P58_NATIVE_VERSION'}
        $row.version=$version;$row.register_module_return=[bool]$owner.hwp.RegisterModule('FilePathCheckDLL',$securityName)
        $owner.window.Visible=$true
        return $owner
    } catch {Close-P58Owner $owner;throw}
}

function Open-P58Document {
    param($Owner,[string]$Path,[string]$Sha)
    if (-not (Test-P58Owner $Owner)) {throw 'P58_OPEN_OWNER_MISMATCH'}
    [void](Assert-P58File $Path 4194304 $Sha)
    $before=[int]$Owner.documents.Count
    if ($Owner.hwp.Open($Path,'HWPX','lock:false;setcurdir:false') -ne $true) {throw 'P58_OPEN_FAILED'}
    $after=[int]$Owner.documents.Count
    if ($after -lt 1 -or $after -lt $before -or $after -gt ($before+1)) {throw 'P58_OPEN_DOCUMENT_INVENTORY'}
    $doc=$Owner.documents.Item($after-1)
    try {
        if (-not [string]::Equals([string]$doc.FullName,$Path,[StringComparison]::OrdinalIgnoreCase)) {throw 'P58_OPEN_DOCUMENT_PATH'}
        [void]$doc.SetActive_XHwpDocument()
        return $doc
    } catch {Release-P58Com $doc;throw}
}

function Save-P58Artifact {
    param($Owner,$Doc,[string]$Name,[string]$Format)
    if (-not (Test-P58Owner $Owner)) {throw 'P58_SAVE_OWNER_MISMATCH'}
    if ($Name -cnotmatch '^(saved|reopened)\.(hwpx|pdf)$' -or
        (($Format -ceq 'PDF') -ne $Name.EndsWith('.pdf')) -or $Format -cnotin @('PDF','HWPX')) {throw 'P58_OUTPUT_SCOPE'}
    $path=Join-Path $run $Name
    if (Test-Path -LiteralPath $path) {throw 'P58_EXCLUSIVE_OUTPUT_EXISTS'}
    if ($Doc.SaveAs($path,$Format,'') -ne $true) {throw 'P58_NATIVE_SAVE_FAILED'}
    $max=if ($Format -ceq 'PDF') {33554432} else {4194304}
    $item=Assert-P58File $path $max
    if ($Format -ceq 'PDF') {
        $stream=[IO.File]::OpenRead($path);$head=[byte[]]::new(5)
        try {if ($stream.Read($head,0,5) -ne 5 -or [Text.Encoding]::ASCII.GetString($head) -cne '%PDF-') {throw 'P58_PDF_SIGNATURE'}}
        finally {$stream.Dispose()}
    }
    return $item
}
