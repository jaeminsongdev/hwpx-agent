[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RequestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRequestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedRequestSha256 = 'd9588469b901ec31136e15f657b772f93872943c0411ac7b4794ba4feca31355'
$expectedFeatures = @('TABLE-010', 'TABLE-015', 'TABLE-016', 'TABLE-017', 'TABLE-046', 'TABLE-048')
$expectedContexts = @(
    'current_row_boundary', 'current_column_block', 'single_cell',
    'adjacent_two_cell_block', 'single_cell', 'single_cell'
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
    finally {
        $sha256.Dispose()
    }
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][string]$Value)
    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'CANDIDATE_SURFACE_VERSION_FORMAT_INVALID' }
    return (@('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }) -join '.'
}

function Get-RedactedErrorCode {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Message)
    if ($Message -cmatch '^CANDIDATE_SURFACE_[A-Z0-9_]+$') { return $Message }
    return 'CANDIDATE_SURFACE_RUNTIME_EXCEPTION'
}

function Clear-ComObject {
    param([AllowNull()]$Value)
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Invoke-ActionRun {
    param([Parameter(Mandatory)][object]$Hwp, [Parameter(Mandatory)][string]$Action)
    if ($Hwp.HAction.Run($Action) -eq $false) {
        throw ('CANDIDATE_SURFACE_CONTEXT_ACTION_FAILED_' + $Action.ToUpperInvariant())
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
        schema_version = 'hwpx-agent.p06-09-table-automation-candidate-6-progress/v1'
        sequence = $script:sequence
        worker_process_id = [Diagnostics.Process]::GetCurrentProcess().Id
        hwp_process_id = $HwpProcessId
        case_index = $CaseIndex
        feature_id = $FeatureId
        phase = $Phase
        state = $State
        candidate_action_executed = $false
        raw_action_identifier_present = $false
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
        table_created = $false
        context_prepared = $false
        is_action_enable = $null
        action_created = $false
        action_set_created = $false
        get_default_state = if ([string]$Case.parameter_set_state -ceq 'source_declares_none') {
            'not_applicable'
        } else { 'not_run' }
        action_set_member_count = 0
        action_set_shape_sha256 = $null
        candidate_action_execute_state = 'not_run'
        document_closed_without_save = $false
        state = 'not_run'
        error_code = $null
        error_type = $null
        error_hresult = $null
        error_message_sha256 = $null
    }
}

$resolvedRequest = (Resolve-Path -LiteralPath $RequestPath).Path
$attemptDirectory = Split-Path -Parent $resolvedRequest
$resolvedAttempt = (Resolve-Path -LiteralPath $attemptDirectory).Path
if ((Split-Path -Leaf $resolvedRequest) -cne 'request.json' -or
    (Split-Path -Leaf $resolvedAttempt) -cne 'p06-09-table-automation-candidate-6-20260914-02' -or
    $ExpectedRequestSha256 -cne $expectedRequestSha256 -or
    (Get-Sha256File -Path $resolvedRequest) -cne $expectedRequestSha256 -or
    [IO.Path]::GetFullPath($TracePath) -cne (Join-Path $resolvedAttempt 'trace.json') -or
    [IO.Path]::GetFullPath($ProgressPath) -cne (Join-Path $resolvedAttempt 'trace.json.progress.jsonl')) {
    throw 'CANDIDATE_SURFACE_CHILD_INPUT_BOUNDARY_MISMATCH'
}
foreach ($path in @($TracePath, $ProgressPath)) {
    if ([IO.File]::Exists($path) -or [IO.Directory]::Exists($path)) {
        throw 'CANDIDATE_SURFACE_CHILD_OUTPUT_ALREADY_EXISTS'
    }
}

$request = Get-Content -LiteralPath $resolvedRequest -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$request.schema_version -cne
        'hwpx-agent.p06-09-table-automation-candidate-6-request/v1' -or
    [string]$request.state -cne 'planned' -or
    [string]$request.target.prog_id -cne 'HWPFrame.HwpObject.2' -or
    [string]$request.target.build -cne '11.0.0.9136' -or
    [int]$request.case_count -ne 6 -or
    @($request.cases).Count -ne 6 -or
    [string]$request.session_strategy -cne
        'one_hwp_session_six_generated_3x3_documents' -or
    [bool]$request.policy.candidate_action_execute_allowed -or
    -not [bool]$request.policy.default_read_allowed -or
    [bool]$request.policy.user_document_open_allowed -or
    [bool]$request.policy.external_network_allowed -or
    [bool]$request.policy.registry_or_system_setting_write_allowed -or
    [bool]$request.policy.computer_use_click_or_type_allowed -or
    [string]$request.promotion.runtime_support_state -cne 'not_eligible' -or
    [bool]$request.promotion.routing_enabled) {
    throw 'CANDIDATE_SURFACE_CHILD_REQUEST_CONTRACT_MISMATCH'
}
for ($index = 0; $index -lt 6; $index += 1) {
    $case = $request.cases[$index]
    if ([int]$case.index -ne ($index + 1) -or
        [string]$case.feature_id -cne $expectedFeatures[$index] -or
        [string]$case.selection_context -cne $expectedContexts[$index] -or
        [bool]$case.execute -or
        [string]$case.surface_probe -cne 'is_action_enable_and_default_read_only') {
        throw 'CANDIDATE_SURFACE_CHILD_CASE_BOUNDARY_MISMATCH'
    }
}

$results = @($request.cases | ForEach-Object { New-Result -Case $_ })
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-table-automation-candidate-6-surface-trace/v1'
    state = 'failed'
    request_sha256 = $expectedRequestSha256
    target = [ordered]@{
        prog_id = 'HWPFrame.HwpObject.2'
        build = '11.0.0.9136'
        client = 'windows_powershell_x86_sta'
    }
    session_strategy = 'one_hwp_session_six_generated_3x3_documents'
    case_count = 6
    completed_case_count = 0
    enabled_case_count = 0
    default_read_passed = 0
    candidate_action_execute_count = 0
    cases = $results
    hwp_process_id = $null
    window_visible_for_user_access = $false
    user_document_opened = $false
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
        throw 'CANDIDATE_SURFACE_AUTOMATION_VERSION_MISMATCH'
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction Stop)
    if ($hwpProcesses.Count -ne 1) { throw 'CANDIDATE_SURFACE_HWP_PROCESS_CARDINALITY_MISMATCH' }
    $trace.hwp_process_id = [int]$hwpProcesses[0].ProcessId
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $trace.hwp_process_id
    $documents = $hwp.XHwpDocuments

    for ($index = 0; $index -lt 6; $index += 1) {
        $case = $request.cases[$index]
        $result = $results[$index]
        $activeFeature = [string]$case.feature_id
        $phase = 'case_setup'
        Write-ProgressEvent -Phase $phase -State 'running' -CaseIndex ($index + 1) `
            -FeatureId $activeFeature -HwpProcessId $trace.hwp_process_id
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'CANDIDATE_SURFACE_DOCUMENT_ADD_FAILED' }
        $result.document_created = $true
        $window = $hwp.XHwpWindows.Item(0)
        $window.Visible = $true
        $trace.window_visible_for_user_access = $true
        [void]$document.SetActive_XHwpDocument()
        $creation = $hwp.HParameterSet.HTableCreation
        $creationHSet = $creation.HSet
        if ($hwp.HAction.GetDefault('TableCreate', $creationHSet) -eq $false) {
            throw 'CANDIDATE_SURFACE_TABLE_CREATE_DEFAULT_FAILED'
        }
        $creation.Rows = 3
        $creation.Cols = 3
        if ($hwp.HAction.Execute('TableCreate', $creationHSet) -eq $false) {
            throw 'CANDIDATE_SURFACE_TABLE_CREATE_FAILED'
        }
        $result.table_created = $true
        Clear-ComObject -Value $creationHSet
        Clear-ComObject -Value $creation
        $creationHSet = $null
        $creation = $null

        switch ([string]$case.selection_context) {
            'current_row_boundary' {
                1..3 | ForEach-Object { Invoke-ActionRun -Hwp $hwp -Action 'TableRightCell' }
            }
            'current_column_block' {
                Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlock'
            }
            'single_cell' {
                Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlock'
            }
            'adjacent_two_cell_block' {
                Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlock'
                Invoke-ActionRun -Hwp $hwp -Action 'TableCellBlockExtend'
            }
            default { throw 'CANDIDATE_SURFACE_UNKNOWN_SELECTION_CONTEXT' }
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
        if ($null -eq $action) { throw 'CANDIDATE_SURFACE_ACTION_CREATE_FAILED' }
        $result.action_created = $true
        if ([string]$case.parameter_set_state -ceq 'documented_candidate') {
            $actionSet = $action.CreateSet()
            if ($null -eq $actionSet) { throw 'CANDIDATE_SURFACE_ACTION_SET_CREATE_FAILED' }
            $result.action_set_created = $true
            if ($action.GetDefault($actionSet) -eq $false) {
                throw 'CANDIDATE_SURFACE_GET_DEFAULT_FAILED'
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
    if ($trace.completed_case_count -ne 6 -or $trace.default_read_passed -ne 4 -or
        $trace.candidate_action_execute_count -ne 0) {
        throw 'CANDIDATE_SURFACE_COMPLETION_BOUNDARY_MISMATCH'
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
        throw 'CANDIDATE_SURFACE_TRACE_COLLISION'
    }
    $payload = ($trace | ConvertTo-Json -Depth 12) + [Environment]::NewLine
    [IO.File]::WriteAllText($TracePath, $payload, [Text.UTF8Encoding]::new($false))
}

if ($trace.state -cne 'pass') { exit 1 }
