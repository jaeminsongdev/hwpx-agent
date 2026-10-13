Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../resource_bounded_test_support.ps1"
function Assert-Equal($actual,$expected) { if ($actual -cne $expected) { throw 'resource_policy_assertion_failed' } }
Assert-Equal (Get-P09CpuMask -AllowedMask 65535 -Count 2) 3
Assert-Equal (Get-P09CpuMask -AllowedMask 20 -Count 2) 20
Assert-Equal (Get-P09CpuMask -AllowedMask 20 -Count 1) 4
$rejected = $false
try { Get-P09CpuMask -AllowedMask 1 -Count 2 | Out-Null } catch { $rejected=$true }
Assert-Equal $rejected $true
Assert-Equal (Get-P09ResourceDecision 20 8192 512 0) 'CONTINUE'
Assert-Equal (Get-P09ResourceDecision 85 8192 512 2) 'CONTINUE'
Assert-Equal (Get-P09ResourceDecision 85 8192 512 3) 'STOP_SUSTAINED_SYSTEM_CPU'
Assert-Equal (Get-P09ResourceDecision 20 4095 512 0) 'STOP_LOW_AVAILABLE_RAM'
Assert-Equal (Get-P09ResourceDecision 20 8192 2049 0) 'STOP_TEST_RAM_LIMIT'
Assert-Equal (Get-P09ResourceDecision 84 4096 2048 0) 'CONTINUE'
$safe = ConvertTo-P09SafeTestResult "test actual_import::sample ... ok`ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 224 filtered out; finished in 1.23s`nPRIVATE_CONTENT_MUST_NOT_PERSIST"
Assert-Equal $safe.terminal_summary.passed 1
Assert-Equal $safe.terminal_summary.filtered 224
Assert-Equal $safe.passed_test_names.Count 1
Assert-Equal (($safe | ConvertTo-Json -Depth 8).Contains('PRIVATE_CONTENT_MUST_NOT_PERSIST')) $false
Assert-Equal (ConvertTo-P09SafeTestResult 'incomplete output').terminal_summary $null
$rejected = $false
try { ConvertTo-P09SafeTestResult 'P120_ORIGINAL_CORPUS_RECEIPT:{"counts":["PRIVATE"],"originals":[]}' | Out-Null } catch { $rejected=$true }
Assert-Equal $rejected $true
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
foreach ($runner in @(
    @{path='run_resource_bounded_tests.ps1'; freeze='Test-SourceFreeze'},
    @{path='build_resource_optimized_tests.ps1'; freeze='Test-BuildSourceFreeze'})) {
    $text = [IO.File]::ReadAllText((Join-Path $PSScriptRoot ('../' + $runner.path)))
    $resourceIndex = $text.IndexOf('$before = Get-P09ResourceSample', [StringComparison]::Ordinal)
    $deferIndex = $text.IndexOf('if ($before.system_cpu_percent -ge 85', [StringComparison]::Ordinal)
    $freezeMatches = [regex]::Matches($text, '(?m)^' + [regex]::Escape($runner.freeze) + '\s*$')
    Assert-Equal ($resourceIndex -ge 0 -and $deferIndex -gt $resourceIndex -and
        $freezeMatches.Count -eq 1 -and $freezeMatches[0].Index -gt $deferIndex) $true
}
$buildText = [IO.File]::ReadAllText((Join-Path $PSScriptRoot '../build_resource_optimized_tests.ps1'))
$launchIndex = $buildText.IndexOf("if (-not `$proc.Start())", [StringComparison]::Ordinal)
$firstDescendantLimitIndex = $buildText.IndexOf('Set-BuildTreeLimits -ParentIds @($proc.Id)', [StringComparison]::Ordinal)
$firstWaitIndex = $buildText.IndexOf('while (-not $proc.WaitForExit(5000))', [StringComparison]::Ordinal)
Assert-Equal ($launchIndex -ge 0 -and $firstDescendantLimitIndex -gt $launchIndex -and
    $firstDescendantLimitIndex -lt $firstWaitIndex) $true
Assert-Equal ($buildText.Contains('$sample.test_process_tree_working_set_mib') -and
    $buildText.Contains('Get-BuildTreeWorkingSetMiB -State $treeState')) $true
Write-Output 'PASS: resource policy 20 assertions; no actual native/SQL/test/build process execution'
