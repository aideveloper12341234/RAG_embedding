param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Chunks,
    [Parameter(Mandatory=$true)][datetime]$At,
    [string]$TaskName = 'AlarmSystem-DailyIndex'
)
$ErrorActionPreference = 'Stop'
$Python = (Resolve-Path -LiteralPath $Python).Path
$Chunks = (Resolve-Path -LiteralPath $Chunks).Path
$runner = Join-Path $PSScriptRoot 'run-daily-index.ps1'
foreach ($value in @($Python, $Chunks, $runner)) {
    if ($value.Contains('"')) { throw 'Paths must not contain double quotes' }
}
$arguments = '-NoProfile -NonInteractive -File "{0}" -Python "{1}" -Chunks "{2}"' -f $runner, $Python, $Chunks
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
# No -Force: an existing task must not be silently overwritten.
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal
