param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot | Resolve-Path),
    [string]$SaveDirectory = 'C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\save',
    [string]$TaskName = 'Lorekeeper Queue Watcher',
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

$wslProjectPath = (wsl.exe wslpath -a $ProjectPath).Trim()
$wslSaveDirectory = (wsl.exe wslpath -a $SaveDirectory).Trim()
if (-not $wslProjectPath -or -not $wslSaveDirectory) {
    throw 'Could not convert the project or save path through WSL.'
}

$command = "bash '$wslProjectPath/helper/start_watcher.sh' '$wslSaveDirectory'"
$action = New-ScheduledTaskAction -Execute 'wsl.exe' -Argument "-- bash -lc `"$command`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$description = 'Watches Dwarf Fortress save queues for Lorekeeper jobs.'

if ($WhatIf) {
    Write-Host 'PowerShell validation passed.'
    Write-Host "Task name: $TaskName"
    Write-Host "WSL project path: $wslProjectPath"
    Write-Host "WSL save path: $wslSaveDirectory"
    Write-Host "Action: wsl.exe $($action.Arguments)"
    Write-Host 'No scheduled task was registered.'
    exit 0
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Description $description -Force | Out-Null

Write-Host "Registered '$TaskName' to start the Lorekeeper watcher at logon."
Write-Host "Project: $ProjectPath"
Write-Host "Save directory: $SaveDirectory"
