[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Za-z][A-Za-z0-9._-]{2,63}$')]
    [string]$ExpectedRegistrationName,

    [ValidatePattern('^$|^[0-9a-f]{64}$')]
    [string]$ExpectedSha256 = '',

    [Parameter(Mandatory)]
    [string]$EvidencePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
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

function Test-X86PeFile {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read
    )
    try {
        $reader = [System.IO.BinaryReader]::new($stream)
        try {
            if ($stream.Length -lt 64 -or $reader.ReadUInt16() -ne 0x5a4d) { return $false }
            $stream.Position = 0x3c
            $offset = $reader.ReadUInt32()
            if ($offset -gt $stream.Length - 6) { return $false }
            $stream.Position = $offset
            return $reader.ReadUInt32() -eq 0x00004550 -and $reader.ReadUInt16() -eq 0x014c
        }
        finally { $reader.Dispose() }
    }
    finally { $stream.Dispose() }
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$evidenceRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'fixtures\target-build'))
$evidence = [System.IO.Path]::GetFullPath($EvidencePath)
$prefix = $evidenceRoot.TrimEnd('\') + '\'
if (-not $evidence.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) -or
    [System.IO.Path]::GetExtension($evidence) -cne '.json') {
    throw 'P10_05_EVIDENCE_OUTSIDE_TARGET_BUILD_ROOT'
}
if (Test-Path -LiteralPath $evidence) { throw 'P10_05_EVIDENCE_ALREADY_EXISTS' }

$keyPresent = $false
$registrationCount = 0
$expectedPresent = $false
$valueIsString = $false
$pathIsAbsolute = $false
$fileExists = $false
$fileIsRegular = $false
$fileIsBounded = $false
$hashReadable = $false
$digestMatches = $null
$x86 = $false

$base = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::CurrentUser,
    [Microsoft.Win32.RegistryView]::Registry32
)
try {
    $modules = $base.OpenSubKey('Software\HNC\HwpAutomation\Modules', $false)
    try {
        if ($null -ne $modules) {
            $keyPresent = $true
            $names = @($modules.GetValueNames())
            $registrationCount = $names.Count
            $expectedPresent = $names -ccontains $ExpectedRegistrationName
            if ($expectedPresent -and
                $modules.GetValueKind($ExpectedRegistrationName) -eq
                    [Microsoft.Win32.RegistryValueKind]::String) {
                $valueIsString = $true
                $configured = $modules.GetValue(
                    $ExpectedRegistrationName,
                    $null,
                    [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
                )
                if ($configured -is [string]) {
                    $pathIsAbsolute = [System.IO.Path]::IsPathFullyQualified($configured)
                    if ($pathIsAbsolute) {
                        $fileExists = [System.IO.File]::Exists($configured)
                        if ($fileExists) {
                            $item = Get-Item -LiteralPath $configured -Force
                            $fileIsRegular = -not $item.PSIsContainer -and
                                ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0
                            $fileIsBounded = $fileIsRegular -and
                                $item.Extension -ieq '.dll' -and
                                $item.Length -gt 0 -and $item.Length -le 16777216
                            if ($fileIsBounded) {
                                try {
                                    $actualHash = (Get-FileHash -LiteralPath $configured -Algorithm SHA256).Hash.ToLowerInvariant()
                                    $hashReadable = $true
                                    if (-not [string]::IsNullOrEmpty($ExpectedSha256)) {
                                        $digestMatches = $actualHash -ceq $ExpectedSha256
                                    }
                                    $x86 = Test-X86PeFile -Path $configured
                                }
                                catch {
                                    $hashReadable = $false
                                    $digestMatches = if ([string]::IsNullOrEmpty($ExpectedSha256)) { $null } else { $false }
                                    $x86 = $false
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    finally { if ($null -ne $modules) { $modules.Dispose() } }
}
finally { $base.Dispose() }

$ready = $keyPresent -and $expectedPresent -and $valueIsString -and $pathIsAbsolute -and
    $fileExists -and $fileIsRegular -and $fileIsBounded -and $hashReadable -and $x86 -and
    -not [string]::IsNullOrEmpty($ExpectedSha256) -and $digestMatches -eq $true
$result = [ordered]@{
    schema_version = 'hwpx-agent.p10-05-security-module-probe/v1'
    state = if ($ready) { 'ready' } else { 'not_ready' }
    target_profile_id = 'hancom-hangul-2020-secondary'
    product_build = '11.0.0.9136'
    process_architecture = 'x86'
    registry_view = 'Registry32'
    registry_hive = 'CurrentUser'
    registry_key_present = $keyPresent
    registration_count = $registrationCount
    expected_registration_present = $expectedPresent
    registration_value_is_string = $valueIsString
    registered_path_is_absolute = $pathIsAbsolute
    registered_file_exists = $fileExists
    registered_file_is_regular = $fileIsRegular
    registered_file_is_bounded_dll = $fileIsBounded
    registered_file_hash_readable = $hashReadable
    expected_digest_supplied = -not [string]::IsNullOrEmpty($ExpectedSha256)
    registered_file_digest_matches_expected = $digestMatches
    registered_file_is_x86 = $x86
    registered_path_present_in_evidence = $false
    raw_registry_value_present_in_evidence = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
}
Write-NewUtf8File -Path $evidence -Content (($result | ConvertTo-Json -Depth 4) + "`n")
$result | ConvertTo-Json -Depth 4
if (-not $ready) { exit 2 }
