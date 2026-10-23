# Pure/source contracts; actual denied and inspected worker processes are separate.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$source=Join-Path $PSScriptRoot 'inspect-crossref-worker-composition.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if (@($errors).Count -ne 0) {throw 'P09_XREF_WORKER_TEST_PARSE'}
$definitions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
foreach ($definition in $definitions) {. ([scriptblock]::Create($definition.Extent.Text))}
$pins=[Collections.Generic.List[object]]::new();$script:passed=0
function Invoke-P09XrefWorkerTest([scriptblock]$Body) {& $Body;$script:passed++}
try {
    Invoke-P09XrefWorkerTest {
        $names=@($ast.ParamBlock.Parameters | ForEach-Object {$_.Name.VariablePath.UserPath})
        Assert-P09XrefWorker (($names -join ',') -ceq
            'ExpectedCompositionSha256,ExpectedProbeSha256,ExpectedBindingSha256,InspectOnly,ExecuteNative') 'TEST_CLOSED_PARAMETERS'
        Assert-P09XrefWorker ($definitions.Count -eq 4) 'TEST_CLOSED_FUNCTION_INVENTORY'
    }
    Invoke-P09XrefWorkerTest {
        $function=@($definitions | Where-Object {$_.Name -ceq 'Invoke-P09XrefPreparationChild'})[0]
        $text=$function.Extent.Text
        Assert-P09XrefWorker ($text.Contains("[ValidateSet('installation_prefix','source_probe_baseline')]") -and
            $text.Contains("'baseline'") -and $text.Contains("'-ExpectedHarnessSha256'") -and
            $text.Contains('inspect-crossref-discovery-preflight.ps1') -and
            $text -cnotmatch '(?i)ReadToEnd|CreateInstance|GetActiveObject|-ComObject') 'TEST_FIXED_NO_NATIVE_CHILDREN'
        Assert-P09XrefWorker ($text.Contains('ReadAsync') -and $text.Contains('maximum=32768') -and
            $text.Contains('maximum=4096') -and $text.Contains('PREPARATION_CHILD_OUTPUT_LIMIT') -and
            $text.Contains('cleanup_confirmed')) 'TEST_SOURCE_BOUNDED_ASYNC_CAPTURE'
    }
    Invoke-P09XrefWorkerTest {
        $path=Join-Path ([IO.Path]::GetTempPath()) ('p09-xref-worker-'+[Guid]::NewGuid().ToString('N')+'.bin')
        $bytes=[Text.Encoding]::UTF8.GetBytes('retained')
        $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try {$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)} finally {$stream.Dispose()}
        try {
            $actual=Read-P09XrefWorkerPin $path 8 (Get-P09XrefWorkerDigest $bytes)
            Assert-P09XrefWorker ([Convert]::ToBase64String($actual) -ceq [Convert]::ToBase64String($bytes)) 'TEST_READ_ONLY_PIN'
            foreach ($maximum in @(7,8)) {
                $rejected=$false
                try {[void](Read-P09XrefWorkerPin $path $maximum ('0'*64))} catch {$rejected=$true}
                Assert-P09XrefWorker $rejected 'TEST_PIN_MUST_REJECT'
            }
            Assert-P09XrefWorker ((Get-P09XrefWorkerDigest ([IO.File]::ReadAllBytes($path))) -ceq
                (Get-P09XrefWorkerDigest $bytes)) 'TEST_RETAINED_DATA'
        } finally {[IO.File]::Delete($path)} # Only this exclusive test-owned eight-byte fixture.
    }
    Invoke-P09XrefWorkerTest {
        $text=$ast.Extent.Text
        $denied=$text.IndexOf("if (`$ExecuteNative)",[StringComparison]::Ordinal)
        $read=$text.IndexOf('[void](Read-P09XrefWorkerPin $PSCommandPath',[StringComparison]::Ordinal)
        $child=$text.IndexOf("`$prefix=Invoke-P09XrefPreparationChild",[StringComparison]::Ordinal)
        Assert-P09XrefWorker ($denied -ge 0 -and $denied -lt $read -and $read -lt $child -and
            $text.Contains('native_dispatch_denied_not_implemented_or_authorized') -and
            $text.Contains('preparation_children_started=0') -and
            $text -cnotmatch '(?i)New-P58Owner\s|Observe-P09XrefOwnedActiveSource\s+\$|\.Execute\(|\.SaveAs\(') 'TEST_DENIAL_PRECEDES_EFFECTS'
    }
    Assert-P09XrefWorker ($script:passed -eq 4) 'TEST_EXACT_FOUR'
    [ordered]@{state='four_worker_composition_contracts_pass_not_native';passed=$script:passed;failed=0;
        actual_worker_inspection_executed=$false;native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 0
} catch {
    $code=if ($_.Exception.Message -cmatch '^P09_XREF_WORKER_[A-Z_]+$') {$_.Exception.Message} else {'P09_XREF_WORKER_TEST_FAILED_NO_RAW_VALUES'}
    [ordered]@{state='worker_composition_contract_failed';passed=$script:passed;failed=1;error_code=$code;
        native_session_started=$false;p09_complete=$false} | ConvertTo-Json -Compress
    exit 2
}
