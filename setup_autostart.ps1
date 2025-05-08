# 获取当前脚本所在目录的绝对路径
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchFilePath = Join-Path $scriptPath "run_update_dns.bat"

# 创建计划任务
$action = New-ScheduledTaskAction -Execute $batchFilePath
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 注册计划任务
Register-ScheduledTask -TaskName "UpdateDNSIPv6" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Write-Host "开机自启动任务已设置完成！"
Write-Host "任务名称: UpdateDNSIPv6"
Write-Host "执行文件: $batchFilePath" 