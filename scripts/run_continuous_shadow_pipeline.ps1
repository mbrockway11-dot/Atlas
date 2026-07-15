param(
    [string]$TargetsPath = "output\investment_paper_execution\shadow_targets_g12.json",
    [string]$SnapshotPath = "output\investment_market_data\latest_market_snapshot.json",
    [int]$IntervalSeconds = 30,
    [double]$InitialCash = 10000.0,
    [int]$MaximumCycles = 0,
    [switch]$RunImmediately
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PipelineRunner = Join-Path $ProjectRoot "scripts\run_shadow_pipeline_once.py"

if (-not [System.IO.Path]::IsPathRooted($TargetsPath)) {
    $TargetsPath = Join-Path $ProjectRoot $TargetsPath
}

if (-not [System.IO.Path]::IsPathRooted($SnapshotPath)) {
    $SnapshotPath = Join-Path $ProjectRoot $SnapshotPath
}

$OutputDirectory = Join-Path `
    $ProjectRoot `
    "output\investment_paper_execution\continuous_pipeline"

$StatePath = Join-Path `
    $OutputDirectory `
    "continuous_pipeline_state.json"

$LogPath = Join-Path `
    $OutputDirectory `
    "continuous_pipeline.log"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $OutputDirectory |
Out-Null

if (-not (Test-Path $Python)) {
    throw "Atlas Python executable not found: $Python"
}

if (-not (Test-Path $PipelineRunner)) {
    throw "Pipeline runner not found: $PipelineRunner"
}

Set-Location $ProjectRoot

function Write-RunnerLog {
    param([string]$Message)

    $line = "$(Get-Date -Format o) $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line
}

function Get-SafeHash {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    return (
        Get-FileHash `
            -LiteralPath $Path `
            -Algorithm SHA256
    ).Hash
}

function Read-State {
    if (-not (Test-Path $StatePath)) {
        return [PSCustomObject]@{
            snapshot_hash = ""
            targets_hash = ""
            last_pipeline_id = ""
            last_status = ""
        }
    }

    try {
        return Get-Content `
            -LiteralPath $StatePath `
            -Raw |
        ConvertFrom-Json
    }
    catch {
        throw "Continuous-pipeline state file is invalid: $StatePath"
    }
}

function Write-State {
    param(
        [string]$SnapshotHash,
        [string]$TargetsHash,
        [string]$PipelineId,
        [string]$Status
    )

    $payload = [ordered]@{
        updated_at = (Get-Date -Format o)
        snapshot_hash = $SnapshotHash
        targets_hash = $TargetsHash
        last_pipeline_id = $PipelineId
        last_status = $Status
        paper_only = $true
        live_execution = $false
    }

    $temporary = "$StatePath.tmp"

    $payload |
        ConvertTo-Json -Depth 10 |
        Set-Content `
            -LiteralPath $temporary `
            -Encoding UTF8

    Move-Item `
        -LiteralPath $temporary `
        -Destination $StatePath `
        -Force
}

$state = Read-State
$cycleCount = 0
$firstIteration = $true

Write-RunnerLog (
    "Continuous integrated shadow pipeline started. " +
    "interval_seconds=$IntervalSeconds " +
    "targets=$TargetsPath " +
    "snapshot=$SnapshotPath"
)

while ($true) {
    if (
        $MaximumCycles -gt 0 -and
        $cycleCount -ge $MaximumCycles
    ) {
        Write-RunnerLog "Maximum executed cycle count reached. Stopping."
        break
    }

    if (-not (Test-Path $SnapshotPath)) {
        Write-RunnerLog "Market snapshot missing. Waiting: $SnapshotPath"
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    if (-not (Test-Path $TargetsPath)) {
        Write-RunnerLog "Strategy targets missing. Waiting: $TargetsPath"
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    $snapshotHash = Get-SafeHash $SnapshotPath
    $targetsHash = Get-SafeHash $TargetsPath

    $snapshotChanged = (
        $snapshotHash -ne [string]$state.snapshot_hash
    )

    $targetsChanged = (
        $targetsHash -ne [string]$state.targets_hash
    )

    $shouldRun = (
        $snapshotChanged -or
        $targetsChanged -or
        ($firstIteration -and $RunImmediately)
    )

    $firstIteration = $false

    if (-not $shouldRun) {
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    $changeReason = @()

    if ($snapshotChanged) {
        $changeReason += "MARKET_SNAPSHOT_CHANGED"
    }

    if ($targetsChanged) {
        $changeReason += "STRATEGY_TARGETS_CHANGED"
    }

    Write-RunnerLog (
        "Running integrated pipeline. reason=" +
        ($changeReason -join ",")
    )

    $result = & $Python `
        $PipelineRunner `
        --targets `
        $TargetsPath `
        --initial-cash `
        $InitialCash

    $exitCode = $LASTEXITCODE

    $jsonLine = $result |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        } |
        Select-Object -Last 1

    if ($exitCode -ne 0) {
        Write-RunnerLog (
            "Integrated pipeline failed with exit code " +
            "$exitCode + output=$jsonLine"
        )

        exit $exitCode
    }

    try {
        $summary = $jsonLine |
            ConvertFrom-Json
    }
    catch {
        Write-RunnerLog (
            "Could not parse pipeline JSON output: $jsonLine"
        )

        exit 3
    }

    $cycleCount += 1

    Write-RunnerLog (
        "pipeline_id=$($summary.pipeline_id) " +
        "snapshot_id=$($summary.snapshot_id) " +
        "plan_id=$($summary.plan_id) " +
        "cycle_id=$($summary.cycle_id) " +
        "status=$($summary.status) " +
        "success=$($summary.success)"
    )

    if (-not $summary.success) {
        Write-RunnerLog (
            "Safety halt: " +
            (($summary.errors | ForEach-Object { "$_" }) -join "|")
        )

        exit 2
    }

    Write-State `
        -SnapshotHash $snapshotHash `
        -TargetsHash $targetsHash `
        -PipelineId $summary.pipeline_id `
        -Status $summary.status

    $state = Read-State

    Start-Sleep -Seconds $IntervalSeconds
}
