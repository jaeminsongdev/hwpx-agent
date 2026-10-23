# Fixed whole-eight preflight only. No native mode, process launch or COM activation.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedHarnessSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedLibrarySha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$inputDirectory='implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01'
$pins=[Collections.Generic.List[object]]::new()

function Read-P09XrefPinnedFile([string]$Path, [long]$Maximum, [string]$Expected) {
    # Bounded stream hashing, one MiB/s, <=20 opens/s. The observed hash is not a race-proof sandbox.
    $item=Get-Item -LiteralPath $Path -Force
    if ($item -isnot [IO.FileInfo] -or $item.Length -lt 1 -or $item.Length -gt $Maximum) {throw 'P09_XREF_FILE_BOUNDARY'}
    $ancestors=@($item);$parent=$item.Directory
    while ($null -ne $parent) {$ancestors+=,$parent;$parent=$parent.Parent}
    foreach ($ancestor in $ancestors) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P09_XREF_LINKED_PATH'}
    }
    Start-Sleep -Milliseconds 50
    $stream=[IO.File]::Open($item.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $hash=[Security.Cryptography.SHA256]::Create();$memory=[IO.MemoryStream]::new()
    $watch=[Diagnostics.Stopwatch]::StartNew();$buffer=[byte[]]::new(65536);$count=0L
    try {
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -ne 0) {
            $count+=$n;if ($count -gt $Maximum) {throw 'P09_XREF_FILE_SIZE_CHANGED'}
            [void]$hash.TransformBlock($buffer,0,$n,$buffer,0);$memory.Write($buffer,0,$n)
            $delay=[int][Math]::Ceiling(($count/1048576.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        [void]$hash.TransformFinalBlock([byte[]]::new(0),0,0)
        $sha=([BitConverter]::ToString($hash.Hash)).Replace('-','').ToLowerInvariant()
        if ($sha -cne $Expected -or $count -ne $item.Length) {throw 'P09_XREF_FILE_IDENTITY'}
        [void]$pins.Add([ordered]@{path=$item.FullName;bytes=$count;sha256=$sha})
        return ,$memory.ToArray()
    } finally {$stream.Dispose();$hash.Dispose();$memory.Dispose();$watch.Stop()}
}

function Get-P09XrefRegistryValue($Registry,[string]$Path) {
    $key=$Registry.OpenSubKey($Path,$false)
    if ($null -eq $key) {throw 'P09_XREF_REGISTRATION_MISSING'}
    try {return [string]$key.GetValue('')} finally {$key.Dispose()}
}

try {
    [void](Read-P09XrefPinnedFile $PSCommandPath 32768 $ExpectedHarnessSha256)
    $library=Join-Path $PSScriptRoot 'crossref-discovery-preflight-library.ps1'
    [void](Read-P09XrefPinnedFile $library 32768 $ExpectedLibrarySha256)
    . $library
    if ([Environment]::Is64BitProcess -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne
            [Threading.ApartmentState]::STA) {throw 'P09_XREF_X86_STA_REQUIRED'}
    $before=@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'")
    if ($before.Count -ne 0) {throw 'P09_XREF_PREEXISTING_HWP'}
    $packetBytes=Read-P09XrefPinnedFile (Join-Path $root ($inputDirectory+'/prepared-sdk-batch.v1.json')) 262144 `
        '1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1'
    $packet=[Text.UTF8Encoding]::new($false,$true).GetString($packetBytes) | ConvertFrom-Json
    $summary=Assert-P09XrefFixedPacket $packet
    [void](Read-P09XrefPinnedFile (Join-Path $root ($inputDirectory+'/source-input-manifest.v1.json')) 65536 `
        'fef538f8e072a72e8d0c0f42b0752a88ecdaf3fc582d4c67d07891bea34fcd29')
    [void](Read-P09XrefPinnedFile (Join-Path $root ($inputDirectory+'/source-with-bookmark.hwpx')) 4194304 `
        '64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184')
    # Existing owned-session source is pinned for future reuse, not imported/activated here.
    $ownedPath=Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1'
    # Expected identity is fixed by the tested harness source, never accepted from a packet.
    [void](Read-P09XrefPinnedFile $ownedPath 32768 'bd908d7d8f57513df7992e75f3e7faddaa81ce71d6dc0ad8c0b65963124a6338')
    $registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,[Microsoft.Win32.RegistryView]::Registry32)
    try {
        $clsid=Get-P09XrefRegistryValue $registry 'HWPFrame.HwpObject.2\CLSID'
        if ($clsid -cnotmatch '^\{[0-9A-Fa-f-]{36}\}$') {throw 'P09_XREF_CLSID'}
        $command=Get-P09XrefRegistryValue $registry ('CLSID\'+$clsid+'\LocalServer32')
        $match=[regex]::Match($command.Trim(),'^(?:"(?<path>[^"\r\n]+\.exe)"|(?<path>[^\r\n]+?\.exe))(?:\s|$)')
        if (-not $match.Success) {throw 'P09_XREF_SERVER_PATH'}
        $executable=[IO.Path]::GetFullPath($match.Groups['path'].Value)
        [void](Read-P09XrefPinnedFile $executable 4194304 '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce')
        if ((Get-Item -LiteralPath $executable).VersionInfo.FileVersion -cne '11.0.0.9136') {throw 'P09_XREF_BUILD'}
        $directory=[IO.Path]::GetDirectoryName($executable)
        [void](Read-P09XrefPinnedFile (Join-Path $directory 'HwpAutomation.dll') 2097152 `
            'edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151')
        $typeId=Get-P09XrefRegistryValue $registry ('CLSID\'+$clsid+'\TypeLib')
        if ($typeId -cnotmatch '^\{[0-9A-Fa-f-]{36}\}$') {throw 'P09_XREF_TYPELIB_ID'}
        $typePath=Get-P09XrefRegistryValue $registry ('TypeLib\'+$typeId+'\1.0\0\win32')
        if (-not [string]::Equals([IO.Path]::GetFullPath($typePath),(Join-Path $directory 'HwpObject.tlb'),[StringComparison]::OrdinalIgnoreCase)) {
            throw 'P09_XREF_TYPELIB_PATH'
        }
        [void](Read-P09XrefPinnedFile $typePath 2097152 'abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9')
    } finally {$registry.Dispose()}
    $security=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
    [void](Read-P09XrefPinnedFile $security 262144 '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6')
    $registry=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryView]::Registry32)
    $key=$null
    try {
        $key=$registry.OpenSubKey('Software\HNC\HwpAutomation\Modules',$false)
        if ($null -eq $key -or $key.GetValueKind('FilePathCheckerModuleExample').ToString() -cne 'String' -or
            [string]$key.GetValue('FilePathCheckerModuleExample') -cne $security) {throw 'P09_XREF_SECURITY_REGISTRATION'}
    } finally {if ($null -ne $key) {$key.Dispose()};$registry.Dispose()}
    # One fresh whole-batch boundary, not eight repeats of the same inputs.
    $firstPins=@($pins.ToArray())
    foreach ($pin in $firstPins) {[void](Read-P09XrefPinnedFile $pin.path $pin.bytes $pin.sha256)}
    if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {throw 'P09_XREF_HWP_SET_CHANGED'}
    [ordered]@{state='whole_eight_preflight_pass_no_com_not_native_ready';case_count=$summary.case_count;
        x86_sta=$true;before_and_after_hwp_count=0;fresh_inputs=$firstPins.Count;final_fresh_hashes=$firstPins.Count;
        source_pins=$firstPins;native_execution_authorized=$false;native_ready=$false;native_session_started=$false;
        native_attempt_created=$false;owned_session_runtime_qualified=$false;active_document_target_bound=$false;
        registry_or_system_setting_changed=$false;accepted_count_delta=0;p09_complete=$false} | ConvertTo-Json -Depth 8 -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_PREFLIGHT_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='preflight_rejected';error_code=$code;native_session_started=$false;
        native_execution_authorized=$false;native_ready=$false;native_attempt_created=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
