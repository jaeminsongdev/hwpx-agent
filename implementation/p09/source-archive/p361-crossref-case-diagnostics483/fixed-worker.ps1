# Private full-eight worker. Host must finish the current live session/source
# qualification before its one-use release. No subset, retry or COM activation.
[CmdletBinding()]
param([switch]$FixedEightAfterSession)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$lease=$null;$states=[Collections.Generic.List[object]]::new();$result=$null;$phase='closed_mode'
try {
    if (-not $FixedEightAfterSession) {throw 'P09_XREF_BIND_FULL_WORKER_FIXED_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
        'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch',
        'crossref-dual-owner-identity','crossref-canonical-runtime','crossref-preassigned-host-channel',
        'crossref-preassigned-owner','crossref-preassigned-case-ports','crossref-preassigned-controller')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    $phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefPreassignedCasePorts
    Initialize-P09XrefFrozenWindowBridge;Initialize-P09XrefHeldIdentityBridge;Assert-P09XrefOriginalOwnerFunction
    $lease=New-P09XrefProbeLease
    $self=[P09CrossrefExisting.ExistingOwner]::InspectCurrentProcessOnly()
    $expected=Join-Path ([Environment]::GetFolderPath('Windows')) 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    Assert-P09XrefBinding ([string]::Equals($self.Image,$expected,[StringComparison]::OrdinalIgnoreCase)) 'FULL_WORKER_FIXED_IMAGE'
    $item=Get-Item -LiteralPath $expected -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le 4194304 -and
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'FULL_WORKER_IMAGE_BOUNDARY'
    $identity=[ordered]@{process_id=[int]$self.Pid;session_id=[int]$self.Session;
        created_at_utc=[datetime]::FromFileTimeUtc($self.Birth).ToString('o');executable_sha256=(Get-P09XrefFreshDigest ([IO.File]::ReadAllBytes($expected)))}
    $ready=[ordered]@{schema_version='hwpx-agent.private.crossref-fixed-worker-ready/v1';worker_identity=$identity}
    [Console]::WriteLine(($ready|ConvertTo-Json -Depth 5 -Compress));[Console]::Out.Flush()
    $channel=New-P09XrefPreassignedHostChannel ([Console]::In) ([Console]::Out)
    $phase='current_live_release';$raw=Read-P09XrefBoundedHostReply $channel;$reply=$raw|ConvertFrom-Json
    $keys=@('schema_version','acknowledged','error_code','native_execution_authorized','p09_complete')
    Assert-P09XrefBinding (@($reply.PSObject.Properties).Count -eq 5) 'FULL_WORKER_RELEASE_SCHEMA'
    foreach ($key in $keys) {Assert-P09XrefBinding ($key -cin @($reply.PSObject.Properties.Name)) 'FULL_WORKER_RELEASE_KEY'}
    Assert-P09XrefBinding ($reply.schema_version -ceq 'hwpx-agent.private.crossref-fixed-worker-release/v1' -and
        $reply.acknowledged -is [bool] -and $reply.acknowledged -and $null -eq $reply.error_code -and
        $reply.native_execution_authorized -is [bool] -and -not $reply.native_execution_authorized -and
        $reply.p09_complete -is [bool] -and -not $reply.p09_complete) 'FULL_WORKER_CURRENT_RELEASE_REQUIRED'
    $canonical=[ordered]@{};foreach ($key in $keys) {$canonical[$key]=$reply.$key}
    Assert-P09XrefBinding ($raw -ceq ($canonical|ConvertTo-Json -Depth 5 -Compress)) 'FULL_WORKER_RELEASE_CANONICAL'
    $phase='fixed_eight';$batch=[ordered]@{}
    Invoke-P09XrefPreassignedFixedHostBatch $channel $lease $batch $states
    $result=[ordered]@{state=if ($batch.completed_callback_cases -eq 8) {'fixed_eight_callbacks_returned_semantics_unqualified'} else {'fixed_eight_callbacks_failed_or_partial'};
        phase=$phase;error_code=$batch.error_code;planned_cases=8;callback_cases=$batch.cases.Count;
        completed_callback_cases=$batch.completed_callback_cases;stopped_case_index=$batch.stopped_case_index;host_messages=$channel.sequence}
} catch {
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_FULL_WORKER_FAILED_NO_RAW_VALUES'}
    $result=[ordered]@{state='fixed_eight_worker_failed_or_uncertain';phase=$phase;error_code=$code;planned_cases=8;completed_callback_cases=0}
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
$retained=@($states|Where-Object {$null -ne $_.owner -and -not $_.owner.preassigned_closed}).Count
$result['schema_version']='hwpx-agent.private.crossref-fixed-worker-result/v1';$result['retained_live_or_uncertain_owners']=$retained
$result['probe_lease_closed']=($null -eq $lease -or $lease.closed)
$result['native_execution_authorized']=$false;$result['native_startup_qualified']=$false;$result['p09_complete']=$false
$result|ConvertTo-Json -Depth 5 -Compress
# Keep uncertain owners reachable until the exact host has observed Native exit
# and sends EOF. No new command, Close/Quit retry, finalizer pressure or force kill.
if ($retained -gt 0) {[void][Console]::In.Read()}
if ($result.state -cne 'fixed_eight_callbacks_returned_semantics_unqualified') {exit 2}
