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
    throw 'LAYOUT_PARAMETER_SET_NOT_RESOLVED'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Write-JsonNoOverwrite {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    if (Test-Path -LiteralPath $Path) { throw 'LAYOUT_OUTPUT_ALREADY_EXISTS' }
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($Value | ConvertTo-Json -Depth 16))
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) }
    finally { $stream.Dispose() }
}

function Assert-Digest {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw 'LAYOUT_DIGEST_INVALID' }
}

function Insert-PlainText {
    param([Parameter(Mandatory)]$Hwp, [Parameter(Mandatory)][string]$Text)
    $parameter = $Hwp.HParameterSet.HInsertText
    $hset = $parameter.HSet
    try {
        if ($Hwp.HAction.GetDefault('InsertText', $hset) -eq $false) {
            throw 'LAYOUT_INLINE_CONTEXT_DEFAULT_FAILED'
        }
        $parameter.Text = $Text
        if ($Hwp.HAction.Execute('InsertText', $hset) -eq $false) {
            throw 'LAYOUT_INLINE_CONTEXT_INSERT_FAILED'
        }
    }
    finally { Clear-ComObject $hset; Clear-ComObject $parameter }
}

function Apply-Program {
    param(
        [Parameter(Mandatory)]$ParameterSet,
        [Parameter(Mandatory)][string]$Script,
        [Parameter(Mandatory)][ValidateSet('inline', 'display')][string]$Layout
    )
    Set-ComProperty $ParameterSet 'String' $Script
    Set-ComProperty $ParameterSet 'BaseUnit' 1000
    Set-ComProperty $ParameterSet 'Color' 0
    Set-ComProperty $ParameterSet 'LineMode' $(if ($Layout -ceq 'inline') { 1 } else { 0 })
    Set-ComProperty $ParameterSet 'Version' 'Equation Version 60'
    Set-ComProperty $ParameterSet 'ApplyTo' 0
    Set-ComProperty $ParameterSet 'EqFontName' 'HancomEQN'
}

function Assert-Pdf {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'LAYOUT_PDF_OUTPUT_MISSING' }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -lt 5 -or $item.Length -gt 33554432) {
        throw 'LAYOUT_PDF_NOT_BOUNDED_REGULAR_FILE'
    }
    $stream = [IO.File]::OpenRead($Path)
    try {
        $signature = [byte[]]::new(5)
        if ($stream.Read($signature, 0, 5) -ne 5 -or
            [Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
            throw 'LAYOUT_PDF_SIGNATURE_MISMATCH'
        }
    }
    finally { $stream.Dispose() }
    return $item.Length
}

$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
$planFile = (Resolve-Path -LiteralPath $PlanPath).Path
if (-not $planFile.StartsWith($run + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $planFile) -cne 'plan.json' -or
    (Get-Sha256File $planFile) -cne $ExpectedPlanFileSha256) {
    throw 'LAYOUT_PLAN_IDENTITY_MISMATCH'
}
$planBytes = [IO.File]::ReadAllBytes($planFile)
if ($planBytes.Length -le 0 -or $planBytes.Length -gt 4194304) { throw 'LAYOUT_PLAN_LIMIT' }
$plan = [Text.Encoding]::UTF8.GetString($planBytes) | ConvertFrom-Json
if ([string]$plan.schema_version -cne 'hwpx-agent.p07-07-equation-layout-target-plan/v1' -or
    [string]$plan.profile_version -cne 'hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1' -or
    @($plan.samples).Count -ne 8 -or [string]$plan.plan_sha256 -cnotmatch '^[0-9a-f]{64}$') {
    throw 'LAYOUT_PLAN_CONTRACT_MISMATCH'
}
for ($index = 0; $index -lt 8; $index += 1) {
    $sample = @($plan.samples)[$index]
    $expectedMode = if ($index -lt 4) { 'inline' } else { 'display' }
    $expectedId = $expectedMode + '-' + ('{0:d3}' -f (($index % 4) + 1))
    if ([string]$sample.id -cne $expectedId -or [int]$sample.ordinal -ne $index -or
        [string]$sample.layout -cne $expectedMode -or [int]$sample.base_unit -ne 1000 -or
        [Text.Encoding]::UTF8.GetByteCount([string]$sample.script) -gt 1048576 -or
        (Get-Sha256String ([string]$sample.script)) -cne [string]$sample.script_sha256) {
        throw 'LAYOUT_SAMPLE_IDENTITY_MISMATCH'
    }
    Assert-Digest ([string]$sample.semantic_sha256)
}
if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'LAYOUT_CLIENT_NOT_STA'
}

$tracePath = Join-Path $run 'child-trace.json'
if (Test-Path -LiteralPath $tracePath) { throw 'LAYOUT_OUTPUT_ALREADY_EXISTS' }
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p07-07-equation-layout-target-child-trace/v1'
    plan_sha256 = [string]$plan.plan_sha256
    state = 'effect_unknown'; exact_build = '11.0.0.9136'
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    sample_results = New-Object Collections.ArrayList
    failed_sample = $null; failed_phase = $null; error_code = $null
    quit_invoked = $false; user_document_opened = $false
    external_network_invoked = $false; registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}
$hwp = $null; $documents = $null; $document = $null
$parameters = $null; $parameterSet = $null; $parameterHSet = $null
$activeSample = $null; $phase = 'initialization'; $current = $null
try {
    $phase = 'com_create'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne '11.0.0.9136') { throw 'LAYOUT_VERSION_MISMATCH' }
    $documents = $hwp.XHwpDocuments
    $parameters = $hwp.HParameterSet
    $parameterSet = Resolve-ParameterSetObject $parameters 'EqEdit'
    $parameterHSet = Get-ComProperty $parameterSet 'HSet'
    Write-Output 'P07_LAYOUT_ACCESS_APPROVAL_MAY_BE_REQUIRED'

    foreach ($sample in @($plan.samples)) {
        $activeSample = [string]$sample.id
        $layout = [string]$sample.layout
        $current = [ordered]@{
            id = $activeSample; layout = $layout; state = 'effect_unknown'; failed_phase = $null
            inline_context_sha256 = $null; insert_readback_sha256 = $null
            reopen_readback_sha256 = $null; artifact_sha256 = $null
            pdf_sha256 = $null; pdf_bytes = $null; pdf_signature_valid = $false
            save = 'not_run'; close = 'not_run'; reopen = 'not_run'
            reopen_readback = 'not_run'; pdf_export = 'not_run'; reopen_close = 'not_run'
        }
        [void]$trace.sample_results.Add($current)
        $outputPath = Join-Path $run ($activeSample + '.hwpx')
        $pdfPath = Join-Path $run ($activeSample + '.pdf')
        if ((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $pdfPath)) {
            throw 'LAYOUT_OUTPUT_ALREADY_EXISTS'
        }

        $phase = 'document_add'
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'LAYOUT_DOCUMENT_ADD_FAILED' }
        [void]$document.SetActive_XHwpDocument()
        if ($layout -ceq 'inline') {
            $phase = 'inline_context'
            Insert-PlainText $hwp 'I'
            $current.inline_context_sha256 = Get-Sha256String 'I'
        }
        $phase = 'insert_default'
        if ($hwp.HAction.GetDefault('EquationCreate', $parameterHSet) -eq $false) {
            throw 'LAYOUT_INSERT_DEFAULT_FAILED'
        }
        Apply-Program $parameterSet ([string]$sample.script) $layout
        $phase = 'insert_execute'
        if ($hwp.HAction.Execute('EquationCreate', $parameterHSet) -eq $false) {
            throw 'LAYOUT_INSERT_EXECUTE_FAILED'
        }
        $phase = 'select_inserted'
        if ($hwp.HAction.Run('SelectCtrlReverse') -eq $false) { throw 'LAYOUT_SELECT_FAILED' }
        $phase = 'insert_readback'
        if ($hwp.HAction.GetDefault('EquationModify', $parameterHSet) -eq $false) {
            throw 'LAYOUT_INSERT_READBACK_FAILED'
        }
        $readback = [string](Get-ComProperty $parameterSet 'String')
        $current.insert_readback_sha256 = Get-Sha256String $readback
        if ($readback -cne [string]$sample.script) { throw 'LAYOUT_INSERT_READBACK_MISMATCH' }

        $phase = 'save'
        if ($document.SaveAs($outputPath, 'HWPX', '') -eq $false -or
            -not (Test-Path -LiteralPath $outputPath -PathType Leaf)) { throw 'LAYOUT_SAVE_FAILED' }
        $current.artifact_sha256 = Get-Sha256File $outputPath; $current.save = 'pass'
        $phase = 'close'
        [void]$document.Close($false); Clear-ComObject $document; $document = $null
        $current.close = 'pass'

        $phase = 'reopen'
        $document = $documents.Add($false)
        if ($null -eq $document -or $document.Open($outputPath, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'LAYOUT_REOPEN_FAILED'
        }
        [void]$document.SetActive_XHwpDocument(); $current.reopen = 'pass'
        $phase = 'reopen_select'
        [void]$hwp.HAction.Run('MoveDocEnd')
        if ($hwp.HAction.Run('SelectCtrlReverse') -eq $false) { throw 'LAYOUT_REOPEN_SELECT_FAILED' }
        $phase = 'reopen_readback'
        if ($hwp.HAction.GetDefault('EquationModify', $parameterHSet) -eq $false) {
            throw 'LAYOUT_REOPEN_READBACK_FAILED'
        }
        $reopenReadback = [string](Get-ComProperty $parameterSet 'String')
        $current.reopen_readback_sha256 = Get-Sha256String $reopenReadback
        if ($reopenReadback -cne [string]$sample.script) { throw 'LAYOUT_REOPEN_READBACK_MISMATCH' }
        $current.reopen_readback = 'pass'

        $phase = 'pdf_export'
        [void]$document.SaveAs($pdfPath, 'PDF', '')
        $current.pdf_bytes = Assert-Pdf $pdfPath
        $current.pdf_sha256 = Get-Sha256File $pdfPath
        $current.pdf_signature_valid = $true; $current.pdf_export = 'pass'
        $phase = 'reopen_close'
        [void]$document.Close($false); Clear-ComObject $document; $document = $null
        $current.reopen_close = 'pass'; $current.state = 'pass'
    }
    $phase = 'quit'; $hwp.Quit(); $trace.quit_invoked = $true; $trace.state = 'pass'
}
catch {
    $trace.failed_sample = $activeSample; $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'LAYOUT_CHILD_EXCEPTION' }
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
