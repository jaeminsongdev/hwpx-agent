[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$exactFixtureManifestSha256 = 'b58c3b68d156550512674d894427bc94dcb26d014f687d3e32e8918a37acc363'
if ($ExpectedFixtureManifestSha256 -cne $exactFixtureManifestSha256) {
    throw 'TABLE_AGGREGATE_BATCH_MANIFEST_IDENTITY_MISMATCH'
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

function Get-Sha256String {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
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

    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC).TrimEnd([char]"`n")
}

function ConvertTo-NormalizedVersion {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) { throw 'TABLE_AGGREGATE_BATCH_VERSION_PARSE_FAILED' }
    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
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
        if ($null -eq $progIdKey) { throw 'TABLE_AGGREGATE_BATCH_PROGID_NOT_REGISTERED' }
        $clsidSubKey = $progIdKey.OpenSubKey('CLSID')
        if ($null -eq $clsidSubKey) { throw 'TABLE_AGGREGATE_BATCH_CLSID_MISSING' }
        $clsid = [string]$clsidSubKey.GetValue('')
        $clsidKey = $classesRoot.OpenSubKey("CLSID\$clsid")
        $serverKey = if ($null -ne $clsidKey) { $clsidKey.OpenSubKey('LocalServer32') } else { $null }
        if ($null -eq $serverKey) { throw 'TABLE_AGGREGATE_BATCH_LOCALSERVER32_MISSING' }
        $command = [string]$serverKey.GetValue('')
    }
    finally {
        foreach ($key in @($serverKey, $clsidKey, $clsidSubKey, $progIdKey, $classesRoot)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw 'TABLE_AGGREGATE_BATCH_LOCALSERVER32_PARSE_FAILED' }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path -Force
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Assert-ExactProperties {
    param(
        [Parameter(Mandatory)][object]$Value,
        [Parameter(Mandatory)][string[]]$Expected,
        [Parameter(Mandatory)][string]$ErrorCode
    )

    $observed = @($Value.PSObject.Properties.Name)
    if ($observed.Count -ne $Expected.Count) { throw $ErrorCode }
    foreach ($name in $observed) {
        if ($Expected -cnotcontains $name) { throw $ErrorCode }
    }
}

function Read-ExactFixtureManifest {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedSha256
    )

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 131072) {
        throw 'TABLE_AGGREGATE_BATCH_MANIFEST_NOT_BOUNDED_REGULAR_FILE'
    }
    if ((Get-Sha256File -Path $item.FullName) -cne $ExpectedSha256) {
        throw 'TABLE_AGGREGATE_BATCH_MANIFEST_SHA256_MISMATCH'
    }
    try {
        $manifest = if ($PSVersionTable.PSVersion.Major -ge 7) {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
        }
        else {
            Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    }
    catch { throw 'TABLE_AGGREGATE_BATCH_MANIFEST_JSON_INVALID' }
    Assert-ExactProperties -Value $manifest -Expected @(
        'schema_version', 'source_ancestor_sha256', 'source_file', 'source_sha256',
        'source_section_sha256', 'cases', 'actual_hangul_2020', 'render', 'automation',
        'differential'
    ) -ErrorCode 'TABLE_AGGREGATE_BATCH_MANIFEST_SHAPE_INVALID'
    if ([string]$manifest.schema_version -cne 'hwpx-agent.p06-09-table-aggregate-target-fixture/v1' -or
        -not ($manifest.actual_hangul_2020 -is [bool]) -or [bool]$manifest.actual_hangul_2020 -or
        [string]$manifest.render -cne 'not_run' -or
        [string]$manifest.automation -cne 'not_run' -or
        [string]$manifest.differential -cne 'not_run') {
        throw 'TABLE_AGGREGATE_BATCH_MANIFEST_STATE_INVALID'
    }
    $expectedCases = @(
        @('TABLE-022', 'table.block_sum', 'table-022-block-sum.hwpx'),
        @('TABLE-023', 'table.block_average', 'table-023-block-average.hwpx'),
        @('TABLE-024', 'table.block_product', 'table-024-block-product.hwpx'),
        @('TABLE-026', 'table.vertical_sum', 'table-026-vertical-sum.hwpx'),
        @('TABLE-027', 'table.horizontal_average', 'table-027-horizontal-average.hwpx'),
        @('TABLE-028', 'table.vertical_average', 'table-028-vertical-average.hwpx'),
        @('TABLE-029', 'table.horizontal_product', 'table-029-horizontal-product.hwpx'),
        @('TABLE-030', 'table.vertical_product', 'table-030-vertical-product.hwpx')
    )
    $cases = @($manifest.cases)
    if ($cases.Count -ne $expectedCases.Count) {
        throw 'TABLE_AGGREGATE_BATCH_CASE_SET_INVALID'
    }
    $caseProperties = @(
        'feature_id', 'capability_id', 'file', 'sha256', 'formula', 'unverified_cache',
        'expected_hangul_text_sha256', 'source_state_sha256', 'target_state_sha256',
        'source_grid_sha256', 'target_grid_sha256', 'request_sha256', 'plan_sha256'
    )
    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        Assert-ExactProperties -Value $case -Expected $caseProperties `
            -ErrorCode 'TABLE_AGGREGATE_BATCH_CASE_SHAPE_INVALID'
        if ([string]$case.feature_id -cne $expectedCases[$index][0] -or
            [string]$case.capability_id -cne $expectedCases[$index][1] -or
            [string]$case.file -cne $expectedCases[$index][2] -or
            [string]$case.sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$case.expected_hangul_text_sha256 -notmatch '^[0-9a-f]{64}$') {
            throw 'TABLE_AGGREGATE_BATCH_CASE_BINDING_INVALID'
        }
    }
    return [ordered]@{ item = $item; value = $manifest; expected_cases = $expectedCases }
}

function Get-CasePaths {
    param(
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][object]$Case
    )

    $input = [System.IO.Path]::GetFullPath((Join-Path $Boundary ([string]$Case.file)))
    $stem = [System.IO.Path]::GetFileNameWithoutExtension([string]$Case.file)
    return [ordered]@{
        input = $input
        output = [System.IO.Path]::GetFullPath((Join-Path $Boundary ($stem + '.hancom-2020-readback.hwpx')))
        pdf = [System.IO.Path]::GetFullPath((Join-Path $Boundary ($stem + '.hancom-2020-render.pdf')))
    }
}

function Assert-CaseFiles {
    param(
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][object[]]$Cases
    )

    $paths = @()
    foreach ($case in $Cases) {
        $casePaths = Get-CasePaths -Boundary $Boundary -Case $case
        foreach ($candidate in @($casePaths.input, $casePaths.output, $casePaths.pdf)) {
            if (-not $candidate.StartsWith($Boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
                throw 'TABLE_AGGREGATE_BATCH_PATH_OUTSIDE_FIXTURE_BOUNDARY'
            }
        }
        $inputItem = Get-Item -LiteralPath $casePaths.input -Force
        if ($inputItem.PSIsContainer -or
            ($inputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $inputItem.Length -le 0 -or $inputItem.Length -gt 8388608 -or
            [System.IO.Path]::GetExtension($casePaths.input) -cne '.hwpx' -or
            (Get-Sha256File -Path $casePaths.input) -cne [string]$case.sha256) {
            throw 'TABLE_AGGREGATE_BATCH_INPUT_INVALID'
        }
        foreach ($candidate in @($casePaths.output, $casePaths.pdf)) {
            if (Test-Path -LiteralPath $candidate) {
                throw 'TABLE_AGGREGATE_BATCH_OUTPUT_ALREADY_EXISTS'
            }
        }
        $paths += ,$casePaths
    }
    return $paths
}

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null,
        [ValidateRange(0, 8)][int]$CaseIndex = 0,
        [AllowNull()][string]$FeatureId = $null
    )

    $script:progressSequence += 1
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p06-09-table-aggregate-batch-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        case_index = $CaseIndex
        feature_id = $FeatureId
        phase = $Phase
        state = $State
        raw_document_text_present = $false
    }
    $line = $event | ConvertTo-Json -Compress
    if ($script:progressSequence -eq 1) {
        Write-NewUtf8File -Path $script:progressFile -Content $line
    }
    else {
        $encoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::AppendAllText($script:progressFile, "`n$line", $encoding)
    }
}

function New-CaseResult {
    param([Parameter(Mandatory)][object]$Case)

    return [ordered]@{
        feature_id = [string]$Case.feature_id
        capability_id = [string]$Case.capability_id
        input_sha256 = [string]$Case.sha256
        input_unchanged = $false
        input_text_sha256 = $null
        output_sha256 = $null
        output_text_sha256 = $null
        output_saved = $false
        render_pdf_requested = $true
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

$manifestRecord = Read-ExactFixtureManifest `
    -Path $FixtureManifestPath `
    -ExpectedSha256 $ExpectedFixtureManifestSha256
$manifestFile = $manifestRecord.item.FullName
$boundary = (Resolve-Path -LiteralPath (Split-Path -Parent $manifestFile)).Path.TrimEnd('\')
$boundaryItem = Get-Item -LiteralPath $boundary -Force
if (($boundaryItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'TABLE_AGGREGATE_BATCH_FIXTURE_BOUNDARY_REPARSE_POINT'
}
$traceFile = [System.IO.Path]::GetFullPath($TracePath)
$script:progressFile = [System.IO.Path]::GetFullPath($ProgressPath)
foreach ($candidate in @($traceFile, $script:progressFile)) {
    if (-not $candidate.StartsWith($boundary + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'TABLE_AGGREGATE_BATCH_PATH_OUTSIDE_FIXTURE_BOUNDARY'
    }
    if (Test-Path -LiteralPath $candidate) {
        throw 'TABLE_AGGREGATE_BATCH_OUTPUT_ALREADY_EXISTS'
    }
}
$cases = @($manifestRecord.value.cases)
$casePaths = @(Assert-CaseFiles -Boundary $boundary -Cases $cases)
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'TABLE_AGGREGATE_BATCH_PREEXISTING_HWP_PROCESS'
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($identity.file_version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw 'TABLE_AGGREGATE_BATCH_TARGET_IDENTITY_MISMATCH'
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.p06-09-hancom-2020-table-aggregate-target-batch-engine/v1'
    state = 'failed'
    target = [ordered]@{
        prog_id = $ProgId
        registry_view = 'Registry32'
        client = 'windows_powershell_x86_sta'
        file_version = $identity.file_version
        executable_sha256 = $identity.sha256
    }
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    case_count = $cases.Count
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
$phase = 'com_create'
$activeIndex = 0
$activeFeature = $null
$activeResult = $null
$hwpProcessId = $null
$script:progressSequence = 0
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'TABLE_AGGREGATE_BATCH_CLIENT_NOT_STA'
    }
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne $ExpectedBuild) {
        throw 'TABLE_AGGREGATE_BATCH_AUTOMATION_VERSION_MISMATCH'
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -eq 1) { $hwpProcessId = [int]$hwpProcesses[0].ProcessId }
    Write-ProgressEvent -Phase 'com_create' -State 'pass' -HwpProcessId $hwpProcessId

    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $result.window_visible_for_user_access = $true

    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        $paths = $casePaths[$index]
        $activeIndex = $index + 1
        $activeFeature = [string]$case.feature_id
        $activeResult = New-CaseResult -Case $case
        $result.cases += ,$activeResult

        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'TABLE_AGGREGATE_BATCH_DOCUMENT_ADD_FAILED' }

        $phase = 'open_input'
        $activeResult.phases.open_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        if ($document.Open($paths.input, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'TABLE_AGGREGATE_BATCH_INPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.open_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'read_input'
        $activeResult.phases.read_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        $inputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
        $activeResult.input_text_sha256 = Get-Sha256String -Value $inputText
        if ($activeResult.input_text_sha256 -cne [string]$case.expected_hangul_text_sha256) {
            throw 'TABLE_AGGREGATE_BATCH_INPUT_TEXT_MISMATCH'
        }
        $activeResult.phases.read_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'save_as_hwpx'
        $activeResult.phases.save_as_hwpx = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        [void]$document.SaveAs($paths.output, 'HWPX', '')
        if (-not (Test-Path -LiteralPath $paths.output -PathType Leaf)) {
            throw 'TABLE_AGGREGATE_BATCH_SAVE_OUTPUT_MISSING'
        }
        $activeResult.output_saved = $true
        $activeResult.output_sha256 = Get-Sha256File -Path $paths.output
        $activeResult.phases.save_as_hwpx = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'close_input'
        $activeResult.phases.close_input = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'reopen_output'
        $activeResult.phases.reopen_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        $document = $documents.Add($false)
        if ($null -eq $document) { throw 'TABLE_AGGREGATE_BATCH_REOPEN_DOCUMENT_ADD_FAILED' }
        if ($document.Open($paths.output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw 'TABLE_AGGREGATE_BATCH_OUTPUT_OPEN_RETURNED_FALSE'
        }
        [void]$document.SetActive_XHwpDocument()
        $activeResult.phases.reopen_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'read_output'
        $activeResult.phases.read_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        $outputText = ConvertTo-CanonicalText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
        $activeResult.output_text_sha256 = Get-Sha256String -Value $outputText
        if ($activeResult.output_text_sha256 -cne [string]$case.expected_hangul_text_sha256) {
            throw 'TABLE_AGGREGATE_BATCH_OUTPUT_TEXT_MISMATCH'
        }
        $activeResult.phases.read_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'export_pdf'
        $activeResult.phases.export_pdf = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        $activeResult.render_pdf_export_method = 'IXHwpDocument.SaveAs/PDF'
        [void]$document.SaveAs($paths.pdf, 'PDF', '')
        if (-not (Test-Path -LiteralPath $paths.pdf -PathType Leaf)) {
            throw 'TABLE_AGGREGATE_BATCH_PDF_EXPORT_OUTPUT_MISSING'
        }
        $pdfItem = Get-Item -LiteralPath $paths.pdf -Force
        if ($pdfItem.PSIsContainer -or
            ($pdfItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $pdfItem.Length -lt 5 -or $pdfItem.Length -gt 33554432) {
            throw 'TABLE_AGGREGATE_BATCH_PDF_NOT_BOUNDED_REGULAR_FILE'
        }
        $pdfStream = [System.IO.File]::OpenRead($paths.pdf)
        try {
            $signature = [byte[]]::new(5)
            if ($pdfStream.Read($signature, 0, $signature.Length) -ne $signature.Length -or
                [System.Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
                throw 'TABLE_AGGREGATE_BATCH_PDF_SIGNATURE_MISMATCH'
            }
        }
        finally { $pdfStream.Dispose() }
        $activeResult.render_pdf_saved = $true
        $activeResult.render_pdf_sha256 = Get-Sha256File -Path $paths.pdf
        $activeResult.render_pdf_bytes = [long]$pdfItem.Length
        $activeResult.render_pdf_signature_valid = $true
        $activeResult.phases.export_pdf = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $phase = 'close_output'
        $activeResult.phases.close_output = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        $activeResult.phases.close_output = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex $activeIndex -FeatureId $activeFeature

        $activeResult.input_unchanged = (Get-Sha256File -Path $paths.input) -ceq [string]$case.sha256
        if (-not $activeResult.input_unchanged) { throw 'TABLE_AGGREGATE_BATCH_INPUT_CHANGED' }
        $result.completed_case_count += 1
    }

    $phase = 'quit'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $hwp.Quit()
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
    $result.state = 'pass'
}
catch {
    $result.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'TABLE_AGGREGATE_BATCH_EXCEPTION' }
    $result.failed_feature_id = $activeFeature
    $result.failed_phase = $phase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    if ($null -ne $activeResult -and $activeResult.phases.Contains($phase)) {
        $activeResult.phases[$phase] = 'failed'
        $activeResult.error_code = $result.error_code
        $activeResult.failed_phase = $phase
    }
    Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId `
        -CaseIndex $activeIndex -FeatureId $activeFeature
}
finally {
    if ($null -ne $document) {
        try { [void]$document.Close($false) } catch { }
        Clear-ComObject -Value $document
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
            $result.cases[$index].input_unchanged =
                (Get-Sha256File -Path $casePaths[$index].input) -ceq [string]$cases[$index].sha256
        }
        catch { $result.cases[$index].input_unchanged = $false }
    }
}

Write-ProgressEvent -Phase 'terminal' -State $(if ($result.state -eq 'pass') { 'pass' } else { 'failed' }) `
    -HwpProcessId $hwpProcessId -CaseIndex $activeIndex -FeatureId $activeFeature
Write-NewUtf8File -Path $traceFile -Content ($result | ConvertTo-Json -Depth 10)
$result | ConvertTo-Json -Depth 10
if ($result.state -ne 'pass') { exit 2 }
