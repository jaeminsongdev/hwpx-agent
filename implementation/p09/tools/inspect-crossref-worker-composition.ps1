# Preparation worker composition only. Native dispatch/authority is not implemented.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedCompositionSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedProbeSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedBindingSha256,
    [switch]$InspectOnly,
    [switch]$ExecuteNative
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$pins=[Collections.Generic.List[object]]::new();$children=[Collections.Generic.List[object]]::new()

function Assert-P09XrefWorker([bool]$Condition,[string]$Code) {
    if (-not $Condition) {throw ('P09_XREF_WORKER_'+$Code)}
}
function Get-P09XrefWorkerDigest([byte[]]$Bytes) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
    finally {$sha.Dispose()}
}
function Read-P09XrefWorkerPin([string]$Path,[long]$Maximum,[string]$Expected) {
    $item=Get-Item -LiteralPath $Path -Force
    Assert-P09XrefWorker ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le $Maximum) 'FILE_BOUNDARY'
    $ancestor=$item
    while ($null -ne $ancestor) {
        Assert-P09XrefWorker (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'LINKED_PATH'
        if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
    }
    Start-Sleep -Milliseconds 50
    $stream=[IO.File]::Open($item.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $memory=[IO.MemoryStream]::new();$watch=[Diagnostics.Stopwatch]::StartNew();$buffer=[byte[]]::new(65536)
    try {
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -ne 0) {
            Assert-P09XrefWorker (($memory.Length+$n) -le $Maximum) 'READ_LIMIT'
            $memory.Write($buffer,0,$n)
            $delay=[int][Math]::Ceiling(($memory.Length/1048576.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        $bytes=$memory.ToArray();$actual=Get-P09XrefWorkerDigest $bytes
        Assert-P09XrefWorker ($bytes.Length -eq $item.Length -and $actual -ceq $Expected) 'FILE_IDENTITY'
        [void]$pins.Add([ordered]@{path=$item.FullName;bytes=$bytes.Length;sha256=$actual})
        return ,$bytes
    } finally {$stream.Dispose();$memory.Dispose();$watch.Stop()}
}

function Invoke-P09XrefPreparationChild {
    param([ValidateSet('installation_prefix','source_probe_baseline')][string]$Kind)
    # This deadline applies only to two fixed no-native preparation commands.
    # It must never be reused for a native access-permission prompt.
    if ($Kind -ceq 'installation_prefix') {
        $file=Join-Path ([Environment]::GetFolderPath('Windows')) 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
        $childArguments=@('-NoLogo','-NoProfile','-NonInteractive','-STA','-File',
            (Join-Path $PSScriptRoot 'inspect-crossref-discovery-preflight.ps1'),
            '-ExpectedHarnessSha256','af1f3909f9e77b7ea1484b9cdd97452e38f617f414d64c12b0a72a88838c387d',
            '-ExpectedLibrarySha256','58db2d375de4c17c00fdaa443a5af223c5461b97eb38ee3c8761f1758534f27e')
    } else {
        $file=Join-Path $root 'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
        $childArguments=@('baseline')
    }
    $start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=$file;$start.WorkingDirectory=$root
    $quoted=@(foreach ($argument in $childArguments) {
        Assert-P09XrefWorker ($argument -cnotmatch '["\r\n\x00]') 'FIXED_ARGUMENT_ENCODING'
        '"'+$argument+'"'
    })
    $start.Arguments=$quoted -join ' ';$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process=[Diagnostics.Process]::new();$process.StartInfo=$start;$started=$false
    $out=[IO.MemoryStream]::new();$err=[IO.MemoryStream]::new();$watch=[Diagnostics.Stopwatch]::StartNew()
    $record=[ordered]@{kind=$Kind;child_created=$false;exit_code=$null;stdout_bytes=0;stderr_bytes=0;
        stdout_sha256=$null;stderr_sha256=$null;cleanup_confirmed=$false}
    [void]$children.Add($record)
    try {
        Assert-P09XrefWorker ($process.Start()) 'PREPARATION_CHILD_START'
        $started=$true;$record.child_created=$true
        $readers=@(
            @{stream=$process.StandardOutput.BaseStream;buffer=[byte[]]::new(4096);output=$out;maximum=32768;ended=$false;task=$null},
            @{stream=$process.StandardError.BaseStream;buffer=[byte[]]::new(4096);output=$err;maximum=4096;ended=$false;task=$null})
        foreach ($reader in $readers) {$reader.task=$reader.stream.ReadAsync($reader.buffer,0,$reader.buffer.Length)}
        while ($true) {
            Assert-P09XrefWorker ($watch.Elapsed.TotalSeconds -lt 60) 'PREPARATION_CHILD_DEADLINE'
            foreach ($reader in $readers) {
                if (-not $reader.ended -and $reader.task.IsCompleted) {
                    $n=$reader.task.GetAwaiter().GetResult()
                    if ($n -eq 0) {$reader.ended=$true} else {
                        Assert-P09XrefWorker (($reader.output.Length+$n) -le $reader.maximum) 'PREPARATION_CHILD_OUTPUT_LIMIT'
                        $reader.output.Write($reader.buffer,0,$n)
                        $reader.task=$reader.stream.ReadAsync($reader.buffer,0,$reader.buffer.Length)
                    }
                }
            }
            if ($process.HasExited -and @($readers | Where-Object {-not $_.ended}).Count -eq 0) {break}
            Start-Sleep -Milliseconds 20
        }
        $process.WaitForExit();$record.exit_code=$process.ExitCode
        $stdout=$out.ToArray();$stderr=$err.ToArray()
        $record.stdout_bytes=$stdout.Length;$record.stderr_bytes=$stderr.Length
        $record.stdout_sha256=Get-P09XrefWorkerDigest $stdout;$record.stderr_sha256=Get-P09XrefWorkerDigest $stderr
        Assert-P09XrefWorker ($record.exit_code -eq 0 -and $stderr.Length -eq 0) 'PREPARATION_CHILD_FAILED'
        return ([Text.UTF8Encoding]::new($false,$true).GetString($stdout) | ConvertFrom-Json)
    } finally {
        try {
            if ($started -and -not $process.HasExited) {$process.Kill();Assert-P09XrefWorker ($process.WaitForExit(2000)) 'PREPARATION_CHILD_CLEANUP'}
            $record.cleanup_confirmed=(-not $started -or $process.HasExited)
        } finally {$process.Dispose();$out.Dispose();$err.Dispose();$watch.Stop()}
    }
}

try {
    Assert-P09XrefWorker ([bool]$InspectOnly -ne [bool]$ExecuteNative) 'EXACTLY_ONE_MODE'
    if ($ExecuteNative) {
        # No authority file, approval boolean, alternate command or replay route is accepted.
        [ordered]@{state='native_dispatch_denied_not_implemented_or_authorized';native_execution_authorized=$false;
            native_session_started=$false;native_attempt_created=$false;preparation_children_started=0;p09_complete=$false} | ConvertTo-Json -Compress
        exit 2
    }
    Assert-P09XrefWorker (-not [Environment]::Is64BitProcess -and
        [Threading.Thread]::CurrentThread.GetApartmentState() -eq [Threading.ApartmentState]::STA) 'X86_STA_REQUIRED'
    [void](Read-P09XrefWorkerPin $PSCommandPath 32768 $ExpectedCompositionSha256)
    $owner=Read-P09XrefWorkerPin (Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1') 32768 `
        'bd908d7d8f57513df7992e75f3e7faddaa81ce71d6dc0ad8c0b65963124a6338'
    $binding=Read-P09XrefWorkerPin (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1') 32768 $ExpectedBindingSha256
    [void](Read-P09XrefWorkerPin (Join-Path $PSScriptRoot 'inspect-crossref-discovery-preflight.ps1') 32768 `
        'af1f3909f9e77b7ea1484b9cdd97452e38f617f414d64c12b0a72a88838c387d')
    [void](Read-P09XrefWorkerPin (Join-Path $PSScriptRoot 'crossref-discovery-preflight-library.ps1') 32768 `
        '58db2d375de4c17c00fdaa443a5af223c5461b97eb38ee3c8761f1758534f27e')
    [void](Read-P09XrefWorkerPin (Join-Path $root 'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe') 16777216 $ExpectedProbeSha256)
    # Preserve each definition's real PSScriptRoot. File hashes are checked again
    # at the closing boundary; this is not a race-proof filesystem sandbox.
    . (Join-Path $PSScriptRoot 'sdk-baseline-owned-session.ps1')
    . (Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1')
    Assert-P09XrefOriginalOwnerFunction
    Assert-P09XrefWorker ((Get-Command Observe-P09XrefOwnedActiveSource -CommandType Function).Name -ceq
        'Observe-P09XrefOwnedActiveSource') 'BINDING_IMPORT'
    $prefix=Invoke-P09XrefPreparationChild 'installation_prefix'
    Assert-P09XrefWorker ($prefix.state -ceq 'whole_eight_preflight_pass_no_com_not_native_ready' -and
        $prefix.case_count -eq 8 -and $prefix.x86_sta -eq $true -and $prefix.before_and_after_hwp_count -eq 0 -and
        $prefix.native_execution_authorized -eq $false -and $prefix.native_session_started -eq $false) 'ORIGINAL_PREFIX_RESPONSE'
    $probe=Invoke-P09XrefPreparationChild 'source_probe_baseline'
    Assert-P09XrefWorker ($probe.state -ceq 'source_probe_completed_not_native_attestation' -and
        $probe.candidate_count -eq 8 -and $probe.target_candidate_counts.unique_exact_name_observed -eq 8 -and
        $probe.crossref_fields -eq 0 -and $probe.native_execution_attested -eq $false -and
        $probe.native_execution_authorized -eq $false -and $probe.raw_document_values_or_sdk_commands_present -eq $false) 'PRODUCT_PROBE_RESPONSE'
    $initial=@($pins.ToArray())
    foreach ($pin in $initial) {[void](Read-P09XrefWorkerPin $pin.path $pin.bytes $pin.sha256)}
    Assert-P09XrefWorker (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -eq 0) 'FINAL_HWP_PRESENT'
    Assert-P09XrefWorker (@($children | Where-Object {-not $_.cleanup_confirmed}).Count -eq 0) 'CHILD_NOT_CLEAN'
    [ordered]@{state='whole_eight_worker_composition_inspected_native_dispatch_denied';candidate_count=8;
        x86_sta=$true;original_whole_eight_prefix_pass=$true;product_probe_baseline_pass=$true;
        owned_binding_imported=$true;original_owner_function_identity_checked=$true;actual_owned_com_observed=$false;
        source_pins=$initial;fresh_inputs=$initial.Count;final_fresh_hashes=$initial.Count;children=@($children.ToArray());
        native_execution_authorized=$false;native_ready=$false;native_dispatch_implemented=$false;
        native_session_started=$false;native_attempt_created=$false;accepted_count_delta=0;p09_complete=$false} | ConvertTo-Json -Depth 8 -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_(WORKER|BIND)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_WORKER_INSPECTION_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='worker_composition_rejected';error_code=$code;children=@($children.ToArray());
        native_execution_authorized=$false;native_ready=$false;native_session_started=$false;native_attempt_created=$false;p09_complete=$false} | ConvertTo-Json -Depth 6 -Compress
    exit 2
}
