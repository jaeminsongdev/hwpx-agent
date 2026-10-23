# Readonly pre-COM preparation only. No owner/session, action, document or output creation.
[CmdletBinding()]
param([switch]$InspectOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$phase='readonly_mode'

function Read-P09XrefPrefixPin([string]$Path,[long]$ExpectedBytes,[string]$ExpectedSha) {
    $item=Get-Item -LiteralPath $Path -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq $ExpectedBytes -and
        $item.Length -gt 0 -and $item.Length -le 4194304) 'PREFIX_FILE_SIZE'
    $ancestor=$item
    while ($null -ne $ancestor) {
        Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREFIX_LINK'
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    $stream=$null;$hash=$null
    try {
        $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $hash=[Security.Cryptography.SHA256]::Create();$buffer=[byte[]]::new(65536);$count=0L
        $watch=[Diagnostics.Stopwatch]::StartNew()
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -gt 0) {
            $count+=$n;Assert-P09XrefBinding ($count -le $ExpectedBytes) 'PREFIX_READ_LIMIT'
            [void]$hash.TransformBlock($buffer,0,$n,$buffer,0)
            $delay=[int][Math]::Ceiling(($count/1048576.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        [void]$hash.TransformFinalBlock([byte[]]::new(0),0,0)
        $sha=([BitConverter]::ToString($hash.Hash)).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($count -eq $ExpectedBytes -and $sha -ceq $ExpectedSha -and
            $stream.Length -eq $ExpectedBytes) 'PREFIX_FILE_SHA'
        return [ordered]@{bytes=$count;sha256=$sha}
    } finally {
        if ($null -ne $stream) {$stream.Dispose()}
        if ($null -ne $hash) {$hash.Dispose()}
    }
}

function Get-P09XrefPrefixHwpInventory {
    return @(@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'") | ForEach-Object {
        [string]$_.ProcessId+':'+([datetime]$_.CreationDate).ToUniversalTime().ToString('o')
    } | Sort-Object)
}

try {
    if (-not $InspectOnly) {throw 'P09_XREF_BIND_PREFIX_INSPECT_ONLY_REQUIRED'}
    foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
        'crossref-save-reopen','crossref-stage-probe','crossref-native-case-ports')) {
        . (Join-Path $PSScriptRoot ($name+'.ps1'))
    }
    Assert-P09XrefBinding (-not [Environment]::Is64BitProcess -and
        [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'PREFIX_X86_STA'
    Assert-P09XrefOriginalIoFunctions
    [void](Read-P09XrefFrozenNativeHarness)
    $phase='initial_inventory';$before=@(Get-P09XrefPrefixHwpInventory)
    for ($i=1;$i -le 8;$i++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $i 'opened')))) 'PREFIX_NATIVE_ATTEMPT_ALREADY_EXISTS'
    }
    $phase='installed_binary_identity'
    $executable='C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe'
    $directory=Split-Path -Parent $executable
    $security=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
    $pins=[ordered]@{}
    $pins.executable=Read-P09XrefPrefixPin $executable 2321432 '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
    $pins.automation_dll=Read-P09XrefPrefixPin (Join-Path $directory 'HwpAutomation.dll') 785432 'edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151'
    $pins.typelib=Read-P09XrefPrefixPin (Join-Path $directory 'HwpObject.tlb') 473120 'abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9'
    $pins.security_module=Read-P09XrefPrefixPin $security 217229 '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'
    Assert-P09XrefBinding ((Get-Item -LiteralPath $executable).VersionInfo.FileVersion -ceq '11.0.0.9136') 'PREFIX_EXE_VERSION'
    $phase='readonly_registry'
    $classes=$null;$user=$null;$keys=[Collections.Generic.List[object]]::new()
    try {
        $classes=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,[Microsoft.Win32.RegistryView]::Registry32)
        $key=$classes.OpenSubKey('HWPFrame.HwpObject.2\CLSID',$false)
        Assert-P09XrefBinding ($null -ne $key) 'PREFIX_PROGID_KEY';[void]$keys.Add($key)
        $clsid=[string]$key.GetValue('')
        Assert-P09XrefBinding ($clsid -cmatch '^\{[0-9A-Fa-f-]{36}\}$') 'PREFIX_CLSID_SHAPE'
        $key=$classes.OpenSubKey(('CLSID\'+$clsid+'\LocalServer32'),$false)
        Assert-P09XrefBinding ($null -ne $key) 'PREFIX_SERVER_KEY';[void]$keys.Add($key)
        $registered=[string]$key.GetValue('')
        Assert-P09XrefBinding ($registered.Length -le 1024) 'PREFIX_SERVER_VALUE_BOUND'
        $match=[regex]::Match($registered.Trim(),'^(?:"(?<path>[^"\r\n]+\.exe)"|(?<path>[^\r\n]+?\.exe))(?:\s|$)')
        Assert-P09XrefBinding ($match.Success -and [string]::Equals($match.Groups['path'].Value,$executable,[StringComparison]::OrdinalIgnoreCase)) 'PREFIX_SERVER_IDENTITY'
        $user=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryView]::Registry32)
        $key=$user.OpenSubKey('Software\HNC\HwpAutomation\Modules',$false)
        Assert-P09XrefBinding ($null -ne $key) 'PREFIX_MODULE_KEY';[void]$keys.Add($key)
        Assert-P09XrefBinding ([string]::Equals([string]$key.GetValue('FilePathCheckerModuleExample'),$security,[StringComparison]::OrdinalIgnoreCase)) 'PREFIX_MODULE_REGISTRATION'
    } finally {
        foreach ($key in $keys) {$key.Dispose()}
        if ($null -ne $user) {$user.Dispose()}
        if ($null -ne $classes) {$classes.Dispose()}
    }
    $phase='frozen_window_type'
    Assert-P09XrefBinding ($null -eq ('P58OwnedWindowProcess' -as [type])) 'PREFIX_FRESH_TYPE_REQUIRED'
    Initialize-P09XrefFrozenWindowBridge
    $type='P58OwnedWindowProcess' -as [type]
    $method=$type.GetMethod('ProcessId',[Reflection.BindingFlags]'Public,Static')
    Assert-P09XrefBinding ($null -ne $method -and $method.ReturnType -eq [uint32] -and
        $method.GetParameters().Count -eq 1 -and $method.GetParameters()[0].ParameterType -eq [int32]) 'PREFIX_WINDOW_SIGNATURE'
    $native=$type.GetMethod('GetWindowThreadProcessId',[Reflection.BindingFlags]'NonPublic,Static')
    $attributes=@($native.GetCustomAttributes([Runtime.InteropServices.DllImportAttribute],$false))
    Assert-P09XrefBinding ($attributes.Count -eq 1 -and $attributes[0].Value -ceq 'user32.dll') 'PREFIX_WINDOW_IMPORT'
    $phase='closing_inventory';$after=@(Get-P09XrefPrefixHwpInventory)
    Assert-P09XrefBinding (($before -join ',') -ceq ($after -join ',')) 'PREFIX_HWP_INVENTORY_CHANGED'
    for ($i=1;$i -le 8;$i++) {
        Assert-P09XrefBinding (-not (Test-Path -LiteralPath (Split-Path -Parent (Get-P09XrefCaseArtifactPath $i 'opened')))) 'PREFIX_NATIVE_ATTEMPT_CREATED'
    }
    [ordered]@{schema_version='hwpx-agent.private.crossref-pre-com-prefix/v1';state='pre_com_prefix_loaded_not_native_ready';
        x86_sta=$true;installed_pins=$pins;registry_readonly_bindings_match=$true;window_type_loaded=$true;
        window_native_method_invoked=$false;hwp_before_count=$before.Count;hwp_after_count=$after.Count;
        hwp_inventory_preserved=$true;native_directories_created=$false;actual_Hangul_or_COM=$false;
        native_execution_authorized=$false;complete_native_guard_integration_qualified=$false;p09_complete=$false} | ConvertTo-Json -Depth 6 -Compress
} catch {
    [ordered]@{schema_version='hwpx-agent.private.crossref-pre-com-prefix/v1';state='pre_com_prefix_failed';phase=$phase;
        error_type=$_.Exception.GetType().Name;source_line=$_.InvocationInfo.ScriptLineNumber;
        error_code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_PREFIX_FAILED_NO_RAW_VALUES'};
        actual_Hangul_or_COM=$false;native_execution_authorized=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
