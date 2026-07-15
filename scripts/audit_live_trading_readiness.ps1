param(
    [string]$AtlasRoot = "C:\Projects\Atlas",
    [string]$V32Root = "C:\Projects\sigil-engine-git"
)

$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$AuditRoot = Join-Path $AtlasRoot "audit\live_readiness_$stamp"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $AuditRoot |
Out-Null

function Write-Section {
    param(
        [string]$Path,
        [string]$Title
    )

    Add-Content $Path ""
    Add-Content $Path ("=" * 90)
    Add-Content $Path $Title
    Add-Content $Path ("=" * 90)
}

function Relative-Path {
    param(
        [string]$Root,
        [string]$Path
    )

    return $Path.Replace(
        $Root.TrimEnd("\") + "\",
        ""
    )
}

$summaryPath = Join-Path $AuditRoot "00_live_readiness_summary.txt"
$brokerInventoryPath = Join-Path $AuditRoot "01_broker_inventory.csv"
$exchangeEvidencePath = Join-Path $AuditRoot "02_exchange_evidence.csv"
$executionEvidencePath = Join-Path $AuditRoot "03_execution_evidence.csv"
$safetyEvidencePath = Join-Path $AuditRoot "04_safety_evidence.csv"
$todoPath = Join-Path $AuditRoot "05_todos_and_placeholders.csv"
$testInventoryPath = Join-Path $AuditRoot "06_trading_tests.csv"
$configInventoryPath = Join-Path $AuditRoot "07_exchange_config_references.csv"
$gitPath = Join-Path $AuditRoot "08_git_state.txt"

Set-Content $summaryPath "ATLAS LIVE TRADING READINESS AUDIT"
Add-Content $summaryPath "Generated: $(Get-Date -Format o)"
Add-Content $summaryPath "Atlas: $AtlasRoot"
Add-Content $summaryPath "V32: $V32Root"

Write-Section $summaryPath "GIT CHECKPOINT"

Push-Location $AtlasRoot

git branch --show-current |
ForEach-Object {
    Add-Content $summaryPath "Branch: $_"
}

git log -1 --oneline |
ForEach-Object {
    Add-Content $summaryPath "Commit: $_"
}

git status --short |
Set-Content $gitPath

$gitStatus = @(
    git status --short
)

Add-Content $summaryPath "Working-tree entries: $($gitStatus.Count)"

Pop-Location

Write-Section $summaryPath "BROKER FILE INVENTORY"

$brokerRoots = @(
    (Join-Path $AtlasRoot "src\atlas\investment\brokers")
    (Join-Path $AtlasRoot "src\atlas\investment\broker")
    (Join-Path $AtlasRoot "src\atlas\investment\market_data")
    (Join-Path $AtlasRoot "src\atlas\investment\execution")
    (Join-Path $AtlasRoot "src\atlas\investment\orchestration")
)

$brokerFiles = foreach ($root in $brokerRoots) {
    if (-not (Test-Path $root)) {
        continue
    }

    Get-ChildItem `
        $root `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -in @(
            ".py",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".md"
        )
    } |
    ForEach-Object {
        [PSCustomObject]@{
            Root = Relative-Path $AtlasRoot $root
            Path = Relative-Path $AtlasRoot $_.FullName
            Name = $_.Name
            Extension = $_.Extension
            SizeBytes = $_.Length
            LastWriteTime = $_.LastWriteTime
        }
    }
}

$brokerFiles |
Sort-Object Path |
Export-Csv `
    $brokerInventoryPath `
    -NoTypeInformation `
    -Encoding UTF8

Add-Content $summaryPath "Broker/execution files: $($brokerFiles.Count)"

$brokerFiles |
ForEach-Object {
    Add-Content $summaryPath "  $($_.Path)"
}

Write-Section $summaryPath "CONCRETE EXCHANGE EVIDENCE"

$exchangePatterns = @(
    "coinbase",
    "kraken",
    "binance",
    "ccxt",
    "advanced trade",
    "api.coinbase",
    "api.kraken",
    "api.binance",
    "sandbox",
    "testnet",
    "api_key",
    "api_secret",
    "passphrase",
    "sign_request",
    "signature",
    "nonce"
)

$sourceFiles = @(
    Get-ChildItem `
        (Join-Path $AtlasRoot "src") `
        -Recurse `
        -File `
        -Filter *.py `
        -ErrorAction SilentlyContinue
)

$exchangeEvidence = foreach ($file in $sourceFiles) {
    foreach ($pattern in $exchangePatterns) {
        $matches = Select-String `
            -Path $file.FullName `
            -Pattern $pattern `
            -SimpleMatch `
            -ErrorAction SilentlyContinue

        foreach ($match in $matches) {
            $line = $match.Line.Trim()

            $line = $line -replace `
                "(?i)(api[_-]?key|api[_-]?secret|private[_-]?key|passphrase)\s*[:=]\s*.+", `
                '$1=<REDACTED>'

            [PSCustomObject]@{
                ExchangePattern = $pattern
                Path = Relative-Path $AtlasRoot $file.FullName
                LineNumber = $match.LineNumber
                Evidence = $line
            }
        }
    }
}

$exchangeEvidence |
Sort-Object Path,LineNumber,ExchangePattern -Unique |
Export-Csv `
    $exchangeEvidencePath `
    -NoTypeInformation `
    -Encoding UTF8

$exchangeGroups = $exchangeEvidence |
Group-Object ExchangePattern |
Sort-Object Count -Descending

foreach ($group in $exchangeGroups) {
    Add-Content $summaryPath (
        "{0}: {1}" -f
        $group.Name,
        $group.Count
    )
}

Write-Section $summaryPath "ORDER-SUBMISSION AND RECONCILIATION EVIDENCE"

$executionPatterns = @(
    "submit_order",
    "place_order",
    "create_order",
    "cancel_order",
    "cancel_all",
    "get_order",
    "get_orders",
    "get_fills",
    "get_positions",
    "get_balance",
    "get_balances",
    "client_order_id",
    "idempotency",
    "partial_fill",
    "reconcile",
    "position_reconciliation",
    "balance_reconciliation",
    "order_submission_allowed",
    "live_authorized",
    "manual_approval",
    "approval_required"
)

$executionEvidence = foreach ($file in $sourceFiles) {
    foreach ($pattern in $executionPatterns) {
        $matches = Select-String `
            -Path $file.FullName `
            -Pattern $pattern `
            -SimpleMatch `
            -ErrorAction SilentlyContinue

        foreach ($match in $matches) {
            [PSCustomObject]@{
                Pattern = $pattern
                Path = Relative-Path $AtlasRoot $file.FullName
                LineNumber = $match.LineNumber
                Evidence = $match.Line.Trim()
            }
        }
    }
}

$executionEvidence |
Sort-Object Path,LineNumber,Pattern -Unique |
Export-Csv `
    $executionEvidencePath `
    -NoTypeInformation `
    -Encoding UTF8

foreach ($group in (
    $executionEvidence |
    Group-Object Pattern |
    Sort-Object Count -Descending
)) {
    Add-Content $summaryPath (
        "{0}: {1}" -f
        $group.Name,
        $group.Count
    )
}

Write-Section $summaryPath "SAFETY CONTROLS"

$safetyPatterns = @(
    "kill_switch",
    "emergency_stop",
    "daily_loss",
    "maximum_daily_loss",
    "maximum_position",
    "maximum_exposure",
    "stale_data",
    "heartbeat",
    "duplicate_order",
    "manual_approval",
    "research_only",
    "shadow_mode",
    "live_authorized",
    "order_submission_allowed",
    "one_position",
    "max_positions"
)

$safetyEvidence = foreach ($file in $sourceFiles) {
    foreach ($pattern in $safetyPatterns) {
        $matches = Select-String `
            -Path $file.FullName `
            -Pattern $pattern `
            -SimpleMatch `
            -ErrorAction SilentlyContinue

        foreach ($match in $matches) {
            [PSCustomObject]@{
                Pattern = $pattern
                Path = Relative-Path $AtlasRoot $file.FullName
                LineNumber = $match.LineNumber
                Evidence = $match.Line.Trim()
            }
        }
    }
}

$safetyEvidence |
Sort-Object Path,LineNumber,Pattern -Unique |
Export-Csv `
    $safetyEvidencePath `
    -NoTypeInformation `
    -Encoding UTF8

foreach ($group in (
    $safetyEvidence |
    Group-Object Pattern |
    Sort-Object Count -Descending
)) {
    Add-Content $summaryPath (
        "{0}: {1}" -f
        $group.Name,
        $group.Count
    )
}

Write-Section $summaryPath "TODOS, STUBS, AND PLACEHOLDERS"

$todoPatterns = @(
    "TODO",
    "FIXME",
    "NotImplementedError",
    "raise NotImplemented",
    "pass #",
    "placeholder",
    "mock only",
    "paper only",
    "not production",
    "live disabled"
)

$todoEvidence = foreach ($file in $sourceFiles) {
    foreach ($pattern in $todoPatterns) {
        $matches = Select-String `
            -Path $file.FullName `
            -Pattern $pattern `
            -SimpleMatch `
            -ErrorAction SilentlyContinue

        foreach ($match in $matches) {
            [PSCustomObject]@{
                Pattern = $pattern
                Path = Relative-Path $AtlasRoot $file.FullName
                LineNumber = $match.LineNumber
                Evidence = $match.Line.Trim()
            }
        }
    }
}

$todoEvidence |
Sort-Object Path,LineNumber,Pattern -Unique |
Export-Csv `
    $todoPath `
    -NoTypeInformation `
    -Encoding UTF8

Add-Content $summaryPath "Potential placeholders: $($todoEvidence.Count)"

Write-Section $summaryPath "TRADING TEST INVENTORY"

$tradingTestPattern = (
    "broker|" +
    "coinbase|" +
    "kraken|" +
    "binance|" +
    "exchange|" +
    "execution|" +
    "approval|" +
    "ledger|" +
    "reconcile|" +
    "paper|" +
    "portfolio|" +
    "position|" +
    "risk|" +
    "safety|" +
    "kill|" +
    "scheduler|" +
    "market_data|" +
    "market_monitor"
)

$tradingTests = @(
    Get-ChildItem `
        (Join-Path $AtlasRoot "tests") `
        -File `
        -Filter "test_*.py" `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match $tradingTestPattern
    }
)

$testRows = foreach ($test in $tradingTests) {
    [PSCustomObject]@{
        Name = $test.Name
        Path = Relative-Path $AtlasRoot $test.FullName
        SizeBytes = $test.Length
        LastWriteTime = $test.LastWriteTime
    }
}

$testRows |
Sort-Object Name |
Export-Csv `
    $testInventoryPath `
    -NoTypeInformation `
    -Encoding UTF8

Add-Content $summaryPath "Trading-related test files: $($tradingTests.Count)"

Write-Section $summaryPath "CONFIGURATION REFERENCES"

$configFiles = @(
    Get-ChildItem `
        $AtlasRoot `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\.venv\\" -and
        $_.FullName -notmatch "\\output\\" -and
        $_.FullName -notmatch "\\.git\\" -and
        $_.Extension -in @(
            ".py",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".env",
            ".example",
            ".md"
        )
    }
)

$configPatterns = @(
    "COINBASE",
    "KRAKEN",
    "BINANCE",
    "CCXT",
    "API_KEY",
    "API_SECRET",
    "PASSPHRASE",
    "TESTNET",
    "SANDBOX",
    "LIVE_TRADING",
    "BROKER_MODE"
)

$configEvidence = foreach ($file in $configFiles) {
    foreach ($pattern in $configPatterns) {
        $matches = Select-String `
            -Path $file.FullName `
            -Pattern $pattern `
            -SimpleMatch `
            -ErrorAction SilentlyContinue

        foreach ($match in $matches) {
            $safe = $match.Line.Trim()

            $safe = $safe -replace `
                "(?i)(api[_-]?key|api[_-]?secret|private[_-]?key|passphrase)\s*[:=]\s*.+", `
                '$1=<REDACTED>'

            [PSCustomObject]@{
                Pattern = $pattern
                Path = Relative-Path $AtlasRoot $file.FullName
                LineNumber = $match.LineNumber
                Evidence = $safe
            }
        }
    }
}

$configEvidence |
Sort-Object Path,LineNumber,Pattern -Unique |
Export-Csv `
    $configInventoryPath `
    -NoTypeInformation `
    -Encoding UTF8

Write-Section $summaryPath "PACKAGE CHECKS"

$packages = @(
    "ccxt",
    "coinbase-advanced-py",
    "coinbase",
    "krakenex",
    "python-binance"
)

foreach ($package in $packages) {
    $result = @(
        & python -m pip show $package 2>&1
    )

    $packageExitCode = $LASTEXITCODE

    if ($packageExitCode -eq 0) {
        $versionLine = $result |
            Where-Object {
                $_ -match "^Version:"
            } |
            Select-Object -First 1

        Add-Content $summaryPath (
            "${package}: INSTALLED $versionLine"
        )
    }
    else {
        Add-Content $summaryPath (
            "${package}: not installed"
        )
    }
}

Write-Section $summaryPath "V32 EXECUTION FILES"

if (Test-Path $V32Root) {
    $v32Files = @(
        Get-ChildItem `
            $V32Root `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\.venv\\" -and
            $_.Name -match (
                "execution|" +
                "broker|" +
                "order|" +
                "wallet|" +
                "coinbase|" +
                "kraken|" +
                "binance|" +
                "ccxt|" +
                "reconcile"
            )
        }
    )

    Add-Content $summaryPath "Matching V32 files: $($v32Files.Count)"

    foreach ($file in $v32Files | Select-Object -First 150) {
        Add-Content $summaryPath (
            "  " +
            (Relative-Path $V32Root $file.FullName)
        )
    }
}

Write-Section $summaryPath "AUDIT OUTPUTS"

Add-Content $summaryPath "Summary: $summaryPath"
Add-Content $summaryPath "Broker inventory: $brokerInventoryPath"
Add-Content $summaryPath "Exchange evidence: $exchangeEvidencePath"
Add-Content $summaryPath "Execution evidence: $executionEvidencePath"
Add-Content $summaryPath "Safety evidence: $safetyEvidencePath"
Add-Content $summaryPath "TODO evidence: $todoPath"
Add-Content $summaryPath "Test inventory: $testInventoryPath"
Add-Content $summaryPath "Config evidence: $configInventoryPath"
Add-Content $summaryPath "Git state: $gitPath"

Write-Host ""
Write-Host "Audit complete."
Write-Host "Audit directory: $AuditRoot"
Write-Host "Summary: $summaryPath"
