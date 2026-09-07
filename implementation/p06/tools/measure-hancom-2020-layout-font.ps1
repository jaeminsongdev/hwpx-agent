[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{32}$')]
    [string]$RunId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertFrom-CodePoints {
    param([Parameter(Mandatory)][int[]]$Value)
    return -join @($Value | ForEach-Object { [char]$_ })
}

$expectedBuild = '11.0.0.9136'
$expectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$expectedFontFile = 'HANBatang.ttf'
$expectedFontSha256 = '0dbeb7b129fcec63f8d6b7f1d3b5bb991c1d599e725286518ccc598de643f014'
$canonicalFamily = ConvertFrom-CodePoints -Value @(0xD568, 0xCD08, 0xB86C, 0xBC14, 0xD0D5)
$acceptedFamilyNames = @($canonicalFamily, 'HCR Batang')
$profileId = 'hwpx-agent.font-metric.gdiplus-typographic-96dpi/1'
$dpi = 96
$fontSizeMillipoints = 10000

function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return (($algorithm.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
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

function Write-NewJson {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][object]$Value)
    $content = ($Value | ConvertTo-Json -Depth 10) + "`n"
    $content = [regex]::Replace(
        $content,
        '[^\x00-\x7F]',
        { param($match) return ('\u{0:x4}' -f [int][char]$match.Value[0]) }
    )
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($content)
    if ($bytes.Length -le 0 -or $bytes.Length -gt 262144) { throw 'RECEIPT_SIZE_INVALID' }
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
    finally { $stream.Dispose() }
}

function Convert-PixelsToMicrometers {
    param([Parameter(Mandatory)][single]$Pixels)
    if ([single]::IsNaN($Pixels) -or [single]::IsInfinity($Pixels) -or $Pixels -le 0) {
        throw 'FONT_METRIC_NONFINITE'
    }
    $value = [Math]::Round(
        ([double]$Pixels * 25400.0) / [double]$dpi,
        0,
        [MidpointRounding]::AwayFromZero
    )
    if ($value -le 0 -or $value -gt 1000000000) { throw 'FONT_METRIC_OUT_OF_RANGE' }
    return [int64]$value
}

function Invoke-MeasurementPass {
    param([Parameter(Mandatory)][string]$FontPath)

    Add-Type -AssemblyName System.Drawing
    $collection = [System.Drawing.Text.PrivateFontCollection]::new()
    try {
        $collection.AddFontFile($FontPath)
        $families = @($collection.Families)
        if ($families.Count -ne 1 -or $acceptedFamilyNames -cnotcontains $families[0].Name) {
            throw 'FONT_FAMILY_IDENTITY_MISMATCH'
        }
        $family = $families[0]
        if (-not $family.IsStyleAvailable([System.Drawing.FontStyle]::Regular)) {
            throw 'FONT_REGULAR_STYLE_MISSING'
        }
        $font = [System.Drawing.Font]::new(
            $family,
            [single]10.0,
            [System.Drawing.FontStyle]::Regular,
            [System.Drawing.GraphicsUnit]::Point
        )
        try {
            $bitmap = [System.Drawing.Bitmap]::new(8, 8)
            try {
                $bitmap.SetResolution([single]$dpi, [single]$dpi)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                try {
                    $graphics.PageUnit = [System.Drawing.GraphicsUnit]::Pixel
                    $format = [System.Drawing.StringFormat]::GenericTypographic.Clone()
                    try {
                        $format.FormatFlags = $format.FormatFlags -bor
                            [System.Drawing.StringFormatFlags]::MeasureTrailingSpaces -bor
                            [System.Drawing.StringFormatFlags]::NoClip
                        $lineHeight = Convert-PixelsToMicrometers -Pixels $font.GetHeight($graphics)
                        $cases = @(
                            [ordered]@{ cell_id = 'cell-a'; text = 'P06-05 A' },
                            [ordered]@{
                                cell_id = 'cell-b'
                                text = ConvertFrom-CodePoints -Value @(
                                    0xD55C, 0xAE00, 0x0020, 0xD45C, 0x0020,
                                    0xC790, 0xB3D9, 0x0020, 0xB9DE, 0xCDA4
                                )
                            },
                            [ordered]@{ cell_id = 'cell-c'; text = 'WIDE-CONTENT-1234567890' },
                            [ordered]@{
                                cell_id = 'cell-d'
                                text = ConvertFrom-CodePoints -Value @(
                                    0xBCD1, 0xD569, 0x0020, 0xC140
                                )
                            }
                        )
                        $cells = @()
                        foreach ($case in $cases) {
                            $text = [string]$case.text
                            $preferredPixels = $graphics.MeasureString(
                                $text, $font, [int]::MaxValue, $format
                            ).Width
                            $tokenWidths = @($text -split '\s+' | ForEach-Object {
                                $graphics.MeasureString(
                                    [string]$_, $font, [int]::MaxValue, $format
                                ).Width
                            })
                            if ($tokenWidths.Count -eq 0) { throw 'FONT_TOKEN_MEASUREMENT_EMPTY' }
                            $minimumPixels = [single](
                                $tokenWidths | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
                            )
                            $minimum = Convert-PixelsToMicrometers -Pixels $minimumPixels
                            $preferred = Convert-PixelsToMicrometers -Pixels $preferredPixels
                            if ($preferred -lt $minimum) { throw 'FONT_METRIC_ORDER_INVALID' }
                            $cells += [ordered]@{
                                cell_id = [string]$case.cell_id
                                text_sha256 = Get-Sha256String -Value $text
                                minimum_content_width_micrometers = $minimum
                                preferred_content_width_micrometers = $preferred
                                line_height_micrometers = $lineHeight
                            }
                        }
                        return @($cells)
                    }
                    finally { $format.Dispose() }
                }
                finally { $graphics.Dispose() }
            }
            finally { $bitmap.Dispose() }
        }
        finally { $font.Dispose() }
    }
    finally { $collection.Dispose() }
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$runRoot = [System.IO.Path]::GetFullPath((
    Join-Path $repositoryRoot 'artifacts\p06\font-metric-runs'
))
$runDirectory = [System.IO.Path]::GetFullPath((Join-Path $runRoot $RunId))
if (-not $runDirectory.StartsWith($runRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'RUN_PATH_OUTSIDE_BOUNDARY'
}
if ([System.IO.Directory]::Exists($runDirectory) -or [System.IO.File]::Exists($runDirectory)) {
    throw 'RUN_ALREADY_EXISTS'
}
[void][System.IO.Directory]::CreateDirectory($runDirectory)
$receiptPath = Join-Path $runDirectory 'receipt.json'

try {
    $programFilesX86 = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)
    $hwpPath = [System.IO.Path]::GetFullPath((
        Join-Path $programFilesX86 'HNC\Office 2020\HOffice110\bin\hwp.exe'
    ))
    if (-not [System.IO.File]::Exists($hwpPath)) { throw 'HWP_EXECUTABLE_MISSING' }
    if ((Get-Sha256File -Path $hwpPath) -cne $expectedExecutableSha256 -or
        (Get-Item -LiteralPath $hwpPath).VersionInfo.FileVersion -cne $expectedBuild) {
        throw 'HWP_EXECUTABLE_IDENTITY_MISMATCH'
    }

    $fontPath = [System.IO.Path]::GetFullPath((Join-Path $env:WINDIR ('Fonts\' + $expectedFontFile)))
    $fontRoot = [System.IO.Path]::GetFullPath((Join-Path $env:WINDIR 'Fonts')).TrimEnd('\')
    if (-not $fontPath.StartsWith($fontRoot + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
        -not [System.IO.File]::Exists($fontPath)) {
        throw 'FONT_FILE_MISSING'
    }
    $fontInfo = Get-Item -LiteralPath $fontPath
    if ($fontInfo.Length -le 0 -or $fontInfo.Length -gt 100000000 -or
        (Get-Sha256File -Path $fontPath) -cne $expectedFontSha256) {
        throw 'FONT_FILE_IDENTITY_MISMATCH'
    }

    $first = @(Invoke-MeasurementPass -FontPath $fontPath)
    $second = @(Invoke-MeasurementPass -FontPath $fontPath)
    $firstCanonical = $first | ConvertTo-Json -Depth 5 -Compress
    $secondCanonical = $second | ConvertTo-Json -Depth 5 -Compress
    if ($firstCanonical -cne $secondCanonical) { throw 'FONT_METRIC_REPEAT_MISMATCH' }

    $receipt = [ordered]@{
        schema_version = 'hwpx-agent.p06-05-current-font-metric-receipt/v1'
        run_id = $RunId
        scope = 'current_pc_named_synthetic_fixture_only'
        state = 'pass'
        profile_id = $profileId
        target = [ordered]@{
            hangul_build = $expectedBuild
            architecture = 'x86'
            executable_sha256 = $expectedExecutableSha256
            font_file_name = $expectedFontFile
            font_file_bytes = [int64]$fontInfo.Length
            font_file_sha256 = $expectedFontSha256
            font_family = $canonicalFamily
        }
        measurement = [ordered]@{
            provider = 'System.Drawing.GDIPlus.GenericTypographic/1'
            dpi = $dpi
            font_size_millipoints = $fontSizeMillipoints
            repeat_count = 2
            conversion = 'micrometers=round_away_from_zero(pixels*25400/96)'
        }
        cells = $first
        measurement_set_sha256 = Get-Sha256String -Value $firstCanonical
        visible_text_present = $false
        user_document_opened = $false
        hwp_process_created = $false
        external_network_invoked = $false
        registry_or_system_setting_changed = $false
        computer_use_click_or_type_invoked = $false
        actual_hangul_renderer = $false
        other_pc_or_version = $false
        product_complete = $false
    }
    Write-NewJson -Path $receiptPath -Value $receipt
    Write-Output $receiptPath
}
catch {
    if (-not [System.IO.File]::Exists($receiptPath)) {
        $message = [string]$_.Exception.Message
        $errorCode = if ($message -cmatch '^[A-Z0-9_]{1,80}$') { $message } else {
            'FONT_METRIC_MEASUREMENT_FAILED'
        }
        $failure = [ordered]@{
            schema_version = 'hwpx-agent.p06-05-current-font-metric-receipt/v1'
            run_id = $RunId
            scope = 'current_pc_named_synthetic_fixture_only'
            state = 'failed'
            error_code = $errorCode
            exception_message_sha256 = Get-Sha256String -Value $message
            visible_text_present = $false
            user_document_opened = $false
            hwp_process_created = $false
            external_network_invoked = $false
            registry_or_system_setting_changed = $false
            computer_use_click_or_type_invoked = $false
            actual_hangul_renderer = $false
            other_pc_or_version = $false
            product_complete = $false
        }
        Write-NewJson -Path $receiptPath -Value $failure
    }
    throw
}
