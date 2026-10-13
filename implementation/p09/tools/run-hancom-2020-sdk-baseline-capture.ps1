[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateRange(1,17)][int]$CaseIndex,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedBundleSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedLibrarySha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedHarnessSha256,
    [switch]$PreflightOnly,
    [switch]$ExecuteNative
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$exeSha='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$dllSha='edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151'
$securityName='FilePathCheckerModuleExample'
$securitySha='9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'

function Assert-P58File {
    param([string]$Path,[long]$Maximum=4194304,[string]$Sha='')
    $item=Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or $item.Length -lt 1 -or $item.Length -gt $Maximum -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P58_FILE_BOUNDARY'}
    $ancestor=$item.Directory
    while ($null -ne $ancestor) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P58_LINKED_ANCESTOR'}
        $ancestor=$ancestor.Parent
    }
    $digest=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Sha -ne '' -and $digest -cne $Sha) {throw 'P58_FILE_IDENTITY'}
    return [ordered]@{sha256=$digest;bytes=[long]$item.Length}
}

function Write-P58Trace {
    param([string]$Path,$Value)
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 14 -Compress))
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
}

if ([bool]$PreflightOnly -eq [bool]$ExecuteNative) {throw 'P58_EXACTLY_ONE_EXECUTION_MODE'}
[void](Assert-P58File $PSCommandPath 65536 $ExpectedHarnessSha256)
if ([Environment]::Is64BitProcess -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne
    [Threading.ApartmentState]::STA) {throw 'P58_X86_STA_REQUIRED'}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {throw 'P58_PREEXISTING_HWP'}
$bundlePath=Join-Path $root 'implementation\p09\evidence\private\p09-58-sdk-baseline-plans-20261003-r01\capture-manifest.json'
[void](Assert-P58File $bundlePath 262144 $ExpectedBundleSha256)
$bundle=[IO.File]::ReadAllText($bundlePath,[Text.UTF8Encoding]::new($false,$true)) | ConvertFrom-Json
if ($bundle.schema_version -cne 'hwpx-agent.sdk-baseline-capture-inputs/v1' -or @($bundle.cases).Count -ne 17 -or
    $bundle.p09_complete -ne $false -or $bundle.human_authored_direct_oracle -ne $false) {throw 'P58_BUNDLE_SCHEMA'}
for ($i=0;$i -lt 17;$i++) {
    $id=if ($i -lt 15) {'P09-35-C'+($i+1).ToString('00')} else {'P09-55-C'+($i-14).ToString('00')}
    $row=$bundle.cases[$i]
    if ($row.case_id -cne $id -or $row.capture_index -ne ($i+1) -or $row.source_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $row.source_file -cnotmatch '^fixtures/target-build/(p09-51-native-form-candidates-20261003-r01|p09-22-click-here-update-target-20261002-02)/output/[a-z0-9-]+\.hwpx$' -or
        $row.run_directory -cne ('implementation/p09/evidence/private/p09-58-sdk-baseline-20261003-r01-c'+($i+1).ToString('00')+'-attempt01')) {
        throw 'P58_BUNDLE_SCOPE'
    }
    $inputPath=Join-Path $root $row.source_file
    $inputFile=Assert-P58File $inputPath 4194304 $row.source_sha256
    if ($inputFile.bytes -ne $row.source_bytes) {throw 'P58_BUNDLE_INPUT_BYTES'}
}
$case=$bundle.cases[$CaseIndex-1];$source=Join-Path $root $case.source_file
$sourceSha=$case.source_sha256;$sourceFile=Assert-P58File $source 4194304 $sourceSha
$run=Join-Path $root $case.run_directory
if (Test-Path -LiteralPath $run) {throw 'P58_EXCLUSIVE_RUN_EXISTS'}
$library=Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1'
[void](Assert-P58File $library 65536 $ExpectedLibrarySha256)
. $library
# The existing regular source/bundle proves ROOT; also check the output parent and ancestors.
$ancestor=Get-Item -LiteralPath (Split-Path -Parent $run) -Force
while ($null -ne $ancestor) {
    if ($ancestor -isnot [IO.DirectoryInfo] -or ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P58_OUTPUT_PARENT_LINKED'}
    $ancestor=$ancestor.Parent
}
$registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,[Microsoft.Win32.RegistryView]::Registry32)
$keys=@()
try {
    $key=$registry.OpenSubKey('HWPFrame.HwpObject.2\CLSID',$false);if ($null -eq $key) {throw 'P58_PROGID_MISSING'};$keys+=,$key
    $clsid=[string]$key.GetValue('')
    if ($clsid -cnotmatch '^\{[0-9A-Fa-f-]{36}\}$') {throw 'P58_CLSID_BOUNDARY'}
    $key=$registry.OpenSubKey(('CLSID\'+$clsid+'\LocalServer32'),$false);if ($null -eq $key) {throw 'P58_SERVER_MISSING'};$keys+=,$key
    $match=[regex]::Match(([string]$key.GetValue('')).Trim(),'^(?:"(?<path>[^"\r\n]+\.exe)"|(?<path>[^\r\n]+?\.exe))(?:\s|$)')
    if (-not $match.Success) {throw 'P58_SERVER_PATH_BOUNDARY'}
    $executable=(Resolve-Path -LiteralPath $match.Groups['path'].Value).ProviderPath
    [void](Assert-P58File $executable 4194304 $exeSha)
    if ((Get-Item -LiteralPath $executable).VersionInfo.FileVersion -cne '11.0.0.9136') {throw 'P58_BUILD_MISMATCH'}
    [void](Assert-P58File (Join-Path (Split-Path -Parent $executable) 'HwpAutomation.dll') 2097152 $dllSha)
} finally {foreach ($key in $keys) {$key.Dispose()};$registry.Dispose()}
$security=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
$securityFile=Assert-P58File $security 262144 $securitySha
if ($securityFile.bytes -ne 217229) {throw 'P58_SECURITY_MODULE_BYTES'}
$registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryView]::Registry32)
$key=$null
try {
    $key=$registry.OpenSubKey('Software\HNC\HwpAutomation\Modules',$false)
    if ($null -eq $key -or $key.GetValueKind($securityName).ToString() -cne 'String' -or
        [string]$key.GetValue($securityName) -cne $security) {throw 'P58_SECURITY_REGISTRY_READ_ONLY_CHECK'}
} finally {if ($null -ne $key) {$key.Dispose()};$registry.Dispose()}
if ($PreflightOnly) {
    [ordered]@{state='preflight_pass_no_com_no_run_directory';case_id=$case.case_id;capture_index=$CaseIndex;
        source_sha256=$sourceSha;bundle_sha256=$ExpectedBundleSha256;harness_sha256=$ExpectedHarnessSha256;
        owned_library_sha256=$ExpectedLibrarySha256;x86_sta=$true;native_session_started=$false;
        native_run_directory_created=$false;registry_or_system_setting_changed=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
}

# P58_NATIVE_BOUNDARY: the actual preflight exits before all activation/output creation.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P58OwnedWindowProcess {
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
    public static uint ProcessId(int window) { uint pid; if (GetWindowThreadProcessId(new IntPtr(window), out pid)==0) throw new InvalidOperationException(); return pid; }
}
'@
[void](New-Item -ItemType Directory -Path $run -ErrorAction Stop)
$trace=[ordered]@{schema_version='hwpx-agent.p09-58-sdk-baseline-target-trace/v1';case_id=$case.case_id;capture_index=$CaseIndex;
    state='effect_unknown';started_at_utc=[datetime]::UtcNow.ToString('o');completed_at_utc=$null;
    target=[ordered]@{build='11.0.0.9136';architecture='x86';prog_id='HWPFrame.HwpObject.2';executable_sha256=$exeSha};
    source_sha256=$sourceSha;source_bytes=$sourceFile.bytes;bundle_sha256=$ExpectedBundleSha256;
    harness_sha256=$ExpectedHarnessSha256;owned_library_sha256=$ExpectedLibrarySha256;security_module_sha256=$securitySha;
    sessions=(New-Object Collections.ArrayList);artifacts=[ordered]@{};failed_phase=$null;error_code=$null;
    source_identity_preserved=$false;remaining_hwp_process_count=$null;managed_document_setter_invoked=$false;
    human_authored_direct_oracle=$false;computer_use_click_or_type_invoked=$false;raw_document_values_present=$false;
    registry_or_system_setting_changed=$false;external_network_invoked=$false;
    native_package_render_differential_or_product_qualified=$false;p09_complete=$false}
$owner=$null;$document=$null;$phase='first_session_create'
try {
    $owner=New-P58Owner 'save' $trace
    $phase='source_open';$document=Open-P58Document $owner $source $sourceSha
    $phase='first_save';$trace.artifacts.'saved.hwpx'=Save-P58Artifact $owner $document 'saved.hwpx' 'HWPX'
    $phase='first_pdf';$trace.artifacts.'saved.pdf'=Save-P58Artifact $owner $document 'saved.pdf' 'PDF'
    Release-P58Com $document;$document=$null;Close-P58Owner $owner
    $phase='first_owner_cleanup'
    if ($owner.trace.cleanup_error -ne $null -or $owner.trace.remaining_owned_process_count -ne 0 -or -not $owner.trace.quit_invoked) {throw 'P58_FIRST_OWNER_CLEANUP'}
    $owner=$null
    $phase='fresh_session_create';$owner=New-P58Owner 'reopen' $trace
    $phase='fresh_saved_open';$document=Open-P58Document $owner (Join-Path $run 'saved.hwpx') $trace.artifacts.'saved.hwpx'.sha256
    $phase='fresh_reopened_save';$trace.artifacts.'reopened.hwpx'=Save-P58Artifact $owner $document 'reopened.hwpx' 'HWPX'
    $phase='fresh_pdf';$trace.artifacts.'reopened.pdf'=Save-P58Artifact $owner $document 'reopened.pdf' 'PDF'
    $phase='source_identity_check';[void](Assert-P58File $source 4194304 $sourceSha)
    $trace.source_identity_preserved=$true
    $trace.state='sdk_baseline_lifecycle_completed_not_semantic_or_render_acceptance'
} catch {
    $trace.failed_phase=$phase
    $trace.error_code=if ($_.Exception.Message -cmatch '^P58_[A-Z_]+$') {$_.Exception.Message} else {'P58_NATIVE_EXCEPTION_NO_RAW_VALUES'}
} finally {
    Release-P58Com $document;Close-P58Owner $owner
    $trace.remaining_hwp_process_count=@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count
    # Original identity must also be checked after failed attempts/cleanup, never reported from intent.
    try {[void](Assert-P58File $source 4194304 $sourceSha);$trace.source_identity_preserved=$true}
    catch {$trace.source_identity_preserved=$false;$trace.state='effect_unknown';$trace.failed_phase='source_identity_check';$trace.error_code='P58_SOURCE_CHANGED_PRESERVE_EVIDENCE'}
    $trace.completed_at_utc=[datetime]::UtcNow.ToString('o')
    Write-P58Trace (Join-Path $run 'target-trace.json') $trace
}
$ok=$trace.state -ceq 'sdk_baseline_lifecycle_completed_not_semantic_or_render_acceptance' -and
    $trace.source_identity_preserved -and $trace.remaining_hwp_process_count -eq 0 -and $trace.sessions.Count -eq 2
foreach ($row in $trace.sessions) {if ($row.cleanup_error -ne $null -or $row.remaining_owned_process_count -ne 0 -or -not $row.quit_invoked) {$ok=$false}}
[ordered]@{state=$trace.state;remaining_hwp_process_count=$trace.remaining_hwp_process_count;
    native_package_render_differential_or_product_qualified=$false;p09_complete=$false} | ConvertTo-Json -Compress
if (-not $ok) {exit 2};exit 0
