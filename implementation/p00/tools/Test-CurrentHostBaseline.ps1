[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [string]$BaselinePath = 'implementation/p00/evidence/current-host-baseline.20260901.json',
    [string]$OutputPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory '..\..\..'))
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

function Get-SafeProjectPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path,
        [switch]$MustExist
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $candidate = if ([System.IO.Path]::IsPathRooted($Path)) {
        [System.IO.Path]::GetFullPath($Path)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $rootFull $Path))
    }
    $prefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the project root: $Path"
    }
    if ($MustExist -and -not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Required project file was not found: $Path"
    }
    return $candidate
}

function Get-RelativeProjectPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path
    )

    $rootUri = [System.Uri]::new(([System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar))
    $pathUri = [System.Uri]::new([System.IO.Path]::GetFullPath($Path))
    return [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString()).Replace('\', '/')
}

$projectRootFull = (Resolve-Path -LiteralPath $ProjectRoot).Path
$baselineFull = Get-SafeProjectPath -Root $projectRootFull -Path $BaselinePath -MustExist
$baseline = Get-Content -LiteralPath $baselineFull -Raw -Encoding UTF8 | ConvertFrom-Json

if ($baseline.schema_version -ne 'hwpx-agent.current-host-baseline/v1') {
    throw 'Unsupported current-host baseline schema version.'
}
if ($baseline.state -ne 'pass_current_pc_local_development_baseline') {
    throw 'The current-host baseline is not in the required pass state.'
}
if ($baseline.pinned_environment.scope.authority -ne 'user_directive_2026-09-01_current_pc_only' -or
    $baseline.pinned_environment.scope.host_policy -ne 'this_current_pc_only') {
    throw 'The baseline is not bound to the user-authorized current-PC-only scope.'
}
if ($baseline.pinned_environment.host.classification -ne 'mutable_current_development_pc' -or
    [bool]$baseline.pinned_environment.host.clean_image_claimed) {
    throw 'The baseline incorrectly claims clean-image qualification.'
}
if (-not $baseline.claims.current_pc_local_p01_development_ready -or
    $baseline.claims.clean_immutable_image_qualified -or
    $baseline.claims.other_pc_or_version_supported -or
    $baseline.claims.production_or_distribution_ready) {
    throw 'The baseline claims exceed the authorized current-PC development scope.'
}

$canonicalPinnedEnvironment = [string]$baseline.pinned_environment_canonical_json
if ([string]::IsNullOrWhiteSpace($canonicalPinnedEnvironment)) {
    throw 'The current-host baseline has no sealed canonical environment payload.'
}
$recomputedDigest = Get-TextSha256 -Value $canonicalPinnedEnvironment
if ($recomputedDigest -ne [string]$baseline.baseline_digest_sha256) {
    throw 'The current-host baseline digest does not match its pinned environment.'
}
$sealedEnvironment = $canonicalPinnedEnvironment | ConvertFrom-Json
$displayEnvironmentJson = $baseline.pinned_environment | ConvertTo-Json -Depth 32 -Compress
$sealedEnvironmentJson = $sealedEnvironment | ConvertTo-Json -Depth 32 -Compress
if ($displayEnvironmentJson -ne $sealedEnvironmentJson) {
    throw 'The displayed pinned environment does not match the sealed canonical payload.'
}

foreach ($evidence in $sealedEnvironment.evidence) {
    $evidenceFull = Get-SafeProjectPath -Root $projectRootFull -Path ([string]$evidence.relative_path) -MustExist
    $item = Get-Item -LiteralPath $evidenceFull
    if ([int64]$item.Length -ne [int64]$evidence.bytes) {
        throw "Evidence byte length changed: $($evidence.relative_path)"
    }
    $actualHash = (Get-FileHash -LiteralPath $evidenceFull -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne [string]$evidence.sha256) {
        throw "Evidence SHA-256 changed: $($evidence.relative_path)"
    }
}

$machineGuid = [string](Get-ItemPropertyValue -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid)
$machineBinding = Get-TextSha256 -Value ("hwpx-agent/current-host/v1`n" + $machineGuid)
if ($machineBinding -ne [string]$sealedEnvironment.host.machine_binding_sha256) {
    throw 'The baseline belongs to a different Windows installation.'
}

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
$currentVersion = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
if ([string]$os.Caption -ne [string]$sealedEnvironment.host.os_caption -or
    [string]$os.Version -ne [string]$sealedEnvironment.host.os_version -or
    [string]$os.BuildNumber -ne [string]$sealedEnvironment.host.os_build -or
    [int]$currentVersion.UBR -ne [int]$sealedEnvironment.host.os_ubr -or
    [string]$os.OSArchitecture -ne [string]$sealedEnvironment.host.os_architecture) {
    throw 'The live Windows baseline no longer matches the sealed environment.'
}

$targetPath = (Resolve-Path -LiteralPath ([string]$sealedEnvironment.target.executable_path)).Path
$targetItem = Get-Item -LiteralPath $targetPath
$targetHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ([string]$targetItem.VersionInfo.FileVersion -ne [string]$sealedEnvironment.target.executable_file_version -or
    [int64]$targetItem.Length -ne [int64]$sealedEnvironment.target.executable_bytes -or
    $targetHash -ne [string]$sealedEnvironment.target.executable_sha256) {
    throw 'The live Hangul 2020 executable no longer matches the sealed environment.'
}

$classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::ClassesRoot,
    [Microsoft.Win32.RegistryView]::Registry32
)
$progIdKey = $null
$clsidKey = $null
$serverKey = $null
try {
    $progIdKey = $classesRoot.OpenSubKey([string]$sealedEnvironment.target.prog_id)
    if ($null -eq $progIdKey) {
        throw 'The sealed Registry32 HWP ProgID is not registered.'
    }
    $clsidKey = $progIdKey.OpenSubKey('CLSID')
    if ($null -eq $clsidKey) {
        throw 'The sealed Registry32 HWP ProgID has no CLSID.'
    }
    $liveClsid = [string]$clsidKey.GetValue('')
    if ($liveClsid -ne [string]$sealedEnvironment.target.clsid) {
        throw 'The live Registry32 HWP CLSID no longer matches the sealed environment.'
    }
    $serverKey = $classesRoot.OpenSubKey("CLSID\$liveClsid\LocalServer32")
    if ($null -eq $serverKey) {
        throw 'The live Registry32 HWP CLSID has no LocalServer32 registration.'
    }
    $serverCommand = [string]$serverKey.GetValue('')
}
finally {
    if ($null -ne $serverKey) { $serverKey.Dispose() }
    if ($null -ne $clsidKey) { $clsidKey.Dispose() }
    if ($null -ne $progIdKey) { $progIdKey.Dispose() }
    $classesRoot.Dispose()
}
$serverMatch = [regex]::Match(
    $serverCommand.Trim(),
    '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)
if (-not $serverMatch.Success) {
    throw 'Unable to parse the live Registry32 HWP LocalServer32 command.'
}
$registeredTargetPath = (Resolve-Path -LiteralPath $serverMatch.Groups['path'].Value).Path
if (-not $registeredTargetPath.Equals($targetPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The live Registry32 HWP server path no longer matches the sealed environment.'
}

$fontPath = (Resolve-Path -LiteralPath ([string]$sealedEnvironment.font.file_path)).Path
$fontItem = Get-Item -LiteralPath $fontPath
$fontHash = (Get-FileHash -LiteralPath $fontPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ([int64]$fontItem.Length -ne [int64]$sealedEnvironment.font.bytes -or
    $fontHash -ne [string]$sealedEnvironment.font.sha256) {
    throw 'The live HCR Batang font no longer matches the sealed environment.'
}

$printerName = [string]$sealedEnvironment.pdf_export.printer_name
$printers = @(Get-CimInstance Win32_Printer -ErrorAction Stop | Where-Object { $_.Name -eq $printerName })
if ($printers.Count -ne 1 -or
    [string]$printers[0].DriverName -ne [string]$sealedEnvironment.pdf_export.driver_name -or
    [string]$printers[0].PortName -ne [string]$sealedEnvironment.pdf_export.port_name) {
    throw 'The live Hancom PDF printer no longer matches the sealed environment.'
}
$printerDrivers = @(Get-CimInstance Win32_PrinterDriver -ErrorAction Stop | Where-Object {
    $_.Name -eq [string]$printers[0].DriverName -or $_.Name -like (([string]$printers[0].DriverName) + ',*')
})
if ($printerDrivers.Count -ne 1) {
    throw 'The live Hancom PDF printer driver is missing or ambiguous.'
}
$printerDriver = $printerDrivers[0]
$driverCandidatePaths = @(
    [string]$printerDriver.DriverPath,
    [string]$printerDriver.ConfigFile,
    [string]$printerDriver.DataFile,
    [string]$printerDriver.HelpFile,
    @($printerDriver.DependentFiles)
) | ForEach-Object { $_ } | Where-Object {
    -not [string]::IsNullOrWhiteSpace([string]$_) -and (Test-Path -LiteralPath ([string]$_) -PathType Leaf)
} | Select-Object -Unique
foreach ($expectedDriverFile in $sealedEnvironment.pdf_export.driver_files) {
    $driverPathMatches = @($driverCandidatePaths | Where-Object {
        [System.IO.Path]::GetFileName([string]$_).Equals([string]$expectedDriverFile.file, [System.StringComparison]::OrdinalIgnoreCase)
    })
    if ($driverPathMatches.Count -ne 1) {
        throw "A sealed Hancom PDF driver file is missing or ambiguous: $($expectedDriverFile.file)"
    }
    $driverItem = Get-Item -LiteralPath ([string]$driverPathMatches[0])
    $driverHash = (Get-FileHash -LiteralPath $driverItem.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ([int64]$driverItem.Length -ne [int64]$expectedDriverFile.bytes -or $driverHash -ne [string]$expectedDriverFile.sha256) {
        throw "A live Hancom PDF driver file no longer matches the sealed environment: $($expectedDriverFile.file)"
    }
}

$runningHwp = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($runningHwp.Count -ne 0) {
    throw 'The current-host verification requires zero running Hwp.exe processes.'
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.current-host-baseline-verification/v1'
    checked_at = (Get-Date).ToString('o')
    state = 'pass'
    baseline_relative_path = Get-RelativeProjectPath -Root $projectRootFull -Path $baselineFull
    baseline_file_sha256 = (Get-FileHash -LiteralPath $baselineFull -Algorithm SHA256).Hash.ToLowerInvariant()
    baseline_digest_sha256 = $recomputedDigest
    checks = [ordered]@{
        digest_match = $true
        evidence_files_match = $true
        machine_binding_match = $true
        windows_baseline_match = $true
        exact_hancom_2020_match = $true
        hcr_batang_match = $true
        hancom_pdf_binding_match = $true
        hancom_pdf_driver_files_match = $true
        current_hwp_processes = 0
        clean_image_claimed = $false
        scope_overclaim_detected = $false
    }
}

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $outputFull = Get-SafeProjectPath -Root $projectRootFull -Path $OutputPath
    $outputDirectory = Split-Path -Parent $outputFull
    if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
        throw "Output directory does not exist: $outputDirectory"
    }
    $json = $result | ConvertTo-Json -Depth 16
    [System.IO.File]::WriteAllText($outputFull, ($json + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
}

[pscustomobject]$result
