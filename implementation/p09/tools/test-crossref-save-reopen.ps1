# No real COM/session/save/open operations. Source/model/early-rejection contracts only.
[CmdletBinding()]
param([switch]$RecordContractsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. (Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1')
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'crossref-owned-artifact.ps1')
. (Join-Path $PSScriptRoot 'crossref-save-reopen.ps1')
$script:passed=0;$script:declared=0;$script:filtered=0
function Invoke-P09XrefIoTest([scriptblock]$Body) {
    $script:declared++
    if ($RecordContractsOnly -and $script:declared -le 6) {$script:filtered++;return}
    & $Body;$script:passed++
}
function Assert-P09XrefIoReject([scriptblock]$Body) {
    $rejected=$false;try {& $Body} catch {$rejected=$true}
    Assert-P09XrefBinding $rejected 'TEST_IO_EXPECTED_REJECTION'
}
function New-P09XrefIoIdentity([int]$ProcessId,[string]$Birth) {
    return [pscustomobject]@{process_id=$ProcessId;session_id=[int]1;created_at_utc=$Birth;
        executable_sha256='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce';window_handle_binds_exact_process=$true}
}
try {
    Invoke-P09XrefIoTest {
        for ($i=1;$i -le 8;$i++) {foreach ($stage in @('opened','saved','reopened')) {
            $path=Get-P09XrefCaseArtifactPath $i $stage
            $scope=Get-P09XrefArtifactScope $i ($stage+'_clean') ('a'*64)
            Assert-P09XrefBinding ($path -ceq $scope.path) 'TEST_IO_FIXED_PATH_MATRIX'
        }}
        Assert-P09XrefIoReject {Get-P09XrefCaseArtifactPath 0 'saved'}
        Assert-P09XrefIoReject {Get-P09XrefCaseArtifactPath 9 'saved'}
        Assert-P09XrefIoReject {Get-P09XrefCaseArtifactPath 1 '../saved'}
    }
    Invoke-P09XrefIoTest {
        Assert-P09XrefOriginalIoFunctions
        $original=(Get-Command Open-P58Document -CommandType Function).ScriptBlock
        try {
            Set-Item -Path Function:Open-P58Document -Value {return $null}
            Assert-P09XrefIoReject {Assert-P09XrefOriginalIoFunctions}
        } finally {Set-Item -Path Function:Open-P58Document -Value $original}
        Assert-P09XrefOriginalIoFunctions
    }
    Invoke-P09XrefIoTest {
        $old=New-P09XrefIoIdentity 100 '2026-10-17T00:00:00.0000000Z'
        $fresh=New-P09XrefIoIdentity 200 '2026-10-17T00:00:01.0000000Z'
        Assert-P09XrefFreshSessionIdentity $old $fresh
        $reusedPid=New-P09XrefIoIdentity 100 '2026-10-17T00:00:01.0000000Z'
        Assert-P09XrefFreshSessionIdentity $old $reusedPid
        Assert-P09XrefIoReject {Assert-P09XrefFreshSessionIdentity $old $old}
        $wrong=New-P09XrefIoIdentity 200 '2026-10-17T00:00:01.0000000Z';$wrong.session_id=2
        Assert-P09XrefIoReject {Assert-P09XrefFreshSessionIdentity $old $wrong}
        $wrong=New-P09XrefIoIdentity 200 '2026-10-17T00:00:01.0000000';
        Assert-P09XrefIoReject {Assert-P09XrefFreshSessionIdentity $old $wrong}
        $wrong=New-P09XrefIoIdentity 200 '2026-10-17T00:00:01.0000000Z';$wrong.window_handle_binds_exact_process=$false
        Assert-P09XrefIoReject {Assert-P09XrefFreshSessionIdentity $old $wrong}
    }
    Invoke-P09XrefIoTest {
        $owner=[pscustomobject]@{hwp=[object]::new();documents=[object]::new()};$document=[object]::new()
        $record=[ordered]@{}
        Assert-P09XrefIoReject {Save-P09XrefOpenedArtifact $owner $document 1 $record}
        Assert-P09XrefBinding (-not $record.save_invoked -and -not $record.effect_unknown -and
            $record.error_code -ceq 'P09_XREF_BIND_IO_REAL_OWNER_REQUIRED') 'TEST_OPENED_NO_NATIVE_FALLBACK'
        $record=[ordered]@{}
        Assert-P09XrefIoReject {Save-P09XrefPostInsertArtifact $owner $document 1 ('a'*64) $record}
        Assert-P09XrefBinding (-not $record.save_invoked -and -not $record.effect_unknown) 'TEST_SAVED_NO_NATIVE_FALLBACK'
        $record=[ordered]@{}
        Assert-P09XrefIoReject {Open-P09XrefSavedInFreshSession $owner ([pscustomobject]@{}) 1 ('a'*64) $record}
        Assert-P09XrefBinding (-not $record.open_invoked -and -not $record.effect_unknown) 'TEST_REOPEN_NO_NATIVE_FALLBACK'
        $record=[ordered]@{}
        Assert-P09XrefIoReject {Save-P09XrefReopenedArtifact $owner $document 1 ('a'*64) $record}
        Assert-P09XrefBinding (-not $record.save_invoked -and -not $record.effect_unknown) 'TEST_REOPENED_NO_NATIVE_FALLBACK'
    }
    Invoke-P09XrefIoTest {
        $path=Join-Path ([IO.Path]::GetTempPath()) ('p09-xref-io-'+[Guid]::NewGuid().ToString('N')+'.bin')
        $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try {$bytes=[Text.Encoding]::UTF8.GetBytes('retained');$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
        try {
            Assert-P09XrefIoReject {Assert-P09XrefExclusiveDestination $path}
            Assert-P09XrefBinding ([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($path)) -ceq 'retained') 'TEST_EXISTING_ARTIFACT_PRESERVED'
        } finally {[IO.File]::Delete($path)} # Only this exclusive eight-byte test fixture.
    }
    Invoke-P09XrefIoTest {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-save-reopen.ps1'),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0 -and
            $ast.Extent.Text -cnotmatch '(?i)New-Object|-ComObject|GetActiveObject|\.Kill\(|New-P58Owner\s') 'TEST_IO_NO_ACTIVATION_OR_FORCE_KILL'
        $functions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
        $opened=@($functions | Where-Object {$_.Name -ceq 'Save-P09XrefOpenedArtifact'})[0].Extent.Text
        Assert-P09XrefBinding ($opened.Contains(".SaveAs(`$path,'HWPX','')") -and
            $opened.IndexOf('$Record.save_invoked=$true',[StringComparison]::Ordinal) -lt
            $opened.IndexOf('.SaveAs(',[StringComparison]::Ordinal)) 'TEST_OPENED_INTENT_AND_SCOPE'
        $saved=@($functions | Where-Object {$_.Name -ceq 'Save-P09XrefPostInsertArtifact'})[0].Extent.Text
        $reopened=@($functions | Where-Object {$_.Name -ceq 'Save-P09XrefReopenedArtifact'})[0].Extent.Text
        Assert-P09XrefBinding ($saved.Contains("Save-P58Artifact `$Owner `$Document 'saved.hwpx' 'HWPX'") -and
            $reopened.Contains("Save-P58Artifact `$Owner `$Document 'reopened.hwpx' 'HWPX'")) 'TEST_UNCHANGED_P58_SAVE_ADAPTERS'
        $open=@($functions | Where-Object {$_.Name -ceq 'Open-P09XrefSavedInFreshSession'})[0].Extent.Text
        Assert-P09XrefBinding ($open.Contains('Assert-P09XrefFreshSessionIdentity') -and
            $open.Contains('Open-P58Document $Owner $scope.path $SavedSha256') -and
            $open.Contains('if (-not $handedOff -and $null -ne $document) {Release-P58Com $document}')) 'TEST_FRESH_OPEN_AND_FAILURE_HANDOFF'
    }
    Invoke-P09XrefIoTest {
        foreach ($operation in @('save','open')) {
            $record=[ordered]@{}
            Set-P09XrefIndirectIoRecord $record $operation 'enter'
            Assert-P09XrefBinding ($null -eq $record[$operation+'_invoked'] -and $record.effect_unknown -and
                $record.helper_invocation_started -and -not $record.helper_returned) 'TEST_INDIRECT_CALL_REMAINS_UNKNOWN'
            # A helper throw before returning leaves this state intact, not native-called True.
            Set-P09XrefIndirectIoRecord $record $operation 'returned'
            Assert-P09XrefBinding ($record[$operation+'_invoked'] -eq $true -and $record.helper_returned -and
                $record.effect_unknown) 'TEST_NORMAL_RETURN_NOT_SEMANTIC_ACCEPTANCE'
            Assert-P09XrefIoReject {Set-P09XrefIndirectIoRecord ([ordered]@{}) $operation 'returned'}
            Assert-P09XrefIoReject {Set-P09XrefIndirectIoRecord $record $operation 'returned'}
        }
    }
    Invoke-P09XrefIoTest {
        $tokens=$null;$errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'crossref-save-reopen.ps1'),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'TEST_IO_RECORD_PARSE'
        $functions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
        foreach ($pair in @(@('Save-P09XrefPostInsertArtifact','save','Save-P58Artifact'),
                @('Open-P09XrefSavedInFreshSession','open','Open-P58Document'),
                @('Save-P09XrefReopenedArtifact','save','Save-P58Artifact'))) {
            $text=@($functions | Where-Object {$_.Name -ceq $pair[0]})[0].Extent.Text
            $before=$text.IndexOf(("Set-P09XrefIndirectIoRecord `$Record '"+$pair[1]+"' 'enter'"),[StringComparison]::Ordinal)
            $call=$text.IndexOf(($pair[2]+' $Owner'),[StringComparison]::Ordinal)
            $after=$text.IndexOf(("Set-P09XrefIndirectIoRecord `$Record '"+$pair[1]+"' 'returned'"),[StringComparison]::Ordinal)
            Assert-P09XrefBinding ($before -ge 0 -and $before -lt $call -and $call -lt $after) 'TEST_INDIRECT_CALL_RECORD_BOUNDARIES'
        }
    }
    $expected=if ($RecordContractsOnly) {2} else {8}
    Assert-P09XrefBinding ($script:passed -eq $expected -and $script:declared -eq 8 -and
        $script:filtered -eq (8-$expected)) 'TEST_EXACT_IO_CONTRACTS'
    $state=if ($RecordContractsOnly) {'two_io_record_contracts_pass_native_not_run'} else {'eight_save_reopen_source_model_contracts_pass_native_not_run'}
    [ordered]@{state=$state;passed=$script:passed;failed=0;filtered=$script:filtered;declared=$script:declared;
        actual_native_open_or_save_invoked=$false;native_session_started=$false;native_producer_qualified=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_IO_TEST_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='save_reopen_contract_failed';passed=$script:passed;failed=1;error_code=$code;
        actual_native_open_or_save_invoked=$false;native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
