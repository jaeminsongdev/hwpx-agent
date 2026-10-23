# Program projection only, no Native activation. Fixed original worker + fixed006 namespace.
Set-StrictMode -Version Latest

function Get-P09XrefCapture006WorkerProgram {
    $path=Join-Path $PSScriptRoot 'run-crossref-qualified-fixed-worker.ps1'
    $item=Get-Item -LiteralPath $path -Force
    if ($item -isnot [IO.FileInfo] -or $item.Length -ne 5420) {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_SOURCE_SIZE'}
    $ancestor=$item
    while ($null -ne $ancestor) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_SOURCE_LINK'}
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    Start-Sleep -Milliseconds 50
    $bytes=[IO.File]::ReadAllBytes($path);$algorithm=[Security.Cryptography.SHA256]::Create()
    try {$sha=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$algorithm.Dispose()}
    if ($sha -cne '7b10f11316296600d42d4953e223eea2363ed6d930b3c100e1af537454db56cf') {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_SOURCE_IDENTITY'}
    $original=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
    $marker="    `$phase='prewarm';Initialize-P09XrefExistingOwnerAdapter;Initialize-P09XrefPreassignedCasePorts"
    $insertion="    . (Join-Path `$PSScriptRoot 'crossref-capture006-namespace.ps1')`r`n    Initialize-P09XrefCapture006Namespace`r`n    . (Join-Path `$PSScriptRoot 'crossref-capture006-source-guard.ps1')`r`n    Initialize-P09XrefCapture006SourceGuard`r`n"
    if ([regex]::Matches($original,[regex]::Escape($marker)).Count -ne 1) {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_EXACT_PREWARM_MARKER'}
    $changed=$original.Replace($marker,$insertion+$marker)
    if ($changed.Replace($insertion,'') -cne $original) {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_WHOLE_PROGRAM_INVERSE'}
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($changed,$path,[ref]$tokens,[ref]$errors)
    if (@($errors).Count -ne 0) {throw 'P09_XREF_BIND_CAPTURE_SIX_WORKER_PROGRAM_PARSE'}
    return [pscustomobject]@{original=$original;changed=$changed;insertion=$insertion;program=$ast.GetScriptBlock();original_sha256=$sha;source=$path}
}
