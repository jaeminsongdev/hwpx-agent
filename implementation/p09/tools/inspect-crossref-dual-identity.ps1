# Closed self-process inspection only, never a Hancom/COM admission.
[CmdletBinding()]
param([switch]$InspectOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $InspectOnly) {throw 'P09_XREF_DUAL_INSPECT_ONLY'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-dual-owner-identity.ps1')
$lease=$null
try {
    Initialize-P09XrefHeldIdentityBridge
    Initialize-P09XrefHeldIdentityBridge # Same process-owned type; no second compile.
    $lease=[P09XrefHeldIdentity]::new($PID)
    $before=$lease.ReadCurrentProcessOnly()
    $rows=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID))
    Assert-P09XrefBinding ($rows.Count -eq 1 -and [int]$rows[0].ProcessId -eq $PID -and
        [int]$rows[0].SessionId -eq $before.SessionId -and $null -ne $rows[0].CreationDate) 'DUAL_INSPECT_OWN_CIM_ONLY'
    $compat=[ordered]@{process_id=[int]$PID;session_id=[int]$rows[0].SessionId;
        created_at_utc=([datetime]$rows[0].CreationDate).ToUniversalTime().ToString('o')}
    $after=$lease.ReadCurrentProcessOnly()
    $record=New-P09XrefDualIdentityRecord $compat 'current_process_cim_only' $before $after
    [Console]::WriteLine(($record | ConvertTo-Json -Depth 6 -Compress));[Console]::Out.Flush()
    # Bounded acknowledgement keeps this same process alive for the parent's
    # independent handle query. No acknowledgement can enable native operations.
    $reply=[Text.StringBuilder]::new()
    for ($i=0;$i -le 64;$i++) {
        $ch=[Console]::In.Read()
        Assert-P09XrefBinding ($ch -ge 0) 'DUAL_INSPECT_PARENT_EOF'
        if ($ch -eq 10) {break}
        [void]$reply.Append([char]$ch)
    }
    Assert-P09XrefBinding ($reply.ToString().TrimEnd([char]13) -ceq 'P09_XREF_DUAL_INSPECTION_DONE') 'DUAL_INSPECT_FIXED_ACK_ONLY'
} catch {
    [Console]::Error.WriteLine('P09_XREF_DUAL_INSPECT_FAILED_NO_RAW_VALUES');exit 2
} finally {if ($null -ne $lease) {$lease.Dispose()}}
