# Always-on forward paper loop: runs one cycle every -IntervalHours, forever.
# Every -FeatureRefreshEvery cycles it also refreshes features from fresh prices
# so the strategy adapts to new live data. Restart-safe: the paper account,
# equity log, and engine weights all persist across cycles.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_forward_loop.ps1
#
# For reboot persistence, register this as a Windows scheduled task instead of
# relying on this process staying up.
param(
    [double]$IntervalHours = 24,
    [int]$FeatureRefreshEvery = 7
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cycle = Join-Path $here "run_forward_cycle.ps1"
$i = 0
Write-Host "Forward paper loop started. interval=${IntervalHours}h refresh_every=$FeatureRefreshEvery cycles."
while ($true) {
    $refresh = ($i % $FeatureRefreshEvery) -eq 0
    if ($refresh) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $cycle -RefreshFeatures
    } else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $cycle
    }
    $i++
    Start-Sleep -Seconds ([int]($IntervalHours * 3600))
}
