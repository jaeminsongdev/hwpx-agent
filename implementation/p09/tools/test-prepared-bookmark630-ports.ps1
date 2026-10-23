# Modeled ports only: no Native object, activation, real document or output files.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
if (-not $ModelsOnly) {throw 'MODEL_ONLY_REQUIRED'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
. (Join-Path $PSScriptRoot 'prepared-bookmark630-channel.ps1')
. (Join-Path $PSScriptRoot 'prepared-bookmark630-ports.ps1')
$script:disposed=0;$script:saveCalls=0;$script:hostCalls=0;$script:closeCalls=0;$failures=0;$run=0
function Assert-Model([bool]$Value) {if (-not $Value) {throw 'MODEL_ASSERTION'}}
function Model-Case([scriptblock]$Body) {
    $script:run++
    try {[void](& $Body)} catch {$script:failures++}
}
function Fake-Lease {
    $value=[pscustomobject]@{}
    $value|Add-Member ScriptMethod Dispose {$script:disposed++}
    return $value
}
function Fake-State {
    return [ordered]@{failed=$false;cursor=0;trace=[ordered]@{artifacts=[ordered]@{};input_leases_closed=$false;cleanup_error=$null};
        owner=$null;document=$null;close_attempted=$false;slot_created=$false;leases=[Collections.Generic.List[object]]::new();
        run='D:\MODELED-NOT-AN-OUTPUT-DIRECTORY'}
}
function Invoke-P09XrefPreassignedHostMessage {$script:hostCalls++;throw 'MODEL_NO_HOST_IO'}
function Assert-P09XrefPreassignedOwnerAnchor {}
function Test-P58Owner {return $true}
function Assert-P09XrefExclusiveDestination {}
function Get-P09Prepared630Pin {return [ordered]@{bytes=1;sha256=('0'*64)}}
function Release-P58Com {}
function Close-P09XrefPreassignedOwner($Owner) {$script:closeCalls++;$Owner.preassigned_closed=$true}

Model-Case {
    $state=Fake-State
    try {Invoke-P09Prepared630Step $state 'saved_save';throw 'MODEL_UNEXPECTED_SUCCESS'}
    catch {Assert-Model ($_.Exception.Message -ceq 'P09_XREF_BIND_PREPARED_STEP_NO_RETRY')}
    Assert-Model ($script:hostCalls -eq 0)
}
Model-Case {
    $state=Fake-State
    try {[void](Save-P09Prepared630Artifact $state 'source.hwpx' HWPX);throw 'MODEL_UNEXPECTED_SUCCESS'}
    catch {Assert-Model ($_.Exception.Message -ceq 'P09_XREF_BIND_PREPARED_EXACT_OUTPUT_FORMAT')}
    Assert-Model ($script:saveCalls -eq 0 -and $state.trace.artifacts.Count -eq 0)
}
Model-Case {
    $state=Fake-State;$state.owner=[ordered]@{identity=[ordered]@{model=$true}}
    $document=[pscustomobject]@{}
    $document|Add-Member ScriptMethod SaveAs {param($Path,$Format,$Options) $script:saveCalls++;return $true}
    $state.document=$document
    $pin=Save-P09Prepared630Artifact $state 'saved.hwpx' HWPX
    Assert-Model ($pin.bytes -eq 1 -and $script:saveCalls -eq 1 -and $state.trace.artifacts.Count -eq 1)
    Assert-Model (-not $state.trace.artifacts['saved.hwpx'].effect_semantics_qualified)
}
Model-Case {
    $state=Fake-State;$state.owner=[ordered]@{identity=[ordered]@{model=$true}}
    $document=[pscustomobject]@{}
    $document|Add-Member ScriptMethod SaveAs {return $false}
    $state.document=$document
    try {[void](Save-P09Prepared630Artifact $state 'saved.hwpx' HWPX);throw 'MODEL_UNEXPECTED_SUCCESS'}
    catch {Assert-Model ($_.Exception.Message -ceq 'P09_XREF_BIND_PREPARED_SAVE_FAILED_EFFECT_UNKNOWN')}
    Assert-Model ($state.trace.artifacts.Count -eq 0)
}
Model-Case {
    $state=Fake-State;$state.owner=[ordered]@{preassigned_closed=$false};$state.document=[pscustomobject]@{}
    Close-P09Prepared630Owner $state
    Close-P09Prepared630Owner $state # No owner remains; no Close/Quit repeated.
    Assert-Model ($script:closeCalls -eq 1 -and $null -eq $state.owner -and $state.close_attempted)
}
Model-Case {
    $state=Fake-State;$state.owner=[ordered]@{preassigned_closed=$false};$state.close_attempted=$true
    [void]$state.leases.Add((Fake-Lease));Complete-P09Prepared630Case $state
    Assert-Model ($script:disposed -eq 0 -and $state.leases.Count -eq 1 -and -not $state.trace.input_leases_closed)
    Assert-Model ($script:closeCalls -eq 1)
}
Model-Case {
    $state=Fake-State;[void]$state.leases.Add((Fake-Lease));[void]$state.leases.Add((Fake-Lease))
    Complete-P09Prepared630Case $state
    Assert-Model ($script:disposed -eq 2 -and $state.leases.Count -eq 0 -and $state.trace.input_leases_closed)
    Assert-Model ((Get-P09Prepared630SafeCode ([pscustomobject]@{Exception=[Exception]::new('PRIVATE VALUE')})) -ceq 'P09_XREF_BIND_PREPARED_FAILED_NO_RAW_VALUES')
    $worker=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'run-prepared-bookmark630-worker.ps1'))
    $primary=$worker.IndexOf('$caseFailure=[ordered]@{case_index=$index;phase=$trace.phase;error_code=$errorCode}',[StringComparison]::Ordinal)
    $finish=$worker.IndexOf('[void](Invoke-P09XrefPreassignedHostMessage $channel $index finish -CaseStatus $status)',[StringComparison]::Ordinal)
    Assert-Model ($primary -ge 0 -and $finish -gt $primary)
}
[ordered]@{run=$script:run;errors=0;failures=$script:failures;skipped=0;actual_native_started=$false}|ConvertTo-Json -Compress
if ($script:failures -ne 0) {exit 2}
