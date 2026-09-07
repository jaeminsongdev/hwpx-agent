[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$measurePath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\measure-hancom-2020-layout-font.ps1'
)).Path
$verifyPath = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\tools\verify-current-font-metric-receipt.py'
)).Path
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$runRoot = [System.IO.Path]::GetFullPath((
    Join-Path $repositoryRoot 'artifacts\p06\font-metric-runs'
))
$measureSource = [System.IO.File]::ReadAllText($measurePath)
$verifySource = [System.IO.File]::ReadAllText($verifyPath)
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $measurePath, [ref]$tokens, [ref]$parseErrors
)

$firstRun = [guid]::NewGuid().ToString('N')
$secondRun = [guid]::NewGuid().ToString('N')
$firstDirectory = Join-Path $runRoot $firstRun
$secondDirectory = Join-Path $runRoot $secondRun
$checks = [ordered]@{}
try {
    $firstReceiptPath = (& $measurePath -RunId $firstRun | Select-Object -Last 1)
    $secondReceiptPath = (& $measurePath -RunId $secondRun | Select-Object -Last 1)
    $firstVerification = & python $verifyPath --receipt $firstReceiptPath | ConvertFrom-Json
    $firstVerifyExit = $LASTEXITCODE
    $secondVerification = & python $verifyPath --receipt $secondReceiptPath | ConvertFrom-Json
    $secondVerifyExit = $LASTEXITCODE
    $first = Get-Content -LiteralPath $firstReceiptPath -Raw | ConvertFrom-Json
    $second = Get-Content -LiteralPath $secondReceiptPath -Raw | ConvertFrom-Json

    $duplicateRejected = $false
    try { & $measurePath -RunId $firstRun | Out-Null }
    catch { $duplicateRejected = [string]$_.Exception.Message -ceq 'RUN_ALREADY_EXISTS' }

    $checks = [ordered]@{
        script_parses = $parseErrors.Count -eq 0
        both_measurements_succeed = (Test-Path -LiteralPath $firstReceiptPath -PathType Leaf) -and
            (Test-Path -LiteralPath $secondReceiptPath -PathType Leaf)
        both_verifiers_succeed = $firstVerifyExit -eq 0 -and $secondVerifyExit -eq 0 -and
            $firstVerification.state -ceq 'pass' -and $secondVerification.state -ceq 'pass'
        exact_target = $first.target.hangul_build -ceq '11.0.0.9136' -and
            $first.target.executable_sha256 -ceq
                '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce' -and
            $first.target.font_file_sha256 -ceq
                '0dbeb7b129fcec63f8d6b7f1d3b5bb991c1d599e725286518ccc598de643f014'
        exact_profile = $first.profile_id -ceq
            'hwpx-agent.font-metric.gdiplus-typographic-96dpi/1'
        repeat_is_exact = $first.measurement.repeat_count -eq 2
        four_bounded_cells = @($first.cells).Count -eq 4 -and
            @($first.cells | Where-Object {
                $_.minimum_content_width_micrometers -le 0 -or
                $_.preferred_content_width_micrometers -lt
                    $_.minimum_content_width_micrometers -or
                $_.line_height_micrometers -le 0
            }).Count -eq 0
        cross_run_deterministic = $first.measurement_set_sha256 -ceq
            $second.measurement_set_sha256 -and
            $first.measurement_set_sha256 -ceq
                '96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9' -and
            (($first.cells | ConvertTo-Json -Depth 5 -Compress) -ceq
                ($second.cells | ConvertTo-Json -Depth 5 -Compress))
        no_raw_text = -not ((Get-Content -LiteralPath $firstReceiptPath -Raw) -match
            'P06-05 A|WIDE-CONTENT-1234567890') -and
            @($first.cells | Where-Object { $_.PSObject.Properties.Name -contains 'text' }).Count -eq 0
        no_user_document = $first.user_document_opened -eq $false
        no_hwp_process = $first.hwp_process_created -eq $false
        create_new = $measureSource -match 'FileMode\]::CreateNew' -and $duplicateRejected
        no_ui_input = ($measureSource + $verifySource) -notmatch
            '(?i)(SendKeys|mouse_event|SetCursorPos|PostMessage|SendMessage)'
        no_network = ($measureSource + $verifySource) -notmatch
            '(?i)(Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer|requests\.|urllib\.)'
        no_registry_write = ($measureSource + $verifySource) -notmatch
            '(?i)(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty|winreg\.)'
        no_completion_promotion = $first.actual_hangul_renderer -eq $false -and
            $first.product_complete -eq $false -and
            $firstVerification.actual_hangul_renderer -eq $false -and
            $firstVerification.product_complete -eq $false
    }
}
finally {
    foreach ($directory in @($firstDirectory, $secondDirectory)) {
        $full = [System.IO.Path]::GetFullPath($directory)
        if ([System.IO.Directory]::Exists($full) -and
            $full.StartsWith($runRoot + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
            [regex]::IsMatch((Split-Path -Leaf $full), '^[0-9a-f]{32}$')) {
            [System.IO.Directory]::Delete($full, $true)
        }
    }
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
[ordered]@{
    schema_version = 'hwpx-agent.p06-05-current-font-metric-static-tests/v1'
    total = $checks.Count
    passed = $checks.Count - $failed.Count
    failed = $failed.Count
    cases = @($checks.GetEnumerator() | ForEach-Object {
        [ordered]@{ case = $_.Key; passed = [bool]$_.Value }
    })
} | ConvertTo-Json -Depth 5
if ($failed.Count -ne 0) { exit 1 }
