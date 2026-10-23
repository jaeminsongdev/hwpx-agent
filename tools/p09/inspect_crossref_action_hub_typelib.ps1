# Additional installed HAction/HParameterSet declarations, no server activation.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
try {
    $path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
    $item=Get-Item -LiteralPath $path -Force
    if ($item -isnot [IO.FileInfo] -or $item.Length -gt 32768 -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'XREF_HUB_TYPELIB_READER_BOUNDARY'}
    $raw=[IO.File]::ReadAllBytes($path)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant() -cne
        'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'XREF_HUB_TYPELIB_READER_IDENTITY'}
    $text=[Text.UTF8Encoding]::new($false,$true).GetString($raw)
    function Replace-P09XrefHubOnce([string]$Text,[string]$Before,[string]$After) {
        $at=$Text.IndexOf($Before,[StringComparison]::Ordinal)
        if ($at -lt 0 -or $Text.IndexOf($Before,$at+$Before.Length,[StringComparison]::Ordinal) -ge 0) {throw 'XREF_HUB_TYPELIB_EXACT_TRANSFORM'}
        return $Text.Substring(0,$at)+$After+$Text.Substring($at+$Before.Length)
    }
    $text=Replace-P09XrefHubOnce $text '"HFormEditAttr", "HFormButtonAttr", "HFormCharshapeattr", "HCharShape"' `
        '"HFormEditAttr", "HFormButtonAttr", "HFormCharshapeattr", "HCharShape", "HAction", "HParameterSet"'
    $text=Replace-P09XrefHubOnce $text 'typeName != "HCharShape" && typeName != "IXHwpWindow") continue;' `
        'typeName != "HCharShape" && typeName != "IXHwpWindow" && typeName != "HAction" && typeName != "HParameterSet") continue;'
    $text=Replace-P09XrefHubOnce $text 'hwpx-agent.click-here-lifecycle-type-surface/v1' 'hwpx-agent.crossref-action-hub-declarations/v1'
    $output=@(& ([scriptblock]::Create($text)))
    if ($output.Count -ne 1 -or $output[0] -isnot [string] -or $output[0].Length -gt 524288) {throw 'XREF_HUB_TYPELIB_OUTPUT_LIMIT'}
    $value=$output[0] | ConvertFrom-Json -Depth 16
    if ($value.state -cne 'read_only_inspection_complete_not_native_qualification' -or
        $value.no_com_server_activation -ne $true -or $value.hwp_process_set_unchanged -ne $true) {throw 'XREF_HUB_TYPELIB_ORIGINAL_READER_FAILED'}
    foreach ($binary in $value.binaries) {
        if ($binary.state -ceq 'type_library_read') {
            $binary.surface.selected_types=@($binary.surface.selected_types | Where-Object {$_.name -cin @('HAction','HParameterSet')} | ForEach-Object {
                $_.members=@($_.members | Where-Object {$_.name -cin @('GetDefault','Execute','HActionCrossRef','ActionCrossRef')})
                $_.declared_member_names=@($_.members.name | Sort-Object -Unique);$_
            })
            $binary.surface.all_type_names=@($binary.surface.selected_types.name)
        }
    }
    $value | ConvertTo-Json -Depth 12 -Compress
} catch {
    $code=if ($_.Exception.Message -cmatch '^XREF_HUB_TYPELIB_[A-Z_]+$') {$_.Exception.Message} else {'XREF_HUB_TYPELIB_INSPECTION_FAILED'}
    [ordered]@{state='fail';error_code=$code;no_com_server_activation=$true} | ConvertTo-Json -Compress
    exit 2
}
