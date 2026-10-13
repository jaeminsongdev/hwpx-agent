Set-StrictMode -Version Latest
. "$PSScriptRoot/resource_bounded_test_support.ps1"
function ConvertTo-P121SafeTestResult {
    param([string]$Output)
    $result = ConvertTo-P09SafeTestResult -Output $Output
    $result['changed_corpus_result'] = $null
    $result['changed_protection_pass'] = $false
    $result['outside_leaf_counterexamples_pass'] = $false
    $result['panic_locations'] = @()
    $result['returned_error_kinds'] = @()
    foreach ($line in ($Output -split '\r?\n')) {
        if ($line -match '(crates[\\/][A-Za-z0-9_\\/.-]+\.rs):(\d+):(\d+):$' -and $line.Contains('panicked at')) {
            $result['panic_locations'] += [ordered]@{path=$Matches[1];line=[int]$Matches[2];column=[int]$Matches[3]}
        }
        if ($line.StartsWith('Error:')) {
            $kind='returned_error_redacted'
            if ($line -match '^Error: ([A-Za-z0-9_:]+)(?:[({ ]|$)' -and
                @('Binding','NoChange','NoTargets','ParseIntError','Utf8Error','Evaluation','Lowering','Claims','Protection') -ccontains $Matches[1]) { $kind=$Matches[1] }
            $result['returned_error_kinds'] += $kind
        }
        if ($line -eq 'P121_PROTECTED_CHANGED_RECEIPT:32_signed_changed_and_current_denied_NOT_native_or_production_trust') { $result['changed_protection_pass'] = $true }
        if ($line -eq 'P121_OUTSIDE_LEAF_COUNTEREXAMPLES_RECEIPT:16_changed_candidate_input_tampers_denied_NOT_native_or_production_trust') { $result['outside_leaf_counterexamples_pass'] = $true }
        if ($line.StartsWith('P121_CHANGED_CORPUS_RECEIPT:')) {
            $corpus = $line.Substring('P121_CHANGED_CORPUS_RECEIPT:'.Length) | ConvertFrom-Json -ErrorAction Stop
            if (($corpus.cases -isnot [long] -and $corpus.cases -isnot [int]) -or $corpus.cases -ne 16 -or $corpus.rows.Count -ne 16) { throw 'invalid_changed_corpus_count' }
            $rows = @()
            foreach ($row in $corpus.rows) {
                if (($row.index -isnot [long] -and $row.index -isnot [int]) -or $row.index -lt 0 -or $row.index -ge 36) { throw 'invalid_changed_original_index' }
                $safe = [ordered]@{index=$row.index}
                foreach ($key in @('original_sha256','derivative_sha256','candidate_sha256')) {
                    if ($row.$key -cnotmatch '^[0-9a-f]{64}$') { throw 'invalid_changed_digest' }
                    $safe[$key]=$row.$key
                }
                foreach ($key in @('formula_targets','source_cell_bindings','changed_parts')) {
                    if (($row.$key -isnot [long] -and $row.$key -isnot [int]) -or $row.$key -lt 1 -or $row.$key -gt 128) { throw 'invalid_changed_counter' }
                    $safe[$key]=$row.$key
                }
                foreach ($key in @('only_numeric_input_leaf_changed','outside_result_leaves_exact','signed_changed_and_current_noop_verified','live_revocation_and_rebinding_denied_callback')) {
                    if ($row.$key -isnot [bool]) { throw 'invalid_changed_bool' }
                    $safe[$key]=$row.$key
                }
                $rows += $safe
            }
            $result['changed_corpus_result'] = [ordered]@{cases=$corpus.cases;rows=$rows}
        }
    }
    return $result
}
