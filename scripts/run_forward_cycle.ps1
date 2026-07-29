# One forward paper-trading cycle for the validated dr + defensive config.
# Paper-only. Refreshes live inputs, runs one paper cycle, self-refines weights.
# -RefreshFeatures also rebuilds the feature history from fresh prices (weekly).
# Each step tolerates failure so a flaky feed does not abort the cycle -- the
# paper step falls back to the last good snapshot.
param(
    [switch]$RefreshFeatures
)
$ErrorActionPreference = "Continue"
$py = ".\.venv\Scripts\python.exe"

function Step($name, $argList) {
    Write-Host "[$(Get-Date -Format o)] $name"
    & $py @argList
    if ($LASTEXITCODE -ne 0) { Write-Host "  ($name exit $LASTEXITCODE - continuing)" }
}

if ($RefreshFeatures) {
    Step "price_repository" @("scripts/update_price_repository.py")
    Step "feature_backfill" @("scripts/backfill_bear_features.py")
    Step "alpha_engines"    @("scripts/run_alpha_engines.py")
}

# Same yfinance price source as the mark ticks, so rebalances and marks never
# create a price-source discontinuity in the equity curve.
Step "quick_snapshot" @("scripts/quick_snapshot.py")
Step "alpha_engines"  @("scripts/run_alpha_engines.py")
Step "forward_paper"  @("scripts/run_forward_paper.py")
Step "self_refine"    @("scripts/forward_refine.py")
Write-Host "[$(Get-Date -Format o)] cycle complete"
