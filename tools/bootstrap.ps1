[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $root
try {
    python .\tools\p01\toolchain_preflight.py
    python .\tools\p01\run_ci.py --lane all
}
finally {
    Pop-Location
}
