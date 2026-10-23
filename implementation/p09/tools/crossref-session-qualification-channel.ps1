# Function-only session candidate transport; no Native permit or activation.
Set-StrictMode -Version Latest

function New-P09XrefSessionQualificationChannel([IO.TextReader]$InputReader,[IO.TextWriter]$OutputWriter) {
    return [ordered]@{input=$InputReader;output=$OutputWriter;sequence=0;failed=$false;finish_attempted=$false;
        pending_descriptor=$null;phase='ready';error_code=$null}
}

function Invoke-P09XrefSessionQualificationMessage {
    param([Parameter(Mandatory)]$Channel,[ValidateSet('ready','admit_owner','closed','failed')][string]$Operation,
        $WorkerIdentity,$Owner,$Cleanup,[string]$ErrorCode)
    Assert-P09XrefBinding (-not $Channel.finish_attempted -and $Channel.sequence -lt 4 -and
        ((-not $Channel.failed -and $Operation -ceq $Channel.phase) -or $Operation -ceq 'failed')) 'SESSION_ONE_LIFETIME_ORDER'
    if ($Operation -cin @('closed','failed')) {$Channel.finish_attempted=$true}
    $Channel.sequence++
    try {
        $request=[ordered]@{schema_version='hwpx-agent.private.crossref-session-qualification-request/v1';sequence=$Channel.sequence;operation=$Operation}
        switch -CaseSensitive ($Operation) {
            'ready' {$request['worker_identity']=$WorkerIdentity}
            'admit_owner' {$request['identity']=$Owner.identity;$request['window_handle']=[int]$Owner.window.WindowHandle}
            'closed' {$request['cleanup']=$Cleanup}
            'failed' {$request['error_code']=$ErrorCode;$request['cleanup']=$Cleanup}
        }
        $wire=$request | ConvertTo-Json -Depth 8 -Compress
        Assert-P09XrefBinding ([Text.Encoding]::UTF8.GetByteCount($wire) -le 4096) 'SESSION_REQUEST_BYTES'
        $Channel.output.WriteLine($wire);$Channel.output.Flush()
        $text=Read-P09XrefBoundedHostReply $Channel;$reply=$text | ConvertFrom-Json
        $keys=@('schema_version','sequence','acknowledged','error_code','owner_descriptor','native_execution_authorized','native_startup_qualified','p09_complete')
        Assert-P09XrefBinding (@($reply.PSObject.Properties).Count -eq $keys.Count) 'SESSION_REPLY_SCHEMA'
        foreach ($key in $keys) {Assert-P09XrefBinding ($key -cin @($reply.PSObject.Properties.Name)) 'SESSION_REPLY_KEY'}
        Assert-P09XrefBinding ($reply.schema_version -ceq 'hwpx-agent.private.crossref-session-qualification-response/v1' -and
            $reply.sequence -is [int] -and $reply.sequence -eq $Channel.sequence -and $reply.acknowledged -is [bool] -and
            (($reply.acknowledged -and $null -eq $reply.error_code) -or (-not $reply.acknowledged -and
                $reply.error_code -is [string] -and $reply.error_code -cmatch '^(XREF_|STOP_)[A-Z0-9_]{1,140}$'))) 'SESSION_REPLY_BINDING'
        foreach ($key in @('native_execution_authorized','native_startup_qualified','p09_complete')) {
            Assert-P09XrefBinding ($reply.$key -is [bool] -and -not $reply.$key) 'SESSION_NO_AUTHORITY_IN_REPLY'
        }
        $descriptor=$null
        if ($reply.acknowledged -and $Operation -ceq 'ready') {$descriptor=Assert-P09XrefPreassignedDescriptor $reply.owner_descriptor 1 'save'}
        else {Assert-P09XrefBinding ($null -eq $reply.owner_descriptor) 'SESSION_NO_OTHER_DESCRIPTOR'}
        $canonical=[ordered]@{};foreach ($key in $keys) {$canonical[$key]=$reply.$key};$canonical.owner_descriptor=$descriptor
        Assert-P09XrefBinding ($text -ceq ($canonical | ConvertTo-Json -Depth 8 -Compress)) 'SESSION_CANONICAL_REPLY'
        if (-not $reply.acknowledged) {$Channel.error_code=$reply.error_code;throw 'P09_XREF_BIND_SESSION_HOST_DENIED'}
        switch -CaseSensitive ($Operation) {
            'ready' {$Channel.pending_descriptor=$descriptor;$Channel.phase='admit_owner'}
            'admit_owner' {$Channel.pending_descriptor=$null;$Channel.phase='closed'}
            default {$Channel.phase='finished'}
        }
        return $descriptor
    } catch {$Channel.failed=$true;throw}
}
