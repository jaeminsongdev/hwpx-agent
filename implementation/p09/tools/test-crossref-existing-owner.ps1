# Compile new adapter/models, then models + current worker's own kernel only.
# Never calls ExistingOwner.Attach, NativeCatalog, ROT, Hancom or a document.
[CmdletBinding()]
param([switch]$ModelsAndSelfOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsAndSelfOnly) {throw 'P09_XREF_ROT_MODELS_AND_SELF_ONLY'}
if ([IntPtr]::Size -ne 4 -or [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') {throw 'P09_XREF_ROT_X86_STA_TEST_REQUIRED'}
$phase='compile'
try {
    Add-Type -Path @((Join-Path $PSScriptRoot 'crossref-existing-owner.cs'),(Join-Path $PSScriptRoot 'test-crossref-existing-owner.cs'))
    $phase='tests';$failed=0
    $names=@('name_family','name_bound','one_exact_owner','no_owner_no_fallback','duplicate_owners','incomplete_enumeration',
        'pid_mismatch','session_mismatch','birth_one_tick_mismatch','image_mismatch','version_mismatch','window_required',
        'window_changed_after_scan','exact_enum_limit','enum_overflow_not_first_match','get_object_missing','catalog_cleanup_failure',
        'invalid_expected_identity','unknown_names_never_get_objects','lease_close_once','stable_kernel_self_not_hancom')
    foreach ($name in $names) {
        try {[P09CrossrefExisting.ExistingOwnerTests]::Run($name);[Console]::WriteLine(('test rot_existing::{0} ... ok' -f $name))}
        catch {$failed++;[Console]::WriteLine(('test rot_existing::{0} ... FAILED' -f $name))
            $code=$_.Exception.GetBaseException().Message
            if ($code -cnotmatch '^P09_XREF_ROT_[A-Z_]{1,120}$') {$code='P09_XREF_ROT_TEST_FAILED_NO_RAW_VALUES'}
            [Console]::Error.WriteLine(('Error: '+$code))}
    }
    if ($failed -gt 0) {exit 2}
    [Console]::WriteLine(('test result: ok. {0} passed; 0 failed; 0 ignored; models_and_self_only_not_ROT_or_Native' -f $names.Count))
} catch {
    $detail=[string]$_.Exception.Message
    if ($null -ne $_.ErrorDetails) {$detail+=[string]$_.ErrorDetails.Message}
    foreach ($match in [regex]::Matches($detail,'\bCS[0-9]{4}\b')) {[Console]::Error.WriteLine(('Error: '+$match.Value))}
    [Console]::Error.WriteLine(('Error: P09_XREF_ROT_'+$phase.ToUpperInvariant()+'_FAILED_NO_RAW_VALUES'));exit 2
}
