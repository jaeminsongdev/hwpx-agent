[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$QualifiedBundlePath,

    [string]$VerifierPath = (Join-Path $PSScriptRoot '..\tools\Test-HancomDiagnosticBundle.ps1')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-AllBytes {
    param([Parameter(Mandatory)]$Entry)
    $source = $Entry.Open()
    $target = New-Object System.IO.MemoryStream
    try {
        $source.CopyTo($target)
        return $target.ToArray()
    }
    finally {
        $target.Dispose()
        $source.Dispose()
    }
}

function Invoke-VerifierCase {
    param(
        [Parameter(Mandatory)][string]$Case,
        [Parameter(Mandatory)][string]$Bundle,
        [Parameter(Mandatory)][string]$ExpectedState,
        [AllowNull()][string]$ExpectedError,
        [switch]$RequireQualified
    )
    $output = if ($RequireQualified) {
        & $script:ResolvedVerifier -BundlePath $Bundle -RequireQualified 2>&1 | Out-String
    }
    else {
        & $script:ResolvedVerifier -BundlePath $Bundle 2>&1 | Out-String
    }
    $result = $output | ConvertFrom-Json
    $actualError = if ($null -eq $result.verification_error_code) { $null } else { [string]$result.verification_error_code }
    return [pscustomobject]@{
        case = $Case
        expected_bundle_state = $ExpectedState
        actual_bundle_state = [string]$result.bundle_state
        expected_verification_error_code = $ExpectedError
        actual_verification_error_code = $actualError
        passed = [string]$result.bundle_state -ceq $ExpectedState -and $actualError -ceq $ExpectedError
    }
}

$qualifiedBundle = (Resolve-Path -LiteralPath $QualifiedBundlePath).Path
$script:ResolvedVerifier = (Resolve-Path -LiteralPath $VerifierPath).Path
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('hwpx-agent-diagnostic-kit-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$results = @()

try {
    $validOutput = & $script:ResolvedVerifier -BundlePath $qualifiedBundle -RequireQualified 2>&1 | Out-String
    $validResult = $validOutput | ConvertFrom-Json
    $results += [pscustomobject]@{
        case = 'qualified_bundle'
        expected_bundle_state = 'valid'
        actual_bundle_state = [string]$validResult.bundle_state
        expected_verification_error_code = $null
        actual_verification_error_code = $validResult.verification_error_code
        passed = $validResult.bundle_state -eq 'valid' -and $validResult.qualification_state -eq 'pass' -and $null -eq $validResult.verification_error_code
    }

    $unsafeZip = Join-Path $testRoot 'unsafe-path.zip'
    Copy-Item -LiteralPath $qualifiedBundle -Destination $unsafeZip
    $stream = [System.IO.File]::Open($unsafeZip, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Update, $false)
    try {
        $entry = $archive.CreateEntry('../escape.json')
        $bytes = [System.Text.Encoding]::UTF8.GetBytes('{}')
        $target = $entry.Open()
        try {
            $target.Write($bytes, 0, $bytes.Length)
        }
        finally {
            $target.Dispose()
        }
    }
    finally {
        $archive.Dispose()
        $stream.Dispose()
    }
    $results += Invoke-VerifierCase -Case 'zip_path_traversal' -Bundle $unsafeZip -ExpectedState 'invalid' -ExpectedError 'ZIP_UNSAFE_PATH'

    $tamperedZip = Join-Path $testRoot 'manifest-content-tamper.zip'
    Copy-Item -LiteralPath $qualifiedBundle -Destination $tamperedZip
    $stream = [System.IO.File]::Open($tamperedZip, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Update, $false)
    try {
        $entry = $archive.GetEntry('events.json')
        $originalBytes = Read-AllBytes -Entry $entry
        $entry.Delete()
        $replacement = $archive.CreateEntry('events.json')
        $target = $replacement.Open()
        try {
            $target.Write($originalBytes, 0, $originalBytes.Length)
            $target.WriteByte(0x20)
        }
        finally {
            $target.Dispose()
        }
    }
    finally {
        $archive.Dispose()
        $stream.Dispose()
    }
    $results += Invoke-VerifierCase -Case 'manifest_content_tamper' -Bundle $tamperedZip -ExpectedState 'invalid' -ExpectedError 'MANIFEST_SIZE_MISMATCH'
}
finally {
    if (Test-Path -LiteralPath $testRoot -PathType Container) {
        $resolvedTestRoot = (Resolve-Path -LiteralPath $testRoot).Path
        $resolvedTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
        $expectedPrefix = $resolvedTemp + '\hwpx-agent-diagnostic-kit-test-'
        if (-not $resolvedTestRoot.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected diagnostic test directory: $resolvedTestRoot"
        }
        [System.IO.Directory]::Delete($resolvedTestRoot, $true)
    }
}

$failed = @($results | Where-Object { -not $_.passed })
[ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-kit-test/v1'
    total = $results.Count
    passed = $results.Count - $failed.Count
    failed = $failed.Count
    cases = @($results)
} | ConvertTo-Json -Depth 7

if ($failed.Count -ne 0) {
    exit 1
}
