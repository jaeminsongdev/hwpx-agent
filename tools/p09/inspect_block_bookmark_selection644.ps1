# Current installed declaration metadata only. No COM server/action activation.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
$bytes=[IO.File]::ReadAllBytes($path)
if ($bytes.Length -gt 32768 -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'BLOCK644_ORIGINAL_INSPECTOR_CHANGED'}
$source=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
$before='"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'
$after='"GetSelectedPos", "GetTextFile", "Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK644_EXACT_MEMBER_PROJECTION'}
$output=@(& ([scriptblock]::Create($source.Replace($before,$after))))
if ($output.Count -ne 1 -or $output[0].Length -gt 262144) {throw 'BLOCK644_INSPECTION_OUTPUT_BOUND'}
$snapshot=$output[0]|ConvertFrom-Json
if ($snapshot.state -cne 'read_only_inspection_complete_not_native_qualification' -or -not $snapshot.no_com_server_activation -or -not $snapshot.hwp_process_set_unchanged) {throw 'BLOCK644_READONLY_INSPECTION_FAILED'}
$library=@($snapshot.binaries|Where-Object {$_.state -ceq 'type_library_read' -and $_.binary_name -ieq 'HwpObject.tlb'})
if ($library.Count -ne 1) {throw 'BLOCK644_REGISTERED_LIBRARY_MISSING'}
$types=@($library[0].surface.selected_types|Where-Object {$_.name -ceq 'IHwpObject'})
if ($types.Count -ne 1) {throw 'BLOCK644_ONE_IHWPOBJECT'}
[ordered]@{state='OBSERVED644_INSTALLED_SELECTION_DECLARATIONS_NOT_NATIVE';exact_build=$snapshot.exact_build;
    typelib_sha256=$snapshot.registered_typelib_sha256;
    selected_members=@($types[0].members|Where-Object {$_.name -cin @('GetSelectedPos','GetTextFile','GetPos','GetPosBySet','SelectionMode','EditMode')});
    no_com_server_activation=$true;registry_read_only=$true;hwp_process_set_unchanged=$true;
    native_selection_methods_invoked=$false;native_execution_authorized=$false;P09_complete=$false}|ConvertTo-Json -Depth 12 -Compress
