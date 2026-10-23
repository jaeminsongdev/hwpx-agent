# 선언 조사만 수행한다. REGKIND_NONE, 기존 바이너리/프로세스 경계 유지.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
$bytes=[IO.File]::ReadAllBytes($path)
if ($bytes.Length -gt 32768 -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'RENDER631_TYPELIB_SOURCE_DRIFT'}
$source=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
$before='"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'RENDER631_EXACT_PROJECTION'}
$source=$source.Replace($before,('"CreatePageImage", "PageCount", '+$before))
$output=@(& ([scriptblock]::Create($source)))
if ($output.Count -ne 1 -or $output[0].Length -gt 262144) {throw 'RENDER631_OUTPUT_BOUND'}
$snapshot=$output[0]|ConvertFrom-Json
if ($snapshot.state -cne 'read_only_inspection_complete_not_native_qualification') {throw 'RENDER631_DECLARATION_INSPECTION_FAILED'}
$rows=@(foreach ($binary in $snapshot.binaries) {
    if ($binary.state -ceq 'type_library_read') {
        foreach ($type in $binary.surface.selected_types) {
            if ($type.name -ceq 'IHwpObject') {
                [ordered]@{binary_name=$binary.binary_name;members=@($type.members|Where-Object {$_.name -cin @('CreatePageImage','PageCount')})}
            }
        }
    }
})
[ordered]@{state='OBSERVED631_INSTALLED_RENDER_DECLARATIONS_NOT_NATIVE';declarations=$rows;
    typelib_sha256=$snapshot.registered_typelib_sha256;hwp_process_set_unchanged=$snapshot.hwp_process_set_unchanged;
    no_com_server_activation=$snapshot.no_com_server_activation;Native_render_qualified=$false}|ConvertTo-Json -Depth 12 -Compress
