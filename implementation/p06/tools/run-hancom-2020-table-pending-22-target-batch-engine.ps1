[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$MergeSplitManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedMergeSplitManifestSha256,
    [Parameter(Mandatory)][string]$LayoutPlacementManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedLayoutPlacementManifestSha256,
    [Parameter(Mandatory)][string]$RemainingManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedRemainingManifestSha256,
    [Parameter(Mandatory)][string]$AccessControlPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedAccessControlSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedManifestSha256 = [ordered]@{
    merge_split = '682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97'
    layout_placement = '33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf'
    remaining = '1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e'
}
$expectedManifestSchema = [ordered]@{
    merge_split = 'hwpx-agent.p06-09-table-merge-split-target-fixture/v1'
    layout_placement = 'hwpx-agent.p06-09-table-layout-placement-target-fixture/v1'
    remaining = 'hwpx-agent.p06-09-table-remaining-target-fixture/v1'
}
$layoutTextSha256 = 'e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91'
$pinnedAccessControlSha256 =
    '04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c'
$expectedCases = [ordered]@{
    merge_split = @(
        @('table-016-split-cells-4x3', 'TABLE-016', 'table.split_cell',
            'table-016-split-cells-4x3.hwpx'),
        @('table-017-merge-cells-4x3', 'TABLE-017', 'table.merge_cells',
            'table-017-merge-cells-4x3.hwpx')
    )
    layout_placement = @(
        @('table-018-equal-row-height-4x3', 'TABLE-018', 'table.equal_row_height',
            'table-018-equal-row-height-4x3.hwpx'),
        @('table-019-equal-column-width-4x3', 'TABLE-019', 'table.equal_column_width',
            'table-019-equal-column-width-4x3.hwpx'),
        @('table-050-row-min-height-4x3', 'TABLE-050', 'table.row_min_height',
            'table-050-row-min-height-4x3.hwpx'),
        @('table-051-column-fixed-width-4x3', 'TABLE-051', 'table.column_fixed_width',
            'table-051-column-fixed-width-4x3.hwpx'),
        @('table-052-autofit-content-4x3', 'TABLE-052', 'table.autofit_content',
            'table-052-autofit-content-4x3.hwpx'),
        @('table-053-autofit-page-4x3', 'TABLE-053', 'table.autofit_page',
            'table-053-autofit-page-4x3.hwpx'),
        @('table-034-position-4x3', 'TABLE-034', 'table.position',
            'table-034-position-4x3.hwpx'),
        @('table-036-inline-floating-4x3', 'TABLE-036', 'table.inline_floating',
            'table-036-inline-floating-4x3.hwpx'),
        @('table-037-wrap-4x3', 'TABLE-037', 'table.wrap',
            'table-037-wrap-4x3.hwpx'),
        @('table-038-outer-margin-4x3', 'TABLE-038', 'table.outer_margin',
            'table-038-outer-margin-4x3.hwpx')
    )
    remaining = @(
        @('table-020-style', 'TABLE-020', 'table.table_style', 'table-020-style.hwpx'),
        @('table-021-transpose', 'TABLE-021', 'table.transpose', 'table-021-transpose.hwpx'),
        @('table-032-thousands-add', 'TABLE-032', 'table.thousands_add',
            'table-032-thousands-add.hwpx'),
        @('table-033-thousands-remove', 'TABLE-033', 'table.thousands_remove',
            'table-033-thousands-remove.hwpx'),
        @('table-049-number-format', 'TABLE-049', 'table.number_format',
            'table-049-number-format.hwpx'),
        @('table-054-nested-table', 'TABLE-054', 'table.nested_table',
            'table-054-nested-table.hwpx'),
        @('table-056-sort', 'TABLE-056', 'table.sort_cells', 'table-056-sort.hwpx'),
        @('table-057-auto-fill', 'TABLE-057', 'table.auto_fill',
            'table-057-auto-fill.hwpx'),
        @('table-058-auto-fill-series', 'TABLE-058', 'table.auto_fill_series',
            'table-058-auto-fill-series.hwpx'),
        @('table-060-absolute-reference', 'TABLE-060', 'table.formula_absolute_ref',
            'table-060-absolute-reference.hwpx')
    )
}

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($stream) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) |
            ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $algorithm.Dispose() }
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function ConvertTo-CanonicalText {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $normalized = $Value.Replace([char]0, '')
    $lineFeed = [string][char]10
    $normalized = $normalized.Replace(
        [Environment]::NewLine,
        $lineFeed
    ).Replace([string][char]13, $lineFeed)
    return $normalized.Normalize(
        [System.Text.NormalizationForm]::FormC
    ).TrimEnd([char]10)
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) {
        throw 'TABLE_PENDING_22_BATCH_VERSION_PARSE_FAILED'
    }
    $components = @('major', 'minor', 'build', 'revision') |
        ForEach-Object { [uint32]$match.Groups[$_].Value }
    return ($components -join '.')
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and
        [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)

    $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $progIdKey = $null
    $clsidSubKey = $null
    $clsidKey = $null
    $serverKey = $null
    try {
        $progIdKey = $classesRoot.OpenSubKey($RequestedProgId)
        if ($null -eq $progIdKey) {
            throw 'TABLE_PENDING_22_BATCH_PROGID_NOT_REGISTERED'
        }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) {
            throw 'TABLE_PENDING_22_BATCH_CLSID_MISSING'
        }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $serverKey = if ($null -ne $clsidKey) {
            $clsidKey.OpenSubKey('LocalServer32')
        }
        else { $null }
        if ($null -eq $serverKey) {
            throw 'TABLE_PENDING_22_BATCH_LOCALSERVER32_MISSING'
        }
        $command = [string]$serverKey.GetValue('')
    }
    finally {
        foreach ($key in @(
            $serverKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot
        )) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) {
        throw 'TABLE_PENDING_22_BATCH_LOCALSERVER32_PARSE_FAILED'
    }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path -Force
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Assert-UnderTargetRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith(
        $TargetRoot + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'TABLE_PENDING_22_BATCH_PATH_OUTSIDE_TARGET_ROOT'
    }
    return $full
}

function Read-ExactManifest {
    param(
        [Parameter(Mandatory)][string]$GroupId,
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    if ($ExpectedSha256 -cne [string]$expectedManifestSha256[$GroupId]) {
        throw 'TABLE_PENDING_22_BATCH_MANIFEST_IDENTITY_MISMATCH'
    }
    $fullPath = Assert-UnderTargetRoot -Path $Path -TargetRoot $TargetRoot
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt 1048576 -or
        (Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_PENDING_22_BATCH_MANIFEST_INVALID'
    }
    try {
        $manifest = Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        throw 'TABLE_PENDING_22_BATCH_MANIFEST_JSON_INVALID'
    }
    if ([string]$manifest.schema_version -cne
            [string]$expectedManifestSchema[$GroupId] -or
        -not ($manifest.actual_hangul_2020 -is [bool]) -or
        [bool]$manifest.actual_hangul_2020 -or
        [string]$manifest.render -cne 'not_run' -or
        [string]$manifest.automation -cne 'not_run' -or
        [string]$manifest.differential -cne 'not_run') {
        throw 'TABLE_PENDING_22_BATCH_MANIFEST_STATE_INVALID'
    }
    $bindings = @($expectedCases[$GroupId])
    $cases = @($manifest.cases)
    if ($cases.Count -ne $bindings.Count) {
        throw 'TABLE_PENDING_22_BATCH_CASE_SET_INVALID'
    }
    $directory = (Resolve-Path -LiteralPath (
        Split-Path -Parent $item.FullName
    )).Path.TrimEnd('\')
    $directoryItem = Get-Item -LiteralPath $directory -Force
    if (($directoryItem.Attributes -band
            [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'TABLE_PENDING_22_BATCH_FIXTURE_BOUNDARY_REPARSE_POINT'
    }
    $prepared = @()
    for ($index = 0; $index -lt $bindings.Count; $index += 1) {
        $case = $cases[$index]
        $binding = $bindings[$index]
        if ([string]$case.case_id -cne $binding[0] -or
            [string]$case.feature_id -cne $binding[1] -or
            [string]$case.capability_id -cne $binding[2] -or
            [string]$case.file -cne $binding[3] -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$') {
            throw 'TABLE_PENDING_22_BATCH_CASE_BINDING_INVALID'
        }
        $inputPath = Assert-UnderTargetRoot -Path (
            Join-Path $directory ([string]$case.file)
        ) -TargetRoot $TargetRoot
        $outputPath = Assert-UnderTargetRoot -Path (
            Join-Path $directory ([string]$case.case_id + '.hancom-2020-readback.hwpx')
        ) -TargetRoot $TargetRoot
        $pdfPath = Assert-UnderTargetRoot -Path (
            Join-Path $directory ([string]$case.case_id + '.hancom-2020-render.pdf')
        ) -TargetRoot $TargetRoot
        $inputItem = Get-Item -LiteralPath $inputPath -Force
        if ($inputItem.PSIsContainer -or
            ($inputItem.Attributes -band
                [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $inputItem.Length -le 0 -or
            $inputItem.Length -gt 8388608 -or
            [System.IO.Path]::GetExtension($inputPath) -cne '.hwpx' -or
            (Get-Sha256File -Path $inputPath) -cne [string]$case.sha256) {
            throw 'TABLE_PENDING_22_BATCH_INPUT_INVALID'
        }
        foreach ($candidate in @($outputPath, $pdfPath)) {
            if (Test-Path -LiteralPath $candidate) {
                throw 'TABLE_PENDING_22_BATCH_OUTPUT_ALREADY_EXISTS'
            }
        }
        $prepared += [ordered]@{
            group_id = $GroupId
            group_case_index = $index + 1
            case_id = [string]$case.case_id
            feature_id = [string]$case.feature_id
            capability_id = [string]$case.capability_id
            manifest_sha256 = $ExpectedSha256
            input_file = [string]$case.file
            input_path = $inputPath
            input_sha256 = [string]$case.sha256
            expected_text_sha256 = if ($GroupId -ceq 'layout_placement') {
                $layoutTextSha256
            }
            else { $null }
            output_path = $outputPath
            pdf_path = $pdfPath
        }
    }
    return $prepared
}

function Resolve-ExactAccessControl {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    if ($ExpectedSha256 -cne $pinnedAccessControlSha256) {
        throw 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_IDENTITY_MISMATCH'
    }
    $fullPath = Assert-UnderTargetRoot -Path $Path -TargetRoot $TargetRoot
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or
        $item.Length -gt 8388608 -or
        [System.IO.Path]::GetExtension($item.FullName) -cne '.hwpx' -or
        (Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_INVALID'
    }
    return [ordered]@{
        path = $item.FullName
        file = $item.Name
        sha256 = $ExpectedSha256
    }
}

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')]
        [string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null,
        [ValidateRange(0, 22)][int]$GlobalCaseIndex = 0,
        [ValidateRange(0, 10)][int]$GroupCaseIndex = 0,
        [AllowNull()][string]$GroupId = $null,
        [AllowNull()][string]$FeatureId = $null
    )

    $script:progressSequence += 1
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-pending-22-batch-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        global_case_index = $GlobalCaseIndex
        group_case_index = $GroupCaseIndex
        group_id = if ([string]::IsNullOrEmpty($GroupId)) { $null } else { $GroupId }
        feature_id = if ([string]::IsNullOrEmpty($FeatureId)) { $null } else { $FeatureId }
        phase = $Phase
        state = $State
        raw_document_text_present = $false
    }
    $line = $event | ConvertTo-Json -Compress
    if ($script:progressSequence -eq 1) {
        Write-NewUtf8File -Path $script:progressFile -Content $line
    }
    else {
        [System.IO.File]::AppendAllText(
            $script:progressFile,
            [Environment]::NewLine + $line,
            [System.Text.UTF8Encoding]::new($false)
        )
    }
}

function New-CaseResult {
    param([Parameter(Mandatory)][object]$Entry)

    return [ordered]@{
        group_id = [string]$Entry.group_id
        group_case_index = [int]$Entry.group_case_index
        case_id = [string]$Entry.case_id
        feature_id = [string]$Entry.feature_id
        capability_id = [string]$Entry.capability_id
        manifest_sha256 = [string]$Entry.manifest_sha256
        input_file = [string]$Entry.input_file
        input_sha256 = [string]$Entry.input_sha256
        input_unchanged = $false
        expected_text_source = if ($null -ne $Entry.expected_text_sha256) {
            'fixture_contract'
        }
        else { 'same_session_input_readback' }
        input_text_sha256 = $null
        output_file = [System.IO.Path]::GetFileName([string]$Entry.output_path)
        output_sha256 = $null
        output_text_sha256 = $null
        output_saved = $false
        render_pdf_file = [System.IO.Path]::GetFileName([string]$Entry.pdf_path)
        render_pdf_saved = $false
        render_pdf_sha256 = $null
        render_pdf_bytes = $null
        render_pdf_signature_valid = $false
        render_pdf_export_method = $null
        phases = [ordered]@{
            open_input = 'not_run'
            read_input = 'not_run'
            save_as_hwpx = 'not_run'
            close_input = 'not_run'
            reopen_output = 'not_run'
            read_output = 'not_run'
            export_pdf = 'not_run'
            close_output = 'not_run'
        }
        error_code = $null
        failed_phase = $null
    }
}

$repoRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '..\..\..'
)).Path.TrimEnd('\')
$targetRoot = (Resolve-Path -LiteralPath (
    Join-Path $repoRoot 'fixtures\target-build'
)).Path.TrimEnd('\')
$traceFile = Assert-UnderTargetRoot -Path $TracePath -TargetRoot $targetRoot
$script:progressFile = Assert-UnderTargetRoot -Path $ProgressPath -TargetRoot $targetRoot
foreach ($candidate in @($traceFile, $script:progressFile)) {
    $parent = Split-Path -Parent $candidate
    if (-not [System.IO.Directory]::Exists($parent)) {
        throw 'TABLE_PENDING_22_BATCH_TRACE_PARENT_MISSING'
    }
    $parentItem = Get-Item -LiteralPath $parent -Force
    if (($parentItem.Attributes -band
            [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        (Test-Path -LiteralPath $candidate)) {
        throw 'TABLE_PENDING_22_BATCH_TRACE_PATH_INVALID'
    }
}

$allCases = @()
$allCases += @(Read-ExactManifest -GroupId 'merge_split' -Path (
    $MergeSplitManifestPath
) -ExpectedSha256 $ExpectedMergeSplitManifestSha256 -TargetRoot $targetRoot)
$allCases += @(Read-ExactManifest -GroupId 'layout_placement' -Path (
    $LayoutPlacementManifestPath
) -ExpectedSha256 $ExpectedLayoutPlacementManifestSha256 -TargetRoot $targetRoot)
$allCases += @(Read-ExactManifest -GroupId 'remaining' -Path (
    $RemainingManifestPath
) -ExpectedSha256 $ExpectedRemainingManifestSha256 -TargetRoot $targetRoot)
$accessControl = Resolve-ExactAccessControl -Path $AccessControlPath `
    -ExpectedSha256 $ExpectedAccessControlSha256 -TargetRoot $targetRoot
if ($allCases.Count -ne 22) {
    throw 'TABLE_PENDING_22_BATCH_TOTAL_CASE_COUNT_INVALID'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TABLE_PENDING_22_BATCH_PREEXISTING_HWP_PROCESS'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'TABLE_PENDING_22_BATCH_TARGET_IDENTITY_MISMATCH'
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-pending-22-target-batch-engine/v1'
    state = 'failed'
    target = [ordered]@{
        prog_id = $ProgId
        registry_view = 'Registry32'
        client = 'windows_powershell_x86_sta'
        file_version = $identity.file_version
        executable_sha256 = $identity.sha256
    }
    session_strategy = 'single_hwp_process_for_22_cases'
    access_approval_strategy = 'user_selects_allow_all_once'
    access_control = [ordered]@{
        source = 'verified_hancom_saved_table_012_control'
        input_file = [string]$accessControl.file
        input_sha256 = [string]$accessControl.sha256
        input_unchanged = $false
        retry_policy = 'one_same_session_retry_after_first_false'
        open_attempt_count = 0
        first_open_returned_false = $false
        open_state = 'not_run'
        close_state = 'not_run'
    }
    manifest_sha256 = [ordered]@{
        merge_split = $ExpectedMergeSplitManifestSha256
        layout_placement = $ExpectedLayoutPlacementManifestSha256
        remaining = $ExpectedRemainingManifestSha256
    }
    case_count = 22
    completed_case_count = 0
    cases = @()
    failed_feature_id = $null
    error_code = $null
    failed_phase = $null
    exception_type = $null
    exception_hresult = $null
    raw_document_text_present = $false
    user_document_scanned = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    window_visible_for_user_access = $false
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$hwpProcessId = $null
$activeEntry = $null
$activeResult = $null
$activeIndex = 0
$phase = 'com_create'
$script:progressSequence = 0
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne
        [Threading.ApartmentState]::STA) {
        throw 'TABLE_PENDING_22_BATCH_CLIENT_NOT_STA'
    }
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne
        $ExpectedBuild) {
        throw 'TABLE_PENDING_22_BATCH_AUTOMATION_VERSION_MISMATCH'
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -eq 1) {
        $hwpProcessId = [int]$hwpProcesses[0].ProcessId
    }
    Write-ProgressEvent -Phase 'com_create' -State 'pass' -HwpProcessId $hwpProcessId

    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $result.window_visible_for_user_access = $true

    $phase = 'access_control_open'
    $document = $documents.Add($false)
    if ($null -eq $document) {
        throw 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_DOCUMENT_ADD_FAILED'
    }
    $result.access_control.open_state = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $result.access_control.open_attempt_count = 1
    $accessControlOpened = $document.Open(
        [string]$accessControl.path,
        'HWPX',
        'lock:false;setcurdir:false'
    )
    if ($accessControlOpened -eq $false) {
        $result.access_control.first_open_returned_false = $true
        $phase = 'access_control_open_retry'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
        Start-Sleep -Milliseconds 250
        $result.access_control.open_attempt_count = 2
        if ($document.Open(
            [string]$accessControl.path,
            'HWPX',
            'lock:false;setcurdir:false'
        ) -eq $false) {
            throw 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_RETRY_RETURNED_FALSE'
        }
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
        $phase = 'access_control_open'
    }
    [void]$document.SetActive_XHwpDocument()
    $result.access_control.open_state = 'pass'
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    $phase = 'access_control_close'
    $result.access_control.close_state = 'running'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    [void]$document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $result.access_control.close_state = 'pass'
    $result.access_control.input_unchanged = (
        Get-Sha256File -Path ([string]$accessControl.path)
    ) -ceq [string]$accessControl.sha256
    if (-not $result.access_control.input_unchanged) {
        throw 'TABLE_PENDING_22_BATCH_ACCESS_CONTROL_CHANGED'
    }
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId

    for ($index = 0; $index -lt $allCases.Count; $index += 1) {
        $activeEntry = $allCases[$index]
        $activeIndex = $index + 1
        $activeResult = New-CaseResult -Entry $activeEntry
        $result.cases += ,$activeResult

        $document = $documents.Add($false)
        if ($null -eq $document) {
            throw 'TABLE_PENDING_22_BATCH_DOCUMENT_ADD_FAILED'
        }

        $phase = 'open_input'
        $activeResult.phases.open_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        if ($document.Open(
            [string]$activeEntry.input_path,
            'HWPX',
            'lock:false;setcurdir:false'
        ) -eq $false) {
            throw 'TABLE_PENDING_22_BATCH_INPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.open_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'read_input'
        $activeResult.phases.read_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        $inputText = ConvertTo-CanonicalText -Value (
            [string]$hwp.GetTextFile('UNICODE', '')
        )
        $activeResult.input_text_sha256 = Get-Sha256String -Value $inputText
        if ($null -ne $activeEntry.expected_text_sha256 -and
            [string]$activeResult.input_text_sha256 -cne
                [string]$activeEntry.expected_text_sha256) {
            throw 'TABLE_PENDING_22_BATCH_INPUT_TEXT_MISMATCH'
        }
        $activeResult.phases.read_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'save_as_hwpx'
        $activeResult.phases.save_as_hwpx = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        [void]$document.SaveAs(
            [string]$activeEntry.output_path,
            'HWPX',
            ''
        )
        if (-not (Test-Path -LiteralPath (
            [string]$activeEntry.output_path
        ) -PathType Leaf)) {
            throw 'TABLE_PENDING_22_BATCH_SAVE_OUTPUT_MISSING'
        }
        $activeResult.output_saved = $true
        $activeResult.output_sha256 = Get-Sha256File -Path (
            [string]$activeEntry.output_path
        )
        $activeResult.phases.save_as_hwpx = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'close_input'
        $activeResult.phases.close_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'reopen_output'
        $activeResult.phases.reopen_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        $document = $documents.Add($false)
        if ($null -eq $document -or
            $document.Open(
                [string]$activeEntry.output_path,
                'HWPX',
                'lock:false;setcurdir:false'
            ) -eq $false) {
            throw 'TABLE_PENDING_22_BATCH_OUTPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.reopen_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'read_output'
        $activeResult.phases.read_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        $outputText = ConvertTo-CanonicalText -Value (
            [string]$hwp.GetTextFile('UNICODE', '')
        )
        $activeResult.output_text_sha256 = Get-Sha256String -Value $outputText
        if ([string]$activeResult.output_text_sha256 -cne
            [string]$activeResult.input_text_sha256) {
            throw 'TABLE_PENDING_22_BATCH_OUTPUT_TEXT_MISMATCH'
        }
        $activeResult.phases.read_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'export_pdf'
        $activeResult.phases.export_pdf = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        $activeResult.render_pdf_export_method = 'IXHwpDocument.SaveAs/PDF'
        [void]$document.SaveAs([string]$activeEntry.pdf_path, 'PDF', '')
        $pdfItem = Get-Item -LiteralPath ([string]$activeEntry.pdf_path) -Force
        if ($pdfItem.PSIsContainer -or
            ($pdfItem.Attributes -band
                [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $pdfItem.Length -lt 5 -or
            $pdfItem.Length -gt 33554432) {
            throw 'TABLE_PENDING_22_BATCH_PDF_NOT_BOUNDED_REGULAR_FILE'
        }
        $pdfStream = [System.IO.File]::OpenRead($pdfItem.FullName)
        try {
            $signature = [byte[]]::new(5)
            if ($pdfStream.Read($signature, 0, 5) -ne 5 -or
                [System.Text.Encoding]::ASCII.GetString($signature) -cne
                    '%PDF-') {
                throw 'TABLE_PENDING_22_BATCH_PDF_SIGNATURE_MISMATCH'
            }
        }
        finally { $pdfStream.Dispose() }
        $activeResult.render_pdf_saved = $true
        $activeResult.render_pdf_sha256 = Get-Sha256File -Path $pdfItem.FullName
        $activeResult.render_pdf_bytes = [long]$pdfItem.Length
        $activeResult.render_pdf_signature_valid = $true
        $activeResult.phases.export_pdf = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)

        $phase = 'close_output'
        $activeResult.phases.close_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_output = 'pass'
        $activeResult.input_unchanged = (
            Get-Sha256File -Path ([string]$activeEntry.input_path)
        ) -ceq [string]$activeEntry.input_sha256
        if (-not $activeResult.input_unchanged) {
            throw 'TABLE_PENDING_22_BATCH_INPUT_CHANGED'
        }
        $result.completed_case_count += 1
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex ([int]$activeEntry.group_case_index) -GroupId ([string]$activeEntry.group_id) -FeatureId ([string]$activeEntry.feature_id)
    }

    $phase = 'quit'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $hwp.Quit()
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
    $result.state = 'pass'
}
catch {
    $result.failed_feature_id = if ($null -eq $activeEntry) {
        $null
    }
    else { [string]$activeEntry.feature_id }
    $result.error_code = if ([string]$_.Exception.Message -match
        '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_PENDING_22_BATCH_EXCEPTION' }
    $result.failed_phase = $phase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    if ($null -ne $activeResult) {
        if ($activeResult.phases.Contains($phase)) {
            $activeResult.phases[$phase] = 'failed'
        }
        $activeResult.error_code = $result.error_code
        $activeResult.failed_phase = $phase
    }
    if ($phase -ceq 'access_control_open' -or
        $phase -ceq 'access_control_open_retry') {
        $result.access_control.open_state = 'failed'
    }
    elseif ($phase -ceq 'access_control_close') {
        $result.access_control.close_state = 'failed'
    }
    Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId -GlobalCaseIndex $activeIndex -GroupCaseIndex $(if ($null -eq $activeEntry) { 0 } else { [int]$activeEntry.group_case_index }) -GroupId $(if ($null -eq $activeEntry) { $null } else { [string]$activeEntry.group_id }) -FeatureId $(if ($null -eq $activeEntry) { $null } else { [string]$activeEntry.feature_id })
}
finally {
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
        Clear-ComObject -Value $document
        $document = $null
    }
    Clear-ComObject -Value $documents
    Clear-ComObject -Value $window
    if ($null -ne $hwp -and $result.state -ne 'pass') {
        try { $hwp.Quit() } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    for ($index = 0; $index -lt $result.cases.Count; $index += 1) {
        try {
            $result.cases[$index].input_unchanged = (
                Get-Sha256File -Path ([string]$allCases[$index].input_path)
            ) -ceq [string]$allCases[$index].input_sha256
        }
        catch { $result.cases[$index].input_unchanged = $false }
    }
    try {
        $result.access_control.input_unchanged = (
            Get-Sha256File -Path ([string]$accessControl.path)
        ) -ceq [string]$accessControl.sha256
    }
    catch { $result.access_control.input_unchanged = $false }
}

Write-ProgressEvent -Phase 'terminal' -State $(if (
    $result.state -eq 'pass'
) { 'pass' } else { 'failed' }) -HwpProcessId $hwpProcessId
Write-NewUtf8File -Path $traceFile -Content (
    $result | ConvertTo-Json -Depth 12
)
$result | ConvertTo-Json -Depth 12
if ($result.state -ne 'pass') { exit 2 }
exit 0
