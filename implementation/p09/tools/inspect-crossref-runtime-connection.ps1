# Closed end-to-end inspection ONLY. The transport refuses a positive first reply
# before the real case step can create a native output slot or COM session.
[CmdletBinding()]
param([switch]$InspectConnectionOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)

class P09InspectionDenyReader : System.IO.TextReader {
    [System.IO.TextReader]$Inner
    [string]$Pending=''
    [int]$Offset=0
    [bool]$FirstReplyChecked=$false
    [bool]$FirstReplyRejected=$false
    P09InspectionDenyReader([System.IO.TextReader]$inner) {$this.Inner=$inner}
    [int]Read() {
        if ($this.Offset -lt $this.Pending.Length) {
            $answer=[int][char]$this.Pending[$this.Offset];$this.Offset++;return $answer
        }
        $builder=[Text.StringBuilder]::new();$line=$null
        for ($i=0;$i -le 4096;$i++) {
            $value=$this.Inner.Read()
            if ($value -lt 0) {return -1}
            if ($value -eq 10) {$line=$builder.ToString().TrimEnd([char]13);break}
            [void]$builder.Append([char]$value)
        }
        if ($null -eq $line) {throw 'P09_XREF_BIND_INSPECTION_REPLY_LIMIT'}
        if (-not $this.FirstReplyChecked) {
            $this.FirstReplyChecked=$true
            $pattern='^\{"schema_version":"hwpx-agent\.private\.crossref-host-response/v1","sequence":1,"case_index":1,"acknowledged":false,"error_code":"(XREF_HOST_|XREF_NATIVE_LIMITS_|STOP_|P09_XREF_|P58_)[A-Z_]{1,120}","native_execution_authorized":false,"p09_complete":false\}$'
            if (-not [regex]::IsMatch($line,$pattern,[Text.RegularExpressions.RegexOptions]::CultureInvariant)) {
                $this.FirstReplyRejected=$true
                throw 'P09_XREF_BIND_INSPECTION_REQUIRES_DENIAL'
            }
        }
        $this.Pending=$line+"`n";$this.Offset=1
        return [int][char]$this.Pending[0]
    }
}

$phase='inspection_mode';$lease=$null;$gate=$null
try {
    if (-not $InspectConnectionOnly) {throw 'P09_XREF_BIND_INSPECTION_MODE_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
        'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
        'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
        [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'INSPECTION_X86_STA'
    $phase='fixed_probe_lease';$lease=New-P09XrefProbeLease
    $gate=[P09InspectionDenyReader]::new([Console]::In)
    $channel=New-P09XrefHostChannel $gate ([Console]::Out);$batch=[ordered]@{}
    $phase='closed_fixed_batch';Invoke-P09XrefFixedHostBatch $channel $lease $batch
    Assert-P09XrefBinding ($gate.FirstReplyChecked -and $batch.planned_cases -eq 8 -and $batch.cases.Count -eq 1 -and
        $batch.completed_callback_cases -eq 0 -and $batch.stopped_case_index -eq 1 -and
        $batch.cases[0].phase -ceq 'prepare_slot' -and $batch.cases[0].callback_steps -eq 1 -and
        $channel.sequence -eq 2 -and $channel.finish_attempted -and $null -eq $batch.cases[0].host_finish_error_code -and
        -not $batch.native_execution_attested -and $null -eq ('P58OwnedWindowProcess' -as [type])) 'INSPECTION_STOPPED_BEFORE_SLOT'
    for ($index=1;$index -le 8;$index++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $index 'opened')))) 'INSPECTION_NATIVE_DIR_CREATED'
    }
    [ordered]@{schema_version='hwpx-agent.private.crossref-runtime-inspection/v1';
        state='closed_fixed_eight_runtime_inspected_not_native';batch=$batch;
        first_reply_checked=$gate.FirstReplyChecked;positive_or_invalid_reply_blocked=$gate.FirstReplyRejected;
        native_directories_created=$false;actual_Hangul_or_COM=$false;native_execution_authorized=$false;
        native_provenance_qualified=$false;p09_complete=$false} | ConvertTo-Json -Depth 9 -Compress
} catch {
    [ordered]@{schema_version='hwpx-agent.private.crossref-runtime-inspection/v1';state='runtime_inspection_failed';
        phase=$phase;source_line=$_.InvocationInfo.ScriptLineNumber;error_type=$_.Exception.GetType().Name;
        error_code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_RUNTIME_INSPECTION_FAILED_NO_RAW_VALUES'};
        actual_Hangul_or_COM=$false;native_execution_authorized=$false;native_provenance_qualified=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
} finally {
    if ($null -ne $lease) {Close-P09XrefProbeLease $lease}
    if ($null -ne $gate) {$gate.Dispose()}
}
