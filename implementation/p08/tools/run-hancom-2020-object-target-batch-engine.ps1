[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FixtureManifestPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedFixtureManifestSha256,
    [Parameter(Mandatory)][string]$RunDirectory,
    [Parameter(Mandatory)][string]$TracePath,
    [Parameter(Mandatory)][string]$ProgressPath,
    [string]$ProgId = 'HWPFrame.HwpObject.2',
    [string]$ExpectedBuild = '11.0.0.9136',
    [string]$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$errorPrefix = 'OBJECT_TARGET_BATCH'
$exactManifestSha256 = '2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b'
$expectedFeatures = @(
    'OBJ-001', 'OBJ-002', 'OBJ-007', 'OBJ-042', 'OBJ-015', 'OBJ-016',
    'OBJ-017', 'OBJ-018', 'OBJ-032', 'OBJ-033', 'OBJ-020', 'OBJ-021',
    'OBJ-022', 'OBJ-023', 'OBJ-024', 'OBJ-026', 'OBJ-027', 'OBJ-028',
    'OBJ-029', 'OBJ-034', 'OBJ-035', 'OBJ-019', 'OBJ-025', 'OBJ-030',
    'OBJ-043', 'OBJ-045', 'OBJ-046', 'OBJ-047', 'OBJ-048', 'OBJ-013',
    'OBJ-012', 'OBJ-003', 'OBJ-014', 'OBJ-036',
    'OBJ-037', 'OBJ-038', 'OBJ-039', 'OBJ-040', 'OBJ-041', 'OBJ-031',
    'OBJ-010'
)
$representativeRetryFeatures = @('OBJ-002', 'OBJ-024', 'OBJ-010')
$securityModuleName = 'FilePathCheckerModuleExample'
$securityModuleSha256 = '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'
$securityModulePath = Join-Path (
    [System.Environment]::GetFolderPath('LocalApplicationData')
) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
$securityModuleRegistryPath =
    'Registry::HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules'

if ($ExpectedFixtureManifestSha256 -cne $exactManifestSha256) {
    throw ($errorPrefix + '_MANIFEST_IDENTITY_MISMATCH')
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
    if (-not $match.Success) { throw ($errorPrefix + '_VERSION_PARSE_FAILED') }
    return ((@('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }) -join '.')
}

function Clear-ComObject {
    param([AllowNull()][object]$Value)

    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value) }
        catch { }
    }
}

function Get-ComServerIdentity {
    param([Parameter(Mandatory)][string]$RequestedProgId)

    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::ClassesRoot,
        [Microsoft.Win32.RegistryView]::Registry32
    )
    $prog = $null
    $clsidNode = $null
    $clsidKey = $null
    $server = $null
    try {
        $prog = $root.OpenSubKey($RequestedProgId)
        if ($null -eq $prog) { throw ($errorPrefix + '_PROGID_NOT_REGISTERED') }
        $clsidNode = $prog.OpenSubKey('CLSID')
        if ($null -eq $clsidNode) { throw ($errorPrefix + '_CLSID_MISSING') }
        $clsid = [string]$clsidNode.GetValue('')
        $clsidKey = $root.OpenSubKey("CLSID\$clsid")
        $server = if ($null -ne $clsidKey) {
            $clsidKey.OpenSubKey('LocalServer32')
        }
        else { $null }
        if ($null -eq $server) { throw ($errorPrefix + '_LOCALSERVER32_MISSING') }
        $command = [string]$server.GetValue('')
    }
    finally {
        foreach ($key in @($server, $clsidKey, $clsidNode, $prog, $root)) {
            if ($null -ne $key) { $key.Dispose() }
        }
    }
    $match = [regex]::Match(
        $command.Trim(),
        '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw ($errorPrefix + '_LOCALSERVER32_PARSE_FAILED') }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    $item = Get-Item -LiteralPath $path -Force
    return [ordered]@{
        path = $path
        file_version = [string]$item.VersionInfo.FileVersion
        sha256 = Get-Sha256File -Path $path
    }
}

function Assert-RegularFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$MaximumBytes,
        [Parameter(Mandatory)][string]$Code
    )

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt $MaximumBytes) {
        throw $Code
    }
    return $item
}

function Assert-PathInside {
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Boundary,
        [Parameter(Mandatory)][string]$Code
    )

    $candidateFull = [System.IO.Path]::GetFullPath($Candidate)
    $boundaryFull = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $candidateFull.StartsWith(
        $boundaryFull + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) { throw $Code }
    return $candidateFull
}

function Read-ExactManifest {
    param([Parameter(Mandatory)][string]$Path)

    $item = Assert-RegularFile -Path $Path -MaximumBytes 131072 `
        -Code ($errorPrefix + '_MANIFEST_NOT_BOUNDED_REGULAR_FILE')
    if ((Get-Sha256File -Path $item.FullName) -cne $exactManifestSha256) {
        throw ($errorPrefix + '_MANIFEST_SHA256_MISMATCH')
    }
    try {
        $manifest = Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch { throw ($errorPrefix + '_MANIFEST_JSON_INVALID') }
    if ([string]$manifest.schema_version -cne
            'hwpx-agent.p08-19-object-target-bundle/v1' -or
        [long]$manifest.direct_feature_count -ne 41 -or
        -not ($manifest.actual_hangul_2020 -is [bool]) -or
        [bool]$manifest.actual_hangul_2020 -or
        [string]$manifest.save_reopen -cne 'not_run' -or
        [string]$manifest.resource_integrity -cne 'not_run' -or
        [string]$manifest.object_bounds -cne 'not_run' -or
        [string]$manifest.render -cne 'not_run' -or
        [string]$manifest.differential -cne 'not_run' -or
        [string]$manifest.rollback_or_retry -cne 'not_run' -or
        [string]$manifest.target_profile.product -cne 'Hancom Hangul 2020' -or
        [string]$manifest.target_profile.build -cne $ExpectedBuild -or
        [string]$manifest.target_profile.architecture -cne 'x86' -or
        [string]$manifest.target_profile.locale -cne 'ko-KR' -or
        [string]$manifest.target_profile.executable_sha256 -cne
            $ExpectedExecutableSha256) {
        throw ($errorPrefix + '_MANIFEST_CONTRACT_MISMATCH')
    }
    $cases = @($manifest.cases)
    if ($cases.Count -ne $expectedFeatures.Count) {
        throw ($errorPrefix + '_CASE_COUNT_MISMATCH')
    }
    $seenCaseIds = @{}
    for ($index = 0; $index -lt $cases.Count; $index += 1) {
        $case = $cases[$index]
        $caseId = [string]$case.case_id
        if ([string]$case.feature_id -cne $expectedFeatures[$index] -or
            $caseId -notmatch '^P08-19-C(0[1-9]|[1-3][0-9]|4[01])$' -or
            $seenCaseIds.ContainsKey($caseId) -or
            [string]$case.capability_id -notmatch '^obj\.[a-z0-9_]+$' -or
            [string]$case.file -notmatch '^obj-[0-9]{3}-[a-z0-9-]+\.hwpx$' -or
            [string]$case.package_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [long]$case.package_bytes -le 0 -or [long]$case.package_bytes -gt 8388608) {
            throw ($errorPrefix + '_CASE_BINDING_INVALID')
        }
        $seenCaseIds[$caseId] = $true
    }
    return [ordered]@{ item = $item; value = $manifest; cases = $cases }
}

function Get-CasePaths {
    param(
        [Parameter(Mandatory)][string]$InputBoundary,
        [Parameter(Mandatory)][string]$OutputBoundary,
        [Parameter(Mandatory)][object]$Case,
        [Parameter(Mandatory)][ValidateSet('primary', 'retry')][string]$Attempt
    )

    $stem = [System.IO.Path]::GetFileNameWithoutExtension([string]$Case.file)
    $suffix = if ($Attempt -ceq 'primary') { 'hancom-2020' } else { 'hancom-2020-retry' }
    return [ordered]@{
        input = Assert-PathInside -Candidate (Join-Path $InputBoundary ([string]$Case.file)) `
            -Boundary $InputBoundary -Code ($errorPrefix + '_INPUT_OUTSIDE_BOUNDARY')
        output = Assert-PathInside -Candidate (Join-Path $OutputBoundary ($stem + ".$suffix-readback.hwpx")) `
            -Boundary $OutputBoundary -Code ($errorPrefix + '_OUTPUT_OUTSIDE_BOUNDARY')
        before_pdf = Assert-PathInside -Candidate (Join-Path $OutputBoundary ($stem + ".$suffix-before.pdf")) `
            -Boundary $OutputBoundary -Code ($errorPrefix + '_OUTPUT_OUTSIDE_BOUNDARY')
        after_pdf = Assert-PathInside -Candidate (Join-Path $OutputBoundary ($stem + ".$suffix-after.pdf")) `
            -Boundary $OutputBoundary -Code ($errorPrefix + '_OUTPUT_OUTSIDE_BOUNDARY')
    }
}

function Assert-Pdf {
    param([Parameter(Mandatory)][string]$Path)

    $item = Assert-RegularFile -Path $Path -MaximumBytes 33554432 `
        -Code ($errorPrefix + '_PDF_NOT_BOUNDED_REGULAR_FILE')
    if ($item.Length -lt 5) { throw ($errorPrefix + '_PDF_SIGNATURE_MISMATCH') }
    $stream = [System.IO.File]::OpenRead($item.FullName)
    try {
        $signature = [byte[]]::new(5)
        if ($stream.Read($signature, 0, 5) -ne 5 -or
            [System.Text.Encoding]::ASCII.GetString($signature) -cne '%PDF-') {
            throw ($errorPrefix + '_PDF_SIGNATURE_MISMATCH')
        }
    }
    finally { $stream.Dispose() }
    return [ordered]@{
        sha256 = Get-Sha256File -Path $item.FullName
        bytes = [long]$item.Length
        signature_valid = $true
    }
}

function Write-ProgressEvent {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed')][string]$State,
        [AllowNull()][Nullable[int]]$HwpProcessId = $null,
        [ValidateRange(0, 41)][int]$CaseIndex = 0,
        [AllowNull()][string]$FeatureId = $null,
        [ValidateSet('session', 'primary', 'retry')][string]$Attempt = 'session'
    )

    $script:progressSequence += 1
    $event = [ordered]@{
        schema_version = 'hwpx-agent.p08-20-object-target-batch-progress/v1'
        sequence = $script:progressSequence
        recorded_at_utc = [datetime]::UtcNow.ToString('o')
        worker_process_id = $PID
        hwp_process_id = $HwpProcessId
        case_index = $CaseIndex
        feature_id = if ([string]::IsNullOrWhiteSpace($FeatureId)) { $null } else { $FeatureId }
        attempt = $Attempt
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
            "`n$line",
            [System.Text.UTF8Encoding]::new($false)
        )
    }
}

function New-CaseResult {
    param(
        [Parameter(Mandatory)][object]$Case,
        [Parameter(Mandatory)][ValidateSet('primary', 'retry')][string]$Attempt
    )

    return [ordered]@{
        case_id = [string]$Case.case_id
        feature_id = [string]$Case.feature_id
        capability_id = [string]$Case.capability_id
        attempt = $Attempt
        input_sha256 = [string]$Case.package_sha256
        input_bytes = [long]$Case.package_bytes
        input_unchanged = $false
        input_text_sha256 = $null
        output_sha256 = $null
        output_bytes = $null
        output_saved = $false
        output_text_sha256 = $null
        text_preserved = $false
        before_pdf_sha256 = $null
        before_pdf_bytes = $null
        after_pdf_sha256 = $null
        after_pdf_bytes = $null
        pdf_signatures_valid = $false
        phases = [ordered]@{
            open_input = 'not_run'
            read_input = 'not_run'
            export_before_pdf = 'not_run'
            save_as_hwpx = 'not_run'
            close_input = 'not_run'
            reopen_output = 'not_run'
            read_output = 'not_run'
            export_after_pdf = 'not_run'
            close_output = 'not_run'
        }
        state = 'failed'
        error_code = $null
        failed_phase = $null
        exception_type = $null
        exception_hresult = $null
    }
}

function Invoke-CaseRoundTrip {
    param(
        [Parameter(Mandatory)][object]$Hwp,
        [Parameter(Mandatory)][object]$Documents,
        [Parameter(Mandatory)][object]$Case,
        [Parameter(Mandatory)][object]$Paths,
        [Parameter(Mandatory)][ValidateRange(1, 41)][int]$CaseIndex,
        [Parameter(Mandatory)][ValidateSet('primary', 'retry')][string]$Attempt,
        [Parameter(Mandatory)][int]$HwpProcessId
    )

    $caseResult = New-CaseResult -Case $Case -Attempt $Attempt
    $document = $null
    $phase = 'open_input'
    try {
        foreach ($candidate in @($Paths.output, $Paths.before_pdf, $Paths.after_pdf)) {
            if (Test-Path -LiteralPath $candidate) {
                throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS')
            }
        }
        $inputItem = Assert-RegularFile -Path $Paths.input -MaximumBytes 8388608 `
            -Code ($errorPrefix + '_INPUT_NOT_BOUNDED_REGULAR_FILE')
        if ([System.IO.Path]::GetExtension($inputItem.FullName) -cne '.hwpx' -or
            $inputItem.Length -ne [long]$Case.package_bytes -or
            (Get-Sha256File -Path $inputItem.FullName) -cne [string]$Case.package_sha256) {
            throw ($errorPrefix + '_INPUT_IDENTITY_MISMATCH')
        }

        $document = $Documents.Add($false)
        if ($null -eq $document) { throw ($errorPrefix + '_DOCUMENT_ADD_FAILED') }
        [void]$document.SetActive_XHwpDocument()
        Start-Sleep -Milliseconds 150
        foreach ($currentPhase in @('open_input')) {
            $phase = $currentPhase
            $caseResult.phases[$phase] = 'running'
            Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
                -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        }
        if ($document.Open($Paths.input, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw ($errorPrefix + '_INPUT_OPEN_RETURNED_FALSE')
        }
        $caseResult.phases.open_input = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'read_input'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        $inputText = ConvertTo-CanonicalText -Value ([string]$Hwp.GetTextFile('UNICODE', ''))
        $caseResult.input_text_sha256 = Get-Sha256String -Value $inputText
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'export_before_pdf'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        [void]$document.SaveAs($Paths.before_pdf, 'PDF', '')
        $beforePdf = Assert-Pdf -Path $Paths.before_pdf
        $caseResult.before_pdf_sha256 = $beforePdf.sha256
        $caseResult.before_pdf_bytes = $beforePdf.bytes
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'save_as_hwpx'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        [void]$document.SaveAs($Paths.output, 'HWPX', '')
        $outputItem = Assert-RegularFile -Path $Paths.output -MaximumBytes 8388608 `
            -Code ($errorPrefix + '_OUTPUT_NOT_BOUNDED_REGULAR_FILE')
        $caseResult.output_saved = $true
        $caseResult.output_sha256 = Get-Sha256File -Path $outputItem.FullName
        $caseResult.output_bytes = [long]$outputItem.Length
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'close_input'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        Start-Sleep -Milliseconds 300
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'reopen_output'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        $document = $Documents.Add($false)
        if ($null -eq $document) { throw ($errorPrefix + '_REOPEN_DOCUMENT_ADD_FAILED') }
        [void]$document.SetActive_XHwpDocument()
        Start-Sleep -Milliseconds 150
        if ($document.Open($Paths.output, 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
            throw ($errorPrefix + '_OUTPUT_OPEN_RETURNED_FALSE')
        }
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'read_output'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        $outputText = ConvertTo-CanonicalText -Value ([string]$Hwp.GetTextFile('UNICODE', ''))
        $caseResult.output_text_sha256 = Get-Sha256String -Value $outputText
        $caseResult.text_preserved = $caseResult.output_text_sha256 -ceq
            $caseResult.input_text_sha256
        if (-not $caseResult.text_preserved) {
            throw ($errorPrefix + '_TEXT_NOT_PRESERVED')
        }
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'export_after_pdf'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        [void]$document.SaveAs($Paths.after_pdf, 'PDF', '')
        $afterPdf = Assert-Pdf -Path $Paths.after_pdf
        $caseResult.after_pdf_sha256 = $afterPdf.sha256
        $caseResult.after_pdf_bytes = $afterPdf.bytes
        $caseResult.pdf_signatures_valid = $beforePdf.signature_valid -and
            $afterPdf.signature_valid
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt

        $phase = 'close_output'
        $caseResult.phases[$phase] = 'running'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        [void]$document.Close($false)
        Clear-ComObject -Value $document
        $document = $null
        Start-Sleep -Milliseconds 150
        $caseResult.phases[$phase] = 'pass'
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
        $caseResult.state = 'pass'
    }
    catch {
        $caseResult.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
            [string]$_.Exception.Message
        }
        else { $errorPrefix + '_CASE_EXCEPTION' }
        $caseResult.failed_phase = $phase
        $caseResult.exception_type = $_.Exception.GetType().FullName
        $caseResult.exception_hresult = $_.Exception.HResult
        if ($caseResult.phases.Contains($phase)) {
            $caseResult.phases[$phase] = 'failed'
        }
        Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $HwpProcessId `
            -CaseIndex $CaseIndex -FeatureId $Case.feature_id -Attempt $Attempt
    }
    finally {
        if ($null -ne $document) {
            try { [void]$document.Close($false) } catch { }
            Clear-ComObject -Value $document
            Start-Sleep -Milliseconds 300
        }
        try {
            $caseResult.input_unchanged = (Get-Sha256File -Path $Paths.input) -ceq
                [string]$Case.package_sha256
        }
        catch { $caseResult.input_unchanged = $false }
        if (-not $caseResult.input_unchanged -and $null -eq $caseResult.error_code) {
            $caseResult.state = 'failed'
            $caseResult.error_code = $errorPrefix + '_INPUT_CHANGED'
            $caseResult.failed_phase = 'input_integrity'
        }
    }
    return $caseResult
}

function Restart-HwpAutomationSession {
    param(
        [AllowNull()][object]$Hwp,
        [AllowNull()][object]$Documents,
        [AllowNull()][object]$Window,
        [AllowNull()][Nullable[int]]$HwpProcessId
    )

    Clear-ComObject -Value $Documents
    Clear-ComObject -Value $Window
    if ($null -ne $Hwp) {
        try { $Hwp.Quit() } catch { }
    }
    Clear-ComObject -Value $Hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    if ($null -ne $HwpProcessId) {
        for ($waitIndex = 0; $waitIndex -lt 50; $waitIndex += 1) {
            if ($null -eq (Get-Process -Id $HwpProcessId -ErrorAction SilentlyContinue)) {
                break
            }
            Start-Sleep -Milliseconds 100
        }
        if ($null -ne (Get-Process -Id $HwpProcessId -ErrorAction SilentlyContinue)) {
            throw ($errorPrefix + '_FAILED_SESSION_PROCESS_DID_NOT_EXIT')
        }
    }

    $nextHwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$nextHwp.Version)) -cne
        $ExpectedBuild) {
        throw ($errorPrefix + '_AUTOMATION_VERSION_MISMATCH_AFTER_RESTART')
    }
    [void]$nextHwp.RegisterModule('FilePathCheckDLL', $securityModuleName)
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -ne 1) {
        throw ($errorPrefix + '_HWP_PROCESS_COUNT_UNEXPECTED_AFTER_RESTART')
    }
    $nextProcessId = [int]$hwpProcesses[0].ProcessId
    $nextDocuments = $nextHwp.XHwpDocuments
    $nextWindow = $nextHwp.XHwpWindows.Item(0)
    $nextWindow.Visible = $true
    return [pscustomobject]@{
        hwp = $nextHwp
        documents = $nextDocuments
        window = $nextWindow
        process_id = $nextProcessId
    }
}

$manifestRecord = Read-ExactManifest -Path $FixtureManifestPath
$inputBoundary = (Resolve-Path -LiteralPath (
    Split-Path -Parent $manifestRecord.item.FullName
)).Path.TrimEnd('\')
$outputBoundary = (Resolve-Path -LiteralPath $RunDirectory).Path.TrimEnd('\')
$traceFile = Assert-PathInside -Candidate $TracePath -Boundary $outputBoundary `
    -Code ($errorPrefix + '_TRACE_OUTSIDE_BOUNDARY')
$script:progressFile = Assert-PathInside -Candidate $ProgressPath -Boundary $outputBoundary `
    -Code ($errorPrefix + '_PROGRESS_OUTSIDE_BOUNDARY')
foreach ($candidate in @($traceFile, $script:progressFile)) {
    if (Test-Path -LiteralPath $candidate) {
        throw ($errorPrefix + '_OUTPUT_ALREADY_EXISTS')
    }
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}
$identity = Get-ComServerIdentity -RequestedProgId $ProgId
if ($ProgId -cne 'HWPFrame.HwpObject.2' -or
    $identity.file_version -cne $ExpectedBuild -or
    $identity.sha256 -cne $ExpectedExecutableSha256) {
    throw ($errorPrefix + '_TARGET_IDENTITY_MISMATCH')
}
$moduleItem = Assert-RegularFile -Path $securityModulePath -MaximumBytes 1048576 `
    -Code ($errorPrefix + '_SECURITY_MODULE_INVALID')
if ($moduleItem.Length -ne 217229 -or
    (Get-Sha256File -Path $moduleItem.FullName) -cne $securityModuleSha256) {
    throw ($errorPrefix + '_SECURITY_MODULE_IDENTITY_MISMATCH')
}
$moduleKey = Get-Item -LiteralPath $securityModuleRegistryPath
if ([string]$moduleKey.GetValueKind($securityModuleName) -cne 'String' -or
    [string]$moduleKey.GetValue($securityModuleName) -cne $moduleItem.FullName) {
    throw ($errorPrefix + '_SECURITY_MODULE_REGISTRY_MISMATCH')
}

$result = [ordered]@{
    schema_version = 'hwpx-agent.p08-20-object-target-batch-engine/v1'
    state = 'failed'
    target = [ordered]@{
        product = 'Hancom Hangul 2020'
        prog_id = $ProgId
        registry_view = 'Registry32'
        client = 'windows_powershell_x86_sta'
        file_version = $identity.file_version
        executable_sha256 = $identity.sha256
        architecture = 'x86'
        locale = 'ko-KR'
    }
    session_strategy = 'single_hwp_process_with_fail_closed_restart_for_41_primary_plus_bounded_retry_cases'
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    case_count = 41
    completed_case_count = 0
    effective_completed_case_count = 0
    recovered_case_count = 0
    cases = @()
    retry_policy = 'retry_all_primary_failures_plus_OBJ-002_OBJ-024_OBJ-010_from_immutable_source'
    retry_case_count = 0
    retry_completed_case_count = 0
    retries = @()
    session_restart_count = 0
    scheduled_session_restart_count = 0
    retry_session_restart_count = 0
    hwp_process_ids = @()
    security_module = [ordered]@{
        source = 'official_hancom_automation_security_module'
        module_type = 'FilePathCheckDLL'
        registry_value_name = $securityModuleName
        dll_sha256 = $securityModuleSha256
        architecture = 'x86'
        preflight_state = 'pass'
        register_state = 'not_run'
        register_return = $null
        effective_state = 'not_run'
    }
    hwp_process_id = $null
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
$window = $null
$hwpProcessId = $null
$phase = 'com_create'
$script:progressSequence = 0
Write-ProgressEvent -Phase 'preflight' -State 'pass'
try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne
        [Threading.ApartmentState]::STA) {
        throw ($errorPrefix + '_CLIENT_NOT_STA')
    }
    $hwp = New-Object -ComObject $ProgId
    if ((ConvertTo-NormalizedVersion -Value ([string]$hwp.Version)) -cne
        $ExpectedBuild) {
        throw ($errorPrefix + '_AUTOMATION_VERSION_MISMATCH')
    }
    $phase = 'security_module_register'
    $result.security_module.register_state = 'running'
    $result.security_module.register_return = [bool]$hwp.RegisterModule(
        'FilePathCheckDLL',
        $securityModuleName
    )
    $result.security_module.register_state = 'call_completed'
    $result.security_module.effective_state = 'pending_first_fixture_open'
    $phase = 'com_create'
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -ne 1) {
        throw ($errorPrefix + '_HWP_PROCESS_COUNT_UNEXPECTED')
    }
    $hwpProcessId = [int]$hwpProcesses[0].ProcessId
    $result.hwp_process_id = $hwpProcessId
    $result.hwp_process_ids += $hwpProcessId
    Write-ProgressEvent -Phase 'com_create' -State 'pass' -HwpProcessId $hwpProcessId

    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $result.window_visible_for_user_access = $true

    for ($index = 0; $index -lt $manifestRecord.cases.Count; $index += 1) {
        $case = $manifestRecord.cases[$index]
        $paths = Get-CasePaths -InputBoundary $inputBoundary `
            -OutputBoundary $outputBoundary -Case $case -Attempt 'primary'
        $caseResult = Invoke-CaseRoundTrip -Hwp $hwp -Documents $documents `
            -Case $case -Paths $paths -CaseIndex ($index + 1) -Attempt 'primary' `
            -HwpProcessId $hwpProcessId
        $result.cases += ,$caseResult
        $caseFailed = [string]$caseResult.state -cne 'pass'
        $firstCaseOpenGateFailed = $index -eq 0 -and $caseFailed -and
            [string]$caseResult.failed_phase -ceq 'open_input'
        if ($firstCaseOpenGateFailed) {
            $result.security_module.effective_state = 'first_fixture_open_failed'
            $phase = 'first_case_open_gate'
            throw ($errorPrefix + '_FIRST_CASE_OPEN_GATE_FAILED')
        }
        if (-not $caseFailed) {
            $result.completed_case_count += 1
            if ($index -eq 0) {
                $result.security_module.effective_state = 'passed_by_first_fixture_open'
            }
        }
        $scheduledRestart = (($index + 1) % 12) -eq 0
        if ($caseFailed -or $scheduledRestart) {
            $phase = if ($caseFailed) { 'failed_session_restart' }
                else { 'scheduled_session_restart' }
            Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
                -CaseIndex ($index + 1) -FeatureId $case.feature_id -Attempt 'primary'
            $session = Restart-HwpAutomationSession -Hwp $hwp -Documents $documents `
                -Window $window -HwpProcessId $hwpProcessId
            $hwp = $session.hwp
            $documents = $session.documents
            $window = $session.window
            $hwpProcessId = [int]$session.process_id
            $result.hwp_process_ids += $hwpProcessId
            $result.session_restart_count += 1
            if ($scheduledRestart) { $result.scheduled_session_restart_count += 1 }
            Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
                -CaseIndex ($index + 1) -FeatureId $case.feature_id -Attempt 'primary'
        }
    }

    $retryFeatures = [System.Collections.Generic.List[string]]::new()
    foreach ($feature in $representativeRetryFeatures) { $retryFeatures.Add($feature) }
    foreach ($caseResult in $result.cases) {
        if ([string]$caseResult.state -cne 'pass' -and
            -not $retryFeatures.Contains([string]$caseResult.feature_id)) {
            $retryFeatures.Add([string]$caseResult.feature_id)
        }
    }
    $result.retry_case_count = $retryFeatures.Count
    foreach ($feature in $retryFeatures) {
        $index = [array]::IndexOf($expectedFeatures, $feature)
        if ($index -lt 0) { throw ($errorPrefix + '_RETRY_FEATURE_UNKNOWN') }
        $case = $manifestRecord.cases[$index]
        $phase = 'retry_session_restart'
        Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId `
            -CaseIndex ($index + 1) -FeatureId $case.feature_id -Attempt 'retry'
        $session = Restart-HwpAutomationSession -Hwp $hwp -Documents $documents `
            -Window $window -HwpProcessId $hwpProcessId
        $hwp = $session.hwp
        $documents = $session.documents
        $window = $session.window
        $hwpProcessId = [int]$session.process_id
        $result.hwp_process_ids += $hwpProcessId
        $result.session_restart_count += 1
        $result.retry_session_restart_count += 1
        Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId `
            -CaseIndex ($index + 1) -FeatureId $case.feature_id -Attempt 'retry'
        $paths = Get-CasePaths -InputBoundary $inputBoundary `
            -OutputBoundary $outputBoundary -Case $case -Attempt 'retry'
        $retryResult = Invoke-CaseRoundTrip -Hwp $hwp -Documents $documents `
            -Case $case -Paths $paths -CaseIndex ($index + 1) -Attempt 'retry' `
            -HwpProcessId $hwpProcessId
        $result.retries += ,$retryResult
        if ([string]$retryResult.state -ceq 'pass') {
            $result.retry_completed_case_count += 1
        }
    }

    $phase = 'quit'
    Write-ProgressEvent -Phase $phase -State 'running' -HwpProcessId $hwpProcessId
    $hwp.Quit()
    Write-ProgressEvent -Phase $phase -State 'pass' -HwpProcessId $hwpProcessId
    $effectiveCompleted = 0
    foreach ($feature in $expectedFeatures) {
        $primaryPassed = @($result.cases | Where-Object {
            [string]$_.feature_id -ceq $feature -and [string]$_.state -ceq 'pass'
        }).Count -eq 1
        $retryPassed = @($result.retries | Where-Object {
            [string]$_.feature_id -ceq $feature -and [string]$_.state -ceq 'pass'
        }).Count -eq 1
        if ($primaryPassed -or $retryPassed) { $effectiveCompleted += 1 }
    }
    $result.effective_completed_case_count = $effectiveCompleted
    $result.recovered_case_count = $effectiveCompleted - $result.completed_case_count
    if ($result.effective_completed_case_count -eq $result.case_count -and
        $result.retry_completed_case_count -eq $result.retry_case_count) {
        $result.state = 'pass'
    }
    else {
        $result.error_code = $errorPrefix + '_ONE_OR_MORE_CASES_FAILED'
        $result.failed_phase = 'case_campaign'
    }
}
catch {
    $result.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { $errorPrefix + '_SESSION_EXCEPTION' }
    $result.failed_phase = $phase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    Write-ProgressEvent -Phase $phase -State 'failed' -HwpProcessId $hwpProcessId
}
finally {
    Clear-ComObject -Value $documents
    Clear-ComObject -Value $window
    if ($null -ne $hwp -and $result.state -ne 'pass') {
        try { $hwp.Quit() } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-ProgressEvent -Phase 'terminal' `
    -State $(if ($result.state -ceq 'pass') { 'pass' } else { 'failed' }) `
    -HwpProcessId $hwpProcessId
Write-NewUtf8File -Path $traceFile -Content ($result | ConvertTo-Json -Depth 12)
$result | ConvertTo-Json -Depth 12
if ($result.state -cne 'pass') { exit 2 }
exit 0
