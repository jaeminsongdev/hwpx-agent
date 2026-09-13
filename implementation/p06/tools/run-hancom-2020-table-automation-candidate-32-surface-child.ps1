[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RequestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRequestSha256,
    [Parameter(Mandatory)][string]$FixtureControlsPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureControlsSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedFeatures = @(
    'TABLE-001', 'TABLE-002', 'TABLE-003', 'TABLE-004', 'TABLE-005', 'TABLE-007',
    'TABLE-010', 'TABLE-011', 'TABLE-014', 'TABLE-015', 'TABLE-016', 'TABLE-017',
    'TABLE-018', 'TABLE-019', 'TABLE-020', 'TABLE-021', 'TABLE-022', 'TABLE-023',
    'TABLE-024', 'TABLE-025', 'TABLE-026', 'TABLE-027', 'TABLE-028', 'TABLE-029',
    'TABLE-030', 'TABLE-031', 'TABLE-032', 'TABLE-033', 'TABLE-036', 'TABLE-046',
    'TABLE-048', 'TABLE-057'
)
$expectedContexts = @(
    'blank_document', 'current_table', 'current_table', 'selected_text',
    'current_table', 'current_table', 'current_row_boundary', 'current_table',
    'current_row_block', 'current_column_block', 'single_cell_block',
    'adjacent_two_cell_block', 'rectangular_cell_block', 'rectangular_cell_block',
    'current_table', 'current_table', 'numeric_cell_block', 'numeric_cell_block',
    'numeric_cell_block', 'numeric_cell_block', 'numeric_cell_block',
    'numeric_cell_block', 'numeric_cell_block', 'numeric_cell_block',
    'numeric_cell_block', 'single_cell_block', 'numeric_cell_block',
    'numeric_cell_block', 'current_table', 'single_cell_block', 'single_cell_block',
    'numeric_cell_block'
)
$expectedControlKeys = @(
    'insert_text', 'insert_text_parameter_set', 'move_document_begin', 'select_all',
    'table_cell_block', 'table_cell_block_column', 'table_cell_block_extend',
    'table_cell_block_row', 'table_creation_parameter_set', 'table_left_cell',
    'table_right_cell'
)

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally { $sha256.Dispose() }
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][string]$Value)
    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'CANDIDATE_32_VERSION_FORMAT_INVALID' }
    return (@('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }) -join '.'
}

function Get-RedactedErrorCode {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Message)
    if ($Message -cmatch '^CANDIDATE_32_[A-Z0-9_]+$') { return $Message }
    return 'CANDIDATE_32_RUNTIME_EXCEPTION'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

$script:fixtureControlActionExecuteCount = 0
function Invoke-FixtureAction {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][string]$Action
    )
    if ($Hwp.HAction.Run($Action) -eq $false) {
        throw 'CANDIDATE_32_FIXTURE_ACTION_FAILED'
    }
    $script:fixtureControlActionExecuteCount += 1
}

function Write-ExactText {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][object]$Controls,
        [Parameter(Mandatory)][string]$Text
    )
    $parameterSetName = [string]$Controls.insert_text_parameter_set
    $parameter = $Hwp.HParameterSet.$parameterSetName
    $hset = $parameter.HSet
    try {
        if ($Hwp.HAction.GetDefault([string]$Controls.insert_text, $hset) -eq $false) {
            throw 'CANDIDATE_32_INSERT_TEXT_DEFAULT_FAILED'
        }
        $parameter.Text = $Text
        if ($Hwp.HAction.Execute([string]$Controls.insert_text, $hset) -eq $false) {
            throw 'CANDIDATE_32_INSERT_TEXT_EXECUTE_FAILED'
        }
        $script:fixtureControlActionExecuteCount += 1
    }
    finally {
        Clear-ComObject -Value $hset
        Clear-ComObject -Value $parameter
    }
}

$sequence = 0
function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][string]$State,
        [int]$CaseIndex = 0,
        [AllowNull()][string]$FeatureId = $null,
        [AllowNull()][object]$HwpProcessId = $null
    )
    $script:sequence += 1
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-automation-candidate-32-progress/v1'
        sequence = $script:sequence
        worker_process_id = [Diagnostics.Process]::GetCurrentProcess().Id
        hwp_process_id = $HwpProcessId
        case_index = $CaseIndex
        feature_id = $FeatureId
        phase = $Phase
        state = $State
        candidate_under_probe_executed = $false
        raw_action_or_parameter_identifier_present = $false
    }
    $line = ($event | ConvertTo-Json -Compress -Depth 4) + [Environment]::NewLine
    [IO.File]::AppendAllText($ProgressPath, $line, [Text.UTF8Encoding]::new($false))
}

function New-Result {
    param([Parameter(Mandatory)]$Case)
    return [ordered]@{
        index = [int]$Case.index
        feature_id = [string]$Case.feature_id
        capability_id = [string]$Case.capability_id
        selection_context = [string]$Case.selection_context
        action_id_sha256 = Get-Sha256String -Value ([string]$Case.action_id)
        parameter_set_id_sha256 = if ($null -eq $Case.parameter_set_id) {
            $null
        } else {
            Get-Sha256String -Value ([string]$Case.parameter_set_id)
        }
        document_created = $false
        fixture_context_created = $false
        context_prepared = $false
        is_action_enable = $null
        action_created = $false
        action_set_created = $false
        get_default_state = if ([string]$Case.parameter_set_state -ceq 'source_declares_none') {
            'not_applicable'
        } else { 'not_run' }
        action_set_member_count = 0
        action_set_shape_sha256 = $null
        candidate_under_probe_execute_state = 'not_run'
        document_closed_without_save = $false
        state = 'not_run'
        error_code = $null
        error_type = $null
        error_hresult = $null
        error_message_sha256 = $null
    }
}

if ([IntPtr]::Size -ne 4) { throw 'CANDIDATE_32_X86_POWERSHELL_REQUIRED' }
$resolvedRequest = (Resolve-Path -LiteralPath $RequestPath).Path
$resolvedControls = (Resolve-Path -LiteralPath $FixtureControlsPath).Path
$attemptDirectory = (Resolve-Path -LiteralPath (Split-Path -Parent $resolvedRequest)).Path
if ((Split-Path -Leaf $resolvedRequest) -cne 'request.json' -or
    (Split-Path -Leaf $resolvedControls) -cne 'fixture-controls.private.json' -or
    (Split-Path -Parent $resolvedControls) -cne $attemptDirectory -or
    (Get-Sha256File -Path $resolvedRequest) -cne $ExpectedRequestSha256 -or
    (Get-Sha256File -Path $resolvedControls) -cne $ExpectedFixtureControlsSha256 -or
    [IO.Path]::GetFullPath($TracePath) -cne (Join-Path $attemptDirectory 'trace.json') -or
    [IO.Path]::GetFullPath($ProgressPath) -cne (Join-Path $attemptDirectory 'trace.json.progress.jsonl')) {
    throw 'CANDIDATE_32_CHILD_INPUT_BOUNDARY_MISMATCH'
}
foreach ($path in @($TracePath, $ProgressPath)) {
    if ([IO.File]::Exists($path) -or [IO.Directory]::Exists($path)) {
        throw 'CANDIDATE_32_CHILD_OUTPUT_ALREADY_EXISTS'
    }
}

$request = Get-Content -LiteralPath $resolvedRequest -Raw -Encoding UTF8 | ConvertFrom-Json
$controls = Get-Content -LiteralPath $resolvedControls -Raw -Encoding UTF8 | ConvertFrom-Json
$controlProperties = @($controls.PSObject.Properties | ForEach-Object { $_.Name })
if ([string]$controls.schema_version -cne
        'hwpx-agent.p06-09-table-automation-candidate-32-fixture-controls-private/v1' -or
    @($controlProperties | Where-Object { $_ -cne 'schema_version' }).Count -ne 11 -or
    @($expectedControlKeys | Where-Object { $_ -notin $controlProperties }).Count -ne 0 -or
    @($expectedControlKeys | ForEach-Object { [string]$controls.$_ } |
        Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -ne 0) {
    throw 'CANDIDATE_32_FIXTURE_CONTROLS_CONTRACT_MISMATCH'
}
if ([string]$request.schema_version -cne
        'hwpx-agent.p06-09-table-automation-candidate-32-request/v1' -or
    [string]$request.state -cne 'planned' -or
    [string]$request.target.prog_id -cne 'HWPFrame.HwpObject.2' -or
    [string]$request.target.build -cne '11.0.0.9136' -or
    [int]$request.case_count -ne 32 -or
    @($request.cases).Count -ne 32 -or
    [int]$request.documented_parameter_set_count -ne 14 -or
    [string]$request.session_strategy -cne
        'one_hwp_session_32_isolated_disposable_documents' -or
    [bool]$request.policy.candidate_under_probe_execute_allowed -or
    -not [bool]$request.policy.default_read_allowed -or
    -not [bool]$request.policy.disposable_fixture_action_execute_allowed -or
    [bool]$request.policy.user_document_open_allowed -or
    [bool]$request.policy.file_open_or_save_allowed -or
    [bool]$request.policy.external_network_allowed -or
    [bool]$request.policy.registry_or_system_setting_write_allowed -or
    [bool]$request.policy.computer_use_click_or_type_allowed -or
    [string]$request.promotion.runtime_support_state -cne 'not_eligible' -or
    [bool]$request.promotion.routing_enabled -or
    [int]$request.fixture_policy.table_create_fixture_action_execute_count -ne 30 -or
    [bool]$request.fixture_policy.fixture_execution_qualifies_runtime) {
    throw 'CANDIDATE_32_CHILD_REQUEST_CONTRACT_MISMATCH'
}
for ($index = 0; $index -lt 32; $index += 1) {
    $case = $request.cases[$index]
    if ([int]$case.index -ne ($index + 1) -or
        [string]$case.feature_id -cne $expectedFeatures[$index] -or
        [string]$case.selection_context -cne $expectedContexts[$index] -or
        [bool]$case.execute_candidate_under_probe -or
        [string]$case.surface_probe -cne 'is_action_enable_and_default_read_only') {
        throw 'CANDIDATE_32_CHILD_CASE_BOUNDARY_MISMATCH'
    }
}
$fixtureCreateCases = @($request.cases | Where-Object { $_.feature_id -ceq 'TABLE-001' })
if ($fixtureCreateCases.Count -ne 1) { throw 'CANDIDATE_32_FIXTURE_CREATE_IDENTITY_MISMATCH' }
$fixtureCreateAction = [string]$fixtureCreateCases[0].action_id

$results = @($request.cases | ForEach-Object { New-Result -Case $_ })
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-candidate-32-surface-trace/v1'
    state = 'failed'
    request_sha256 = $ExpectedRequestSha256
    fixture_controls_sha256 = $ExpectedFixtureControlsSha256
    target = [ordered]@{
        prog_id = 'HWPFrame.HwpObject.2'
        build = '11.0.0.9136'
        client = 'windows_powershell_x86_sta'
    }
    session_strategy = 'one_hwp_session_32_isolated_disposable_documents'
    case_count = 32
    completed_case_count = 0
    enabled_case_count = 0
    default_read_passed = 0
    table_create_fixture_action_execute_count = 0
    fixture_control_action_execute_count = 0
    candidate_under_probe_execute_count = 0
    cases = $results
    hwp_process_id = $null
    window_visible_for_user_access = $false
    user_document_opened = $false
    file_open_or_save_invoked = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    failed_phase = $null
    failed_feature_id = $null
    error_code = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    quit_invoked = $false
}

$hwp = $null
$documents = $null
$window = $null
$document = $null
$creation = $null
$creationHSet = $null
$action = $null
$actionSet = $null
$phase = 'initialization'
$activeFeature = $null
try {
    Write-ProgressEvent -Phase 'preflight' -State 'pass'
    $phase = 'com_create'
    Write-ProgressEvent -Phase $phase -State 'running'
    $hwp = New-Object -ComObject ([string]$request.target.prog_id)
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne '11.0.0.9136') {
        throw 'CANDIDATE_32_AUTOMATION_VERSION_MISMATCH'
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction Stop)
    if ($hwpProcesses.Count -ne 1) { throw 'CANDIDATE_32_HWP_PROCESS_CARDINALITY_MISMATCH' }
    $trace.hwp_process_id = [int]$hwpProcesses[0].ProcessId
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $trace.hwp_process_id
    $documents = $hwp.XHwpDocuments

    for ($index = 0; $index -lt 32; $index += 1) {
        $case = $request.cases[$index]
        $result = $results[$index]
        $activeFeature = [string]$case.feature_id
        $phase = 'case_setup'
        Write-ProgressEvent -Phase $phase -State 'running' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'CANDIDATE_32_DOCUMENT_ADD_FAILED' }
        $result.document_created = $true
        $window = $hwp.XHwpWindows.Item(0)
        $window.Visible = $true
        $trace.window_visible_for_user_access = $true
        [void]$document.SetActive_XHwpDocument()

        $context = [string]$case.selection_context
        if ($context -eq 'selected_text') {
            Write-ExactText -Hwp $hwp -Controls $controls -Text "1`t2`r`n3`t4"
            Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.move_document_begin)
            Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.select_all)
            $result.fixture_context_created = $true
        }
        elseif ($context -ne 'blank_document') {
            $creationParameterSetName = [string]$controls.table_creation_parameter_set
            $creation = $hwp.HParameterSet.$creationParameterSetName
            $creationHSet = $creation.HSet
            if ($hwp.HAction.GetDefault($fixtureCreateAction, $creationHSet) -eq $false) {
                throw 'CANDIDATE_32_TABLE_CREATE_DEFAULT_FAILED'
            }
            $creation.Rows = 3
            $creation.Cols = 3
            if ($hwp.HAction.Execute($fixtureCreateAction, $creationHSet) -eq $false) {
                throw 'CANDIDATE_32_TABLE_CREATE_FAILED'
            }
            $trace.table_create_fixture_action_execute_count += 1
            $result.fixture_context_created = $true
            Clear-ComObject -Value $creationHSet
            Clear-ComObject -Value $creation
            $creationHSet = $null
            $creation = $null
        }

        switch ($context) {
            'blank_document' { }
            'selected_text' { }
            'current_table' { }
            'current_row_boundary' {
                1..3 | ForEach-Object {
                    Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_right_cell)
                }
            }
            'current_row_block' {
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block_row)
            }
            'current_column_block' {
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block_column)
            }
            'single_cell_block' {
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block)
            }
            'adjacent_two_cell_block' {
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block)
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block_extend)
            }
            'rectangular_cell_block' {
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block)
                1..2 | ForEach-Object {
                    Invoke-FixtureAction -Hwp $hwp `
                        -Action ([string]$controls.table_cell_block_extend)
                }
            }
            'numeric_cell_block' {
                foreach ($value in @('1', '2', '3', '4')) {
                    Write-ExactText -Hwp $hwp -Controls $controls -Text $value
                    if ($value -cne '4') {
                        Invoke-FixtureAction -Hwp $hwp `
                            -Action ([string]$controls.table_right_cell)
                    }
                }
                1..3 | ForEach-Object {
                    Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_left_cell)
                }
                Invoke-FixtureAction -Hwp $hwp -Action ([string]$controls.table_cell_block)
                1..2 | ForEach-Object {
                    Invoke-FixtureAction -Hwp $hwp `
                        -Action ([string]$controls.table_cell_block_extend)
                }
            }
            default { throw 'CANDIDATE_32_UNKNOWN_SELECTION_CONTEXT' }
        }
        $result.context_prepared = $true
        Write-ProgressEvent -Phase $phase -State 'pass' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id

        $phase = 'surface_probe'
        Write-ProgressEvent -Phase $phase -State 'running' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id
        $result.is_action_enable = [bool]$hwp.IsActionEnable([string]$case.action_id)
        if ($result.is_action_enable) { $trace.enabled_case_count += 1 }
        $action = $hwp.CreateAction([string]$case.action_id)
        if ($null -eq $action) { throw 'CANDIDATE_32_ACTION_CREATE_FAILED' }
        $result.action_created = $true
        if ([string]$case.parameter_set_state -ceq 'documented_candidate') {
            $actionSet = $action.CreateSet()
            if ($null -eq $actionSet) { throw 'CANDIDATE_32_ACTION_SET_CREATE_FAILED' }
            $result.action_set_created = $true
            if ($action.GetDefault($actionSet) -eq $false) {
                throw 'CANDIDATE_32_GET_DEFAULT_FAILED'
            }
            $members = @(
                $actionSet.PSObject.Properties |
                    ForEach-Object { "property:$($_.Name):$($_.TypeNameOfValue)" } |
                    Sort-Object -Unique
            )
            $result.action_set_member_count = $members.Count
            $result.action_set_shape_sha256 = Get-Sha256String -Value ($members -join "`n")
            $result.get_default_state = 'pass'
            $trace.default_read_passed += 1
        }
        $result.state = if ($result.is_action_enable) { 'surface_present_enabled' } `
            else { 'surface_present_disabled_in_context' }
        Write-ProgressEvent -Phase $phase -State 'pass' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id

        $phase = 'case_close'
        Clear-ComObject -Value $actionSet
        Clear-ComObject -Value $action
        $actionSet = $null
        $action = $null
        [void]$document.Close($false)
        $result.document_closed_without_save = $true
        Clear-ComObject -Value $window
        Clear-ComObject -Value $document
        $window = $null
        $document = $null
        $trace.completed_case_count += 1
        Write-ProgressEvent -Phase $phase -State 'pass' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id
    }
    $trace.fixture_control_action_execute_count = $script:fixtureControlActionExecuteCount
    if ($trace.completed_case_count -ne 32 -or $trace.default_read_passed -ne 14 -or
        $trace.table_create_fixture_action_execute_count -ne 30 -or
        $trace.fixture_control_action_execute_count -ne 176 -or
        $trace.candidate_under_probe_execute_count -ne 0) {
        throw 'CANDIDATE_32_COMPLETION_BOUNDARY_MISMATCH'
    }
    $phase = 'quit'
    [void]$hwp.Quit()
    $trace.quit_invoked = $true
    $trace.state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $trace.hwp_process_id
}
catch {
    $trace.state = 'failed'
    $trace.failed_phase = $phase
    $trace.failed_feature_id = $activeFeature
    $trace.error_code = Get-RedactedErrorCode -Message ([string]$_.Exception.Message)
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    if ($null -ne $activeFeature) {
        $failed = @($results | Where-Object { $_.feature_id -ceq $activeFeature })
        if ($failed.Count -eq 1) {
            $failed[0].state = 'failed'
            $failed[0].error_code = $trace.error_code
            $failed[0].error_type = $_.Exception.GetType().FullName
            $failed[0].error_hresult = $_.Exception.HResult
            $failed[0].error_message_sha256 = $trace.exception_message_sha256
        }
    }
    Write-ProgressEvent -Phase $phase -State 'failed' -FeatureId $activeFeature `
        -HwpProcessId $trace.hwp_process_id
}
finally {
    $trace.fixture_control_action_execute_count = $script:fixtureControlActionExecuteCount
    Clear-ComObject -Value $actionSet
    Clear-ComObject -Value $action
    Clear-ComObject -Value $creationHSet
    Clear-ComObject -Value $creation
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
    }
    Clear-ComObject -Value $window
    Clear-ComObject -Value $document
    Clear-ComObject -Value $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { [void]$hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    if ([IO.File]::Exists($TracePath) -or [IO.Directory]::Exists($TracePath)) {
        throw 'CANDIDATE_32_TRACE_COLLISION'
    }
    $payload = ($trace | ConvertTo-Json -Depth 12) + [Environment]::NewLine
    [IO.File]::WriteAllText($TracePath, $payload, [Text.UTF8Encoding]::new($false))
}

if ($trace.state -cne 'pass') { exit 1 }
