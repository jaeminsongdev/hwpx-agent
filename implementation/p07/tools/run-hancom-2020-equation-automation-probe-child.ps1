[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$RequestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRequestSha256
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
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function Get-ReturnKind {
    param([AllowNull()]$Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { return $(if ([bool]$Value) { 'true' } else { 'false' }) }
    return 'other'
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
        $Name,
        [Reflection.BindingFlags]::GetProperty,
        $null,
        $ComObject,
        $null
    )
}

function Set-ComProperty {
    param(
        [Parameter(Mandatory)]$ComObject,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][AllowEmptyString()]$Value
    )
    $property = $ComObject.PSObject.Properties[$Name]
    if ($null -ne $property) {
        $property.Value = $Value
        return
    }
    try {
        [Microsoft.VisualBasic.Interaction]::CallByName(
            $ComObject, $Name, [Microsoft.VisualBasic.CallType]::Let, @($Value)
        )
        return
    }
    catch { }
    $null = $ComObject.GetType().InvokeMember(
        $Name,
        [Reflection.BindingFlags]::SetProperty,
        $null,
        $ComObject,
        @($Value)
    )
}

function Resolve-ParameterSetObject {
    param([Parameter(Mandatory)]$Container, [Parameter(Mandatory)][string]$DocumentedId)
    if ($DocumentedId -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,127}$') {
        throw 'EQUATION_PARAMETER_SET_ID_SHAPE_INVALID'
    }
    $candidates = @(
        [pscustomobject]@{ name = $DocumentedId; strategy = 'documented_exact' },
        [pscustomobject]@{ name = $DocumentedId + 'E'; strategy = 'documented_plus_e' },
        [pscustomobject]@{ name = 'H' + $DocumentedId; strategy = 'runtime_h_prefix' },
        [pscustomobject]@{ name = 'H' + $DocumentedId + 'E'; strategy = 'runtime_h_prefix_plus_e' }
    )
    $seen = @{}
    foreach ($candidate in $candidates) {
        if ($seen.ContainsKey([string]$candidate.name)) { continue }
        $seen[[string]$candidate.name] = $true
        try {
            $value = Get-ComProperty -ComObject $Container -Name ([string]$candidate.name)
            if ($null -ne $value) {
                return [pscustomobject]@{ value = $value; strategy = [string]$candidate.strategy }
            }
        }
        catch { }
    }
    throw 'EQUATION_PARAMETER_SET_RUNTIME_ALIAS_NOT_RESOLVED'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Get-NamedValue {
    param([Parameter(Mandatory)]$Object, [Parameter(Mandatory)][string]$Name)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { throw 'EQUATION_PRIVATE_BINDING_MISSING' }
    return $property.Value
}

function Assert-Identifier {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,127}$') {
        throw 'EQUATION_PRIVATE_IDENTIFIER_SHAPE_INVALID'
    }
}

function Apply-EquationProgram {
    param(
        [Parameter(Mandatory)]$ParameterSet,
        [Parameter(Mandatory)]$Items,
        [Parameter(Mandatory)]$Program,
        [Parameter(Mandatory)]$Style
    )
    $values = [ordered]@{
        script = [string]$Program.script
        base_unit = [int]$Style.base_unit
        color = [int]$Style.color_bbggrr
        line_mode = [int]$Style.line_mode
        version = [string]$Style.version
        apply_to = [int]$Style.apply_to
        font_name = [string]$Style.font_name
    }
    foreach ($entry in $values.GetEnumerator()) {
        $binding = Get-NamedValue -Object $Items -Name ([string]$entry.Key)
        $itemName = [string]$binding.item_name
        Assert-Identifier -Value $itemName
        Set-ComProperty -ComObject $ParameterSet -Name $itemName -Value $entry.Value
    }
}

function Read-EquationScript {
    param([Parameter(Mandatory)]$ParameterSet, [Parameter(Mandatory)]$Items)
    $binding = Get-NamedValue -Object $Items -Name 'script'
    $itemName = [string]$binding.item_name
    Assert-Identifier -Value $itemName
    return [string](Get-ComProperty -ComObject $ParameterSet -Name $itemName)
}

$requestBytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $RequestPath).Path)
$requestSha256 = Get-Sha256Bytes -Value $requestBytes
if ($requestSha256 -cne $ExpectedRequestSha256) { throw 'EQUATION_REQUEST_SHA256_MISMATCH' }
$request = [Text.Encoding]::UTF8.GetString($requestBytes) | ConvertFrom-Json
if ([string]$request.schema_version -cne 'hwpx-agent.p07-06-equation-automation-probe-request/v1' -or
    [string]$request.target.profile_id -cne 'hancom-hangul-2020-secondary' -or
    [string]$request.target.exact_build -cne '11.0.0.9136' -or
    [string]$request.target.architecture -cne 'x86' -or
    [string]$request.target.client_apartment_state -cne 'STA' -or
    -not [bool]$request.policy.disposable_blank_document_only -or
    -not [bool]$request.policy.save_reopen_required -or
    -not [bool]$request.policy.no_fallback_after_possible_effect -or
    [bool]$request.policy.computer_use_click_or_type) {
    throw 'EQUATION_REQUEST_CONTRACT_MISMATCH'
}
if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'EQUATION_CLIENT_NOT_STA'
}
foreach ($program in @($request.program.initial, $request.program.edited)) {
    if ([Text.Encoding]::UTF8.GetByteCount([string]$program.script) -gt 1048576 -or
        (Get-Sha256String -Value ([string]$program.script)) -cne [string]$program.script_sha256) {
        throw 'EQUATION_PROGRAM_IDENTITY_MISMATCH'
    }
}

$insert = Get-NamedValue -Object $request.bindings.actions -Name 'eq.insert_native'
$edit = Get-NamedValue -Object $request.bindings.actions -Name 'eq.edit_native'
$selection = $request.bindings.selection
foreach ($binding in @($insert, $edit)) {
    Assert-Identifier -Value ([string]$binding.action_id)
    Assert-Identifier -Value ([string]$binding.parameter_set_id)
}
Assert-Identifier -Value ([string]$selection.action_id)
if ($null -ne $selection.parameter_set_id -or
    [string]$selection.operation_id -cne 'select_inserted_control_reverse') {
    throw 'EQUATION_SELECTION_BINDING_MISMATCH'
}
if ([string]$insert.parameter_set_id -cne [string]$edit.parameter_set_id) {
    throw 'EQUATION_PARAMETER_SET_ID_MISMATCH'
}

$tracePath = Join-Path $RunDirectory 'trace.json'
$initialPath = Join-Path $RunDirectory 'inserted.hwpx'
$editedPath = Join-Path $RunDirectory 'edited.hwpx'
foreach ($path in @($tracePath, $initialPath, $editedPath)) {
    if (Test-Path -LiteralPath $path) { throw 'EQUATION_OUTPUT_ALREADY_EXISTS' }
}
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p07-06-equation-automation-probe-trace/v1'
    request_id = [string]$request.request_id
    request_sha256 = $requestSha256
    binding_set_sha256 = [string]$request.source.binding_set_sha256
    target_profile_id = [string]$request.target.profile_id
    exact_build = [string]$request.target.exact_build
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    parameter_set_resolution = 'not_run'
    phases = [ordered]@{
        com_create = 'not_run'; version_check = 'not_run'; document_add = 'not_run'
        insert_default = 'not_run'; insert_execute = 'not_run'; select_inserted = 'not_run'
        insert_readback = 'not_run'
        insert_save = 'not_run'; edit_default = 'not_run'; edit_execute = 'not_run'
        edit_readback = 'not_run'; edit_save = 'not_run'; close = 'not_run'
        reopen = 'not_run'; reopen_close = 'not_run'; quit = 'not_run'
    }
    actions = [ordered]@{
        insert_return_kind = 'not_run'; selection_return_kind = 'not_run'; edit_return_kind = 'not_run'
        insert_default_return_kind = 'not_run'; edit_default_return_kind = 'not_run'
        insert_readback_return_kind = 'not_run'; edit_readback_return_kind = 'not_run'
    }
    semantic = [ordered]@{
        initial_script_sha256 = [string]$request.program.initial.script_sha256
        initial_readback_sha256 = $null
        initial_exact_match = $false
        edited_script_sha256 = [string]$request.program.edited.script_sha256
        edited_readback_sha256 = $null
        edited_exact_match = $false
    }
    outputs = [ordered]@{ inserted_hwpx_sha256 = $null; edited_hwpx_sha256 = $null }
    state = 'failed'; failed_phase = $null; error_code = $null
    exception_type = $null; exception_hresult = $null; exception_message_sha256 = $null
    quit_invoked = $false; user_document_opened = $false
    external_network_invoked = $false; registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
}

$hwp = $null
$documents = $null
$document = $null
$reopened = $null
$parameterContainer = $null
$parameterSet = $null
$parameterHSet = $null
$activePhase = 'initialization'
try {
    $activePhase = 'com_create'; $trace.phases.com_create = 'running'
    $hwp = New-Object -ComObject ([string]$request.target.prog_id)
    $trace.phases.com_create = 'pass'

    $activePhase = 'version_check'; $trace.phases.version_check = 'running'
    $version = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($version -cne [string]$request.target.exact_build) { throw 'EQUATION_VERSION_MISMATCH' }
    $trace.phases.version_check = 'pass'

    $documents = $hwp.XHwpDocuments
    $activePhase = 'document_add'; $trace.phases.document_add = 'running'
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'EQUATION_DOCUMENT_ADD_RETURNED_NULL' }
    $trace.phases.document_add = 'pass'

    $parameterContainer = $hwp.HParameterSet
    $resolution = Resolve-ParameterSetObject -Container $parameterContainer -DocumentedId ([string]$insert.parameter_set_id)
    $parameterSet = $resolution.value
    $trace.parameter_set_resolution = [string]$resolution.strategy
    $parameterHSet = Get-ComProperty -ComObject $parameterSet -Name 'HSet'

    $activePhase = 'insert_default'; $trace.phases.insert_default = 'running'
    $defaultReturn = $hwp.HAction.GetDefault([string]$insert.action_id, $parameterHSet)
    $trace.actions.insert_default_return_kind = Get-ReturnKind -Value $defaultReturn
    if ($defaultReturn -eq $false) { throw 'EQUATION_INSERT_DEFAULT_RETURNED_FALSE' }
    $trace.phases.insert_default = 'pass'

    Apply-EquationProgram -ParameterSet $parameterSet -Items $request.bindings.items -Program $request.program.initial -Style $request.program.style
    $activePhase = 'insert_execute'; $trace.phases.insert_execute = 'running'
    $insertReturn = $hwp.HAction.Execute([string]$insert.action_id, $parameterHSet)
    $trace.actions.insert_return_kind = Get-ReturnKind -Value $insertReturn
    if ($insertReturn -eq $false) { throw 'EQUATION_INSERT_EXECUTE_RETURNED_FALSE' }
    $trace.phases.insert_execute = 'pass'

    $activePhase = 'select_inserted'; $trace.phases.select_inserted = 'running'
    $selectionReturn = $hwp.HAction.Run([string]$selection.action_id)
    $trace.actions.selection_return_kind = Get-ReturnKind -Value $selectionReturn
    if ($selectionReturn -eq $false) { throw 'EQUATION_SELECT_INSERTED_RETURNED_FALSE' }
    $trace.phases.select_inserted = 'pass'

    $activePhase = 'insert_readback'; $trace.phases.insert_readback = 'running'
    $readReturn = $hwp.HAction.GetDefault([string]$edit.action_id, $parameterHSet)
    $trace.actions.insert_readback_return_kind = Get-ReturnKind -Value $readReturn
    if ($readReturn -eq $false) { throw 'EQUATION_INSERT_READBACK_RETURNED_FALSE' }
    $initialReadback = Read-EquationScript -ParameterSet $parameterSet -Items $request.bindings.items
    $trace.semantic.initial_readback_sha256 = Get-Sha256String -Value $initialReadback
    $trace.semantic.initial_exact_match = $initialReadback -ceq [string]$request.program.initial.script
    if (-not $trace.semantic.initial_exact_match) { throw 'EQUATION_INSERT_READBACK_MISMATCH' }
    $trace.phases.insert_readback = 'pass'

    $activePhase = 'insert_save'; $trace.phases.insert_save = 'running'
    $saveReturn = $document.SaveAs($initialPath, 'HWPX', '')
    if ($saveReturn -eq $false -or -not [IO.File]::Exists($initialPath)) {
        throw 'EQUATION_INSERT_SAVE_FAILED'
    }
    $trace.outputs.inserted_hwpx_sha256 = Get-Sha256File -Path $initialPath
    $trace.phases.insert_save = 'pass'

    $activePhase = 'edit_default'; $trace.phases.edit_default = 'running'
    $editDefaultReturn = $hwp.HAction.GetDefault([string]$edit.action_id, $parameterHSet)
    $trace.actions.edit_default_return_kind = Get-ReturnKind -Value $editDefaultReturn
    if ($editDefaultReturn -eq $false) { throw 'EQUATION_EDIT_DEFAULT_RETURNED_FALSE' }
    $trace.phases.edit_default = 'pass'

    Apply-EquationProgram -ParameterSet $parameterSet -Items $request.bindings.items -Program $request.program.edited -Style $request.program.style
    $activePhase = 'edit_execute'; $trace.phases.edit_execute = 'running'
    $editReturn = $hwp.HAction.Execute([string]$edit.action_id, $parameterHSet)
    $trace.actions.edit_return_kind = Get-ReturnKind -Value $editReturn
    if ($editReturn -eq $false) { throw 'EQUATION_EDIT_EXECUTE_RETURNED_FALSE' }
    $trace.phases.edit_execute = 'pass'

    $activePhase = 'edit_readback'; $trace.phases.edit_readback = 'running'
    $editedReadReturn = $hwp.HAction.GetDefault([string]$edit.action_id, $parameterHSet)
    $trace.actions.edit_readback_return_kind = Get-ReturnKind -Value $editedReadReturn
    if ($editedReadReturn -eq $false) { throw 'EQUATION_EDIT_READBACK_RETURNED_FALSE' }
    $editedReadback = Read-EquationScript -ParameterSet $parameterSet -Items $request.bindings.items
    $trace.semantic.edited_readback_sha256 = Get-Sha256String -Value $editedReadback
    $trace.semantic.edited_exact_match = $editedReadback -ceq [string]$request.program.edited.script
    if (-not $trace.semantic.edited_exact_match) { throw 'EQUATION_EDIT_READBACK_MISMATCH' }
    $trace.phases.edit_readback = 'pass'

    $activePhase = 'edit_save'; $trace.phases.edit_save = 'running'
    $editSaveReturn = $document.SaveAs($editedPath, 'HWPX', '')
    if ($editSaveReturn -eq $false -or -not [IO.File]::Exists($editedPath)) {
        throw 'EQUATION_EDIT_SAVE_FAILED'
    }
    $trace.outputs.edited_hwpx_sha256 = Get-Sha256File -Path $editedPath
    $trace.phases.edit_save = 'pass'

    $activePhase = 'close'; $trace.phases.close = 'running'
    $null = $document.Close($false)
    Clear-ComObject -Value $document; $document = $null
    $trace.phases.close = 'pass'

    $activePhase = 'reopen'; $trace.phases.reopen = 'running'
    $reopened = $documents.Add($false)
    if ($null -eq $reopened) { throw 'EQUATION_REOPEN_DOCUMENT_ADD_RETURNED_NULL' }
    $openReturn = $reopened.Open($editedPath, 'HWPX', 'lock:false;setcurdir:false')
    if ($openReturn -eq $false) { throw 'EQUATION_REOPEN_RETURNED_FALSE' }
    $trace.phases.reopen = 'pass'

    $activePhase = 'reopen_close'; $trace.phases.reopen_close = 'running'
    $null = $reopened.Close($false)
    Clear-ComObject -Value $reopened; $reopened = $null
    $trace.phases.reopen_close = 'pass'

    $activePhase = 'quit'; $trace.phases.quit = 'running'
    $hwp.Quit(); $trace.quit_invoked = $true; $trace.phases.quit = 'pass'
    $trace.state = 'pass'
}
catch {
    $trace.state = 'failed'; $trace.failed_phase = $activePhase
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    } else { 'EQUATION_AUTOMATION_CHILD_EXCEPTION' }
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    if ($trace.phases.Contains($activePhase)) { $trace.phases[$activePhase] = 'failed' }
}
finally {
    Clear-ComObject -Value $parameterHSet
    Clear-ComObject -Value $parameterSet
    Clear-ComObject -Value $parameterContainer
    foreach ($candidate in @($reopened, $document)) {
        if ($null -ne $candidate) {
            try { $null = $candidate.Close($false) } catch { }
            Clear-ComObject -Value $candidate
        }
    }
    Clear-ComObject -Value $documents
    if ($null -ne $hwp) {
        if (-not $trace.quit_invoked) {
            try { $hwp.Quit(); $trace.quit_invoked = $true; $trace.phases.quit = 'pass' }
            catch { $trace.phases.quit = 'failed' }
        }
        Clear-ComObject -Value $hwp
    }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}

$utf8 = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText($tracePath, ($trace | ConvertTo-Json -Depth 12), $utf8)
if ($trace.state -ne 'pass') { exit 2 }
