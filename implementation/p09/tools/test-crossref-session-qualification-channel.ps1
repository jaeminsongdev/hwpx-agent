# New transport/source models only. No worker, Native, ROT or COM call.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_SESSION_MODELS_ONLY'}
foreach ($name in @('crossref-owned-active-source','crossref-host-channel','crossref-preassigned-host-channel','crossref-session-qualification-channel')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function New-SessionModelDescriptor {
    return [ordered]@{profile='hwpx-agent.private.crossref-preassigned-session-scope/v1';case_index=1;session_label='save';
        process_id=1001;session_id=1;created_at_utc='2022-06-18T04:26:40.0000001Z';
        executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';source='current_exact_preassigned_process_handle';
        COM_owner_bound=$false;native_execution_authorized=$false;native_startup_qualified=$false;P09_complete=$false}
}
function New-SessionModelReply([int]$Sequence,[bool]$Ack,$Descriptor) {
    return [ordered]@{schema_version='hwpx-agent.private.crossref-session-qualification-response/v1';sequence=$Sequence;acknowledged=$Ack;
        error_code=if ($Ack) {$null} else {'XREF_SESSION_QUALIFICATION_MODEL_DENIED'};owner_descriptor=$Descriptor;
        native_execution_authorized=$false;native_startup_qualified=$false;p09_complete=$false}
}
function Assert-SessionModelRejected([scriptblock]$Body) {
    $caught=$false;try {[void](& $Body)} catch {$caught=$true};Assert-P09XrefBinding $caught 'SESSION_MODEL_EXPECTED_REJECTION'
}
function Invoke-SessionModelOne([string]$Raw) {
    $reader=[IO.StringReader]::new($Raw+"`n");$writer=[IO.StringWriter]::new()
    try {$c=New-P09XrefSessionQualificationChannel $reader $writer;return Invoke-P09XrefSessionQualificationMessage $c 'ready' -WorkerIdentity ([ordered]@{})}
    finally {$reader.Dispose();$writer.Dispose()}
}
try {
    $d=New-SessionModelDescriptor;$raw=New-SessionModelReply 1 $true $d | ConvertTo-Json -Depth 8 -Compress
    $result=Invoke-SessionModelOne $raw;Assert-P09XrefBinding ($result.process_id -eq 1001 -and -not $result.COM_owner_bound) 'SESSION_MODEL_READY_DATA_ONLY'
    [Console]::WriteLine('test session_channel::ready_descriptor_data_not_authority ... ok')
    $lines=@($raw,((New-SessionModelReply 2 $true $null)|ConvertTo-Json -Depth 8 -Compress),((New-SessionModelReply 3 $true $null)|ConvertTo-Json -Depth 8 -Compress))
    $reader=[IO.StringReader]::new(($lines -join "`n")+"`n");$writer=[IO.StringWriter]::new()
    try {
        $c=New-P09XrefSessionQualificationChannel $reader $writer
        [void](Invoke-P09XrefSessionQualificationMessage $c 'ready' -WorkerIdentity ([ordered]@{}))
        [void](Invoke-P09XrefSessionQualificationMessage $c 'admit_owner' -Owner ([ordered]@{identity=[ordered]@{};window=[pscustomobject]@{WindowHandle=123}}))
        [void](Invoke-P09XrefSessionQualificationMessage $c 'closed' -Cleanup ([ordered]@{}))
        Assert-P09XrefBinding ($c.sequence -eq 3 -and $c.finish_attempted -and $c.phase -ceq 'finished' -and $null -eq $c.pending_descriptor) 'SESSION_MODEL_THREE_PHASE_ORDER'
    } finally {$reader.Dispose();$writer.Dispose()}
    [Console]::WriteLine('test session_channel::three_phase_transport_only ... ok')
    $deny=New-SessionModelReply 1 $false $null
    $reader=[IO.StringReader]::new(($deny|ConvertTo-Json -Depth 8 -Compress)+"`n"+((New-SessionModelReply 2 $true $null)|ConvertTo-Json -Depth 8 -Compress)+"`n")
    $writer=[IO.StringWriter]::new()
    try {
        $c=New-P09XrefSessionQualificationChannel $reader $writer
        Assert-SessionModelRejected {Invoke-P09XrefSessionQualificationMessage $c 'ready' -WorkerIdentity ([ordered]@{})}
        [void](Invoke-P09XrefSessionQualificationMessage $c 'failed' -ErrorCode 'P09_XREF_BIND_MODEL_FAILED' -Cleanup ([ordered]@{}))
        Assert-P09XrefBinding ($c.sequence -eq 2 -and $c.failed -and $c.finish_attempted) 'SESSION_MODEL_FAILURE_FINISH_ONCE'
    } finally {$reader.Dispose();$writer.Dispose()}
    [Console]::WriteLine('test session_channel::denial_allows_one_failed_finish ... ok')
    $reader=[IO.StringReader]::new('');$writer=[IO.StringWriter]::new()
    try {$c=New-P09XrefSessionQualificationChannel $reader $writer;Assert-SessionModelRejected {Invoke-P09XrefSessionQualificationMessage $c 'closed' -Cleanup ([ordered]@{})}
        Assert-P09XrefBinding ($writer.ToString().Length -eq 0) 'SESSION_MODEL_EARLY_FINISH_NO_WIRE'}
    finally {$reader.Dispose();$writer.Dispose()}
    [Console]::WriteLine('test session_channel::early_closed_rejected ... ok')
    Assert-SessionModelRejected {Invoke-SessionModelOne ($raw.Replace('"acknowledged":true','"acknowledged":true,"acknowl\u0065dged":false'))}
    [Console]::WriteLine('test session_channel::escaped_duplicate_rejected ... ok')
    Assert-SessionModelRejected {Invoke-SessionModelOne ($raw.Replace('"native_startup_qualified":false','"native_startup_qualified":true'))}
    [Console]::WriteLine('test session_channel::qualification_flag_cannot_grant_authority ... ok')
    Assert-SessionModelRejected {Invoke-SessionModelOne ($raw.Replace('"session_label":"save"','"session_label":"reopen"'))}
    [Console]::WriteLine('test session_channel::different_descriptor_context_rejected ... ok')
    $extra=New-SessionModelReply 1 $true $d;$extra['approved']=$true
    Assert-SessionModelRejected {Invoke-SessionModelOne ($extra|ConvertTo-Json -Depth 8 -Compress)}
    [Console]::WriteLine('test session_channel::unknown_reply_key_rejected ... ok')
    $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'run-crossref-session-qualification-worker.ps1'),[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $ast.ParamBlock.Parameters.Count -eq 1 -and
        $ast.ParamBlock.Parameters[0].Name.VariablePath.UserPath -ceq 'QualifySessionOnly') 'SESSION_MODEL_CLOSED_WORKER_PARAMETER'
    $methods=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.InvokeMemberExpressionAst]},$true) | ForEach-Object {$_.Member.Extent.Text})
    Assert-P09XrefBinding (@($methods | Where-Object {$_ -cin @('Open','Save','SaveAs','Execute','RegisterModule','Quit')}).Count -eq 0) 'SESSION_MODEL_NO_DOCUMENT_OR_ACTIVATION_METHODS'
    [Console]::WriteLine('test session_channel::worker_source_closed_no_document_actions ... ok')
    $definitions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Get-SessionWorkerCleanup'},$false))
    Assert-P09XrefBinding ($definitions.Count -eq 1) 'SESSION_MODEL_CLEANUP_HELPER_INVENTORY'
    . ([scriptblock]::Create($definitions[0].Extent.Text))
    $observed=Get-SessionWorkerCleanup $null
    Assert-P09XrefBinding ($observed.remaining_owned_process_count -eq -1 -and -not $observed.quit_invoked -and
        -not $observed.close_without_dirty_prompt_returned -and -not $observed.reference_release_returned) 'SESSION_MODEL_ABSENCE_NOT_SUCCESS'
    [Console]::WriteLine('test session_channel::absent_owner_never_cleanup_success ... ok')
    [Console]::WriteLine('test result: ok. 10 passed; 0 failed; 0 ignored; models_and_source_only_not_native')
} catch {
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_SESSION_CHANNEL_MODELS_FAILED_NO_RAW_VALUES'}
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
