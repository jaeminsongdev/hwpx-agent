# Fixed009: acquire saved artifact read/no-write/no-delete lease BEFORE reopening.
# No activation, original replacement IO, retry, alternate path or relaxed sharing.
Set-StrictMode -Version Latest

function Open-P09XrefCapture009SavedGuard($State) {
    Assert-P09XrefBinding (-not $State.Contains('capture009_saved_lease')) 'CAPTURE_NINE_SAVED_NO_RETRY'
    $pin=$State.trace.artifacts.saved
    $scope=Get-P09XrefArtifactScope $State.case_index 'saved_clean' $pin.sha256
    $record=[ordered]@{phase='saved_boundary';lease_acquired=$false;lease_closed=$false;
        read_only_sharing=$true;digest_verified=$false;error_code=$null;native_semantics_qualified=$false}
    $State.trace.operations['capture009_saved_guard']=$record
    $State['capture009_saved_lease']=$null
    try {
        Assert-P09XrefBinding ($pin.bytes -is [int] -or $pin.bytes -is [long]) 'CAPTURE_NINE_SAVED_SIZE_TYPE'
        Assert-P09XrefBinding ($pin.bytes -gt 0 -and $pin.bytes -le 4194304) 'CAPTURE_NINE_SAVED_SIZE'
        $item=Get-Item -LiteralPath $scope.path -Force
        Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq $pin.bytes) 'CAPTURE_NINE_SAVED_FILE'
        $ancestor=$item
        while ($null -ne $ancestor) {
            Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'CAPTURE_NINE_SAVED_LINKED'
            if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
        }
        $record.phase='saved_read_lease'
        try {$State.capture009_saved_lease=[IO.File]::Open($scope.path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)}
        catch {throw ((Get-P09XrefSourceReadLeaseFailureCode $_.Exception).Replace('SOURCE_READ_LEASE','SAVED_READ_LEASE'))}
        $record.lease_acquired=$true;$record.phase='saved_held_digest'
        $algorithm=[Security.Cryptography.SHA256]::Create();$watch=[Diagnostics.Stopwatch]::StartNew()
        try {
            $buffer=[byte[]]::new(65536);$count=0L
            while (($n=$State.capture009_saved_lease.Read($buffer,0,$buffer.Length)) -ne 0) {
                $count+=$n;Assert-P09XrefBinding ($count -le 4194304) 'CAPTURE_NINE_SAVED_READ_LIMIT'
                [void]$algorithm.TransformBlock($buffer,0,$n,$buffer,0)
                $delay=[int][Math]::Ceiling(($count/2097152.0-$watch.Elapsed.TotalSeconds)*1000)
                if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
            }
            [void]$algorithm.TransformFinalBlock([byte[]]::new(0),0,0)
            $sha=([BitConverter]::ToString($algorithm.Hash)).Replace('-','').ToLowerInvariant()
            Assert-P09XrefBinding ($count -eq $pin.bytes -and $sha -ceq $scope.sha256) 'CAPTURE_NINE_SAVED_HELD_DIGEST'
        } finally {$watch.Stop();$algorithm.Dispose()}
        $record.digest_verified=$true;$record.phase='saved_guard_retained_before_original_fresh_open'
        # Original fresh-session Open, paired artifact observations, final hashes
        # and owner cleanup remain intact. Keep lease until original completion.
    } catch {
        $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message}
            else {'P09_XREF_BIND_CAPTURE_NINE_SAVED_GUARD_FAILED_NO_RAW_VALUES'}
        $record.error_code=$code;throw $code
    }
}

function Close-P09XrefCapture009SavedGuard($State) {
    if ($State.Contains('capture009_saved_lease') -and $null -ne $State.capture009_saved_lease) {
        try {$State.capture009_saved_lease.Dispose();$State.trace.operations.capture009_saved_guard.lease_closed=$true}
        finally {$State.capture009_saved_lease=$null}
    }
}

function Get-P09XrefCapture009ArtifactObservationDefinition {
    $path=Join-Path $PSScriptRoot 'crossref-owned-artifact.ps1'
    $bytes=[IO.File]::ReadAllBytes($path);$algorithm=[Security.Cryptography.SHA256]::Create()
    try {$sha=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()} finally {$algorithm.Dispose()}
    Assert-P09XrefBinding ($sha -ceq 'd4c3aa70f4b251fbe34e0ef5d0e9093bfb6ff2daa5702316021888b811ac58af') 'CAPTURE_NINE_ORIGINAL_ARTIFACT_SOURCE'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput([Text.UTF8Encoding]::new($false,$true).GetString($bytes),$path,[ref]$tokens,[ref]$errors)
    $found=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Observe-P09XrefOwnedArtifact'},$false))
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $found.Count -eq 1) 'CAPTURE_NINE_ORIGINAL_ARTIFACT_PARSE'
    $original=$found[0].Extent.Text
    $before='$stream=[IO.File]::Open($scope.path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)'
    $after='try {'+$before+'} catch {throw ((Get-P09XrefSourceReadLeaseFailureCode $_.Exception).Replace(''SOURCE_READ_LEASE'',''ARTIFACT_READ_LEASE''))}'
    Assert-P09XrefBinding ([regex]::Matches($original,[regex]::Escape($before)).Count -eq 1) 'CAPTURE_NINE_ONE_ARTIFACT_DIAGNOSTIC_REWRITE'
    $changed=$original.Replace($before,$after)
    Assert-P09XrefBinding ($changed.Replace($after,$before) -ceq $original) 'CAPTURE_NINE_ARTIFACT_WHOLE_FUNCTION_INVERSE'
    $tokens=$null;$errors=$null;$projected=[Management.Automation.Language.Parser]::ParseInput($changed,$path,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_NINE_ARTIFACT_DIAGNOSTIC_PARSE'
    return [pscustomobject]@{original=$original;changed=$changed;before=$before;after=$after;loader=$projected.GetScriptBlock()}
}

function Get-P09XrefCapture009ArtifactPortDefinitions {
    foreach ($definition in (& $script:P09XrefCapture009SourcePortFactory)) {
        $rules=@()
        if ($definition.name -ceq 'Invoke-P09XrefPreassignedCaseStep') {
            $before='$State.document=Open-P09XrefSavedInFreshSession $State.owner $State.previous_identity $State.case_index $State.trace.artifacts.saved.sha256 $record'
            $rules=,@($before,('Open-P09XrefCapture009SavedGuard $State;'+$before))
        } elseif ($definition.name -ceq 'Complete-P09XrefPreassignedCasePorts') {
            $before='try {try {Close-P09XrefPreassignedCaseOwner $State} finally {Close-P09XrefCapture009SourceGuard $State}}'
            $rules=,@($before,('try {'+$before+' finally {Close-P09XrefCapture009SavedGuard $State}}'))
        }
        foreach ($rule in $rules) {
            Assert-P09XrefBinding ([regex]::Matches($definition.inner,[regex]::Escape($rule[0])).Count -eq 1) 'CAPTURE_NINE_ARTIFACT_EXACT_PORT_REWRITE'
            $original=$definition.inner;$definition.inner=$original.Replace($rule[0],$rule[1])
            Assert-P09XrefBinding ($definition.inner.Replace($rule[1],$rule[0]) -ceq $original) 'CAPTURE_NINE_ARTIFACT_PORT_WHOLE_INVERSE'
        }
        $tokens=$null;$errors=$null
        [void][Management.Automation.Language.Parser]::ParseInput($definition.inner,[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_NINE_ARTIFACT_PORT_PARSE'
        $definition
    }
}

function Initialize-P09XrefCapture009ArtifactGuard {
    Assert-P09XrefBinding ($null -eq (Get-Variable P09XrefCapture009SourcePortFactory -Scope Script -ErrorAction SilentlyContinue)) 'CAPTURE_NINE_ARTIFACT_NO_REINSTALL'
    $definition=Get-P09XrefCapture009ArtifactObservationDefinition
    $actual=Get-Command Observe-P09XrefOwnedArtifact -CommandType Function -ErrorAction Stop
    Assert-P09XrefBinding ($actual.ScriptBlock.Ast.Extent.Text -ceq $definition.original) 'CAPTURE_NINE_ARTIFACT_ORIGINAL_LIVE_FUNCTION'
    . $definition.loader
    $loaded=Get-Command Observe-P09XrefOwnedArtifact -CommandType Function -ErrorAction Stop
    Assert-P09XrefBinding ($loaded.ScriptBlock.Ast.Extent.Text -ceq $definition.changed) 'CAPTURE_NINE_ARTIFACT_LIVE_DIAGNOSTIC_INVERSE'
    Set-Item -Path Function:script:Observe-P09XrefOwnedArtifact -Value $loaded.ScriptBlock
    $script:P09XrefCapture009SourcePortFactory=(Get-Command Get-P09XrefPreassignedPortDefinitions -CommandType Function -ErrorAction Stop).ScriptBlock
    Set-Item -Path Function:script:Get-P09XrefPreassignedPortDefinitions -Value (Get-Command Get-P09XrefCapture009ArtifactPortDefinitions).ScriptBlock
}
