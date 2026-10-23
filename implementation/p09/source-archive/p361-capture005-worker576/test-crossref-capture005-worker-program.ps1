# Original program projection and context only. Never invoke its Native branch.
[CmdletBinding()]
param([switch]$ModelsOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
if (-not $ModelsOnly) {throw 'P09_XREF_BIND_CAPTURE_FIVE_PROGRAM_MODELS_ONLY'}
try {
    . (Join-Path $PSScriptRoot 'crossref-capture005-worker-program.ps1')
    $projection=Get-P09XrefCapture005WorkerProgram
    if ($projection.changed.Replace($projection.insertion,'') -cne $projection.original -or
        $projection.original_sha256 -cne '7b10f11316296600d42d4953e223eea2363ed6d930b3c100e1af537454db56cf') {
        throw 'P09_XREF_BIND_CAPTURE_FIVE_MODEL_WHOLE_WORKER_INVERSE'
    }
    [Console]::WriteLine('test capture005_worker::complete_original_release_protocol_result_cleanup_and_eof_body_preserved ... ok')

    if ($projection.program.File -cne $projection.source -or $projection.program.Ast.ParamBlock.Parameters.Count -ne 1 -or
        $projection.program.Ast.ParamBlock.Parameters[0].Name.VariablePath.UserPath -cne 'FixedEightAfterSession') {
        throw 'P09_XREF_BIND_CAPTURE_FIVE_MODEL_PROGRAM_FILE_CONTEXT_AND_ORIGINAL_PARAMETER'
    }
    [Console]::WriteLine('test capture005_worker::trusted_original_filename_and_fixed_mode_parameter_retained ... ok')

    $at=$projection.changed.IndexOf($projection.insertion,[StringComparison]::Ordinal)
    $prewarm=$projection.changed.IndexOf("`$phase='prewarm'",[StringComparison]::Ordinal)
    $lease=$projection.changed.IndexOf('$lease=New-P09XrefProbeLease',[StringComparison]::Ordinal)
    if ($at -lt 0 -or $at -ge $prewarm -or $prewarm -ge $lease -or
        [regex]::Matches($projection.changed,'Initialize-P09XrefCapture005Namespace').Count -ne 1) {
        throw 'P09_XREF_BIND_CAPTURE_FIVE_MODEL_NAMESPACE_BEFORE_PREWARM_AND_LEASE'
    }
    [Console]::WriteLine('test capture005_worker::one_fixed_namespace_install_precedes_original_prewarm_and_probe_lease ... ok')
    [Console]::WriteLine('test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out')
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_BIND_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_CAPTURE_FIVE_PROGRAM_MODEL_FAILED_NO_RAW_VALUES'}
    [Console]::WriteLine('Error: '+$code);exit 1
}

