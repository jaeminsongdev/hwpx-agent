[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RequestPath,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [ValidateRange(5, 120)]
    [int]$TimeoutSeconds = 45
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256Lower {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-StringSha256Lower {
    param([AllowEmptyString()][string]$Value)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($bytes)) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )
    if (Test-Path -LiteralPath $Path) {
        throw "Refusing to overwrite diagnostic artifact: $Path"
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 12), $encoding)
}

function Get-PropertyValue {
    param(
        [AllowNull()]$InputObject,
        [Parameter(Mandatory)][string]$Name
    )
    if ($null -eq $InputObject) {
        return $null
    }
    $property = $InputObject.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function ConvertTo-NormalizedHancomVersion {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }
    $match = [regex]::Match(
        $Value,
        '^\s*(?<major>\d+)\s*[\.,]\s*(?<minor>\d+)\s*[\.,]\s*(?<build>\d+)\s*[\.,]\s*(?<revision>\d+)\s*$'
    )
    if (-not $match.Success) {
        return $null
    }
    $parts = @('major', 'minor', 'build', 'revision') | ForEach-Object {
        [uint32]$match.Groups[$_].Value
    }
    return ($parts -join '.')
}

function Get-PeArchitecture {
    param([Parameter(Mandatory)][string]$Path)
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        $reader = New-Object System.IO.BinaryReader($stream)
        try {
            if ($reader.ReadUInt16() -ne 0x5A4D) {
                return 'unknown'
            }
            $stream.Position = 0x3C
            $peOffset = $reader.ReadInt32()
            if ($peOffset -lt 0 -or $peOffset -gt ($stream.Length - 6)) {
                return 'unknown'
            }
            $stream.Position = $peOffset
            if ($reader.ReadUInt32() -ne 0x00004550) {
                return 'unknown'
            }
            $machine = $reader.ReadUInt16()
            switch ($machine) {
                0x014c { return 'x86' }
                0x8664 { return 'x64' }
                0xaa64 { return 'arm64' }
                default { return ('unknown-0x{0:x4}' -f $machine) }
            }
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-SafePathDescriptor {
    param([AllowNull()][string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    $full = [System.IO.Path]::GetFullPath($Path)
    $roots = @(
        @{ Name = 'program_files_x86'; Path = ${env:ProgramFiles(x86)} },
        @{ Name = 'program_files'; Path = $env:ProgramFiles },
        @{ Name = 'windows'; Path = $env:WINDIR }
    )
    foreach ($root in $roots) {
        if ([string]::IsNullOrWhiteSpace([string]$root.Path)) {
            continue
        }
        $rootPath = [System.IO.Path]::GetFullPath([string]$root.Path).TrimEnd('\')
        if ($full.StartsWith($rootPath + '\', [System.StringComparison]::OrdinalIgnoreCase) -or $full.Equals($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            return [ordered]@{
                scope = $root.Name
                relative_path = $full.Substring($rootPath.Length).TrimStart('\').Replace('\', '/')
                file_name = [System.IO.Path]::GetFileName($full)
                path_sha256 = Get-StringSha256Lower -Value $full.ToLowerInvariant()
            }
        }
    }
    return [ordered]@{
        scope = if ($full.StartsWith([Environment]::GetFolderPath('UserProfile'), [System.StringComparison]::OrdinalIgnoreCase)) { 'user_profile_redacted' } else { 'other_redacted' }
        relative_path = $null
        file_name = [System.IO.Path]::GetFileName($full)
        path_sha256 = Get-StringSha256Lower -Value $full.ToLowerInvariant()
    }
}

function Get-ObservedMajorRelease {
    param(
        [Parameter(Mandatory)][string]$ExecutablePath,
        [AllowNull()][string]$ProductName,
        [AllowNull()][string]$FileDescription,
        [AllowNull()][string]$FileVersion
    )
    $identityText = "$ExecutablePath`n$ProductName`n$FileDescription"
    $releaseMatch = [regex]::Match($identityText, '(?<!\d)(20(?:2[0-9]|[3-9][0-9]))(?!\d)')
    if ($releaseMatch.Success) {
        return $releaseMatch.Groups[1].Value
    }
    $normalized = ConvertTo-NormalizedHancomVersion -Value $FileVersion
    if ($null -ne $normalized) {
        $fileMajor = [int]($normalized.Split('.')[0])
        switch ($fileMajor) {
            11 { return '2020' }
            12 { return '2022' }
            13 { return '2024' }
        }
    }
    return $null
}

function Get-ComRegistrationCandidates {
    param([Parameter(Mandatory)][string]$ProgId)
    $candidates = @()
    foreach ($view in @([Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64)) {
        $classesRoot = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot, $view)
        try {
            $progIdKey = $classesRoot.OpenSubKey($ProgId)
            if ($null -eq $progIdKey) {
                continue
            }
            $clsidKey = $progIdKey.OpenSubKey('CLSID')
            if ($null -eq $clsidKey) {
                continue
            }
            $clsid = [string]$clsidKey.GetValue('')
            $classKey = $classesRoot.OpenSubKey("CLSID\$clsid")
            $serverKey = if ($null -ne $classKey) { $classKey.OpenSubKey('LocalServer32') } else { $null }
            if ($null -eq $serverKey) {
                continue
            }
            $serverCommand = [string]$serverKey.GetValue('')
            $serverMatch = [regex]::Match(
                $serverCommand.Trim(),
                '^(?:"(?<path>[^"]+\.exe)"|(?<path>.+?\.exe))(?:\s|$)',
                [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
            if (-not $serverMatch.Success) {
                continue
            }
            $rawPath = $serverMatch.Groups['path'].Value
            if (-not (Test-Path -LiteralPath $rawPath -PathType Leaf)) {
                continue
            }
            $resolvedPath = (Resolve-Path -LiteralPath $rawPath).Path
            $item = Get-Item -LiteralPath $resolvedPath
            $architecture = Get-PeArchitecture -Path $resolvedPath
            $expectedView = if ($architecture -eq 'x86') { 'Registry32' } elseif ($architecture -eq 'x64') { 'Registry64' } else { $null }
            $viewName = [string]$view
            $candidates += [pscustomobject]@{
                registry_view = $viewName
                registry_architecture_match = $null -ne $expectedView -and $expectedView -eq $viewName
                clsid = $clsid
                executable_path = $resolvedPath
                executable_path_descriptor = Get-SafePathDescriptor -Path $resolvedPath
                executable_sha256 = Get-Sha256Lower -Path $resolvedPath
                file_version = [string]$item.VersionInfo.FileVersion
                product_version = [string]$item.VersionInfo.ProductVersion
                product_name = [string]$item.VersionInfo.ProductName
                file_description = [string]$item.VersionInfo.FileDescription
                architecture = $architecture
                observed_major_release = Get-ObservedMajorRelease -ExecutablePath $resolvedPath -ProductName ([string]$item.VersionInfo.ProductName) -FileDescription ([string]$item.VersionInfo.FileDescription) -FileVersion ([string]$item.VersionInfo.FileVersion)
                server_command_class = if ($serverCommand -match '(?i)-Automation') { 'automation_local_server' } else { 'local_server_without_automation_marker' }
            }
        }
        finally {
            $classesRoot.Dispose()
        }
    }
    return @($candidates)
}

function Get-InstalledProductInventory {
    $roots = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    $koreanHancom = -join @([char]0xD55C, [char]0xCEF4)
    $koreanHangul = -join @([char]0xD55C, [char]0xAE00)
    $productPattern = '(?i)' + [regex]::Escape($koreanHancom) + '|Hancom|' + [regex]::Escape($koreanHangul) + '|Hangul'
    $seen = @{}
    $items = @()
    foreach ($product in @(Get-ItemProperty -Path $roots -ErrorAction SilentlyContinue | Where-Object { [string](Get-PropertyValue -InputObject $_ -Name 'DisplayName') -match $productPattern })) {
        $displayName = [string](Get-PropertyValue -InputObject $product -Name 'DisplayName')
        $displayVersion = [string](Get-PropertyValue -InputObject $product -Name 'DisplayVersion')
        $publisher = [string](Get-PropertyValue -InputObject $product -Name 'Publisher')
        $installLocation = [string](Get-PropertyValue -InputObject $product -Name 'InstallLocation')
        $key = "{0}|{1}|{2}" -f $displayName, $displayVersion, $installLocation
        if ($seen.ContainsKey($key)) {
            continue
        }
        $seen[$key] = $true
        $items += [ordered]@{
            display_name = $displayName
            display_version = $displayVersion
            publisher = $publisher
            install_location = Get-SafePathDescriptor -Path $installLocation
        }
    }
    return @($items)
}

function Get-TargetFileInventory {
    param([Parameter(Mandatory)][string]$ExecutablePath)
    $binRoot = Split-Path -Parent $ExecutablePath
    $relativePaths = @(
        'Hwp.exe',
        'HwpAutomation.dll',
        'HwpAutomation.tlb',
        'HwpCtrl.tlb',
        'Resource\Hwp\Help\ko-KR\Hwp.chm',
        'Resource\Hwp\Help\en-US\Hwp.chm'
    )
    $result = @()
    foreach ($relative in $relativePaths) {
        $path = Join-Path $binRoot $relative
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        $item = Get-Item -LiteralPath $path
        $result += [ordered]@{
            role = $relative.Replace('\', '/')
            path = Get-SafePathDescriptor -Path $path
            bytes = [int64]$item.Length
            sha256 = Get-Sha256Lower -Path $path
            file_version = [string]$item.VersionInfo.FileVersion
        }
    }
    return @($result)
}

function Get-FontInventory {
    $fontRoot = Join-Path $env:WINDIR 'Fonts'
    $files = @()
    foreach ($pattern in @('HAN*.ttf', 'HCR*.ttf', 'Hancom*.ttf', 'malgun*.ttf')) {
        $files += @(Get-ChildItem -LiteralPath $fontRoot -Filter $pattern -File -ErrorAction SilentlyContinue)
    }
    $seen = @{}
    $result = @()
    foreach ($file in @($files | Sort-Object Name)) {
        if ($seen.ContainsKey($file.FullName.ToLowerInvariant())) {
            continue
        }
        $seen[$file.FullName.ToLowerInvariant()] = $true
        $result += [ordered]@{
            file_name = $file.Name
            bytes = [int64]$file.Length
            sha256 = Get-Sha256Lower -Path $file.FullName
        }
    }
    return @($result)
}

function Get-PrinterInventory {
    $allowedNames = @('Microsoft Print to PDF', 'Hancom PDF')
    $result = @()
    foreach ($printer in @(Get-CimInstance Win32_Printer -ErrorAction SilentlyContinue | Where-Object { $_.Name -in $allowedNames })) {
        $result += [ordered]@{
            name = [string]$printer.Name
            driver_name = [string]$printer.DriverName
            is_default = [bool]$printer.Default
            is_network = [bool]$printer.Network
        }
    }
    return @($result)
}

function Get-CrashDumpMetadata {
    param([Parameter(Mandatory)][datetime]$Since)
    $roots = @(
        (Join-Path $env:LOCALAPPDATA 'CrashDumps'),
        (Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportArchive'),
        (Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportQueue')
    )
    $result = @()
    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) {
            continue
        }
        foreach ($item in @(Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $Since -and ($_.Name -match '(?i)hwp|hancom') } | Sort-Object LastWriteTime | Select-Object -First 20)) {
            $result += [ordered]@{
                file_name = $item.Name
                bytes = [int64]$item.Length
                last_write_time = $item.LastWriteTime.ToString('o')
                path = Get-SafePathDescriptor -Path $item.FullName
                content_collected = $false
            }
        }
    }
    return @($result)
}

function Get-ApplicationEventMetadata {
    param(
        [Parameter(Mandatory)][datetime]$From,
        [Parameter(Mandatory)][datetime]$To
    )
    $providers = @('Application Error', 'Application Hang', 'Windows Error Reporting', '.NET Runtime', 'SideBySide')
    $allowedData = @('AppName', 'ApplicationName', 'FaultingApplicationName', 'AppVersion', 'ApplicationVersion', 'ModuleName', 'FaultingModuleName', 'ModuleVersion', 'ExceptionCode', 'FaultOffset', 'ProcessId', 'HangType')
    $result = @()
    try {
        $events = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; StartTime = $From; EndTime = $To } -ErrorAction Stop)
    }
    catch {
        return @()
    }
    foreach ($eventRecord in $events) {
        if ($eventRecord.ProviderName -notin $providers) {
            continue
        }
        try {
            [xml]$xml = $eventRecord.ToXml()
        }
        catch {
            continue
        }
        $dataValues = @()
        $safeData = [ordered]@{}
        foreach ($data in @($xml.Event.EventData.Data)) {
            $name = [string]$data.Name
            $value = [string]$data.InnerText
            $dataValues += $value
            if ($name -in $allowedData) {
                if ($name -match '(?i)Name$') {
                    $safeData[$name] = [System.IO.Path]::GetFileName($value)
                }
                else {
                    $safeData[$name] = $value
                }
            }
        }
        if (($dataValues -join ' ') -notmatch '(?i)hwp(?:\.exe)?|hancom|HWPFrame') {
            continue
        }
        $result += [ordered]@{
            provider_name = [string]$eventRecord.ProviderName
            event_id = [int]$eventRecord.Id
            level = [string]$eventRecord.LevelDisplayName
            time_created = if ($null -ne $eventRecord.TimeCreated) { $eventRecord.TimeCreated.ToString('o') } else { $null }
            record_id = [int64]$eventRecord.RecordId
            data = $safeData
            raw_message_collected = $false
        }
        if ($result.Count -ge 50) {
            break
        }
    }
    return @($result)
}

function Invoke-HancomRuntimeProbe {
    param(
        [Parameter(Mandatory)]$Candidate,
        [Parameter(Mandatory)]$Request,
        [Parameter(Mandatory)][int]$Timeout
    )
    $before = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    if ($before.Count -ne 0) {
        return [ordered]@{
            attempted = $false
            state = 'blocked'
            error_code = 'PREEXISTING_HWP_PROCESS'
            preexisting_hwp_processes = $before.Count
            observed_hwp_processes = @()
            remaining_probe_processes = $before.Count
            document_opened = $false
            file_opened = $false
            register_module_invoked = $false
        }
    }

    $expectedVersion = [string]$Request.target.expected_file_version
    $expectedHash = [string]$Request.target.expected_executable_sha256
    if ($Candidate.file_version -ne $expectedVersion -or $Candidate.executable_sha256 -ne $expectedHash) {
        return [ordered]@{
            attempted = $false
            state = 'failed'
            error_code = 'TARGET_PREFLIGHT_MISMATCH'
            preexisting_hwp_processes = 0
            observed_hwp_processes = @()
            remaining_probe_processes = 0
            document_opened = $false
            file_opened = $false
            register_module_invoked = $false
        }
    }

    $clientPath = $null
    if ($Candidate.architecture -eq 'x86') {
        $clientPath = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    }
    elseif ($Candidate.architecture -eq 'x64') {
        $systemDirectory = if ([Environment]::Is64BitProcess) { 'System32' } else { 'Sysnative' }
        $clientPath = Join-Path $env:WINDIR "$systemDirectory\WindowsPowerShell\v1.0\powershell.exe"
    }
    else {
        return [ordered]@{
            attempted = $false
            state = 'failed'
            error_code = 'UNSUPPORTED_EXECUTABLE_ARCHITECTURE'
            preexisting_hwp_processes = 0
            observed_hwp_processes = @()
            remaining_probe_processes = 0
            document_opened = $false
            file_opened = $false
            register_module_invoked = $false
        }
    }
    if (-not (Test-Path -LiteralPath $clientPath -PathType Leaf)) {
        throw "Matching Windows PowerShell client is unavailable: $clientPath"
    }

    $escapedProgId = ([string]$Request.target.prog_id).Replace("'", "''")
    $childScript = @"
`$ErrorActionPreference = 'Stop'
`$hwp = `$null
`$result = [ordered]@{
    state = 'failed'
    error_code = `$null
    automation_version = `$null
    quit_invoked = `$false
    apartment_state = [string][Threading.Thread]::CurrentThread.GetApartmentState()
    exception_type = `$null
    exception_hresult = `$null
}
try {
    `$hwp = New-Object -ComObject '$escapedProgId'
    `$result.automation_version = [string]`$hwp.Version
    `$hwp.Quit()
    `$result.quit_invoked = `$true
    `$result.state = 'pass'
}
catch {
    `$result.error_code = 'COM_CLIENT_EXCEPTION'
    `$result.exception_type = `$_.Exception.GetType().FullName
    `$result.exception_hresult = `$_.Exception.HResult
}
finally {
    if (`$null -ne `$hwp) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject(`$hwp)
    }
}
`$result | ConvertTo-Json -Compress
if (`$result.state -ne 'pass') { exit 2 }
"@
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($childScript))
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $clientPath
    $startInfo.Arguments = "-NoProfile -NonInteractive -STA -EncodedCommand $encodedCommand"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $child = New-Object System.Diagnostics.Process
    $child.StartInfo = $startInfo
    [void]$child.Start()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()

    $probeStartedAt = Get-Date
    $currentSessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
    $knownConsentTitle = -join @(
        [char]0xC0AC, [char]0xC6A9, [char]0xC131, [char]0x20,
        [char]0xB370, [char]0xC774, [char]0xD130, [char]0x20,
        [char]0xC218, [char]0xC9D1, [char]0x20,
        [char]0xB3D9, [char]0xC758
    )
    $observed = @{}
    $deadline = $probeStartedAt.AddSeconds($Timeout)
    $exitedWithinTimeout = $false
    while ((Get-Date) -lt $deadline) {
        foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
            $key = [string]$process.ProcessId
            if ($observed.ContainsKey($key)) {
                continue
            }
            $runtime = Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue
            $path = [string]$process.ExecutablePath
            if ([string]::IsNullOrWhiteSpace($path) -and $null -ne $runtime) {
                try { $path = [string]$runtime.Path } catch { $path = '' }
            }
            $title = if ($null -ne $runtime) { [string]$runtime.MainWindowTitle } else { '' }
            $titleClass = if ([string]::IsNullOrWhiteSpace($title)) { 'none' } elseif ($title -eq $knownConsentTitle) { 'known_usage_data_consent' } else { 'redacted_unknown' }
            $observed[$key] = [ordered]@{
                process_id = [int]$process.ProcessId
                parent_process_id = [int]$process.ParentProcessId
                session_id = [int]$process.SessionId
                created_at = if ($null -ne $process.CreationDate) { ([datetime]$process.CreationDate).ToString('o') } else { $null }
                executable_path_match = $path.Equals($Candidate.executable_path, [System.StringComparison]::OrdinalIgnoreCase)
                automation_command_line = [bool]($process.CommandLine -match '(?i)-Automation(?:\s+-Embedding)?\s*$')
                main_window_present = $null -ne $runtime -and $runtime.MainWindowHandle -ne 0
                window_title_class = $titleClass
                window_title_sha256 = if ($titleClass -eq 'redacted_unknown') { Get-StringSha256Lower -Value $title } else { $null }
            }
        }
        if ($child.WaitForExit(250)) {
            $exitedWithinTimeout = $true
            break
        }
    }
    if (-not $exitedWithinTimeout -and $child.HasExited) {
        $exitedWithinTimeout = $true
    }
    if (-not $exitedWithinTimeout) {
        $child.Kill()
        $child.WaitForExit()
    }
    $childExitCode = $child.ExitCode

    $cleaned = @()
    $cleanupRefused = @()
    $cleanupErrors = @()
    foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)) {
        $runtime = Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $runtime) {
            continue
        }
        $path = [string]$process.ExecutablePath
        if ([string]::IsNullOrWhiteSpace($path)) {
            try { $path = [string]$runtime.Path } catch { $path = '' }
        }
        $createdAt = if ($null -ne $process.CreationDate) { [datetime]$process.CreationDate } else { [datetime]::MinValue }
        $ownedByProbe =
            $process.SessionId -eq $currentSessionId -and
            $createdAt -ge $probeStartedAt.AddSeconds(-2) -and
            $path.Equals($Candidate.executable_path, [System.StringComparison]::OrdinalIgnoreCase) -and
            $process.CommandLine -match '(?i)-Automation(?:\s+-Embedding)?\s*$'
        if (-not $ownedByProbe) {
            $cleanupRefused += [int]$process.ProcessId
            continue
        }
        try {
            Stop-Process -Id $process.ProcessId -PassThru | Wait-Process -Timeout 10
            $cleaned += [int]$process.ProcessId
        }
        catch {
            if ($null -eq (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) {
                $cleaned += [int]$process.ProcessId
            }
            else {
                $cleanupErrors += [ordered]@{
                    process_id = [int]$process.ProcessId
                    exception_type = $_.Exception.GetType().FullName
                    message_sha256 = Get-StringSha256Lower -Value $_.Exception.Message
                }
            }
        }
    }

    $outputDrained = $false
    try {
        $outputDrained = [System.Threading.Tasks.Task]::WaitAll([System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask), 5000)
    }
    catch {
        $outputDrained = $false
    }
    $stdout = if ($outputDrained) { $stdoutTask.GetAwaiter().GetResult().Trim() } else { '' }
    $stderr = if ($outputDrained) { $stderrTask.GetAwaiter().GetResult() } else { '' }
    $childResult = $null
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        try { $childResult = $stdout | ConvertFrom-Json } catch { $childResult = $null }
    }

    Start-Sleep -Milliseconds 500
    $remaining = @(Get-CimInstance Win32_Process -Filter "Name='Hwp.exe'" -ErrorAction SilentlyContinue)
    $expectedNormalized = ConvertTo-NormalizedHancomVersion -Value $expectedVersion
    $automationNormalized = if ($null -ne $childResult) { ConvertTo-NormalizedHancomVersion -Value ([string]$childResult.automation_version) } else { $null }
    $versionMatches = $null -ne $expectedNormalized -and $null -ne $automationNormalized -and $expectedNormalized -eq $automationNormalized
    $timedOut = -not $exitedWithinTimeout
    $state = if ($timedOut -or -not $outputDrained -or $childExitCode -ne 0 -or $null -eq $childResult -or -not $versionMatches) {
        'failed'
    }
    elseif ($remaining.Count -ne 0 -or $cleanupRefused.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
        'failed'
    }
    else {
        'pass'
    }
    $errorCode = if ($timedOut) {
        'AUTOMATION_INITIALIZATION_TIMEOUT'
    }
    elseif (-not $outputDrained) {
        'PROBE_OUTPUT_DRAIN_TIMEOUT'
    }
    elseif ($null -eq $childResult) {
        'AUTOMATION_RESULT_INVALID'
    }
    elseif ($childExitCode -ne 0) {
        if ($childResult.error_code) { [string]$childResult.error_code } else { 'AUTOMATION_CHILD_FAILED' }
    }
    elseif (-not $versionMatches) {
        'AUTOMATION_VERSION_MISMATCH'
    }
    elseif ($remaining.Count -ne 0 -or $cleanupRefused.Count -ne 0 -or $cleanupErrors.Count -ne 0) {
        'AUTOMATION_PROCESS_REMAINED'
    }
    else {
        $null
    }

    return [ordered]@{
        attempted = $true
        state = $state
        error_code = $errorCode
        client_architecture = $Candidate.architecture
        client_apartment_state = 'STA'
        timeout_seconds = $Timeout
        timed_out = $timedOut
        output_drained = $outputDrained
        child_exit_code = $childExitCode
        child_exception_type = if ($null -ne $childResult) { $childResult.exception_type } else { $null }
        child_exception_hresult = if ($null -ne $childResult) { $childResult.exception_hresult } else { $null }
        stdout_bytes = [System.Text.Encoding]::UTF8.GetByteCount($stdout)
        stdout_sha256 = Get-StringSha256Lower -Value $stdout
        stderr_bytes = [System.Text.Encoding]::UTF8.GetByteCount($stderr)
        stderr_sha256 = Get-StringSha256Lower -Value $stderr
        raw_stream_content_collected = $false
        automation_version_raw = if ($null -ne $childResult) { [string]$childResult.automation_version } else { $null }
        automation_version_normalized = $automationNormalized
        expected_version_normalized = $expectedNormalized
        automation_version_matches_expected = $versionMatches
        quit_invoked = $null -ne $childResult -and [bool]$childResult.quit_invoked
        preexisting_hwp_processes = 0
        observed_hwp_processes = @($observed.Values | Sort-Object process_id)
        cleaned_probe_process_ids = @($cleaned)
        cleanup_refused_process_ids = @($cleanupRefused)
        cleanup_errors = @($cleanupErrors)
        remaining_probe_processes = $remaining.Count
        document_opened = $false
        file_opened = $false
        register_module_invoked = $false
    }
}

$requestFile = (Resolve-Path -LiteralPath $RequestPath).Path
$collectorPath = $MyInvocation.MyCommand.Path
$collectorSha256 = Get-Sha256Lower -Path $collectorPath
$requestSha256 = Get-Sha256Lower -Path $requestFile
$request = Get-Content -Raw -LiteralPath $requestFile | ConvertFrom-Json

if ($request.schema_version -ne 'hwpx-agent.hancom-diagnostic-request/v1') {
    throw 'Unsupported diagnostic request schema.'
}
$requestGuid = [guid]::Empty
if (-not [guid]::TryParse([string]$request.request_id, [ref]$requestGuid)) {
    throw 'Request ID is not a UUID.'
}
if ([string]$request.challenge_nonce -notmatch '^[0-9a-f]{64}$') {
    throw 'Request challenge nonce is invalid.'
}
if ([string]$request.collector_sha256 -ne $collectorSha256) {
    throw 'Collector hash does not match the diagnostic request.'
}
if ([int]$request.target.minimum_major_release -lt 2020) {
    throw 'Target family minimum release must be at least 2020.'
}
if ([string]$request.target.prog_id -ne 'HWPFrame.HwpObject.2') {
    throw 'Only the canonical HWPFrame.HwpObject.2 ProgID is allowed.'
}
if ($request.mode -notin @('discover', 'probe')) {
    throw 'Unsupported diagnostic mode.'
}
if ($request.policy.network_allowed -or $request.policy.ui_automation_allowed -or $request.policy.user_documents_allowed) {
    throw 'Unsafe diagnostic request policy.'
}
if ($request.policy.computer_use_mode -ne 'screenshot_only' -or $request.policy.event_log_mode -ne 'metadata_allowlist' -or $request.policy.crash_dump_mode -ne 'metadata_only') {
    throw 'Diagnostic privacy policy mismatch.'
}
if ($request.mode -eq 'probe') {
    if ([string]$request.target.expected_major_release -notmatch '^20[2-9][0-9]$') {
        throw 'Probe request requires an expected 2020+ major release.'
    }
    if ([string]$request.target.expected_file_version -notmatch '^\d+\.\d+\.\d+\.\d+$') {
        throw 'Probe request requires an exact four-part file version.'
    }
    if ([string]$request.target.expected_executable_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'Probe request requires an exact executable SHA-256.'
    }
}

if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$outputRoot = (Resolve-Path -LiteralPath $OutputDirectory).Path
$runId = [guid]::NewGuid().ToString()
$partialDirectory = Join-Path $outputRoot "$runId.partial"
$finalDirectory = Join-Path $outputRoot $runId
$partialZip = Join-Path $outputRoot "$runId.zip.partial"
$finalZip = Join-Path $outputRoot "$runId.zip"
foreach ($path in @($partialDirectory, $finalDirectory, $partialZip, $finalZip)) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing to overwrite diagnostic output: $path"
    }
}
New-Item -ItemType Directory -Path $partialDirectory | Out-Null

$startedAt = Get-Date
$collectorPhase = 'initialization'
$sessionState = 'failed'
$sessionErrorCode = $null
$exceptionEvidence = $null
$selectedCandidate = $null
$runtimeProbe = [ordered]@{
    attempted = $false
    state = 'not_run'
    error_code = $null
    preexisting_hwp_processes = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count
    observed_hwp_processes = @()
    remaining_probe_processes = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue).Count
    document_opened = $false
    file_opened = $false
    register_module_invoked = $false
}
$comCandidates = @()
$targetFiles = @()
$fontInventory = @()
$printerInventory = @()
$products = @()
$hotfixes = @()

try {
    $collectorPhase = 'com_registration_inventory'
    $comCandidates = @(Get-ComRegistrationCandidates -ProgId ([string]$request.target.prog_id))
    $usableCandidates = @($comCandidates | Where-Object { $_.registry_architecture_match } | Group-Object executable_sha256 | ForEach-Object { $_.Group[0] })
    if ($usableCandidates.Count -eq 0) {
        $sessionErrorCode = 'TARGET_NOT_INSTALLED_OR_COM_NOT_REGISTERED'
        $sessionState = 'failed'
    }
    elseif ($usableCandidates.Count -ne 1) {
        $sessionErrorCode = 'AMBIGUOUS_COM_TARGET'
        $sessionState = 'failed'
    }
    else {
        $selectedCandidate = $usableCandidates[0]
        $collectorPhase = 'target_file_inventory'
        $targetFiles = @(Get-TargetFileInventory -ExecutablePath $selectedCandidate.executable_path)
        $observedMajor = [string]$selectedCandidate.observed_major_release
        $minimumMajor = [int]$request.target.minimum_major_release
        if ($request.mode -eq 'discover') {
            if (-not [string]::IsNullOrWhiteSpace($observedMajor) -and [int]$observedMajor -lt $minimumMajor) {
                $sessionErrorCode = 'TARGET_MAJOR_RELEASE_BELOW_MINIMUM'
                $sessionState = 'failed'
            }
            else {
                $sessionState = 'discovered_unqualified'
                $sessionErrorCode = $null
            }
        }
        elseif ([string]::IsNullOrWhiteSpace($observedMajor) -or [int]$observedMajor -lt $minimumMajor) {
            $sessionErrorCode = 'TARGET_MAJOR_RELEASE_UNVERIFIED_OR_BELOW_MINIMUM'
            $sessionState = 'failed'
        }
        else {
            $majorMatches = $observedMajor -eq [string]$request.target.expected_major_release
            $versionMatches = $selectedCandidate.file_version -eq [string]$request.target.expected_file_version
            $hashMatches = $selectedCandidate.executable_sha256 -eq [string]$request.target.expected_executable_sha256
            if (-not $majorMatches -or -not $versionMatches -or -not $hashMatches) {
                $sessionErrorCode = 'TARGET_PROFILE_MISMATCH'
                $sessionState = 'failed'
            }
            else {
                $collectorPhase = 'runtime_probe'
                $runtimeProbe = Invoke-HancomRuntimeProbe -Candidate $selectedCandidate -Request $request -Timeout $TimeoutSeconds
                $sessionState = [string]$runtimeProbe.state
                $sessionErrorCode = $runtimeProbe.error_code
            }
        }
    }

    $collectorPhase = 'installed_product_inventory'
    $products = @(Get-InstalledProductInventory)
    $collectorPhase = 'font_inventory'
    $fontInventory = @(Get-FontInventory)
    $collectorPhase = 'printer_inventory'
    $printerInventory = @(Get-PrinterInventory)
    $collectorPhase = 'hotfix_inventory'
    $hotfixes = @(Get-CimInstance Win32_QuickFixEngineering -ErrorAction SilentlyContinue | Select-Object -ExpandProperty HotFixID | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
    $collectorPhase = 'primary_collection_complete'
}
catch {
    $sessionState = 'failed'
    $sessionErrorCode = 'COLLECTOR_EXCEPTION'
    $exceptionEvidence = [ordered]@{
        phase = $collectorPhase
        exception_type = $_.Exception.GetType().FullName
        message_sha256 = Get-StringSha256Lower -Value $_.Exception.Message
    }
}

$eventMetadata = @()
$dumpMetadata = @()
$os = $null
try {
    $collectorPhase = 'application_event_metadata'
    $completedAt = Get-Date
    $eventMetadata = @(Get-ApplicationEventMetadata -From $startedAt.AddMinutes(-1) -To $completedAt.AddSeconds(1))
    $collectorPhase = 'crash_dump_metadata'
    $dumpMetadata = @(Get-CrashDumpMetadata -Since $startedAt.AddMinutes(-1))
    $collectorPhase = 'os_inventory'
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $collectorPhase = if ($null -eq $exceptionEvidence) { 'collection_complete' } else { [string]$exceptionEvidence.phase }
}
catch {
    if ($null -eq $exceptionEvidence) {
        $sessionState = 'failed'
        $sessionErrorCode = 'COLLECTOR_EXCEPTION'
        $exceptionEvidence = [ordered]@{
            phase = $collectorPhase
            exception_type = $_.Exception.GetType().FullName
            message_sha256 = Get-StringSha256Lower -Value $_.Exception.Message
        }
    }
    $collectorPhase = [string]$exceptionEvidence.phase
}
$completedAt = Get-Date
$sessionNameClass = if ($env:SESSIONNAME -match '(?i)^console$') { 'console' } elseif ($env:SESSIONNAME -match '(?i)^rdp') { 'rdp' } else { 'other_or_unknown' }
$osSerialNumber = [string](Get-PropertyValue -InputObject $os -Name 'SerialNumber')
$hostFingerprint = Get-StringSha256Lower -Value ("{0}|{1}|{2}" -f [string]$request.challenge_nonce, [string]$env:COMPUTERNAME, $osSerialNumber)

$publicCandidates = @($comCandidates | ForEach-Object {
    [ordered]@{
        registry_view = $_.registry_view
        registry_architecture_match = $_.registry_architecture_match
        clsid = $_.clsid
        executable_path = $_.executable_path_descriptor
        executable_sha256 = $_.executable_sha256
        file_version = $_.file_version
        product_version = $_.product_version
        product_name = $_.product_name
        file_description = $_.file_description
        architecture = $_.architecture
        observed_major_release = $_.observed_major_release
        server_command_class = $_.server_command_class
    }
})

$inventory = [ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-inventory/v1'
    request_id = [string]$request.request_id
    run_id = $runId
    host_fingerprint = $hostFingerprint
    os = [ordered]@{
        caption = [string](Get-PropertyValue -InputObject $os -Name 'Caption')
        version = [string](Get-PropertyValue -InputObject $os -Name 'Version')
        build_number = [string](Get-PropertyValue -InputObject $os -Name 'BuildNumber')
        architecture = [string](Get-PropertyValue -InputObject $os -Name 'OSArchitecture')
        locale = [string](Get-PropertyValue -InputObject $os -Name 'Locale')
        ui_culture = [System.Globalization.CultureInfo]::CurrentUICulture.Name
    }
    interactive_session = [ordered]@{
        process_session_id = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
        session_class = $sessionNameClass
    }
    installed_product_candidates = @($products)
    com_candidates = @($publicCandidates)
    target_files = @($targetFiles)
    fonts = @($fontInventory)
    printers = @($printerInventory)
    installed_hotfix_ids = @($hotfixes)
    crash_dump_metadata = @($dumpMetadata)
    crash_dump_content_collected = $false
}

$events = [ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-events/v1'
    request_id = [string]$request.request_id
    run_id = $runId
    from = $startedAt.AddMinutes(-1).ToString('o')
    to = $completedAt.AddSeconds(1).ToString('o')
    raw_messages_collected = $false
    events = @($eventMetadata)
}

$targetObservation = if ($null -eq $selectedCandidate) {
    $null
}
else {
    [ordered]@{
        profile_id = [string]$request.target.profile_id
        observed_major_release = $selectedCandidate.observed_major_release
        expected_major_release = $request.target.expected_major_release
        observed_file_version = $selectedCandidate.file_version
        expected_file_version = $request.target.expected_file_version
        observed_executable_sha256 = $selectedCandidate.executable_sha256
        expected_executable_sha256 = $request.target.expected_executable_sha256
        architecture = $selectedCandidate.architecture
        registry_view = $selectedCandidate.registry_view
        clsid = $selectedCandidate.clsid
        executable_path = $selectedCandidate.executable_path_descriptor
    }
}

$session = [ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-session/v1'
    request_id = [string]$request.request_id
    challenge_nonce = [string]$request.challenge_nonce
    run_id = $runId
    started_at = $startedAt.ToString('o')
    completed_at = $completedAt.ToString('o')
    mode = [string]$request.mode
    state = $sessionState
    error_code = $sessionErrorCode
    collector_phase = $collectorPhase
    exception = $exceptionEvidence
    target_profile_id = [string]$request.target.profile_id
    collector_sha256 = $collectorSha256
    request_sha256 = $requestSha256
    privacy = [ordered]@{
        document_content_collected = $false
        user_document_opened = $false
        raw_event_messages_collected = $false
        dump_content_collected = $false
        ui_automation_performed = $false
        network_transmission_performed = $false
    }
    target_observation = $targetObservation
    runtime_probe = $runtimeProbe
    event_summary = [ordered]@{
        relevant_application_events = $eventMetadata.Count
        crash_dump_metadata_entries = $dumpMetadata.Count
    }
}

[System.IO.File]::WriteAllBytes((Join-Path $partialDirectory 'request.json'), [System.IO.File]::ReadAllBytes($requestFile))
Write-JsonFile -Path (Join-Path $partialDirectory 'inventory.json') -Value $inventory
Write-JsonFile -Path (Join-Path $partialDirectory 'events.json') -Value $events
Write-JsonFile -Path (Join-Path $partialDirectory 'session.json') -Value $session

$manifestEntries = @(Get-ChildItem -LiteralPath $partialDirectory -File | Sort-Object Name | ForEach-Object {
    [ordered]@{
        path = $_.Name
        bytes = [int64]$_.Length
        sha256 = Get-Sha256Lower -Path $_.FullName
    }
})
$manifest = [ordered]@{
    schema_version = 'hwpx-agent.hancom-diagnostic-bundle-manifest/v1'
    request_id = [string]$request.request_id
    run_id = $runId
    entries = @($manifestEntries)
}
Write-JsonFile -Path (Join-Path $partialDirectory 'manifest.json') -Value $manifest

Move-Item -LiteralPath $partialDirectory -Destination $finalDirectory
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($finalDirectory, $partialZip, [System.IO.Compression.CompressionLevel]::Optimal, $false)
Move-Item -LiteralPath $partialZip -Destination $finalZip

[pscustomobject]@{
    state = $sessionState
    error_code = $sessionErrorCode
    request_id = [string]$request.request_id
    run_id = $runId
    bundle_path = $finalZip
    bundle_sha256 = Get-Sha256Lower -Path $finalZip
    evidence_directory = $finalDirectory
    network_transmission_performed = $false
    ui_automation_performed = $false
} | ConvertTo-Json -Depth 5

if ($sessionState -notin @('pass', 'discovered_unqualified')) {
    exit 2
}
