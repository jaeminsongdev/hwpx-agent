Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/../changed_formula_test_support.ps1"
function Assert-P121($condition) { if (-not $condition) { throw 'changed_resource_policy_assertion_failed' } }
Assert-P121 ((Get-P09CpuMask -AllowedMask 65535 -Count 2) -eq 3)
Assert-P121 ((Get-P09ResourceDecision 85 8192 512 3) -eq 'STOP_SUSTAINED_SYSTEM_CPU')
Assert-P121 ((Get-P09ResourceDecision 20 4095 512 0) -eq 'STOP_LOW_AVAILABLE_RAM')
$result=ConvertTo-P121SafeTestResult "test actual_import::changed ... ok`ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 227 filtered out; finished in 1.00s`nPRIVATE_CONTENT_MUST_NOT_PERSIST"
Assert-P121 ($result.terminal_summary.passed -eq 1 -and $result.terminal_summary.filtered -eq 227)
Assert-P121 (-not ($result|ConvertTo-Json -Depth 8).Contains('PRIVATE_CONTENT_MUST_NOT_PERSIST'))
$row=@{index=0;original_sha256=('a'*64);derivative_sha256=('b'*64);candidate_sha256=('c'*64);formula_targets=1;source_cell_bindings=8;changed_parts=1;only_numeric_input_leaf_changed=$true;outside_result_leaves_exact=$true;signed_changed_and_current_noop_verified=$true;live_revocation_and_rebinding_denied_callback=$true;private_key='MUST_NOT_PERSIST'}
$payload=@{cases=16;rows=@(0..15|ForEach-Object {$copy=$row.Clone();$copy.index=$_;$copy})}
$projected=ConvertTo-P121SafeTestResult ('P121_CHANGED_CORPUS_RECEIPT:'+($payload|ConvertTo-Json -Depth 5 -Compress))
Assert-P121 ($projected.changed_corpus_result.rows.Count -eq 16)
Assert-P121 (-not ($projected|ConvertTo-Json -Depth 8).Contains('MUST_NOT_PERSIST'))
foreach ($bad in @('count','digest','integer','boolean')) {
    $copy=$payload|ConvertTo-Json -Depth 5|ConvertFrom-Json
    if ($bad -eq 'count') {$copy.cases=15}
    elseif ($bad -eq 'digest') {$copy.rows[0].candidate_sha256='invalid'}
    elseif ($bad -eq 'integer') {$copy.rows[0].formula_targets=$true}
    else {$copy.rows[0].outside_result_leaves_exact='PRIVATE'}
    $rejected=$false
    try {ConvertTo-P121SafeTestResult ('P121_CHANGED_CORPUS_RECEIPT:'+($copy|ConvertTo-Json -Depth 5 -Compress))|Out-Null} catch {$rejected=$true}
    Assert-P121 $rejected
}
$diagnostic=ConvertTo-P121SafeTestResult "thread 'redacted' panicked at crates\product-cli\tests\redacted.rs:20:9:`nPRIVATE_MESSAGE_MUST_NOT_PERSIST`nError: ParseIntError { PRIVATE_MESSAGE_MUST_NOT_PERSIST }`nError: PRIVATE_TOKEN_MUST_NOT_PERSIST"
Assert-P121 ($diagnostic.panic_locations.Count -eq 1 -and $diagnostic.panic_locations[0].line -eq 20)
Assert-P121 ($diagnostic.returned_error_kinds[0] -ceq 'ParseIntError' -and $diagnostic.returned_error_kinds[1] -ceq 'returned_error_redacted')
Assert-P121 (-not ($diagnostic|ConvertTo-Json -Depth 8).Contains('MUST_NOT_PERSIST'))
Write-Output 'PASS: P121 resource/parser 14 assertions; no actual native/SQL/test process execution'
