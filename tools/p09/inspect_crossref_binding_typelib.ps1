# Original REGKIND_NONE reader, two fixed source transforms, filtered declarations only.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
try {
    $path=Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
    $item=Get-Item -LiteralPath $path -Force
    if ($item -isnot [IO.FileInfo] -or $item.Length -gt 32768 -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'XREF_BINDING_TYPELIB_READER_BOUNDARY'}
    $bytes=[IO.File]::ReadAllBytes($path)
    $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    if ($hash -cne 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1') {throw 'XREF_BINDING_TYPELIB_READER_IDENTITY'}
    $text=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
    function Replace-P09XrefBindingOnce([string]$Text,[string]$Before,[string]$After) {
        $at=$Text.IndexOf($Before,[StringComparison]::Ordinal)
        if ($at -lt 0 -or $Text.IndexOf($Before,$at+$Before.Length,[StringComparison]::Ordinal) -ge 0) {
            throw 'XREF_BINDING_TYPELIB_EXACT_TRANSFORM'
        }
        return $Text.Substring(0,$at)+$After+$Text.Substring($at+$Before.Length)
    }
    $text=Replace-P09XrefBindingOnce $text `
        '"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName",' `
        '"Application", "XHwpDocuments", "Active_XHwpDocument", "Item", "Count", "ItemFromName", "ItemFormName", "FullName", "Modified",'
    $text=Replace-P09XrefBindingOnce $text 'hwpx-agent.click-here-lifecycle-type-surface/v1' 'hwpx-agent.crossref-binding-declarations/v1'
    $output=@(& ([scriptblock]::Create($text)))
    if ($output.Count -ne 1 -or $output[0] -isnot [string] -or $output[0].Length -gt 262144) {throw 'XREF_BINDING_TYPELIB_OUTPUT_BOUNDARY'}
    $snapshot=$output[0] | ConvertFrom-Json -Depth 16
    if ($snapshot.state -cne 'read_only_inspection_complete_not_native_qualification' -or
        $snapshot.no_com_server_activation -ne $true -or $snapshot.registry_read_only -ne $true -or
        $snapshot.hwp_process_set_unchanged -ne $true) {throw 'XREF_BINDING_TYPELIB_ORIGINAL_READER_FAILED'}
    foreach ($binary in $snapshot.binaries) {
        if ($binary.state -ceq 'type_library_read') {
            $binary.surface.selected_types=@($binary.surface.selected_types | Where-Object {
                $_.name -cin @('IHwpObject','IXHwpDocuments','IXHwpDocument')
            } | ForEach-Object {
                $_.members=@($_.members | Where-Object {
                    $_.name -cin @('Application','XHwpDocuments','Active_XHwpDocument','Count','FullName','Modified','Version','SetActive_XHwpDocument')
                })
                $_.declared_member_names=@($_.members.name | Sort-Object -Unique)
                $_
            })
            $binary.surface.all_type_names=@($binary.surface.selected_types.name)
        }
    }
    $snapshot | ConvertTo-Json -Depth 12 -Compress
} catch {
    $code=if ($_.Exception.Message -cmatch '^XREF_BINDING_TYPELIB_[A-Z_]+$') {$_.Exception.Message} else {'XREF_BINDING_TYPELIB_INSPECTION_FAILED'}
    [ordered]@{state='fail';error_code=$code;no_com_server_activation=$true} | ConvertTo-Json -Compress
    exit 2
}
