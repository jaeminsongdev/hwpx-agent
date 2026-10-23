[CmdletBinding()]
param([switch]$InspectExisting29824Only)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if(-not $InspectExisting29824Only -or [IntPtr]::Size -ne 4 -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA'){throw 'P09_XREF_ROT_READBACK_CLOSED_MODE'}
$phase='compile'
try{
    Add-Type -Path @((Join-Path $PSScriptRoot 'crossref-existing-owner.cs'),(Join-Path $PSScriptRoot 'crossref-existing-owner-readback.cs'))
    $phase='error_models'
    $good=[InvalidOperationException]::new('P09_XREF_ROT_NO_EXACT_EXISTING_OWNER')
    if([P09CrossrefExisting.OwnerReadback]::ClosedError($good) -cne $good.Message){throw 'P09_XREF_ROT_READBACK_MODEL_CODE'}
    [Console]::WriteLine('test owner_readback::closed_code ... ok')
    $private=[InvalidOperationException]::new('private document and account values')
    if([P09CrossrefExisting.OwnerReadback]::ClosedError($private) -cne 'P09_XREF_ROT_READBACK_FAILURE_NO_RAW_VALUES'){throw 'P09_XREF_ROT_READBACK_MODEL_REDACTION'}
    [Console]::WriteLine('test owner_readback::private_message_redacted ... ok')
    $com=[Runtime.InteropServices.COMException]::new('private native details',-2147467262)
    $wrapped=[Reflection.TargetInvocationException]::new($com)
    if([P09CrossrefExisting.OwnerReadback]::ErrorHResult($wrapped) -cne '80004002'){throw 'P09_XREF_ROT_READBACK_MODEL_HRESULT'}
    [Console]::WriteLine('test owner_readback::nested_hresult_only ... ok')
    $phase='expected_kernel_identity';$process=[Diagnostics.Process]::GetProcessById(29824)
    try{
        if($process.HasExited -or -not [string]::Equals($process.MainModule.FileName,[P09CrossrefExisting.ExistingOwner]::Image,[StringComparison]::OrdinalIgnoreCase)){throw 'P09_XREF_ROT_READBACK_EXPECTED_PROCESS'}
        $birth=$process.StartTime.ToFileTimeUtc();$session=$process.SessionId
        $expected=[P09CrossrefExisting.ExpectedOwner]::new(29824,$session,$birth)
        $phase='readonly_existing_owner';$row=[P09CrossrefExisting.OwnerReadback]::Inspect($expected)
        $process.Refresh();$same=(-not $process.HasExited -and $process.StartTime.ToFileTimeUtc() -eq $birth -and $process.SessionId -eq $session)
        [ordered]@{schema_version='hwpx-agent.crossref-existing-owner-readback/v1';state=$row.State;phase=$row.Phase;
            error_code=$row.ErrorCode;HRESULT=$row.HResult;window_handle_type=$row.HandleType;candidate_names=$row.CandidateNames;
            enumeration_complete=$row.EnumerationComplete;references_released=$row.ReferencesReleased;exact_kernel_window_version=$row.ExactKernelWindowVersion;
            expected_process_id=29824;same_existing_kernel_process_after=$same;activation_invoked=$false;Hancom_started_or_closed=$false;
            document_or_permission_action_invoked=$false;native_startup_qualified=$false} | ConvertTo-Json -Compress
        if(-not $same -or -not $row.ReferencesReleased){exit 2}
    }finally{$process.Dispose()}
}catch{
    $e=$_.Exception.GetBaseException();$code=[string]$e.Message
    if($code -cnotmatch '^P09_XREF_ROT_[A-Z_]{1,120}$'){$code='P09_XREF_ROT_READBACK_FAILURE_NO_RAW_VALUES'}
    [ordered]@{state='FAILED_EXISTING_OWNER_READONLY_INSPECTION';phase=$phase;error_code=$code;
        HRESULT=[BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$e.HResult),0).ToString('X8');
        activation_invoked=$false;Hancom_started_or_closed=$false;document_or_permission_action_invoked=$false} | ConvertTo-Json -Compress
    exit 2
}
