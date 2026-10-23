[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OverlayPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedOverlaySha256,
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

$errorPrefix = 'P08_OBJECT_SURFACE_BATCH'
function Get-Sha256File {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-NewUtf8File {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
    $stream = [IO.File]::Open(
        $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
}

function Add-Progress {
    param([Parameter(Mandatory)][object]$Value)
    $line = ($Value | ConvertTo-Json -Compress -Depth 6) + "`n"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($line)
    $stream = [IO.File]::Open(
        $ProgressPath, [IO.FileMode]::Append, [IO.FileAccess]::Write, [IO.FileShare]::Read
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
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
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { throw ($errorPrefix + '_LOCALSERVER32_PARSE_FAILED') }
    $path = (Resolve-Path -LiteralPath $match.Groups['path'].Value).Path
    return [ordered]@{
        path = $path
        sha256 = Get-Sha256File -Path $path
    }
}

if (-not [Environment]::Is64BitOperatingSystem -or [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA) {
    throw ($errorPrefix + '_REQUIRES_X86_STA')
}
if (Test-Path -LiteralPath $TracePath -PathType Leaf) {
    throw ($errorPrefix + '_TRACE_ALREADY_EXISTS')
}
if (Test-Path -LiteralPath $ProgressPath -PathType Leaf) {
    throw ($errorPrefix + '_PROGRESS_ALREADY_EXISTS')
}
if (@(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue).Count -ne 0) {
    throw ($errorPrefix + '_PREEXISTING_HWP_PROCESS')
}
foreach ($pair in @(
    @($OverlayPath, $ExpectedOverlaySha256),
    @($FixtureManifestPath, $ExpectedFixtureManifestSha256)
)) {
    if (-not (Test-Path -LiteralPath ([string]$pair[0]) -PathType Leaf) -or
        (Get-Sha256File -Path ([string]$pair[0])) -cne [string]$pair[1]) {
        throw ($errorPrefix + '_INPUT_IDENTITY_MISMATCH')
    }
}

$overlay = Get-Content -LiteralPath $OverlayPath -Raw -Encoding UTF8 | ConvertFrom-Json
$manifest = Get-Content -LiteralPath $FixtureManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$serverIdentity = Get-ComServerIdentity -RequestedProgId $ProgId
if ([string]$serverIdentity.sha256 -cne $ExpectedExecutableSha256) {
    throw ($errorPrefix + '_COM_SERVER_IDENTITY_MISMATCH')
}
$routes = @($overlay.routes)
$candidates = @($routes | Where-Object { $_.state -ceq 'candidate_unverified' })
$excluded = @($candidates | Where-Object { $_.modal_risk -ceq 'known_modal' })
$probes = @($candidates | Where-Object { $_.modal_risk -cne 'known_modal' } | Sort-Object feature_id)
if ([string]$overlay.schema_version -cne
        'hwpx-agent.p08-object-automation-binding-overlay/v1' -or
    $routes.Count -ne 42 -or $candidates.Count -ne 40 -or
    $excluded.Count -ne 2 -or $probes.Count -ne 38 -or
    (@($excluded.feature_id | Sort-Object) -join ',') -cne 'OBJ-003,OBJ-043' -or
    [string]$manifest.schema_version -cne 'hwpx-agent.p08-19-object-target-bundle/v1' -or
    @($manifest.cases).Count -ne 41) {
    throw ($errorPrefix + '_INPUT_CONTRACT_MISMATCH')
}
$trace = [ordered]@{
    schema_version = 'hwpx-agent.p08-object-surface-batch-private/v1'
    state = 'failed'
    overlay_sha256 = $ExpectedOverlaySha256
    fixture_manifest_sha256 = $ExpectedFixtureManifestSha256
    target_build = $null
    target_executable_sha256 = [string]$serverIdentity.sha256
    hwp_process_identity_verified = $false
    candidate_count = 40
    probed_case_count = 38
    excluded_known_modal = @($excluded.feature_id | Sort-Object)
    completed_case_count = 0
    action_case_count = 0
    method_case_count = 0
    enabled_case_count = 0
    action_created_count = 0
    set_created_count = 0
    get_default_passed_count = 0
    method_present_count = 0
    action_execute_count = 0
    document_save_count = 0
    hwp_file_open_count = 0
    user_document_opened = $false
    external_network_invoked = $false
    registry_or_system_setting_changed = $false
    computer_use_click_or_type_invoked = $false
    security_module_register_invoked = $false
    quit_invoked = $false
    cases = @()
    error_code = $null
}

$hwp = $null
$documents = $null
$document = $null
$window = $null
$action = $null
$set = $null
try {
    Add-Progress -Value ([ordered]@{ event = 'starting'; completed = 0; total = 38 })
    $hwp = New-Object -ComObject $ProgId
    $trace.target_build = ([string]$hwp.Version).Replace(',', '.').Replace(' ', '')
    if ($trace.target_build -cne $ExpectedBuild) {
        throw ($errorPrefix + '_TARGET_BUILD_MISMATCH')
    }
    $hwpProcesses = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" `
        -ErrorAction SilentlyContinue)
    if ($hwpProcesses.Count -ne 1 -or
        [string]::IsNullOrWhiteSpace([string]$hwpProcesses[0].ExecutablePath) -or
        (Get-Sha256File -Path ([string]$hwpProcesses[0].ExecutablePath)) -cne
            $ExpectedExecutableSha256) {
        throw ($errorPrefix + '_HWP_PROCESS_IDENTITY_MISMATCH')
    }
    $trace.hwp_process_identity_verified = $true
    $documents = $hwp.XHwpDocuments
    $window = $hwp.XHwpWindows.Item(0)
    $window.Visible = $true
    $document = $documents.Add($false)
    if ($null -eq $document) {
        throw ($errorPrefix + '_DOCUMENT_ADD_FAILED')
    }
    [void]$document.SetActive_XHwpDocument()

    foreach ($route in $probes) {
        $featureId = [string]$route.feature_id
        $result = [ordered]@{
            feature_id = $featureId
            capability_id = [string]$route.capability_id
            source_kind = [string]$route.source_kind
            source_name = [string]$route.source_name
            modal_risk = [string]$route.modal_risk
            context = 'one_shared_blank_disposable_document'
            is_action_enable = $null
            action_created = $false
            set_created = $false
            get_default_state = 'not_applicable'
            method_present = $null
            state = 'failed'
            error_code = $null
        }
        Add-Progress -Value ([ordered]@{
            event = 'case_start'; feature_id = $featureId
            completed = $trace.completed_case_count; total = 38
        })
        try {
            if ([string]$route.source_kind -ceq 'automation_object') {
                $trace.method_case_count += 1
                $methodName = ([string]$route.source_name).Replace('(Method)', '')
                $member = @($hwp | Get-Member -Name $methodName -MemberType Method)
                $result.method_present = $member.Count -eq 1
                if ($result.method_present) {
                    $trace.method_present_count += 1
                    $result.state = 'surface_present_method_not_invoked'
                }
                else {
                    $result.state = 'surface_absent'
                }
            }
            else {
                $trace.action_case_count += 1
                $result.is_action_enable = [bool]$hwp.IsActionEnable([string]$route.source_name)
                if ($result.is_action_enable) { $trace.enabled_case_count += 1 }
                $action = $hwp.CreateAction([string]$route.source_name)
                if ($null -eq $action) {
                    $result.state = 'surface_absent'
                }
                else {
                    $result.action_created = $true
                    $trace.action_created_count += 1
                    try {
                        $set = $action.CreateSet()
                        if ($null -ne $set) {
                            $result.set_created = $true
                            $trace.set_created_count += 1
                            if ([bool]$action.GetDefault($set)) {
                                $result.get_default_state = 'pass'
                                $trace.get_default_passed_count += 1
                            }
                            else { $result.get_default_state = 'returned_false' }
                        }
                    }
                    catch {
                        $result.get_default_state = 'not_supported_or_failed'
                    }
                    $result.state = if ($result.is_action_enable) {
                        'surface_present_enabled'
                    }
                    else { 'surface_present_disabled_in_blank_context' }
                }
            }
        }
        catch {
            $result.error_code = [string]$_.Exception.Message
        }
        finally {
            Clear-ComObject -Value $set
            Clear-ComObject -Value $action
            $set = $null
            $action = $null
        }
        $trace.cases += $result
        $trace.completed_case_count += 1
        Add-Progress -Value ([ordered]@{
            event = 'case_complete'; feature_id = $featureId; state = $result.state
            completed = $trace.completed_case_count; total = 38
        })
    }
    [void]$document.Close($false)
    Clear-ComObject -Value $document
    $document = $null
    $hwp.Quit()
    $trace.quit_invoked = $true
    if ($trace.completed_case_count -ne 38 -or
        @($trace.cases | Where-Object { $_.state -eq 'failed' }).Count -ne 0 -or
        $trace.hwp_file_open_count -ne 0 -or
        $trace.action_execute_count -ne 0 -or $trace.document_save_count -ne 0) {
        throw ($errorPrefix + '_BATCH_INCOMPLETE')
    }
    $trace.state = 'pass'
}
catch {
    $trace.error_code = [string]$_.Exception.Message
}
finally {
    Clear-ComObject -Value $set
    Clear-ComObject -Value $action
    if ($null -ne $document) { try { [void]$document.Close($false) } catch { } }
    Clear-ComObject -Value $document
    Clear-ComObject -Value $window
    Clear-ComObject -Value $documents
    if ($null -ne $hwp -and -not $trace.quit_invoked) {
        try { $hwp.Quit(); $trace.quit_invoked = $true } catch { }
    }
    Clear-ComObject -Value $hwp
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$json = $trace | ConvertTo-Json -Depth 8
Write-NewUtf8File -Path $TracePath -Content $json
$json
if ($trace.state -cne 'pass') { exit 2 }
