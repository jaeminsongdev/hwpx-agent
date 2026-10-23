# Pure descriptor/reply models or full-eight fake-owner wire only. No Native/COM/ROT.
[CmdletBinding()]
param([switch]$ModelsOnly,[switch]$WireModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
if (($ModelsOnly -and $WireModelsOnly) -or (-not $ModelsOnly -and -not $WireModelsOnly)) {throw 'P09_XREF_V2_CLOSED_TEST_MODE'}
foreach ($name in @('crossref-owned-active-source','crossref-case-flow','crossref-host-channel','crossref-preassigned-host-channel')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function New-V2TestDescriptor {
    return [pscustomobject][ordered]@{profile='hwpx-agent.private.crossref-preassigned-session-scope/v1';case_index=1;session_label='save';
        process_id=101;session_id=1;created_at_utc='2026-10-21T00:00:00.0000001Z';
        executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';source='current_exact_preassigned_process_handle';
        COM_owner_bound=$false;native_execution_authorized=$false;native_startup_qualified=$false;P09_complete=$false}
}
function New-V2TestReply([int]$Sequence,[bool]$Acknowledged,$Descriptor) {
    return [ordered]@{schema_version='hwpx-agent.private.crossref-preassigned-host-response/v2';sequence=$Sequence;case_index=1;
        acknowledged=$Acknowledged;error_code=if ($Acknowledged) {$null} else {'XREF_HOST_V2_MODEL_DENIED'};
        owner_descriptor=$Descriptor;native_execution_authorized=$false;p09_complete=$false}
}
function Assert-V2TestReject([scriptblock]$Body) {
    $caught=$false;try {[void](& $Body)} catch {$caught=$true};Assert-P09XrefBinding $caught 'V2_MODEL_EXPECTED_REJECTION'
}
function Invoke-V2TestSingleReply([string]$Raw,[string]$Step) {
    $reader=[IO.StringReader]::new($Raw+"`n");$writer=[IO.StringWriter]::new()
    try {$channel=New-P09XrefPreassignedHostChannel $reader $writer
        return Invoke-P09XrefPreassignedHostMessage $channel 1 'checkpoint' -Step $Step
    } finally {$reader.Dispose();$writer.Dispose()}
}
try {
    if ($ModelsOnly) {
        $d=New-V2TestDescriptor
        [void](Assert-P09XrefPreassignedDescriptor $d 1 'save')
        [Console]::WriteLine('test xref_v2_ps::closed_descriptor ... ok')
        foreach ($key in @('COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete')) {
            $bad=New-V2TestDescriptor;$bad.$key=$true;Assert-V2TestReject {Assert-P09XrefPreassignedDescriptor $bad 1 'save'}
        }
        [Console]::WriteLine('test xref_v2_ps::no_descriptor_authority ... ok')
        $bad=New-V2TestDescriptor;$bad | Add-Member -NotePropertyName approved -NotePropertyValue $true
        Assert-V2TestReject {Assert-P09XrefPreassignedDescriptor $bad 1 'save'}
        [Console]::WriteLine('test xref_v2_ps::unknown_descriptor_field ... ok')
        $reply=New-V2TestReply 1 $true $d;$raw=$reply | ConvertTo-Json -Depth 8 -Compress
        $result=Invoke-V2TestSingleReply $raw 'create_save_session';Assert-P09XrefBinding ($result.process_id -eq 101) 'V2_MODEL_DESCRIPTOR_RETURN'
        [Console]::WriteLine('test xref_v2_ps::creation_descriptor ... ok')
        $bad=$raw.Replace('"acknowledged":true','"acknowledged":true,"acknowl\u0065dged":false')
        Assert-V2TestReject {Invoke-V2TestSingleReply $bad 'create_save_session'}
        [Console]::WriteLine('test xref_v2_ps::escaped_duplicate_reply ... ok')
        Assert-V2TestReject {Invoke-V2TestSingleReply ($raw.Replace('preassigned-host-response/v2','host-response/v1')) 'create_save_session'}
        [Console]::WriteLine('test xref_v2_ps::old_reply_rejected ... ok')
        Assert-V2TestReject {Invoke-V2TestSingleReply $raw 'prepare_slot'}
        [Console]::WriteLine('test xref_v2_ps::unexpected_descriptor_rejected ... ok')
        $reply['approved']=$true
        Assert-V2TestReject {Invoke-V2TestSingleReply ($reply | ConvertTo-Json -Depth 8 -Compress) 'create_save_session'}
        [Console]::WriteLine('test xref_v2_ps::unknown_reply_field ... ok')
        [Console]::WriteLine('test result: ok. 8 passed; 0 failed; 0 ignored; v2_models_only_not_native')
    } else {
        $channel=New-P09XrefPreassignedHostChannel ([Console]::In) ([Console]::Out)
        $admissions=0
        for ($index=1;$index -le 8;$index++) {
            foreach ($step in (Get-P09XrefCaseFlowSteps)) {
                $d=Invoke-P09XrefPreassignedHostMessage $channel $index 'checkpoint' -Step $step
                if ($step -cin @('create_save_session','create_reopen_session')) {
                    Assert-P09XrefBinding ($null -ne $d -and $d.case_index -eq $index) 'V2_WIRE_CURRENT_DESCRIPTOR'
                    $owner=[ordered]@{identity=[ordered]@{process_id=$d.process_id;session_id=$d.session_id;created_at_utc=$d.created_at_utc;
                        executable_sha256=$d.executable_sha256;window_handle_binds_exact_process=$true};window=[pscustomobject]@{WindowHandle=123}}
                    [void](Invoke-P09XrefPreassignedHostMessage $channel $index 'admit_owner' -Owner $owner);$admissions++
                } else {Assert-P09XrefBinding ($null -eq $d) 'V2_WIRE_NO_OTHER_DESCRIPTOR'}
            }
            [void](Invoke-P09XrefPreassignedHostMessage $channel $index 'finish' -CaseStatus 'returned')
        }
        Assert-P09XrefBinding ($channel.case_index -eq 9 -and $channel.sequence -eq 152 -and $admissions -eq 16 -and -not $channel.failed) 'V2_WIRE_COMPLETE_EIGHT_MODEL_SESSIONS'
        [Console]::WriteLine('test xref_v2_wire::all_eight_models_and_canonical_descriptors ... ok')
        [Console]::WriteLine('test result: ok. 1 passed; 0 failed; 0 ignored; v2_wire_fake_owners_not_native')
    }
} catch {
    $code=$_.Exception.Message
    if ($code -cnotmatch '^P09_XREF_BIND_[A-Z0-9_]{1,120}$') {$code='P09_XREF_BIND_V2_TEST_FAILED_NO_RAW_VALUES'}
    [Console]::Error.WriteLine(('Error: '+$code));exit 2
}
