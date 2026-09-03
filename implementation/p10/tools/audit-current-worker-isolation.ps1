[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [string]$DotNetPath = 'dotnet',
    [string]$PythonPath = 'python'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$evidenceRoot = [System.IO.Path]::GetFullPath((Join-Path $root 'implementation\p10\evidence'))
$outputFull = [System.IO.Path]::GetFullPath(
    $(if ([System.IO.Path]::IsPathRooted($OutputPath)) { $OutputPath } else { Join-Path $root $OutputPath })
)
$evidencePrefix = $evidenceRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
if (-not $outputFull.StartsWith($evidencePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'P10-08 audit output must be a named file below implementation/p10/evidence.'
}
if (Test-Path -LiteralPath $outputFull) {
    throw 'P10-08 audit output already exists; no-overwrite policy refused the run.'
}

$policyRelative = 'implementation/p10/isolation/p10-current-pc-local-worker-policy.json'
$policyPath = (Resolve-Path -LiteralPath (Join-Path $root $policyRelative)).Path
$agentDll = (Resolve-Path -LiteralPath (
    Join-Path $root 'workers\windows-hancom-agent\tests\HwpxAgent.WindowsAgent.Smoke\bin\Release\net10.0\HwpxAgent.WindowsAgent.Smoke.dll'
)).Path
$baselineId = [Guid]::NewGuid().ToString('N')
$baselineRelative = "implementation/p10/evidence/.p10-08-host-baseline-$baselineId.json"
$baselinePath = Join-Path $root $baselineRelative
$partialPath = "$outputFull.partial-$baselineId"

function Get-TextSha256([Parameter(Mandatory)][string]$Value) {
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Value)
    try {
        return [Convert]::ToHexStringLower([System.Security.Cryptography.SHA256]::HashData($bytes))
    }
    finally {
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($bytes)
    }
}

try {
    [System.IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null
    if (@(Get-Process -Name 'Hwp' -ErrorAction SilentlyContinue).Count -ne 0) {
        throw 'P10-08 current-host audit requires zero running Hwp.exe processes.'
    }

    & (Join-Path $root 'implementation\p00\tools\Test-CurrentHostBaseline.ps1') `
        -ProjectRoot $root `
        -BaselinePath 'implementation/p00/evidence/current-host-baseline.20260901.json' `
        -OutputPath $baselineRelative | Out-Null
    $baselineSucceeded = $?
    if (-not $baselineSucceeded -or -not (Test-Path -LiteralPath $baselinePath)) {
        throw 'The live current-host baseline verification did not complete.'
    }
    $baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
    if ($baseline.state -ne 'pass') {
        throw 'The live current-host baseline verification did not pass.'
    }

    $liveText = (& $DotNetPath $agentDll '--actual-current-host-isolation' $policyPath 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($liveText)) {
        throw 'The bounded current-host isolation observer did not pass.'
    }
    $live = $liveText | ConvertFrom-Json
    if ($live.state -ne 'pass_current_pc_development_only') {
        throw 'The current-host isolation observer returned an unexpected state.'
    }

    $firewallProbeComplete = $false
    $allOutboundBlock = $false
    $firewallProfileCount = 0
    $firewallStateSha256 = Get-TextSha256 -Value 'unavailable'
    try {
        $profiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop)
        $firewallProfileCount = $profiles.Count
        $states = @($profiles | Sort-Object -Property Name | ForEach-Object {
            [ordered]@{
                enabled = [bool]$_.Enabled
                default_outbound_action = [string]$_.DefaultOutboundAction
            }
        })
        $firewallStateSha256 = Get-TextSha256 -Value ($states | ConvertTo-Json -Compress -Depth 4)
        $allOutboundBlock = $profiles.Count -gt 0 -and @(
            $profiles | Where-Object { [string]$_.DefaultOutboundAction -ne 'Block' }
        ).Count -eq 0
        $firewallProbeComplete = $true
    }
    catch {
        $firewallProbeComplete = $false
    }
    if (-not $firewallProbeComplete) {
        throw 'The read-only active firewall profile observation did not complete.'
    }

    $policySha256 = (Get-FileHash -LiteralPath $policyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($live.policy_manifest_sha256 -ne $policySha256) {
        throw 'The live observation did not bind the exact worker isolation policy.'
    }
    $baselineVerificationSha256 = (
        Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    $audit = [ordered]@{
        schema_version = 'hwpx-agent.p10-08-worker-isolation-audit/v1'
        generated_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        state = 'pass_current_pc_development_only'
        policy_relative_path = $policyRelative
        policy_sha256 = $policySha256
        host_baseline_verification = [ordered]@{
            state = [string]$baseline.state
            baseline_digest_sha256 = [string]$baseline.baseline_digest_sha256
            verification_sha256 = $baselineVerificationSha256
        }
        live_observation = $live
        firewall_observation = [ordered]@{
            probe_complete = $firewallProbeComplete
            profile_count = $firewallProfileCount
            all_default_outbound_block = $allOutboundBlock
            state_sha256 = $firewallStateSha256
        }
        scope = [ordered]@{
            current_pc_local_development_qualified = $true
            production_or_provider_qualified = $false
            dedicated_worker_image_qualified = $false
            profile_wide_residue_scan_performed = $false
            clipboard_content_read = $false
            system_setting_changed = $false
        }
        privacy = [ordered]@{
            raw_user_identity_present = $false
            raw_path_present = $false
            raw_document_text_present = $false
            user_document_scanned = $false
        }
    }
    $json = $audit | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($partialPath, $json + "`n", [System.Text.UTF8Encoding]::new($false))
    & $PythonPath (Join-Path $root 'tools\p10\validate_worker_isolation.py') `
        --policy $policyPath `
        --audit $partialPath | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'The P10-08 audit schema validation failed.'
    }
    [System.IO.File]::Move($partialPath, $outputFull)
    Get-Content -LiteralPath $outputFull -Raw
}
finally {
    foreach ($temporary in @($baselinePath, $partialPath)) {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}
