# P50 관측기를 보존한 별도 필드 선택/글자서식 선언 조사. 한글 실행/문서 열기 없음.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$targetSha = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$dllSha = 'edbc7140f1f09025a34c5ffc2a07c47f90b6a1cdcb2a452b2969b53cd47e1151'
$beforePids = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" | ForEach-Object { [int]$_.ProcessId } | Sort-Object)
$registry = $null
$keys = [System.Collections.Generic.List[Microsoft.Win32.RegistryKey]]::new()
try {
    $registry = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot, [Microsoft.Win32.RegistryView]::Registry32)
    $key = $registry.OpenSubKey('HWPFrame.HwpObject.2\CLSID', $false)
    if ($null -eq $key) { throw 'FORM_TYPELIB_PROGID_MISSING' }; $keys.Add($key)
    $clsid = [string]$key.GetValue('')
    if ($clsid -notmatch '^\{[0-9A-Fa-f-]{36}\}$') { throw 'FORM_TYPELIB_CLSID_INVALID' }
    $key = $registry.OpenSubKey("CLSID\$clsid\LocalServer32", $false)
    if ($null -eq $key) { throw 'FORM_TYPELIB_SERVER_MISSING' }; $keys.Add($key)
    $command = [string]$key.GetValue('')
    $match = [regex]::Match($command.Trim(), '^(?:"(?<path>[^"\r\n]+\.exe)"|(?<path>[^\r\n]+?\.exe))(?:\s|$)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $match.Success) { throw 'FORM_TYPELIB_SERVER_PATH_INVALID' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value -ErrorAction Stop).ProviderPath
    $item = Get-Item -LiteralPath $path
    if ($item.Name -ine 'Hwp.exe' -or $item.Length -gt 4MB -or $item.VersionInfo.FileVersion -ne '11.0.0.9136' -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $targetSha) { throw 'FORM_TYPELIB_TARGET_IDENTITY_CHANGED' }
    $dllPath = Join-Path $item.Directory.FullName 'HwpAutomation.dll'
    if (-not (Test-Path -LiteralPath $dllPath -PathType Leaf)) { throw 'FORM_TYPELIB_DLL_MISSING' }
    if ((Get-Item -LiteralPath $dllPath).Length -gt 2MB -or
        (Get-FileHash -LiteralPath $dllPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $dllSha) { throw 'FORM_TYPELIB_DLL_IDENTITY_CHANGED' }
    $key = $registry.OpenSubKey("CLSID\$clsid\TypeLib", $false)
    if ($null -eq $key) { throw 'FORM_TYPELIB_REGISTRATION_MISSING' }; $keys.Add($key)
    $libraryId = [string]$key.GetValue('')
    if ($libraryId -notmatch '^\{[0-9A-Fa-f-]{36}\}$') { throw 'FORM_TYPELIB_LIBRARY_ID_INVALID' }
    $key = $registry.OpenSubKey("TypeLib\$libraryId\1.0\0\win32", $false)
    if ($null -eq $key) { throw 'FORM_TYPELIB_REGISTERED_FILE_MISSING' }; $keys.Add($key)
    $typePath = (Resolve-Path -LiteralPath ([string]$key.GetValue('')) -ErrorAction Stop).ProviderPath
    $typeItem = Get-Item -LiteralPath $typePath
    if ($typeItem.Name -ine 'HwpObject.tlb' -or $typeItem.Length -gt 2MB -or
        -not [string]::Equals($typeItem.Directory.FullName,$item.Directory.FullName,[StringComparison]::OrdinalIgnoreCase)) { throw 'FORM_TYPELIB_REGISTERED_FILE_BOUNDARY' }
    # 현재 설치 파일의 새로운 관측 identity다. 기존 P00 고정 해시로 주장하지 않는다.
    $typeSha = (Get-FileHash -LiteralPath $typePath -Algorithm SHA256).Hash.ToLowerInvariant()

    # REGKIND_NONE: 타입 라이브러리를 등록하지 않으며 COM 서버를 활성화하지 않는다.
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
public static class P09FormTypeLibraryReader {
    [DllImport("oleaut32.dll", CharSet=CharSet.Unicode, PreserveSig=true)]
    private static extern int LoadTypeLibEx(string file, int regKind, out ITypeLib typeLib);
    public static object Read(string file, string expectedLibraryId) {
        ITypeLib library = null;
        int hr = LoadTypeLibEx(file, 2, out library);
        if (hr < 0) Marshal.ThrowExceptionForHR(hr);
        if (library == null) throw new InvalidOperationException("FORM_TYPELIB_NULL");
        try {
            TYPELIBATTR libraryAttr; IntPtr libraryAttrPtr = IntPtr.Zero;
            try {
                library.GetLibAttr(out libraryAttrPtr);
                libraryAttr = Marshal.PtrToStructure<TYPELIBATTR>(libraryAttrPtr);
            } finally { if (libraryAttrPtr != IntPtr.Zero) library.ReleaseTLibAttr(libraryAttrPtr); }
            if (libraryAttr.guid != new Guid(expectedLibraryId) || libraryAttr.wMajorVerNum != 1 || libraryAttr.wMinorVerNum != 0)
                throw new InvalidOperationException("FORM_TYPELIB_REGISTERED_IDENTITY_MISMATCH");
            int count = library.GetTypeInfoCount();
            if (count < 1 || count > 512) throw new InvalidOperationException("FORM_TYPELIB_TYPE_LIMIT");
            var wantedTypes = new HashSet<string>(StringComparer.Ordinal) {
                "IHwpObject", "IXHwpDocuments", "IXHwpDocument", "IXHwpWindows", "IXHwpWindow", "IXHwpFormEdits", "IXHwpFormEdit",
                "IXHwpFormRadioButtons", "IXHwpFormRadioButton", "HwpFormRadioButton",
                "IDHwpCtrlCode", "IDHwpParameterSet", "HShapeObject", "HFormGeneral", "HFormCommonAttr",
                "HFormEditAttr", "HFormButtonAttr", "HFormCharshapeattr", "HCharShape"
            };
            var wantedMembers = new HashSet<string>(StringComparer.Ordinal) {
                "Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",
                "XHwpFormEdits", "XHwpFormRadioButtons", "Name", "name", "ForeColor", "BackColor", "GroupName", "TabStop", "TabOrder",
                "Width", "Height", "Heigh", "Left", "Top", "CharShapeID", "FollowContext", "AutoSize", "WordWrap", "Text", "ReadOnly",
                "HeadCtrl", "LastCtrl", "CurSelectedCtrl", "ParentCtrl", "GetPos", "GetPosBySet", "FindCtrl", "RGBColor", "CharShape", "MoveToField", "GetFieldList", "GetFieldText", "PutFieldText", "SetPosBySet", "CurFieldState", "SelectionMode", "GetCurFieldName", "Close", "Clear", "SaveAs", "Quit", "Open", "Version", "EditMode", "SetActive_XHwpDocument", "XHwpWindows", "Visible"
            };
            string libraryName, documentation, helpFile; int context;
            library.GetDocumentation(-1, out libraryName, out documentation, out context, out helpFile);
            if (libraryName == null || libraryName.Length > 128) throw new InvalidOperationException("FORM_TYPELIB_NAME_LIMIT");
            var types = new List<object>();
            var allTypeNames = new List<string>();
            for (int i = 0; i < count; i++) {
                string typeName;
                library.GetDocumentation(i, out typeName, out documentation, out context, out helpFile);
                if (typeName == null || typeName.Length > 128) throw new InvalidOperationException("FORM_TYPELIB_NAME_LIMIT");
                allTypeNames.Add(typeName);
                if (!wantedTypes.Contains(typeName)) continue;
                ITypeInfo info = null; IntPtr attrPtr = IntPtr.Zero;
                library.GetTypeInfo(i, out info);
                try {
                    info.GetTypeAttr(out attrPtr);
                    var attr = Marshal.PtrToStructure<TYPEATTR>(attrPtr);
                    if (attr.cFuncs < 0 || attr.cFuncs > 512) throw new InvalidOperationException("FORM_TYPELIB_FUNCTION_LIMIT");
                    var members = new List<object>();
                    var declaredNames = new List<string>();
                    for (int j = 0; j < attr.cFuncs; j++) {
                        IntPtr descPtr = IntPtr.Zero;
                        try {
                            info.GetFuncDesc(j, out descPtr);
                            var desc = Marshal.PtrToStructure<FUNCDESC>(descPtr);
                            if (desc.cParams < 0 || desc.cParams > 16) throw new InvalidOperationException("FORM_TYPELIB_PARAMETER_LIMIT");
                            string[] names = new string[17]; int obtained;
                            info.GetNames(desc.memid, names, names.Length, out obtained);
                            if (obtained < 1 || obtained > 17 || names[0] == null) throw new InvalidOperationException("FORM_TYPELIB_MEMBER_NAME_LIMIT");
                            if (names[0].Length > 128) throw new InvalidOperationException("FORM_TYPELIB_MEMBER_NAME_LIMIT");
                            declaredNames.Add(names[0]);
                            if (!wantedMembers.Contains(names[0]) && typeName != "IDHwpCtrlCode" &&
                                typeName != "IDHwpParameterSet" && !typeName.StartsWith("HForm", StringComparison.Ordinal) &&
                                typeName != "HShapeObject" && typeName != "HCharShape" && typeName != "IXHwpWindow") continue;
                            var parameters = new List<object>();
                            int size = Marshal.SizeOf<ELEMDESC>();
                            for (int k = 0; k < desc.cParams; k++) {
                                var element = Marshal.PtrToStructure<ELEMDESC>(IntPtr.Add(desc.lprgelemdescParam, checked(k * size)));
                                parameters.Add(new { name=(k + 1 < obtained ? names[k + 1] : ""),
                                    variant_type=(int)element.tdesc.vt, flags=(int)element.desc.paramdesc.wParamFlags });
                            }
                            members.Add(new { name=names[0], member_id=desc.memid, invoke_kind=desc.invkind.ToString(),
                                return_variant_type=(int)desc.elemdescFunc.tdesc.vt, parameters=parameters });
                        } finally { if (descPtr != IntPtr.Zero) info.ReleaseFuncDesc(descPtr); }
                    }
                    types.Add(new { name=typeName, type_kind=attr.typekind.ToString(), declared_member_names=declaredNames, members=members });
                } finally {
                    if (attrPtr != IntPtr.Zero) info.ReleaseTypeAttr(attrPtr);
                    if (info != null && Marshal.IsComObject(info)) Marshal.ReleaseComObject(info);
                }
            }
            return new { library_name=libraryName, library_guid=libraryAttr.guid.ToString(), major_version=libraryAttr.wMajorVerNum,
                minor_version=libraryAttr.wMinorVerNum, system_kind=libraryAttr.syskind.ToString(), type_count=count,
                all_type_names=allTypeNames, selected_types=types };
        } finally { if (Marshal.IsComObject(library)) Marshal.ReleaseComObject(library); }
    }
}
'@ -ErrorAction Stop
    $results = @()
    foreach ($binary in @($path, $dllPath, $typePath)) {
        try {
            $surface = [P09FormTypeLibraryReader]::Read($binary, $libraryId)
            $results += [ordered]@{ binary_name=(Get-Item -LiteralPath $binary).Name; state='type_library_read'; surface=$surface }
        } catch {
            # 래퍼 아래 원인 오류 종류/HRESULT만 출력한다. 경로/전체 예외는 출력하지 않는다.
            $cause = $_.Exception
            for ($depth=0; $depth -lt 8 -and $null -ne $cause.InnerException; $depth++) { $cause = $cause.InnerException }
            $results += [ordered]@{ binary_name=(Get-Item -LiteralPath $binary).Name; state='type_library_unavailable'; error_type=$cause.GetType().Name; hresult=$cause.HResult }
        }
    }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $targetSha -or
        (Get-FileHash -LiteralPath $dllPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $dllSha -or
        (Get-FileHash -LiteralPath $typePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $typeSha) { throw 'FORM_TYPELIB_BINARY_CHANGED_DURING_READ' }
    $afterPids = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" | ForEach-Object { [int]$_.ProcessId } | Sort-Object)
    if (($beforePids -join ',') -ne ($afterPids -join ',')) { throw 'FORM_TYPELIB_HWP_PROCESS_SET_CHANGED' }
    [ordered]@{ schema_version='hwpx-agent.click-here-lifecycle-type-surface/v1'; state='read_only_inspection_complete_not_native_qualification';
        exact_build='11.0.0.9136'; executable_sha256=$targetSha; automation_dll_sha256=$dllSha; binaries=$results;
        registered_typelib_sha256=$typeSha; registered_typelib_bytes=$typeItem.Length;
        no_com_server_activation=$true; registry_read_only=$true; type_library_registration_requested=$false;
        hwp_process_set_unchanged=$true; raw_document_values_or_absolute_paths_present=$false;
        native_property_set_or_save_reopen_qualified=$false; p09_complete=$false } | ConvertTo-Json -Depth 12 -Compress
} catch {
    $code = if ($_.Exception.Message -match '^FORM_TYPELIB_[A-Z_]+$') { $_.Exception.Message } else { $_.Exception.GetType().Name }
    [ordered]@{ state='fail'; error_code=$code; no_com_server_activation=$true } | ConvertTo-Json -Compress
    exit 2
} finally {
    foreach ($key in $keys) { $key.Dispose() }
    if ($null -ne $registry) { $registry.Dispose() }
}
