[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedTextSha256,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

$runner = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot 'run-hancom-2020-tab-readback.ps1'
)).Path
$input = (Resolve-Path -LiteralPath $InputPath).Path
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $input)).Path.TrimEnd('\')
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
if (-not $traceFile.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'PAGE_SETUP_READBACK_PATH_OUTSIDE_FIXTURE_BOUNDARY'
}
if (Test-Path -LiteralPath $traceFile) { throw 'PAGE_SETUP_READBACK_OUTPUT_ALREADY_EXISTS' }
$innerTrace = $traceFile + '.inner.' + [string]$PID + '.json'
if (Test-Path -LiteralPath $innerTrace) { throw 'PAGE_SETUP_READBACK_INNER_TRACE_ALREADY_EXISTS' }

$powerShell = Join-Path $PSHOME 'powershell.exe'
$arguments = @(
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $runner,
    '-InputPath', $input,
    '-ExpectedInputSha256', $ExpectedInputSha256,
    '-OutputPath', ([System.IO.Path]::GetFullPath($OutputPath)),
    '-TracePath', $innerTrace,
    '-ExpectedTextSha256', $ExpectedTextSha256,
    '-ProgId', $ProgId,
    '-ExpectedBuild', $ExpectedBuild,
    '-ExpectedExecutableSha256', $ExpectedExecutableSha256
)

& $powerShell @arguments | Out-Null
$childExitCode = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $innerTrace -PathType Leaf)) {
    throw 'PAGE_SETUP_READBACK_INNER_TRACE_MISSING'
}
$trace = Get-Content -LiteralPath $innerTrace -Raw | ConvertFrom-Json
$innerSchema = [string]$trace.schema_version
$trace.schema_version = 'hwpx-agent.p05-06-hancom-2020-page-setup-readback/v1'
$trace | Add-Member -NotePropertyName delegated_engine_schema -NotePropertyValue $innerSchema
if ($null -ne $trace.error_code) {
    $trace.error_code = ([string]$trace.error_code).Replace('TAB_READBACK_', 'PAGE_SETUP_READBACK_')
}
$json = $trace | ConvertTo-Json -Depth 8
Write-NewUtf8File -Path $traceFile -Content $json
[System.IO.File]::Delete($innerTrace)
$json
if ($childExitCode -ne 0 -or $trace.state -ne 'pass') { exit 2 }
