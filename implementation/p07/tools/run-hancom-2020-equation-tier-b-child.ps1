[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$PlanPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedPlanFileSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256Bytes {
    param([Parameter(Mandatory)][AllowEmptyCollection()][byte[]]$Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash($Value) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose() }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    return Get-Sha256Bytes -Value ([Text.Encoding]::UTF8.GetBytes($Value))
}

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ComProperty {
    param([Parameter(Mandatory)]$ComObject, [Parameter(Mandatory)][string]$Name)
    try { return $ComObject.$Name } catch { }
    $property = $ComObject.PSObject.Properties[$Name]
    if ($null -ne $property) { return $property.Value }
    try {
        return [Microsoft.VisualBasic.Interaction]::CallByName(
            $ComObject, $Name, [Microsoft.VisualBasic.CallType]::Get, @()
        )
    }
    catch { }
    return $ComObject.GetType().InvokeMember(
        $Name, [Reflection.BindingFlags]::GetProperty, $null, $ComObject, $null
    )
}

function Set-ComProperty {
    param(
        [Parameter(Mandatory)]$ComObject,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][AllowEmptyString()]$Value
    )
    $property = $ComObject.PSObject.Properties[$Name]
    if ($null -ne $property) { $property.Value = $Value; return }
    try {
        [Microsoft.VisualBasic.Interaction]::CallByName(
            $ComObject, $Name, [Microsoft.VisualBasic.CallType]::Let, @($Value)
        )
        return
    }
    catch { }
    $null = $ComObject.GetType().InvokeMember(
        $Name, [Reflection.BindingFlags]::SetProperty, $null, $ComObject, @($Value)
    )
}

function Resolve-ParameterSetObject {
    param([Parameter(Mandatory)]$Container, [Parameter(Mandatory)][string]$DocumentedId)
    foreach ($candidate in @($DocumentedId, $DocumentedId + 'E', 'H' + $DocumentedId, 'H' + $DocumentedId + 'E')) {
        try {
            $value = Get-ComProperty -ComObject $Container -Name $candidate
            if ($null -ne $value) { return $value }
        }
        catch { }
    }
    throw 'TIER_B_PARAMETER_SET_NOT_RESOLVED'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'TIER_B_OUTPUT_ALREADY_EXISTS' }
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($Value | ConvertTo-Json -Depth 16))
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) }
    finally { $stream.Dispose() }
}

function Assert-Digest {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw 'TIER_B_DIGEST_INVALID' }
}

function Apply-Program {
    param([Parameter(Mandatory)]$ParameterSet, [Parameter(Mandatory)][string]$Script)
    Set-ComProperty $ParameterSet 'String' $Script
    Set-ComProperty $ParameterSet 'BaseUnit' 1000
    Set-ComProperty $ParameterSet 'Color' 0
    Set-ComProperty $ParameterSet 'LineMode' 0
    Set-ComProperty $ParameterSet 'Version' 'Equation Version 60'
    Set-ComProperty $ParameterSet 'ApplyTo' 0
    Set-ComProperty $ParameterSet 'EqFontName' 'HancomEQN'
}

$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
$planFile = (Resolve-Path -LiteralPath $PlanPath).Path
if (-not $planFile.StartsWith($run + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $planFile) -cne 'plan.json' -or
    (Get-Sha256File $planFile) -cne $ExpectedPlanFileSha256) {
    throw 'TIER_B_PLAN_IDENTITY_MISMATCH'
}
$planBytes = [IO.File]::ReadAllBytes($planFile)
if ($planBytes.Length -le 0 -or $planBytes.Length -gt 4194304) { throw 'TIER_B_PLAN_LIMIT' }
$plan = [Text.Encoding]::UTF8.GetString($planBytes) | ConvertFrom-Json
if ([string]$plan.schema_version -cne 'hwpx-agent.p07-08-tier-b-target-plan/v1' -or
    [string]$plan.profile_version -cne 'hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1' -or
    @($plan.cases).Count -ne 14 -or [string]$plan.plan_sha256 -cnotmatch '^[0-9a-f]{64}$') {
    throw 'TIER_B_PLAN_CONTRACT_MISMATCH'
}
for ($index = 0; $index -lt 14; $index += 1) {
    $case = @($plan.cases)[$index]
    if ([string]$case.id -cne ('b-{0:d3}' -f ($index + 1)) -or [int]$case.ordinal -ne $index -or
        [Text.Encoding]::UTF8.GetByteCount([string]$case.script) -gt 1048576 -or
        (Get-Sha256String ([string]$case.script)) -cne [string]$case.script_sha256) {
        throw 'TIER_B_CASE_IDENTITY_MISMATCH'
    }
    Assert-Digest ([string]$case.semantic_sha256)
}
if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'TIER_B_CLIENT_NOT_STA'
}

$tracePath = Join-Path $run 'child-trace.json'
if (Test-Path -LiteralPath $tracePath) { throw 'TIER_B_OUTPUT_ALREADY_EXISTS' }
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p07-08-tier-b-target-child-trace/v1'
    plan_sha256 = [string]$plan.plan_sha256
    state = 'effect_unknown'
    exact_build = '11.0.0.9136'
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    case_results = New-Object Collections.ArrayList
    failed_case = $null; failed_phase = $null; error_code = $null
    quit_invoked = $false; user_document_opened = $false
    external_network_invoked = $false; registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}
$hwp = $null; $documents = $null; $document = $null
$parameters = $null; $parameterSet = $null; $parameterHSet = $null
$activeCase = $null; $phase = 'initialization'; $current = $null
try {
    $phase = 'com_create'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne '11.0.0.9136') { throw 'TIER_B_VERSION_MISMATCH' }
    $documents = $hwp.XHwpDocuments
    $parameters = $hwp.HParameterSet
    $parameterSet = Resolve-ParameterSetObject $parameters 'EqEdit'
    $parameterHSet = Get-ComProperty $parameterSet 'HSet'
    Write-Output 'P07_TIER_B_ACCESS_APPROVAL_MAY_BE_REQUIRED'

    foreach ($case in @($plan.cases)) {
        $activeCase = [string]$case.id
        $current = [ordered]@{
            id = $activeCase; state = 'effect_unknown'; failed_phase = $null
            insert_readback_sha256 = $null; reopen_readback_sha256 = $null
            artifact_sha256 = $null; save = 'not_run'; close = 'not_run'
            reopen = 'not_run'; reopen_readback = 'not_run'; reopen_close = 'not_run'
        }
        [void]$trace.case_results.Add($current)
        $outputPath = Join-Path $run ($activeCase + '.hwpx')
        if (Test-Path -LiteralPath $outputPath) { throw 'TIER_B_OUTPUT_ALREADY_EXISTS' }

        $phase = 'document_add'
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'TIER_B_DOCUMENT_ADD_FAILED' }
        [void]$document.SetActive_XHwpDocument()

        $phase = 'insert_default'
        if ($hwp.HAction.GetDefault('EquationCreate', $parameterHSet) -eq $false) {
            throw 'TIER_B_INSERT_DEFAULT_FAILED'
        }
        Apply-Program $parameterSet ([string]$case.script)
        $phase = 'insert_execute'
        if ($hwp.HAction.Execute('EquationCreate', $parameterHSet) -eq $false) {
            throw 'TIER_B_INSERT_EXECUTE_FAILED'
        }
        $phase = 'select_inserted'
        if ($hwp.HAction.Run('SelectCtrlReverse') -eq $false) { throw 'TIER_B_SELECT_FAILED' }
        $phase = 'insert_readback'
        if ($hwp.HAction.GetDefault('EquationModify', $parameterHSet) -eq $false) {
            throw 'TIER_B_INSERT_READBACK_FAILED'
        }
        $readback = [string](Get-ComProperty $parameterSet 'String')
        $current.insert_readback_sha256 = Get-Sha256String $readback
        if ($readback -cne [string]$case.script) { throw 'TIER_B_INSERT_READBACK_MISMATCH' }

        $phase = 'save'
        if ($document.SaveAs($outputPath, 'HWPX', '') -eq $false -or
            -not (Test-Path -LiteralPath $outputPath -PathType Leaf)) { throw 'TIER_B_SAVE_FAILED' }
        $current.artifact_sha256 = Get-Sha256File $outputPath
        $current.save = 'pass'
        $phase = 'close'
        [void]$document.Close($false); Clear-ComObject $document; $document = $null
        $current.close = 'pass'

        $phase = 'reopen'
        $document = $documents.Add($false)
        if ($null -eq $document -or $document.Open($outputPath, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'TIER_B_REOPEN_FAILED'
        }
        [void]$document.SetActive_XHwpDocument(); $current.reopen = 'pass'
        $phase = 'reopen_select'
        [void]$hwp.HAction.Run('MoveDocEnd')
        if ($hwp.HAction.Run('SelectCtrlReverse') -eq $false) { throw 'TIER_B_REOPEN_SELECT_FAILED' }
        $phase = 'reopen_readback'
        if ($hwp.HAction.GetDefault('EquationModify', $parameterHSet) -eq $false) {
            throw 'TIER_B_REOPEN_READBACK_FAILED'
        }
        $reopenReadback = [string](Get-ComProperty $parameterSet 'String')
        $current.reopen_readback_sha256 = Get-Sha256String $reopenReadback
        if ($reopenReadback -cne [string]$case.script) { throw 'TIER_B_REOPEN_READBACK_MISMATCH' }
        $current.reopen_readback = 'pass'
        $phase = 'reopen_close'
        [void]$document.Close($false); Clear-ComObject $document; $document = $null
        $current.reopen_close = 'pass'; $current.state = 'pass'
    }
    $phase = 'quit'; $hwp.Quit(); $trace.quit_invoked = $true; $trace.state = 'pass'
}
catch {
    $trace.failed_case = $activeCase; $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'TIER_B_CHILD_EXCEPTION' }
    if ($null -ne $current) { $current.failed_phase = $phase; $current.state = 'failed' }
}
finally {
    Clear-ComObject $parameterHSet; Clear-ComObject $parameterSet; Clear-ComObject $parameters
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { }; Clear-ComObject $document }
    Clear-ComObject $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { $hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject $hwp
    [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Write-JsonNoOverwrite $tracePath $trace
if ($trace.state -ne 'pass') { exit 2 }
