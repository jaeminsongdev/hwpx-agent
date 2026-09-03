[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
function Read-RepoFile([string]$relativePath) {
    Get-Content -LiteralPath (Join-Path $root $relativePath) -Raw
}

$events = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomEventJournal.cs'
$watchdog = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomModalWatchdog.cs'
$handler = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\HancomLifecycleCommandHandler.cs'
$server = Read-RepoFile 'workers\windows-hancom-worker\src\HwpxAgent.WindowsWorker\StaWorkerServer.cs'
$protocol = Read-RepoFile 'protocol\proto\hwpx_agent\windows_bridge\v1\windows_bridge.proto'
$smoke = Read-RepoFile 'workers\windows-hancom-worker\tests\HwpxAgent.WindowsWorker.ModalWatchdogSmoke\Program.cs'

$forbiddenInputApis = '(?i)SendInput|SendMessage|PostMessage|mouse_event|keybd_event|SetCursorPos'
$forbiddenPersistenceApis = '(?i)File\.(Write|Create|OpenWrite)|WriteAll(Bytes|Text)|Bitmap\.Save|Image\.Save'

$checks = [ordered]@{
    exact_event_interface = $events -match 'Guid\("F04A09A0-F319-40D5-88CA-CA439CC6820C"\)' -and
        $events -match 'InterfaceType\(ComInterfaceType\.InterfaceIsIDispatch\)' -and
        $events -match 'public interface IHancomObjectEventDispatch' -and
        $events -match 'public sealed class HancomObjectEventDispatch'
    exact_event_dispids = (1..16 | ForEach-Object { $events -match "\[DispId\($_\)\]" }) -notcontains $false
    connection_point_subscription = $events -match 'IConnectionPointContainer' -and
        $events -match 'FindConnectionPoint\(ref interfaceId' -and
        $events -match 'point\.Advise\(sink' -and
        $events -match 'point\.Unadvise\(currentCookie\)'
    event_queue_bounded = $events -match 'MaximumSignals = 1_024' -and
        $events -match 'maximumEvents is < 1 or > 10_000' -and
        $events -match 'HancomLifecycleError\.EventOverflow'
    event_payload_redacted = $events -match '_ = address' -and
        $events -match '_ = displayText' -and
        $events -match 'SafeMetadataSha256' -and
        $events -notmatch 'HancomAutomationSignal\([^,]+,\s*(address|displayText)'
    immutable_v1_event_carrier = $events -match 'windows_bridge\.v1 is immutable' -and
        $events -match 'RecordDigest\(carrierEventType, signal\.SafeMetadataSha256\)' -and
        $protocol -notmatch 'STA_EVENT_TYPE_AUTOMATION_SIGNAL'
    current_policy_has_no_unproved_allowlist = $watchdog -match 'FailClosedHancomModalPolicyResolver' -and
        $watchdog -match 'profile\.ProfileId,\s*profile\.ProductBuild,\s*\[\]'
    policy_bound_to_exact_target = $watchdog -match 'policy\.TargetProfileId, profile\.ProfileId' -and
        $watchdog -match 'policy\.ProductBuild, profile\.ProductBuild' -and
        $watchdog -match 'policy\.ExpectedDialogs\.Count > 64'
    process_owned_modal_scan = $watchdog -match 'GetWindowThreadProcessId\(window, out var ownerProcessId\)' -and
        $watchdog -match 'ownerProcessId == processId' -and
        $watchdog -match 'candidateProcessId != processId' -and
        $watchdog -match 'EnumChildWindows' -and
        $watchdog -match '"#32770"' -and
        $watchdog -match 'WsExDlgModalFrame'
    bounded_capture = $watchdog -match 'MaximumDimension = 8_192' -and
        $watchdog -match 'MaximumPixels = 16_777_216' -and
        $watchdog -match 'controls\.Count >= 256'
    screenshot_metadata_only = $watchdog -match 'SHA256\.HashData\(bytes\)' -and
        $watchdog -match 'CryptographicOperations\.ZeroMemory\(bytes\)' -and
        $watchdog -notmatch $forbiddenPersistenceApis
    screenshot_capture_does_not_message_target = $watchdog -match 'BitBlt\(' -and
        $watchdog -notmatch 'PrintWindow|SendMessageTimeout'
    no_ui_input_or_auto_response = $watchdog -notmatch $forbiddenInputApis -and
        $watchdog -match 'AutoResponseAttempted: false'
    unknown_modal_fail_closed = $watchdog -match 'HancomModalDisposition\.UnknownBlocked' -and
        $watchdog -match 'BridgeErrorCode\.UnknownModal' -and
        $watchdog -match 'RequiresRecycle: true'
    expected_modal_report_and_stop = $watchdog -match 'HancomModalDisposition\.ExpectedBlocked' -and
        $watchdog -match 'BridgeErrorCode\.PolicyDenied'
    background_watchdog_bounded_stop = $watchdog -match 'TimeSpan\.FromMilliseconds\(100\)' -and
        $watchdog -match 'monitor\.Wait\(TimeSpan\.FromSeconds\(2\)\)' -and
        $watchdog -match 'ModalWatchdogStopFailed'
    handler_scans_before_and_after = $handler -match 'var before = InspectModal\(journal\)' -and
        $handler -match 'var after = InspectModal\(journal\)'
    handler_preserves_modal_evidence = $handler -match 'events: journal\.Snapshot\(\)' -and
        $handler -match 'safeDetailSha256: incident\.SafeMetadataSha256'
    cleanup_required_stops_dispatch = $server -match 'receipt\.State == ExecutionState\.UnknownOutcome\s*\|\| receipt\.CleanupRequired'
    command_scoped_signal_carriers = $handler -match 'StartSession => StaEventType\.SessionStarted' -and
        $handler -match 'OpenDocument => StaEventType\.DocumentOpened' -and
        $handler -match 'ExecutePlan => StaEventType\.PlanExecuted' -and
        $handler -match 'current\.DrainAutomationSignals\(context\),\s*StaEventType\.CleanupCompleted'
    smoke_covers_modal_boundaries = $smoke -match 'UnknownModalFailsClosed' -and
        $smoke -match 'ExactExpectedFingerprintIsDistinguished' -and
        $smoke -match 'FingerprintDriftBecomesUnknown' -and
        $smoke -match 'CleanupRequiredReceiptStopsFurtherDispatchAsync'
    smoke_has_actual_event_delivery_mode = $smoke -match '--actual-event-delivery' -and
        $smoke -match 'HANCOM_EVENT_DELIVERY_PASS'
    smoke_has_actual_modal_probe_mode = $smoke -match '--actual-modal-probe' -and
        $smoke -match 'classification=unknown_fail_closed' -and
        $smoke -match 'auto_response=false raw_dialog_text=false screenshot_persisted=false'
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
[pscustomobject]@{
    schema_version = 'hwpx-agent.p10-07-event-modal-static-tests/v1'
    state = if ($failed.Count -eq 0) { 'pass' } else { 'failed' }
    passed = $checks.Count - $failed.Count
    total = $checks.Count
    failed = $failed
} | ConvertTo-Json -Depth 5

if ($failed.Count -ne 0) { exit 2 }
