Set-StrictMode -Version Latest

function Get-P09ResourceDecision {
    param([double]$SystemCpuPercent, [double]$FreeMemoryMiB,
          [double]$TestWorkingSetMiB, [int]$HotSamples,
          [double]$CpuThreshold = 85, [int]$RequiredHotSamples = 3,
          [double]$MinimumFreeMiB = 4096, [double]$MaximumTestMiB = 2048)
    if ($FreeMemoryMiB -lt $MinimumFreeMiB) { return 'STOP_LOW_AVAILABLE_RAM' }
    if ($TestWorkingSetMiB -gt $MaximumTestMiB) { return 'STOP_TEST_RAM_LIMIT' }
    if ($SystemCpuPercent -ge $CpuThreshold -and $HotSamples -ge $RequiredHotSamples) {
        return 'STOP_SUSTAINED_SYSTEM_CPU'
    }
    return 'CONTINUE'
}

function Get-P09CpuMask {
    param([long]$AllowedMask, [int]$Count = 2)
    if ($Count -lt 1 -or $Count -gt 2 -or $AllowedMask -le 0) { throw 'invalid_cpu_affinity_policy' }
    [long]$chosen = 0
    $selected = 0
    for ($bit = 0; $bit -lt 63 -and $selected -lt $Count; $bit++) {
        [long]$flag = [long]1 -shl $bit
        if (($AllowedMask -band $flag) -ne 0) { $chosen = $chosen -bor $flag; $selected++ }
    }
    if ($selected -ne $Count) { throw 'insufficient_allowed_processors' }
    return $chosen
}

function Get-P09ResourceSample {
    param([System.Diagnostics.Process]$TestProcess)
    $cpu = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" -Property PercentProcessorTime -ErrorAction Stop
    $memory = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -Property AvailableMBytes -ErrorAction Stop
    $workingSet = 0
    $testCpu = 0
    if ($null -ne $TestProcess -and -not $TestProcess.HasExited) {
        $TestProcess.Refresh()
        $workingSet = [math]::Round($TestProcess.WorkingSet64 / 1MB, 2)
        $testCpu = [math]::Round($TestProcess.TotalProcessorTime.TotalSeconds, 2)
    }
    return [ordered]@{time_utc=[datetime]::UtcNow.ToString('o'); system_cpu_percent=[double]$cpu.PercentProcessorTime;
        available_ram_mib=[double]$memory.AvailableMBytes; test_working_set_mib=$workingSet; test_cpu_seconds=$testCpu}
}

function ConvertTo-P09SafeTestResult {
    param([string]$Output)
    $result = [ordered]@{terminal_summary=$null; corpus_result=$null; current_derivatives_pass=$false;
        protection_derivatives_pass=$false; passed_test_names=@(); failed_test_names=@()}
    foreach ($line in ($Output -split '\r?\n')) {
        if ($line -match '^test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out; finished in ([0-9.]+)s$') {
            $result.terminal_summary = [ordered]@{outcome=$Matches[1];passed=[int]$Matches[2];failed=[int]$Matches[3];
                ignored=[int]$Matches[4];measured=[int]$Matches[5];filtered=[int]$Matches[6];seconds=[double]$Matches[7]}
        }
        if ($line -match '^test ([a-zA-Z0-9_:]+) \.\.\. (ok|FAILED)$') {
            if ($Matches[2] -eq 'ok') { $result.passed_test_names += $Matches[1] }
            else { $result.failed_test_names += $Matches[1] }
        }
        if ($line -eq 'P120_CURRENT_DERIVATIVES_RECEIPT:16_signed_exact_noop_expiry_and_new_denial_pass_NOT_native_or_production_trust') { $result.current_derivatives_pass = $true }
        if ($line -eq 'P120_PROTECTION_DERIVATIVES_RECEIPT:32_signed_protected_original_and_current_denials_pass_NOT_native_or_production_trust') { $result.protection_derivatives_pass = $true }
        if ($line.StartsWith('P120_ORIGINAL_CORPUS_RECEIPT:')) {
            $corpus = $line.Substring('P120_ORIGINAL_CORPUS_RECEIPT:'.Length) | ConvertFrom-Json -ErrorAction Stop
            if ($corpus.counts.Count -ne 6 -or $corpus.originals.Count -ne 36) { throw 'invalid_corpus_receipt_shape' }
            foreach ($count in $corpus.counts) {
                if (($count -isnot [long] -and $count -isnot [int]) -or $count -lt 0 -or $count -gt 128) { throw 'invalid_corpus_count' }
            }
            $rows = @()
            foreach ($row in $corpus.originals) {
                if ($row.source_sha256 -cnotmatch '^[0-9a-f]{64}$' -or ($row.index -isnot [long] -and $row.index -isnot [int]) -or $row.index -lt 0 -or $row.index -ge 36) { throw 'invalid_corpus_source_identity' }
                $safe = [ordered]@{index=$row.index;source_sha256=$row.source_sha256;outcome=$row.outcome}
                if ($row.outcome -notin @('changed','unchanged','no_formula_denied_no_policy_proof_or_result')) { throw 'invalid_corpus_outcome' }
                if ($row.outcome -ne 'no_formula_denied_no_policy_proof_or_result') {
                    if ($row.candidate_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'invalid_corpus_candidate_identity' }
                    foreach ($key in @('formula_targets','source_cell_bindings')) {
                        if (($row.$key -isnot [long] -and $row.$key -isnot [int]) -or $row.$key -lt 1 -or $row.$key -gt 128) { throw 'invalid_corpus_target_count' }
                    }
                    foreach ($key in @('whole_candidate_and_outside_leaves_exact','live_revocation_denied_callback')) {
                        if ($row.$key -isnot [bool]) { throw 'invalid_corpus_boolean' }
                    }
                    foreach ($key in @('candidate_sha256','formula_targets','source_cell_bindings','whole_candidate_and_outside_leaves_exact','live_revocation_denied_callback')) { $safe[$key] = $row.$key }
                }
                $rows += $safe
            }
            $result.corpus_result = [ordered]@{counts=$corpus.counts;originals=$rows}
        }
    }
    return $result
}
