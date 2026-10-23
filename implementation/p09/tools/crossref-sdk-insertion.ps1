# Internal SDK adapter functions only. No CLI/native dispatcher, activation or approval flag.
# Only a separately authorized dispatcher may call this with a real verified owned session.
Set-StrictMode -Version Latest

function Assert-P09XrefOpenedProbe($Probe,[int]$CaseIndex,[string]$OpenedSha256) {
    $scope=Get-P09XrefArtifactScope $CaseIndex 'opened_clean' $OpenedSha256
    Assert-P09XrefBinding ($Probe.schema_version -ceq 'hwpx-agent.private.crossref-worker-source-probe/v1' -and
        $Probe.state -ceq 'source_probe_completed_not_native_attestation' -and $Probe.candidate_count -eq 8 -and
        $Probe.prepared_batch_sha256 -ceq '1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1' -and
        $Probe.observed_output_sha256 -ceq $OpenedSha256 -and $Probe.selected_case.case_id -ceq $scope.case_id -and
        $Probe.selected_case.phase -ceq 'opened' -and
        $Probe.selected_case.source_target_observation.observation -ceq 'unique_exact_name_observed') 'SDK_OPENED_PROBE_BINDING'
    foreach ($key in @('native_execution_attested','native_target_resolution_qualified','parameter_key_semantics_qualified',
            'causal_insertion_or_preservation_proved','complete_reference_validation_qualified','native_execution_authorized',
            'raw_document_values_or_sdk_commands_present','p09_complete')) {
        Assert-P09XrefBinding ($Probe.$key -is [bool] -and -not $Probe.$key) 'SDK_PROBE_FALSE_CLAIM'
    }
    # Observation data is necessary but never a producer/authority attestation.
}

function Get-P09XrefFixedSdkCase([int]$CaseIndex) {
    Assert-P09XrefBinding ($CaseIndex -ge 1 -and $CaseIndex -le 8) 'SDK_CASE_INDEX'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $path=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/prepared-sdk-batch.v1.json'
    $item=Get-Item -LiteralPath $path -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq 42762) 'SDK_PACKET_SIZE'
    $ancestor=$item
    while ($null -ne $ancestor) {
        Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'SDK_PACKET_LINKED'
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    Start-Sleep -Milliseconds 50
    $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $memory=[IO.MemoryStream]::new();$algorithm=[Security.Cryptography.SHA256]::Create()
    try {
        $buffer=[byte[]]::new(8192)
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -ne 0) {
            Assert-P09XrefBinding (($memory.Length+$n) -le 42762) 'SDK_PACKET_READ_LIMIT'
            $memory.Write($buffer,0,$n)
        }
        $bytes=$memory.ToArray()
        $sha=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($bytes.Length -eq 42762 -and $sha -ceq
            '1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1') 'SDK_PACKET_SHA'
        $packet=[Text.UTF8Encoding]::new($false,$true).GetString($bytes) | ConvertFrom-Json
        [void](Assert-P09XrefFixedPacket $packet)
        return $packet.cases[$CaseIndex-1]
    } finally {$stream.Dispose();$memory.Dispose();$algorithm.Dispose()}
}

function Invoke-P09XrefSdkInsertion {
    param([Parameter(Mandatory)]$Owner,[Parameter(Mandatory)]$Document,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$OpenedSha256,[Parameter(Mandatory)]$OpenedProbe,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    # The mutable caller-owned record survives any thrown failure; no retry/rollback claim.
    $Record.phase='input_binding';$Record.execute_invoked=$false;$Record.execute_returned=$null
    $Record.effect_unknown=$false;$Record.error_code=$null;$Record.native_semantics_qualified=$false
    try {
        Assert-P09XrefOpenedProbe $OpenedProbe $CaseIndex $OpenedSha256
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'opened_clean' $OpenedSha256)
        $case=Get-P09XrefFixedSdkCase $CaseIndex
        $Record.phase='get_default'
        $action=$Owner.hwp.HAction;$parameters=$Owner.hwp.HParameterSet
        $crossref=$parameters.HActionCrossRef;$set=$crossref.HSet
        foreach ($value in @($action,$parameters,$crossref,$set)) {
            Assert-P09XrefBinding ([Runtime.InteropServices.Marshal]::IsComObject($value)) 'SDK_REAL_PARAMETERS_REQUIRED'
        }
        $default=$action.GetDefault('InsertCrossReference',$set)
        Assert-P09XrefBinding ($default -is [bool] -and $default) 'SDK_DEFAULT_REJECTED'
        $Record.phase='parameter_assignment'
        $crossref.Command=$case.sdk_command
        Assert-P09XrefBinding ($crossref.Command -is [string] -and $crossref.Command -ceq $case.sdk_command) 'SDK_COMMAND_READBACK'
        # A prior observation never becomes a stale permission to execute on a different document.
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'opened_clean' $OpenedSha256)
        $Record.phase='sdk_execute';$Record.execute_invoked=$true;$Record.effect_unknown=$true
        $executed=$action.Execute('InsertCrossReference',$set)
        if ($executed -is [bool]) {$Record.execute_returned=$executed}
        Assert-P09XrefBinding ($executed -is [bool] -and $executed) 'SDK_EXECUTE_REJECTED_EFFECT_UNKNOWN'
        $Record.phase='post_insert_binding'
        [void](Observe-P09XrefOwnedArtifact $Owner $Document $CaseIndex 'opened_after_insert' $OpenedSha256)
        $Record.phase='sdk_returned_true_semantics_unqualified'
        return [ordered]@{state='sdk_returned_true_not_semantic_or_preservation_acceptance';case_id=$case.case_id;
            execute_invoked=$true;execute_returned=$true;effect_unknown=$true;native_semantics_qualified=$false;
            execution_authority_granted_by_this_adapter=$false;causal_insertion_or_preservation_proved=$false;p09_complete=$false}
    } catch {
        $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_SDK_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code
        throw $code
    }
    # Borrowed HAction/HParameterSet RCW aliases belong to the owned session.
    # Never FinalRelease them or reset shared Command after an uncertain execute.
}
