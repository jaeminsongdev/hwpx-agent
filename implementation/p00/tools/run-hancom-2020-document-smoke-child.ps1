[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RunDirectory,

    [string]$ProgId = 'HWPFrame.HwpObject.2',

    [string]$ExpectedAutomationVersion = '11.0.0.9136',

    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{32}$')]
    [string]$FixtureId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256String {
    param([Parameter(Mandatory)][string]$Value)

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
    if (-not $match.Success) {
        return $null
    }

    $components = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($components -join '.')
}

function ConvertTo-CanonicalSmokeText {
    param([AllowEmptyString()][string]$Value)

    if ($null -eq $Value) {
        return $null
    }

    # HWP text APIs may expose Windows or legacy CR-only paragraph separators.
    # Only separator encoding and Unicode composition are normalized; whitespace
    # and document content are otherwise compared exactly.
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

function Write-SmokeFailure {
    param(
        [Parameter(Mandatory)][System.Collections.IDictionary]$Result,
        [Parameter(Mandatory)][string]$Code
    )

    $Result.state = 'failed'
    $Result.error_code = $Code
    throw $Code
}

$resolvedRunDirectory = (Resolve-Path -LiteralPath $RunDirectory).Path
$hwpxPath = Join-Path $resolvedRunDirectory 'synthetic-p00-2020.hwpx'
$pdfPath = Join-Path $resolvedRunDirectory 'synthetic-p00-2020.pdf'
$resultPath = Join-Path $resolvedRunDirectory 'child-result.json'

foreach ($path in @($hwpxPath, $pdfPath, $resultPath)) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing to overwrite an existing smoke output: $path"
    }
}

$koreanFixtureLine = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('7ZWc6riAIOyekOuPme2ZlCDtlanshLEg66y47IScIOyZleuztSDqsoDspp0=')
)
$fixtureText = @(
    'HWPX Agent P00 Hangul 2020 synthetic smoke'
    "fixture_id=$FixtureId"
    $koreanFixtureLine
    'ASCII=ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789'
    'FORMULA_LITERAL=(a+b)^2=a^2+2ab+b^2'
) -join "`r`n"
$fixtureCanonical = ConvertTo-CanonicalSmokeText -Value $fixtureText

$result = [ordered]@{
    schema_version = 'hwpx-agent.hancom-document-smoke-child/v1'
    state = 'failed'
    error_code = $null
    failed_phase = $null
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    prog_id = $ProgId
    expected_automation_version = $ExpectedAutomationVersion
    automation_version = $null
    automation_version_normalized = $null
    automation_version_matches_expected = $false
    fixture_id = $FixtureId
    fixture_sha256 = Get-Sha256String -Value $fixtureCanonical
    fixture_utf16_length = $fixtureCanonical.Length
    readback_sha256 = $null
    readback_utf16_length = $null
    text_exact_match_after_document_separator_normalization = $false
    hwpx_file_created = $false
    pdf_file_created = $false
    pdf_export_method = $null
    quit_invoked = $false
    register_module_invoked = $false
    user_document_opened = $false
    cleanup_close_error_hashes = @()
    phases = [ordered]@{
        com_create = 'not_run'
        version_check = 'not_run'
        document_add = 'not_run'
        insert_text = 'not_run'
        hwpx_save = 'not_run'
        document_close_before_reopen = 'not_run'
        hwpx_reopen = 'not_run'
        readback = 'not_run'
        pdf_export = 'not_run'
        document_close = 'not_run'
        quit = 'not_run'
    }
    exception_type = $null
    exception_hresult = $null
    exception_message_sha256 = $null
}

$hwp = $null
$documents = $null
$document = $null
$reopenedDocument = $null
$activePhase = 'initialization'

try {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
        Write-SmokeFailure -Result $result -Code 'CLIENT_NOT_STA'
    }

    $activePhase = 'com_create'
    $result.phases.com_create = 'running'
    $hwp = New-Object -ComObject $ProgId
    $result.phases.com_create = 'pass'

    $activePhase = 'version_check'
    $result.phases.version_check = 'running'
    $result.automation_version = [string]$hwp.Version
    $result.automation_version_normalized = ConvertTo-NormalizedHancomVersion -Value $result.automation_version
    $expectedVersionNormalized = ConvertTo-NormalizedHancomVersion -Value $ExpectedAutomationVersion
    $result.automation_version_matches_expected =
        $null -ne $expectedVersionNormalized -and
        $result.automation_version_normalized -ceq $expectedVersionNormalized
    if (-not $result.automation_version_matches_expected) {
        Write-SmokeFailure -Result $result -Code 'AUTOMATION_VERSION_MISMATCH'
    }
    $result.phases.version_check = 'pass'

    $documents = $hwp.XHwpDocuments

    $activePhase = 'document_add'
    $result.phases.document_add = 'running'
    $document = $documents.Add($false)
    if ($null -eq $document) {
        Write-SmokeFailure -Result $result -Code 'DOCUMENT_ADD_RETURNED_NULL'
    }
    $result.phases.document_add = 'pass'

    $activePhase = 'insert_text'
    $result.phases.insert_text = 'running'
    $null = $hwp.HAction.GetDefault('InsertText', $hwp.HParameterSet.HInsertText.HSet)
    $hwp.HParameterSet.HInsertText.Text = $fixtureText
    $insertResult = $hwp.HAction.Execute('InsertText', $hwp.HParameterSet.HInsertText.HSet)
    if ($insertResult -eq $false) {
        Write-SmokeFailure -Result $result -Code 'INSERT_TEXT_RETURNED_FALSE'
    }
    $result.phases.insert_text = 'pass'

    $activePhase = 'hwpx_save'
    $result.phases.hwpx_save = 'running'
    $null = $document.SaveAs($hwpxPath, 'HWPX', '')
    $result.hwpx_file_created = Test-Path -LiteralPath $hwpxPath -PathType Leaf
    if (-not $result.hwpx_file_created) {
        Write-SmokeFailure -Result $result -Code 'HWPX_SAVE_OUTPUT_MISSING'
    }
    $result.phases.hwpx_save = 'pass'

    $activePhase = 'document_close_before_reopen'
    $result.phases.document_close_before_reopen = 'running'
    $null = $document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $result.phases.document_close_before_reopen = 'pass'

    $activePhase = 'hwpx_reopen'
    $result.phases.hwpx_reopen = 'running'
    # Open is an IXHwpDocument method in the official automation catalog,
    # not a method on the IXHwpDocuments collection. Create a fresh document
    # object and load the generated package into that bounded document.
    $reopenedDocument = $documents.Add($false)
    if ($null -eq $reopenedDocument) {
        Write-SmokeFailure -Result $result -Code 'REOPEN_DOCUMENT_ADD_RETURNED_NULL'
    }
    $openResult = $reopenedDocument.Open($hwpxPath, 'HWPX', 'lock:false;setcurdir:false')
    if ($openResult -eq $false) {
        Write-SmokeFailure -Result $result -Code 'HWPX_REOPEN_RETURNED_FALSE'
    }
    $null = $reopenedDocument.SetActive_XHwpDocument()
    $result.phases.hwpx_reopen = 'pass'

    $activePhase = 'readback'
    $result.phases.readback = 'running'
    $readbackText = [string]$hwp.GetTextFile('UNICODE', '')
    $readbackCanonical = ConvertTo-CanonicalSmokeText -Value $readbackText
    $result.readback_sha256 = Get-Sha256String -Value $readbackCanonical
    $result.readback_utf16_length = $readbackCanonical.Length
    $result.text_exact_match_after_document_separator_normalization = $readbackCanonical -ceq $fixtureCanonical
    if (-not $result.text_exact_match_after_document_separator_normalization) {
        Write-SmokeFailure -Result $result -Code 'READBACK_TEXT_MISMATCH'
    }
    $result.phases.readback = 'pass'

    $activePhase = 'pdf_export'
    $result.phases.pdf_export = 'running'
    $result.pdf_export_method = 'IXHwpDocument.SaveAs/PDF'
    $null = $reopenedDocument.SaveAs($pdfPath, 'PDF', '')
    $result.pdf_file_created = Test-Path -LiteralPath $pdfPath -PathType Leaf
    if (-not $result.pdf_file_created) {
        Write-SmokeFailure -Result $result -Code 'PDF_EXPORT_OUTPUT_MISSING'
    }
    $result.phases.pdf_export = 'pass'

    $activePhase = 'document_close'
    $result.phases.document_close = 'running'
    $null = $reopenedDocument.Close($false)
    Clear-ComObject -Value $reopenedDocument
    $reopenedDocument = $null
    $result.phases.document_close = 'pass'

    $activePhase = 'quit'
    $result.phases.quit = 'running'
    $hwp.Quit()
    $result.quit_invoked = $true
    $result.phases.quit = 'pass'
    $result.state = 'pass'
}
catch {
    $result.state = 'failed'
    if ($null -eq $result.error_code) {
        $result.error_code = 'COM_DOCUMENT_SMOKE_EXCEPTION'
    }
    $result.failed_phase = $activePhase
    $result.exception_type = $_.Exception.GetType().FullName
    $result.exception_hresult = $_.Exception.HResult
    $result.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
}
finally {
    if ($null -ne $reopenedDocument) {
        try {
            $null = $reopenedDocument.Close($false)
        }
        catch {
            $result.cleanup_close_error_hashes += Get-Sha256String -Value ([string]$_.Exception.Message)
        }
        Clear-ComObject -Value $reopenedDocument
    }
    if ($null -ne $document) {
        try {
            $null = $document.Close($false)
        }
        catch {
            $result.cleanup_close_error_hashes += Get-Sha256String -Value ([string]$_.Exception.Message)
        }
        Clear-ComObject -Value $document
    }
    Clear-ComObject -Value $documents

    if ($null -ne $hwp) {
        if (-not $result.quit_invoked) {
            try {
                $hwp.Quit()
                $result.quit_invoked = $true
                $result.phases.quit = 'pass'
            }
            catch {
                $result.phases.quit = 'failed'
                if ($result.state -eq 'pass') {
                    $result.state = 'failed'
                    $result.error_code = 'QUIT_FAILED'
                    $result.failed_phase = 'quit'
                    $result.exception_type = $_.Exception.GetType().FullName
                    $result.exception_hresult = $_.Exception.HResult
                    $result.exception_message_sha256 = Get-Sha256String -Value ([string]$_.Exception.Message)
                }
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
$resultJson = $result | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($resultPath, $resultJson, $utf8WithoutBom)

if ($result.state -ne 'pass') {
    exit 2
}
