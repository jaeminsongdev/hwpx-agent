# Pure packet checks only. No file, registry, process or COM operations here.
Set-StrictMode -Version Latest

function Assert-P09XrefCondition([bool]$Condition, [string]$Code) {
    if (-not $Condition) {throw ('P09_XREF_'+$Code)}
}

function Get-P09XrefDigest([byte[]]$Bytes) {
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
    finally {$algorithm.Dispose()}
}

function Assert-P09XrefFalse($Value) {
    Assert-P09XrefCondition ($Value -is [bool] -and -not $Value) 'FALSE_CLAIM_REQUIRED'
}

function Assert-P09XrefDigestArray($Value, [string]$Expected) {
    Assert-P09XrefCondition ($Value -is [Array] -and $Value.Count -eq 32) 'DIGEST_ARRAY_SIZE'
    foreach ($part in $Value) {
        Assert-P09XrefCondition (($part -is [int] -or $part -is [long]) -and $part -ge 0 -and $part -le 255) 'DIGEST_ARRAY_TYPE'
    }
    Assert-P09XrefCondition (([BitConverter]::ToString([byte[]]$Value)).Replace('-','').ToLowerInvariant() -ceq $Expected) 'DIGEST_ARRAY_IDENTITY'
}

function Assert-P09XrefFixedPacket($Packet) {
    Assert-P09XrefCondition ($Packet.schema_version -ceq 'hwpx-agent.private.crossref-discovery-prepared-batch/v1' -and
        $Packet.state -ceq 'prepared_eight_source_bound_candidates_not_native_ready' -and
        $Packet.document_namespace -ceq 'p09-crossref-sdk-discovery-input-r01') 'PACKET_SCOPE'
    foreach ($name in @('native_execution_authorized','native_executed','native_attempt_created','public_raw_action_route','p09_complete')) {
        Assert-P09XrefFalse $Packet.$name
    }
    Assert-P09XrefCondition ($Packet.separate_from_frozen_p58_full34_queue -is [bool] -and
        $Packet.separate_from_frozen_p58_full34_queue -and $Packet.accepted_count_delta -eq 0) 'FROZEN_QUEUE_BOUNDARY'
    $inputSha='64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184'
    Assert-P09XrefCondition ($Packet.generated_input_pin.sha256 -ceq $inputSha -and
        $Packet.generated_input_pin.bytes -eq 14425 -and $Packet.generated_input_pin.path -ceq
        'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx' -and
        $Packet.source_manifest_sha256 -ceq 'fef538f8e072a72e8d0c0f42b0752a88ecdaf3fc582d4c67d07891bea34fcd29') 'INPUT_BINDING'
    Assert-P09XrefCondition ($Packet.cases -is [Array] -and $Packet.cases.Count -eq 8) 'ALL_EIGHT_REQUIRED'
    $sourceReceipt=$null;$targetDigest=$null;$logicalDigest=$null
    for ($i=0;$i -lt 8;$i++) {
        $row=$Packet.cases[$i]
        Assert-P09XrefCondition ($row.case_id -ceq ('P09-XREF-BOOK-C'+($i+1).ToString('00')) -and
            $row.sdk_action -ceq 'InsertCrossReference' -and $row.sdk_parameter_set -ceq 'HActionCrossRef' -and
            $row.sdk_property -ceq 'Command' -and $row.native_execution -ceq 'not_run' -and
            $row.requires_native_target_qualification -is [bool] -and $row.requires_native_target_qualification) 'CASE_SCOPE'
        $expected='?p09_crossref_discovery_anchor;6;'+[int][Math]::Floor($i/2)+';'+($i%2)+';0'
        Assert-P09XrefCondition ($row.sdk_command -is [string] -and $row.sdk_command -ceq $expected) 'CASE_MATRIX'
        $receipt=$row.source_binding_receipt
        Assert-P09XrefCondition ($receipt.requires_native_target_qualification -is [bool] -and
            $receipt.requires_native_target_qualification) 'TARGET_REQUIRES_QUALIFICATION'
        Assert-P09XrefDigestArray $receipt.command_sha256 (Get-P09XrefDigest ([Text.Encoding]::UTF8.GetBytes($expected)))
        Assert-P09XrefDigestArray $receipt.source.source_package_sha256 $inputSha
        Assert-P09XrefFalse $receipt.source.complete_reference_state_qualified
        Assert-P09XrefCondition ($receipt.source.bookmark_targets -eq 1 -and $receipt.source.observed_native_fields -eq 1 -and
            $receipt.source.ambiguous_source_names -eq 0) 'ACTUAL_SOURCE_TARGET_COUNTS'
        # Equal batch identity is required; no XML id/instId/note-index guess is admitted.
        $source=$receipt.source | ConvertTo-Json -Depth 12 -Compress
        $target=$receipt.target_state_sha256 | ConvertTo-Json -Compress
        $logical=$receipt.logical_target_id_sha256 | ConvertTo-Json -Compress
        if ($i -eq 0) {$sourceReceipt=$source;$targetDigest=$target;$logicalDigest=$logical}
        Assert-P09XrefCondition ($source -ceq $sourceReceipt -and $target -ceq $targetDigest -and $logical -ceq $logicalDigest) 'BATCH_TARGET_BINDING'
    }
    $observed=$Packet.generated_input_observations
    Assert-P09XrefCondition ($observed.status -ceq 'source_observation_only' -and $observed.crossref_fields -eq 0 -and
        @($observed.candidates).Count -eq 8) 'BASELINE_OBSERVATION'
    foreach ($name in @('causal_insertion_or_preservation_proved','complete_reference_validation_qualified',
            'native_execution_attested','parameter_key_semantics_qualified')) {Assert-P09XrefFalse $observed.$name}
    foreach ($row in $observed.candidates) {
        Assert-P09XrefCondition ($row.observation -ceq 'not_observed') 'UNQUALIFIED_BASELINE'
    }
    return [ordered]@{case_count=8;native_execution_authorized=$false;native_ready=$false;
        complete_reference_state_qualified=$false;separate_from_frozen_p58_full34_queue=$true}
}
