# Fixed007 only. A restrictive source lease PRECEDES Open; never relax sharing.
# No CLI/COM activation/retry. The original owned Open and observations remain intact.
Set-StrictMode -Version Latest

function Open-P09XrefCapture007GuardedSource($State) {
    Assert-P09XrefBinding (-not $State.Contains('capture007_source_lease')) 'CAPTURE_SEVEN_SOURCE_NO_RETRY'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $fixed=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx'
    Assert-P09XrefBinding ([string]::Equals($State.source,$fixed,[StringComparison]::OrdinalIgnoreCase) -and
        $State.source_sha256 -ceq '64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184') 'CAPTURE_SEVEN_SOURCE_FIXED_IDENTITY'
    $record=[ordered]@{phase='before_source_open';acquisition_attempted=$true;lease_acquired=$false;
        original_open_entered=$false;original_open_returned=$false;lease_closed=$false;error_code=$null;
        read_only_sharing=$true;native_semantics_qualified=$false;error_kind=$null;error_id=$null;error_line=$null}
    $State.trace.operations['capture007_source_guard']=$record
    $State['capture007_source_lease']=$null
    try {
        # Bound the entry without an extra Get-FileHash call before the lease.
        # The digest is read from the HELD stream; original Open still performs
        # its unchanged Assert-P58File check under the same restrictive lease.
        $record.phase='source_file_boundary';$item=Get-Item -LiteralPath $fixed -Force
        Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq 14425) 'CAPTURE_SEVEN_SOURCE_SIZE'
        $ancestor=$item
        while ($null -ne $ancestor) {
            Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'CAPTURE_SEVEN_SOURCE_LINKED'
            if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
        }
        $record.phase='read_lease_acquisition'
        try {$State.capture007_source_lease=[IO.File]::Open($fixed,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)}
        catch {throw (Get-P09XrefSourceReadLeaseFailureCode $_.Exception)}
        $record.lease_acquired=$true
        $record.phase='held_source_digest';$algorithm=[Security.Cryptography.SHA256]::Create()
        try {
            $sha=([BitConverter]::ToString($algorithm.ComputeHash($State.capture007_source_lease))).Replace('-','').ToLowerInvariant()
            Assert-P09XrefBinding ($State.capture007_source_lease.Length -eq 14425 -and $sha -ceq $State.source_sha256) 'CAPTURE_SEVEN_HELD_SOURCE_DIGEST'
        } finally {$algorithm.Dispose()}
        $record.phase='original_source_open_under_read_lease';$record.original_open_entered=$true
        $State.document=Open-P58Document $State.owner $State.source $State.source_sha256
        $record.original_open_returned=$true;$record.phase='source_opened_guard_retained'
        # Keep the original no-write/no-delete lease through SaveAs, all later
        # callbacks, final source verification, and owned-session cleanup.
    } catch {
        $kind=$_.Exception.GetType().Name
        if ($kind -cmatch '^[A-Za-z0-9]{1,80}$') {$record.error_kind=$kind}
        $id=$_.FullyQualifiedErrorId
        if ($id -cmatch '^[A-Za-z0-9_,.+-]{1,128}$') {$record.error_id=$id}
        $record.error_line=[int]$_.InvocationInfo.ScriptLineNumber
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {$_.Exception.Message}
            else {'P09_XREF_BIND_CAPTURE_SEVEN_SOURCE_OPEN_FAILED_NO_RAW_VALUES'}
        $record.error_code=$code;throw $code
    }
}

function Close-P09XrefCapture007SourceGuard($State) {
    if ($State.Contains('capture007_source_lease') -and $null -ne $State.capture007_source_lease) {
        try {$State.capture007_source_lease.Dispose();$State.trace.operations.capture007_source_guard.lease_closed=$true}
        finally {$State.capture007_source_lease=$null}
    }
}

function Get-P09XrefCapture007GuardedPortDefinitions {
    foreach ($definition in (& $script:P09XrefCapture007OriginalPortFactory)) {
        $rules=@()
        if ($definition.name -ceq 'Invoke-P09XrefPreassignedCaseStep') {
            $rules=,@("'source_open' {`$State.document=Open-P58Document `$State.owner `$State.source `$State.source_sha256}",
                "'source_open' {Open-P09XrefCapture007GuardedSource `$State}")
        } elseif ($definition.name -ceq 'Complete-P09XrefPreassignedCasePorts') {
            $rules=,@('try {Close-P09XrefPreassignedCaseOwner $State}',
                'try {try {Close-P09XrefPreassignedCaseOwner $State} finally {Close-P09XrefCapture007SourceGuard $State}}')
        }
        foreach ($rule in $rules) {
            Assert-P09XrefBinding ([regex]::Matches($definition.inner,[regex]::Escape($rule[0])).Count -eq 1) 'CAPTURE_SEVEN_SOURCE_GUARD_EXACT_REWRITE'
            $original=$definition.inner;$definition.inner=$original.Replace($rule[0],$rule[1])
            Assert-P09XrefBinding ($definition.inner.Replace($rule[1],$rule[0]) -ceq $original) 'CAPTURE_SEVEN_SOURCE_GUARD_WHOLE_BODY_INVERSE'
        }
        $tokens=$null;$errors=$null
        [void][Management.Automation.Language.Parser]::ParseInput($definition.inner,[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_SEVEN_SOURCE_GUARD_PORT_PARSE'
        $definition
    }
}

function Initialize-P09XrefCapture007SourceGuard {
    Assert-P09XrefBinding ($null -eq (Get-Variable P09XrefCapture007OriginalPortFactory -Scope Script -ErrorAction SilentlyContinue)) 'CAPTURE_SEVEN_SOURCE_GUARD_NO_REINSTALL'
    $script:P09XrefCapture007OriginalPortFactory=(Get-Command Get-P09XrefPreassignedPortDefinitions -CommandType Function -ErrorAction Stop).ScriptBlock
    Set-Item -Path Function:script:Get-P09XrefPreassignedPortDefinitions -Value (Get-Command Get-P09XrefCapture007GuardedPortDefinitions).ScriptBlock
}
