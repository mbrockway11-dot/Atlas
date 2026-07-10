# Market Universe v1

Market Universe v1 evaluated 12 whitelisted asset(s), approved 10, rejected 2, and found 0 failed required core asset(s).

## Approved Assets

- `BTC-USD`
- `ETH-USD`
- `SOL-USD`
- `BNB-USD`
- `XRP-USD`
- `LINK-USD`
- `AVAX-USD`
- `AAVE-USD`
- `DOGE-USD`
- `ADA-USD`

## Rejected Assets

- `SUI-USD` ? fetch_error:empty_download, insufficient_observations, price_below_minimum, median_dollar_volume_below_minimum, average_dollar_volume_below_minimum, stale_market_data, excessive_missing_close_data
- `HYPE-USD` ? insufficient_observations, price_below_minimum, median_dollar_volume_below_minimum, average_dollar_volume_below_minimum, stale_market_data

## Liquidity Gates

```json
{
  "minimum_observations": 120,
  "minimum_price": 0.01,
  "minimum_median_daily_dollar_volume": 5000000.0,
  "minimum_average_daily_dollar_volume": 10000000.0,
  "maximum_stale_days": 5,
  "maximum_missing_close_ratio": 0.02
}
```
