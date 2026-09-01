[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [string]$OutputPath = 'implementation/p00/evidence/current-host-baseline.20260901.json',
    [string]$RuntimeProbePath = 'implementation/p00/evidence/runtime-probe.2020.20260901.v3.json',
    [string]$DocumentReceiptPath = 'implementation/p00/evidence/document-smoke-runs/98798b1801314a5e9bebf0f2505bc763/receipt.json',
    [string]$FontPrinterEvidencePath = 'implementation/p00/evidence/font-printer-reference-smoke.20260901.json',
    [string]$SourceLockPowerShell7Path = 'implementation/p00/evidence/source-lock-verification.20260901.v9.json',
    [string]$SourceLockWindowsPowerShellPath = 'implementation/p00/evidence/source-lock-verification.20260901.v9.windows-powershell.json'
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

function Get-EvidenceRecord {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$RelativePath
    )

    $fullPath = Get-SafeProjectPath -Root $Root -Path $RelativePath -MustExist
    $item = Get-Item -LiteralPath $fullPath
    return [ordered]@{
        relative_path = (Get-RelativeProjectPath -Root $Root -Path $fullPath)
        bytes = [int64]$item.Length
        sha256 = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Read-JsonFile {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$RelativePath
    )

    $fullPath = Get-SafeProjectPath -Root $Root -Path $RelativePath -MustExist
    return (Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8 | ConvertFrom-Json)
}

$projectRootFull = (Resolve-Path -LiteralPath $ProjectRoot).Path
$outputFull = Get-SafeProjectPath -Root $projectRootFull -Path $OutputPath
$outputDirectory = Split-Path -Parent $outputFull
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    throw "Output directory does not exist: $outputDirectory"
}

$runningHwp = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
if ($runningHwp.Count -ne 0) {
    throw 'Refusing to seal the current-host baseline while an Hwp.exe process is running.'
}

$runtimeProbe = Read-JsonFile -Root $projectRootFull -RelativePath $RuntimeProbePath
$receipt = Read-JsonFile -Root $projectRootFull -RelativePath $DocumentReceiptPath
$fontPrinter = Read-JsonFile -Root $projectRootFull -RelativePath $FontPrinterEvidencePath
$sourceLockPowerShell7 = Read-JsonFile -Root $projectRootFull -RelativePath $SourceLockPowerShell7Path
$sourceLockWindowsPowerShell = Read-JsonFile -Root $projectRootFull -RelativePath $SourceLockWindowsPowerShellPath
$licenseEvidence = Read-JsonFile -Root $projectRootFull -RelativePath 'implementation/p00/evidence/user-license-scope-confirmation.20260901.json'

if ($runtimeProbe.state -ne 'pass' -or $runtimeProbe.target_profile_id -ne 'hancom-hangul-2020-secondary') {
    throw 'The accepted exact-target runtime probe is not in the required pass state.'
}
if ($receipt.state -ne 'pass' -or $receipt.target_profile_id -ne 'hancom-hangul-2020-secondary') {
    throw 'The accepted document smoke receipt is not in the required pass state.'
}
if ($receipt.observed_file_version -ne '11.0.0.9136' -or -not $receipt.automation_version_matches_expected) {
    throw 'The document smoke receipt does not bind exact Hangul 2020 build 11.0.0.9136.'
}
if (-not $receipt.text_exact_match_after_document_separator_normalization -or
    -not $receipt.hwpx.package_verification.valid -or
    -not $receipt.pdf.file_verification.valid -or
    -not $receipt.quit_invoked -or
    [int]$receipt.preexisting_hwp_processes -ne 0 -or
    [int]$receipt.remaining_hwp_processes -ne 0) {
    throw 'The accepted document smoke receipt does not satisfy the current-host oracle invariants.'
}
if ($receipt.user_document_opened -or -not $receipt.generated_document_only -or
    $receipt.register_module_invoked -or $receipt.external_network_invoked -or
    $receipt.registry_or_system_setting_changed -or $receipt.computer_use_click_or_type_invoked) {
    throw 'The document smoke receipt violates a privacy or scope invariant.'
}
foreach ($phaseProperty in $receipt.phases.PSObject.Properties) {
    if ([string]$phaseProperty.Value -ne 'pass') {
        throw "Document smoke phase is not pass: $($phaseProperty.Name)"
    }
}
if ($fontPrinter.state -ne 'pass_current_2020_reference_scope' -or
    -not $fontPrinter.font_observation.substitution_zero_for_fixture -or
    -not $fontPrinter.font_observation.pdf_font.embedded) {
    throw 'The accepted font/printer evidence is not in the required current-host pass state.'
}
foreach ($lock in @($sourceLockPowerShell7, $sourceLockWindowsPowerShell)) {
    if ($lock.state -ne 'pass' -or [int]$lock.local_failure_count -ne 0 -or [int]$lock.remote_failure_count -ne 0) {
        throw 'A required source-lock verification is not in the pass state.'
    }
}
if (-not $licenseEvidence.user_confirmations.personal_noncommercial_local_development -or
    -not $licenseEvidence.user_confirmations.installed_product_seat_is_genuine_and_valid) {
    throw 'The current local license/use-scope confirmation is missing.'
}

$executablePath = (Resolve-Path -LiteralPath ([string]$runtimeProbe.executable_path)).Path
$executableItem = Get-Item -LiteralPath $executablePath
$executableSha256 = (Get-FileHash -LiteralPath $executablePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ([string]$executableItem.VersionInfo.FileVersion -ne '11.0.0.9136' -or
    $executableSha256 -ne '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce') {
    throw 'The live Hangul executable no longer matches the accepted exact target.'
}

$classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::ClassesRoot,
    [Microsoft.Win32.RegistryView]::Registry32
)
$progIdKey = $null
$clsidKey = $null
$serverKey = $null
try {
    $progIdKey = $classesRoot.OpenSubKey('HWPFrame.HwpObject.2')
    if ($null -eq $progIdKey) {
        throw 'The required Registry32 HWP ProgID is not registered.'
    }
    $clsidKey = $progIdKey.OpenSubKey('CLSID')
    if ($null -eq $clsidKey) {
        throw 'The required Registry32 HWP ProgID has no CLSID.'
    }
    $clsid = [string]$clsidKey.GetValue('')
    $serverKey = $classesRoot.OpenSubKey("CLSID\$clsid\LocalServer32")
    if ($null -eq $serverKey) {
        throw 'The required Registry32 HWP CLSID has no LocalServer32 registration.'
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
    throw 'Unable to parse the Registry32 HWP LocalServer32 command.'
}
$registeredExecutablePath = (Resolve-Path -LiteralPath $serverMatch.Groups['path'].Value).Path
if (-not $registeredExecutablePath.Equals($executablePath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The live Registry32 HWP registration does not point to the accepted executable.'
}

$fontPath = (Resolve-Path -LiteralPath ([string]$fontPrinter.font_observation.installed_file.path)).Path
$fontItem = Get-Item -LiteralPath $fontPath
$fontSha256 = (Get-FileHash -LiteralPath $fontPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($fontSha256 -ne [string]$fontPrinter.font_observation.installed_file.sha256) {
    throw 'The live HCR Batang font no longer matches the accepted evidence.'
}

$printerName = [string]$fontPrinter.pdf_export.printer_name
$printers = @(Get-CimInstance Win32_Printer -ErrorAction Stop | Where-Object { $_.Name -eq $printerName })
if ($printers.Count -ne 1) {
    throw "Expected exactly one current Hancom PDF printer, observed $($printers.Count)."
}
$printer = $printers[0]
if ([string]$printer.DriverName -ne [string]$fontPrinter.pdf_export.driver_name -or
    [string]$printer.PortName -ne [string]$fontPrinter.pdf_export.port_name) {
    throw 'The live Hancom PDF printer binding no longer matches the accepted evidence.'
}
$printerDrivers = @(Get-CimInstance Win32_PrinterDriver -ErrorAction Stop | Where-Object {
    $_.Name -eq [string]$printer.DriverName -or $_.Name -like (([string]$printer.DriverName) + ',*')
})
if ($printerDrivers.Count -ne 1) {
    throw "Expected exactly one current Hancom PDF printer driver, observed $($printerDrivers.Count)."
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
$driverRecords = @($fontPrinter.pdf_export.driver_files | Sort-Object file | ForEach-Object {
    $expectedDriverFile = $_
    $driverPathMatches = @($driverCandidatePaths | Where-Object {
        [System.IO.Path]::GetFileName([string]$_).Equals([string]$expectedDriverFile.file, [System.StringComparison]::OrdinalIgnoreCase)
    })
    if ($driverPathMatches.Count -ne 1) {
        throw "Expected exactly one live Hancom PDF driver file: $($expectedDriverFile.file)"
    }
    $driverItem = Get-Item -LiteralPath ([string]$driverPathMatches[0])
    $driverHash = (Get-FileHash -LiteralPath $driverItem.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ([int64]$driverItem.Length -ne [int64]$expectedDriverFile.bytes -or $driverHash -ne [string]$expectedDriverFile.sha256) {
        throw "The live Hancom PDF driver file no longer matches accepted evidence: $($expectedDriverFile.file)"
    }
    [ordered]@{
        file = [string]$expectedDriverFile.file
        bytes = [int64]$driverItem.Length
        version = [string]$expectedDriverFile.version
        sha256 = $driverHash
    }
})

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
$currentVersion = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$machineGuid = [string](Get-ItemPropertyValue -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid)
if ([string]::IsNullOrWhiteSpace($machineGuid)) {
    throw 'The current host cannot be privately bound because MachineGuid is unavailable.'
}
$machineBinding = Get-TextSha256 -Value ("hwpx-agent/current-host/v1`n" + $machineGuid)
$installDate = if ($os.InstallDate -is [datetime]) {
    ([datetime]$os.InstallDate).ToUniversalTime().ToString('o')
}
else {
    [string]$os.InstallDate
}

$evidencePaths = @(
    'implementation/p00/target-profile.yaml',
    'implementation/p00/tools/New-CurrentHostBaseline.ps1',
    'implementation/p00/tools/Test-CurrentHostBaseline.ps1',
    'implementation/p00/tests/Test-CurrentHostBaselineKit.ps1',
    'implementation/p00/schemas/current-host-baseline.schema.json',
    'implementation/p00/schemas/current-host-baseline-verification.schema.json',
    $RuntimeProbePath,
    $DocumentReceiptPath,
    $FontPrinterEvidencePath,
    'implementation/p00/evidence/official-source-rights.20260901.json',
    'implementation/p00/evidence/user-license-scope-confirmation.20260901.json',
    $SourceLockPowerShell7Path,
    $SourceLockWindowsPowerShellPath
)
$evidenceRecords = @($evidencePaths | ForEach-Object {
    Get-EvidenceRecord -Root $projectRootFull -RelativePath $_
})

$pinnedEnvironment = [ordered]@{
    scope = [ordered]@{
        authority = 'user_directive_2026-09-01_current_pc_only'
        use = 'personal_noncommercial_local_development'
        host_policy = 'this_current_pc_only'
        target_policy = 'exact_hancom_hangul_2020_only'
        other_versions_state = 'deferred_until_their_installed_pc_is_available'
        production_release_state = 'disabled'
    }
    host = [ordered]@{
        classification = 'mutable_current_development_pc'
        clean_image_claimed = $false
        machine_binding_sha256 = $machineBinding
        machine_binding_raw_value_stored = $false
        os_caption = [string]$os.Caption
        os_version = [string]$os.Version
        os_build = [string]$os.BuildNumber
        os_ubr = [int]$currentVersion.UBR
        os_architecture = [string]$os.OSArchitecture
        os_install_date_utc = $installDate
        locale = [string](Get-Culture).Name
        ui_culture = [string](Get-UICulture).Name
    }
    target = [ordered]@{
        profile_id = 'hancom-hangul-2020-secondary'
        product = 'Hancom Hangul 2020'
        exact_build = '11.0.0.9136'
        executable_architecture = 'x86'
        executable_path = $executablePath
        executable_bytes = [int64]$executableItem.Length
        executable_file_version = [string]$executableItem.VersionInfo.FileVersion
        executable_sha256 = $executableSha256
        prog_id = 'HWPFrame.HwpObject.2'
        clsid = $clsid
        com_registry_view = 'Registry32'
        registered_executable_path = $registeredExecutablePath
    }
    font = [ordered]@{
        family = 'HCR Batang'
        korean_family = [string]$fontPrinter.font_observation.requested_hwp_family
        file_path = $fontPath
        bytes = [int64]$fontItem.Length
        sha256 = $fontSha256
        fixture_substitution_zero = $true
        pdf_embedded = $true
    }
    pdf_export = [ordered]@{
        printer_name = $printerName
        driver_name = [string]$printer.DriverName
        port_name = [string]$printer.PortName
        producer = [string]$fontPrinter.pdf_export.producer
        driver_files = $driverRecords
    }
    oracle = [ordered]@{
        run_id = [string]$receipt.run_id
        exact_normalized_text_readback = $true
        hwpx_sha256 = [string]$receipt.hwpx.sha256
        pdf_sha256 = [string]$receipt.pdf.sha256
        quit_invoked = $true
        remaining_hwp_processes = 0
    }
    source_lock = [ordered]@{
        source_lock_id = [string]$sourceLockPowerShell7.source_lock_id
        entries = [int]$sourceLockPowerShell7.source_count
        local_matches = [int]$sourceLockPowerShell7.local_match_count
        remote_matches = [int]$sourceLockPowerShell7.remote_match_count
        powershell_7_state = [string]$sourceLockPowerShell7.state
        windows_powershell_5_1_state = [string]$sourceLockWindowsPowerShell.state
    }
    evidence = $evidenceRecords
}

$canonicalPinnedEnvironment = $pinnedEnvironment | ConvertTo-Json -Depth 32 -Compress
$baselineDigest = Get-TextSha256 -Value $canonicalPinnedEnvironment
$generatedAt = (Get-Date).ToString('o')
$manifest = [ordered]@{
    schema_version = 'hwpx-agent.current-host-baseline/v1'
    generated_at = $generatedAt
    state = 'pass_current_pc_local_development_baseline'
    baseline_digest_sha256 = $baselineDigest
    digest_canonicalization = 'stored-utf8-json-compact-payload-v1'
    pinned_environment_canonical_json = $canonicalPinnedEnvironment
    pinned_environment = $pinnedEnvironment
    live_checks = [ordered]@{
        exact_target_hash_match = $true
        registry32_target_match = $true
        accepted_oracle_invariants_match = $true
        font_hash_match = $true
        hancom_pdf_binding_match = $true
        hancom_pdf_driver_files_match = $true
        source_lock_dual_shell_pass = $true
        current_hwp_processes = 0
        user_document_opened = $false
        com_object_created = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_invoked = $false
    }
    claims = [ordered]@{
        current_pc_local_p01_development_ready = $true
        clean_immutable_image_qualified = $false
        other_pc_or_version_supported = $false
        production_or_distribution_ready = $false
    }
}

$json = $manifest | ConvertTo-Json -Depth 32
[System.IO.File]::WriteAllText($outputFull, ($json + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    state = $manifest.state
    baseline_path = Get-RelativeProjectPath -Root $projectRootFull -Path $outputFull
    baseline_digest_sha256 = $baselineDigest
    current_hwp_processes = 0
}
