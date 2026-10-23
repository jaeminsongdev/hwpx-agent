# Function library only. No session creation or native execution authority.
Set-StrictMode -Version Latest

function Initialize-P09XrefHeldIdentityBridge {
    $type='P09XrefHeldIdentity' -as [type]
    $owned=Get-Variable -Name P09XrefHeldIdentityOwnedType -Scope Script -ErrorAction SilentlyContinue
    if ($null -ne $type) {
        Assert-P09XrefBinding ($null -ne $owned -and $owned.Value -eq $type) 'KERNEL_IDENTITY_TYPE_NOT_OWNED'
        return
    }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public sealed class P09XrefHeldIdentity : IDisposable {
    public sealed class Snapshot {
        public int ProcessId;
        public int SessionId;
        public long Birth100ns;
        public string Image;
        public bool WindowVerified;
    }
    [StructLayout(LayoutKind.Sequential)] private struct FileTime { public uint Low, High; }
    [DllImport("kernel32.dll", SetLastError=true)] private static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll")] private static extern int GetCurrentProcessId();
    [DllImport("kernel32.dll")] private static extern int GetProcessId(IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool GetProcessTimes(IntPtr process, out FileTime birth, out FileTime exit, out FileTime kernel, out FileTime user);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool GetExitCodeProcess(IntPtr process, out uint code);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool ProcessIdToSessionId(int pid, out int session);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] private static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder image, ref uint size);
    [DllImport("kernel32.dll")] private static extern uint WaitForSingleObject(IntPtr process, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool CloseHandle(IntPtr handle);
    [DllImport("user32.dll", SetLastError=true)] private static extern uint GetWindowThreadProcessId(IntPtr window, out int pid);
    private IntPtr handle;
    private readonly int pid;
    public P09XrefHeldIdentity(int processId) {
        if (processId <= 0) throw new InvalidOperationException("P09_XREF_KERNEL_PID");
        pid=processId;
        handle=OpenProcess(0x00101000, false, pid); // Query-limited + synchronize only.
        if (handle==IntPtr.Zero) throw new InvalidOperationException("P09_XREF_KERNEL_OPEN_QUERY_ONLY");
    }
    private Snapshot Read() {
        if (handle==IntPtr.Zero || GetProcessId(handle)!=pid || WaitForSingleObject(handle,0)!=258)
            throw new InvalidOperationException("P09_XREF_KERNEL_SAME_LIVE_HANDLE");
        FileTime birth,exit,kernel,user; uint code; int session;
        var image=new StringBuilder(32768); uint size=32768;
        if (!GetProcessTimes(handle,out birth,out exit,out kernel,out user) ||
            !GetExitCodeProcess(handle,out code) || code!=259 || !ProcessIdToSessionId(pid,out session) ||
            !QueryFullProcessImageName(handle,0,image,ref size) || WaitForSingleObject(handle,0)!=258)
            throw new InvalidOperationException("P09_XREF_KERNEL_OBSERVATION");
        return new Snapshot { ProcessId=pid,SessionId=session,
            Birth100ns=(long)(((ulong)birth.High<<32)|birth.Low),Image=image.ToString(),WindowVerified=false };
    }
    public Snapshot ReadCurrentProcessOnly() {
        if (pid!=GetCurrentProcessId()) throw new InvalidOperationException("P09_XREF_KERNEL_SELF_ONLY");
        return Read();
    }
    public Snapshot ReadOwnedWindow(int window) {
        if (window==0) throw new InvalidOperationException("P09_XREF_KERNEL_WINDOW_REQUIRED");
        var row=Read(); int actual;
        var hwnd=IntPtr.Size==4 ? new IntPtr(window) : new IntPtr((long)(uint)window);
        if (GetWindowThreadProcessId(hwnd,out actual)==0 || actual!=pid)
            throw new InvalidOperationException("P09_XREF_KERNEL_WINDOW_PID");
        row.WindowVerified=true; return row;
    }
    public void Dispose() {
        if (handle!=IntPtr.Zero) {
            if (!CloseHandle(handle)) throw new InvalidOperationException("P09_XREF_KERNEL_HANDLE_CLOSE");
            handle=IntPtr.Zero;
        }
    }
}
'@
    $script:P09XrefHeldIdentityOwnedType='P09XrefHeldIdentity' -as [type]
}

function New-P09XrefDualIdentityRecord($Compatibility,[string]$Kind,$Before,$After) {
    Assert-P09XrefBinding ($Kind -cin @('original_p58_identity','current_process_cim_only')) 'DUAL_IDENTITY_KIND'
    $keys=@('process_id','session_id','created_at_utc')
    if ($Kind -ceq 'original_p58_identity') {$keys+=@('executable_sha256','window_handle_binds_exact_process')}
    Assert-P09XrefBinding ($Compatibility -is [Collections.IDictionary] -and
        $Compatibility.Count -eq $keys.Count) 'DUAL_COMPATIBILITY_SCHEMA'
    foreach ($key in $keys) {Assert-P09XrefBinding ($Compatibility.Contains($key)) 'DUAL_COMPATIBILITY_KEY'}
    Assert-P09XrefBinding ($Compatibility.process_id -is [int] -and $Compatibility.process_id -gt 0 -and
        $Compatibility.session_id -is [int] -and $Compatibility.session_id -ge 0 -and
        $Compatibility.created_at_utc -is [string] -and
        $Compatibility.created_at_utc -cmatch '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}Z$') 'DUAL_COMPATIBILITY_TYPES'
    # Validate the date without converting/rounding it into the kernel identity.
    [void][datetime]::ParseExact($Compatibility.created_at_utc,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)
    Assert-P09XrefBinding ($Before.ProcessId -eq $After.ProcessId -and $Before.SessionId -eq $After.SessionId -and
        $Before.Birth100ns -eq $After.Birth100ns -and $Before.Birth100ns -gt 0 -and
        $Before.Image -ceq $After.Image -and $Before.WindowVerified -eq $After.WindowVerified -and
        $Compatibility.process_id -eq $Before.ProcessId -and $Compatibility.session_id -eq $Before.SessionId) 'DUAL_SAME_HELD_KERNEL_IDENTITY'
    $compat=[ordered]@{};$canonical=[ordered]@{}
    foreach ($key in $keys) {$compat[$key]=$Compatibility[$key];$canonical[$key]=$Compatibility[$key]}
    $canonical.created_at_utc=[datetime]::FromFileTimeUtc([long]$Before.Birth100ns).ToString('o')
    return [ordered]@{schema_version='hwpx-agent.private.crossref-dual-owner-identity/v1';
        compatibility_kind=$Kind;compatibility_identity=$compat;kernel_identity=$canonical;
        kernel_creation_filetime_100ns=([long]$Before.Birth100ns).ToString([Globalization.CultureInfo]::InvariantCulture);
        kernel_process_image=[string]$Before.Image;kernel_window_verified=[bool]$Before.WindowVerified;
        kernel_before_after_same_handle_equal=$true;compatibility_fresh_check_returned=$true;
        kernel_creation_not_derived_from_cim=$true;native_provenance_qualified=$false;
        native_execution_authorized=$false;p09_complete=$false}
}

function Observe-P09XrefDualOwnedIdentity($Owner) {
    Assert-P09XrefOriginalOwnerFunction
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    Assert-P09XrefBinding ($Owner.verified -eq $true -and $null -ne $Owner.identity -and $null -ne $Owner.window -and
        $Owner.identity.executable_sha256 -ceq '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce' -and
        $Owner.identity.window_handle_binds_exact_process -is [bool] -and $Owner.identity.window_handle_binds_exact_process -and
        [Runtime.InteropServices.Marshal]::IsComObject($Owner.window)) 'DUAL_REAL_OWNED_WINDOW_REQUIRED'
    $window=$Owner.window.WindowHandle
    Assert-P09XrefBinding ($window -is [int] -and $window -ne 0) 'DUAL_WINDOW_HANDLE_TYPE'
    Initialize-P09XrefHeldIdentityBridge
    $lease=[P09XrefHeldIdentity]::new([int]$Owner.identity.process_id)
    try {
        $before=$lease.ReadOwnedWindow($window)
        # Original fresh CIM/session/window predicate stays byte-for-byte unchanged.
        Assert-P09XrefBinding ((Test-P58Owner $Owner) -eq $true) 'DUAL_ORIGINAL_FRESH_OWNER_CHECK'
        $after=$lease.ReadOwnedWindow($window)
        Assert-P09XrefBinding ([string]::Equals($before.Image,$executable,[StringComparison]::OrdinalIgnoreCase)) 'DUAL_FIXED_HANCOM_IMAGE'
        return New-P09XrefDualIdentityRecord $Owner.identity 'original_p58_identity' $before $after
    } finally {$lease.Dispose()}
}

function Invoke-P09XrefCanonicalHostAdmission($Channel,[int]$CaseIndex,$Owner,$Evidence) {
    Assert-P09XrefBinding ($Evidence -is [Collections.Generic.List[object]]) 'DUAL_EVIDENCE_LIST'
    $observed=Observe-P09XrefDualOwnedIdentity $Owner
    $entry=[ordered]@{observation=$observed;channel_message_attempted=$true;channel_message_returned=$false;
        error_code=$null;native_provenance_qualified=$false;native_execution_authorized=$false;p09_complete=$false}
    [void]$Evidence.Add($entry)
    # A borrowed-window proxy changes only the admission representation, not Owner,
    # its original CIM identity, original cleanup, source trace or RCW ownership.
    $proxy=[ordered]@{identity=$observed.kernel_identity;window=$Owner.window}
    try {
        Invoke-P09XrefHostMessage $Channel $CaseIndex 'admit_owner' -Owner $proxy
        $entry.channel_message_returned=$true
    } catch {$entry.error_code='P09_XREF_BIND_DUAL_HOST_ADMISSION_FAILED';throw}
}
