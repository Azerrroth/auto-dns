# 删除计划任务
try {
    Unregister-ScheduledTask -TaskName "UpdateDNSIPv6" -Confirm:$false
    Write-Host "成功删除开机自启动任务！"
} catch {
    Write-Host "删除任务失败，可能任务不存在或没有权限。"
    Write-Host "错误信息: $_"
}

Write-Host "`n如果上述方法失败，你也可以手动删除任务："
Write-Host "1. 按 Win + R，输入 taskschd.msc 打开任务计划程序"
Write-Host "2. 在左侧面板中展开'任务计划程序库'"
Write-Host "3. 找到名为 'UpdateDNSIPv6' 的任务"
Write-Host "4. 右键点击任务，选择'删除'" 