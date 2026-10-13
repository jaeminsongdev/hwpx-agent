[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('P09-55-C01','P09-55-C02')][string]$CaseId,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedLifecycleLibrarySha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedHarnessSha256,
    [switch]$PreflightOnly,
    [switch]$ExecuteNative
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$exeSha='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$dllSha='edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151'
$p54Sha='6ccda3e4c42979e99be67f1033c4ff10866a97a822effee5c2ea1746e70cca89'
$p50Sha='c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183'
$securityName='FilePathCheckerModuleExample'
$securitySha='9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'

function Assert-P55File {
    param([string]$Path,[long]$Maximum=4194304,[string]$Sha='')
    $item=Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or $item.Length -lt 1 -or $item.Length -gt $Maximum -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P55_FILE_BOUNDARY'}
    $ancestor=$item.Directory
    while ($null -ne $ancestor) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P55_LINKED_ANCESTOR'}
        $ancestor=$ancestor.Parent
    }
    $digest=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Sha -ne '' -and $digest -cne $Sha) {throw 'P55_FILE_IDENTITY'}
    return [ordered]@{sha256=$digest;bytes=[long]$item.Length}
}

function Write-P55Trace {
    param([string]$Path,$Value)
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 14 -Compress))
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
}

# This preflight is the ACTUAL prefix of the native runner; it cannot create COM/run directories.
if ([bool]$PreflightOnly -eq [bool]$ExecuteNative) {throw 'P55_EXACTLY_ONE_EXECUTION_MODE'}
[void](Assert-P55File $PSCommandPath 65536 $ExpectedHarnessSha256)
if ([Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {throw 'P55_X86_STA_REQUIRED'}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {throw 'P55_PREEXISTING_HWP'}
$index=$CaseId.Substring($CaseId.Length-2)
$sourceName=if ($index -ceq '01') {'empty.hwpx'} else {'filled.hwpx'}
$sourceSha=if ($index -ceq '01') {'60a646f488941bad203d1c1d8bab43a36f2ae5c4712396eeeb3c1acb81d50747'}
    else {'ab6d2d2d8f9d4375c30b16b80e963a71c31c3b3ed6c7466f5bc3da872b00ebaf'}
$fixedPlanSha=if ($index -ceq '01') {'6d24d0bd05b93863ca109018bd567011ae8001e18027de0e38eb2515f188a0f7'}
    else {'0c8cb9404b0eaac58f9ff83b02a5ce43f0b4c0a2c41f58470850d6cccd5d37c2'}
if ($ExpectedPlanSha256 -cne $fixedPlanSha) {throw 'P55_PLAN_SCOPE'}
$source=Join-Path $root ('implementation\p09\evidence\private\p09-22-click-here-discovery-20261002-01\'+$sourceName)
$sourceFile=Assert-P55File $source 4194304 $sourceSha
$plans=Join-Path $root 'implementation\p09\evidence\private\p09-55-click-format-plans-20261003-r01'
$planPath=Join-Path $plans ('p09-55-c'+$index+'-plan.json')
[void](Assert-P55File $planPath 262144 $ExpectedPlanSha256)
$p54=Join-Path $PSScriptRoot 'click-here-format-preservation.ps1'
$p50=Join-Path $PSScriptRoot 'native-form-control-binding.ps1'
$library=Join-Path $PSScriptRoot 'click-here-format-lifecycle.ps1'
[void](Assert-P55File $p54 262144 $p54Sha)
[void](Assert-P55File $p50 262144 $p50Sha)
[void](Assert-P55File $library 262144 $ExpectedLifecycleLibrarySha256)
. $p50
. $p54
. $library
$plan=[IO.File]::ReadAllText($planPath,[Text.UTF8Encoding]::new($false,$true)) | ConvertFrom-Json
Assert-P09ClickFormatPlan $plan $sourceSha
if ($plan.case_id -cne ('P09-54-C'+$index) -or $plan.source_package_bytes -ne $sourceFile.bytes) {throw 'P55_CASE_PLAN_ALIAS'}
$private=Join-Path $root 'implementation\p09\evidence\private'
$run=Join-Path $private ('p09-55-click-format-20261003-r01-c'+$index+'-attempt01')
if (Test-Path -LiteralPath $run) {throw 'P55_EXCLUSIVE_RUN_EXISTS'}
$registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,[Microsoft.Win32.RegistryView]::Registry32)
$keys=@()
try {
    $key=$registry.OpenSubKey('HWPFrame.HwpObject.2\CLSID',$false); if ($null -eq $key) {throw 'P55_PROGID_MISSING'}; $keys+=,$key
    $clsid=[string]$key.GetValue('')
    if ($clsid -cnotmatch '^\{[0-9A-Fa-f-]{36}\}$') {throw 'P55_CLSID_BOUNDARY'}
    $key=$registry.OpenSubKey(('CLSID\'+$clsid+'\LocalServer32'),$false); if ($null -eq $key) {throw 'P55_SERVER_MISSING'}; $keys+=,$key
    $match=[regex]::Match(([string]$key.GetValue('')).Trim(),'^(?:"(?<path>[^"\r\n]+\.exe)"|(?<path>[^\r\n]+?\.exe))(?:\s|$)')
    if (-not $match.Success) {throw 'P55_SERVER_PATH_BOUNDARY'}
    $executable=(Resolve-Path -LiteralPath $match.Groups['path'].Value).ProviderPath
    [void](Assert-P55File $executable 4194304 $exeSha)
    if ((Get-Item -LiteralPath $executable).VersionInfo.FileVersion -cne '11.0.0.9136') {throw 'P55_BUILD_MISMATCH'}
    [void](Assert-P55File (Join-Path (Split-Path -Parent $executable) 'HwpAutomation.dll') 2097152 $dllSha)
} finally {foreach ($key in $keys) {$key.Dispose()};$registry.Dispose()}
$security=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
$securityFile=Assert-P55File $security 262144 $securitySha
if ($securityFile.bytes -ne 217229) {throw 'P55_SECURITY_MODULE_BYTES'}
$registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryView]::Registry32)
$key=$null
try {
    $key=$registry.OpenSubKey('Software\HNC\HwpAutomation\Modules',$false)
    if ($null -eq $key -or $key.GetValueKind($securityName).ToString() -cne 'String' -or
        [string]$key.GetValue($securityName) -cne $security) {throw 'P55_SECURITY_REGISTRY_READ_ONLY_CHECK'}
} finally {if ($null -ne $key) {$key.Dispose()};$registry.Dispose()}
if ($PreflightOnly) {
    [ordered]@{state='preflight_pass_no_com_no_run_directory';case_id=$CaseId;source_sha256=$sourceSha;
        plan_sha256=$ExpectedPlanSha256;harness_sha256=$ExpectedHarnessSha256;
        lifecycle_library_sha256=$ExpectedLifecycleLibrarySha256;x86_sta=$true;no_com_server_activation=$true;
        native_run_directory_created=$false;registry_or_system_setting_changed=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
}

# P55_NATIVE_BOUNDARY: source verification NEVER enters this explicit ExecuteNative branch.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P55OwnedWindowProcess {
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
    public static uint ProcessId(int window) { uint pid; if (GetWindowThreadProcessId(new IntPtr(window), out pid)==0) throw new InvalidOperationException(); return pid; }
}
'@

function Test-P55Owner {
    param($Owner)
    if (-not $Owner.verified -or $null -eq $Owner.identity) {return $false}
    $rows=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$Owner.identity.process_id))
    if ($rows.Count -ne 1) {return $false}
    $row=$rows[0]
    return ([int]$row.SessionId -eq $Owner.identity.session_id -and
        ([datetime]$row.CreationDate).ToUniversalTime().ToString('o') -ceq $Owner.identity.created_at_utc -and
        [string]$row.ExecutablePath -ceq $executable -and
        ([P55OwnedWindowProcess]::ProcessId([int]$Owner.window.WindowHandle)) -eq $Owner.identity.process_id)
}

function Close-P55Owner {
    param($Owner)
    if ($null -eq $Owner) {return}
    try {
        if (Test-P55Owner $Owner) {
            # False is an explicit no-dirty-prompt request; actual cleanup must still be observed.
            $Owner.documents.Close($false)
            $Owner.trace.close_without_dirty_prompt_returned=$true
            if (-not (Test-P55Owner $Owner)) {throw 'P55_OWNER_CHANGED_BEFORE_QUIT'}
            $Owner.hwp.Quit();$Owner.trace.quit_invoked=$true
        } else {$Owner.trace.cleanup_error='P55_OWNER_UNVERIFIED_NO_BLANKET_QUIT'}
    } catch {$Owner.trace.cleanup_error='P55_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL'}
    finally {
        Release-P09FormCom $Owner.documents; Release-P09FormCom $Owner.window
        Release-P09FormCom $Owner.windows; Release-P09FormCom $Owner.hwp
        $Owner.documents=$null;$Owner.window=$null;$Owner.windows=$null;$Owner.hwp=$null
        [GC]::Collect();[GC]::WaitForPendingFinalizers();[GC]::Collect();[GC]::WaitForPendingFinalizers()
    }
    $watch=[Diagnostics.Stopwatch]::StartNew()
    do {
        $remaining=if ($null -ne $Owner.identity) {@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$Owner.identity.process_id)).Count} else {-1}
        if ($remaining -eq 0 -or $watch.ElapsedMilliseconds -ge 10000) {break}
        Start-Sleep -Milliseconds 100
    } while ($true)
    $watch.Stop();$Owner.trace.remaining_owned_process_count=$remaining
}

function New-P55Owner {
    param([string]$Label,$Trace)
    if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {throw 'P55_NEW_SESSION_REQUIRES_ZERO_HWP'}
    $started=[datetime]::UtcNow
    $row=[ordered]@{label=$Label;version=$null;register_module_return=$null;process=$null;
        close_without_dirty_prompt_returned=$false;quit_invoked=$false;remaining_owned_process_count=$null;cleanup_error=$null}
    [void]$Trace.sessions.Add($row)
    $owner=[ordered]@{hwp=$null;windows=$null;window=$null;documents=$null;verified=$false;identity=$null;trace=$row}
    try {
        $owner.hwp=New-Object -ComObject 'HWPFrame.HwpObject.2'
        $owner.windows=$owner.hwp.XHwpWindows;$owner.window=$owner.windows.Item(0)
        $handle=$owner.window.WindowHandle
        if ($handle -isnot [int] -or $handle -eq 0) {throw 'P55_NATIVE_WINDOW_HANDLE_TYPE'}
        $processId=[P55OwnedWindowProcess]::ProcessId($handle)
        $processes=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$processId))
        if ($processes.Count -ne 1) {throw 'P55_OWNED_WINDOW_PROCESS_MISSING'}
        $process=$processes[0]
        if ([string]$process.Name -cne 'Hwp.exe' -or [string]$process.ExecutablePath -cne $executable -or
            [int]$process.SessionId -ne [Diagnostics.Process]::GetCurrentProcess().SessionId -or
            $null -eq $process.CreationDate -or ([datetime]$process.CreationDate).ToUniversalTime() -lt $started.AddSeconds(-2)) {
            throw 'P55_WINDOW_PROCESS_OWNERSHIP_REJECTED'
        }
        [void](Assert-P55File $executable 4194304 $exeSha)
        $owner.identity=[ordered]@{process_id=[int]$processId;session_id=[int]$process.SessionId;
            created_at_utc=([datetime]$process.CreationDate).ToUniversalTime().ToString('o');
            executable_sha256=$exeSha;window_handle_binds_exact_process=$true}
        $owner.verified=$true;$row.process=$owner.identity
        $owner.documents=$owner.hwp.XHwpDocuments
        $version=([string]$owner.hwp.Version).Replace(',','.').Replace(' ','')
        if ($version -cne '11.0.0.9136') {throw 'P55_NATIVE_VERSION'}
        $row.version=$version;$row.register_module_return=[bool]$owner.hwp.RegisterModule('FilePathCheckDLL',$securityName)
        $owner.window.Visible=$true
        return $owner
    } catch {Close-P55Owner $owner;throw}
}

function Open-P55Document {
    param($Owner,[string]$Path,[string]$Sha)
    if (-not (Test-P55Owner $Owner)) {throw 'P55_OPEN_OWNER_MISMATCH'}
    [void](Assert-P55File $Path 4194304 $Sha)
    $before=[int]$Owner.documents.Count
    if ($Owner.hwp.Open($Path,'HWPX','lock:false;setcurdir:false') -ne $true) {throw 'P55_OPEN_FAILED'}
    $after=[int]$Owner.documents.Count
    if ($after -lt 1 -or $after -lt $before -or $after -gt ($before+1)) {throw 'P55_OPEN_DOCUMENT_INVENTORY'}
    $doc=$Owner.documents.Item($after-1)
    try {
        if (-not [string]::Equals([string]$doc.FullName,$Path,[StringComparison]::OrdinalIgnoreCase)) {throw 'P55_OPEN_DOCUMENT_PATH'}
        [void]$doc.SetActive_XHwpDocument()
        return $doc
    } catch {Release-P09FormCom $doc;throw}
}

function Save-P55Artifact {
    param($Doc,[string]$Name,[string]$Format)
    $path=Join-Path $run $Name
    if (Test-Path -LiteralPath $path) {throw 'P55_EXCLUSIVE_OUTPUT_EXISTS'}
    if ($Doc.SaveAs($path,$Format,'') -ne $true) {throw 'P55_NATIVE_SAVE_FAILED'}
    $max=if ($Format -ceq 'PDF') {33554432} else {4194304}
    $item=Assert-P55File $path $max
    if ($Format -ceq 'PDF') {
        $stream=[IO.File]::OpenRead($path);$head=[byte[]]::new(5)
        try {if ($stream.Read($head,0,5) -ne 5 -or [Text.Encoding]::ASCII.GetString($head) -cne '%PDF-') {throw 'P55_PDF_SIGNATURE'}}
        finally {$stream.Dispose()}
    }
    return $item
}

# Exact existing private parent was checked through both regular original/plan paths.
[void](New-Item -ItemType Directory -Path $run -ErrorAction Stop)
$trace=[ordered]@{schema_version='hwpx-agent.p09-55-click-format-owned-target-trace/v1';case_id=$CaseId;
    worker_plan_case_id=$plan.case_id;state='effect_unknown';started_at_utc=[datetime]::UtcNow.ToString('o');
    target=[ordered]@{build='11.0.0.9136';architecture='x86';prog_id='HWPFrame.HwpObject.2';executable_sha256=$exeSha};
    source_sha256=$sourceSha;plan_sha256=$ExpectedPlanSha256;harness_sha256=$ExpectedHarnessSha256;
    lifecycle_library_sha256=$ExpectedLifecycleLibrarySha256;p54_worker_sha256=$p54Sha;p50_copy_library_sha256=$p50Sha;
    security_module_sha256=$securitySha;sessions=(New-Object Collections.ArrayList);artifacts=[ordered]@{};
    checks=[ordered]@{};failed_phase=$null;error_code=$null;binding_failure=$null;remaining_hwp_process_count=$null;
    completed_at_utc=$null;raw_document_values_present=$false;computer_use_click_or_type_invoked=$false;
    registry_or_system_setting_changed=$false;external_network_invoked=$false;
    saved_package_render_differential_or_product_qualified=$false;p09_complete=$false}
$owner=$null;$document=$null;$baseline=$null;$phase='first_session_create'
try {
    $owner=New-P55Owner 'save' $trace
    $phase='first_source_open';$document=Open-P55Document $owner $source $sourceSha
    $phase='first_complete_original_style_capture';$baseline=Get-P55SourceCharacterBaseline $owner.hwp $plan
    $phase='native_text_and_complete_style_application'
    $trace.checks.first_application=Invoke-P09ClickFormatPreservation $owner.hwp $plan $sourceSha
    $trace.checks.after_application=Confirm-P55ResultCharacterBaseline $owner.hwp $plan $baseline
    $phase='first_save';$trace.artifacts.'saved.hwpx'=Save-P55Artifact $document 'saved.hwpx' 'HWPX'
    $phase='after_first_save_check';$trace.checks.after_first_save=Confirm-P55ResultCharacterBaseline $owner.hwp $plan $baseline
    $phase='first_pdf';$trace.artifacts.'saved.pdf'=Save-P55Artifact $document 'saved.pdf' 'PDF'
    Release-P09FormCom $baseline.parameters;$baseline=$null;Release-P09FormCom $document;$document=$null
    Close-P55Owner $owner
    if ($owner.trace.cleanup_error -ne $null -or $owner.trace.remaining_owned_process_count -ne 0 -or -not $owner.trace.quit_invoked) {throw 'P55_FIRST_OWNER_CLEANUP'}
    $owner=$null
    $phase='fresh_session_create';$owner=New-P55Owner 'reopen' $trace
    $phase='fresh_original_source_open';$document=Open-P55Document $owner $source $sourceSha
    $phase='fresh_complete_original_style_capture';$baseline=Get-P55SourceCharacterBaseline $owner.hwp $plan
    if ($document.Close($false) -ne $true) {throw 'P55_FRESH_SOURCE_CLOSE'}
    Release-P09FormCom $document;$document=$null
    $phase='fresh_saved_open';$document=Open-P55Document $owner (Join-Path $run 'saved.hwpx') $trace.artifacts.'saved.hwpx'.sha256
    $phase='fresh_read_only_entire_style_check';$trace.checks.fresh_reopen=Confirm-P55ResultCharacterBaseline $owner.hwp $plan $baseline
    $phase='fresh_reopened_save';$trace.artifacts.'reopened.hwpx'=Save-P55Artifact $document 'reopened.hwpx' 'HWPX'
    $phase='after_reopened_save_check';$trace.checks.after_reopened_save=Confirm-P55ResultCharacterBaseline $owner.hwp $plan $baseline
    $phase='fresh_pdf';$trace.artifacts.'reopened.pdf'=Save-P55Artifact $document 'reopened.pdf' 'PDF'
    [void](Assert-P55File $source 4194304 $sourceSha)
    $trace.state='owned_lifecycle_checks_completed_not_package_or_render_acceptance'
} catch {
    $trace.failed_phase=$phase
    $trace.error_code=if ($_.Exception.Message -cmatch '^(P55|P09_CLICK_FORMAT)_[A-Z_]+$') {$_.Exception.Message} else {'P55_NATIVE_EXCEPTION_NO_RAW_VALUES'}
    if ($_.Exception.Data.Contains('rollback_state')) {
        $trace.binding_failure=[ordered]@{failed_phase=$_.Exception.Data['failed_phase'];error_code=$_.Exception.Data['error_code'];
            rollback_state=$_.Exception.Data['rollback_state'];raw_document_values_present=$false}
    }
} finally {
    if ($null -ne $baseline) {Release-P09FormCom $baseline.parameters}
    Release-P09FormCom $document;Close-P55Owner $owner
    $trace.remaining_hwp_process_count=@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count
    $trace.completed_at_utc=[datetime]::UtcNow.ToString('o')
    Write-P55Trace (Join-Path $run 'target-trace.json') $trace
}
$ok=$trace.state -ceq 'owned_lifecycle_checks_completed_not_package_or_render_acceptance' -and
    $trace.remaining_hwp_process_count -eq 0 -and $trace.sessions.Count -eq 2
foreach ($row in $trace.sessions) {if ($row.cleanup_error -ne $null -or $row.remaining_owned_process_count -ne 0 -or -not $row.quit_invoked) {$ok=$false}}
[ordered]@{state=$trace.state;remaining_hwp_process_count=$trace.remaining_hwp_process_count;
    raw_document_values_present=$false;p09_complete=$false} | ConvertTo-Json -Compress
if (-not $ok) {exit 2};exit 0
