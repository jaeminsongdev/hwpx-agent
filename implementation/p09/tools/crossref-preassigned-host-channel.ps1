# Private v2 descriptor channel only. No activation, process creation or native CLI.
Set-StrictMode -Version Latest

function Assert-P09XrefPreassignedDescriptor($Value,[int]$CaseIndex,[string]$Label) {
    $keys=@('profile','case_index','session_label','process_id','session_id','created_at_utc','executable_sha256','source',
        'COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete')
    Assert-P09XrefBinding ($null -ne $Value -and $Value -is [pscustomobject] -and @($Value.PSObject.Properties).Count -eq $keys.Count) 'V2_DESCRIPTOR_SCHEMA'
    foreach ($key in $keys) {Assert-P09XrefBinding ($key -cin @($Value.PSObject.Properties.Name)) 'V2_DESCRIPTOR_KEY'}
    Assert-P09XrefBinding ($Value.profile -ceq 'hwpx-agent.private.crossref-preassigned-session-scope/v1' -and
        $Value.case_index -is [int] -and $Value.case_index -eq $CaseIndex -and $Value.session_label -ceq $Label -and
        $Label -cin @('save','reopen') -and $Value.source -ceq 'current_exact_preassigned_process_handle') 'V2_DESCRIPTOR_CONTEXT'
    Assert-P09XrefBinding ($Value.process_id -is [int] -and $Value.process_id -gt 0 -and
        $Value.session_id -is [int] -and $Value.session_id -ge 0 -and
        $Value.executable_sha256 -ceq '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce' -and
        $Value.created_at_utc -is [string] -and $Value.created_at_utc -cmatch '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}Z$') 'V2_DESCRIPTOR_IDENTITY'
    [void][datetime]::ParseExact($Value.created_at_utc,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)
    foreach ($key in @('COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete')) {
        Assert-P09XrefBinding ($Value.$key -is [bool] -and -not $Value.$key) 'V2_DESCRIPTOR_NO_AUTHORITY'
    }
    $canonical=[ordered]@{};foreach ($key in $keys) {$canonical[$key]=$Value.$key};return $canonical
}

function New-P09XrefPreassignedHostChannel {
    param([Parameter(Mandatory)][IO.TextReader]$InputReader,[Parameter(Mandatory)][IO.TextWriter]$OutputWriter)
    return [ordered]@{input=$InputReader;output=$OutputWriter;sequence=0;case_index=1;failed=$false;
        finish_attempted=$false;error_code=$null;cleanup_error_code=$null;pending_descriptor=$null}
}

function Invoke-P09XrefPreassignedHostMessage {
    param([Parameter(Mandatory)]$Channel,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][ValidateSet('checkpoint','admit_owner','finish')][string]$Operation,
        [string]$Step,$Owner,[ValidateSet('returned','failed')][string]$CaseStatus)
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8 -and $Channel.case_index -eq $CaseIndex -and
        -not $Channel.finish_attempted) 'V2_CASE_ORDER_OR_FINISHED'
    Assert-P09XrefBinding (-not $Channel.failed -or ($Operation -ceq 'finish' -and $CaseStatus -ceq 'failed')) 'V2_STOP_LATCHED'
    if ($Operation -ceq 'finish') {$Channel.finish_attempted=$true}
    $Channel.sequence++
    $request=[ordered]@{schema_version='hwpx-agent.private.crossref-preassigned-host-request/v2';sequence=$Channel.sequence;case_index=$CaseIndex;operation=$Operation}
    $creation=($Operation -ceq 'checkpoint' -and $Step -cin @('create_save_session','create_reopen_session'))
    try {
        switch -CaseSensitive ($Operation) {
            'checkpoint' {
                Assert-P09XrefBinding ($Step -cin (Get-P09XrefCaseFlowSteps) -and $null -eq $Channel.pending_descriptor) 'V2_FIXED_STEP_NO_PENDING_OWNER'
                $request.step=$Step
            }
            'admit_owner' {
                $d=$Channel.pending_descriptor
                Assert-P09XrefBinding ($null -ne $d -and $null -ne $Owner.identity -and $null -ne $Owner.window -and
                    $Owner.identity.process_id -eq $d.process_id -and $Owner.identity.session_id -eq $d.session_id -and
                    $Owner.identity.created_at_utc -ceq $d.created_at_utc) 'V2_EXACT_PENDING_CANONICAL_OWNER'
                $request.identity=$Owner.identity;$request.window_handle=[int]$Owner.window.WindowHandle
            }
            'finish' {$request.case_status=$CaseStatus}
        }
        $wire=$request | ConvertTo-Json -Depth 8 -Compress
        Assert-P09XrefBinding ([Text.Encoding]::UTF8.GetByteCount($wire) -le 4096) 'V2_REQUEST_BYTES'
        $Channel.output.WriteLine($wire);$Channel.output.Flush()
        $text=Read-P09XrefBoundedHostReply $Channel;$reply=$text | ConvertFrom-Json
        $keys=@('schema_version','sequence','case_index','acknowledged','error_code','owner_descriptor','native_execution_authorized','p09_complete')
        Assert-P09XrefBinding (@($reply.PSObject.Properties).Count -eq $keys.Count) 'V2_REPLY_SCHEMA'
        foreach ($key in $keys) {Assert-P09XrefBinding ($key -cin @($reply.PSObject.Properties.Name)) 'V2_REPLY_KEY'}
        Assert-P09XrefBinding ($reply.schema_version -ceq 'hwpx-agent.private.crossref-preassigned-host-response/v2' -and
            $reply.sequence -is [int] -and $reply.sequence -eq $Channel.sequence -and $reply.case_index -is [int] -and $reply.case_index -eq $CaseIndex -and
            $reply.acknowledged -is [bool] -and $reply.native_execution_authorized -is [bool] -and -not $reply.native_execution_authorized -and
            $reply.p09_complete -is [bool] -and -not $reply.p09_complete -and
            (($reply.acknowledged -and $null -eq $reply.error_code) -or (-not $reply.acknowledged -and
                $reply.error_code -is [string] -and $reply.error_code -cmatch '^(XREF_HOST_|XREF_NATIVE_STARTUP_|XREF_NATIVE_LIMITS_|XREF_PREASSIGNED_SCOPE_|STOP_|P09_XREF_|P58_)[A-Z0-9_]{1,120}$'))) 'V2_REPLY_BINDING'
        $descriptor=$null
        if ($reply.acknowledged -and $creation) {
            $label=if ($Step -ceq 'create_save_session') {'save'} else {'reopen'}
            $descriptor=Assert-P09XrefPreassignedDescriptor $reply.owner_descriptor $CaseIndex $label
        } else {Assert-P09XrefBinding ($null -eq $reply.owner_descriptor) 'V2_NO_UNEXPECTED_DESCRIPTOR'}
        $canonical=[ordered]@{};foreach ($key in $keys) {$canonical[$key]=$reply.$key};$canonical.owner_descriptor=$descriptor
        Assert-P09XrefBinding ($text -ceq ($canonical | ConvertTo-Json -Depth 8 -Compress)) 'V2_REPLY_CANONICAL'
        if (-not $reply.acknowledged) {$Channel.error_code=$reply.error_code;throw 'P09_XREF_BIND_V2_HOST_DENIED'}
        if ($creation) {$Channel.pending_descriptor=$descriptor}
        if ($Operation -ceq 'admit_owner') {$Channel.pending_descriptor=$null}
        if ($Operation -ceq 'finish' -and $CaseStatus -ceq 'returned') {$Channel.case_index++;$Channel.finish_attempted=$false}
        return $descriptor
    } catch {
        $Channel.failed=$true
        if ($Operation -ceq 'finish') {$Channel.cleanup_error_code='P09_XREF_BIND_V2_HOST_FINISH_FAILED'}
        throw
    }
}
