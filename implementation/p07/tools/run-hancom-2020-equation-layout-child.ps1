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
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read
    )
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
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
    foreach ($candidate in @(
        $DocumentedId,
        ($DocumentedId + 'E'),
        ('H' + $DocumentedId),
        ('H' + $DocumentedId + 'E')
    )) {
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
    Set-ComProperty $ParameterSet 'LineMode' $(if ($Layout -ceq 'inline') { 0 } else { 1 })
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
    security_module = [ordered]@{
        module_type = 'FilePathCheckDLL'
        registry_value_name = 'FilePathCheckerModuleExample'
        dll_sha256 = '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'
        preflight_state = 'not_run'; register_state = 'not_run'; register_return = $null
        display_register_state = 'not_run'; display_register_return = $null
        readback_register_state = 'not_run'; readback_register_return = $null
    }
    hwp_session_count = 0; create_session_quit_invoked = $false
    sample_results = New-Object Collections.ArrayList
    failed_sample = $null; failed_phase = $null; error_code = $null
    quit_invoked = $false; user_document_opened = $false
    external_network_invoked = $false; registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}
$hwp = $null; $documents = $null; $document = $null; $window = $null
$parameters = $null; $parameterSet = $null; $parameterHSet = $null
$activeSample = $null; $phase = 'initialization'; $current = $null
try {
    $phase = 'com_create'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne '11.0.0.9136') { throw 'LAYOUT_VERSION_MISMATCH' }

    $phase = 'security_module_preflight'
    $securityModuleName = 'FilePathCheckerModuleExample'
    $securityModulePath = Join-Path (
        [Environment]::GetFolderPath('LocalApplicationData')
    ) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
    $securityModuleItem = Get-Item -LiteralPath $securityModulePath -Force
    if ($securityModuleItem.PSIsContainer -or
        ($securityModuleItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $securityModuleItem.Length -ne 217229 -or
        (Get-Sha256File $securityModuleItem.FullName) -cne
            [string]$trace.security_module.dll_sha256) {
        throw 'LAYOUT_SECURITY_MODULE_IDENTITY_MISMATCH'
    }
    $securityModuleRegistryKey = Get-Item -LiteralPath (
        'Registry::HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules'
    )
    try {
        if ([string]$securityModuleRegistryKey.GetValueKind($securityModuleName) -cne 'String' -or
            [string]$securityModuleRegistryKey.GetValue($securityModuleName) -cne
                $securityModuleItem.FullName) {
            throw 'LAYOUT_SECURITY_MODULE_REGISTRY_MISMATCH'
        }
    }
    finally { $securityModuleRegistryKey.Dispose() }
    $trace.security_module.preflight_state = 'pass'

    $phase = 'security_module_register'
    $trace.security_module.register_return = [bool]$hwp.RegisterModule(
        'FilePathCheckDLL', $securityModuleName
    )
    $trace.security_module.register_state = 'call_completed'

    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.hwp_session_count = 1
    Write-Output 'P07_LAYOUT_SECURITY_MODULE_CALL_COMPLETED'

    foreach ($sample in @($plan.samples)) {
        if ([int]$sample.ordinal -eq 4) {
            $phase = 'inline_create_session_quit'
            Clear-ComObject $parameterHSet; $parameterHSet = $null
            Clear-ComObject $parameterSet; $parameterSet = $null
            Clear-ComObject $parameters; $parameters = $null
            Clear-ComObject $document; $document = $null
            $hwp.Quit()
            Clear-ComObject $window; $window = $null
            Clear-ComObject $documents; $documents = $null
            Clear-ComObject $hwp; $hwp = $null
            [GC]::Collect(); [GC]::WaitForPendingFinalizers()

            $phase = 'display_create_com_create'
            $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
            $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
            if ($version -cne '11.0.0.9136') { throw 'LAYOUT_DISPLAY_VERSION_MISMATCH' }
            $trace.security_module.display_register_return = [bool]$hwp.RegisterModule(
                'FilePathCheckDLL', $securityModuleName
            )
            $trace.security_module.display_register_state = 'call_completed'
            $documents = $hwp.XHwpDocuments
            $window = $hwp.XHwpWindows.Item(0)
            $window.Visible = $true
            $trace.hwp_session_count = 2
            Write-Output 'P07_LAYOUT_DISPLAY_CREATE_SESSION_STARTED'
        }
        $activeSample = [string]$sample.id
        $layout = [string]$sample.layout
        $current = [ordered]@{
            id = $activeSample; layout = $layout; state = 'effect_unknown'; failed_phase = $null
            inline_context_sha256 = $null; insert_readback_sha256 = $null
            reopen_readback_sha256 = $null; artifact_sha256 = $null
            pdf_sha256 = $null; pdf_bytes = $null; pdf_signature_valid = $false
            save = 'not_run'; close = 'not_run'; reopen = 'not_run'
            reopen_readback = 'not_run'; pdf_export = 'not_run'; reopen_close = 'not_run'
            reopen_document_count_before = $null; reopen_document_count_after = $null
        }
        [void]$trace.sample_results.Add($current)
        $outputPath = Join-Path $run ($activeSample + '.hwpx')
        $pdfPath = Join-Path $run ($activeSample + '.pdf')
        if ((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $pdfPath)) {
            throw 'LAYOUT_OUTPUT_ALREADY_EXISTS'
        }

        $phase = 'document_add'
        if ([int]$documents.Count -eq 0) { $document = $documents.Add($false) }
        elseif ([int]$documents.Count -eq 1) { $document = $documents.Item(0) }
        else { throw 'LAYOUT_DOCUMENT_COUNT_INVALID' }
        if ($null -eq $document) { throw 'LAYOUT_DOCUMENT_ADD_FAILED' }
        [void]$document.SetActive_XHwpDocument()
        if ($null -eq $parameterSet) {
            $parameters = $hwp.HParameterSet
            $parameterSet = Resolve-ParameterSetObject $parameters 'EqEdit'
            $parameterHSet = Get-ComProperty $parameterSet 'HSet'
        }
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
        Write-Output ("P07_LAYOUT_PHASE {0} {1}" -f $activeSample, $phase)
        [void]$hwp.Clear(1)
        [void]$document.Close($false)
        Clear-ComObject $document
        $remainingDocumentCount = [int]$documents.Count
        if ($remainingDocumentCount -gt 1) { throw 'LAYOUT_CLOSE_DOCUMENT_COUNT_INVALID' }
        if ($remainingDocumentCount -eq 1) {
            $document = $documents.Item(0)
            if ($null -eq $document) { throw 'LAYOUT_CLOSE_BLANK_DOCUMENT_MISSING' }
            [void]$document.SetActive_XHwpDocument()
        }
        $current.close = 'pass'; $current.state = 'saved_waiting_readback'
    }

    $phase = 'create_session_quit'
    Clear-ComObject $parameterHSet; $parameterHSet = $null
    Clear-ComObject $parameterSet; $parameterSet = $null
    Clear-ComObject $parameters; $parameters = $null
    Clear-ComObject $document; $document = $null
    $hwp.Quit(); $trace.create_session_quit_invoked = $true
    Clear-ComObject $window; $window = $null
    Clear-ComObject $documents; $documents = $null
    Clear-ComObject $hwp; $hwp = $null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    $trace.hwp_session_count = 2

    $phase = 'readback_com_create'
    $hwp = New-Object -ComObject 'HWPFrame.HwpObject.2'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne '11.0.0.9136') { throw 'LAYOUT_READBACK_VERSION_MISMATCH' }
    $trace.security_module.readback_register_return = [bool]$hwp.RegisterModule(
        'FilePathCheckDLL', $securityModuleName
    )
    $trace.security_module.readback_register_state = 'call_completed'
    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $trace.hwp_session_count = 3
    Write-Output 'P07_LAYOUT_READBACK_SESSION_STARTED'

    if ([int]$documents.Count -eq 0) { $document = $documents.Add($false) }
    elseif ([int]$documents.Count -eq 1) { $document = $documents.Item(0) }
    else { throw 'LAYOUT_READBACK_DOCUMENT_COUNT_INVALID' }
    if ($null -eq $document) { throw 'LAYOUT_READBACK_DOCUMENT_ADD_FAILED' }
    [void]$document.SetActive_XHwpDocument()
    Clear-ComObject $document; $document = $null

    for ($index = 0; $index -lt @($plan.samples).Count; $index += 1) {
        $sample = @($plan.samples)[$index]
        $activeSample = [string]$sample.id
        $current = @($trace.sample_results)[$index]
        $outputPath = Join-Path $run ($activeSample + '.hwpx')
        $pdfPath = Join-Path $run ($activeSample + '.pdf')

        $phase = 'reopen'
        Write-Output ("P07_LAYOUT_PHASE {0} {1}" -f $activeSample, $phase)
        $documentCountBeforeOpen = [int]$documents.Count
        $reopenSucceeded = $hwp.Open($outputPath, 'HWPX', 'lock:false;setcurdir:false') -ne $false
        $documentCountAfterOpen = [int]$documents.Count
        $current.reopen_document_count_before = $documentCountBeforeOpen
        $current.reopen_document_count_after = $documentCountAfterOpen
        if (-not $reopenSucceeded -or $documentCountAfterOpen -lt 1 -or
            $documentCountAfterOpen -lt $documentCountBeforeOpen -or
            $documentCountAfterOpen -gt ($documentCountBeforeOpen + 1)) {
            throw 'LAYOUT_REOPEN_FAILED'
        }
        Clear-ComObject $document
        $document = $documents.Item(([int]$documents.Count) - 1)
        if ($null -eq $document) { throw 'LAYOUT_REOPEN_DOCUMENT_MISSING' }
        [void]$document.SetActive_XHwpDocument(); $current.reopen = 'pass'
        if ($null -eq $parameterSet) {
            $parameters = $hwp.HParameterSet
            $parameterSet = Resolve-ParameterSetObject $parameters 'EqEdit'
            $parameterHSet = Get-ComProperty $parameterSet 'HSet'
        }
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
        $phase = 'readback_session_hold'
        Write-Output ("P07_LAYOUT_PHASE {0} {1}" -f $activeSample, $phase)
        Clear-ComObject $document; $document = $null
        $current.state = 'readback_pass_waiting_session_close'
    }
    $phase = 'quit'; $hwp.Quit(); $trace.quit_invoked = $true
    foreach ($result in @($trace.sample_results)) {
        $result.reopen_close = 'pass'; $result.state = 'pass'
    }
    $trace.state = 'pass'
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
    if ($null -ne $document) {
        if ($null -ne $hwp) { try { [void]$hwp.Clear(1) } catch { } }
        Clear-ComObject $document
    }
    Clear-ComObject $window
    Clear-ComObject $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { $hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject $hwp
    [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Write-JsonNoOverwrite $tracePath $trace
if ($trace.state -ne 'pass') { exit 2 }
