# Models use real Windows read leases but never invoke COM or Native.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_SEVEN_MODELS_ONLY'}
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$current=[Diagnostics.Process]::GetCurrentProcess();$current.ProcessorAffinity=[IntPtr]4;$current.PriorityClass='BelowNormal'
foreach ($name in @('sdk-baseline-owned-session','crossref-owned-active-source','crossref-stage-probe','crossref-native-case-ports','crossref-preassigned-owner','crossref-preassigned-case-ports','crossref-capture007-source-guard')) {
    . (Join-Path $PSScriptRoot ($name+'.ps1'))
}
function Assert-Model007([bool]$Condition) {if (-not $Condition) {throw 'P09_XREF_BIND_CAPTURE_SEVEN_MODEL_FAILED'}}
Import-P09XrefFrozenIoHelpers
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$fixed=Join-Path $root 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx'
$script:model007OpenCalls=0;$script:model007Throw=$false
function New-Model007State {
    return [ordered]@{source=$fixed;source_sha256='64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184';
        owner=$null;document=$null;trace=[ordered]@{operations=[ordered]@{}}}
}
function Open-P58Document($Owner,[string]$Path,[string]$Sha) {
    $script:model007OpenCalls++
    $writer=$null;$reader=$null;$blocked=$false
    try {
        try {$writer=[IO.File]::Open($Path,'Open','ReadWrite','ReadWrite')}
        catch {$blocked=(Get-P09XrefSourceReadLeaseFailureCode $_.Exception).EndsWith('_SHARING_VIOLATION')}
        Assert-Model007 $blocked
        $reader=[IO.File]::Open($Path,'Open','Read','Read');Assert-Model007 ($reader.Length -eq 14425)
    } finally {if ($null -ne $reader) {$reader.Dispose()};if ($null -ne $writer) {$writer.Dispose()}}
    if ($script:model007Throw) {throw 'P58_OPEN_FAILED'}
    return [pscustomobject]@{model_only=$true}
}
$state=New-Model007State
try {
    try {Open-P09XrefCapture007GuardedSource $state} catch {
        $r=$state.trace.operations.capture007_source_guard
        [Console]::Error.WriteLine(('P588_GUARD_DIAGNOSTIC_'+$r.phase+'_'+$r.error_kind+'_'+$r.error_id+'_LINE_'+$r.error_line));throw
    }
    Assert-Model007 ($script:model007OpenCalls -eq 1 -and $state.capture007_source_lease.CanRead -and
        $state.trace.operations.capture007_source_guard.original_open_returned)
    $failed=$false;try {Open-P09XrefCapture007GuardedSource $state} catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_SEVEN_SOURCE_NO_RETRY'}
    Assert-Model007 ($failed -and $script:model007OpenCalls -eq 1)
} finally {Close-P09XrefCapture007SourceGuard $state}
Assert-Model007 ($null -eq $state.capture007_source_lease -and $state.trace.operations.capture007_source_guard.lease_closed)
[Console]::WriteLine('test capture007_guard::lease_precedes_open_blocks_writer_allows_reader_and_no_retry ... ok')
$script:model007Throw=$true;$state=New-Model007State
try {
    $failed=$false;try {Open-P09XrefCapture007GuardedSource $state} catch {$failed=$_.Exception.Message -ceq 'P58_OPEN_FAILED'}
    Assert-Model007 ($failed -and $null -ne $state.capture007_source_lease -and $script:model007OpenCalls -eq 2)
} finally {Close-P09XrefCapture007SourceGuard $state}
Assert-Model007 $state.trace.operations.capture007_source_guard.lease_closed
[Console]::WriteLine('test capture007_guard::failed_open_keeps_guard_until_cleanup_without_replay ... ok')
$state=New-Model007State;$state.source=$root;$failed=$false
try {Open-P09XrefCapture007GuardedSource $state} catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_CAPTURE_SEVEN_SOURCE_FIXED_IDENTITY'}
Assert-Model007 ($failed -and $script:model007OpenCalls -eq 2)
[Console]::WriteLine('test capture007_guard::alternate_source_rejected_before_open ... ok')
$script:P09XrefCapture007OriginalPortFactory={
    [pscustomobject]@{name='Invoke-P09XrefPreassignedCaseStep';inner="param(`$Step,`$State) switch (`$Step) {'source_open' {`$State.document=Open-P58Document `$State.owner `$State.source `$State.source_sha256}}"}
    [pscustomobject]@{name='Complete-P09XrefPreassignedCasePorts';inner='param($State) try {Close-P09XrefPreassignedCaseOwner $State} catch {throw}'}
}
$defs=@(Get-P09XrefCapture007GuardedPortDefinitions)
Assert-Model007 ($defs.Count -eq 2 -and $defs[0].inner.Contains('Open-P09XrefCapture007GuardedSource $State') -and
    $defs[1].inner.Contains('finally {Close-P09XrefCapture007SourceGuard $State}'))
[Console]::WriteLine('test capture007_guard::exact_port_projection_preserves_cleanup_finally ... ok')
$writer=$null;$reader=$null
try {
    $writer=[IO.File]::Open($fixed,'Open','ReadWrite','ReadWrite')
    $state=New-Model007State;$failed=$false
    try {Open-P09XrefCapture007GuardedSource $state}
    catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION'}
    Assert-Model007 ($failed -and $script:model007OpenCalls -eq 2 -and
        $state.trace.operations.capture007_source_guard.phase -ceq 'read_lease_acquisition')
} finally {if ($null -ne $writer) {$writer.Dispose()};Close-P09XrefCapture007SourceGuard $state}
[Console]::WriteLine('test capture007_guard::existing_writer_rejected_before_any_original_open ... ok')
$script:P09XrefCapture007OriginalPortFactory=(Get-Command Get-P09XrefPreassignedPortDefinitions).ScriptBlock
$originalDefs=@(& $script:P09XrefCapture007OriginalPortFactory)
$actualDefs=@(Get-P09XrefCapture007GuardedPortDefinitions)
Assert-Model007 ($actualDefs.Count -eq 4 -and $originalDefs.Count -eq 4)
for ($i=0;$i -lt 4;$i++) {
    Assert-Model007 ($actualDefs[$i].name -ceq $originalDefs[$i].name)
    if ($actualDefs[$i].name -cin @('Close-P09XrefPreassignedCaseOwner','Invoke-P09XrefPreassignedCaseWorkflow')) {
        Assert-Model007 ($actualDefs[$i].inner -ceq $originalDefs[$i].inner)
    }
}
$complete=@($actualDefs | Where-Object name -CEQ 'Complete-P09XrefPreassignedCasePorts')[0]
function Close-P09XrefPreassignedCaseOwner($State) {throw 'P09_XREF_BIND_MODEL_CLEANUP_FAILED'}
$script:model007Throw=$false;$state=New-Model007State
$state['completion_attempted']=$false;$state['slot_created']=$false;$state['trace_written']=$false
try {
    Open-P09XrefCapture007GuardedSource $state
    $failed=$false
    try {& ([scriptblock]::Create($complete.inner)) $state}
    catch {$failed=$_.Exception.Message -ceq 'P09_XREF_BIND_PORTS_COMPLETION_FAILED'}
    Assert-Model007 ($failed -and $null -eq $state.capture007_source_lease -and
        $state.trace.operations.capture007_source_guard.lease_closed -and
        $state.trace.completion.cleanup_error_code -ceq 'P09_XREF_BIND_MODEL_CLEANUP_FAILED')
} finally {Close-P09XrefCapture007SourceGuard $state}
[Console]::WriteLine('test capture007_guard::actual_frozen_port_projection_closes_source_even_on_owned_cleanup_failure ... ok')
