# Private bounded checkpoint channel. A reply never grants native authority.
# No process/COM creation, retry, prompt timeout or force kill in this module.
Set-StrictMode -Version Latest

function New-P09XrefHostChannel {
    param([Parameter(Mandatory)][IO.TextReader]$InputReader,[Parameter(Mandatory)][IO.TextWriter]$OutputWriter)
    return [ordered]@{input=$InputReader;output=$OutputWriter;sequence=0;case_index=1;
        failed=$false;finish_attempted=$false;error_code=$null;cleanup_error_code=$null}
}

function Read-P09XrefBoundedHostReply($Channel) {
    $buffer=[Text.StringBuilder]::new()
    for ($i=0;$i -le 4096;$i++) {
        $value=$Channel.input.Read()
        Assert-P09XrefBinding ($value -ge 0) 'HOST_REPLY_EOF'
        if ($value -eq 10) {
            $text=$buffer.ToString().TrimEnd([char]13)
            Assert-P09XrefBinding ([Text.Encoding]::UTF8.GetByteCount($text) -le 4096) 'HOST_REPLY_BYTES'
            return $text
        }
        [void]$buffer.Append([char]$value)
    }
    throw 'P09_XREF_BIND_HOST_REPLY_LIMIT'
}

function Invoke-P09XrefHostMessage {
    param([Parameter(Mandatory)]$Channel,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][ValidateSet('checkpoint','admit_owner','finish')][string]$Operation,
        [string]$Step,$Owner,[ValidateSet('returned','failed')][string]$CaseStatus)
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8 -and $Channel.case_index -eq $CaseIndex -and
        -not $Channel.finish_attempted) 'HOST_CASE_ORDER_OR_FINISHED'
    Assert-P09XrefBinding (-not $Channel.failed -or ($Operation -ceq 'finish' -and $CaseStatus -ceq 'failed')) 'HOST_STOP_LATCHED'
    if ($Operation -ceq 'finish') {$Channel.finish_attempted=$true}
    $Channel.sequence++ # Uncertain write/read never reuses a sequence or retries.
    $request=[ordered]@{schema_version='hwpx-agent.private.crossref-host-request/v1';
        sequence=$Channel.sequence;case_index=$CaseIndex;operation=$Operation}
    try {
        switch -CaseSensitive ($Operation) {
            'checkpoint' {
                Assert-P09XrefBinding ($Step -cin (Get-P09XrefCaseFlowSteps)) 'HOST_FIXED_STEP'
                $request.step=$Step
            }
            'admit_owner' {
                Assert-P09XrefBinding ($null -ne $Owner.identity -and $null -ne $Owner.window) 'HOST_OWNER_REQUIRED'
                $request.identity=$Owner.identity;$request.window_handle=[int]$Owner.window.WindowHandle
            }
            'finish' {$request.case_status=$CaseStatus}
        }
        $wire=$request | ConvertTo-Json -Depth 8 -Compress
        Assert-P09XrefBinding ([Text.Encoding]::UTF8.GetByteCount($wire) -le 4096) 'HOST_REQUEST_BYTES'
        $Channel.output.WriteLine($wire);$Channel.output.Flush()
        $text=Read-P09XrefBoundedHostReply $Channel
        $reply=$text | ConvertFrom-Json
        $keys=@('schema_version','sequence','case_index','acknowledged','error_code','native_execution_authorized','p09_complete')
        Assert-P09XrefBinding (@($reply.PSObject.Properties).Count -eq $keys.Count) 'HOST_REPLY_SCHEMA'
        foreach ($key in $keys) {Assert-P09XrefBinding ($key -cin @($reply.PSObject.Properties.Name)) 'HOST_REPLY_KEY'}
        Assert-P09XrefBinding ($reply.schema_version -ceq 'hwpx-agent.private.crossref-host-response/v1' -and
            $reply.sequence -is [int] -and $reply.sequence -eq $Channel.sequence -and
            $reply.case_index -is [int] -and $reply.case_index -eq $CaseIndex -and
            $reply.acknowledged -is [bool] -and $reply.native_execution_authorized -is [bool] -and
            -not $reply.native_execution_authorized -and $reply.p09_complete -is [bool] -and -not $reply.p09_complete -and
            (($reply.acknowledged -and $null -eq $reply.error_code) -or
            (-not $reply.acknowledged -and $reply.error_code -is [string] -and
                $reply.error_code -cmatch '^(XREF_HOST_|XREF_NATIVE_LIMITS_|STOP_|P09_XREF_|P58_)[A-Z_]{1,120}$'))) 'HOST_REPLY_BINDING'
        $canonical=[ordered]@{}
        foreach ($key in $keys) {$canonical[$key]=$reply.$key}
        # Reject duplicate keys, alternative/coerced values and noncanonical parser ambiguities.
        Assert-P09XrefBinding ($text -ceq ($canonical | ConvertTo-Json -Depth 4 -Compress)) 'HOST_REPLY_CANONICAL'
        if (-not $reply.acknowledged) {
            if ($null -eq $Channel.error_code) {$Channel.error_code=$reply.error_code}
            throw 'P09_XREF_BIND_HOST_DENIED'
        }
        if ($Operation -ceq 'finish' -and $CaseStatus -ceq 'returned') {
            $Channel.case_index++;$Channel.finish_attempted=$false
        }
    } catch {
        $Channel.failed=$true
        if ($Operation -ceq 'finish') {$Channel.cleanup_error_code='P09_XREF_BIND_HOST_FINISH_FAILED'}
        throw
    }
}

function Invoke-P09XrefHostBoundCase {
    param([Parameter(Mandatory)]$Channel,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)]$ProbeLease,[Parameter(Mandatory)][System.Collections.IDictionary]$FlowRecord)
    $status='failed'
    try {
        $state=New-P09XrefNativeCaseState $CaseIndex $ProbeLease `
            {param($step,$s) Invoke-P09XrefHostMessage $Channel $s.case_index 'checkpoint' -Step $step} `
            {param($owner,$s) Invoke-P09XrefHostMessage $Channel $s.case_index 'admit_owner' -Owner $owner}
        Invoke-P09XrefNativeCaseWorkflow $state $FlowRecord
        if ($null -eq $FlowRecord.error_code -and $null -eq $FlowRecord.cleanup_error_code -and $FlowRecord.steps.Count -eq 16) {
            $status='returned'
        }
    } catch {
        $FlowRecord.error_code='P09_XREF_BIND_HOST_CASE_FAILED_NO_RAW_VALUES'
    } finally {
        $FlowRecord.host_finish_error_code=$null
        try {Invoke-P09XrefHostMessage $Channel $CaseIndex 'finish' -CaseStatus $status}
        catch {$FlowRecord.host_finish_error_code='P09_XREF_BIND_HOST_FINISH_FAILED'}
        $FlowRecord.native_execution_authorized=$false;$FlowRecord.p09_complete=$false;$FlowRecord.accepted_count_delta=0
    }
}
