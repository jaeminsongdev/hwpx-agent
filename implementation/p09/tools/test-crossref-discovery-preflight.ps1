# Source/pure contracts only; the actual x86 preflight is a separate owned command.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
. (Join-Path $PSScriptRoot 'crossref-discovery-preflight-library.ps1')
$path=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/prepared-sdk-batch.v1.json'
$item=Get-Item -LiteralPath $path
Assert-P09XrefCondition ($item.Length -eq 42762) 'TEST_PACKET_SIZE'
$bytes=[IO.File]::ReadAllBytes($path)
Assert-P09XrefCondition ((Get-P09XrefDigest $bytes) -ceq '1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1') 'TEST_PACKET_PIN'
$json=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
$script:passed=0
function New-P09XrefTestPacket {return ($json | ConvertFrom-Json)}
function Assert-P09XrefReject($Packet) {
    $rejected=$false
    try {[void](Assert-P09XrefFixedPacket $Packet)} catch {$rejected=$true}
    Assert-P09XrefCondition $rejected 'TEST_INVALID_PACKET_ACCEPTED'
}
function Invoke-P09XrefTest([string]$Name,[scriptblock]$Body) {
    & $Body
    $script:passed++
}
try {
    Invoke-P09XrefTest 'actual_fixed_packet_all_eight' {
        $value=Assert-P09XrefFixedPacket (New-P09XrefTestPacket)
        Assert-P09XrefCondition ($value.case_count -eq 8 -and -not $value.native_ready -and -not $value.native_execution_authorized) 'TEST_VALID_SUMMARY'
    }
    Invoke-P09XrefTest 'no_subset_reorder_or_duplicate' {
        $p=New-P09XrefTestPacket;$p.cases=@($p.cases[0..6]);Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;$p.cases[0]=$p.cases[1];Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;[Array]::Reverse($p.cases);Assert-P09XrefReject $p
    }
    Invoke-P09XrefTest 'each_command_matrix_entry_is_exact' {
        for ($i=0;$i -lt 8;$i++) {
            $p=New-P09XrefTestPacket;$p.cases[$i].sdk_command+=';0';Assert-P09XrefReject $p
        }
    }
    Invoke-P09XrefTest 'each_source_and_command_digest_bound' {
        for ($i=0;$i -lt 8;$i++) {
            $p=New-P09XrefTestPacket;$p.cases[$i].source_binding_receipt.command_sha256[0]=
                [int]$p.cases[$i].source_binding_receipt.command_sha256[0] -bxor 1;Assert-P09XrefReject $p
            $p=New-P09XrefTestPacket;$p.cases[$i].source_binding_receipt.source.source_package_sha256[0]=
                [int]$p.cases[$i].source_binding_receipt.source.source_package_sha256[0] -bxor 1;Assert-P09XrefReject $p
        }
    }
    Invoke-P09XrefTest 'false_flags_require_actual_boolean_false' {
        foreach ($name in @('native_execution_authorized','native_executed','native_attempt_created','public_raw_action_route','p09_complete')) {
            foreach ($value in @($true,0,'false')) {$p=New-P09XrefTestPacket;$p.$name=$value;Assert-P09XrefReject $p}
        }
    }
    Invoke-P09XrefTest 'batch_target_and_frozen_queue_binding' {
        $p=New-P09XrefTestPacket;$p.cases[7].source_binding_receipt.logical_target_id_sha256[0]=
            [int]$p.cases[7].source_binding_receipt.logical_target_id_sha256[0] -bxor 1;Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;$p.generated_input_pin.bytes++;Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;$p.separate_from_frozen_p58_full34_queue=$false;Assert-P09XrefReject $p
    }
    Invoke-P09XrefTest 'baseline_does_not_attest_native_or_matching_output' {
        $p=New-P09XrefTestPacket;$p.generated_input_observations.candidates[7].observation='observed';Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;$p.generated_input_observations.native_execution_attested=$true;Assert-P09XrefReject $p
        $p=New-P09XrefTestPacket;$p.generated_input_observations.crossref_fields=1;Assert-P09XrefReject $p
    }
    Invoke-P09XrefTest 'actual_preflight_ast_has_no_native_or_write_route' {
        $source=Join-Path $PSScriptRoot 'inspect-crossref-discovery-preflight.ps1'
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
        Assert-P09XrefCondition (@($errors).Count -eq 0) 'TEST_PREFLIGHT_SYNTAX'
        $parameters=@($ast.ParamBlock.Parameters | ForEach-Object {$_.Name.VariablePath.UserPath})
        Assert-P09XrefCondition ($parameters.Count -eq 2 -and
            ($parameters -join ',') -ceq 'ExpectedHarnessSha256,ExpectedLibrarySha256') 'TEST_NO_NATIVE_OR_PATH_SWITCH'
        $commands=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst]},$true))
        $forbidden=@('New-Object','Add-Type','Start-Process','Invoke-Command','Invoke-Expression','New-Item',
            'Set-Content','Add-Content','Out-File','Remove-Item','Move-Item','Set-ItemProperty','Stop-Process')
        foreach ($command in $commands) {
            Assert-P09XrefCondition ($command.GetCommandName() -cnotin $forbidden) 'TEST_FORBIDDEN_COMMAND'
        }
        $text=$ast.Extent.Text
        Assert-P09XrefCondition ($text -cnotmatch '(?i)ComObject|GetActiveObject|GetTypeFromProgID|CreateInstance|FileAccess\]::Write|FileMode\]::Create|\.SaveAs\(' -and
            $text.Contains('[IO.File]::Open($item.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)')) 'TEST_NO_ACTIVATION_OR_FILE_WRITE'
    }
    Assert-P09XrefCondition ($script:passed -eq 8) 'TEST_EXACT_CONTRACT_COUNT'
    [ordered]@{state='eight_preflight_contracts_pass_not_native';passed=$script:passed;failed=0;
        actual_x86_preflight_executed=$false;native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    [ordered]@{state='preflight_contract_failed';passed=$script:passed;failed=1;error_code='P09_XREF_PREFLIGHT_CONTRACT_FAILED';
        native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
