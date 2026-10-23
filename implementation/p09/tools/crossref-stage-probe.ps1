# Fixed readonly source-probe lease/runner. No COM activation or execution authority.
Set-StrictMode -Version Latest

function Get-P09XrefStageRunnerCode([string]$TemplateText) {
    Assert-P09XrefBinding ($TemplateText.Length -gt 0 -and $TemplateText.Length -le 32768) 'PROBE_TEMPLATE_TEXT_LIMIT'
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try {$sha=([BitConverter]::ToString($algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($TemplateText)))).Replace('-','').ToLowerInvariant()}
    finally {$algorithm.Dispose()}
    Assert-P09XrefBinding ($sha -ceq 'b6e6abfb685cd1af58426b17ed73793910747a8dbf2c51a81fab9f4d18e1ba36') 'PROBE_TEMPLATE_TEXT_SHA'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($TemplateText,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'PROBE_TEMPLATE_PARSE'
    $functions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
    $support=@(foreach ($name in @('Assert-P09XrefWorker','Get-P09XrefWorkerDigest')) {
        $found=@($functions | Where-Object {$_.Name -ceq $name})
        Assert-P09XrefBinding ($found.Count -eq 1) 'PROBE_TEMPLATE_SUPPORT'
        $found[0].Extent.Text
    })
    $found=@($functions | Where-Object {$_.Name -ceq 'Invoke-P09XrefPreparationChild'})
    Assert-P09XrefBinding ($found.Count -eq 1) 'PROBE_TEMPLATE_RUNNER'
    $body=$found[0].Extent.Text;$marker='    $start=[Diagnostics.ProcessStartInfo]::new()'
    $at=$body.IndexOf($marker,[StringComparison]::Ordinal)
    Assert-P09XrefBinding ($at -gt 0 -and $body.IndexOf($marker,$at+$marker.Length,[StringComparison]::Ordinal) -lt 0) 'PROBE_TEMPLATE_BOUNDARY'
    $runner="function Invoke-P09XrefStageChild {`n"+
        "    `$Kind='source_stage_'+`$Stage`n"+
        "    `$file=`$Lease.binary`n"+
        "    `$childArguments=@('case',`$CaseIndex.ToString(),`$Stage,`$ExpectedSha256)`n"+$body.Substring($at)
    return [pscustomobject]@{support=$support;runner=$runner;capture_suffix=$body.Substring($at)}
}

function Get-P09XrefFreshDigest([byte[]]$Bytes) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
    finally {$hash.Dispose()}
}

function New-P09XrefProbeLease {
    $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $binary=Join-Path $root 'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
    $template=Join-Path $PSScriptRoot 'inspect-crossref-worker-composition.ps1'
    $stream=$null;$algorithm=$null
    try {
        foreach ($path in @($binary,$template)) {
            $item=Get-Item -LiteralPath $path -Force
            Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and
                $item.Length -le 16777216) 'PROBE_LEASE_FILE'
            $ancestor=$item
            while ($null -ne $ancestor) {
                Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PROBE_LEASE_LINK'
                if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
            }
        }
        $templateItem=Get-Item -LiteralPath $template
        Assert-P09XrefBinding ($templateItem.Length -le 32768) 'PROBE_TEMPLATE_SIZE'
        $raw=[IO.File]::ReadAllBytes($template)
        $algorithm=[Security.Cryptography.SHA256]::Create()
        $templateSha=([BitConverter]::ToString($algorithm.ComputeHash($raw))).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($templateSha -ceq 'b6e6abfb685cd1af58426b17ed73793910747a8dbf2c51a81fab9f4d18e1ba36') 'PROBE_TEMPLATE_SHA'
        $text=[Text.UTF8Encoding]::new($false,$true).GetString($raw)
        $code=Get-P09XrefStageRunnerCode $text
        Start-Sleep -Milliseconds 50
        $stream=[IO.File]::Open($binary,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        Assert-P09XrefBinding ($stream.Length -eq 5112832) 'PROBE_BINARY_SIZE'
        $algorithm.Initialize();$watch=[Diagnostics.Stopwatch]::StartNew();$buffer=[byte[]]::new(65536);$count=0L
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -ne 0) {
            $count+=$n;Assert-P09XrefBinding ($count -le 5112832) 'PROBE_BINARY_READ_LIMIT'
            [void]$algorithm.TransformBlock($buffer,0,$n,$buffer,0)
            $delay=[int][Math]::Ceiling(($count/1048576.0-$watch.Elapsed.TotalSeconds)*1000)
            if ($delay -gt 0) {Start-Sleep -Milliseconds $delay}
        }
        [void]$algorithm.TransformFinalBlock([byte[]]::new(0),0,0);$watch.Stop()
        $sha=([BitConverter]::ToString($algorithm.Hash)).Replace('-','').ToLowerInvariant()
        Assert-P09XrefBinding ($count -eq 5112832 -and $sha -ceq '0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb') 'PROBE_BINARY_SHA'
        $lease=[pscustomobject]@{root=$root;binary=$binary;stream=$stream;binary_sha256=$sha;template_sha256=$templateSha;
            template_text=$text;capture_suffix_sha256=(Get-P09XrefFreshDigest ([Text.Encoding]::UTF8.GetBytes($code.capture_suffix)));closed=$false}
        $stream=$null
        return $lease
    } finally {if ($null -ne $stream) {$stream.Dispose()};if ($null -ne $algorithm) {$algorithm.Dispose()}}
}

function Close-P09XrefProbeLease($Lease) {
    if ($null -ne $Lease -and -not $Lease.closed) {$Lease.stream.Dispose();$Lease.closed=$true}
}

function Invoke-P09XrefStageProbe {
    param([Parameter(Mandatory)]$Lease,[Parameter(Mandatory)][int]$CaseIndex,
        [Parameter(Mandatory)][string]$Stage,[Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Record)
    $Record.children=[Collections.Generic.List[object]]::new();$Record.error_code=$null
    try {
        Assert-P09XrefBinding ($Stage -cin @('opened','saved','reopened')) 'PROBE_STAGE'
        $scope=Get-P09XrefArtifactScope $CaseIndex ($Stage+'_clean') $ExpectedSha256
        $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
        $binary=Join-Path $root 'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
        Assert-P09XrefBinding (-not $Lease.closed -and $Lease.stream -is [IO.FileStream] -and
            $Lease.stream.CanRead -and -not $Lease.stream.CanWrite -and $Lease.root -ceq $root -and
            $Lease.binary -ceq $binary -and $Lease.stream.Name -ceq $binary -and
            $Lease.binary_sha256 -ceq '0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb' -and
            $Lease.template_sha256 -ceq 'b6e6abfb685cd1af58426b17ed73793910747a8dbf2c51a81fab9f4d18e1ba36') 'PROBE_ACTIVE_LEASE'
        # Revalidate immutable template bytes, not caller-supplied executable code strings.
        $code=Get-P09XrefStageRunnerCode $Lease.template_text
        foreach ($definition in $code.support) {. ([scriptblock]::Create($definition))}
        . ([scriptblock]::Create($code.runner))
        $children=$Record.children
        $response=Invoke-P09XrefStageChild
        Assert-P09XrefBinding ($response.schema_version -ceq 'hwpx-agent.private.crossref-worker-source-probe/v1' -and
            $response.state -ceq 'source_probe_completed_not_native_attestation' -and
            $response.observed_output_sha256 -ceq $ExpectedSha256 -and
            $response.selected_case.case_id -ceq $scope.case_id -and $response.selected_case.phase -ceq $Stage -and
            $response.candidate_count -eq 8) 'PROBE_STAGE_RESPONSE'
        foreach ($name in @('native_execution_attested','native_target_resolution_qualified','parameter_key_semantics_qualified',
                'causal_insertion_or_preservation_proved','complete_reference_validation_qualified','native_execution_authorized',
                'raw_document_values_or_sdk_commands_present','p09_complete')) {
            Assert-P09XrefBinding ($response.$name -is [bool] -and -not $response.$name) 'PROBE_FALSE_CLAIM'
        }
        return $response
    } catch {
        $code=if ($_.Exception.Message -cmatch '^P09_XREF_(WORKER|BIND)_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_BIND_STAGE_PROBE_FAILED_NO_RAW_VALUES'}
        $Record.error_code=$code;throw $code
    }
}
