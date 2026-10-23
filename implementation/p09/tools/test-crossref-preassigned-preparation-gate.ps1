# Pure bounded TextReader contracts only. No process, native controller or COM.
[CmdletBinding()]
param([switch]$GateModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $GateModelsOnly) {throw 'P09_XREF_BIND_PREPARATION_GATE_MODE_REQUIRED'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-preassigned-preparation-gate.ps1')
function New-GateModelReply {
    return [ordered]@{schema_version='hwpx-agent.private.crossref-preassigned-host-response/v2';sequence=1;case_index=1;
        acknowledged=$false;error_code='XREF_HOST_PREPARATION_NATIVE_DISPATCH_DENIED';owner_descriptor=$null;
        native_execution_authorized=$false;p09_complete=$false}
}
function Read-GateModel([string]$Text) {
    $inner=[IO.StringReader]::new($Text);$gate=[P09PreassignedPreparationDenyReader]::new($inner)
    try {
        $output=[Text.StringBuilder]::new()
        for ($i=0;$i -le 10000;$i++) {
            $value=$gate.Read()
            if ($value -lt 0) {return [ordered]@{text=$output.ToString();checked=$gate.FirstReplyChecked;rejected=$gate.FirstReplyRejected}}
            [void]$output.Append([char]$value)
        }
        throw 'P09_XREF_BIND_GATE_MODEL_READ_BOUND'
    } finally {$gate.Dispose();$inner.Dispose()}
}
function Assert-GateModelRejected([string]$Text,[string]$Code) {
    $caught=$false
    try {[void](Read-GateModel ($Text+"`n"))} catch {$caught=($_.Exception.GetBaseException().Message -ceq ('P09_XREF_BIND_'+$Code))}
    Assert-P09XrefBinding $caught 'GATE_MODEL_EXPECTED_REJECTION'
}
try {
    $reply=New-GateModelReply;$valid=$reply | ConvertTo-Json -Depth 5 -Compress
    $second=New-GateModelReply;$second.sequence=2;$second.acknowledged=$true;$second.error_code=$null
    $text=$valid+"`n"+($second | ConvertTo-Json -Depth 5 -Compress)+"`n"
    $read=Read-GateModel $text
    Assert-P09XrefBinding ($read.text -ceq $text -and $read.checked -and -not $read.rejected) 'GATE_MODEL_DENIAL_THEN_SECOND_REPLY'
    [Console]::WriteLine('test preparation_gate::exact_denial_passthrough ... ok')
    $positive=New-GateModelReply;$positive.acknowledged=$true;$positive.error_code=$null
    Assert-GateModelRejected ($positive | ConvertTo-Json -Depth 5 -Compress) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::positive_first_never_reaches_controller ... ok')
    Assert-GateModelRejected ($valid.Replace('preassigned-host-response/v2','host-response/v1')) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::old_version_rejected ... ok')
    Assert-GateModelRejected ($valid.Replace('"sequence":1','"sequence":2')) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::wrong_sequence_rejected ... ok')
    Assert-GateModelRejected ($valid.Replace('"acknowledged":false','"acknowledged":false,"acknowl\u0065dged":false')) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::escaped_duplicate_rejected ... ok')
    $extra=New-GateModelReply;$extra['approved']=$true
    Assert-GateModelRejected ($extra | ConvertTo-Json -Depth 5 -Compress) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::extra_field_rejected ... ok')
    Assert-GateModelRejected ($valid.Replace('"native_execution_authorized":false','"native_execution_authorized":true')) 'PREPARATION_REQUIRES_DENIAL'
    [Console]::WriteLine('test preparation_gate::true_native_authority_rejected ... ok')
    Assert-GateModelRejected ('x'*4097) 'PREPARATION_REPLY_LIMIT'
    Assert-GateModelRejected ([string]::new([char]0xAC00,2000)) 'PREPARATION_REPLY_LIMIT'
    [Console]::WriteLine('test preparation_gate::character_and_utf8_byte_bounds ... ok')
    [Console]::WriteLine('test result: ok. 8 passed; 0 failed; 0 ignored; reader_only_not_Native')
} catch {
    $code=$_.Exception.GetBaseException().Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_GATE_MODELS_FAILED_NO_RAW_VALUES'}
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
