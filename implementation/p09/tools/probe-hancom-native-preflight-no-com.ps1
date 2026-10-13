[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedInputSha256,
    [Parameter(Mandatory)][string]$RunDirectory,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$errorPrefix = 'P09_FIELD_AUTO_NUMBER_TARGET'
$securityModuleName = 'FilePathCheckerModuleExample'
$securityModuleSha256 = '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write,
        [IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Assert-RegularBoundedFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$MinimumBytes,
        [Parameter(Mandatory)][long]$MaximumBytes
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw ($errorPrefix + '_OUTPUT_MISSING')
    }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -lt $MinimumBytes -or $item.Length -gt $MaximumBytes) {
        throw ($errorPrefix + '_OUTPUT_NOT_BOUNDED_REGULAR_FILE')
    }
    return $item
}

function Get-OwnedHwpIdentity {
    param(
        [Parameter(Mandatory)][datetime]$StartedAt,
        [Parameter(Mandatory)][int]$SessionId,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )
    $candidates = @()
    foreach ($candidate in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'")) {
        if ([int]$candidate.SessionId -ne $SessionId -or
            $null -eq $candidate.CreationDate -or
            [datetime]$candidate.CreationDate -lt $StartedAt.AddSeconds(-2)) {
            continue
        }
        $path = [string]$candidate.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($path) -or
            -not (Test-Path -LiteralPath $path -PathType Leaf) -or
            (Get-Sha256File -Path $path) -cne $ExpectedSha256) {
            continue
        }
        $candidates += $candidate
    }
    if ($candidates.Count -ne 1) {
        throw ($errorPrefix + '_OWNED_PROCESS_IDENTITY_AMBIGUOUS')
    }
    $candidate = $candidates[0]
    return [ordered]@{
        process_id = [int]$candidate.ProcessId
        session_id = [int]$candidate.SessionId
        executable_sha256 = $ExpectedSha256
        command_line_sha256 = Get-Sha256String -Value ([string]$candidate.CommandLine)
    }
}

function New-ExactHwpSession {
    param(
        [Parameter(Mandatory)][string]$SessionLabel,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Trace
    )
    $startedAt = Get-Date
    $hwp = New-Object -ComObject $ProgId
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne $ExpectedBuild) {
        Clear-ComObject $hwp
        throw ($errorPrefix + '_VERSION_MISMATCH')
    }
    $registerReturn = [bool]$hwp.RegisterModule('FilePathCheckDLL', $securityModuleName)
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $identity = Get-OwnedHwpIdentity -StartedAt $startedAt `
        -SessionId ([Diagnostics.Process]::GetCurrentProcess().SessionId) `
        -ExpectedSha256 $ExpectedExecutableSha256
    [void]$Trace.sessions.Add([ordered]@{
        label = $SessionLabel
        version = $version
        register_module_return = $registerReturn
        process = $identity
    })
    return [ordered]@{ hwp = $hwp; window = $window; documents = $hwp.XHwpDocuments }
}

function Close-HwpSession {
    param([AllowNull()]$Session)
    if ($null -eq $Session) { return }
    $hwp = $Session.hwp
    try { if ($null -ne $hwp) { $hwp.Quit() } } catch { }
    Clear-ComObject $Session.documents
    Clear-ComObject $Session.window
    Clear-ComObject $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$privateBoundaryPath = Join-Path $root 'implementation\p09\evidence\private'
[void][IO.Directory]::CreateDirectory($privateBoundaryPath)
$privateBoundary = (Resolve-Path -LiteralPath $privateBoundaryPath).Path.TrimEnd('\')
$fixturesBoundary = (Resolve-Path -LiteralPath (
    Join-Path $root 'fixtures\target-build'
)).Path.TrimEnd('\')
$input = (Resolve-Path -LiteralPath $InputPath).Path
$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if (-not $input.StartsWith($fixturesBoundary + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Get-Sha256File -Path $input) -cne $ExpectedInputSha256) {
    throw ($errorPrefix + '_INPUT_IDENTITY_MISMATCH')
}
$inputItem = Assert-RegularBoundedFile -Path $input -MinimumBytes 1 -MaximumBytes 4194304
if (-not $run.StartsWith($privateBoundary + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $run) -cnotmatch '^p09-17-field-auto-number-target-[a-z0-9-]{1,80}$' -or
    (Test-Path -LiteralPath $run)) {
    throw ($errorPrefix + '_RUN_DIRECTORY_INVALID')
}
if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw ($errorPrefix + '_CLIENT_NOT_STA')
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}

$securityModulePath = Join-Path (
    [Environment]::GetFolderPath('LocalApplicationData')
) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
$securityModuleItem = Get-Item -LiteralPath $securityModulePath -Force
if ($securityModuleItem.PSIsContainer -or
    ($securityModuleItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $securityModuleItem.Length -ne 217229 -or
    (Get-Sha256File -Path $securityModuleItem.FullName) -cne $securityModuleSha256) {
    throw ($errorPrefix + '_SECURITY_MODULE_IDENTITY_MISMATCH')
}
$securityModuleRegistryKey = Get-Item -LiteralPath (
    'Registry::HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules'
)
try {
    if ([string]$securityModuleRegistryKey.GetValueKind($securityModuleName) -cne 'String' -or
        [string]$securityModuleRegistryKey.GetValue($securityModuleName) -cne
            $securityModuleItem.FullName) {
        throw ($errorPrefix + '_SECURITY_MODULE_REGISTRY_MISMATCH')
    }
}
finally { $securityModuleRegistryKey.Dispose() }

[Console]::Write('P09_EXACT_PRE_NATIVE_PREFIX_PASS')
exit 0
