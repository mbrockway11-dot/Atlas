param(
    [int]$IntervalSeconds = 300,
    [double]$InitialCash = 10000.0,
    [int]$MaximumCycles = 0
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$CycleRunner = Join-Path $ProjectRoot "scripts\run_shadow_cycle_once.py"
$IntentPlan = Join-Path $ProjectRoot "output\investment_paper_execution\portfolio_intent_plan.json"
$LogDirectory = Join-Path $ProjectRoot "output\investment_paper_execution\continuous_runner"
$LogPath = Join-Path $LogDirectory "continuous_shadow_runner.log"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $LogDirectory |
Out-Null

if (-not (Test-Path $Python)) {
    throw "Atlas Python executable not found: $Python"
}

if (-not (Test-Path $CycleRunner)) {
    throw "Shadow-cycle runner not found: $CycleRunner"
}

Set-Location $ProjectRoot

function Write-RunnerLog {
    param(
        [string]$Message
    )

    $line = "$(Get-Date -Format o) $Message"

    Write-Host $line

    Add-Content `
        -LiteralPath $LogPath `
        -Value $line
}

$cycleCount = 0

Write-RunnerLog (
    "Continuous shadow trading started. " +
    "interval_seconds=$IntervalSeconds " +
    "initial_cash=$InitialCash"
)

while ($true) {
    $cycleCount += 1

    if (
        $MaximumCycles -gt 0 -and
        $cycleCount -gt $MaximumCycles
    ) {
        Write-RunnerLog "Maximum cycle count reached. Stopping."
        break
    }

    if (-not (Test-Path $IntentPlan)) {
        Write-RunnerLog "No intent plan found. Waiting: $IntentPlan"

        Start-Sleep `
            -Seconds $IntervalSeconds

        continue
    }

    Write-RunnerLog "Starting shadow cycle $cycleCount"

    $result = & $Python `
        $CycleRunner `
        --initial-cash `
        $InitialCash

    $pythonExitCode = $LASTEXITCODE

    if ($pythonExitCode -ne 0) {
        Write-RunnerLog (
            "Shadow cycle failed or halted with exit code " +
            "$pythonExitCode. Stopping."
        )

        exit $pythonExitCode
    }

    $jsonLine = $result |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        } |
        Select-Object -Last 1

    try {
        $summary = $jsonLine |
            ConvertFrom-Json
    }
    catch {
        Write-RunnerLog (
            "Could not parse shadow-cycle output as JSON: " +
            "$jsonLine"
        )

        exit 3
    }

    Write-RunnerLog (
        "cycle_id=$($summary.cycle_id) " +
        "plan_id=$($summary.plan_id) " +
        "status=$($summary.status) " +
        "success=$($summary.success) " +
        "processed=$($summary.counts.processed_this_run) " +
        "remaining=$($summary.counts.remaining)"
    )

    if ($summary.status -eq "HALTED") {
        Write-RunnerLog (
            "Safety halt detected: " +
            "$($summary.halt_reason). Stopping."
        )

        exit 2
    }

    if (
        $MaximumCycles -eq 0 -or
        $cycleCount -lt $MaximumCycles
    ) {
        Start-Sleep `
            -Seconds $IntervalSeconds
    }
}
