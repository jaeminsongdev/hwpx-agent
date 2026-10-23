# Pure record models only. No Add-Type, process/window/COM query or native action.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_DUAL_MODELS_ONLY'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-dual-owner-identity.ps1')
$compat=[ordered]@{process_id=135;session_id=1;created_at_utc='2026-10-17T00:00:00.0000000Z';
    executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';window_handle_binds_exact_process=$true}
$original=$compat | ConvertTo-Json -Compress
$before=[pscustomobject]@{ProcessId=135;SessionId=1;Birth100ns=[datetime]::Parse('2026-10-17T00:00:00.0000006Z').ToUniversalTime().ToFileTimeUtc();
    Image='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe';WindowVerified=$true}
$after=[pscustomobject]@{ProcessId=$before.ProcessId;SessionId=$before.SessionId;Birth100ns=$before.Birth100ns;
    Image=$before.Image;WindowVerified=$before.WindowVerified}
$record=New-P09XrefDualIdentityRecord $compat 'original_p58_identity' $before $after
Assert-P09XrefBinding (($compat | ConvertTo-Json -Compress) -ceq $original -and
    $record.kernel_identity.created_at_utc -ceq '2026-10-17T00:00:00.0000006Z' -and
    $record.compatibility_identity.created_at_utc -ceq $compat.created_at_utc) 'DUAL_MODEL_CLOCKS_SEPARATE_UNMODIFIED'
$after.Birth100ns++
$caught=$null;try {[void](New-P09XrefDualIdentityRecord $compat 'original_p58_identity' $before $after)} catch {$caught=$_.Exception.Message}
Assert-P09XrefBinding ($caught -ceq 'P09_XREF_BIND_DUAL_SAME_HELD_KERNEL_IDENTITY') 'DUAL_MODEL_ONE_TICK_DRIFT_REJECTED'
[ordered]@{state='two_pure_dual_record_models_pass_not_native';passed=2;failed=0;model_record=$record;
    model_only=$true;actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Depth 7 -Compress
