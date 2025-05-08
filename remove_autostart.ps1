# Remove scheduled task
try {
    Unregister-ScheduledTask -TaskName "UpdateDNSIPv6" -Confirm:$false
    Write-Host "Successfully removed auto-start task!"
} catch {
    Write-Host "Failed to remove task. The task might not exist or you don't have permission."
    Write-Host "Error message: $_"
}

Write-Host "`nIf the above method fails, you can also remove the task manually:"
Write-Host "1. Press Win + R, type taskschd.msc to open Task Scheduler"
Write-Host "2. Expand 'Task Scheduler Library' in the left panel"
Write-Host "3. Find the task named 'UpdateDNSIPv6'"
Write-Host "4. Right-click the task and select 'Delete'" 