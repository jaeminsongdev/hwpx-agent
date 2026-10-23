# Fixed005 process-local path/binary successor only. No launcher or execution permit.
Set-StrictMode -Version Latest

function Get-P09XrefCapture005Definitions {
    $pins=@{
        'crossref-save-reopen.ps1'='32fd8f28c3ab89287c22f7937933df2c800c43f5aba7fbf0540eb5f0b6610c81';
        'crossref-owned-artifact.ps1'='d4c3aa70f4b251fbe34e0ef5d0e9093bfb6ff2daa5702316021888b811ac58af';
        'crossref-canonical-runtime.ps1'='a44f94012ec91dab34d5481dd760172e88191cc42a1ef7920633cde9dfc004bc';
        'crossref-stage-probe.ps1'='5992d9510dfb3a1be4aee2db4eb41e4003d667148aa1f8155cccfc5976e5dae4';
        'crossref-fixed-batch.ps1'='b55c2020063773bb7536a211dcb247186f89d667ede26b4a894238f2471f7fff';
        'crossref-preassigned-controller.ps1'='3f676f6fd8b8cc0e37ad8916e476069b317e5110c2352966848caed3970589da'}
    $rules=[ordered]@{
        'Get-P09XrefCaseArtifactPath'=@('crossref-save-reopen.ps1','path');
        'Get-P09XrefArtifactScope'=@('crossref-owned-artifact.ps1','path');
        'Get-P09XrefCanonicalEvidenceRelativePath'=@('crossref-canonical-runtime.ps1','path');
        'New-P09XrefProbeLease'=@('crossref-stage-probe.ps1','lease');
        'Invoke-P09XrefStageProbe'=@('crossref-stage-probe.ps1','probe');
        'Invoke-P09XrefFixedHostBatch'=@('crossref-fixed-batch.ps1','hash');
        'Invoke-P09XrefPreassignedFixedHostBatch'=@('crossref-preassigned-controller.ps1','hash')}
    $trees=@{}
    foreach ($file in $pins.Keys) {
        $item=Get-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Force
        Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -gt 0 -and $item.Length -le 32768) 'CAPTURE_FIVE_SOURCE_SIZE'
        $ancestor=$item
        while ($null -ne $ancestor) {
            Assert-P09XrefBinding (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'CAPTURE_FIVE_SOURCE_LINK'
            if ($ancestor -is [IO.FileInfo]) {$ancestor=$ancestor.Directory} else {$ancestor=$ancestor.Parent}
        }
        Start-Sleep -Milliseconds 50
        $bytes=[IO.File]::ReadAllBytes($item.FullName)
        Assert-P09XrefBinding ((Get-P09XrefFreshDigest $bytes) -ceq $pins[$file]) 'CAPTURE_FIVE_SOURCE_IDENTITY'
        $tokens=$null;$errors=$null
        $trees[$file]=[Management.Automation.Language.Parser]::ParseInput([Text.UTF8Encoding]::new($false,$true).GetString($bytes),[ref]$tokens,[ref]$errors)
        Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_FIVE_SOURCE_PARSE'
    }
    foreach ($name in $rules.Keys) {
        $rule=$rules[$name];$nodes=@($trees[$rule[0]].FindAll({param($node)
            $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$false))
        Assert-P09XrefBinding ($nodes.Count -eq 1) 'CAPTURE_FIVE_FUNCTION_INVENTORY'
        $original=$nodes[0].Extent.Text;$changed=$original;$replacements=[Collections.Generic.List[object]]::new()
        if ($rule[1] -ceq 'path') {
            [void]$replacements.Add(@('p09-361-crossref-bookmark-native-20261017-r01-c','p09-361-crossref-bookmark-native-20261022-g005-c',1))
        } else {
            if ($rule[1] -cin @('lease','probe')) {
                [void]$replacements.Add(@('target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe','target/debug/examples/p09_crossref_capture005_probe.exe',1))
            }
            if ($rule[1] -ceq 'lease') {[void]$replacements.Add(@('5112832','5150720',3))}
            [void]$replacements.Add(@('0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb','9c07898c40bb95ce1ed60b42d10481152bda8aaf7bb68e9c453fffef736756d9',1))
        }
        foreach ($replacement in $replacements) {
            Assert-P09XrefBinding ([regex]::Matches($changed,[regex]::Escape($replacement[0])).Count -eq $replacement[2]) 'CAPTURE_FIVE_EXACT_REWRITE_COUNT'
            $changed=$changed.Replace($replacement[0],$replacement[1])
        }
        $restored=$changed
        for ($i=$replacements.Count-1;$i -ge 0;$i--) {$restored=$restored.Replace($replacements[$i][1],$replacements[$i][0])}
        Assert-P09XrefBinding ($restored -ceq $original) 'CAPTURE_FIVE_WHOLE_FUNCTION_INVERSE'
        # Retain the exact original file context: ScriptBlock.Create(body) loses
        # PSScriptRoot and function-level parameter metadata for these adapters.
        $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($changed,(Join-Path $PSScriptRoot $rule[0]),[ref]$tokens,[ref]$errors)
        $found=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
        Assert-P09XrefBinding (@($errors).Count -eq 0 -and $found.Count -eq 1 -and $found[0].Name -ceq $name) 'CAPTURE_FIVE_SUCCESSOR_PARSE'
        [pscustomobject]@{name=$name;original=$original;changed=$changed;loader=$ast.GetScriptBlock();replacements=$replacements}
    }
}

function Initialize-P09XrefCapture005Namespace {
    Assert-P09XrefBinding ($null -eq (Get-Variable P09XrefCapture005Installed -Scope Script -ErrorAction SilentlyContinue)) 'CAPTURE_FIVE_NO_REINSTALL_OR_MODE_SWITCH'
    $definitions=@(Get-P09XrefCapture005Definitions)
    # Validate the entire current original set before replacing any function.
    foreach ($definition in $definitions) {
        $current=Get-Command $definition.name -CommandType Function -ErrorAction Stop
        Assert-P09XrefBinding ($current.ScriptBlock.Ast -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $current.ScriptBlock.Ast.Extent.Text -ceq $definition.original) 'CAPTURE_FIVE_ORIGINAL_LIVE_FUNCTION_REPLACED'
    }
    $script:P09XrefCapture005Installed=$true
    foreach ($definition in $definitions) {
        # Compile in a private local function scope, then install the complete
        # function ScriptBlock, including its trusted filename and parameters.
        . $definition.loader
        $loaded=Get-Command $definition.name -CommandType Function -ErrorAction Stop
        Assert-P09XrefBinding ($loaded.ScriptBlock.Ast.Extent.Text -ceq $definition.changed) 'CAPTURE_FIVE_COMPILED_FUNCTION_IDENTITY'
        Set-Item -Path ('Function:script:'+$definition.name) -Value $loaded.ScriptBlock
    }
}

