[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunDirectory,
    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$errorPrefix = 'P09_CLICK_HERE_DISCOVERY'
$ProgId = 'HWPFrame.HwpObject.2'
$ExpectedBuild = '11.0.0.9136'
$ExpectedExecutableSha256 = '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
$securityModuleName = 'FilePathCheckerModuleExample'
$securityModuleSha256 = '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')).TrimEnd('\')
$helperPath = Join-Path $PSScriptRoot 'run-hancom-2020-field-auto-number-target.ps1'
$helperSha256 = '30341f7a7ff5106e4c3ac74331abdd9b612ec4d88eb060387b506809399338a9'
if ((Get-FileHash -LiteralPath $helperPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $helperSha256) {
    throw 'P09_CLICK_HERE_DISCOVERY_HELPER_DRIFT'
}

# 기존 검증 엔진의 정확히 고정된 lifecycle 함수만 재사용한다.
# 원본 스크립트의 실행부나 임의 사용자 입력을 dot-source하지 않는다.
$parseTokens = $null
$parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($helperPath, [ref]$parseTokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'P09_CLICK_HERE_DISCOVERY_HELPER_PARSE' }
$helpers = @('Get-Sha256File', 'Get-Sha256String', 'Write-NewUtf8File', 'Clear-ComObject',
    'Assert-RegularBoundedFile', 'Get-OwnedHwpIdentity', 'New-ExactHwpSession', 'Close-HwpSession')
foreach ($name in $helpers) {
    $definitions = @($ast.FindAll({ param($node)
        $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name
    }, $true))
    if ($definitions.Count -ne 1) { throw 'P09_CLICK_HERE_DISCOVERY_HELPER_AMBIGUOUS' }
    . ([ScriptBlock]::Create($definitions[0].Extent.Text))
}

$boundary = Join-Path $root 'implementation\p09\evidence\private'
$run = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
if ((Split-Path -Parent $run) -cne $boundary -or
    (Split-Path -Leaf $run) -cnotmatch '^p09-22-click-here-discovery-[a-z0-9-]{1,64}$' -or
    (Test-Path -LiteralPath $run)) { throw 'P09_CLICK_HERE_DISCOVERY_RUN_BOUNDARY' }
$ancestor = $boundary
while (-not [string]::IsNullOrEmpty($ancestor)) {
    $item = Get-Item -LiteralPath $ancestor -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'P09_CLICK_HERE_DISCOVERY_LINKED_BOUNDARY'
    }
    $ancestor = Split-Path -Parent $ancestor
}
$docPath = Join-Path $root 'fixtures\target-build\official-source-cache\devcenter-archive-main-20260906\hwp-automation\HwpAutomation.pdf'
$docSha256 = 'c787c69d46f26a9fca49ac9d34106bb4f146fb29da9f1caf92c6e77d46cef45b'
if ((Get-Sha256File $docPath) -cne $docSha256) { throw 'P09_CLICK_HERE_DISCOVERY_OFFICIAL_DOC_DRIFT' }
if ([Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw 'P09_CLICK_HERE_DISCOVERY_REQUIRES_X86_STA'
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'").Count -ne 0) {
    throw 'P09_CLICK_HERE_DISCOVERY_PREEXISTING_HWP'
}
$securityPath = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'hwpx-agent\HancomAutomation\FilePathCheckerModuleExample.dll'
$securityItem = Assert-RegularBoundedFile $securityPath 217229 217229
if ((Get-Sha256File $securityPath) -cne $securityModuleSha256) { throw 'P09_CLICK_HERE_DISCOVERY_MODULE_DRIFT' }
$registry = Get-Item -LiteralPath 'Registry::HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules'
try {
    if ([string]$registry.GetValueKind($securityModuleName) -cne 'String' -or
        [string]$registry.GetValue($securityModuleName) -cne $securityItem.FullName) {
        throw 'P09_CLICK_HERE_DISCOVERY_MODULE_REGISTRY_MISMATCH'
    }
} finally { $registry.Dispose() }
if ($ValidateOnly) {
    Write-Output '{"state":"preflight_pass","com_created":false,"files_created":false}'
    exit 0
}

function Save-DiscoveryArtifact {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Format,
        [Parameter(Mandatory)][long]$Maximum)
    $path = Join-Path $run $Name
    if (Test-Path -LiteralPath $path) { throw 'P09_CLICK_HERE_DISCOVERY_OUTPUT_EXISTS' }
    if ($document.SaveAs($path, $Format, '') -eq $false) { throw 'P09_CLICK_HERE_DISCOVERY_SAVE_FAILED' }
    $saved = Assert-RegularBoundedFile $path 5 $Maximum
    $trace.artifacts[$Name] = [ordered]@{ sha256 = Get-Sha256File $path; bytes = [long]$saved.Length }
}

# 폐기용 알려진 값만 사용하고 값 자체는 trace/출력에 넣지 않는다.
$fieldName = 'p09-click-field'
$direction = 'P09 prompt & <guide>'
$memo = 'P09 help & <memo>'
# Windows PowerShell 5.1 호환성을 위해 명시적 코드포인트를 사용한다.
$filledText = 'P09 value & <text> ' + [char]0xD55C + [char]0xAE00
[void][IO.Directory]::CreateDirectory($run)
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p09-click-here-discovery-trace/v1'
    task = 'P09-22'; state = 'effect_unknown'; started_at_utc = [datetime]::UtcNow.ToString('o')
    target = [ordered]@{ product = 'Hancom Hangul 2020'; build = $ExpectedBuild;
        architecture = 'x86'; locale = 'ko-KR'; prog_id = $ProgId; executable_sha256 = $ExpectedExecutableSha256 }
    lifecycle_helper_sha256 = $helperSha256; official_api_pdf_sha256 = $docSha256
    security_module_sha256 = $securityModuleSha256; security_preflight = 'pass'
    sessions = New-Object Collections.ArrayList
    create_field = 'not_run'; field_list = 'not_run'; filled_readback = 'not_run'; fresh_readback = 'not_run'
    field_name_sha256 = Get-Sha256String $fieldName; direction_sha256 = Get-Sha256String $direction
    memo_sha256 = Get-Sha256String $memo; filled_text_sha256 = Get-Sha256String $filledText
    artifacts = [ordered]@{}; failed_phase = $null; error_code = $null
    raw_document_text_present = $false; user_document_scanned = $false; external_network_invoked = $false
    registry_or_system_setting_changed = $false; computer_use_click_or_type_invoked = $false
    product_routing_qualified = $false; p09_complete = $false; product_complete = $false
}
$session = $null
$document = $null
$phase = 'first_session'
try {
    $session = New-ExactHwpSession -SessionLabel 'capture' -Trace $trace
    $phase = 'create_field'
    if ($session.hwp.CreateField($direction, $memo, $fieldName) -eq $false) {
        throw 'P09_CLICK_HERE_DISCOVERY_CREATE_FAILED'
    }
    $trace.create_field = 'pass'
    $phase = 'field_list'
    if ([string]$session.hwp.GetFieldList(0, 2) -cne $fieldName) {
        throw 'P09_CLICK_HERE_DISCOVERY_LIST_MISMATCH'
    }
    $trace.field_list = 'pass'
    $document = $session.documents.Item(0)
    [void]$document.SetActive_XHwpDocument()
    $phase = 'empty_save'
    Save-DiscoveryArtifact 'empty.hwpx' 'HWPX' 4194304
    $phase = 'put_text'
    [void]$session.hwp.PutFieldText($fieldName, $filledText)
    if ([string]$session.hwp.GetFieldText($fieldName) -cne $filledText) {
        throw 'P09_CLICK_HERE_DISCOVERY_FILLED_TEXT_MISMATCH'
    }
    $trace.filled_readback = 'pass'
    $phase = 'filled_save'
    Save-DiscoveryArtifact 'filled.hwpx' 'HWPX' 4194304
    Save-DiscoveryArtifact 'filled.pdf' 'PDF' 33554432
    Clear-ComObject $document; $document = $null
    Close-HwpSession $session; $session = $null
    $phase = 'fresh_session'
    $session = New-ExactHwpSession -SessionLabel 'reopen' -Trace $trace
    $phase = 'fresh_open'
    Write-Output 'P09_CLICK_HERE_READY_FOR_FRESH_OPEN'
    if ($session.hwp.Open((Join-Path $run 'filled.hwpx'), 'HWPX', 'lock:false;setcurdir:false') -eq $false) {
        throw 'P09_CLICK_HERE_DISCOVERY_REOPEN_FAILED'
    }
    if ([string]$session.hwp.GetFieldList(0, 2) -cne $fieldName -or
        [string]$session.hwp.GetFieldText($fieldName) -cne $filledText) {
        throw 'P09_CLICK_HERE_DISCOVERY_FRESH_TEXT_MISMATCH'
    }
    $trace.fresh_readback = 'pass'
    $document = $session.documents.Item($session.documents.Count - 1)
    [void]$document.SetActive_XHwpDocument()
    $phase = 'fresh_save'
    Save-DiscoveryArtifact 'reopened.hwpx' 'HWPX' 4194304
    Save-DiscoveryArtifact 'reopened.pdf' 'PDF' 33554432
    $trace.state = 'pass'
} catch {
    $trace.failed_phase = $phase
    $trace.error_code = if ([string]$_.Exception.Message -match '^P09_CLICK_HERE_DISCOVERY_[A-Z_]+$') {
        [string]$_.Exception.Message
    } else { 'P09_CLICK_HERE_DISCOVERY_EXCEPTION' }
} finally {
    Clear-ComObject $document
    Close-HwpSession $session
    Start-Sleep -Milliseconds 500
    $trace.remaining_hwp_process_count = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue).Count
    $trace.completed_at_utc = [datetime]::UtcNow.ToString('o')
    $tracePath = Join-Path $run 'discovery-trace.json'
    Write-NewUtf8File $tracePath ($trace | ConvertTo-Json -Depth 12)
}
Write-Output (([ordered]@{ state = $trace.state; failed_phase = $trace.failed_phase;
    error_code = $trace.error_code; remaining_hwp = $trace.remaining_hwp_process_count;
    trace_sha256 = Get-Sha256File $tracePath }) | ConvertTo-Json -Compress)
if ($trace.state -ne 'pass' -or $trace.remaining_hwp_process_count -ne 0) { exit 2 }
