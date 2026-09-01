[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RunDirectory,

    [Parameter(Mandatory)]
    [string]$RequestPath,

    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedRequestSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256Bytes {
    param([Parameter(Mandatory)][byte[]]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($Value) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    return Get-Sha256Bytes -Value ([System.Text.Encoding]::UTF8.GetBytes($Value))
}

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function ConvertTo-NormalizedHancomVersion {
    param([Parameter(Mandatory)][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { return $null }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function ConvertTo-CanonicalProbeText {
    param([AllowEmptyString()][string]$Value)

    if ($null -eq $Value) { return $null }
    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC)
}

function Get-ReturnValueKind {
    param([AllowNull()]$Value)

    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) {
        if ([bool]$Value) { return 'true' }
        return 'false'
    }
    return 'other'
}

function Get-ComProperty {
    param(
        [Parameter(Mandatory)]$ComObject,
        [Parameter(Mandatory)][string]$Name
    )

    try {
        # PowerShell's COM adapter can resolve IDispatch members that are not
        # surfaced by __ComObject.GetType().
        return $ComObject.$Name
    }
    catch {
        $property = $ComObject.PSObject.Properties[$Name]
        if ($null -ne $property) { return $property.Value }
        return $ComObject.GetType().InvokeMember(
            $Name,
            [System.Reflection.BindingFlags]::GetProperty,
            $null,
            $ComObject,
            $null
        )
    }
}

function Clear-ComObject {
    param([AllowNull()]$Value)

    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function New-ProbeResult {
    param([Parameter(Mandatory)]$Probe)

    return [ordered]@{
        binding_key = [string]$Probe.binding_key
        feature_id = [string]$Probe.feature_id
        capability_id = [string]$Probe.capability_id
        planned_execution = [string]$Probe.execution_plan
        disposition = [string]$Probe.planned_disposition
        reason_code = [string]$Probe.reason_code
        default_read_state = if ([string]$Probe.parameter_set_state -eq 'source_declares_none') {
            'not_applicable'
        }
        else { 'not_run' }
        default_member_count = 0
        default_shape_sha256 = $null
        execute_state = 'not_run'
        return_value_kind = 'not_run'
        pre_snapshot_sha256 = $null
        post_snapshot_sha256 = $null
        expected_effect_observed = $false
    }
}

$resolvedRunDirectory = (Resolve-Path -LiteralPath $RunDirectory).Path
$resolvedRequestPath = (Resolve-Path -LiteralPath $RequestPath).Path
$tracePath = Join-Path $resolvedRunDirectory 'trace.json'
$hwpxPath = Join-Path $resolvedRunDirectory 'synthetic-p02-runtime-probe.hwpx'
foreach ($path in @($tracePath, $hwpxPath)) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing to overwrite an existing runtime probe output: $path"
    }
}

$requestBytes = [System.IO.File]::ReadAllBytes($resolvedRequestPath)
$requestSha256 = Get-Sha256Bytes -Value $requestBytes
if ($requestSha256 -cne $ExpectedRequestSha256) {
    throw 'RUNTIME_PROBE_REQUEST_SHA256_MISMATCH'
}
$request = [System.Text.Encoding]::UTF8.GetString($requestBytes) | ConvertFrom-Json
if ([string]$request.schema_version -cne 'hwpx-agent.runtime-probe-request/v1') {
    throw 'RUNTIME_PROBE_REQUEST_SCHEMA_VERSION_MISMATCH'
}
if ([string]$request.target.profile_id -cne 'hancom-hangul-2020-secondary' -or
    [string]$request.target.exact_build -cne '11.0.0.9136' -or
    [string]$request.target.architecture -cne 'x86' -or
    [string]$request.target.client_apartment_state -cne 'STA') {
    throw 'RUNTIME_PROBE_REQUEST_TARGET_MISMATCH'
}
if (@($request.policy.execution_allowlist) -join ',' -cne 'edit.undo,edit.redo' -or
    @($request.policy.default_read_allowlist) -join ',' -cne 'edit.go_to') {
    throw 'RUNTIME_PROBE_REQUEST_ALLOWLIST_MISMATCH'
}

$fixtureId = [string]$request.fixture.fixture_id
$unicodeFixtureLine = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('VU5JQ09ERT3tlZzquIAg7J6Q64+Z7ZmUIOyViOyghCDtlITroZzruIw=')
)
$fixtureText = @(
    'HWPX Agent P02 exact 2020 disposable runtime probe'
    "fixture_id=$fixtureId"
    'ASCII=ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789'
    $unicodeFixtureLine
) -join "`r`n"
$fixtureCanonical = ConvertTo-CanonicalProbeText -Value $fixtureText
$fixtureSha256 = Get-Sha256String -Value $fixtureCanonical

$probeResults = @()
$resultByCapability = @{}
foreach ($probe in @($request.probes)) {
    $result = New-ProbeResult -Probe $probe
    $probeResults += $result
    $resultByCapability[[string]$probe.capability_id] = $result
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.runtime-probe-trace/v1'
    request_id = [string]$request.request_id
    request_sha256 = $requestSha256
    registry_sha256 = [string]$request.registry_sha256
    target_profile_id = [string]$request.target.profile_id
    exact_build = [string]$request.target.exact_build
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    automation_version_normalized = $null
    fixture = [ordered]@{
        fixture_id = $fixtureId
        input_sha256 = $fixtureSha256
        undo_snapshot_sha256 = $null
        redo_snapshot_sha256 = $null
        reopen_snapshot_sha256 = $null
        output_hwpx_sha256 = $null
        reopen_exact_match = $false
    }
    phases = [ordered]@{
        com_create = 'not_run'
        version_check = 'not_run'
        document_add = 'not_run'
        fixture_insert = 'not_run'
        default_parameter_read = 'not_run'
        undo_canary = 'not_run'
        redo_canary = 'not_run'
        hwpx_save = 'not_run'
        document_close_before_reopen = 'not_run'
        hwpx_reopen = 'not_run'
        semantic_reopen = 'not_run'
        document_close = 'not_run'
        quit = 'not_run'
    }
    probe_results = $probeResults
    state = 'failed'
    error_code = $null
    failed_phase = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    quit_invoked = $false
    user_document_opened = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
}

$hwp = $null
$documents = $null
$document = $null
$reopenedDocument = $null
$parameterContainer = $null
$parameterSet = $null
$parameterHSet = $null
$activePhase = 'initialization'

try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'CLIENT_NOT_STA'
    }

    $activePhase = 'com_create'
    $trace.phases.com_create = 'running'
    $hwp = New-Object -ComObject ([string]$request.target.prog_id)
    $trace.phases.com_create = 'pass'

    $activePhase = 'version_check'
    $trace.phases.version_check = 'running'
    $trace.automation_version_normalized = ConvertTo-NormalizedHancomVersion -Value ([string]$hwp.Version)
    if ($trace.automation_version_normalized -cne [string]$request.target.exact_build) {
        throw 'AUTOMATION_VERSION_MISMATCH'
    }
    $trace.phases.version_check = 'pass'

    $documents = $hwp.XHwpDocuments
    $activePhase = 'document_add'
    $trace.phases.document_add = 'running'
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'DOCUMENT_ADD_RETURNED_NULL' }
    $trace.phases.document_add = 'pass'

    $activePhase = 'fixture_insert'
    $trace.phases.fixture_insert = 'running'
    $null = $hwp.HAction.GetDefault('InsertText', $hwp.HParameterSet.HInsertText.HSet)
    $hwp.HParameterSet.HInsertText.Text = $fixtureText
    $insertResult = $hwp.HAction.Execute('InsertText', $hwp.HParameterSet.HInsertText.HSet)
    if ($insertResult -eq $false) { throw 'FIXTURE_INSERT_RETURNED_FALSE' }
    $insertedCanonical = ConvertTo-CanonicalProbeText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    if ($insertedCanonical -cne $fixtureCanonical) { throw 'FIXTURE_INSERT_READBACK_MISMATCH' }
    $trace.phases.fixture_insert = 'pass'

    $activePhase = 'default_parameter_read'
    $trace.phases.default_parameter_read = 'running'
    $defaultProbe = @($request.probes | Where-Object { [bool]$_.default_read_planned })
    if ($defaultProbe.Count -ne 1 -or [string]$defaultProbe[0].capability_id -cne 'edit.go_to') {
        throw 'DEFAULT_READ_ALLOWLIST_CARDINALITY_MISMATCH'
    }
    $defaultResult = $resultByCapability['edit.go_to']
    $defaultReadSubphase = 'parameter_container'
    try {
        $parameterContainer = $hwp.HParameterSet
        $defaultReadSubphase = 'parameter_set_resolve'
        $parameterSet = Get-ComProperty -ComObject $parameterContainer -Name ([string]$defaultProbe[0].parameter_set_id)
        $defaultReadSubphase = 'hset_resolve'
        $parameterHSet = Get-ComProperty -ComObject $parameterSet -Name 'HSet'
        $defaultReadSubphase = 'get_default'
        $getDefaultResult = $hwp.HAction.GetDefault([string]$defaultProbe[0].action_id, $parameterHSet)
        if ($getDefaultResult -eq $false) { throw 'GET_DEFAULT_RETURNED_FALSE' }
        $defaultReadSubphase = 'shape_snapshot'
        $memberDescriptors = @(
            $parameterSet.PSObject.Properties |
                ForEach-Object { "property:$($_.Name):$($_.TypeNameOfValue)" } |
                Sort-Object -Unique
        )
        $shapeSeed = @(
            "parameter_set_id_sha256=$(Get-Sha256String -Value ([string]$defaultProbe[0].parameter_set_id))"
            "get_default_return=$(Get-ReturnValueKind -Value $getDefaultResult)"
            $memberDescriptors
        ) -join "`n"
        $defaultResult.default_read_state = 'pass'
        $defaultResult.default_member_count = $memberDescriptors.Count
        $defaultResult.default_shape_sha256 = Get-Sha256String -Value $shapeSeed
        $defaultResult.reason_code = 'safe_default_read_pass_execution_not_run'
    }
    catch {
        $defaultResult.default_read_state = 'failed'
        $defaultResult.disposition = 'failed'
        $defaultResult.reason_code = "default_read_${defaultReadSubphase}_failed"
        throw
    }
    finally {
        Clear-ComObject -Value $parameterHSet
        Clear-ComObject -Value $parameterSet
        Clear-ComObject -Value $parameterContainer
        $parameterHSet = $null
        $parameterSet = $null
        $parameterContainer = $null
    }
    $trace.phases.default_parameter_read = 'pass'

    $activePhase = 'undo_canary'
    $trace.phases.undo_canary = 'running'
    $undoProbe = @($request.probes | Where-Object { [string]$_.capability_id -ceq 'edit.undo' })
    if ($undoProbe.Count -ne 1 -or [string]$undoProbe[0].execution_plan -cne 'safe_canary') {
        throw 'UNDO_CANARY_REQUEST_INVALID'
    }
    $undoResult = $resultByCapability['edit.undo']
    $undoResult.pre_snapshot_sha256 = $fixtureSha256
    $undoReturn = $hwp.HAction.Run([string]$undoProbe[0].action_id)
    $undoCanonical = ConvertTo-CanonicalProbeText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $undoSha256 = Get-Sha256String -Value $undoCanonical
    $undoObserved = $undoReturn -ne $false -and $undoCanonical -cne $fixtureCanonical -and -not $undoCanonical.Contains($fixtureId)
    $undoResult.return_value_kind = Get-ReturnValueKind -Value $undoReturn
    $undoResult.post_snapshot_sha256 = $undoSha256
    $undoResult.expected_effect_observed = $undoObserved
    $trace.fixture.undo_snapshot_sha256 = $undoSha256
    if (-not $undoObserved) {
        $undoResult.execute_state = 'failed'
        $undoResult.disposition = 'failed'
        $undoResult.reason_code = 'undo_effect_mismatch'
        throw 'UNDO_CANARY_EFFECT_MISMATCH'
    }
    $undoResult.execute_state = 'pass'
    $undoResult.disposition = 'verified'
    $undoResult.reason_code = 'fixture_removed_exact_2020'
    $trace.phases.undo_canary = 'pass'

    $activePhase = 'redo_canary'
    $trace.phases.redo_canary = 'running'
    $redoProbe = @($request.probes | Where-Object { [string]$_.capability_id -ceq 'edit.redo' })
    if ($redoProbe.Count -ne 1 -or [string]$redoProbe[0].execution_plan -cne 'safe_canary') {
        throw 'REDO_CANARY_REQUEST_INVALID'
    }
    $redoResult = $resultByCapability['edit.redo']
    $redoResult.pre_snapshot_sha256 = $undoSha256
    $redoReturn = $hwp.HAction.Run([string]$redoProbe[0].action_id)
    $redoCanonical = ConvertTo-CanonicalProbeText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $redoSha256 = Get-Sha256String -Value $redoCanonical
    $redoObserved = $redoReturn -ne $false -and $redoCanonical -ceq $fixtureCanonical
    $redoResult.return_value_kind = Get-ReturnValueKind -Value $redoReturn
    $redoResult.post_snapshot_sha256 = $redoSha256
    $redoResult.expected_effect_observed = $redoObserved
    $trace.fixture.redo_snapshot_sha256 = $redoSha256
    if (-not $redoObserved) {
        $redoResult.execute_state = 'failed'
        $redoResult.disposition = 'failed'
        $redoResult.reason_code = 'redo_effect_mismatch'
        throw 'REDO_CANARY_EFFECT_MISMATCH'
    }
    $redoResult.execute_state = 'pass'
    $redoResult.disposition = 'verified'
    $redoResult.reason_code = 'fixture_restored_exact_2020'
    $trace.phases.redo_canary = 'pass'

    $activePhase = 'hwpx_save'
    $trace.phases.hwpx_save = 'running'
    $null = $document.SaveAs($hwpxPath, 'HWPX', '')
    if (-not (Test-Path -LiteralPath $hwpxPath -PathType Leaf)) {
        throw 'HWPX_SAVE_OUTPUT_MISSING'
    }
    $trace.fixture.output_hwpx_sha256 = Get-Sha256File -Path $hwpxPath
    $trace.phases.hwpx_save = 'pass'

    $activePhase = 'document_close_before_reopen'
    $trace.phases.document_close_before_reopen = 'running'
    $null = $document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $trace.phases.document_close_before_reopen = 'pass'

    $activePhase = 'hwpx_reopen'
    $trace.phases.hwpx_reopen = 'running'
    $reopenedDocument = $documents.Add($false)
    if ($null -eq $reopenedDocument) { throw 'REOPEN_DOCUMENT_ADD_RETURNED_NULL' }
    $openResult = $reopenedDocument.Open($hwpxPath, 'HWPX', 'lock:false;setcurdir:false')
    if ($openResult -eq $false) { throw 'HWPX_REOPEN_RETURNED_FALSE' }
    $null = $reopenedDocument.SetActive_XHwpDocument()
    $trace.phases.hwpx_reopen = 'pass'

    $activePhase = 'semantic_reopen'
    $trace.phases.semantic_reopen = 'running'
    $reopenCanonical = ConvertTo-CanonicalProbeText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $trace.fixture.reopen_snapshot_sha256 = Get-Sha256String -Value $reopenCanonical
    $trace.fixture.reopen_exact_match = $reopenCanonical -ceq $fixtureCanonical
    if (-not $trace.fixture.reopen_exact_match) { throw 'HWPX_REOPEN_TEXT_MISMATCH' }
    $trace.phases.semantic_reopen = 'pass'

    $activePhase = 'document_close'
    $trace.phases.document_close = 'running'
    $null = $reopenedDocument.Close($false)
    Clear-ComObject -Value $reopenedDocument
    $reopenedDocument = $null
    $trace.phases.document_close = 'pass'

    $activePhase = 'quit'
    $trace.phases.quit = 'running'
    $hwp.Quit()
    $trace.quit_invoked = $true
    $trace.phases.quit = 'pass'
    $trace.state = 'pass'
}
catch {
    $trace.state = 'failed'
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'RUNTIME_PROBE_CHILD_EXCEPTION' }
    $trace.failed_phase = $activePhase
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    if ($trace.phases.Contains($activePhase)) { $trace.phases[$activePhase] = 'failed' }
}
finally {
    foreach ($candidate in @($reopenedDocument, $document)) {
        if ($null -ne $candidate) {
            try { $null = $candidate.Close($false) } catch { }
            Clear-ComObject -Value $candidate
        }
    }
    Clear-ComObject -Value $documents
    if ($null -ne $hwp) {
        if (-not $trace.quit_invoked) {
            try {
                $hwp.Quit()
                $trace.quit_invoked = $true
                $trace.phases.quit = 'pass'
            }
            catch {
                $trace.phases.quit = 'failed'
            }
        }
        Clear-ComObject -Value $hwp
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
$traceJson = $trace | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($tracePath, $traceJson, $utf8WithoutBom)
if ($trace.state -ne 'pass') { exit 2 }
