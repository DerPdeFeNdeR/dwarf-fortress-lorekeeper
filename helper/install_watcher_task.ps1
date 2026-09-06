param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot | Resolve-Path),
    [string]$SaveDirectory = 'C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\save',
    [string]$TaskName = 'Lorekeeper Queue Watcher',
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

function Convert-WindowsPathToWsl([string]$Path) {
    $normalizedPath = $Path -replace '\\', '/'
    $convertedPath = wsl.exe --exec wslpath -a $normalizedPath
    if ($LASTEXITCODE -ne 0 -or -not $convertedPath) {
        throw "Could not convert Windows path '$Path' through WSL."
    }
    return $convertedPath.Trim()
}

$wslProjectPath = Convert-WindowsPathToWsl $ProjectPath
$wslSaveDirectory = Convert-WindowsPathToWsl $SaveDirectory
if (-not $wslProjectPath -or -not $wslSaveDirectory) {
    throw 'Could not convert the project or save path through WSL.'
}

$shellQuoteEscape = [string][char]39 + [char]34 + [char]39 + [char]34 + [char]39
$quotedProject = $wslProjectPath.Replace("'", $shellQuoteEscape)
$quotedSave = $wslSaveDirectory.Replace("'", $shellQuoteEscape)
$command = "bash '$quotedProject/helper/start_watcher.sh' '$quotedSave'"
$action = New-ScheduledTaskAction -Execute 'wsl.exe' -Argument "-- bash -lc `"$command`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$description = 'Watches Dwarf Fortress save queues for Lorekeeper jobs.'
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

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
    -Principal $principal -Settings $settings -Description $description -Force | Out-Null

Write-Host "Registered '$TaskName' to start the Lorekeeper watcher at logon."
Write-Host "Project: $ProjectPath"
Write-Host "Save directory: $SaveDirectory"
