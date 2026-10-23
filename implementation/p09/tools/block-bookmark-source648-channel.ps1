# Fixed one-document wire only. Imported after the original owner/channel library.
Set-StrictMode -Version Latest
function Get-P09Block648Steps {
    return @('prepare_slot','create_save_session','bind_blank_document','seed_document','create_bookmarks',
        'created_save','created_image','created_bind','save_ready_close','save_session_close',
        'create_reopen_session','fresh_created_open','reopened_save','reopened_image','reopen_session_close','final_source_check')
}
function Invoke-P09Block648Message {
    param($Channel,[ValidateSet('checkpoint','admit_owner','pulse','finish')][string]$Operation,
        [string]$Step,$Owner,[string]$CaseStatus,[string]$Phase,[int]$RangeIndex)
    Assert-P09Block645 ($Channel.case_index -eq 1 -and -not $Channel.finish_attempted -and
        (-not $Channel.failed -or ($Operation -ceq 'finish' -and $CaseStatus -ceq 'failed'))) 'CHANNEL_STOP_OR_FINISH'
    if ($Operation -ceq 'finish') {$Channel.finish_attempted=$true}
    $Channel.sequence++
    Assert-P09Block645 ($Channel.sequence -le 64) 'CHANNEL_SEQUENCE_BOUND'
    $request=[ordered]@{schema_version='hwpx-agent.private.block-bookmark-source647-request/v1';sequence=$Channel.sequence;case_index=1;operation=$Operation}
    $creation=($Operation -ceq 'checkpoint' -and $Step -cin @('create_save_session','create_reopen_session'))
    try {
        switch -CaseSensitive ($Operation) {
            'checkpoint' {
                Assert-P09Block645 ($Step -cin (Get-P09Block648Steps) -and $null -eq $Channel.pending_descriptor) 'CHANNEL_FIXED_STEP'
                $request.step=$Step
            }
            'pulse' {
                $seed=($RangeIndex -eq 0 -and $Phase -cin @('seed_prepare','seed_execute','seed_returned'))
                $range=($RangeIndex -ge 1 -and $RangeIndex -le 8 -and $Phase -cin @('bookmark_prepare','bookmark_select','bookmark_execute','bookmark_returned'))
                Assert-P09Block645 (($seed -or $range) -and $null -eq $Channel.pending_descriptor) 'CHANNEL_FIXED_PULSE'
                $request.phase=$Phase;$request.range_index=$RangeIndex
            }
            'admit_owner' {
                $d=$Channel.pending_descriptor
                Assert-P09Block645 ($null -ne $d -and $Owner.identity.process_id -eq $d.process_id -and
                    $Owner.identity.session_id -eq $d.session_id -and $Owner.identity.created_at_utc -ceq $d.created_at_utc) 'CHANNEL_PENDING_OWNER'
                $request.identity=$Owner.identity;$request.window_handle=[int]$Owner.window.WindowHandle
            }
            'finish' {
                Assert-P09Block645 ($CaseStatus -cin @('returned','failed')) 'CHANNEL_FINISH_STATUS'
                $request.case_status=$CaseStatus
            }
        }
        $wire=$request|ConvertTo-Json -Depth 8 -Compress
        Assert-P09Block645 ([Text.Encoding]::UTF8.GetByteCount($wire) -le 4096) 'CHANNEL_WIRE_BOUND'
        $Channel.output.WriteLine($wire);$Channel.output.Flush()
        $text=Read-P09XrefBoundedHostReply $Channel;$reply=$text|ConvertFrom-Json
        $keys=@('schema_version','sequence','case_index','acknowledged','error_code','owner_descriptor','native_execution_authorized','p09_complete')
        Assert-P09Block645 (@($reply.PSObject.Properties).Count -eq $keys.Count) 'CHANNEL_REPLY_KEYS'
        foreach ($key in $keys) {Assert-P09Block645 ($key -cin @($reply.PSObject.Properties.Name)) 'CHANNEL_REPLY_KEY'}
        Assert-P09Block645 ($reply.schema_version -ceq 'hwpx-agent.private.block-bookmark-source647-response/v1' -and
            $reply.sequence -is [int] -and $reply.sequence -eq $Channel.sequence -and $reply.case_index -is [int] -and $reply.case_index -eq 1 -and
            $reply.acknowledged -is [bool] -and $reply.native_execution_authorized -is [bool] -and -not $reply.native_execution_authorized -and
            $reply.p09_complete -is [bool] -and -not $reply.p09_complete -and
            (($reply.acknowledged -and $null -eq $reply.error_code) -or (-not $reply.acknowledged -and $reply.error_code -is [string] -and
                $reply.error_code -cmatch '^(XREF_|P09_BLOCK|P09_XREF_|P58_|STOP_)[A-Z0-9_]{1,140}$'))) 'CHANNEL_REPLY_BINDING'
        $descriptor=$null
        if ($reply.acknowledged -and $creation) {
            $label=if ($Step -ceq 'create_save_session') {'save'}else{'reopen'}
            $descriptor=Assert-P09XrefPreassignedDescriptor $reply.owner_descriptor 1 $label
        } else {Assert-P09Block645 ($null -eq $reply.owner_descriptor) 'CHANNEL_NO_UNEXPECTED_DESCRIPTOR'}
        $canonical=[ordered]@{};foreach ($key in $keys) {$canonical[$key]=$reply.$key};$canonical.owner_descriptor=$descriptor
        Assert-P09Block645 ($text -ceq ($canonical|ConvertTo-Json -Depth 8 -Compress)) 'CHANNEL_CANONICAL_REPLY'
        if (-not $reply.acknowledged) {$Channel.error_code=$reply.error_code;throw 'P09_XREF_BIND_BLOCK648_HOST_DENIED'}
        if ($creation) {$Channel.pending_descriptor=$descriptor}
        if ($Operation -ceq 'admit_owner') {$Channel.pending_descriptor=$null}
        if ($Operation -ceq 'finish') {$Channel.case_index=2}
        return $descriptor
    } catch {$Channel.failed=$true;throw}
}
function Invoke-P09XrefPreassignedHostMessage {
    param($Channel,[int]$CaseIndex,[string]$Operation,[string]$Step,$Owner,[string]$CaseStatus)
    # Existing Connect/Admit owner functions call this private, worker-local wire.
    Assert-P09Block645 ($CaseIndex -eq 1) 'CHANNEL_ONE_SOURCE_ONLY'
    return Invoke-P09Block648Message $Channel $Operation -Step $Step -Owner $Owner -CaseStatus $CaseStatus
}
