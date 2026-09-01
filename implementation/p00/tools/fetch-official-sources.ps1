[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$archiveRoot = Join-Path $projectRoot 'implementation\p00\source-archive\original'

$downloads = @(
    @{
        Relative = 'automation\ActionTable_2504.pdf'
        Uri = 'https://github.com/hancom-io/devcenter-archive/raw/main/hwp-automation/ActionTable_2504.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'automation\HwpAutomation_2504.pdf'
        Uri = 'https://github.com/hancom-io/devcenter-archive/raw/main/hwp-automation/HwpAutomation_2504.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'automation\ParameterSetTable_2504.pdf'
        Uri = 'https://github.com/hancom-io/devcenter-archive/raw/main/hwp-automation/ParameterSetTable_2504.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'automation\EventHandler_2504.pdf'
        Uri = 'https://github.com/hancom-io/devcenter-archive/raw/main/hwp-automation/%ED%95%9C%EA%B8%80%EC%98%A4%ED%86%A0%EB%A9%94%EC%9D%B4%EC%85%98EventHandler%EC%B6%94%EA%B0%80_2504.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'format\HWPML_3.0_revision1.2.pdf'
        Uri = 'https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D3.0_HWPML_revision1.2.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'format\HWP_5.0_revision1.3.pdf'
        Uri = 'https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_5.0_revision1.3.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'format\HWP_Distribution_revision1.2.pdf'
        Uri = 'https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_%EB%B0%B0%ED%8F%AC%EC%9A%A9%EB%AC%B8%EC%84%9C_revision1.2.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'format\HWP_Equation_revision1.3.pdf'
        Uri = 'https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_%EC%88%98%EC%8B%9D_revision1.3.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'format\HWP_Chart_revision1.2.pdf'
        Uri = 'https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_%EC%B0%A8%ED%8A%B8_revision1.2.pdf'
        Kind = 'pdf'
    },
    @{
        Relative = 'web\HancomAutomation_20260901.html'
        Uri = 'https://developer.hancom.com/hwpautomation'
        Kind = 'html'
    },
    @{
        Relative = 'web\WebHWP_DevGuide_20260901.html'
        Uri = 'https://developer.hancom.com/en-us/webhwp/devguide'
        Kind = 'html'
    },
    @{
        Relative = 'web\HWP_OWPML_DownloadCenter_20260901.html'
        Uri = 'https://online.hancom.co.kr/support/downloadCenter/hwpOwpml'
        Kind = 'html'
    },
    @{
        Relative = 'web\HOffice2022_Update_20260901.html'
        Uri = 'https://help.hancom.com/updates/hoffice120/ko-KR/HOffice2022_update.htm'
        Kind = 'html'
    },
    @{
        Relative = 'web\HOffice2022_Update_app_20260901.js'
        Uri = 'https://help.hancom.com/updates/hoffice120/ko-KR/app.js'
        Kind = 'text'
    },
    @{
        Relative = 'web\HOffice2024_Update_20260901.html'
        Uri = 'https://help.hancom.com/updates/hoffice130/ko-KR/HOffice2024_update.htm'
        Kind = 'html'
    },
    @{
        Relative = 'web\HOffice2024_Update_app_20260901.js'
        Uri = 'https://help.hancom.com/updates/hoffice130/ko-KR/app.js'
        Kind = 'text'
    },
    @{
        Relative = 'web\HOffice2020_Update_20260901.html'
        Uri = 'https://help.hancom.com/updates/hoffice110/ko-KR/HOffice2020_update.htm'
        Kind = 'html'
    },
    @{
        Relative = 'web\HOffice2020_Update_app_20260901.js'
        Uri = 'https://help.hancom.com/updates/hoffice110/ko-KR/app.js'
        Kind = 'text'
    },
    @{
        Relative = 'web\ProductSupportStatus_20260901.html'
        Uri = 'https://www.hancom.com/support/csCenter/prdStatus'
        Kind = 'html'
    },
    @{
        Relative = 'web\KS_X_6101_Standard_Detail_20260901.html'
        Uri = 'https://www.standard.go.kr/KSCI/standardIntro/getStandardSearchView.do?ksNo=KSX6101&menuId=503&tmprKsNo=KSX6101&topMenuId=502'
        Kind = 'html'
    },
    @{
        Relative = 'web\KS_X_6101_MachineReadable_20260901.html'
        Uri = 'https://www.standard.go.kr/KSCI/api/std/viewMachine.do?reformNo=03&tmprKsNo=KSX6101&formType=STD'
        Kind = 'html'
    },
    @{
        Relative = 'web\KS_X_6101_MachineReadable_Content_20260901.json'
        Uri = 'https://www.standard.go.kr/KSCI/api/std/viewMachineNextPage.do?format=json'
        Method = 'Post'
        Body = 'tmprKsNo=KSX6101&reformNo=03&formType=STD'
        ContentType = 'application/x-www-form-urlencoded'
        Kind = 'json'
        RequiredMarkers = @(
            'KSX6101',
            '"title"',
            '"content"',
            '"info"'
        )
    },
    @{
        Relative = 'web\Hancom2020_Hwp_License_20260901.html'
        Uri = 'https://help.hancom.com/hoffice110/ko-KR/Hwp/rights/rights.htm'
        Kind = 'html'
    },
    @{
        Relative = 'web\Hancom_HCR_Font_License_FAQ_20260901.html'
        Uri = 'https://download.hancom.com/support/faqCenter/faq/detail/2301'
        Kind = 'html'
    }
)

New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$archiveRoot = (Resolve-Path -LiteralPath $archiveRoot).Path

$results = foreach ($item in $downloads) {
    $target = Join-Path $archiveRoot $item.Relative
    $targetParent = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    $resolvedParent = (Resolve-Path -LiteralPath $targetParent).Path

    if (-not $resolvedParent.StartsWith($archiveRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved target escaped archive root: $target"
    }

    $partial = "$target.partial"
    if (Test-Path -LiteralPath $target) {
        [pscustomobject]@{
            relative = $item.Relative.Replace('\', '/')
            status = 'skipped_existing'
            bytes = (Get-Item -LiteralPath $target).Length
            sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
            origin = $item.Uri
        }
        continue
    }
    if (Test-Path -LiteralPath $partial) {
        [pscustomobject]@{
            relative = $item.Relative.Replace('\', '/')
            status = 'blocked_partial'
            bytes = (Get-Item -LiteralPath $partial).Length
            sha256 = $null
            origin = $item.Uri
            error = 'A previous partial download exists and will not be overwritten.'
        }
        continue
    }

    try {
        $request = @{
            Uri = $item.Uri
            OutFile = $partial
            UseBasicParsing = $true
            MaximumRedirection = 10
        }
        if ($item.Method) {
            $request.Method = $item.Method
        }
        if ($item.Body) {
            $request.Body = $item.Body
        }
        if ($item.ContentType) {
            $request.ContentType = $item.ContentType
        }
        Invoke-WebRequest @request
        $bytes = [System.IO.File]::ReadAllBytes($partial)
        if ($bytes.Length -eq 0) {
            throw "Downloaded artifact is empty: $($item.Relative)"
        }
        if ($item.Kind -eq 'pdf') {
            $magic = [System.Text.Encoding]::ASCII.GetString($bytes, 0, [Math]::Min(5, $bytes.Length))
            if ($magic -ne '%PDF-') {
                throw "Unexpected PDF magic for $($item.Relative): $magic"
            }
        }
        if ($item.Kind -eq 'json') {
            $text = [System.Text.Encoding]::UTF8.GetString($bytes)
            $parsed = $text | ConvertFrom-Json
            if ($null -eq $parsed) {
                throw "Downloaded JSON could not be parsed: $($item.Relative)"
            }
            foreach ($marker in @($item.RequiredMarkers)) {
                if (-not $text.Contains($marker)) {
                    throw "Downloaded JSON is missing required marker '$marker': $($item.Relative)"
                }
            }
        }

        Move-Item -LiteralPath $partial -Destination $target
        [pscustomobject]@{
            relative = $item.Relative.Replace('\', '/')
            status = 'downloaded'
            bytes = $bytes.Length
            sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
            origin = $item.Uri
        }
    }
    catch {
        [pscustomobject]@{
            relative = $item.Relative.Replace('\', '/')
            status = 'failed'
            bytes = if (Test-Path -LiteralPath $partial) { (Get-Item -LiteralPath $partial).Length } else { 0 }
            sha256 = $null
            origin = $item.Uri
            error = $_.Exception.Message
        }
    }
}

$results | ConvertTo-Json -Depth 4
