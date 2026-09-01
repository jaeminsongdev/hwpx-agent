[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [string]$CollectorPath = '',
    [string]$VerifierPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory '..\..\..'))
}
if ([string]::IsNullOrWhiteSpace($CollectorPath)) {
    $CollectorPath = Join-Path $scriptDirectory '..\tools\New-CurrentHostBaseline.ps1'
}
if ([string]::IsNullOrWhiteSpace($VerifierPath)) {
    $VerifierPath = Join-Path $scriptDirectory '..\tools\Test-CurrentHostBaseline.ps1'
}

function Get-TextSha256 {
    param([Parameter(Mandatory)][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Value)
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

$projectRootFull = (Resolve-Path -LiteralPath $ProjectRoot).Path
$testId = [guid]::NewGuid().ToString('N')
$baselineRelative = "tmp/current-host-baseline-$testId.json"
$verificationRelative = "tmp/current-host-verification-$testId.json"
$digestTamperRelative = "tmp/current-host-digest-tamper-$testId.json"
$traversalTamperRelative = "tmp/current-host-traversal-tamper-$testId.json"
$temporaryPaths = @(
    (Join-Path $projectRootFull $baselineRelative),
    (Join-Path $projectRootFull $verificationRelative),
    (Join-Path $projectRootFull $digestTamperRelative),
    (Join-Path $projectRootFull $traversalTamperRelative)
)
$passed = 0
$failed = 0
$results = [System.Collections.Generic.List[object]]::new()

function Add-TestResult {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][bool]$Passed,
        [Parameter(Mandatory)][string]$Detail
    )

    $script:results.Add([pscustomobject]@{
        name = $Name
        passed = $Passed
        detail = $Detail
    })
    if ($Passed) {
        $script:passed++
    }
    else {
        $script:failed++
    }
}

try {
    $beforeHwp = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    Add-TestResult -Name 'precondition_zero_hwp' -Passed ($beforeHwp.Count -eq 0) -Detail "count=$($beforeHwp.Count)"

    $collection = & $CollectorPath -ProjectRoot $projectRootFull -OutputPath $baselineRelative
    Add-TestResult -Name 'collector_live_pass' -Passed ($collection.state -eq 'pass_current_pc_local_development_baseline') -Detail ([string]$collection.state)

    $verification = & $VerifierPath -ProjectRoot $projectRootFull -BaselinePath $baselineRelative -OutputPath $verificationRelative
    Add-TestResult -Name 'verifier_live_pass' -Passed ($verification.state -eq 'pass') -Detail ([string]$verification.state)

    $baseline = Get-Content -LiteralPath $temporaryPaths[0] -Raw -Encoding UTF8 | ConvertFrom-Json
    $baseline.pinned_environment_canonical_json = ([string]$baseline.pinned_environment_canonical_json + ' ')
    $digestTamperJson = $baseline | ConvertTo-Json -Depth 32
    [System.IO.File]::WriteAllText($temporaryPaths[2], ($digestTamperJson + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    $digestTamperRejected = $false
    try {
        $null = & $VerifierPath -ProjectRoot $projectRootFull -BaselinePath $digestTamperRelative
    }
    catch {
        $digestTamperRejected = $_.Exception.Message -match 'digest does not match'
    }
    Add-TestResult -Name 'digest_tamper_rejected' -Passed $digestTamperRejected -Detail 'fail-closed digest check'

    $baseline = Get-Content -LiteralPath $temporaryPaths[0] -Raw -Encoding UTF8 | ConvertFrom-Json
    $sealedEnvironment = [string]$baseline.pinned_environment_canonical_json | ConvertFrom-Json
    $sealedEnvironment.evidence[0].relative_path = '../outside-project.json'
    $baseline.pinned_environment.evidence[0].relative_path = '../outside-project.json'
    $canonical = $sealedEnvironment | ConvertTo-Json -Depth 32 -Compress
    $baseline.pinned_environment_canonical_json = $canonical
    $baseline.baseline_digest_sha256 = Get-TextSha256 -Value $canonical
    $traversalTamperJson = $baseline | ConvertTo-Json -Depth 32
    [System.IO.File]::WriteAllText($temporaryPaths[3], ($traversalTamperJson + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    $traversalTamperRejected = $false
    try {
        $null = & $VerifierPath -ProjectRoot $projectRootFull -BaselinePath $traversalTamperRelative
    }
    catch {
        $traversalTamperRejected = $_.Exception.Message -match 'escapes the project root'
    }
    Add-TestResult -Name 'path_traversal_rejected' -Passed $traversalTamperRejected -Detail 'fail-closed evidence path check'

    $afterHwp = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    Add-TestResult -Name 'postcondition_zero_hwp' -Passed ($afterHwp.Count -eq 0) -Detail "count=$($afterHwp.Count)"
}
finally {
    foreach ($temporaryPath in $temporaryPaths) {
        if (Test-Path -LiteralPath $temporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}

$summary = [pscustomobject]@{
    state = if ($failed -eq 0) { 'pass' } else { 'failed' }
    passed = $passed
    total = $passed + $failed
    tests = @($results)
}
$summary
if ($failed -ne 0) {
    throw "Current-host baseline kit tests failed: $failed"
}
