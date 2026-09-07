param(
    [string]$SaveDirectory = 'C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\save',
    [string]$Python = 'python',
    [switch]$Check
)
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $SaveDirectory -PathType Container)) {
    throw "Save directory does not exist: $SaveDirectory"
}
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $Python --version
if ($LASTEXITCODE -ne 0) { throw 'A working Windows Python installation is required.' }
if ($Check) {
    & $Python "$projectDirectory\helper\watch_save_directory.py" --help
    exit $LASTEXITCODE
}
& $Python -u "$projectDirectory\helper\watch_save_directory.py" $SaveDirectory
exit $LASTEXITCODE
