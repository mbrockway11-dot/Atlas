# Register (or re-register) the always-on forward paper tasks as Windows
# scheduled tasks so they survive reboots and session end. Paper-only.
# Run once:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register_forward_tasks.ps1
$repo = "C:\Projects\Atlas"
$ps = "powershell"

$dailyArg = "-NoProfile -ExecutionPolicy Bypass -Command ""Set-Location '$repo'; .\scripts\run_forward_cycle.ps1"""
$weeklyArg = "-NoProfile -ExecutionPolicy Bypass -Command ""Set-Location '$repo'; .\scripts\run_forward_cycle.ps1 -RefreshFeatures"""

$dailyAction  = New-ScheduledTaskAction -Execute $ps -Argument $dailyArg
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "AtlasForwardPaper" -Action $dailyAction -Trigger $dailyTrigger -Description "Atlas forward paper cycle (dr+defensive), paper-only" -Force | Out-Null
Write-Host "Registered daily task 'AtlasForwardPaper' at 09:00"

$weeklyAction  = New-ScheduledTaskAction -Execute $ps -Argument $weeklyArg
$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8am
Register-ScheduledTask -TaskName "AtlasForwardPaper-WeeklyRefresh" -Action $weeklyAction -Trigger $weeklyTrigger -Description "Atlas weekly feature refresh + forward cycle" -Force | Out-Null
Write-Host "Registered weekly refresh task 'AtlasForwardPaper-WeeklyRefresh' Sun 08:00"

# Frequent mark-to-market: revalue the book every 5 minutes (no rebalance).
$markArg = "-NoProfile -ExecutionPolicy Bypass -Command ""Set-Location '$repo'; .\scripts\run_forward_mark.ps1"""
$markAction  = New-ScheduledTaskAction -Execute $ps -Argument $markArg
$markTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "AtlasForwardPaper-Mark" -Action $markAction -Trigger $markTrigger -Description "Atlas forward paper mark-to-market every 5 min (paper-only, no trades)" -Force | Out-Null
Write-Host "Registered mark task 'AtlasForwardPaper-Mark' every 5 minutes"

Write-Host "`nTo remove: Unregister-ScheduledTask -TaskName AtlasForwardPaper,AtlasForwardPaper-WeeklyRefresh -Confirm:`$false"
