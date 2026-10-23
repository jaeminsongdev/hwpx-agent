# 설치된 선언만 읽는다. COM 서버 활성화/Action/GetDefault/SetItem/문서 IO 없음.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
$bytes=[IO.File]::ReadAllBytes($path)
if ($bytes.Length -gt 32768 -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'BLOCK642_ORIGINAL_INSPECTOR_CHANGED'}
$source=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
$before='if (!wantedTypes.Contains(typeName)) continue;'
$after='if (!wantedTypes.Contains(typeName) && typeName.IndexOf("Book", StringComparison.OrdinalIgnoreCase) < 0 && typeName.IndexOf("InsertText", StringComparison.OrdinalIgnoreCase) < 0 && typeName.IndexOf("Action", StringComparison.OrdinalIgnoreCase) < 0 && typeName.IndexOf("ParameterSet", StringComparison.OrdinalIgnoreCase) < 0) continue;'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK642_EXACT_TYPE_PROJECTION'}
$source=$source.Replace($before,$after)
$before='"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'
$after='"Type", "Command", "HSet", "HBookMark", "HInsertText", "HAction", "HParameterSet", "SelectText", "SetPos", "CreateAction", "CreateSet", "GetDefault", "SetItem", "Execute", "Run", "Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK642_EXACT_MEMBER_PROJECTION'}
$source=$source.Replace($before,$after)
$output=@(& ([scriptblock]::Create($source)))
if ($output.Count -ne 1 -or $output[0].Length -gt 262144) {throw 'BLOCK642_INSPECTION_OUTPUT_BOUND'}
$snapshot=$output[0]|ConvertFrom-Json
if ($snapshot.state -cne 'read_only_inspection_complete_not_native_qualification' -or -not $snapshot.no_com_server_activation -or -not $snapshot.hwp_process_set_unchanged) {throw 'BLOCK642_READONLY_INSPECTION_FAILED'}
$library=@($snapshot.binaries|Where-Object {$_.state -ceq 'type_library_read' -and $_.binary_name -ieq 'HwpObject.tlb'})
if ($library.Count -ne 1) {throw 'BLOCK642_REGISTERED_LIBRARY_MISSING'}
$selected=@(foreach ($type in $library[0].surface.selected_types) {
    if ($type.name -match 'Book|InsertText|Action|ParameterSet' -or $type.name -ceq 'IHwpObject') {
        $names=if ($type.name -ceq 'IHwpObject') {@('HAction','HParameterSet','SelectText','SetPos','SelectionMode','GetPos')} else {@('Name','Type','Command','HSet','HBookMark','HInsertText','Text','CreateAction','CreateSet','GetDefault','SetItem','Item','Execute','Run')}
        [ordered]@{name=$type.name;type_kind=$type.type_kind;members=@($type.members|Where-Object {$_.name -cin $names})}
    }
})
[ordered]@{state='OBSERVED642_INSTALLED_BLOCK_CAPTURE_DECLARATIONS_NOT_NATIVE';exact_build=$snapshot.exact_build;
    executable_sha256=$snapshot.executable_sha256;automation_dll_sha256=$snapshot.automation_dll_sha256;
    typelib_sha256=$snapshot.registered_typelib_sha256;selected_types=$selected;
    related_type_names=@($library[0].surface.all_type_names|Where-Object {$_ -match 'Book|InsertText|Action|ParameterSet'});
    no_com_server_activation=$true;registry_read_only=$true;hwp_process_set_unchanged=$true;
    native_GetDefault_Execute_SetItem_or_SelectText_invoked=$false;native_execution_authorized=$false;P09_complete=$false}|ConvertTo-Json -Depth 12 -Compress
