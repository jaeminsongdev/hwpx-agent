# Fixed readonly pipe qualification. Parent must deny the FIRST preparation checkpoint.
# This driver never selects a native entry or calls a native session step directly.
[CmdletBinding()]
param([switch]$PortDenial,[switch]$WrapperOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe','crossref-case-flow','crossref-native-case-ports','crossref-host-channel')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function Assert-P09XrefChannelReject([scriptblock]$Body) {
    $failed=$false;try {& $Body} catch {$failed=$true}
    Assert-P09XrefBinding $failed 'TEST_CHANNEL_EXPECTED_REJECT'
}
if ($WrapperOnly) {
    Assert-P09XrefBinding (-not $PortDenial) 'TEST_CHANNEL_ONE_READONLY_MODE'
    # Fixed in-memory DENIAL, never external input: this cannot authorize a slot/session.
    $deny='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":1,"case_index":1,"acknowledged":false,"error_code":"XREF_HOST_TEST_WRAPPER_DENIED","native_execution_authorized":false,"p09_complete":false}'
    $finish='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":2,"case_index":1,"acknowledged":true,"error_code":null,"native_execution_authorized":false,"p09_complete":false}'
    $reader=[IO.StringReader]::new($deny+"`n"+$finish+"`n");$writer=[IO.StringWriter]::new();$lease=$null
    try {
        $channel=New-P09XrefHostChannel $reader $writer;$lease=New-P09XrefProbeLease;$record=[ordered]@{}
        Invoke-P09XrefHostBoundCase $channel 1 $lease $record
        Assert-P09XrefBinding ($record.error_code -ceq 'P09_XREF_BIND_HOST_DENIED' -and $record.phase -ceq 'prepare_slot' -and
            $record.steps.Count -eq 1 -and $record.cleanup_callback_returned -and $null -eq $record.cleanup_error_code -and
            $null -eq $record.host_finish_error_code -and $channel.sequence -eq 2 -and $channel.finish_attempted -and
            $channel.error_code -ceq 'XREF_HOST_TEST_WRAPPER_DENIED' -and -not $record.native_execution_attested -and
            -not $record.native_execution_authorized -and -not $record.p09_complete -and
            -not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath 1 'opened'))) -and
            $null -eq ('P58OwnedWindowProcess' -as [type])) 'TEST_CHANNEL_ACTUAL_WRAPPER_CLOSED_BEFORE_SLOT'
        $sent=@($writer.ToString() -split '\r?\n' | Where-Object {$_.Length -gt 0} | ForEach-Object {$_ | ConvertFrom-Json})
        Assert-P09XrefBinding ($sent.Count -eq 2 -and $sent[0].operation -ceq 'checkpoint' -and
            $sent[0].step -ceq 'prepare_slot' -and $sent[1].operation -ceq 'finish' -and
            $sent[1].case_status -ceq 'failed') 'TEST_CHANNEL_WRAPPER_FINISH_ONCE'
        [ordered]@{schema_version='hwpx-agent.private.crossref-host-channel-contract-result/v1';
            state='one_actual_host_bound_wrapper_denial_contract_pass_not_native';passed=1;failed=0;
            fixed_denial_not_external_input=$true;native_directory_created=$false;actual_Hangul_or_COM=$false;
            native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    } finally {
        if ($null -ne $lease) {Close-P09XrefProbeLease $lease}
        $reader.Dispose();$writer.Dispose()
    }
    exit 0
}
if (-not $PortDenial) {
    $passed=0
    $reply='{"schema_version":"hwpx-agent.private.crossref-host-response/v1","sequence":1,"case_index":1,"acknowledged":true,"error_code":null,"native_execution_authorized":false,"p09_complete":false}'
    foreach ($text in @($reply.Replace('"sequence":1','"sequence":2'),
        $reply.Replace('"native_execution_authorized":false','"native_execution_authorized":true'),
        $reply.Replace('"acknowledged":true','"acknowledged":1'),
        $reply.Replace('"acknowledged":true','"acknowledged":false,"acknowledged":true'),
        $reply.Replace('"case_index":1','"case_index":true'),('x'*4097),'')) {
        $reader=[IO.StringReader]::new($text+"`n");$writer=[IO.StringWriter]::new()
        try {
            $channel=New-P09XrefHostChannel $reader $writer
            Assert-P09XrefChannelReject {Invoke-P09XrefHostMessage $channel 1 'checkpoint' -Step 'prepare_slot'}
            Assert-P09XrefBinding ($channel.failed -and $channel.sequence -eq 1) 'TEST_CHANNEL_FAILURE_LATCHED'
            $before=$writer.ToString()
            Assert-P09XrefChannelReject {Invoke-P09XrefHostMessage $channel 1 'checkpoint' -Step 'prepare_slot'}
            Assert-P09XrefBinding ($writer.ToString() -ceq $before) 'TEST_CHANNEL_NO_RETRY_WRITE'
        } finally {$reader.Dispose();$writer.Dispose()}
    }
    $passed++
    $reader=[IO.StringReader]::new($reply+"`n");$writer=[IO.StringWriter]::new()
    try {
        $channel=New-P09XrefHostChannel $reader $writer
        Invoke-P09XrefHostMessage $channel 1 'checkpoint' -Step 'prepare_slot'
        Assert-P09XrefBinding (-not $channel.failed -and $channel.sequence -eq 1) 'TEST_CHANNEL_ACK_NOT_AUTHORITY'
        $wire=$writer.ToString().Trim() | ConvertFrom-Json
        Assert-P09XrefBinding ($wire.operation -ceq 'checkpoint' -and $wire.step -ceq 'prepare_slot' -and
            @($wire.PSObject.Properties).Count -eq 5) 'TEST_CHANNEL_FIXED_OUTBOUND'
    } finally {$reader.Dispose();$writer.Dispose()}
    $passed++
    [ordered]@{schema_version='hwpx-agent.private.crossref-host-channel-contract-result/v1';
        state='two_ps_channel_contracts_pass_not_native';passed=$passed;failed=0;
        actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
}
$lease=$null
try {
    $channel=New-P09XrefHostChannel ([Console]::In) ([Console]::Out)
    $lease=New-P09XrefProbeLease
    $record=[ordered]@{}
    $state=New-P09XrefNativeCaseState 1 $lease `
        {param($step,$s)
            Invoke-P09XrefHostMessage $channel $s.case_index 'checkpoint' -Step $step
            # Even a malicious positive reply cannot let this TEST create a slot/session.
            throw 'STOP_TEST_PARENT_MUST_DENY_BEFORE_SLOT'
        } {throw 'STOP_TEST_NATIVE_ADMISSION_MUST_NOT_REACH'}
    Invoke-P09XrefNativeCaseWorkflow $state $record
    Invoke-P09XrefHostMessage $channel 1 'finish' -CaseStatus 'failed'
    Assert-P09XrefBinding ($record.error_code -ceq 'P09_XREF_BIND_HOST_DENIED' -and $record.phase -ceq 'prepare_slot' -and
        $record.steps.Count -eq 1 -and $record.cleanup_callback_returned -and $null -eq $record.cleanup_error_code -and
        $channel.sequence -eq 2 -and $channel.failed -and
        $channel.finish_attempted -and -not $record.native_execution_attested -and -not $record.p09_complete -and
        -not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath 1 'opened'))) -and
        $null -eq ('P58OwnedWindowProcess' -as [type])) 'TEST_CHANNEL_ACTUAL_PORTS_STOPPED_BEFORE_SLOT'
    [ordered]@{schema_version='hwpx-agent.private.crossref-host-channel-contract-result/v1';
        state='actual_x86_pipe_ports_denial_and_finish_pass_not_native';request_count=$channel.sequence;
        callback_steps=1;cleanup_callback_returned=$true;native_directory_created=$false;
        actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
} finally {if ($null -ne $lease) {Close-P09XrefProbeLease $lease}}
