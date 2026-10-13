[CmdletBinding()]
param([Parameter(Mandatory)][string]$ProbeMarker)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProbeMarker -cne 'P09_NON_NATIVE_SHELL_ARGUMENT_PROBE') { exit 2 }
[Console]::Write('P09_NON_NATIVE_SHELL_ARGUMENT_PROBE_PASS')
exit 0
