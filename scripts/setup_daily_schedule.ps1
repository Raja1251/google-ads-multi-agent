# PowerShell script to register a Daily 8:00 AM Task in Windows Task Scheduler
# Registers task under current user context (Least Privilege - No Admin/SYSTEM needed).

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$PythonExe = (Get-Command python.exe -ErrorAction Stop).Source
$TargetScript = Join-Path $ProjectDir "scripts\orchestrate_team.py"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$TargetScript`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00 AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$TaskName = "Antigravity_GoogleAds_MorningAudit"

# Register task under CURRENT user context (Least privilege)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -User $env:USERNAME -Description "Runs Antigravity Multi-Agent Google Ads Audit every morning at 8:00 AM."

Write-Host "Scheduled Task '$TaskName' registered successfully for $env:USERNAME at 8:00 AM daily!" -ForegroundColor Green
