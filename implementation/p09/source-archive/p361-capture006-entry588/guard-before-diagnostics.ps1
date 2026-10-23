# Fixed006 only. A restrictive source lease PRECEDES Open; never relax sharing.
# No CLI/COM activation/retry. The original owned Open and observations remain intact.
Set-StrictMode -Version Latest

function Open-P09XrefCapture006GuardedSource($State) {
    Assert-P09XrefBinding (-not $State.Contains('capture006_source_lease')) 'CAPTURE_SIX_SOURCE_NO_RETRY'
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $fixed=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx'
    Assert-P09XrefBinding ([string]::Equals($State.source,$fixed,[StringComparison]::OrdinalIgnoreCase) -and
        $State.source_sha256 -ceq '64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184') 'CAPTURE_SIX_SOURCE_FIXED_IDENTITY'
    $record=[ordered]@{phase='before_source_open';acquisition_attempted=$true;lease_acquired=$false;
        original_open_entered=$false;original_open_returned=$false;lease_closed=$false;error_code=$null;
        read_only_sharing=$true;native_semantics_qualified=$false}
    $State.trace.operations['capture006_source_guard']=$record
    $State['capture006_source_lease']=$null
    try {
        # Original regular-file, ancestors, size and digest checks remain mandatory.
        [void](Assert-P58File $fixed 4194304 $State.source_sha256)
        try {$State.capture006_source_lease=[IO.File]::Open($fixed,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)}
        catch {throw (Get-P09XrefSourceReadLeaseFailureCode $_.Exception)}
        $record.lease_acquired=$true
        $algorithm=[Security.Cryptography.SHA256]::Create()
        try {
            $sha=([BitConverter]::ToString($algorithm.ComputeHash($State.capture006_source_lease))).Replace('-','').ToLowerInvariant()
            Assert-P09XrefBinding ($State.capture006_source_lease.Length -eq 14425 -and $sha -ceq $State.source_sha256) 'CAPTURE_SIX_HELD_SOURCE_DIGEST'
        } finally {$algorithm.Dispose()}
        $record.phase='original_source_open_under_read_lease';$record.original_open_entered=$true
        $State.document=Open-P58Document $State.owner $State.source $State.source_sha256
        $record.original_open_returned=$true;$record.phase='source_opened_guard_retained'
        # Keep the original no-write/no-delete lease through SaveAs, all later
        # callbacks, final source verification, and owned-session cleanup.
    } catch {
        $code=if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {$_.Exception.Message}
            else {'P09_XREF_BIND_CAPTURE_SIX_SOURCE_OPEN_FAILED_NO_RAW_VALUES'}
        $record.error_code=$code;throw $code
    }
}

function Close-P09XrefCapture006SourceGuard($State) {
    if ($State.Contains('capture006_source_lease') -and $null -ne $State.capture006_source_lease) {
        try {$State.capture006_source_lease.Dispose();$State.trace.operations.capture006_source_guard.lease_closed=$true}
        finally {$State.capture006_source_lease=$null}
    }
}

function Get-P09XrefCapture006GuardedPortDefinitions {
    foreach ($definition in (& $script:P09XrefCapture006OriginalPortFactory)) {
        $rules=@()
        if ($definition.name -ceq 'Invoke-P09XrefPreassignedCaseStep') {
            $rules=,@("'source_open' {`$State.document=Open-P58Document `$State.owner `$State.source `$State.source_sha256}",
                "'source_open' {Open-P09XrefCapture006GuardedSource `$State}")
        } elseif ($definition.name -ceq 'Complete-P09XrefPreassignedCasePorts') {
            $rules=,@('try {Close-P09XrefPreassignedCaseOwner $State}',
                'try {try {Close-P09XrefPreassignedCaseOwner $State} finally {Close-P09XrefCapture006SourceGuard $State}}')
        }
        foreach ($rule in $rules) {
            Assert-P09XrefBinding ([regex]::Matches($definition.inner,[regex]::Escape($rule[0])).Count -eq 1) 'CAPTURE_SIX_SOURCE_GUARD_EXACT_REWRITE'
            $original=$definition.inner;$definition.inner=$original.Replace($rule[0],$rule[1])
            Assert-P09XrefBinding ($definition.inner.Replace($rule[1],$rule[0]) -ceq $original) 'CAPTURE_SIX_SOURCE_GUARD_WHOLE_BODY_INVERSE'
        }
        $tokens=$null;$errors=$null
        [void][Management.Automation.Language.Parser]::ParseInput($definition.inner,[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_SIX_SOURCE_GUARD_PORT_PARSE'
        $definition
    }
}

function Initialize-P09XrefCapture006SourceGuard {
    Assert-P09XrefBinding ($null -eq (Get-Variable P09XrefCapture006OriginalPortFactory -Scope Script -ErrorAction SilentlyContinue)) 'CAPTURE_SIX_SOURCE_GUARD_NO_REINSTALL'
    $script:P09XrefCapture006OriginalPortFactory=(Get-Command Get-P09XrefPreassignedPortDefinitions -CommandType Function -ErrorAction Stop).ScriptBlock
    Set-Item -Path Function:script:Get-P09XrefPreassignedPortDefinitions -Value (Get-Command Get-P09XrefCapture006GuardedPortDefinitions).ScriptBlock
}
