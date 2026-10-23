# 원 타입 조사기는 보존하고 고정된 세 타입의 선언만 추가 관측한다.
[CmdletBinding()]
param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
try {
    $original = Join-Path $PSScriptRoot 'inspect_click_here_lifecycle_typelib.ps1'
    $item = Get-Item -LiteralPath $original -ErrorAction Stop
    if (-not ($item -is [System.IO.FileInfo]) -or $item.Length -gt 32768 -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'REFERENCE_TYPELIB_SOURCE_BOUNDARY'
    }
    $expected = 'a455f7e00acbd106de6b5c5f73a654bc450a421d47e88574aee56744abfecbf1'
    $raw = [System.IO.File]::ReadAllBytes($original)
    $actual = [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()
    if ($actual -ne $expected) { throw 'REFERENCE_TYPELIB_SOURCE_DRIFT' }
    $source = [System.Text.UTF8Encoding]::new($false, $true).GetString($raw)
    function Replace-ExactlyOnce([string]$Text, [string]$Before, [string]$After) {
        $index = $Text.IndexOf($Before, [StringComparison]::Ordinal)
        if ($index -lt 0 -or $Text.IndexOf($Before, $index + $Before.Length, [StringComparison]::Ordinal) -ge 0) {
            throw 'REFERENCE_TYPELIB_TRANSFORM_BOUNDARY'
        }
        return $Text.Substring(0, $index) + $After + $Text.Substring($index + $Before.Length)
    }
    $source = Replace-ExactlyOnce $source `
        '"HFormEditAttr", "HFormButtonAttr", "HFormCharshapeattr", "HCharShape"' `
        '"HFormEditAttr", "HFormButtonAttr", "HFormCharshapeattr", "HCharShape", "HActionCrossRef", "HFieldCtrl", "HInsertFieldTemplate"'
    $source = Replace-ExactlyOnce $source `
        'typeName != "HCharShape" && typeName != "IXHwpWindow") continue;' `
        'typeName != "HCharShape" && typeName != "IXHwpWindow" && typeName != "HActionCrossRef" && typeName != "HFieldCtrl" && typeName != "HInsertFieldTemplate") continue;'
    $source = Replace-ExactlyOnce $source `
        'hwpx-agent.click-here-lifecycle-type-surface/v1' `
        'hwpx-agent.reference-installed-type-surface/v1'
    if ($ValidateOnly) {
        $transformed = [System.Text.Encoding]::UTF8.GetBytes($source)
        [ordered]@{
            state = 'exact_original_plus_three_closed_declaration_transforms'
            original_sha256 = $actual
            transformed_sha256 = [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($transformed)).ToLowerInvariant()
            added_types = @('HActionCrossRef', 'HFieldCtrl', 'HInsertFieldTemplate')
            registry_or_typelib_read = $false
            no_com_server_activation = $true
        } | ConvertTo-Json -Compress
        return
    }
    # 신뢰 경계를 변경하지 않는다. 원 검사기의 REGKIND_NONE, binary SHA,
    # Registry32 읽기전용 및 한글 process-set 전후 검사를 그대로 실행한다.
    $output = @(& ([scriptblock]::Create($source)))
    if ($output.Count -ne 1 -or $output[0] -isnot [string] -or $output[0].Length -gt 262144) {
        throw 'REFERENCE_TYPELIB_OUTPUT_BOUNDARY'
    }
    $snapshot = $output[0] | ConvertFrom-Json -Depth 16
    foreach ($binary in $snapshot.binaries) {
        if ($binary.state -eq 'type_library_read') {
            $binary.surface.selected_types = @($binary.surface.selected_types | Where-Object {
                $_.name -in @('HActionCrossRef', 'HFieldCtrl', 'HInsertFieldTemplate')
            })
        }
    }
    $snapshot | ConvertTo-Json -Depth 12 -Compress
} catch {
    $code = if ($_.Exception.Message -match '^REFERENCE_TYPELIB_[A-Z_]+$') {
        $_.Exception.Message
    } else { 'REFERENCE_TYPELIB_INSPECTION_FAILED' }
    [ordered]@{ state='fail'; error_code=$code; no_com_server_activation=$true } | ConvertTo-Json -Compress
    exit 2
}
