# Get the absolute path of the current script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchFilePath = Join-Path $scriptPath "run_update_dns.bat"

# Create scheduled task
$action = New-ScheduledTaskAction -Execute $batchFilePath
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register scheduled task
Register-ScheduledTask -TaskName "UpdateDNSIPv6" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Write-Host "Auto-start task has been set up successfully!"
Write-Host "Task Name: UpdateDNSIPv6"
Write-Host "Executable: $batchFilePath" 