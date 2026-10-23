# Read-only Windows signature/version checks for two fixed local runtime images. Never changes trust or launches an app.
[CmdletBinding()]
param([switch]$VerifyCurrentRuntimeOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$phase='closed_mode'
try {
    if (-not $VerifyCurrentRuntimeOnly) {throw 'P555_SIGNATURE_CLOSED_MODE'}
    $phase='canonical_security_module'
    $module=Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1'
    Import-Module -Name $module -ErrorAction Stop
    $base=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python'
    $expected=@{
        'python.exe'=@(107312,'7a4102b91959bb234507850ea584e1d31d300a6831b171e4aadc59ff592f0234');
        'python312.dll'=@(6985520,'e39aa2da5ea2d310d89994f71bf913a0a137ebaf9f692a565b8c896081512f28')}
    $rows=@()
    foreach ($name in @('python.exe','python312.dll')) {
        $phase='file_identity'
        $path=Join-Path $base $name;$item=Get-Item -LiteralPath $path -Force
        if ($item -isnot [IO.FileInfo] -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $item.Length -ne $expected[$name][0] -or $item.VersionInfo.FileVersion -cne '3.12.14') {throw 'P555_SIGNATURE_FILE_IDENTITY'}
        $phase='sha256';$algorithm=[Security.Cryptography.SHA256]::Create()
        try {$sha=([BitConverter]::ToString($algorithm.ComputeHash([IO.File]::ReadAllBytes($path)))).Replace('-','').ToLowerInvariant()}
        finally {$algorithm.Dispose()}
        if ($sha -cne $expected[$name][1]) {throw 'P555_SIGNATURE_IMAGE_CHANGED'}
        $phase='windows_signature';$signature=Get-AuthenticodeSignature -LiteralPath $path
        if ($signature.Status -ne [Management.Automation.SignatureStatus]::Valid -or $null -eq $signature.SignerCertificate -or
            $signature.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName,$false) -cne 'OpenAI OpCo, LLC') {
            throw 'P555_SIGNATURE_CURRENT_WINDOWS_VALID_PUBLISHER_REQUIRED'
        }
        $rows+= [ordered]@{path=$name;bytes=$item.Length;sha256=$sha;version=$item.VersionInfo.FileVersion;windows_signature='Valid';publisher='OpenAI OpCo, LLC'}
    }
    [ordered]@{state='PASS_CURRENT_FIXED_EXE_CORE_WINDOWS_SIGNATURES_NOT_NATIVE_QUALIFICATION';images=$rows;trust_or_runtime_files_modified=$false}|ConvertTo-Json -Depth 4 -Compress
} catch {
    $code=if ($_.Exception.Message -cmatch '^P555_[A-Z_]+$') {$_.Exception.Message} else {'P555_SIGNATURE_FAILURE_NO_RAW_VALUES'}
    [ordered]@{state='FAILED_CURRENT_PYTHON_SIGNATURE_CHECK';error_code=$code;phase=$phase;kind=$_.Exception.GetType().Name;line=[int]$_.InvocationInfo.ScriptLineNumber}|ConvertTo-Json -Compress
    exit 2
}
