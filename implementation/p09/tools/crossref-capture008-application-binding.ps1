# Fixed008: bind Document.Application through exact document membership; verify windows on the owned root.
# Read-only COM getters only. No activation, actions, fallback, writes, retry or execution permit.
Set-StrictMode -Version Latest

function Test-P09XrefCapture008ApplicationGraph($Observation) {
    $names=@('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
        'window_handle_matches','window_pid_matches','single_document','version_matches')
    if ($Observation -isnot [pscustomobject] -or @($Observation.PSObject.Properties).Count -ne $names.Count) {return $false}
    foreach ($name in $names) {
        if ($name -cnotin @($Observation.PSObject.Properties.Name) -or $Observation.$name -isnot [bool] -or -not $Observation.$name) {return $false}
    }
    return $true
}

function Test-P09XrefCapture008ReturnedApplication($Application,$Owner,$Pointers,$CollectionId,$DocumentId) {
    Assert-P09XrefBinding ($null -ne $Application -and [Runtime.InteropServices.Marshal]::IsComObject($Application)) 'CAPTURE_EIGHT_RETURNED_APPLICATION_REAL_COM'
    # Keep every identity alive through both original paired observations. A
    # different top-level IUnknown alone is neither acceptance nor rejection.
    [void](Get-P09XrefHeldComIdentity $Application $Pointers)
    try {$collection=$Application.XHwpDocuments} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_COLLECTION'}
    Assert-P09XrefBinding ($null -ne $collection -and [Runtime.InteropServices.Marshal]::IsComObject($collection)) 'CAPTURE_EIGHT_APPLICATION_REAL_COLLECTION'
    try {$active=$collection.Active_XHwpDocument} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_DOCUMENT'}
    Assert-P09XrefBinding ($null -ne $active -and [Runtime.InteropServices.Marshal]::IsComObject($active)) 'CAPTURE_EIGHT_APPLICATION_REAL_DOCUMENT'
    # The document's returned application is admitted ONLY through the exact
    # owner collection AND active document. Do not assume its full IHwpObject
    # window API, and do not fall back after an identity mismatch.
    $collectionBound=((Get-P09XrefHeldComIdentity $collection $Pointers) -eq $CollectionId)
    Assert-P09XrefBinding $collectionBound 'CAPTURE_EIGHT_APPLICATION_COLLECTION_MISMATCH'
    $documentBound=((Get-P09XrefHeldComIdentity $active $Pointers) -eq $DocumentId)
    Assert-P09XrefBinding $documentBound 'CAPTURE_EIGHT_APPLICATION_DOCUMENT_MISMATCH'
    # The previously qualified root, not the returned document application,
    # must still yield the exact held windows/window/HWND/PID for this session.
    try {$windows=$Owner.hwp.XHwpWindows} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_WINDOWS'}
    Assert-P09XrefBinding ($null -ne $windows -and [Runtime.InteropServices.Marshal]::IsComObject($windows)) 'CAPTURE_EIGHT_APPLICATION_REAL_WINDOWS'
    try {$window=$windows.Item(0)} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_WINDOW'}
    Assert-P09XrefBinding ($null -ne $window -and [Runtime.InteropServices.Marshal]::IsComObject($window)) 'CAPTURE_EIGHT_APPLICATION_REAL_WINDOW'
    try {$hwnd=$window.WindowHandle;$ownerHwnd=$Owner.window.WindowHandle} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_HWND'}
    Assert-P09XrefBinding ($hwnd -is [int] -and $hwnd -ne 0 -and $ownerHwnd -is [int] -and $ownerHwnd -ne 0) 'CAPTURE_EIGHT_APPLICATION_EXACT_HWND_TYPE'
    try {$count=$collection.Count;$version=$Owner.hwp.Version} catch {throw 'P09_XREF_BIND_CAPTURE_EIGHT_APPLICATION_READ_STATE'}
    $observation=[pscustomobject]@{
        returned_application_is_com=$true
        collection_bound=$collectionBound
        document_bound=$documentBound
        windows_bound=((Get-P09XrefHeldComIdentity $windows $Pointers) -eq (Get-P09XrefHeldComIdentity $Owner.windows $Pointers))
        window_bound=((Get-P09XrefHeldComIdentity $window $Pointers) -eq (Get-P09XrefHeldComIdentity $Owner.window $Pointers))
        window_handle_matches=($hwnd -eq $ownerHwnd)
        window_pid_matches=([P58OwnedWindowProcess]::ProcessId($hwnd) -eq $Owner.identity.process_id)
        single_document=($count -is [int] -and $count -eq 1)
        version_matches=($version -is [string] -and $version.Replace(',','.').Replace(' ','') -ceq '11.0.0.9136')
    }
    $codes=@{collection_bound='COLLECTION';document_bound='DOCUMENT';windows_bound='WINDOWS';window_bound='WINDOW';
        window_handle_matches='HWND';window_pid_matches='PID';single_document='COUNT';version_matches='VERSION'}
    foreach ($name in $codes.Keys) {
        Assert-P09XrefBinding ($observation.$name -is [bool] -and $observation.$name) ('CAPTURE_EIGHT_APPLICATION_'+$codes[$name]+'_MISMATCH')
    }
    # Original caller still requires its owner check, source/path/clean/version
    # observations, exact active document, paired samples and final owner check.
    return (Test-P09XrefCapture008ApplicationGraph $observation)
}

function Get-P09XrefCapture008ApplicationDefinition {
    $path=Join-Path $PSScriptRoot 'crossref-owned-active-source.ps1'
    $item=Get-Item -LiteralPath $path -Force
    Assert-P09XrefBinding ($item -is [IO.FileInfo] -and $item.Length -eq 12580 -and
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'CAPTURE_EIGHT_ORIGINAL_OBSERVER_BOUNDARY'
    $bytes=[IO.File]::ReadAllBytes($path);$algorithm=[Security.Cryptography.SHA256]::Create()
    try {$sha=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()} finally {$algorithm.Dispose()}
    Assert-P09XrefBinding ($sha -ceq 'b676d0749771f55474dc4530b9d735cf3a9cfb3646e5a9afae0249b5e80cbb3f') 'CAPTURE_EIGHT_ORIGINAL_OBSERVER_SHA'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput([Text.UTF8Encoding]::new($false,$true).GetString($bytes),$path,[ref]$tokens,[ref]$errors)
    $nodes=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -ceq 'Read-P09XrefActiveSourceObservation'},$false))
    Assert-P09XrefBinding (@($errors).Count -eq 0 -and $nodes.Count -eq 1) 'CAPTURE_EIGHT_ORIGINAL_OBSERVER_PARSE'
    $original=$nodes[0].Extent.Text
    $before='document_application_bound=((Get-P09XrefHeldComIdentity $documentApplication $Pointers) -eq $ApplicationId)'
    $after='document_application_bound=(Test-P09XrefCapture008ReturnedApplication $documentApplication $Owner $Pointers $CollectionId $DocumentId)'
    Assert-P09XrefBinding ([regex]::Matches($original,[regex]::Escape($before)).Count -eq 1) 'CAPTURE_EIGHT_ONE_APPLICATION_BINDING_REPLACEMENT'
    $changed=$original.Replace($before,$after)
    Assert-P09XrefBinding ($changed.Replace($after,$before) -ceq $original) 'CAPTURE_EIGHT_OBSERVER_WHOLE_FUNCTION_INVERSE'
    $tokens=$null;$errors=$null
    $projected=[Management.Automation.Language.Parser]::ParseInput($changed,$path,[ref]$tokens,[ref]$errors)
    Assert-P09XrefBinding (@($errors).Count -eq 0) 'CAPTURE_EIGHT_PROJECTED_OBSERVER_PARSE'
    return [pscustomobject]@{original=$original;changed=$changed;loader=$projected.GetScriptBlock();before=$before;after=$after}
}

function Initialize-P09XrefCapture008ApplicationBinding {
    Assert-P09XrefBinding ($null -eq (Get-Variable P09XrefCapture008ApplicationInstalled -Scope Script -ErrorAction SilentlyContinue)) 'CAPTURE_EIGHT_APPLICATION_NO_REINSTALL'
    $definition=Get-P09XrefCapture008ApplicationDefinition
    $actual=Get-Command Read-P09XrefActiveSourceObservation -CommandType Function -ErrorAction Stop
    Assert-P09XrefBinding ($actual.ScriptBlock.Ast -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $actual.ScriptBlock.Ast.Extent.Text -ceq $definition.original) 'CAPTURE_EIGHT_ORIGINAL_LIVE_OBSERVER_UNCHANGED'
    $script:P09XrefCapture008ApplicationInstalled=$true
    . $definition.loader
    $loaded=Get-Command Read-P09XrefActiveSourceObservation -CommandType Function -ErrorAction Stop
    Assert-P09XrefBinding ($loaded.ScriptBlock.Ast.Extent.Text -ceq $definition.changed) 'CAPTURE_EIGHT_PROJECTED_LIVE_OBSERVER_EXACT'
    Set-Item -Path Function:script:Read-P09XrefActiveSourceObservation -Value $loaded.ScriptBlock
}
