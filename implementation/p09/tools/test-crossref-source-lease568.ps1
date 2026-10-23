# Only typed errors and Windows file-sharing models. Never Native/COM/real source writes.
[CmdletBinding()]
param([switch]$ModelsOnly,[switch]$FileSharingOnlyAfter569)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
trap {
    [Console]::Error.WriteLine(('LEASE_MODEL_RUNTIME_{0}_LINE_{1}' -f $_.Exception.GetType().Name,$_.InvocationInfo.ScriptLineNumber))
    exit 1
}
if (-not $ModelsOnly) {throw 'P09_LEASE568_MODELS_ONLY'}
. (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
function Assert-LeaseModel([bool]$Value) {if (-not $Value) {throw 'P09_LEASE568_MODEL_FAILED'}}
function Get-OwnedLeaseFixtureDigest([string]$Path) {
    $held=$null;$algorithm=$null
    try {
        $held=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $algorithm=[Security.Cryptography.SHA256]::Create()
        return ([BitConverter]::ToString($algorithm.ComputeHash($held))).Replace('-','')
    } finally {if ($null -ne $algorithm) {$algorithm.Dispose()};if ($null -ne $held) {$held.Dispose()}}
}
if (-not $FileSharingOnlyAfter569) {
$cases=@{'80070020'='SHARING_VIOLATION';'80070021'='LOCK_VIOLATION';'80070005'='ACCESS_DENIED';'80070002'='FILE_NOT_FOUND';'80070003'='PATH_NOT_FOUND'}
foreach ($entry in $cases.GetEnumerator()) {
    $leaseException=[IO.IOException]::new('PRIVATE-MESSAGE-MUST-NOT-LEAK',[Convert]::ToInt32($entry.Key,16))
    Assert-LeaseModel ((Get-P09XrefSourceReadLeaseFailureCode $leaseException) -ceq ('P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_'+$entry.Value))
}
[Console]::WriteLine('test lease568::five_closed_hresult_categories ... ok')
$wrapped=[Exception]::new('PRIVATE-OUTER',[IO.IOException]::new('PRIVATE-INNER',[Convert]::ToInt32('80070020',16)))
Assert-LeaseModel ((Get-P09XrefSourceReadLeaseFailureCode $wrapped) -ceq 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION')
[Console]::WriteLine('test lease568::wrapped_exception_keeps_closed_inner_category ... ok')
$unknown=[Exception]::new('PRIVATE-UNKNOWN-PATH')
Assert-LeaseModel ((Get-P09XrefSourceReadLeaseFailureCode $unknown) -ceq 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED')
for ($i=0;$i -lt 9;$i++) {$wrapped=[Exception]::new('PRIVATE-DEPTH',$wrapped)}
Assert-LeaseModel ((Get-P09XrefSourceReadLeaseFailureCode $wrapped) -ceq 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED')
[Console]::WriteLine('test lease568::unknown_and_overdeep_errors_fail_closed_without_raw_values ... ok')
}
$path=Join-Path $PSScriptRoot 'fixtures/source-lease-share568.txt'
$before=Get-OwnedLeaseFixtureDigest $path
$writer=$null;$reader=$null;$second=$null
try {
    # No Write/SetLength call: opening an owned fixture with write access alone is sufficient.
    $writer=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::ReadWrite)
    $caught=$false
    try {$reader=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)}
    catch {$caught=$true;Assert-LeaseModel ((Get-P09XrefSourceReadLeaseFailureCode $_.Exception) -ceq 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION')}
    Assert-LeaseModel $caught
    [Console]::WriteLine('test lease568::existing_writer_rejects_read_only_share_even_without_writes ... ok')
} finally {if ($null -ne $reader) {$reader.Dispose()};if ($null -ne $writer) {$writer.Dispose()}}
try {
    $reader=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $second=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    Assert-LeaseModel ($reader.Length -eq $second.Length -and $reader.Length -gt 0)
    [Console]::WriteLine('test lease568::two_shared_read_handles_are_compatible ... ok')
} finally {if ($null -ne $second) {$second.Dispose()};if ($null -ne $reader) {$reader.Dispose()}}
Assert-LeaseModel ((Get-OwnedLeaseFixtureDigest $path) -ceq $before)
[Console]::WriteLine('test lease568::owned_fixture_bytes_unchanged_and_all_handles_disposed ... ok')
