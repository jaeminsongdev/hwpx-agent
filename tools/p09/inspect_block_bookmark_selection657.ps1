# Exact installed selection ABI metadata. No server activation or document IO.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'BLOCK657_ORIGINAL_INSPECTOR_CHANGED'}
$source=[IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false,$true))
$changes=@(
    @('"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",',
      '"CreateSet", "SelectText", "GetSelectedPos", "GetSelectedPosBySet", "Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",'),
    @('variant_type=(int)element.tdesc.vt, flags=(int)element.desc.paramdesc.wParamFlags',
      'variant_type=(int)element.tdesc.vt, pointer_variant_type=(element.tdesc.vt == 26 ? (int)Marshal.PtrToStructure<TYPEDESC>(element.tdesc.lpValue).vt : -1), flags=(int)element.desc.paramdesc.wParamFlags')
)
foreach ($change in $changes) {
    if ($source.Split(@($change[0]),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK657_EXACT_METADATA_PROJECTION'}
    $source=$source.Replace($change[0],$change[1])
}
$output=@(& ([scriptblock]::Create($source)))
if ($output.Count -ne 1 -or $output[0].Length -gt 262144) {throw 'BLOCK657_OUTPUT_BOUND'}
$v=$output[0]|ConvertFrom-Json
if (-not $v.no_com_server_activation -or -not $v.hwp_process_set_unchanged -or $v.exact_build -cne '11.0.0.9136') {throw 'BLOCK657_CURRENT_METADATA_ONLY'}
$lib=@($v.binaries|Where-Object {$_.binary_name -ieq 'HwpObject.tlb' -and $_.state -ceq 'type_library_read'})
if ($lib.Count -ne 1) {throw 'BLOCK657_TYPELIB'}
[ordered]@{state='OBSERVED657_SELECTION_PARAMETER_DECLARATIONS_NOT_NATIVE';no_com_server_activation=$true;hwp_process_set_unchanged=$true;
    typelib_sha256=$v.registered_typelib_sha256;types=@($lib[0].surface.selected_types|Where-Object {$_.name -cin @('IHwpObject','IDHwpParameterSet')});
    Native_started=$false;P09_complete=$false}|ConvertTo-Json -Depth 12 -Compress
