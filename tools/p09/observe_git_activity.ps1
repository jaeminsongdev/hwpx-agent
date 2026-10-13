# Read-only, timed Git process observation. Never launches Git, kills processes, or changes settings.
[CmdletBinding()]
param([ValidateRange(5,30)][int]$Seconds=15,[ValidatePattern('^run[0-9]{2}$')][string]$Run='run01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$mask=$self.ProcessorAffinity.ToInt64()
$self.ProcessorAffinity=[IntPtr]($mask -band (-$mask))
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$expectedRoot='D:\'+[char]0xAC1C+[char]0xBC1C+'\hwpx-agent'
if($root -ne $expectedRoot){throw 'P149_WRONG_ROOT'}
$directory=Join-Path $root 'target/private/p09-149-git-observation'
$ancestor=$directory
while($ancestor -and $ancestor.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)){
    if((Test-Path -LiteralPath $ancestor) -and ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'P149_REPARSE_SCOPE'}
    if($ancestor -eq $root){break}
    $ancestor=[IO.Path]::GetDirectoryName($ancestor)
}
if(-not(Test-Path -LiteralPath $directory)){New-Item -ItemType Directory -Path $directory | Out-Null}
$receipt=Join-Path $directory "$Run.v1.json"
if(Test-Path -LiteralPath $receipt){throw 'P149_FRESH_RECEIPT_REQUIRED'}
function Safe-Role([string]$Name){
    if($Name -in @('git.exe','ChatGPT.exe','codex.exe','Code.exe','powershell.exe','pwsh.exe','cmd.exe','python.exe','node.exe','rustc.exe','cargo.exe')){return $Name}
    return 'other-process-redacted'
}
function Image-Role([string]$Image){
    if($Image -match '\\cmd\\git.exe$'){return 'cmd-launcher'}
    if($Image -match '\\mingw64\\bin\\git.exe$'){return 'mingw-worker'}
    if($Image -match '\\libexec\\git-core\\git.exe$'){return 'git-core-worker'}
    return 'unknown-git'
}
$watch=[Diagnostics.Stopwatch]::StartNew()
$rows=@();$seen=@{};$parentCache=@{};$failures=0
while($watch.Elapsed.TotalSeconds -lt $Seconds){
    try{$git=@(Get-CimInstance Win32_Process -Filter "Name='git.exe'" -OperationTimeoutSec 2 -ErrorAction Stop)}
    catch{$failures++;Start-Sleep -Milliseconds 500;continue}
    $rows+=@{elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,3);git_count=$git.Count}
    foreach($item in $git){
        $created=$item.CreationDate.ToUniversalTime().ToString('o')
        $key="$($item.ProcessId)/$created"
        if($seen.ContainsKey($key)){continue}
        $command=[string]$item.CommandLine
        $operations=@(foreach($name in @('status','diff','rev-parse','ls-files','cat-file','for-each-ref','symbolic-ref','show','log','config','fetch','clone','worktree')){
            if($command -match ('(?i)(?:^|\s)'+[regex]::Escape($name)+'(?:\s|$)')){$name}
        })
        $chain=@();$parentId=[uint32]$item.ParentProcessId
        for($depth=0;$depth -lt 6 -and $parentId -and $watch.Elapsed.TotalSeconds -lt $Seconds;$depth++){
            if(-not $parentCache.ContainsKey($parentId)){
                try{
                    $parent=Get-CimInstance Win32_Process -Filter "ProcessId=$parentId" -OperationTimeoutSec 2 -ErrorAction Stop
                    $parentCache[$parentId]=if($parent){@{pid=$parent.ProcessId;parent_pid=$parent.ParentProcessId;role=(Safe-Role $parent.Name);created_utc=$parent.CreationDate.ToUniversalTime().ToString('o')}}else{$null}
                }catch{$failures++;$parentCache[$parentId]=$null}
            }
            $safeParent=$parentCache[$parentId]
            if($null -eq $safeParent){$chain+=@{pid=$parentId;role='unavailable'};break}
            # A parent PID reused after this Git was created cannot establish ancestry.
            if([datetime]$safeParent.created_utc -gt $item.CreationDate.ToUniversalTime()){$chain+=@{pid=$parentId;role='pid-reused-unbound'};break}
            $chain+=$safeParent
            $parentId=[uint32]$safeParent.parent_pid
        }
        $seen[$key]=@{pid=$item.ProcessId;parent_pid=$item.ParentProcessId;created_utc=$created;
            first_elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,3);operation_tags=$operations;
            image_role=(Image-Role ([string]$item.ExecutablePath));parent_chain=$chain;
            explicit_hwpx_path_in_command=($command -match 'hwpx-agent');cwd_binding='NOT_OBSERVED';raw_command_line_saved=$false}
    }
    Start-Sleep -Milliseconds 500
}
$result=[ordered]@{schema_version='hwpx-agent.p09-git-observation/v1';state='READ_ONLY_OBSERVATION_NOT_CAUSE_OR_PRODUCT_PROOF';
    run=$Run;ended_utc=[datetime]::UtcNow.ToString('o');elapsed_seconds=[math]::Round($watch.Elapsed.TotalSeconds,2);
    source_pin=@{path='tools/p09/observe_git_activity.ps1';sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()};
    git_max_concurrent=if($rows.Count){($rows|ForEach-Object{$_['git_count']}|Measure-Object -Maximum).Maximum}else{$null};
    git_distinct_observed=$seen.Count;observation_errors=$failures;samples=$rows;git_processes=@($seen.Values);
    new_git_started=$false;foreign_processes_modified=$false;settings_changed=$false;heavy_verification_started=$false;
    raw_command_lines_saved=$false;P09_gate='OPEN';product_complete=$false}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 10))
$stream=[IO.File]::Open($receipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
$result.Remove('samples');$result.Remove('git_processes')
$result|ConvertTo-Json -Depth 4 -Compress
