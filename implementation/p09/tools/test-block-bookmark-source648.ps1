# New channel/flow functions on models. No Native or real artifact IO.
[CmdletBinding()]
param([switch]$ModelsOnly,[switch]$DecoderProbeOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'MODELS_ONLY_REQUIRED'}
if ($DecoderProbeOnly) {
    $v='{"sequence":1}'|ConvertFrom-Json
    [ordered]@{state='OBSERVED_JSON_NUMBER_TYPE_ONLY';sequence_type=$v.sequence.GetType().FullName;actual_native_started=$false}|ConvertTo-Json -Compress
    exit 0
}
foreach ($name in @('crossref-owned-active-source','crossref-preassigned-host-channel','block-bookmark-source645-ports','block-bookmark-source648-channel','block-bookmark-source648-flow')) {. (Join-Path $PSScriptRoot ($name+'.ps1'))}
$script:run=0;$script:failed=[Collections.Generic.List[string]]::new()
function Assert-Model([bool]$V) {if (-not $V) {throw 'MODEL_ASSERTION'}}
function Model([string]$Name,[scriptblock]$Body) {$script:run++;try {[void](& $Body)}catch {[void]$script:failed.Add($Name)}}
function Descriptor([string]$Label) {
    return [ordered]@{profile='hwpx-agent.private.crossref-preassigned-session-scope/v1';case_index=1;session_label=$Label;
        process_id=123;session_id=1;created_at_utc='2026-10-23T00:00:00.0000001Z';
        executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';source='current_exact_preassigned_process_handle';
        COM_owner_bound=$false;native_execution_authorized=$false;native_startup_qualified=$false;P09_complete=$false}
}
function Channel {
    $script:replyMode='ok';$script:creationLabel=$null
    return New-P09XrefPreassignedHostChannel ([IO.StringReader]::new('')) ([IO.StringWriter]::new())
}
function Read-P09XrefBoundedHostReply($Channel) {
    $d=if ($null -ne $script:creationLabel) {Descriptor $script:creationLabel}else{$null}
    $ack=($script:replyMode -cne 'deny')
    $reply=[ordered]@{schema_version='hwpx-agent.private.block-bookmark-source647-response/v1';sequence=$Channel.sequence;case_index=1;
        acknowledged=$ack;error_code=$(if ($ack) {$null}else{'STOP_CPU_LIMIT'});owner_descriptor=$d;native_execution_authorized=$false;p09_complete=$false}
    if ($script:replyMode -ceq 'authority') {$reply.native_execution_authorized=$true}
    if ($script:replyMode -ceq 'sequence') {$reply.sequence++}
    if ($script:replyMode -ceq 'keys') {$reply['extra']=$true}
    $raw=$reply|ConvertTo-Json -Depth 8 -Compress
    if ($script:replyMode -ceq 'noncanonical') {$raw=' '+$raw}
    return $raw
}
function Denied([scriptblock]$Body,[string]$Code) {
    $ok=$false;try {[void](& $Body)}catch {$ok=$_.Exception.GetBaseException().Message -ceq $Code};Assert-Model $ok
}
Model 'checkpoint_frame_matches_fixed_schema' {
    $c=Channel;[void](Invoke-P09Block648Message $c checkpoint -Step prepare_slot)
    $v=$c.output.ToString()|ConvertFrom-Json
    Assert-Model ($v.schema_version -ceq 'hwpx-agent.private.block-bookmark-source647-request/v1' -and $v.sequence -eq 1 -and $v.case_index -eq 1 -and $v.step -ceq 'prepare_slot')
}
Model 'creation_descriptor_is_same_pending_value' {
    $c=Channel;$script:creationLabel='save';$d=Invoke-P09Block648Message $c checkpoint -Step create_save_session
    Assert-Model ([object]::ReferenceEquals($d,$c.pending_descriptor))
}
Model 'unknown_pulse_before_io' {
    $c=Channel;Denied {Invoke-P09Block648Message $c pulse -Phase bookmark_execute -RangeIndex 9} 'P09_BLOCK645_CHANNEL_FIXED_PULSE'
    Assert-Model ($c.output.ToString().Length -eq 0 -and $c.failed)
}
foreach ($mode in @('authority','sequence','keys','noncanonical')) {
    Model ('reply_'+$mode) {
        $c=Channel;$script:replyMode=$mode
        $code=if ($mode -ceq 'keys') {'P09_BLOCK645_CHANNEL_REPLY_KEYS'}elseif ($mode -ceq 'noncanonical') {'P09_BLOCK645_CHANNEL_CANONICAL_REPLY'}else{'P09_BLOCK645_CHANNEL_REPLY_BINDING'}
        Denied {Invoke-P09Block648Message $c checkpoint -Step prepare_slot} $code;Assert-Model $c.failed
    }
}
Model 'host_denial_allows_only_one_failed_finish' {
    $c=Channel;$script:replyMode='deny'
    Denied {Invoke-P09Block648Message $c checkpoint -Step prepare_slot} 'P09_XREF_BIND_BLOCK648_HOST_DENIED'
    $script:replyMode='ok';[void](Invoke-P09Block648Message $c finish -CaseStatus failed)
    Denied {Invoke-P09Block648Message $c finish -CaseStatus failed} 'P09_BLOCK645_CHANNEL_STOP_OR_FINISH'
    Assert-Model ($c.sequence -eq 2 -and $c.finish_attempted)
}
Model 'unexpected_descriptor_rejected' {
    $c=Channel;$script:creationLabel='save'
    Denied {Invoke-P09Block648Message $c checkpoint -Step prepare_slot} 'P09_BLOCK645_CHANNEL_NO_UNEXPECTED_DESCRIPTOR'
}

# From here only model the external owner and filesystem ports, not the body
# under test. This intentionally does not prove real SaveAs/Open/Close effects.
function Assert-P09XrefPreassignedOwnerAnchor {}
function Test-P58Owner {return $true}
function Assert-P09XrefExclusiveDestination {}
function Get-P09Prepared631Pin {return [ordered]@{bytes=1;sha256=('0'*64)}}
function State {
    $script:saves=0;$script:saveReturns=$true;$script:hostCalls=0;$script:seedCalls=0;$script:ranges=8
    $doc=[pscustomobject]@{}
    $doc|Add-Member ScriptMethod SaveAs {param($Path,$Format,$Options)
        $script:saves++;Assert-Model ($Format -ceq 'HWPX' -and $Options -ceq '')
        return $script:saveReturns
    }
    return [ordered]@{owner=[ordered]@{identity=@{};hwp=[pscustomobject]@{PageCount=[int]1}};document=$doc;failed=$false;cursor=0;
        current_descriptor=$null;preassigned_channel=$null;run='D:\MODELED-NOT-AN-OUTPUT';created=@{sha256=('0'*64)};
        completed_ranges=0;cleanup_error_code=$null;trace=[ordered]@{phase=$null;artifacts=[ordered]@{}}}
}
function Invoke-P09Block648Message {$script:hostCalls++;return $null}
function Invoke-P09Block645Seed {$script:seedCalls++}
function Invoke-P09Block645Ranges($State) {$State.completed_ranges=$script:ranges}
Model 'wrong_step_no_host_no_retry' {$s=State;Denied {Invoke-P09Block648Step $s created_save} 'P09_BLOCK645_STEP_NO_RETRY';Assert-Model ($script:hostCalls -eq 0)}
Model 'seed_dispatch_once' {$s=State;$s.cursor=3;Invoke-P09Block648Step $s seed_document;Assert-Model ($script:seedCalls -eq 1 -and $s.cursor -eq 4)}
Model 'must_return_all_eight_ranges' {$s=State;$s.cursor=4;$script:ranges=7;Denied {Invoke-P09Block648Step $s create_bookmarks} 'P09_BLOCK645_EIGHT_RANGES_REQUIRED';Assert-Model $s.failed}
Model 'source_save_exact_private_name' {$s=State;$pin=Save-P09Block648Artifact $s created.hwpx;Assert-Model ($script:saves -eq 1 -and $pin.bytes -eq 1 -and $s.trace.artifacts.Count -eq 1)}
Model 'source_save_denied_name_before_effect' {$s=State;Denied {Save-P09Block648Artifact $s source.hwpx} 'P09_BLOCK645_FIXED_SOURCE_OUTPUT';Assert-Model ($script:saves -eq 0)}
Model 'source_save_false_no_artifact_success' {$s=State;$script:saveReturns=$false;Denied {Save-P09Block648Artifact $s created.hwpx} 'P09_BLOCK645_SOURCE_SAVE_EFFECT_UNKNOWN';Assert-Model ($script:saves -eq 1 -and $s.trace.artifacts.Count -eq 0)}
Model 'image_page_scope_before_io' {$s=State;$s.owner.hwp.PageCount=9;Denied {Export-P09Block648Image $s created} 'P09_BLOCK645_SOURCE_IMAGE_SINGLE_PAGE'}
Model 'private_errors_not_disclosed' {
    Assert-Model ((Get-P09Block648SafeCode ([pscustomobject]@{Exception=[Exception]::new('PRIVATE')})) -ceq 'P09_XREF_BIND_BLOCK648_FAILURE_NO_RAW_VALUES')
    Assert-Model ((Get-P09Block648SafeCode ([pscustomobject]@{Exception=[Exception]::new('P09_BLOCK645_BOOKMARK_SELECT_FAILED')})) -ceq 'P09_XREF_BIND_BLOCK648_PORT_BOOKMARK_SELECT_FAILED')
}
[ordered]@{run=$script:run;errors=0;failures=$script:failed.Count;failed_tests=$script:failed.ToArray();skipped=0;
    steps=@(Get-P09Block648Steps);actual_native_started=$false}|ConvertTo-Json -Depth 5 -Compress
if ($script:failed.Count -ne 0) {exit 2}
