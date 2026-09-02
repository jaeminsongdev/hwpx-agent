[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$InputPath,

    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedInputSha256,

    [Parameter(Mandatory)]
    [ValidateRange(0, 1)]
    [int]$FixtureOrdinal,

    [Parameter(Mandatory)]
    [ValidateSet('preserving', 'normalized')]
    [string]$Mode,

    [Parameter(Mandatory)]
    [string]$TracePath,

    [string]$ProgressPath,

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$ExpectedBuild = '11.0.0.9136',

    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$ExpectedSingleParagraphSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
    finally {
        $algorithm.Dispose()
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

function ConvertTo-CanonicalDocumentText {
    param([AllowEmptyString()][string]$Value)

    if ($null -eq $Value) { return [string]::Empty }
    $normalized = $Value.Replace("`0", '')
    $normalized = $normalized.Replace("`r`n", "`n").Replace("`r", "`n")
    return $normalized.Normalize([System.Text.NormalizationForm]::FormC)
}

function Clear-ComObject {
    param([AllowNull()]$Value)

    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $encoding = [System.Text.UTF8Encoding]::new($false)
    $bytes = $encoding.GetBytes($Content)
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
    finally {
        $stream.Dispose()
    }
}

function Write-ProgressCheckpoint {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][ValidateSet('running', 'pass', 'failed', 'complete')][string]$State
    )

    if ($null -eq $resolvedProgressPath) { return }
    $script:progressSequence += 1
    $snapshot = [ordered]@{
        schema_version = 'hwpx-agent.hancom-roundtrip-progress/v1'
        sequence = $script:progressSequence
        observed_utc = [DateTime]::UtcNow.ToString('o')
        process_id = $PID
        apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
        phase = $Phase
        state = $State
    }
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText(
        $resolvedProgressPath,
        ($snapshot | ConvertTo-Json -Depth 4),
        $encoding
    )
}

$resolvedInputPath = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedTraceParent = (Resolve-Path -LiteralPath (Split-Path -Parent $TracePath)).Path
$resolvedTracePath = Join-Path $resolvedTraceParent (Split-Path -Leaf $TracePath)
if (Test-Path -LiteralPath $resolvedTracePath) {
    throw 'ROUNDTRIP_ORACLE_TRACE_ALREADY_EXISTS'
}
$resolvedProgressPath = $null
$progressSequence = 0
if (-not [string]::IsNullOrWhiteSpace($ProgressPath)) {
    $resolvedProgressParent = (Resolve-Path -LiteralPath (Split-Path -Parent $ProgressPath)).Path
    $resolvedProgressPath = Join-Path $resolvedProgressParent (Split-Path -Leaf $ProgressPath)
    if (Test-Path -LiteralPath $resolvedProgressPath) {
        throw 'ROUNDTRIP_ORACLE_PROGRESS_ALREADY_EXISTS'
    }
}

$trace = [ordered]@{
    schema_version = 'hwpx-agent.hancom-2020-roundtrip-trace/v1'
    state = 'failed'
    fixture_ordinal = $FixtureOrdinal
    mode = $Mode
    input_sha256 = $null
    input_size = 0
    input_identity_subphase = 'not_run'
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    automation_version_normalized = $null
    text_sha256 = $null
    text_utf8_length = 0
    expected_single_paragraph_match = $null
    phases = [ordered]@{
        input_identity = 'not_run'
        com_create = 'not_run'
        version_check = 'not_run'
        document_add = 'not_run'
        document_open = 'not_run'
        text_read = 'not_run'
        document_close = 'not_run'
        quit = 'not_run'
    }
    error_code = $null
    failed_phase = $null
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
    quit_invoked = $false
    input_modified = $false
    output_saved = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
}

$hwp = $null
$documents = $null
$document = $null
$activePhase = 'input_identity'

try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        throw 'ROUNDTRIP_ORACLE_CLIENT_NOT_STA'
    }

    $trace.phases.input_identity = 'running'
    Write-ProgressCheckpoint -Phase 'input_identity' -State 'running'
    $trace.input_identity_subphase = 'get_item'
    $inputItem = Get-Item -LiteralPath $resolvedInputPath
    $trace.input_identity_subphase = 'read_size'
    $trace.input_size = [int64]$inputItem.Length
    $trace.input_identity_subphase = 'hash_file'
    $trace.input_sha256 = Get-Sha256File -Path $resolvedInputPath
    $trace.input_identity_subphase = 'compare_hash'
    if ($trace.input_sha256 -cne $ExpectedInputSha256) {
        throw 'ROUNDTRIP_ORACLE_INPUT_SHA256_MISMATCH'
    }
    $trace.input_identity_subphase = 'pass'
    $trace.phases.input_identity = 'pass'
    Write-ProgressCheckpoint -Phase 'input_identity' -State 'pass'

    $activePhase = 'com_create'
    $trace.phases.com_create = 'running'
    Write-ProgressCheckpoint -Phase 'com_create' -State 'running'
    $hwp = New-Object -ComObject $ProgId
    $trace.phases.com_create = 'pass'
    Write-ProgressCheckpoint -Phase 'com_create' -State 'pass'

    $activePhase = 'version_check'
    $trace.phases.version_check = 'running'
    Write-ProgressCheckpoint -Phase 'version_check' -State 'running'
    $trace.automation_version_normalized = ConvertTo-NormalizedHancomVersion -Value ([string]$hwp.Version)
    if ($trace.automation_version_normalized -cne $ExpectedBuild) {
        throw 'ROUNDTRIP_ORACLE_AUTOMATION_VERSION_MISMATCH'
    }
    $trace.phases.version_check = 'pass'
    Write-ProgressCheckpoint -Phase 'version_check' -State 'pass'

    $activePhase = 'document_add'
    $trace.phases.document_add = 'running'
    Write-ProgressCheckpoint -Phase 'document_add' -State 'running'
    $documents = $hwp.XHwpDocuments
    $document = $documents.Add($false)
    if ($null -eq $document) { throw 'ROUNDTRIP_ORACLE_DOCUMENT_ADD_RETURNED_NULL' }
    $trace.phases.document_add = 'pass'
    Write-ProgressCheckpoint -Phase 'document_add' -State 'pass'

    $activePhase = 'document_open'
    $trace.phases.document_open = 'running'
    Write-ProgressCheckpoint -Phase 'document_open' -State 'running'
    $openResult = $document.Open($resolvedInputPath, 'HWPX', 'lock:false;setcurdir:false')
    if ($openResult -eq $false) { throw 'ROUNDTRIP_ORACLE_DOCUMENT_OPEN_RETURNED_FALSE' }
    $null = $document.SetActive_XHwpDocument()
    $trace.phases.document_open = 'pass'
    Write-ProgressCheckpoint -Phase 'document_open' -State 'pass'

    $activePhase = 'text_read'
    $trace.phases.text_read = 'running'
    Write-ProgressCheckpoint -Phase 'text_read' -State 'running'
    $canonicalText = ConvertTo-CanonicalDocumentText -Value ([string]$hwp.GetTextFile('UNICODE', ''))
    $textBytes = [System.Text.Encoding]::UTF8.GetBytes($canonicalText)
    $trace.text_utf8_length = $textBytes.Length
    $trace.text_sha256 = Get-Sha256String -Value $canonicalText
    if (-not [string]::IsNullOrWhiteSpace($ExpectedSingleParagraphSha256)) {
        $singleParagraph = $canonicalText.TrimEnd([char]"`n")
        if (
            $singleParagraph.Contains("`n") -or
            (Get-Sha256String -Value $singleParagraph) -cne $ExpectedSingleParagraphSha256
        ) {
            $trace.expected_single_paragraph_match = $false
            throw 'ROUNDTRIP_ORACLE_SINGLE_PARAGRAPH_MISMATCH'
        }
        $trace.expected_single_paragraph_match = $true
    }
    $trace.phases.text_read = 'pass'
    Write-ProgressCheckpoint -Phase 'text_read' -State 'pass'

    $activePhase = 'document_close'
    $trace.phases.document_close = 'running'
    Write-ProgressCheckpoint -Phase 'document_close' -State 'running'
    $null = $document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $trace.phases.document_close = 'pass'
    Write-ProgressCheckpoint -Phase 'document_close' -State 'pass'

    $activePhase = 'quit'
    $trace.phases.quit = 'running'
    Write-ProgressCheckpoint -Phase 'quit' -State 'running'
    $hwp.Quit()
    $trace.quit_invoked = $true
    $trace.phases.quit = 'pass'
    $trace.state = 'pass'
    Write-ProgressCheckpoint -Phase 'quit' -State 'pass'
}
catch {
    $trace.state = 'failed'
    $trace.error_code = if ([string]$_.Exception.Message -match '^[A-Z0-9_]+$') {
        [string]$_.Exception.Message
    }
    else { 'ROUNDTRIP_ORACLE_CHILD_EXCEPTION' }
    $trace.failed_phase = $activePhase
    $trace.exception_type = $_.Exception.GetType().FullName
    $trace.exception_hresult = $_.Exception.HResult
    $trace.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
    if ($trace.phases.Contains($activePhase)) { $trace.phases[$activePhase] = 'failed' }
    Write-ProgressCheckpoint -Phase $activePhase -State 'failed'
}
finally {
    if ($null -ne $document) {
        try { $null = $document.Close($false) } catch { }
        Clear-ComObject -Value $document
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

Write-NewUtf8File -Path $resolvedTracePath -Content ($trace | ConvertTo-Json -Depth 8)
Write-ProgressCheckpoint -Phase 'final_trace' -State 'complete'
if ($trace.state -ne 'pass') { exit 2 }
