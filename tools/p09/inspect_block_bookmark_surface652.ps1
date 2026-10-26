# Read-only complete BookMark declaration surface; no server activation/actions.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'BLOCK652_ORIGINAL_INSPECTOR_CHANGED'}
$source=[IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false,$true))
$before='if (!wantedTypes.Contains(typeName)) continue;'
$after='if (!wantedTypes.Contains(typeName) && typeName != "HBookMark") continue;'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK652_TYPE_PROJECTION'}
$source=$source.Replace($before,$after)
$before='if (!wantedMembers.Contains(names[0]) && typeName != "IDHwpCtrlCode" &&'
$after='if (!wantedMembers.Contains(names[0]) && typeName != "HBookMark" && typeName != "IDHwpCtrlCode" &&'
if ($source.Split(@($before),[StringSplitOptions]::None).Length -ne 2) {throw 'BLOCK652_MEMBER_PROJECTION'}
$output=@(& ([scriptblock]::Create($source.Replace($before,$after))))
if ($output.Count -ne 1 -or $output[0].Length -gt 262144) {throw 'BLOCK652_OUTPUT_BOUND'}
$v=$output[0]|ConvertFrom-Json
if (-not $v.no_com_server_activation -or -not $v.hwp_process_set_unchanged -or $v.exact_build -cne '11.0.0.9136') {throw 'BLOCK652_CURRENT_METADATA_ONLY'}
$lib=@($v.binaries|Where-Object {$_.binary_name -ieq 'HwpObject.tlb' -and $_.state -ceq 'type_library_read'})
if ($lib.Count -ne 1) {throw 'BLOCK652_TYPELIB'}
[ordered]@{state='OBSERVED652_COMPLETE_BOOKMARK_DECLARATIONS_NOT_NATIVE';no_com_server_activation=$true;hwp_process_set_unchanged=$true;
    typelib_sha256=$v.registered_typelib_sha256;types=@($lib[0].surface.selected_types|Where-Object {$_.name -cin @('HBookMark','IDHwpParameterSet')});
    Native_started=$false;P09_complete=$false}|ConvertTo-Json -Depth 12 -Compress
