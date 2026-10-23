[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_NINE_MODELS_ONLY'}
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-stage-probe','crossref-native-case-ports','crossref-preassigned-owner','crossref-preassigned-case-ports',
    'crossref-capture009-source-guard','crossref-capture009-artifact-guard')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function Assert-ArtifactModel009([bool]$Condition) {if (-not $Condition) {throw 'P09_XREF_BIND_CAPTURE_NINE_ARTIFACT_MODEL_FAILED'}}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$temp=Join-Path $root ('target/p09-artifact009-model-'+[Guid]::NewGuid().ToString('N')+'.bin')
$bytes=[Text.Encoding]::UTF8.GetBytes('owned-temporary-Windows-sharing-model-not-Hancom-evidence')
$hash=[Security.Cryptography.SHA256]::Create()
try {$sha=([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}
function Get-P09XrefArtifactScope($CaseIndex,$Point,$ExpectedSha256) {
    Assert-P09XrefBinding ($CaseIndex -eq 1 -and $Point -ceq 'saved_clean' -and $ExpectedSha256 -cmatch '^[0-9a-f]{64}$') 'ARTIFACT_SELECTOR'
    return [pscustomobject]@{path=$temp;sha256=$ExpectedSha256}
}
function New-ArtifactModel009State {
    return [ordered]@{case_index=1;trace=[ordered]@{artifacts=[ordered]@{saved=[ordered]@{bytes=$bytes.Length;sha256=$sha}};operations=[ordered]@{}}}
}
$reader=$writer=$state=$null
try {
    [IO.File]::WriteAllBytes($temp,$bytes)
    $writer=[IO.File]::Open($temp,'Open','ReadWrite','ReadWrite');$blocked=$false
    try {$reader=[IO.File]::Open($temp,'Open','Read','Read')}
    catch {$blocked=(Get-P09XrefSourceReadLeaseFailureCode $_.Exception).EndsWith('_SHARING_VIOLATION')}
    Assert-ArtifactModel009 ($blocked -and $null -eq $reader)
    $writer.Dispose();$writer=$null
    [Console]::WriteLine('test capture009_artifact::legacy_open_before_restrictive_lease_reproduces_windows_sharing_failure ... ok')

    $state=New-ArtifactModel009State;Open-P09XrefCapture009SavedGuard $state
    Assert-ArtifactModel009 ($state.trace.operations.capture009_saved_guard.digest_verified -and $state.capture009_saved_lease.CanRead)
    $blocked=$false
    try {$writer=[IO.File]::Open($temp,'Open','ReadWrite','ReadWrite')}
    catch {$blocked=(Get-P09XrefSourceReadLeaseFailureCode $_.Exception).EndsWith('_SHARING_VIOLATION')}
    Assert-ArtifactModel009 ($blocked -and $null -eq $writer)
    $reader=[IO.File]::Open($temp,'Open','Read','Read');$reader.Dispose();$reader=$null
    [Console]::WriteLine('test capture009_artifact::guard_precedes_mock_open_denies_writer_and_allows_original_observer_reader ... ok')
    $blocked=$false;try {Open-P09XrefCapture009SavedGuard $state} catch {$blocked=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_NINE_SAVED_NO_RETRY'}
    Assert-ArtifactModel009 $blocked
    [Console]::WriteLine('test capture009_artifact::same_saved_guard_cannot_be_replayed ... ok')
    Close-P09XrefCapture009SavedGuard $state;Close-P09XrefCapture009SavedGuard $state
    Assert-ArtifactModel009 ($null -eq $state.capture009_saved_lease -and $state.trace.operations.capture009_saved_guard.lease_closed)
    [Console]::WriteLine('test capture009_artifact::owned_lease_closes_once_and_cleanup_is_idempotent ... ok')

    $state=New-ArtifactModel009State;$state.trace.artifacts.saved.sha256='0'*64;$blocked=$false
    try {Open-P09XrefCapture009SavedGuard $state} catch {$blocked=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_NINE_SAVED_HELD_DIGEST'}
    Assert-ArtifactModel009 ($blocked -and $state.capture009_saved_lease.CanRead -and -not $state.trace.operations.capture009_saved_guard.digest_verified)
    Close-P09XrefCapture009SavedGuard $state
    [Console]::WriteLine('test capture009_artifact::wrong_digest_denied_and_acquired_lease_retained_until_cleanup ... ok')
    $state=New-ArtifactModel009State;$state.trace.artifacts.saved.bytes=-1;$blocked=$false
    try {Open-P09XrefCapture009SavedGuard $state} catch {$blocked=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_NINE_SAVED_SIZE'}
    Assert-ArtifactModel009 ($blocked -and $null -eq $state.capture009_saved_lease)
    [Console]::WriteLine('test capture009_artifact::invalid_artifact_size_denied_before_acquisition ... ok')

    $definition=Get-P09XrefCapture009ArtifactObservationDefinition
    Assert-ArtifactModel009 ($definition.changed.Replace($definition.after,$definition.before) -ceq $definition.original -and
        $definition.changed.Contains("Replace('SOURCE_READ_LEASE','ARTIFACT_READ_LEASE')"))
    [Console]::WriteLine('test capture009_artifact::observer_changes_only_closed_file_open_error_category ... ok')
    # Load the actual frozen port definitions: no mock body replacing the new hook.
    Import-P09XrefFrozenIoHelpers
    Initialize-P09XrefCapture009SourceGuard
    Initialize-P09XrefCapture009ArtifactGuard
    $defs=@(Get-P09XrefCapture009ArtifactPortDefinitions)
    $invoke=@($defs|Where-Object name -CEQ 'Invoke-P09XrefPreassignedCaseStep')[0].inner
    $complete=@($defs|Where-Object name -CEQ 'Complete-P09XrefPreassignedCasePorts')[0].inner
    Assert-ArtifactModel009 ($invoke.Contains('Open-P09XrefCapture009SavedGuard $State;$State.document=Open-P09XrefSavedInFreshSession') -and
        $complete.Contains('finally {Close-P09XrefCapture009SavedGuard $State}'))
    [Console]::WriteLine('test capture009_artifact::actual_frozen_ports_precede_fresh_open_and_close_saved_guard_in_finally ... ok')

    function Close-P09XrefPreassignedCaseOwner($State) {throw 'P09_XREF_BIND_CAPTURE_NINE_MODEL_OWNER_CLOSE_FAILED'}
    function Close-P09XrefCapture009SourceGuard($State) {throw 'P09_XREF_BIND_CAPTURE_NINE_MODEL_SOURCE_CLOSE_FAILED'}
    # Execute only the exact projected nested cleanup fragment, not COM or case IO.
    $fragment='try {try {Close-P09XrefPreassignedCaseOwner $State} finally {Close-P09XrefCapture009SourceGuard $State}} finally {Close-P09XrefCapture009SavedGuard $State}'
    Assert-ArtifactModel009 ($complete.Contains($fragment))
    $state=New-ArtifactModel009State;Open-P09XrefCapture009SavedGuard $state
    try {& ([scriptblock]::Create($fragment))} catch {}
    Assert-ArtifactModel009 ($null -eq $state.capture009_saved_lease -and $state.trace.operations.capture009_saved_guard.lease_closed)
    [Console]::WriteLine('test capture009_artifact::saved_lease_closes_even_if_both_owner_and_source_cleanup_throw ... ok')
    $blocked=$false;try {Initialize-P09XrefCapture009ArtifactGuard} catch {$blocked=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_NINE_ARTIFACT_NO_REINSTALL'}
    Assert-ArtifactModel009 $blocked
    [Console]::WriteLine('test capture009_artifact::no_reinstall_or_fallback ... ok')
} finally {
    if ($null -ne $reader) {$reader.Dispose()};if ($null -ne $writer) {$writer.Dispose()}
    if ($null -ne $state) {Close-P09XrefCapture009SavedGuard $state}
    Assert-ArtifactModel009 ($temp.StartsWith((Join-Path $root 'target/p09-artifact009-model-'),[StringComparison]::OrdinalIgnoreCase))
    if ([IO.File]::Exists($temp)) {[IO.File]::Delete($temp)}
}
